from __future__ import annotations

import enum
import logging
import queue
import threading
from typing import List, Optional, Set, Union

from .exceptions import (
    ConnectionClosed,
    FrameError,
    ProtocolError,
)
from .frames import (
    CONTROL_FRAMES,
    CloseCode,
    Frame,
    Opcode,
    decode_close_payload,
    encode_close_payload,
    parse_frame,
)
from .utils import BytesLike

__all__ = ["WebSocketProtocol", "State", "ConnectionState"]


class State(enum.IntEnum):
    """
    WebSocket connection states.

    .. note::
        State transitions:
        CONNECTING -> OPEN -> CLOSING -> CLOSED
    """

    CONNECTING = 0
    OPEN = 1
    CLOSING = 2
    CLOSED = 3


class ConnectionState:
    """
    Thread-safe connection state management.

    :param initial: Initial state
    """

    def __init__(self, initial: State = State.CONNECTING):
        self._state = initial
        self._lock = threading.Lock()
        self._close_code: Optional[int] = None
        self._close_reason: Optional[str] = None

    @property
    def state(self) -> State:
        """Current connection state."""
        with self._lock:
            return self._state

    @property
    def close_code(self) -> Optional[int]:
        """Close status code if connection is closed."""
        with self._lock:
            return self._close_code

    @property
    def close_reason(self) -> Optional[str]:
        """Close reason if connection is closed."""
        with self._lock:
            return self._close_reason

    def transition(
        self, to_state: State, code: Optional[int] = None, reason: str = ""
    ) -> None:
        """
        Transition to a new state.

        :param to_state: Target state
        :param code: Close status code
        :param reason: Close reason
        :raises ValueError: If transition is invalid
        """
        with self._lock:
            current = self._state

            # Validate state transition
            if (
                (
                    current == State.CONNECTING and to_state not in {State.OPEN, State.CLOSED}
                ) or (
                    current == State.OPEN and to_state not in {State.CLOSING, State.CLOSED}
                ) or (
                    current == State.CLOSING and to_state != State.CLOSED
                ) or (
                    current == State.CLOSED
                )
            ):
                raise ValueError(
                    f"Invalid state transition: {current.name} -> {to_state.name}"
                )

            self._state = to_state
            if to_state == State.CLOSED:
                self._close_code = code
                self._close_reason = reason


class WebSocketProtocol:
    """
    WebSocket protocol implementation.

    This class handles the WebSocket protocol logic including:
    - Connection state management
    - Frame parsing and validation
    - Message fragmentation
    - Control frame handling
    - Close handshake

    :param logger: Logger instance
    :param max_size: Maximum message size in bytes
    """

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        max_size: Optional[int] = 2**20,
    ) -> None:
        if logger is None:
            logger = logging.getLogger("simple_websocket.protocol")
        self.logger = logger
        self.max_size = max_size

        self.state = ConnectionState()

        # Frame/message handling
        self._incoming_buffer = bytearray()
        self._outgoing_queue: queue.Queue[bytes] = queue.Queue()
        self._message_queue: queue.Queue[Union[str, bytes]] = queue.Queue()

        # Message fragmentation state
        self._fragmented_message_type: Optional[Opcode] = None
        self._fragmented_message_buffer: List[bytes] = []
        self._fragmented_message_size = 0

        # Close frame tracking
        self._close_frame_sent = False
        self._close_frame_received = False

        # Active pings
        self._pending_pings: Set[bytes] = set()

    def receive_data(self, data: bytes) -> None:
        """
        Process incoming WebSocket data.

        :param data: Raw bytes received from socket
        :raises ProtocolError: If protocol violation is detected
        """
        if self.state.state == State.CLOSED:
            return

        self._incoming_buffer.extend(data)

        while self._incoming_buffer:
            # Try to parse a frame
            try:
                frame, consumed = parse_frame(
                    self._incoming_buffer, max_size=self.max_size
                )
            except FrameError:
                # Not enough data for a complete frame
                break

            # Remove consumed data
            del self._incoming_buffer[:consumed]

            try:
                self._handle_frame(frame)
            except Exception as exc:
                self.logger.error("Error handling frame", exc_info=True)
                self.close(CloseCode.PROTOCOL_ERROR, str(exc))
                raise

    def _handle_frame(self, frame: Frame) -> None:
        """
        Handle a parsed WebSocket frame.

        :param frame: Parsed frame
        :raises ProtocolError: If protocol violation is detected
        """
        if frame.opcode in CONTROL_FRAMES:
            self._handle_control_frame(frame)
        else:
            self._handle_data_frame(frame)

    def _handle_control_frame(self, frame: Frame) -> None:
        """
        Handle a WebSocket control frame.

        :param frame: Control frame
        :raises ProtocolError: If protocol violation is detected
        """
        if frame.opcode == Opcode.CLOSE:
            if len(frame.payload) >= 2:
                code, reason = decode_close_payload(frame.payload)
                self._handle_close(code, reason)
            else:
                self._handle_close(CloseCode.NORMAL, "")

        elif frame.opcode == Opcode.PING:
            if self.state.state != State.CLOSED:
                # Echo the payload back in a pong
                self.pong(frame.payload)

        elif frame.opcode == Opcode.PONG:
            # Remove from pending pings if it matches
            self._pending_pings.discard(bytes(frame.payload))

    def _handle_data_frame(self, frame: Frame) -> None:
        """
        Handle a WebSocket data frame.

        :param frame: Data frame
        :raises ProtocolError: If protocol violation is detected
        """
        if frame.opcode == Opcode.CONTINUATION:
            if self._fragmented_message_type is None:
                raise ProtocolError("Unexpected continuation frame")

            self._fragmented_message_buffer.append(frame.payload)
            self._fragmented_message_size += len(frame.payload)

            if self.max_size and self._fragmented_message_size > self.max_size:
                raise ProtocolError("Message size exceeds limit")

            if frame.fin:
                # Message is complete
                message = b"".join(self._fragmented_message_buffer)
                if self._fragmented_message_type == Opcode.TEXT:
                    try:
                        message = message.decode("utf-8")
                    except UnicodeDecodeError:
                        raise ProtocolError("Invalid UTF-8 in text message")

                self._message_queue.put(message)
                self._fragmented_message_type = None
                self._fragmented_message_buffer.clear()
                self._fragmented_message_size = 0

        else:  # New message
            if self._fragmented_message_type is not None:
                raise ProtocolError("Expected continuation frame")

            if frame.fin:
                # Unfragmented message
                if frame.opcode == Opcode.TEXT:
                    try:
                        message = frame.payload.decode("utf-8")
                    except UnicodeDecodeError:
                        raise ProtocolError("Invalid UTF-8 in text message")
                    self._message_queue.put(message)
                else:
                    self._message_queue.put(frame.payload)

            else:
                # Start of fragmented message
                self._fragmented_message_type = frame.opcode
                self._fragmented_message_buffer = [frame.payload]
                self._fragmented_message_size = len(frame.payload)

    def _handle_close(self, code: int, reason: str) -> None:
        """
        Handle a close frame.

        :param code: Close status code
        :param reason: Close reason
        """
        self._close_frame_received = True

        if not self._close_frame_sent:
            # Echo the close frame back
            self.close(code, reason)

        # Update state
        if self.state.state != State.CLOSED:
            self.state.transition(State.CLOSED, code, reason)

    def send_frame(self, frame: Frame) -> None:
        """
        Queue a frame for sending.

        :param frame: Frame to send
        :raises ConnectionClosed: If connection is closed
        """
        if self.state.state == State.CLOSED:
            raise ConnectionClosed(self.state.close_code, self.state.close_reason)

        data = frame.serialize(mask=True)  # Client always masks
        self._outgoing_queue.put(data)

    def get_outgoing_data(self) -> bytes:
        """
        Get queued outgoing data.

        :return: Data to send
        """
        data = bytearray()
        while True:
            try:
                chunk = self._outgoing_queue.get_nowait()
                data.extend(chunk)
            except queue.Empty:
                break
        return bytes(data)

    def receive_message(self, *, timeout: Optional[float] = None) -> Union[str, bytes]:
        """
        Receive the next message.

        :param timeout: Optional timeout in seconds
        :return: Received message
        :raises ConnectionClosed: If connection is closed
        :raises queue.Empty: If timeout occurs
        """
        if self.state.state == State.CLOSED:
            raise ConnectionClosed(self.state.close_code, self.state.close_reason)

        return self._message_queue.get(timeout=timeout)

    def send_message(self, message: Union[str, bytes]) -> None:
        """
        Send a message.

        :param message: Message to send
        :raises ConnectionClosed: If connection is closed
        :raises TypeError: If message type is invalid
        """
        if isinstance(message, str):
            frame = Frame(True, Opcode.TEXT, message.encode())
        elif isinstance(message, (bytes, bytearray, memoryview)):
            frame = Frame(True, Opcode.BINARY, message)
        else:
            raise TypeError("Message must be str or bytes-like object")

        self.send_frame(frame)

    def ping(self, data: BytesLike = b"") -> None:
        """
        Send a ping frame.

        :param data: Optional ping payload
        :raises ConnectionClosed: If connection is closed
        """
        if len(data) > 125:
            raise ValueError("Ping payload too long")

        payload = bytes(data)
        self._pending_pings.add(payload)
        frame = Frame(True, Opcode.PING, payload)
        self.send_frame(frame)

    def pong(self, data: BytesLike = b"") -> None:
        """
        Send a pong frame.

        :param data: Optional pong payload
        :raises ConnectionClosed: If connection is closed
        """
        if len(data) > 125:
            raise ValueError("Pong payload too long")

        frame = Frame(True, Opcode.PONG, bytes(data))
        self.send_frame(frame)

    def close(self, code: int = CloseCode.NORMAL, reason: str = "") -> None:
        """
        Initiate or complete the closing handshake.

        :param code: Close status code
        :param reason: Close reason
        :raises ConnectionClosed: If connection is already closed
        """
        if self.state.state == State.CLOSED:
            raise ConnectionClosed(self.state.close_code, self.state.close_reason)

        if not self._close_frame_sent:
            frame = Frame(True, Opcode.CLOSE, encode_close_payload(code, reason))
            self.send_frame(frame)
            self._close_frame_sent = True

        if self._close_frame_received:
            self.state.transition(State.CLOSED, code, reason)
        else:
            self.state.transition(State.CLOSING)

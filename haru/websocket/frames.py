from __future__ import annotations

import enum
import struct
from typing import NamedTuple, Optional, Tuple, Union

from .exceptions import FrameError, PayloadError
from .utils import BytesLike, apply_mask

__all__ = [
    "Frame",
    "Opcode",
    "FrameHeader",
    "parse_frame",
    "create_frame",
]


class Opcode(enum.IntEnum):
    """
    WebSocket frame opcodes as defined in RFC 6455.

    .. note::
        Reference: https://tools.ietf.org/html/rfc6455#section-5.2
    """

    CONTINUATION = 0x0
    TEXT = 0x1
    BINARY = 0x2
    CLOSE = 0x8
    PING = 0x9
    PONG = 0xA


# Frame type constants for internal use
CONTROL_FRAMES = {Opcode.CLOSE, Opcode.PING, Opcode.PONG}
DATA_FRAMES = {Opcode.CONTINUATION, Opcode.TEXT, Opcode.BINARY}


class CloseCode(enum.IntEnum):
    """
    WebSocket close codes as defined in RFC 6455.

    .. note::
        Reference: https://tools.ietf.org/html/rfc6455#section-7.4.1
    """

    NORMAL = 1000
    GOING_AWAY = 1001
    PROTOCOL_ERROR = 1002
    UNSUPPORTED_DATA = 1003
    NO_STATUS_RECEIVED = 1005
    ABNORMAL_CLOSURE = 1006
    INVALID_PAYLOAD = 1007
    POLICY_VIOLATION = 1008
    MESSAGE_TOO_BIG = 1009
    MANDATORY_EXTENSION = 1010
    INTERNAL_ERROR = 1011
    SERVICE_RESTART = 1012
    TRY_AGAIN_LATER = 1013
    BAD_GATEWAY = 1014
    TLS_HANDSHAKE_FAILED = 1015


class FrameHeader(NamedTuple):
    """
    WebSocket frame header information.

    .. note::
        This class is used internally for parsing and creating frames.
    """

    fin: bool
    rsv1: bool
    rsv2: bool
    rsv3: bool
    opcode: Opcode
    masked: bool
    payload_length: int
    mask_key: Optional[bytes]


class Frame:
    """
    WebSocket frame representation.

    :param fin: Whether this is the final frame in a message
    :param opcode: Frame opcode (see :class:`Opcode`)
    :param payload: Frame payload
    :param rsv1: Reserved bit 1
    :param rsv2: Reserved bit 2
    :param rsv3: Reserved bit 3
    :raises FrameError: If frame parameters are invalid
    """

    __slots__ = ("fin", "opcode", "payload", "rsv1", "rsv2", "rsv3")

    def __init__(
        self,
        fin: bool,
        opcode: Union[Opcode, int],
        payload: BytesLike,
        rsv1: bool = False,
        rsv2: bool = False,
        rsv3: bool = False,
    ) -> None:
        self.fin = fin
        self.opcode = Opcode(opcode)
        self.payload = bytes(payload)
        self.rsv1 = rsv1
        self.rsv2 = rsv2
        self.rsv3 = rsv3
        self._validate()

    def _validate(self) -> None:
        """
        Validate frame according to RFC 6455.

        :raises FrameError: If frame is invalid
        """
        if self.opcode not in list(Opcode):
            raise FrameError(f"Invalid opcode: {self.opcode}")

        if self.opcode in CONTROL_FRAMES:
            if not self.fin:
                raise FrameError("Control frames must not be fragmented")
            if len(self.payload) > 125:
                raise FrameError("Control frame payloads must not exceed 125 bytes")

        if any((self.rsv1, self.rsv2, self.rsv3)):
            raise FrameError("Reserved bits must be 0 unless negotiated otherwise")

    def serialize(self, *, mask: bool = False) -> bytes:
        """
        Serialize frame to bytes according to RFC 6455.

        :param mask: Whether to mask the frame (required for client-to-server frames)
        :return: Serialized frame as bytes
        """
        header_bytes = bytearray()

        # First byte: FIN + RSV + Opcode
        first_byte = (
            (0b10000000 if self.fin else 0) | (0b01000000 if self.rsv1 else 0) | (0b00100000 if self.rsv2 else 0) | (0b00010000 if self.rsv3 else 0) | self.opcode
        )
        header_bytes.append(first_byte)

        # Second byte: Mask + Payload length
        payload_length = len(self.payload)
        if payload_length <= 125:
            second_byte = payload_length
        elif payload_length <= 65535:
            second_byte = 126
        else:
            second_byte = 127

        if mask:
            second_byte |= 0b10000000

        header_bytes.append(second_byte)

        # Extended payload length
        if payload_length > 125:
            if payload_length <= 65535:
                header_bytes.extend(struct.pack("!H", payload_length))
            else:
                header_bytes.extend(struct.pack("!Q", payload_length))

        # Masking key and payload
        if mask:
            import os
            mask_key = os.urandom(4)
            header_bytes.extend(mask_key)
            payload = apply_mask(self.payload, mask_key)
        else:
            payload = self.payload

        return bytes(header_bytes) + payload

    @property
    def is_control(self) -> bool:
        """Whether this is a control frame."""
        return self.opcode in CONTROL_FRAMES

    @property
    def is_data(self) -> bool:
        """Whether this is a data frame."""
        return self.opcode in DATA_FRAMES

    def __repr__(self) -> str:
        return (
            f"Frame(fin={self.fin}, opcode={self.opcode.name}, "
            f"payload={len(self.payload)} bytes, "
            f"rsv1={self.rsv1}, rsv2={self.rsv2}, rsv3={self.rsv3})"
        )


def parse_frame(data: Union[bytes, bytearray], *, max_size: Optional[int] = None) -> Tuple[Frame, int]:
    """
    Parse a WebSocket frame from bytes.

    :param data: Raw frame data
    :param max_size: Maximum allowed payload size
    :return: Tuple of (parsed frame, number of bytes consumed)
    :raises FrameError: If frame format is invalid
    :raises PayloadError: If payload exceeds max_size
    """
    if len(data) < 2:
        raise FrameError("Frame too short")

    # Parse first byte
    first_byte = data[0]
    fin = bool(first_byte & 0b10000000)
    rsv1 = bool(first_byte & 0b01000000)
    rsv2 = bool(first_byte & 0b00100000)
    rsv3 = bool(first_byte & 0b00010000)
    opcode = first_byte & 0b00001111

    try:
        opcode = Opcode(opcode)
    except ValueError:
        raise FrameError(f"Invalid opcode: {opcode}")

    # Parse second byte
    second_byte = data[1]
    masked = bool(second_byte & 0b10000000)
    payload_length = second_byte & 0b01111111

    # Current position in data
    pos = 2

    # Handle extended payload length
    if payload_length == 126:
        if len(data) < pos + 2:
            raise FrameError("Frame too short for 2-byte payload length")
        payload_length = struct.unpack("!H", data[pos:pos + 2])[0]
        pos += 2
    elif payload_length == 127:
        if len(data) < pos + 8:
            raise FrameError("Frame too short for 8-byte payload length")
        payload_length = struct.unpack("!Q", data[pos:pos + 8])[0]
        pos += 8

    if max_size is not None and payload_length > max_size:
        raise PayloadError(f"Payload length {payload_length} exceeds maximum size {max_size}")

    # Handle mask
    mask_key = None
    if masked:
        if len(data) < pos + 4:
            raise FrameError("Frame too short for mask key")
        mask_key = data[pos:pos + 4]
        pos += 4

    # Check if we have the full payload
    if len(data) < pos + payload_length:
        raise FrameError("Frame too short for payload")

    # Extract payload
    payload = data[pos:pos + payload_length]
    if masked:
        payload = apply_mask(payload, mask_key)

    frame = Frame(
        fin=fin,
        opcode=opcode,
        payload=payload,
        rsv1=rsv1,
        rsv2=rsv2,
        rsv3=rsv3,
    )

    return frame, pos + payload_length


def create_frame(
    opcode: Union[Opcode, int],
    payload: BytesLike,
    *,
    fin: bool = True,
    rsv1: bool = False,
    rsv2: bool = False,
    rsv3: bool = False,
    mask: bool = False,
) -> bytes:
    """
    Create a WebSocket frame.

    This is a convenience function that creates and serializes a frame in one step.

    :param opcode: Frame opcode
    :param payload: Frame payload
    :param fin: Whether this is the final frame in a message
    :param rsv1: Reserved bit 1
    :param rsv2: Reserved bit 2
    :param rsv3: Reserved bit 3
    :param mask: Whether to mask the frame
    :return: Serialized frame as bytes
    :raises FrameError: If frame parameters are invalid
    """
    frame = Frame(
        fin=fin,
        opcode=opcode,
        payload=payload,
        rsv1=rsv1,
        rsv2=rsv2,
        rsv3=rsv3,
    )
    return frame.serialize(mask=mask)


def encode_close_payload(code: int, reason: str = "") -> bytes:
    """
    Encode close frame payload according to RFC 6455.

    :param code: Close status code
    :param reason: Close reason
    :return: Encoded payload
    :raises ValueError: If code or reason is invalid
    """
    if not 1000 <= code <= 4999:
        raise ValueError(f"Invalid close code: {code}")

    reason_bytes = reason.encode("utf-8")
    if len(reason_bytes) > 123:  # 125 - 2 bytes for code
        raise ValueError("Close reason too long")

    return struct.pack("!H", code) + reason_bytes


def decode_close_payload(payload: bytes) -> Tuple[int, str]:
    """
    Decode close frame payload according to RFC 6455.

    :param payload: Raw payload
    :return: Tuple of (status code, reason string)
    :raises ValueError: If payload format is invalid
    """
    if not payload:
        return CloseCode.NORMAL, ""

    if len(payload) < 2:
        raise ValueError("Close payload too short")

    code = struct.unpack("!H", payload[:2])[0]
    reason = payload[2:].decode("utf-8")

    if not 1000 <= code <= 4999:
        raise ValueError(f"Invalid close code: {code}")

    return code, reason

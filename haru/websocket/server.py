from __future__ import annotations

import logging
import socket
import ssl
import threading
import weakref
from typing import Any, Callable, Optional, Set, Union

from .exceptions import ConnectionClosed, HandshakeError
from .frames import CloseCode
from .http import Headers, build_response, parse_request, validate_handshake
from .protocol import State, WebSocketProtocol
from .utils import compute_accept_key

__all__ = ["WebSocketServer", "WebSocketHandler", "serve", "serve_ssl"]


class WebSocketHandler:
    """
    Handler for a single WebSocket connection.

    :param sock: Connected socket
    :param server: Server instance
    :param handler: User-provided connection handler
    :param logger: Logger instance
    :param max_size: Maximum message size
    """

    def __init__(
        self,
        sock: socket.socket,
        server: WebSocketServer,
        handler: Callable[[WebSocketHandler], None],
        logger: Optional[logging.Logger] = None,
        max_size: Optional[int] = None,
    ) -> None:
        self.socket = sock
        self.server = server
        self.handler = handler
        self.protocol = WebSocketProtocol(logger=logger, max_size=max_size)

        # Set TCP_NODELAY to disable Nagle's algorithm
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        self._thread: Optional[threading.Thread] = None
        self._running = True
        self._send_lock = threading.Lock()
        self._close_event = threading.Event()

    def start(self) -> None:
        """Start handling the connection in a new thread."""
        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True
        self._thread.start()

    def _run(self) -> None:
        """Main connection handler loop."""
        try:
            self._handle_connection()
        except Exception:
            self.protocol.logger.exception("Unhandled error in connection handler")
        finally:
            self._cleanup()

    def _handle_connection(self) -> None:
        """Handle the WebSocket connection lifecycle."""
        try:
            # Perform opening handshake
            self._handle_handshake()

            if self.protocol.state.state != State.OPEN:
                return

            # Start reader thread
            reader_thread = threading.Thread(target=self._reader_loop)
            reader_thread.daemon = True
            reader_thread.start()

            try:
                # Run user handler
                self.handler(self)
            except Exception:
                self.protocol.logger.exception("Error in connection handler")
                self.close(CloseCode.INTERNAL_ERROR)
            else:
                # Normal closure
                self.close(CloseCode.NORMAL)

            # Wait for reader thread
            reader_thread.join()

        except ConnectionClosed:
            pass
        except Exception:
            self.protocol.logger.error("Connection error", exc_info=True)
            self.close(CloseCode.INTERNAL_ERROR)

    def _handle_handshake(self) -> None:
        """
        Perform the WebSocket opening handshake.

        :raises HandshakeError: If handshake fails
        """
        # Read HTTP request
        data = self.socket.recv(65536)
        if not data:
            raise HandshakeError("Client disconnected during handshake")

        try:
            request, _ = parse_request(data)
        except Exception as exc:
            raise HandshakeError("Invalid HTTP request") from exc

        # Validate WebSocket headers
        try:
            validate_handshake(request.headers, client_mode=False)
        except Exception as exc:
            raise HandshakeError("Invalid WebSocket headers") from exc

        key = request.headers["Sec-WebSocket-Key"]
        accept = compute_accept_key(key)

        # Build response
        headers = Headers(
            [
                ("Upgrade", "websocket"),
                ("Connection", "Upgrade"),
                ("Sec-WebSocket-Accept", accept),
            ]
        )

        response = build_response(101, headers)

        with self._send_lock:
            self.socket.sendall(response)

        # Update protocol state
        self.protocol.state.transition(State.OPEN)

    def _reader_loop(self) -> None:
        """Read incoming data from the socket."""
        try:
            while self._running:
                try:
                    data = self.socket.recv(65536)
                    if not data:
                        break

                    self.protocol.receive_data(data)

                    # Send any queued outgoing data
                    outgoing = self.protocol.get_outgoing_data()
                    if outgoing:
                        with self._send_lock:
                            self.socket.sendall(outgoing)

                except ConnectionClosed:
                    break
                except Exception:
                    self.protocol.logger.exception("Error in reader loop")
                    self.close(CloseCode.INTERNAL_ERROR)
                    break
        finally:
            self._close_event.set()

    def send(self, message: Union[str, bytes]) -> None:
        """
        Send a message to the client.

        :param message: Message to send
        :raises ConnectionClosed: If connection is closed
        """
        self.protocol.send_message(message)
        outgoing = self.protocol.get_outgoing_data()
        if outgoing:
            with self._send_lock:
                self.socket.sendall(outgoing)

    def close(self, code: int = CloseCode.NORMAL, reason: str = "") -> None:
        """
        Close the connection.

        :param code: Close status code
        :param reason: Close reason
        """
        if not self._running:
            return

        self._running = False

        try:
            self.protocol.close(code, reason)
            outgoing = self.protocol.get_outgoing_data()
            if outgoing:
                with self._send_lock:
                    self.socket.sendall(outgoing)
        except Exception:
            self.protocol.logger.exception("Error during close")

        # Wait for reader thread to finish
        self._close_event.wait(timeout=5.0)

        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass

        try:
            self.socket.close()
        except Exception:
            pass

    def ping(self, data: bytes = b"") -> None:
        """
        Send a ping frame.

        :param data: Optional ping payload
        :raises ConnectionClosed: If connection is closed
        """
        self.protocol.ping(data)
        outgoing = self.protocol.get_outgoing_data()
        if outgoing:
            with self._send_lock:
                self.socket.sendall(outgoing)

    def recv(self, timeout: Optional[float] = None) -> Union[str, bytes]:
        """
        Receive a message.

        :param timeout: Optional timeout in seconds
        :return: Received message
        :raises ConnectionClosed: If connection is closed
        :raises queue.Empty: If timeout occurs
        """
        return self.protocol.receive_message(timeout=timeout)

    @property
    def closed(self) -> bool:
        """Whether the connection is closed."""
        return not self._running

    def _cleanup(self) -> None:
        """Clean up resources."""
        self._running = False
        self.server._remove_handler(self)

        try:
            self.socket.close()
        except Exception:
            pass


class WebSocketServer:
    """
    WebSocket server implementation.

    :param handler: Connection handler callable
    :param host: Host to bind to
    :param port: Port to bind to
    :param ssl_context: Optional SSL context for WSS
    :param logger: Logger instance
    :param max_size: Maximum message size
    """

    def __init__(
        self,
        handler: Callable[[WebSocketHandler], None],
        host: str = "localhost",
        port: int = 8765,
        ssl_context: Optional[ssl.SSLContext] = None,
        logger: Optional[logging.Logger] = None,
        max_size: Optional[int] = None,
    ):
        if logger is None:
            logger = logging.getLogger("simple_websocket.server")

        self.handler = handler
        self.host = host
        self.port = port
        self.ssl_context = ssl_context
        self.logger = logger
        self.max_size = max_size

        self._socket: Optional[socket.socket] = None
        self._handlers: weakref.WeakSet[WebSocketHandler] = weakref.WeakSet()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def serve_forever(self) -> None:
        """Start the server."""
        if self._running:
            return

        try:
            # Create server socket
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind((self.host, self.port))
            self._socket.listen(128)

            self._running = True
            self.logger.info("Server starting on %s:%d", self.host, self.port)

            while self._running:
                try:
                    sock, addr = self._socket.accept()
                    if self.ssl_context:
                        sock = self.ssl_context.wrap_socket(sock, server_side=True)

                    self.logger.info("New connection from %s:%d", *addr)

                    handler = WebSocketHandler(
                        sock,
                        self,
                        self.handler,
                        self.logger,
                        self.max_size,
                    )
                    self._handlers.add(handler)
                    handler.start()

                except Exception:
                    self.logger.exception("Error accepting connection")

        except Exception:
            self.logger.exception("Server error")
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Stop the server and close all connections."""
        if not self._running:
            return

        self._running = False

        # Close server socket
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass

        # Close all handlers
        for handler in list(self._handlers):
            try:
                handler.close()
            except Exception:
                pass

    def _remove_handler(self, handler: WebSocketHandler) -> None:
        """Remove a connection handler."""
        self._handlers.discard(handler)

    @property
    def handlers(self) -> Set[WebSocketHandler]:
        """Set of active connection handlers."""
        return set(self._handlers)

    def broadcast(self, message: Union[str, bytes]) -> None:
        """
        Broadcast a message to all connected clients.

        :param message: Message to broadcast
        """
        for handler in self.handlers:
            try:
                handler.send(message)
            except Exception:
                self.logger.exception("Error broadcasting to client")


def serve(
    handler: Callable[[WebSocketHandler], None],
    host: str = "localhost",
    port: int = 8765,
    **kwargs: Any,
) -> WebSocketServer:
    """
    Create and start a WebSocket server.

    :param handler: Connection handler callable
    :param host: Host to bind to
    :param port: Port to bind to
    :param kwargs: Additional arguments for WebSocketServer
    :return: Server instance
    """
    server = WebSocketServer(handler, host, port, **kwargs)

    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    server._thread = thread

    return server


def serve_ssl(
    handler: Callable[[WebSocketHandler], None],
    certfile: str,
    keyfile: Optional[str] = None,
    password: Optional[str] = None,
    host: str = "localhost",
    port: int = 8765,
    **kwargs: Any,
) -> WebSocketServer:
    """
    Create and start a secure WebSocket server (WSS).

    :param handler: Connection handler callable
    :param certfile: Path to certificate file
    :param keyfile: Path to private key file
    :param password: Password for private key
    :param host: Host to bind to
    :param port: Port to bind to
    :param kwargs: Additional arguments for WebSocketServer
    :return: Server instance
    """
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile, keyfile, password)

    return serve(handler, host=host, port=port, ssl_context=ssl_context, **kwargs)

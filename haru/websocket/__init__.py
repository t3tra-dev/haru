from __future__ import annotations

import asyncio
import functools
import logging
import ssl
import threading
from typing import Any, Awaitable, Callable, Dict, Optional, Set, Union
from . import exceptions
from . import utils

from .exceptions import ConnectionClosed, SecurityError
from .protocol import State, WebSocketProtocol
from .server import WebSocketServer as BaseWebSocketServer
from .utils import Deadline

__all__ = [
    "exceptions",
    "utils",
    "WebSocketServerProtocol",
    "upgrade_websocket",
]

logger = logging.getLogger(__name__)

MAX_CONNECTIONS = 1000
HANDSHAKE_TIMEOUT = 30
IDLE_TIMEOUT = 300
MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB
RATE_LIMIT_MESSAGES = 100
RATE_LIMIT_WINDOW = 10  # seconds


class WebSocketServerProtocol(WebSocketProtocol):
    """
    WebSocket protocol implementation for Haru framework.

    :param max_size: Maximum message size in bytes
    :param logger: Logger instance
    """

    def __init__(
        self,
        max_size: Optional[int] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        if logger is None:
            logger = logging.getLogger("haru.websocket")

        super().__init__(
            logger=logger, max_size=min(max_size or MAX_MESSAGE_SIZE, MAX_MESSAGE_SIZE)
        )

        self.application: Any = None
        self.path: str = ""
        self.query_string: str = ""
        self.headers: Dict[str, str] = {}

        self._message_count = 0
        self._message_time = 0.0

    async def send(self, message: Union[str, bytes]) -> None:
        """
        Send a message to the client.

        :param message: Message to send
        :raises ConnectionClosed: If connection is closed
        :raises SecurityError: If rate limit is exceeded
        """
        if self.state != State.OPEN:
            raise ConnectionClosed(code=1006, reason="Connection is not open")

        current_time = asyncio.get_event_loop().time()
        if current_time - self._message_time >= RATE_LIMIT_WINDOW:
            self._message_count = 0
            self._message_time = current_time

        self._message_count += 1
        if self._message_count > RATE_LIMIT_MESSAGES:
            raise SecurityError("Rate limit exceeded")

        if isinstance(message, str):
            size = len(message.encode("utf-8"))
        else:
            size = len(message)

        if size > self.max_size:
            raise ValueError(f"Message size exceeds limit: {size} > {self.max_size}")

        await super().send(message)

    async def receive(self) -> Union[str, bytes]:
        """
        Receive a message from the client.

        :return: Received message
        :raises ConnectionClosed: If connection is closed
        """
        if self.state != State.OPEN:
            raise ConnectionClosed(code=1006, reason="Connection is not open")

        return await super().receive()

    async def close(self, code: int = 1000, reason: str = "") -> None:
        """
        Close the WebSocket connection.

        :param code: Status code for closure
        :param reason: Reason for closure
        """
        try:
            await super().close(code, reason)
        except Exception as exc:
            self.logger.error(f"Error during connection close: {exc}")
            raise


class WebSocketServer(BaseWebSocketServer):
    """
    WebSocket server implementation for Haru framework.

    :param host: Host to bind to
    :param port: Port to bind to
    :param ssl_context: Optional SSL context
    """

    def __init__(
        self,
        host: str,
        port: int,
        ssl_context: Optional[ssl.SSLContext] = None,
    ) -> None:
        super().__init__(host=host, port=port, ssl_context=ssl_context)

        self.loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        self.thread: Optional[threading.Thread] = None
        self.routes: Dict[str, Callable[[WebSocketServerProtocol], Awaitable[None]]] = (
            {}
        )

        self._active_connections: Set[WebSocketServerProtocol] = set()
        self._connections_lock = threading.Lock()

        self._running = False
        self._shutdown_event = threading.Event()

    def add_route(
        self, path: str, handler: Callable[[WebSocketServerProtocol], Awaitable[None]]
    ) -> None:
        """
        Register a WebSocket route.

        :param path: URL path
        :param handler: Handler function
        """
        self.routes[path] = handler

    async def _connection_handler(
        self, protocol: WebSocketServerProtocol, path: str
    ) -> None:
        """
        Handle a WebSocket connection.

        :param protocol: WebSocket protocol instance
        :param path: Request path
        """
        handler = self.routes.get(path)
        if not handler:
            await protocol.close(1003, f"No handler found for path: {path}")
            return

        with self._connections_lock:
            if len(self._active_connections) >= MAX_CONNECTIONS:
                await protocol.close(1013, "Server is at capacity")
                return
            self._active_connections.add(protocol)

        try:
            deadline = Deadline(HANDSHAKE_TIMEOUT)
            await asyncio.wait_for(handler(protocol), timeout=deadline.remaining())
        except asyncio.TimeoutError:
            await protocol.close(1001, "Operation timed out")
        except Exception as exc:
            self.logger.error(f"Error in WebSocket handler: {exc}")
            await protocol.close(1011, "Internal server error")
        finally:
            with self._connections_lock:
                self._active_connections.discard(protocol)

    def start(self) -> None:
        """Start the WebSocket server."""
        if self._running:
            return

        self._running = True
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()

    def shutdown(self) -> None:
        """Shutdown the WebSocket server."""
        if not self._running:
            return

        self._running = False
        self._shutdown_event.set()

        for protocol in list(self._active_connections):
            try:
                asyncio.run_coroutine_threadsafe(
                    protocol.close(1001, "Server shutting down"), self.loop
                )
            except Exception:
                pass

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)

        try:
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.loop.close()
        except Exception:
            pass


def upgrade_websocket(
    func: Callable[[WebSocketServerProtocol], Awaitable[None]]
) -> Callable:
    """
    Decorator to mark a function as a WebSocket handler.

    :param func: Handler function
    :return: Decorated function
    """

    @functools.wraps(func)
    async def wrapper(websocket: WebSocketServerProtocol) -> None:
        try:
            await func(websocket)
        except ConnectionClosed:
            pass
        except Exception as exc:
            logger.exception("WebSocket handler error")
            try:
                await websocket.close(1011, str(exc))
            except Exception:
                pass
        finally:
            if websocket.state != State.CLOSED:
                await websocket.close(1000, "Handler completed")

    wrapper.is_websocket = True  # type: ignore
    return wrapper

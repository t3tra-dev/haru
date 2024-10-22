"""
This module provides WebSocket support for the Haru web framework using the 'websockets' library.
It defines the `WebSocketServer` class, which manages the WebSocket server running in a separate
thread when the application is in WSGI mode.

The module also provides the `upgrade_websocket` decorator to register WebSocket handlers.

Dependencies:
- websockets (Install with 'pip install haru[ws]')
"""

from __future__ import annotations
import asyncio
import threading
import logging
from typing import Callable, Dict, Awaitable, Optional

__all__ = ['WebSocketServerProtocol', 'WebSocketServer', 'upgrade_websocket']

logger = logging.getLogger(__name__)

try:
    import websockets
    from websockets.server import WebSocketServerProtocol as _WebSocketServerProtocol
except ImportError:
    websockets = None
    _WebSocketServerProtocol = None


class WebSocketServerProtocol(_WebSocketServerProtocol):
    pass


def upgrade_websocket(func: Callable[[WebSocketServerProtocol], Awaitable[None]]) -> Callable:
    """
    Decorator to register a WebSocket route handler.

    :param func: The asynchronous function that handles the WebSocket connection.
    :type func: Callable[[WebSocketServerProtocol], Awaitable[None]]
    :return: The original function marked as a WebSocket handler.
    :rtype: Callable
    :raises ImportError: If the 'websockets' library is not installed.
    """
    if websockets is None:
        raise ImportError(
            "The 'websockets' library is required for WebSocket support. Install with 'pip install haru[ws]'"
        )
    func.is_websocket = True  # Mark the function as a WebSocket handler
    return func


class WebSocketServer:
    """
    Manages the WebSocket server running in a separate thread.

    This class handles the registration of WebSocket routes and starts the WebSocket server
    using the 'websockets' library in a separate thread to allow asynchronous communication
    while the main application runs in WSGI mode.

    :param host: The host address to bind the WebSocket server to.
    :type host: str
    :param port: The port number to bind the WebSocket server to.
    :type port: int
    """

    def __init__(self, host: str, port: int) -> None:
        self.host: str = host
        self.port: int = port
        self.loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        self.thread: Optional[threading.Thread] = None
        self.routes: Dict[str, Callable[[WebSocketServerProtocol], Awaitable[None]]] = {}

    def add_route(self, path: str, handler: Callable[[WebSocketServerProtocol], Awaitable[None]]) -> None:
        """
        Register a WebSocket route with its handler.

        :param path: The URL path to bind the WebSocket handler.
        :type path: str
        :param handler: The asynchronous function that handles the WebSocket connection.
        :type handler: Callable[[WebSocketServerProtocol], Awaitable[None]]
        """
        self.routes[path] = handler

    def start(self) -> None:
        """
        Start the WebSocket server in a separate thread.
        """
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()

    def _run_server(self) -> None:
        """
        The target function for the server thread.

        Sets up the event loop and runs the WebSocket server.
        """
        asyncio.set_event_loop(self.loop)
        start_server = websockets.serve(self._handler, self.host, self.port)
        self.loop.run_until_complete(start_server)
        logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
        self.loop.run_forever()

    async def _handler(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """
        Handles incoming WebSocket connections by dispatching them to the appropriate handler.

        :param websocket: The WebSocket connection instance.
        :type websocket: WebSocketServerProtocol
        :param path: The URL path of the incoming connection.
        :type path: str
        """
        handler = self.routes.get(path)
        if handler:
            try:
                await handler(websocket)
            except Exception as e:
                logger.error(f"Error in WebSocket handler for path '{path}': {e}")
                await websocket.close(code=1011)
        else:
            logger.warning(f"No WebSocket handler found for path '{path}'. Connection will be closed.")
            await websocket.close()

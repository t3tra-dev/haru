"""
This module provides WebSocket support for the Haru web framework using the 'websockets' library.
"""

from typing import Callable, Awaitable, Any
import asyncio
import threading
import logging

__all__ = ['upgrade_websocket']

logger = logging.getLogger(__name__)

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
except ImportError:
    websockets = None
    WebSocketServerProtocol = None


def upgrade_websocket(func: Callable[[Any], Awaitable[None]]) -> Callable:
    """
    Decorator to register a WebSocket route handler.

    :param func: The asynchronous function that handles the WebSocket connection.
    :type func: Callable
    :return: The original function.
    :rtype: Callable
    """
    if websockets is None:
        raise ImportError("The 'websockets' library is required for WebSocket support. Install with 'pip install haru[ws]'")
    func.is_websocket = True  # Mark the function as a WebSocket handler
    return func


class WebSocketServer:
    """
    Manages the WebSocket server running in a separate thread.
    """

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.loop = None
        self.thread = None
        self.server = None
        self.routes = {}

    def add_route(self, path: str, handler: Callable[[WebSocketServerProtocol, str], Awaitable[None]]):  # type: ignore
        self.routes[path] = handler

    def start(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()

    def _run_server(self):
        asyncio.set_event_loop(self.loop)
        start_server = websockets.serve(self._handler, self.host, self.port)
        self.loop.run_until_complete(start_server)
        logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
        self.loop.run_forever()

    async def _handler(self, websocket: WebSocketServerProtocol, path: str):  # type: ignore
        handler = self.routes.get(path)
        if handler:
            await handler(websocket)
        else:
            await websocket.close()

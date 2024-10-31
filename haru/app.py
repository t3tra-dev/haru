"""
This module defines the core application class for the Haru web framework.
It provides functionality to handle routing, middleware management, and request/response processing.
"""

import asyncio
import os
from typing import Callable, Dict, List, Any, Optional, Awaitable, Set, Tuple, Type, TypeVar, Union

from .router import Router
from .request import Request
from .response import Response
from .exceptions import (
    HTTPException,
    NotFound,
    MethodNotAllowed,
    StaticRouteOverlapError,
)
from .blueprint import Blueprint
from .middleware import Middleware
try:
    from .websocket import WebSocketServer, upgrade_websocket
    websockets_available = True
except ImportError:
    WebSocketServer = None  # type: ignore
    upgrade_websocket = None  # type: ignore
    websockets_available = False

__all__ = ['Haru']

T = TypeVar('T')
MiddlewareType = TypeVar('MiddlewareType', bound=Middleware)


class Haru:
    """
    The main application class of the Haru web framework. This class is responsible for
    managing routes, handling HTTP requests, and middleware processing. It supports both
    ASGI and WSGI interfaces, allowing flexible deployment options. It also integrates
    WebSocket support when running in WSGI mode by starting a separate WebSocket server.
    """

    def __init__(self, import_name: str, asgi: bool = False):
        """
        Initialize the Haru application.

        :param import_name: The name of the module or package for the application.
        :type import_name: str
        :param asgi: Flag to enable ASGI mode.
        :type asgi: bool
        """
        self.import_name: str = import_name
        self.router: Router = Router()
        self.blueprints: List[Blueprint] = []
        self.middleware: List[Middleware] = []
        self.error_handlers: Dict[Union[int, Type[Exception]], Callable] = {}
        self.asgi: bool = asgi
        self.websocket_server: Optional[WebSocketServer] = None  # type: ignore
        self.websocket_routes: Dict[str, Callable] = {}
        self.static_routes: List[Tuple[str, str, Optional[List[str]]]] = []  # (path, dir, ignore)

    def route(self, path: str, methods: Optional[List[str]] = None) -> Callable:
        """
        Define a new route in the application.

        :param path: The URL path to bind the route.
        :type path: str
        :param methods: A list of HTTP methods allowed for this route (GET, POST, etc.).
        :type methods: Optional[List[str]]
        :return: A decorator to wrap the route handler function.
        :rtype: Callable
        """
        def decorator(func: Callable) -> Callable:
            if getattr(func, 'is_websocket', False):
                # Register WebSocket route
                if not websockets_available:
                    raise ImportError(
                        "The 'websockets' library is required for WebSocket support. Install with 'pip install haru[ws]'"
                    )
                self.websocket_routes[path] = func
            else:
                self.router.add_route(path, func, methods)
            return func
        return decorator

    def errorhandler(self, exception_or_status_code: Union[int, Type[Exception]]) -> Callable:
        """
        Register an error handler for a specific exception or HTTP status code.

        :param exception_or_status_code: The exception class or HTTP status code to handle.
        :type exception_or_status_code: Union[int, Type[Exception]]
        :return: A decorator to wrap the error handler function.
        :rtype: Callable
        """
        def decorator(func: Callable) -> Callable:
            self.error_handlers[exception_or_status_code] = func
            return func
        return decorator

    def register_blueprint(self, blueprint: Blueprint) -> None:
        """
        Register a blueprint with the application.

        :param blueprint: The blueprint to be registered.
        :type blueprint: Blueprint
        """
        blueprint.register(self)
        self.blueprints.append(blueprint)

    def add_middleware(self, middleware: Middleware) -> None:
        """
        Add application-level middleware.

        :param middleware: The middleware to be added.
        :type middleware: Middleware
        """
        self.middleware.append(middleware)

    def remove_middleware(self, middleware: Middleware) -> None:
        """
        Remove application-level middleware.

        :param middleware: The middleware to be removed.
        :type middleware: Middleware
        """
        if middleware in self.middleware:
            self.middleware.remove(middleware)

    def get_middleware(self, middleware_class: Type[MiddlewareType]) -> Optional[MiddlewareType]:
        """
        Retrieve middleware by its class from the application and its blueprints.

        :param middleware_class: The class of the middleware to retrieve.
        :type middleware_class: Type[MiddlewareType]
        :return: The middleware instance if found, or None if not found.
        :rtype: Optional[MiddlewareType]
        """
        for mw in self.get_middlewares():
            if isinstance(mw, middleware_class):
                return mw  # type: ignore
        return None

    def get_middlewares(self) -> List[Middleware]:
        """
        Retrieve all middleware instances from the application and its blueprints.

        :return: A list of middleware instances.
        :rtype: List[Middleware]
        """
        all_middlewares = self.middleware.copy()
        for blueprint in self.blueprints:
            all_middlewares.extend(blueprint.middleware)
        return all_middlewares

    def add_static_router(self, dir: str, path: Optional[str] = '/static', ignore: Optional[List[str]] = None) -> None:
        """
        Add a static file router to serve files from a directory.

        :param dir: The directory to serve files from.
        :type dir: str
        :param path: The URL path prefix to serve the files at.
        :type path: Optional[str]
        :param ignore: A list of file or directory names to ignore.
        :type ignore: Optional[List[str]]
        :raises ValueError: If dir or path is invalid.
        """
        if not os.path.isdir(dir):
            raise ValueError(f"The directory '{dir}' does not exist or is not a directory.")
        if not path.startswith('/'):
            raise ValueError("The path must start with '/'.")

        self.static_routes.append((path.rstrip('/'), dir, ignore))

    def _check_static_route_overlaps(self) -> None:
        """
        Check for overlaps in static routes.

        :raises StaticRouteOverlapError: If overlapping static routes are detected.
        """
        path_set: Set[str] = set()
        for path, _, _ in self.static_routes:
            if path in path_set:
                raise StaticRouteOverlapError(f"Static route path '{path}' is already registered.")
            path_set.add(path)

    def run(self, host: str = '127.0.0.1', port: int = 8000, ws_host: Optional[str] = None, ws_port: Optional[int] = None) -> None:
        """
        Start the HTTP server and run the application. If WebSocket routes are registered,
        start a separate WebSocket server in a different thread.

        :param host: The host address to bind the HTTP server to.
        :type host: str
        :param port: The port number to bind the HTTP server to.
        :type port: int
        :param ws_host: The host address to bind the WebSocket server to (default is same as HTTP host).
        :type ws_host: Optional[str]
        :param ws_port: The port number to bind the WebSocket server to (default is HTTP port + 1).
        :type ws_port: Optional[int]
        :raises RuntimeError: If ASGI mode is enabled.
        """
        self._check_static_route_overlaps()

        for path, dir, ignore in self.static_routes:
            self._register_static_route(path, dir, ignore)

        if self.asgi:
            raise RuntimeError("ASGI mode is enabled. Use an ASGI server to run the app.")

        if self.websocket_routes:
            # Start WebSocket server
            if not websockets_available:
                raise ImportError(
                    "The 'websockets' library is required for WebSocket support. Install with 'pip install haru[ws]'"
                )
            ws_host = ws_host or host
            ws_port = ws_port or (port + 1)
            self.websocket_server = WebSocketServer(ws_host, ws_port)
            for path, handler in self.websocket_routes.items():
                self.websocket_server.add_route(path, handler)
            self.websocket_server.start()
            print(f"WebSocket server is running on ws://{ws_host}:{ws_port}")

        # Start HTTP server
        from wsgiref.simple_server import make_server
        print(f"Serving HTTP on http://{host}:{port}")
        with make_server(host, port, self.wsgi_app) as httpd:
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("Server is shutting down.")
                httpd.server_close()

    def wsgi_app(self, environ: Dict[str, Any], start_response: Callable) -> List[bytes]:
        """
        WSGI application callable.

        This method handles WSGI requests and sends responses synchronously.
        It ignores WebSocket routes to prevent errors when a client attempts to
        access them via HTTP.

        :param environ: The WSGI environment dictionary.
        :type environ: Dict[str, Any]
        :param start_response: The WSGI start_response callable.
        :type start_response: Callable
        :return: The response body as a list of bytes.
        :rtype: List[bytes]
        """
        try:
            # Read the request body
            content_length = int(environ.get('CONTENT_LENGTH', 0) or 0)
            body = environ['wsgi.input'].read(content_length) if content_length > 0 else b''

            method = environ['REQUEST_METHOD']
            path = environ['PATH_INFO']
            headers = {
                key[5:].replace('_', '-').lower(): value
                for key, value in environ.items() if key.startswith('HTTP_')
            }

            if 'CONTENT_TYPE' in environ:
                headers['content-type'] = environ['CONTENT_TYPE']
            if 'CONTENT_LENGTH' in environ:
                headers['content-length'] = environ['CONTENT_LENGTH']

            client_address = environ.get('REMOTE_ADDR', '')
            request = Request(method=method, path=path, headers=headers, body=body, client_address=client_address)

            # Process the request and match the route
            route, params, allowed_methods = self.router.match(request.path, request.method)
            if route is None:
                if method == 'OPTIONS':
                    allowed_methods = set(allowed_methods)
                    if allowed_methods:
                        status = '200 OK'
                        response_headers = [('Allow', ', '.join(sorted(allowed_methods)))]
                        start_response(status, response_headers)
                        return [b'']
                    else:
                        raise NotFound("Not Found")
                elif allowed_methods:
                    raise MethodNotAllowed(allowed_methods)
                else:
                    raise NotFound("Not Found")

            # Set request parameters from URL path
            request.params = params

            # Middleware processing
            middlewares = self.middleware.copy()
            if route.blueprint:
                middlewares.extend(route.blueprint.middleware)

            for mw in middlewares:
                self._run_middleware_method_sync(mw.before_request, request)

            # Call the route handler and get the result
            result = self._call_route_handler_sync(route.handler, request)

            # Process the result and create a Response object
            if isinstance(result, Response):
                response = result
            elif isinstance(result, tuple):
                content, status_code = result
                response = Response(content, status_code=status_code)
            else:
                response = Response(result)

            for mw in reversed(middlewares):
                middleware_result = self._run_middleware_method_sync(mw.after_request, request, response)
                if middleware_result is not None:
                    response = middleware_result

            for mw in middlewares:
                self._run_middleware_method_sync(mw.before_response, request, response)

            # Send response
            status = f"{response.status_code} {self._http_status_message(response.status_code)}"
            response_headers = list(response.headers.items())
            start_response(status, response_headers)
            content = response.get_content()

            for mw in reversed(middlewares):
                self._run_middleware_method_sync(mw.after_response, request, response)

            return [content]

        except Exception as e:
            # Error handling with correct status code
            response = self._handle_exception(request, e)

            # Send error response
            status = f"{response.status_code} {self._http_status_message(response.status_code)}"
            response_headers = list(response.headers.items())
            start_response(status, response_headers)
            content = response.get_content()
            return [content]

    async def _asgi_app(self, scope: Dict[str, Any], receive: Callable[[], Awaitable[Dict[str, Any]]], send: Callable[[Dict[str, Any]], Awaitable[None]]):
        """
        ASGI entry point for handling requests.

        This method handles ASGI requests and sends responses asynchronously.

        :param scope: The ASGI scope containing request information.
        :type scope: Dict[str, Any]
        :param receive: The receive callable to fetch request body and messages.
        :type receive: Callable
        :param send: The send callable to send the response messages.
        :type send: Callable
        """
        if scope['type'] == 'http':
            try:
                # Read the request body
                body = b""
                more_body = True
                while more_body:
                    message = await receive()
                    body += message.get('body', b'')
                    more_body = message.get('more_body', False)

                method = scope.get('method', 'GET')
                path = scope.get('path', '/')
                headers = {k.decode('latin1'): v.decode('latin1') for k, v in scope.get('headers', [])}
                client = scope.get('client')
                client_address = client[0] if client else ''
                request = Request(method=method, path=path, headers=headers, body=body, client_address=client_address)

                # Process the request and match the route
                route, params, allowed_methods = self.router.match(request.path, request.method)
                if route is None:
                    if method == 'OPTIONS':
                        allowed_methods = set(allowed_methods)
                        if allowed_methods:
                            await send({
                                'type': 'http.response.start',
                                'status': 200,
                                'headers': [(b'allow', ', '.join(sorted(allowed_methods)).encode('latin1'))],
                            })
                            await send({
                                'type': 'http.response.body',
                                'body': b'',
                            })
                            return
                        else:
                            raise NotFound("Not Found")
                    elif allowed_methods:
                        raise MethodNotAllowed(allowed_methods)
                    else:
                        raise NotFound("Not Found")

                # Store params in request
                request.params = params

                # Middleware processing
                middlewares = self.middleware.copy()
                if route.blueprint:
                    middlewares.extend(route.blueprint.middleware)

                for mw in middlewares:
                    await self._maybe_async(mw.before_request, request)

                # Call the route handler and pass the request object
                response = await self._call_route_handler(route.handler, request)

                for mw in reversed(middlewares):
                    result = await self._maybe_async(mw.after_request, request, response)
                    if result is not None:
                        response = result

                for mw in middlewares:
                    await self._maybe_async(mw.before_response, request, response)

                await send({
                    'type': 'http.response.start',
                    'status': response.status_code,
                    'headers': [(k.encode('latin1'), v.encode('latin1')) for k, v in response.headers.items()],
                })
                await send({
                    'type': 'http.response.body',
                    'body': response.get_content(),
                })

                for mw in reversed(middlewares):
                    await self._maybe_async(mw.after_response, request, response)

            except Exception as e:
                response = await self._handle_exception_async(request, e)

                await send({
                    'type': 'http.response.start',
                    'status': response.status_code,
                    'headers': [(k.encode('latin1'), v.encode('latin1')) for k, v in response.headers.items()],
                })
                await send({
                    'type': 'http.response.body',
                    'body': response.get_content(),
                })

        elif scope['type'] == 'websocket':
            path = scope.get('path', '/')
            headers = {k.decode('latin1'): v.decode('latin1') for k, v in scope.get('headers', [])}
            client = scope.get('client')
            client_address = client[0] if client else ''
            request = Request(method='GET', path=path, headers=headers, body=b'', client_address=client_address)

            route, params, _ = self.router.match(request.path, 'GET')
            if route is None or not getattr(route.handler, 'is_websocket', False):
                await send({
                    'type': 'websocket.close',
                    'code': 1000,
                })
                return

            await send({'type': 'websocket.accept'})

            # TODO: Middleware processing for WebSocket
            # Currently, middleware methods for WebSocket are not implemented.

            try:
                await route.handler(scope, receive, send, **params)
            except Exception as e:
                await send({'type': 'websocket.close', 'code': 1011})
                raise e

        else:
            pass

    def asgi_app(self) -> Callable:
        """
        Returns the ASGI application callable.

        This function should be used to run the application with ASGI servers like Uvicorn.

        :return: The ASGI application callable.
        :rtype: Callable
        """
        if not self.asgi:
            raise RuntimeError("ASGI mode is not enabled. Pass 'asgi=True' when creating the app.")

        self._check_static_route_overlaps()

        for path, directory, ignore in self.static_routes:
            self._register_static_route(path, directory, ignore)

        return self._asgi_app

    async def _call_route_handler(self, handler: Callable, request: Request) -> Response:
        """
        Calls the route handler with the given parameters.

        Supports both asynchronous and synchronous handlers.

        :param handler: The route handler function.
        :type handler: Callable
        :param request: The request object.
        :type request: Request
        :return: The response object.
        :rtype: Response
        """
        if asyncio.iscoroutinefunction(handler):
            result = await handler(request)
        else:
            result = handler(request)
        if not isinstance(result, Response):
            result = Response(result)
        return result

    def _call_route_handler_sync(self, handler: Callable, request: Request) -> Any:
        """
        Calls the route handler synchronously.

        Supports both synchronous and asynchronous handlers by running async handlers in an event loop.

        :param handler: The route handler function.
        :type handler: Callable
        :param request: The request object.
        :type request: Request
        :return: The result of the handler function.
        :rtype: Any
        """
        if asyncio.iscoroutinefunction(handler):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(handler(request))
            finally:
                loop.close()
        else:
            result = handler(request)
        return result

    async def _maybe_async(self, func: Callable, *args, **kwargs):
        """
        Helper method to call functions that may be asynchronous.

        :param func: The function to call.
        :type func: Callable
        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return: The result of the function call.
        """
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

    def _run_middleware_method_sync(self, method: Callable[..., Awaitable[T] | T], *args, **kwargs) -> T:
        """
        Helper method to run middleware methods synchronously, supporting both sync and async methods.

        :param method: The middleware method to call.
        :type method: Callable
        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return: The result of the middleware method.
        """
        if asyncio.iscoroutinefunction(method):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(method(*args, **kwargs))
            finally:
                loop.close()
        else:
            result = method(*args, **kwargs)
        return result

    def _http_status_message(self, status_code: int) -> str:
        """
        Returns the standard HTTP status message for a given status code.

        :param status_code: The HTTP status code.
        :type status_code: int
        :return: The standard HTTP status message.
        :rtype: str
        """
        from http.server import BaseHTTPRequestHandler
        return BaseHTTPRequestHandler.responses.get(status_code, ('Unknown',))[0]

    def _handle_exception(self, request: Request, exc: Exception) -> Response:
        """
        Handles exceptions by invoking the registered error handlers or returning a default error response.

        :param request: The current request object.
        :type request: Request
        :param exc: The exception that occurred.
        :type exc: Exception
        :return: A Response object representing the error response.
        :rtype: Response
        """
        handler = None

        # First, check for handlers registered with exception classes
        for exc_type in self.error_handlers:
            if isinstance(exc_type, type) and issubclass(exc_type, Exception):
                if isinstance(exc, exc_type):
                    handler = self.error_handlers[exc_type]
                    break

        # If no handler found and it's an HTTPException, check for handlers registered with status codes
        if handler is None and isinstance(exc, HTTPException):
            handler = self.error_handlers.get(exc.status_code)

        if handler:
            result = self._run_middleware_method_sync(handler, request, exc)
            if not isinstance(result, Response):
                if isinstance(result, tuple):
                    content, status_code = result
                    result = Response(content=content, status_code=status_code)
                else:
                    result = Response(result)
            return result
        else:
            if isinstance(exc, HTTPException):
                status_code = exc.status_code
                description = exc.description
            else:
                status_code = 500
                description = 'Internal Server Error'
                raise exc

            return Response(
                content=description,
                status_code=status_code,
                content_type='text/plain; charset=utf-8'
            )

    async def _handle_exception_async(self, request: Request, exc: Exception) -> Response:
        """
        Handles exceptions asynchronously by invoking the registered error handlers or returning a default error response.

        :param request: The current request object.
        :type request: Request
        :param exc: The exception that occurred.
        :type exc: Exception
        :return: A Response object representing the error response.
        :rtype: Response
        """
        # Find an error handler
        handler = None
        if isinstance(exc, HTTPException):
            handler = self.error_handlers.get(exc.status_code)
        for exc_type in self.error_handlers:
            if isinstance(exc, exc_type):
                handler = self.error_handlers[exc_type]
                break

        if handler:
            result = await self._maybe_async(handler, request, exc)
            if not isinstance(result, Response):
                if isinstance(result, tuple):
                    content, status_code = result
                    result = Response(content=content, status_code=status_code)
                else:
                    result = Response(result)
            return result
        else:
            # Default error response
            if isinstance(exc, HTTPException):
                status_code = exc.status_code
                description = exc.description
            else:
                status_code = 500
                description = 'Internal Server Error'
                raise exc
            return Response(
                content=description,
                status_code=status_code,
                content_type='text/plain; charset=utf-8'
            )

    def _register_static_route(self, path_prefix: str, directory: str, ignore: Optional[List[str]]) -> None:
        """
        Register a static file route.

        :param path_prefix: The URL path prefix to serve the files at.
        :type path_prefix: str
        :param directory: The directory to serve files from.
        :type directory: str
        :param ignore: A list of file or directory names to ignore.
        :type ignore: Optional[List[str]]
        """
        async def static_file_handler(request: Request) -> Response:
            file_path = request.path[len(path_prefix):]
            file_full_path = os.path.join(directory, file_path.lstrip('/'))

            if not os.path.abspath(file_full_path).startswith(os.path.abspath(directory)):
                raise NotFound("File not found.")

            if ignore:
                for ignored in ignore:
                    if file_full_path.endswith(ignored):
                        raise NotFound("File not found.")

            if not os.path.isfile(file_full_path):
                raise NotFound("File not found.")

            with open(file_full_path, 'rb') as f:
                content = f.read()
            content_type = self._guess_mime_type(file_full_path)
            return Response(content, content_type=content_type)

        self.router.add_route(f"{path_prefix}/<filepath:path>", static_file_handler, methods=['GET'])

    def _guess_mime_type(self, file_path: str) -> str:
        """
        Guess the MIME type of a file based on its extension.

        :param file_path: The path to the file.
        :type file_path: str
        :return: The MIME type.
        :rtype: str
        """
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or 'application/octet-stream'

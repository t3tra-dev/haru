"""
This module defines the core application class for the Haru web framework.
It provides functionality to handle routing, middleware management, and request/response processing.
"""

from typing import Callable, List, Optional, Type, TypeVar
import http.server
import socketserver
import traceback

from .router import Router
from .ctx import request_context
from .request import Request
from .response import Response
from .exceptions import (
    HTTPException,
    NotFound,
    MethodNotAllowed,
)
from .blueprint import Blueprint
from .middleware import Middleware
from .wrappers import FileWrapper, BytesWrapper

__all__ = ['Haru']

MiddlewareType = TypeVar('MiddlewareType', bound=Middleware)


class Haru:
    """
    The main application class of the Haru web framework. This class is responsible for
    managing routes, handling HTTP requests, and middleware processing.

    :param import_name: The name of the module or package that this application instance is associated with.
    :type import_name: str
    """

    def __init__(self, import_name: str):
        """
        Initialize the Haru application.

        :param import_name: The name of the module or package for the application.
        :type import_name: str
        """
        self.import_name: str = import_name
        self.router: Router = Router()
        self.blueprints: List[Blueprint] = []
        self.middleware: List[Middleware] = []

    def route(self, path: str, methods: Optional[List[str]] = None) -> Callable:
        """
        Define a new route in the application.

        :param path: The URL path to bind the route.
        :type path: str
        :param methods: A list of HTTP methods allowed for this route (GET, POST, etc.).
        :type methods: List[str], optional
        :return: A decorator to wrap the route handler function.
        :rtype: Callable
        """
        def decorator(func: Callable) -> Callable:
            self.router.add_route(path, func, methods)
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
        Retrieve a middleware instance by its class.

        :param middleware_class: The class of the middleware to retrieve.
        :type middleware_class: Type[MiddlewareType]
        :return: The middleware instance, or None if not found.
        :rtype: Optional[MiddlewareType]
        """
        for mw in self.middleware:
            if isinstance(mw, middleware_class):
                return mw
        return None

    def run(self, host: str = '127.0.0.1', port: int = 8000) -> None:
        """
        Start the HTTP server and run the application.

        :param host: The host address to bind the server to (default is 127.0.0.1).
        :type host: str
        :param port: The port number to bind the server to (default is 8000).
        :type port: int
        """
        handler_class = self._make_handler()
        with socketserver.ThreadingTCPServer((host, port), handler_class) as httpd:
            print(f"Serving on {host}:{port}")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("Server is shutting down.")
                httpd.server_close()

    def _make_handler(self) -> Type[http.server.BaseHTTPRequestHandler]:
        """
        Create a request handler class that processes incoming HTTP requests and routes them to the appropriate handlers.

        :return: A custom request handler class that processes HTTP requests.
        :rtype: Type[http.server.BaseHTTPRequestHandler]
        """
        app = self

        class RequestHandler(http.server.BaseHTTPRequestHandler):
            """
            Custom request handler for processing HTTP requests in the Haru framework.
            This handler maps requests to the application's routes and handles middleware processing.
            """

            server_version = "HaruHTTP/1.0"

            def do_GET(self) -> None:
                """Handle GET requests."""
                self._handle_request()

            def do_POST(self) -> None:
                """Handle POST requests."""
                self._handle_request()

            def do_PUT(self) -> None:
                """Handle PUT requests."""
                self._handle_request()

            def do_DELETE(self) -> None:
                """Handle DELETE requests."""
                self._handle_request()

            def do_PATCH(self) -> None:
                """Handle PATCH requests."""
                self._handle_request()

            def do_HEAD(self) -> None:
                """Handle HEAD requests."""
                self._handle_request()

            def do_OPTIONS(self) -> None:
                """Handle OPTIONS requests."""
                self._handle_request()

            def _handle_request(self) -> None:
                """
                Handle incoming HTTP requests, match routes, and apply middleware.
                If no route matches, it handles 404 (Not Found) or 405 (Method Not Allowed) errors.
                """
                method = self.command
                path = self.path
                try:
                    route, kwargs, allowed_methods = app.router.match(path, method)
                    if route is not None:
                        handler = route.handler
                        blueprint = route.blueprint

                        req = Request(
                            method=method,
                            path=path,
                            headers=dict(self.headers),
                            client_address=self.client_address[0]
                        )
                        token = request_context.set(req)

                        middlewares = app.middleware.copy()
                        if blueprint:
                            middlewares.extend(blueprint.middleware)

                        try:
                            for mw in middlewares:
                                mw.before_request(req)

                            response = handler(**kwargs)

                            if isinstance(response, Response):
                                pass
                            elif isinstance(response, tuple):
                                if len(response) == 2:
                                    body, status_code = response
                                    response = Response(body, status_code)
                                else:
                                    raise TypeError("View function must return 'Response', 'str', or '(str, int)'")
                            elif isinstance(response, str):
                                response = Response(response)
                            else:
                                raise TypeError("View function must return 'Response', 'str', or '(str, int)'")

                            for mw in reversed(middlewares):
                                result = mw.after_request(req, response)
                                if result is not None:
                                    response = result

                            for mw in middlewares:
                                mw.before_response(req, response)

                            self._send_response(response)

                            for mw in reversed(middlewares):
                                mw.after_response(req, response)

                        finally:
                            request_context.reset(token)
                    else:
                        if method == 'OPTIONS':
                            allowed_methods = set(allowed_methods)
                            if allowed_methods:
                                self.send_response(200)
                                self.send_header('Allow', ', '.join(sorted(allowed_methods)))
                                self.end_headers()
                            else:
                                raise NotFound("Not Found")
                        elif allowed_methods:
                            raise MethodNotAllowed(allowed_methods)
                        else:
                            raise NotFound("Not Found")
                except HTTPException as e:
                    self.send_response(e.status_code)
                    for key, value in e.headers.items():
                        self.send_header(key, value)
                    self.end_headers()
                    if self.command != 'HEAD' and e.status_code >= 400 and e.status_code != 204:
                        self.wfile.write(str(e).encode('utf-8'))
                    print(f"HTTPException: {e.status_code} {e.description}")
                except Exception as e:
                    traceback.print_exc()
                    self.send_error(500, str(e))

            def _send_response(self, response: Response) -> None:
                """
                Send an HTTP response to the client.

                :param response: The response object containing status code, headers, and content.
                :type response: Response
                """
                self.send_response(response.status_code)
                for key, value in response.headers.items():
                    self.send_header(key, value)
                self.end_headers()
                if self.command != 'HEAD' and response.status_code != 204:
                    if isinstance(response.content, (bytes, str)):
                        self.wfile.write(response.get_content())
                    elif isinstance(response.content, (FileWrapper, BytesWrapper)):
                        for chunk in response.content:
                            self.wfile.write(chunk)
                    else:
                        raise TypeError("Response content must be bytes, str, FileWrapper, or BytesWrapper")

        return RequestHandler

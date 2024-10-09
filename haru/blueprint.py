"""
This module defines the `Blueprint` class, which is used to organize routes and middleware
at a modular level in a Haru web application. Blueprints allow you to split your application
into components, each with its own routes and middleware.
"""

from typing import Callable, List, Optional, Type, TypeVar, Any
from .router import Router
from .middleware import Middleware

__all__ = ['Blueprint']

MiddlewareType = TypeVar('MiddlewareType', bound=Middleware)


class Blueprint:
    """
    A `Blueprint` is a modular component of a Haru web application. It allows you to define
    a set of routes and middleware that can be grouped together under a common URL prefix.
    This helps in organizing large applications by dividing them into smaller components.

    :param name: The name of the blueprint.
    :type name: str
    :param import_name: The name of the module or package where this blueprint is defined.
    :type import_name: str
    :param url_prefix: An optional URL prefix that will be prepended to all routes in this blueprint.
    :type url_prefix: Optional[str]
    """

    def __init__(self, name: str, import_name: str, url_prefix: Optional[str] = None):
        """
        Initialize a new blueprint.

        :param name: The name of the blueprint.
        :type name: str
        :param import_name: The name of the module or package for the blueprint.
        :type import_name: str
        :param url_prefix: An optional URL prefix for the blueprint routes.
        :type url_prefix: Optional[str]
        """
        self.name: str = name
        self.import_name: str = import_name
        self.url_prefix: Optional[str] = url_prefix
        self.router: Router = Router()
        self.middleware: List[Middleware] = []

    def route(self, path: str, methods: Optional[List[str]] = None) -> Callable:
        """
        Define a new route for the blueprint.

        :param path: The URL path for the route.
        :type path: str
        :param methods: A list of HTTP methods allowed for this route (GET, POST, etc.).
        :type methods: Optional[List[str]]
        :return: A decorator to wrap the route handler function.
        :rtype: Callable[[Callable], Callable]
        """
        def decorator(func: Callable) -> Callable:
            full_path = self._full_path(path)
            self.router.add_route(full_path, func, methods, blueprint=self)
            return func
        return decorator

    def add_middleware(self, middleware: Middleware) -> None:
        """
        Add middleware to the blueprint. This middleware will be executed
        for all routes registered under this blueprint.

        :param middleware: The middleware to be added.
        :type middleware: Middleware
        """
        self.middleware.append(middleware)

    def remove_middleware(self, middleware: Middleware) -> None:
        """
        Remove middleware from the blueprint.

        :param middleware: The middleware to be removed.
        :type middleware: Middleware
        """
        if middleware in self.middleware:
            self.middleware.remove(middleware)

    def get_middleware(self, middleware_class: Type[MiddlewareType]) -> Optional[MiddlewareType]:
        """
        Retrieve middleware by its class from the blueprint.

        :param middleware_class: The class of the middleware to retrieve.
        :type middleware_class: Type[MiddlewareType]
        :return: The middleware instance if found, or None if not found.
        :rtype: Optional[MiddlewareType]
        """
        for mw in self.middleware:
            if isinstance(mw, middleware_class):
                return mw
        return None

    def _full_path(self, path: str) -> str:
        """
        Generate the full path for a route, taking into account the blueprint's URL prefix.

        :param path: The route path.
        :type path: str
        :return: The full URL path with the URL prefix applied.
        :rtype: str
        """
        if self.url_prefix:
            return f"{self.url_prefix.rstrip('/')}/{path.lstrip('/')}"
        return path

    def register(self, app: Any) -> None:
        """
        Register all routes in the blueprint with the main application.

        :param app: The main Haru application instance.
        :type app: Haru
        """
        for route in self.router.routes:
            app.router.add_route(route.path, route.handler, route.methods, blueprint=self)

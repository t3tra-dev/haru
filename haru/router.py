"""
This module defines the routing system for the Haru web framework, including the `Route` and `Router` classes.
The routing system is responsible for mapping URL paths to handler functions and ensuring that
the correct handler is executed based on the request's path and HTTP method.
"""

from __future__ import annotations
from typing import Callable, Dict, List, Optional, Tuple, Any, TYPE_CHECKING
import re

__all__ = ['Route', 'Router']

if TYPE_CHECKING:
    from .blueprint import Blueprint


class Route:
    """
    Represents a single route in the application, which binds a URL path to a handler function
    and allows specific HTTP methods.

    :param path: The URL path pattern for this route. Supports regex-like matching.
    :type path: str
    :param handler: The function that handles requests matching this route.
    :type handler: Callable
    :param methods: A list of HTTP methods (e.g., GET, POST) that this route allows.
    :type methods: List[str]
    :param blueprint: The blueprint this route is associated with, if any.
    :type blueprint: Optional[Blueprint]
    """

    def __init__(self, path: str, handler: Callable, methods: List[str], blueprint: Optional[Blueprint] = None):
        self.path: str = path
        self.handler: Callable = handler
        self.methods: List[str] = methods
        self.blueprint: Optional[Blueprint] = blueprint
        self.pattern: re.Pattern = re.compile(f'^{path}$')

    def match(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Check if the provided path matches the route's pattern.

        :param path: The URL path to match against the route's pattern.
        :type path: str
        :return: A dictionary of matched parameters if the path matches, otherwise None.
        :rtype: Optional[Dict[str, Any]]
        """
        match = self.pattern.match(path)
        if match:
            return match.groupdict()
        return None


class Router:
    """
    The `Router` class manages a collection of routes and provides functionality to add and match routes.
    It serves as the core routing mechanism for the Haru web framework.

    :param routes: A list of registered routes.
    :type routes: List[Route]
    """

    def __init__(self):
        """
        Initialize a new `Router` instance with an empty list of routes.
        """
        self.routes: List[Route] = []

    def add_route(self, path: str, handler: Callable, methods: Optional[List[str]] = None, blueprint: Optional[Blueprint] = None) -> None:
        """
        Add a new route to the router.

        :param path: The URL path for the route.
        :type path: str
        :param handler: The function to handle requests that match this route.
        :type handler: Callable
        :param methods: A list of allowed HTTP methods for this route. Defaults to ['GET'].
        :type methods: Optional[List[str]]
        :param blueprint: The blueprint that this route is associated with, if any.
        :type blueprint: Optional[Blueprint]
        """
        methods = methods or ['GET']
        methods = [method.upper() for method in methods]

        # Automatically include HEAD and OPTIONS methods if applicable
        if 'GET' in methods and 'HEAD' not in methods:
            methods.append('HEAD')

        if 'OPTIONS' not in methods:
            methods.append('OPTIONS')

        route = Route(path, handler, methods, blueprint)
        self.routes.append(route)

    def match(self, path: str, method: str) -> Tuple[Optional[Route], Dict[str, Any], List[str]]:
        """
        Match the given path and HTTP method to a registered route.

        :param path: The URL path to match.
        :type path: str
        :param method: The HTTP method of the request (e.g., 'GET', 'POST').
        :type method: str
        :return: A tuple containing the matched route (if any), a dictionary of parameters,
                 and a list of allowed methods for the path.
        :rtype: Tuple[Optional[Route], Dict[str, Any], List[str]]
        """
        allowed_methods: List[str] = []
        for route in self.routes:
            params = route.match(path)
            if params is not None:
                allowed_methods.extend(route.methods)
                if method in route.methods:
                    return route, params, allowed_methods
        return None, {}, allowed_methods

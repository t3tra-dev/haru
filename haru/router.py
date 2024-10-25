"""
This module defines the routing system for the Haru web framework, including the `Route` and `Router` classes.
The routing system is responsible for mapping URL paths to handler functions and ensuring that
the correct handler is executed based on the request's path and HTTP method.
"""

from __future__ import annotations
from typing import Callable, Dict, List, Optional, Tuple, Any, Pattern
import re

__all__ = ['Route', 'Router']


class Route:
    """
    Represents a single route in the application, which binds a URL path to a handler function
    and allows specific HTTP methods.

    :param path: The URL path pattern for this route. Supports parameterized paths like '/users/<username:str>'.
    :type path: str
    :param handler: The function that handles requests matching this route.
    :type handler: Callable
    :param methods: A list of HTTP methods (e.g., GET, POST) that this route allows.
    :type methods: List[str]
    :param blueprint: The blueprint this route is associated with, if any.
    :type blueprint: Optional[Blueprint]
    """

    def __init__(self, path: str, handler: Callable, methods: List[str], blueprint: Optional[Any] = None):
        self.path: str = path
        self.handler: Callable = handler
        self.methods: List[str] = methods
        self.blueprint: Optional[Any] = blueprint
        self.pattern: Pattern = self._compile_path(path)
        self.param_types: Dict[str, str] = {}  # Store parameter types

    def _compile_path(self, path: str) -> Pattern:
        """
        Compiles the route path into a regular expression pattern.

        :param path: The route path.
        :type path: str
        :return: The compiled regular expression pattern.
        :rtype: Pattern
        """
        # Replace path parameters like '<name:type>' with regex groups
        param_regex = re.compile(r'<(\w+)(?::(\w+))?>')
        pattern = '^'
        last_pos = 0

        for match in param_regex.finditer(path):
            start, end = match.span()
            param_name, param_type = match.groups()
            param_type = param_type or 'str'  # Default type is 'str'
            self.param_types[param_name] = param_type

            # Add the text before the parameter
            pattern += re.escape(path[last_pos:start])

            # Add the parameter pattern
            if param_type == 'str':
                regex = f'(?P<{param_name}>[^/]+)'
            elif param_type == 'int':
                regex = f'(?P<{param_name}>\\d+)'
            elif param_type == 'float':
                regex = f'(?P<{param_name}>\\d+\\.\\d+)'
            elif param_type == 'path':
                regex = f'(?P<{param_name}>.+)'
            else:
                raise ValueError(f"Unsupported parameter type: {param_type}")

            pattern += regex
            last_pos = end

        # Add the remaining text after the last parameter
        pattern += re.escape(path[last_pos:])
        pattern += '$'
        return re.compile(pattern)

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
            params = match.groupdict()
            # Convert params to their specified types
            for name, value in params.items():
                param_type = self.param_types.get(name, 'str')
                params[name] = self._convert_param(value, param_type)
            return params
        return None

    def _convert_param(self, value: str, param_type: str) -> Any:
        """
        Convert the parameter value to the specified type.

        :param value: The parameter value as a string.
        :type value: str
        :param param_type: The type to convert to.
        :type param_type: str
        :return: The converted value.
        :rtype: Any
        """
        if param_type == 'str':
            return value
        elif param_type == 'int':
            return int(value)
        elif param_type == 'float':
            return float(value)
        elif param_type == 'path':
            return value  # 'path' type remains as string
        else:
            return value  # Unknown type, return as string


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

    def add_route(self, path: str, handler: Callable, methods: Optional[List[str]] = None, blueprint: Optional[Any] = None) -> None:
        """
        Add a new route to the router.

        :param path: The URL path for the route.
        :type path: str
        :param handler: The function to handle requests that match this route.
        :type handler: Callable
        :param methods: A list of allowed HTTP methods for this route. Defaults to ['GET'].
        :type methods: Optional[List[str]]
        :param blueprint: The blueprint that this route is associated with, if any.
        :type blueprint: Optional[Any]
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
                if method.upper() in route.methods:
                    return route, params, []
        return None, {}, allowed_methods

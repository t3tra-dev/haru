"""
This module defines the routing system for the Haru web framework, including the `Route` and `Router` classes.
The routing system is responsible for mapping URL paths to handler functions and ensuring that
the correct handler is executed based on the request's path and HTTP method.
"""

from __future__ import annotations
from typing import Callable, Dict, List, Optional, Tuple, Any, Pattern
import re

__all__ = ["Route", "Router"]


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

    def __init__(
        self,
        path: str,
        handler: Callable,
        methods: List[str],
        blueprint: Optional[Any] = None,
    ):
        self.path: str = path
        self.handler: Callable = handler
        self.methods: List[str] = methods
        self.blueprint: Optional[Any] = blueprint
        self.param_types: Dict[str, str] = {}
        # The pattern will be compiled in the Router


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
        self.compiled: bool = False
        self._regex: Optional[Pattern] = None

    def add_route(
        self,
        path: str,
        handler: Callable,
        methods: Optional[List[str]] = None,
        blueprint: Optional[Any] = None,
    ) -> None:
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
        methods = methods or ["GET"]
        methods = [method.upper() for method in methods]

        # Automatically include HEAD and OPTIONS methods if applicable
        if "GET" in methods and "HEAD" not in methods:
            methods.append("HEAD")

        if "OPTIONS" not in methods:
            methods.append("OPTIONS")

        route = Route(path, handler, methods, blueprint)
        self.routes.append(route)
        self.compiled = False  # Mark as needing recompilation

    def match(
        self, path: str, method: str
    ) -> Tuple[Optional[Route], Dict[str, Any], List[str]]:
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
        if not self.compiled:
            self._compile_routes()
        match = self._regex.match(path)
        if not match:
            # No match found, collect allowed methods for this path
            allowed_methods = self._collect_allowed_methods(path)
            return None, {}, allowed_methods

        # Identify which route matched
        route_index = None
        for i in range(len(self.routes)):
            group_name = f"route_{i}"
            if match.group(group_name):
                route_index = i
                break
        if route_index is None:
            return None, {}, []

        route = self.routes[route_index]
        if method.upper() not in route.methods:
            allowed_methods = route.methods
            return None, {}, allowed_methods

        # Extract parameters
        params = {}
        for name, value in match.groupdict().items():
            if value is not None:
                m = re.match(r"param_(\d+)_(.+)", name)
                if m:
                    idx, param_name = m.groups()
                    idx = int(idx)
                    if idx == route_index:
                        param_type = route.param_types[param_name]
                        params[param_name] = self._convert_param(value, param_type)
        return route, params, []

    def _compile_routes(self) -> None:
        """
        Compile all registered routes into a single regular expression.
        """
        patterns = []
        for index, route in enumerate(self.routes):
            pattern, param_types = self._compile_route_pattern(route.path, index)
            route.param_types = param_types
            group_name = f"route_{index}"
            patterns.append(f"(?P<{group_name}>" + pattern + ")")
        combined_pattern = "^(" + "|".join(patterns) + ")$"
        self._regex = re.compile(combined_pattern)
        self.compiled = True

    def _compile_route_pattern(
        self, path: str, route_index: int
    ) -> Tuple[str, Dict[str, str]]:
        """
        Compile an individual route's path pattern into a regular expression fragment.

        :param path: The route path.
        :type path: str
        :param route_index: The index of the route in the routes list.
        :type route_index: int
        :return: A tuple containing the regex pattern and parameter types.
        :rtype: Tuple[str, Dict[str, str]]
        """
        param_regex = re.compile(r"<(\w+)(?::(\w+))?>")
        pattern = ""
        last_pos = 0
        param_types = {}
        for match in param_regex.finditer(path):
            start, end = match.span()
            param_name, param_type = match.groups()
            param_type = param_type or "str"  # Default type is 'str'
            param_types[param_name] = param_type

            # Add the text before the parameter
            pattern += re.escape(path[last_pos:start])

            # Add the parameter pattern with unique group name
            if route_index is not None and route_index >= 0:
                group_name = f"param_{route_index}_{param_name}"
            else:
                # Use param_name as group name when route_index is None or negative
                group_name = param_name

            # Ensure group name is a valid Python identifier
            if not group_name.isidentifier():
                group_name = (
                    f"param_{abs(route_index)}_{param_name}"
                    if route_index is not None
                    else param_name
                )
                group_name = re.sub(r"\W|^(?=\d)", "_", group_name)

            if param_type == "str":
                regex = f"(?P<{group_name}>[^/]+)"
            elif param_type == "int":
                regex = f"(?P<{group_name}>\\d+)"
            elif param_type == "float":
                regex = f"(?P<{group_name}>\\d+\\.\\d+)"
            elif param_type == "path":
                regex = f"(?P<{group_name}>.+)"
            else:
                raise ValueError(f"Unsupported parameter type: {param_type}")

            pattern += regex
            last_pos = end

        # Add the remaining text after the last parameter
        pattern += re.escape(path[last_pos:])
        return pattern, param_types

    def _collect_allowed_methods(self, path: str) -> List[str]:
        """
        Collect allowed HTTP methods for a given path when no route matches.

        :param path: The URL path to check.
        :type path: str
        :return: A list of allowed methods for the path.
        :rtype: List[str]
        """
        allowed_methods = []
        for route in self.routes:
            # Pass route_index=None to avoid including it in group names
            pattern, _ = self._compile_route_pattern(route.path, None)
            route_regex = re.compile("^" + pattern + "$")
            if route_regex.match(path):
                allowed_methods.extend(route.methods)
        return allowed_methods

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
        if param_type == "str":
            return value
        elif param_type == "int":
            return int(value)
        elif param_type == "float":
            return float(value)
        elif param_type == "path":
            return value  # 'path' type remains as string
        else:
            return value  # Unknown type, return as string

"""
This module defines the routing system for the Haru web framework, including the `Route` and `Router` classes.
The routing system is optimized by compiling all routes into a single regular expression for faster matching.
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
    :type blueprint: Optional[Any]
    """

    def __init__(self, path: str, handler: Callable, methods: List[str], blueprint: Optional[Any] = None):
        self.path: str = path
        self.handler: Callable = handler
        self.methods: List[str] = methods
        self.blueprint: Optional[Any] = blueprint
        self.param_names: List[str] = []
        self.pattern: str = self._convert_path_to_regex(path)

    def _convert_path_to_regex(self, path: str) -> str:
        """
        Converts the route path into a regex pattern string.

        :param path: The route path.
        :type path: str
        :return: The regex pattern as a string.
        :rtype: str
        """
        # Replace path parameters like '<name:type>' with regex groups
        param_regex = re.compile(r'<(\w+)(?::(\w+))?>')
        pattern = ''
        last_pos = 0

        for match in param_regex.finditer(path):
            start, end = match.span()
            param_name, param_type = match.groups()
            param_type = param_type or 'str'  # Default type is 'str'
            self.param_names.append(param_name)

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
        return pattern

    def convert_params(self, params: Dict[str, str]) -> Dict[str, Any]:
        """
        Convert the parameter values to their specified types.

        :param params: The dictionary of parameter values as strings.
        :type params: Dict[str, str]
        :return: The dictionary of converted parameter values.
        :rtype: Dict[str, Any]
        """
        converted_params = {}
        param_types = self._get_param_types()

        for name in self.param_names:
            value = params.get(name)
            param_type = param_types.get(name, 'str')
            converted_params[name] = self._convert_param(value, param_type)

        return converted_params

    def _get_param_types(self) -> Dict[str, str]:
        """
        Extract parameter types from the route path.

        :return: A dictionary mapping parameter names to types.
        :rtype: Dict[str, str]
        """
        param_types = {}
        param_regex = re.compile(r'<(\w+)(?::(\w+))?>')
        for match in param_regex.finditer(self.path):
            param_name, param_type = match.groups()
            param_types[param_name] = param_type or 'str'
        return param_types

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
    It compiles all routes into a single regular expression for faster matching.

    :param routes: A list of registered routes.
    :type routes: List[Route]
    """

    def __init__(self):
        """
        Initialize a new `Router` instance with an empty list of routes.
        """
        self.routes: List[Route] = []
        self._compiled_pattern: Optional[Pattern] = None
        self._route_map: Dict[int, Route] = {}
        self._param_names_list: List[List[str]] = []

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
        methods = [method.upper() for method in methods]  # Convert all methods to uppercase

        # Automatically include HEAD and OPTIONS methods if applicable
        if 'GET' in methods and 'HEAD' not in methods:
            methods.append('HEAD')

        if 'OPTIONS' not in methods:
            methods.append('OPTIONS')

        route = Route(path, handler, methods, blueprint)
        self.routes.append(route)
        self._compiled_pattern = None  # Invalidate the compiled pattern

    def compile(self) -> None:
        """
        Compile all routes into a single regular expression for faster matching.
        """
        pattern_strings = []
        index = 0
        for route in self.routes:
            pattern_strings.append(f'(?P<route_{index}>{route.pattern})')
            self._route_map[index] = route
            self._param_names_list.append(route.param_names)
            index += 1

        full_pattern = '^' + '|'.join(pattern_strings) + '$'
        self._compiled_pattern = re.compile(full_pattern)

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
        if self._compiled_pattern is None:
            self.compile()

        match = self._compiled_pattern.match(path)
        allowed_methods: List[str] = []

        if match:
            for index, route in self._route_map.items():
                if match.group(f'route_{index}') is not None:
                    allowed_methods.extend(route.methods)
                    if method.upper() in route.methods:  # Ensure method is checked in uppercase
                        # Extract parameters
                        param_names = self._param_names_list[index]
                        params = {name: match.group(name) for name in param_names}
                        # Convert parameter types
                        params = route.convert_params(params)
                        return route, params, []
            return None, {}, allowed_methods  # Method not allowed
        else:
            return None, {}, allowed_methods  # Not found

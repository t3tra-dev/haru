"""
This module defines classes for handling HTTP requests in the Haru web framework.
It includes the `Request` class, which encapsulates details about an incoming HTTP request,
and the `RequestProxy` class, which acts as a proxy to access the current request data
via the request context.

The `request` object is an instance of `RequestProxy` and provides easy access
to the current request in the application.
"""

from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

from .ctx import request_context

__all__ = ['Request', 'RequestProxy', 'request']


class Request:
    """
    Represents an HTTP request. This class provides access to common request properties
    such as the method, path, headers, query parameters, cookies, and more.

    :param method: The HTTP method of the request (e.g., 'GET', 'POST').
    :type method: str
    :param path: The URL path of the request.
    :type path: str
    :param headers: A dictionary of HTTP headers.
    :type headers: Dict[str, str]
    :param body: The raw body of the request.
    :type body: bytes
    :param client_address: The client's IP address.
    :type client_address: str
    """

    def __init__(self, method: str, path: str, headers: Dict[str, str], body: bytes = b'', client_address: str = ''):
        self.method: str = method
        self.path: str = path
        self.headers: Dict[str, str] = headers
        self.body: bytes = body
        self.remote_addr: str = client_address
        self.user_agent: str = headers.get('user-agent', '')
        self.host: str = headers.get('host', '')
        self.cookies: Dict[str, str] = self._parse_cookies()
        self.query_string: str = self._parse_query_string()
        self.args: Dict[str, str] = self._parse_query_params()
        self.form: Dict[str, Any] = {}
        self.json: Optional[Dict[str, Any]] = self._parse_json()
        self.files: Dict[str, Any] = {}

    def _parse_cookies(self) -> Dict[str, str]:
        """
        Parse the 'Cookie' header into a dictionary of key-value pairs.

        :return: A dictionary of cookies sent with the request.
        :rtype: Dict[str, str]
        """
        cookie_header = self.headers.get('cookie', '')
        cookies = {}
        if cookie_header:
            for cookie in cookie_header.split(';'):
                if '=' in cookie:
                    key, value = cookie.strip().split('=', 1)
                    cookies[key] = value
        return cookies

    def _parse_query_string(self) -> str:
        """
        Extract the query string from the URL path.

        :return: The query string of the request, or an empty string if none exists.
        :rtype: str
        """
        parsed_url = urlparse(self.path)
        return parsed_url.query

    def _parse_query_params(self) -> Dict[str, str]:
        """
        Parse the query string into a dictionary of key-value pairs.

        :return: A dictionary of query parameters.
        :rtype: Dict[str, str]
        """
        query_string = self.query_string
        return {k: v[0] for k, v in parse_qs(query_string).items()}

    def _parse_json(self) -> Optional[Dict[str, Any]]:
        """
        Parse the request body as JSON, if possible.

        :return: A dictionary representing the JSON data, or None if parsing fails.
        :rtype: Optional[Dict[str, Any]]
        """
        if 'application/json' in self.headers.get('content-type', ''):
            import json
            try:
                return json.loads(self.body.decode('utf-8'))
            except (ValueError, UnicodeDecodeError):
                return None
        return None

    def get_json(self) -> Optional[Dict[str, Any]]:
        """
        Public method to access the parsed JSON data.

        :return: The parsed JSON data.
        :rtype: Optional[Dict[str, Any]]
        """
        return self.json

    def get_body(self) -> bytes:
        """
        Returns the request body as bytes.

        :return: The request body.
        :rtype: bytes
        """
        return self.body


class RequestProxy:
    """
    A proxy object that provides access to the current request in the context of an HTTP request.
    The `RequestProxy` retrieves the current request from the request context, allowing global access
    to the request properties without passing the request object explicitly.

    The attributes of `RequestProxy` correspond to those of the `Request` object.
    """
    request_context = request_context

    method: str
    path: str
    headers: Dict[str, str]
    body: bytes
    remote_addr: str
    user_agent: str
    host: str
    cookies: Dict[str, str]
    query_string: str
    args: Dict[str, str]
    form: Dict[str, Any]
    json: Optional[Dict[str, Any]]
    files: Dict[str, Any]

    def __getattribute__(self, name: str) -> Any:
        """
        Overrides attribute access to dynamically fetch the current request's attribute
        from the request context.

        :param name: The name of the attribute to retrieve.
        :type name: str
        :return: The value of the attribute from the current request.
        :rtype: Any
        """
        if name in ('__class__', '__dict__', '__doc__', '__module__', '__weakref__', 'request_context'):
            return object.__getattribute__(self, name)
        req = self.request_context.get()
        return getattr(req, name)


request = RequestProxy()

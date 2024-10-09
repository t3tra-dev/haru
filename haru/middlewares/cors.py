"""
This module defines the `CORSMiddleware` class, which provides Cross-Origin Resource Sharing (CORS)
functionality in the Haru web framework. This middleware adds the necessary CORS headers to HTTP
responses, enabling cross-origin requests from specified origins.

CORS is a mechanism that allows resources on a web server to be requested from another domain outside
the domain from which the resource originated. This middleware can be configured to control which origins,
methods, and headers are allowed for cross-origin requests.

Usage example:

.. code-block:: python

    app.add_middleware(CORSMiddleware(
        allow_origins=['https://example.com'],
        allow_methods=['GET', 'POST'],
        allow_headers=['Content-Type'],
    ))

Parameters:
    allow_origins (List[str]): List of origins that are allowed to make requests.
    allow_methods (List[str]): List of HTTP methods allowed (e.g., GET, POST).
    allow_headers (List[str]): List of HTTP headers allowed in requests.
    max_age (Optional[int]): Maximum time in seconds the CORS request is cached.
    allow_credentials (bool): Whether to allow credentials (cookies, authorization headers).

Note:
    This middleware should be applied before any other middlewares that modify the response.
"""

from typing import List, Optional
from haru.middleware import Middleware
from haru.request import Request
from haru.response import Response

__all__ = ['CORSMiddleware']


class CORSMiddleware(Middleware):
    """
    Cross-Origin Resource Sharing (CORS) Middleware

    This middleware adds CORS headers to responses to allow cross-origin requests.
    It can be configured to allow specific origins, methods, and headers.

    :param allow_origins: A list of origins that are allowed to make requests.
    :type allow_origins: List[str]
    :param allow_methods: A list of HTTP methods allowed for cross-origin requests.
    :type allow_methods: List[str]
    :param allow_headers: A list of HTTP headers allowed in the request.
    :type allow_headers: List[str]
    :param max_age: The maximum time (in seconds) that the results of a preflight request can be cached.
    :type max_age: Optional[int]
    :param allow_credentials: Whether to allow credentials (cookies, authorization headers, etc.) to be included in cross-origin requests.
    :type allow_credentials: bool
    """

    def __init__(
        self,
        allow_origins: List[str],
        allow_methods: List[str],
        allow_headers: List[str],
        max_age: Optional[int] = None,
        allow_credentials: bool = False,
    ):
        """
        Initialize the `CORSMiddleware` with the allowed origins, methods, headers, and optional settings for caching and credentials.

        :param allow_origins: A list of origins that are allowed to make requests.
        :type allow_origins: List[str]
        :param allow_methods: A list of HTTP methods allowed for cross-origin requests.
        :type allow_methods: List[str]
        :param allow_headers: A list of HTTP headers allowed in the request.
        :type allow_headers: List[str]
        :param max_age: The maximum time (in seconds) that the results of a preflight request can be cached.
        :type max_age: Optional[int]
        :param allow_credentials: Whether to allow credentials (cookies, authorization headers, etc.) to be included in cross-origin requests.
        :type allow_credentials: bool
        """
        super().__init__()
        self.allow_origins = allow_origins
        self.allow_methods = ', '.join(allow_methods)
        self.allow_headers = ', '.join(allow_headers)
        self.max_age = str(max_age) if max_age is not None else None
        self.allow_credentials = allow_credentials

    def after_request(self, request: Request, response: Response) -> Response:
        """
        Add the CORS headers to the response after the request is processed. This method checks the origin
        of the request and sets the appropriate CORS headers to allow the request if the origin is allowed.

        :param request: The current HTTP request object.
        :type request: Request
        :param response: The HTTP response object to which the CORS headers will be added.
        :type response: Response
        :return: The response object with the CORS headers added.
        :rtype: Response
        """
        origin = request.headers.get('Origin')
        if origin and (origin in self.allow_origins or '*' in self.allow_origins):
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = self.allow_methods
            response.headers['Access-Control-Allow-Headers'] = self.allow_headers
            if self.max_age:
                response.headers['Access-Control-Max-Age'] = self.max_age
            if self.allow_credentials:
                response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response

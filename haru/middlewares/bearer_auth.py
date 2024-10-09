"""
This module defines the `BearerAuthMiddleware` class, which provides Bearer Token Authentication
for protected routes in the Haru web framework. The middleware verifies the presence and validity
of an API token in the 'Authorization' header of incoming requests.

If the token is missing or invalid, the middleware raises an `Unauthorized` exception, prompting the client
to provide a valid token.

Usage example:

.. code-block:: python

    app.add_middleware(BearerAuthMiddleware(tokens=['token1', 'token2']))
"""

from typing import List
from haru.middleware import Middleware
from haru.request import Request
from haru.exceptions import Unauthorized

__all__ = ['BearerAuthMiddleware']


class BearerAuthMiddleware(Middleware):
    """
    Bearer Authentication Middleware

    This middleware provides authentication by verifying an API token in the
    'Authorization' header of the request. Clients should include the header
    'Authorization: Bearer {token}'.

    :param tokens: A list of valid tokens that are accepted for authentication.
    :type tokens: List[str]

    :raises Unauthorized: If authentication fails or token is missing/invalid.
    """

    def __init__(self, tokens: List[str]):
        """
        Initialize the `BearerAuthMiddleware` with a list of valid tokens.

        :param tokens: A list of valid tokens for authenticating requests.
        :type tokens: List[str]
        """
        super().__init__()
        self.tokens = tokens

    def before_request(self, request: Request) -> None:
        """
        Process the request before it reaches the main route handler.
        This method checks the 'Authorization' header and validates the Bearer token.

        :param request: The current HTTP request object.
        :type request: Request

        :raises Unauthorized: If the 'Authorization' header is missing, malformed, or contains an invalid token.
        """
        auth_header = request.headers.get('Authorization')
        if auth_header is None or not auth_header.startswith('Bearer '):
            self._unauthorized()
        else:
            token = auth_header.split(' ', 1)[1]
            if token not in self.tokens:
                self._unauthorized()

    def _unauthorized(self):
        """
        Helper method to raise an Unauthorized exception when the token is missing or invalid.
        """
        raise Unauthorized(description='Invalid or missing authentication token.')

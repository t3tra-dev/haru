"""
This module defines the `BasicAuthMiddleware` class, which provides HTTP Basic Authentication
for protected routes in the Haru web framework. This middleware intercepts incoming requests
and checks the 'Authorization' header for valid credentials, comparing them against a configured
list of users.

If the credentials are missing or invalid, the middleware raises an `Unauthorized` exception,
prompting the client to authenticate.

Usage example:

.. code-block:: python

    app.add_middleware(BasicAuthMiddleware(users=[{'username': 'admin', 'password': 'mypass'}]))

"""

from base64 import b64decode
from typing import List, Dict, Optional
from haru.middleware import Middleware
from haru.request import Request
from haru.exceptions import Unauthorized

__all__ = ['BasicAuthMiddleware']


class BasicAuthMiddleware(Middleware):
    """
    Basic Authentication Middleware

    This middleware applies HTTP Basic Authentication to specified routes.
    It checks the 'Authorization' header in the request and verifies
    the provided credentials against the configured list of users.

    :param users: A list of dictionaries where each dictionary contains 'username' and 'password' keys.
    :type users: List[Dict[str, str]]
    :param realm: The authentication realm displayed in the authentication dialog (default is 'Protected').
    :type realm: Optional[str]

    :raises Unauthorized: If authentication fails or credentials are missing.
    """

    def __init__(self, users: List[Dict[str, str]], realm: Optional[str] = 'Protected'):
        """
        Initialize the `BasicAuthMiddleware` with a list of users and an optional authentication realm.

        :param users: A list of user dictionaries containing 'username' and 'password' keys.
        :type users: List[Dict[str, str]]
        :param realm: An optional string representing the authentication realm (default is 'Protected').
        :type realm: Optional[str]
        """
        super().__init__()
        self.users = {user['username']: user['password'] for user in users}
        self.realm = realm

    def before_request(self, request: Request) -> None:
        """
        Process the request before it reaches the main route handler.
        This method checks the 'Authorization' header and validates the Basic Authentication credentials.

        :param request: The current HTTP request object.
        :type request: Request

        :raises Unauthorized: If the 'Authorization' header is missing, malformed, or contains invalid credentials.
        """
        auth_header = request.headers.get('Authorization')
        if auth_header is None or not auth_header.startswith('Basic '):
            self._unauthorized()
        else:
            # Decode Base64 encoded credentials
            encoded_credentials = auth_header.split(' ', 1)[1]
            try:
                decoded_credentials = b64decode(encoded_credentials).decode('utf-8')
                username, password = decoded_credentials.split(':', 1)
                expected_password = self.users.get(username)
                if expected_password is None or password != expected_password:
                    self._unauthorized()
            except Exception:
                self._unauthorized()

    def _unauthorized(self):
        """
        Helper method to raise an Unauthorized exception with a WWW-Authenticate header.
        """
        headers = {
            'WWW-Authenticate': f'Basic realm="{self.realm}"'
        }
        raise Unauthorized(description='Authentication required.', headers=headers)

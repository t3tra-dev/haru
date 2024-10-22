"""
This module defines the `JWTAuthMiddleware` class, which provides JWT (JSON Web Token) Authentication
for protected routes in the Haru web framework. The middleware verifies the presence and validity
of a JWT token in the 'Authorization' header of incoming requests.

If the token is missing or invalid, the middleware raises an `Unauthorized` exception, prompting the client
to provide a valid token.

Usage example:

.. code-block:: python

    app.add_middleware(JWTAuthMiddleware(secret_key='your-secret-key'))
"""

import base64
import hmac
import hashlib
import json
from typing import Optional

from haru.middleware import Middleware
from haru.request import Request
from haru.exceptions import Unauthorized

__all__ = ['JWTAuthMiddleware']


class JWTAuthMiddleware(Middleware):
    """
    JWT Authentication Middleware

    This middleware provides authentication by verifying a JWT token in the
    'Authorization' header of the request. Clients should include the header
    'Authorization: Bearer {token}'.

    :param secret_key: The secret key used to sign the JWT tokens.
    :type secret_key: str
    :param algorithm: The hashing algorithm to use (default is 'HS256').
    :type algorithm: str

    :raises Unauthorized: If authentication fails or token is missing/invalid.
    """

    def __init__(self, secret_key: str, algorithm: str = 'HS256', verify_exp: bool = True):
        """
        Initialize the `JWTAuthMiddleware` with a secret key and algorithm.

        :param secret_key: The secret key used to sign the JWT tokens.
        :type secret_key: str
        :param algorithm: The hashing algorithm to use (default is 'HS256').
        :type algorithm: str
        :param verify_exp: Whether to verify the 'exp' claim (default is True).
        :type verify_exp: bool
        """
        super().__init__()
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.verify_exp = verify_exp

        if self.algorithm != 'HS256':
            raise ValueError("Unsupported algorithm. Only 'HS256' is supported in this implementation.")

    def before_request(self, request: Request) -> None:
        """
        Process the request before it reaches the main route handler.
        This method checks the 'Authorization' header and validates the JWT token.

        :param request: The current HTTP request object.
        :type request: Request

        :raises Unauthorized: If the 'Authorization' header is missing, malformed, or contains an invalid token.
        """
        auth_header = request.headers.get('Authorization')
        if auth_header is None or not auth_header.startswith('Bearer '):
            self._unauthorized('Authorization header missing or malformed.')
        else:
            token = auth_header.split(' ', 1)[1]
            payload = self._decode_jwt(token)
            if payload is None:
                self._unauthorized('Invalid or expired token.')
            else:
                # Attach payload to the request for use in route handlers
                request.user = payload

    def _unauthorized(self, message: str):
        """
        Helper method to raise an Unauthorized exception when the token is missing or invalid.
        """
        raise Unauthorized(description=message)

    def _decode_jwt(self, token: str) -> Optional[dict]:
        """
        Decode and verify a JWT token.

        :param token: The JWT token to decode.
        :type token: str
        :return: The payload of the token if valid, otherwise None.
        :rtype: Optional[dict]
        """
        try:
            header_b64, payload_b64, signature_b64 = token.split('.')
        except ValueError:
            return None

        header = self._b64_decode(header_b64)
        payload = self._b64_decode(payload_b64)
        signature = self._b64_decode(signature_b64, urlsafe=False)

        if header is None or payload is None or signature is None:
            return None

        header_json = json.loads(header)
        payload_json = json.loads(payload)

        if header_json.get('alg') != self.algorithm:
            return None

        expected_signature = self._sign(f'{header_b64}.{payload_b64}')

        if not hmac.compare_digest(signature, expected_signature):
            return None

        if self.verify_exp and 'exp' in payload_json:
            import time
            if time.time() > payload_json['exp']:
                return None

        return payload_json

    def _sign(self, msg: str) -> bytes:
        """
        Generate a signature for the given message.

        :param msg: The message to sign.
        :type msg: str
        :return: The generated signature.
        :rtype: bytes
        """
        return hmac.new(
            key=self.secret_key.encode(),
            msg=msg.encode(),
            digestmod=hashlib.sha256
        ).digest()

    def _b64_decode(self, data: str, urlsafe: bool = True) -> Optional[bytes]:
        """
        Decode a Base64 encoded string.

        :param data: The Base64 encoded string.
        :type data: str
        :param urlsafe: Whether to use URL-safe decoding.
        :type urlsafe: bool
        :return: The decoded bytes, or None if decoding fails.
        :rtype: Optional[bytes]
        """
        import binascii
        try:
            padding = '=' * (-len(data) % 4)  # Fix padding
            if urlsafe:
                return base64.urlsafe_b64decode(data + padding)
            else:
                return base64.b64decode(data + padding)
        except (ValueError, binascii.Error):
            return None

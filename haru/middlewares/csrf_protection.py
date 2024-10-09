"""
This module defines the `CSRFProtectionMiddleware` class, which provides protection against
Cross-Site Request Forgery (CSRF) attacks in the Haru web framework. The middleware compares
the 'Origin' header in incoming requests with a list of allowed origins to ensure that
requests are being made from trusted sources.

Usage example:

.. code-block:: python

    app.add_middleware(CSRFProtectionMiddleware(allowed_origins=['https://example.com']))

Parameters:
    allowed_origins (List[str]): A list of trusted origins that are allowed to make requests.
    error_message (str): A custom error message that will be used when CSRF validation fails.

Note:
    This middleware may not work correctly with older browsers or when requests pass through reverse proxies
    that strip the 'Origin' header.
"""

from typing import List

from haru.middleware import Middleware
from haru.request import Request
from haru.exceptions import Forbidden

__all__ = ['CSRFProtectionMiddleware']


class CSRFProtectionMiddleware(Middleware):
    """
    CSRF Protection Middleware

    This middleware prevents Cross-Site Request Forgery (CSRF) attacks by
    comparing the 'Origin' header of the request with the server's list of allowed origins.

    :param allowed_origins: A list of trusted origins that are allowed to make requests.
    :type allowed_origins: List[str]
    :param error_message: A custom error message that is returned when CSRF validation fails.
    :type error_message: str
    """

    def __init__(self, allowed_origins: List[str], error_message: str = 'CSRF validation failed.'):
        """
        Initialize the `CSRFProtectionMiddleware` with a list of allowed origins and an optional error message.

        :param allowed_origins: A list of trusted origins that are allowed to make requests.
        :type allowed_origins: List[str]
        :param error_message: A custom error message that is returned when CSRF validation fails.
        :type error_message: str
        """
        super().__init__()
        self.allowed_origins = allowed_origins
        self.error_message = error_message

    def before_request(self, request: Request) -> None:
        """
        Validate the 'Origin' header of the incoming request. If the 'Origin' header is missing
        or does not match any of the allowed origins, the request is rejected with a 403 Forbidden response.

        :param request: The current HTTP request object.
        :type request: Request

        :raises Forbidden: If the 'Origin' header is missing or does not match any allowed origins.
        """
        origin = request.headers.get('Origin')
        if not origin:
            # If 'Origin' header is missing, reject the request
            raise Forbidden(description=self.error_message)

        if origin not in self.allowed_origins:
            raise Forbidden(description=self.error_message)

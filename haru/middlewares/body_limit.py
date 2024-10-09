"""
This module defines the `BodyLimitMiddleware` class, which enforces a limit on the size of
the request body in the Haru web framework. The middleware checks the 'Content-Length' header
or reads the body directly, raising an error if the size exceeds the specified limit.

If the request body exceeds the limit, a `RequestEntityTooLarge` exception is raised.

Usage example:

.. code-block:: python

    app.add_middleware(BodyLimitMiddleware(max_size=1024 * 1024))  # 1 MB limit

"""

from haru.middleware import Middleware
from haru.request import Request
from haru.exceptions import RequestEntityTooLarge

__all__ = ['BodyLimitMiddleware']


class BodyLimitMiddleware(Middleware):
    """
    Body Limit Middleware

    This middleware limits the size of the request body. It first checks the
    'Content-Length' header. If it's absent, it reads the body and raises an
    error if the size exceeds the specified limit.

    :param max_size: The maximum allowed size of the request body in bytes.
    :type max_size: int

    :raises RequestEntityTooLarge: If the request body exceeds the specified limit.
    """

    def __init__(self, max_size: int):
        """
        Initialize the `BodyLimitMiddleware` with the specified maximum body size.

        :param max_size: The maximum allowed size of the request body in bytes.
        :type max_size: int
        """
        super().__init__()
        self.max_size = max_size

    def before_request(self, request: Request) -> None:
        """
        Process the request before it reaches the main route handler.
        This method checks the 'Content-Length' header and raises an exception if the request body
        exceeds the allowed size. If the 'Content-Length' header is not present, the body is read
        and checked manually.

        :param request: The current HTTP request object.
        :type request: Request

        :raises RequestEntityTooLarge: If the request body exceeds the specified size limit.
        """
        content_length = request.headers.get('Content-Length')
        if content_length is not None:
            try:
                content_length = int(content_length)
                if content_length > self.max_size:
                    raise RequestEntityTooLarge(
                        description=f'Request body too large. Maximum allowed is {self.max_size} bytes.'
                    )
            except ValueError:
                # Invalid Content-Length header
                pass
        else:
            # Read the body and check the size manually
            body = request.get_body(max_size=self.max_size)
            if body is None:
                raise RequestEntityTooLarge(
                    description=f'Request body too large. Maximum allowed is {self.max_size} bytes.'
                )
            request.body = body

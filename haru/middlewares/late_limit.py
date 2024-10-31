"""
This module provides the `RateLimitMiddleware` class, which limits the rate of incoming requests
based on a specified key (e.g., IP address, User-Agent). It does not use any external storage,
making it lightweight and suitable for simple rate-limiting needs.
"""

from time import time
from typing import Callable, Dict, Optional
from haru.middleware import Middleware
from haru.request import Request
from haru.response import Response
from haru.exceptions import TooManyRequests

__all__ = ['RateLimitMiddleware']


class RateLimitMiddleware(Middleware):
    """
    Rate Limiting Middleware

    This middleware limits the rate of incoming requests based on a specified key (e.g., IP address, User-Agent).
    It does not use any external storage, making it lightweight and suitable for simple rate-limiting needs.

    :param limit: The maximum number of requests allowed within the specified period.
    :type limit: int
    :param period: The duration in seconds for the rate limit window (e.g., 60 for a minute).
    :type period: int
    :param key_func: A function that generates a unique key for each request to apply rate limiting.
                     Defaults to using the client's IP address.
    :type key_func: Callable[[Request], str]
    :param error_message: Custom error message returned when the rate limit is exceeded.
    :type error_message: str
    """

    def __init__(
        self,
        limit: int,
        period: int,
        key_func: Optional[Callable[[Request], str]] = None,
        error_message: str = 'Rate limit exceeded. Please try again later.'
    ):
        """
        Initialize the RateLimitMiddleware with specified options.

        :param limit: The maximum number of requests allowed within the period.
        :type limit: int
        :param period: The period in seconds during which the limit applies.
        :type period: int
        :param key_func: A function to generate a unique key for rate limiting. Defaults to IP-based limiting.
        :type key_func: Callable[[Request], str]
        :param error_message: The message to return when the limit is exceeded.
        :type error_message: str
        """
        super().__init__()
        self.limit = limit
        self.period = period
        self.key_func = key_func or (lambda request: request.remote_addr)
        self.error_message = error_message
        self.request_counts: Dict[str, Dict[str, int]] = {}

    def before_request(self, request: Request) -> None:
        """
        Process the request before it reaches the main route handler.
        This method checks if the rate limit has been exceeded based on the generated key.

        :param request: The current HTTP request object.
        :type request: Request

        :raises TooManyRequests: If the request count exceeds the limit within the specified period.
        """
        key = self.key_func(request)
        current_time = time()
        window_start = int(current_time // self.period) * self.period

        if key not in self.request_counts:
            self.request_counts[key] = {"count": 0, "start": window_start}

        data = self.request_counts[key]

        # Reset the count if the current period has elapsed
        if data["start"] != window_start:
            data["count"] = 0
            data["start"] = window_start

        if data["count"] >= self.limit:
            raise TooManyRequests(description=self.error_message)

        # Increment the request count
        data["count"] += 1

    def after_response(self, request: Request, response: Response) -> Response:
        """
        Optionally modify the response to include rate limit headers.

        :param request: The HTTP request object.
        :type request: Request
        :param response: The HTTP response object.
        :type response: Response
        :return: The response object, potentially with rate limit headers added.
        :rtype: Response
        """
        key = self.key_func(request)
        data = self.request_counts[key]
        remaining = max(0, self.limit - data["count"])

        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(data["start"] + self.period)

        return response

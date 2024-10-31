"""
This module defines the `LoggerMiddleware` class, which logs incoming HTTP requests and outgoing
responses in the Haru web framework. It logs details such as the HTTP method, request path,
status code, and the time taken to process the request.

Usage example:

.. code-block:: python

    app.add_middleware(LoggerMiddleware(logger=logging.getLogger('haru'), level=logging.INFO))

Parameters:
    logger (Optional[logging.Logger]): An optional `logging.Logger` instance to use for logging.
                                        If not provided, the root logger is used.
    level (int): The logging level for the log messages (e.g., logging.INFO, logging.DEBUG).

Note:
    This middleware should be added early in the middleware chain to capture the entire request processing time.
"""

import logging
from time import time
from typing import Optional
from haru.middleware import Middleware
from haru.request import Request
from haru.response import Response

__all__ = ["LoggerMiddleware"]


class LoggerMiddleware(Middleware):
    """
    Logger Middleware

    This middleware logs incoming requests and outgoing responses, including
    the method, path, status code, and response time.

    :param logger: A `logging.Logger` instance to use for logging. If not provided, the root logger is used.
    :type logger: Optional[logging.Logger]
    :param level: The logging level to use for log messages (e.g., logging.INFO, logging.DEBUG).
    :type level: int

    :example:
        app.add_middleware(LoggerMiddleware(logger=logging.getLogger('haru'), level=logging.INFO))
    """

    def __init__(
        self, logger: Optional[logging.Logger] = None, level: int = logging.INFO
    ):
        """
        Initialize the `LoggerMiddleware` with a logger instance and logging level.

        :param logger: A `logging.Logger` instance to use for logging. If not provided, the root logger is used.
        :type logger: Optional[logging.Logger]
        :param level: The logging level to use for log messages.
        :type level: int
        """
        super().__init__()
        self.logger = logger or logging.getLogger()
        self.level = level

    def before_request(self, request: Request) -> None:
        """
        Record the start time of the request. This is used to calculate the response time.

        :param request: The current HTTP request object.
        :type request: Request
        """
        request.start_time = time()

    def after_response(self, request: Request, response: Response) -> None:
        """
        Log details about the completed request, including the method, path, status code,
        and the time taken to process the request.

        :param request: The current HTTP request object.
        :type request: Request
        :param response: The HTTP response object that was generated by the route handler.
        :type response: Response
        """
        duration = time() - request.start_time
        message = (
            f"{request.method} {request.path} {response.status_code} {duration:.4f}s"
        )
        self.logger.log(self.level, message)

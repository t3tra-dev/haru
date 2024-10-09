"""
This module defines the `Middleware` class, which serves as a base class for creating middleware
in the Haru web framework. Middleware components allow developers to modify the request and response
objects at different stages of the request lifecycle (before and after request handling,
and before and after the response is sent).

Developers can extend this class to implement custom middleware with specific behavior.
"""

from typing import Optional, Dict, Any

from .request import Request
from .response import Response

__all__ = ['Middleware']


class Middleware:
    """
    The base class for middleware in the Haru web framework. Middleware allows custom processing
    of requests and responses at various stages in the request-response cycle.

    :param options: A dictionary of options that can be passed to the middleware.
    :type options: Dict[str, Any]
    """

    def __init__(self, **options):
        """
        Initialize the middleware with the given options.

        :param options: Options for configuring the middleware.
        :type options: Dict[str, Any]
        """
        self.options: Dict[str, Any] = options

    def update(self, **options) -> None:
        """
        Update the middleware's options.

        :param options: New options to update the middleware's configuration.
        :type options: Dict[str, Any]
        """
        self.options.update(options)

    async def before_request(self, request: Request) -> None:
        """
        Called before the request is processed. This method can be overridden to implement
        behavior that needs to occur before the main request handler is executed.

        :param request: The request object that is being processed.
        :type request: Request
        """
        pass

    async def after_request(self, request: Request, response: Response) -> Optional[Response]:
        """
        Called after the request is processed but before the response is sent. This method
        can modify the response object if necessary.

        :param request: The request object that was processed.
        :type request: Request
        :param response: The response object that is about to be sent to the client.
        :type response: Response
        :return: The (possibly modified) response object.
        :rtype: Optional[Response]
        """
        return response

    async def before_response(self, request: Request, response: Response) -> None:
        """
        Called right before the response is sent to the client. This method can be overridden
        to implement behavior that needs to occur just before the response is returned.

        :param request: The request object that was processed.
        :type request: Request
        :param response: The response object that is about to be sent to the client.
        :type response: Response
        """
        pass

    async def after_response(self, request: Request, response: Response) -> None:
        """
        Called after the response has been sent to the client. This method can be overridden
        to implement behavior that needs to occur after the response is sent.

        :param request: The request object that was processed.
        :type request: Request
        :param response: The response object that was sent to the client.
        :type response: Response
        """
        pass

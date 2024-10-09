"""
This module defines custom exceptions for the Haru web framework, including various HTTP exceptions
that correspond to different HTTP status codes. These exceptions allow the framework to handle
error conditions and respond with the appropriate HTTP status and messages.

The primary base class for HTTP-related exceptions is `HTTPException`, which is used to represent
any HTTP error condition. More specific exceptions (e.g., `BadRequest`, `NotFound`, etc.) are
defined for common HTTP error statuses.
"""

from http import HTTPStatus
from typing import Optional, List, Dict

__all__ = [
    'HaruException',
    'HTTPException',
    'BadRequest',
    'Unauthorized',
    'PaymentRequired',
    'Forbidden',
    'NotFound',
    'MethodNotAllowed',
    'NotAcceptable',
    'ProxyAuthenticationRequired',
    'RequestTimeout',
    'Conflict',
    'Gone',
    'LengthRequired',
    'PreconditionFailed',
    'RequestEntityTooLarge',
    'URITooLong',
    'UnsupportedMediaType',
    'RangeNotSatisfiable',
    'ExpectationFailed',
    'ImATeapot',
    'MisdirectedRequest',
    'UnprocessableEntity',
    'Locked',
    'FailedDependency',
    'TooEarly',
    'UpgradeRequired',
    'PreconditionRequired',
    'TooManyRequests',
    'RequestHeaderFieldsTooLarge',
    'UnavailableForLegalReasons',
    'InternalServerError',
    'NotImplemented',
    'BadGateway',
    'ServiceUnavailable',
    'GatewayTimeout',
    'HTTPVersionNotSupported',
    'VariantAlsoNegotiates',
    'InsufficientStorage',
    'LoopDetected',
    'NotExtended',
    'NetworkAuthenticationRequired',
]


class HaruException(Exception):
    """
    The base exception class for the Haru framework. All custom exceptions in Haru should
    inherit from this class.
    """


class HTTPException(HaruException):
    """
    The base class for HTTP exceptions in the Haru framework.

    :param status_code: The HTTP status code associated with the exception.
    :type status_code: int
    :param description: An optional description of the error, which defaults to the standard HTTP status phrase.
    :type description: Optional[str]
    :param headers: Optional headers to be included in the HTTP response.
    :type headers: Optional[Dict[str, str]]
    """

    def __init__(self, status_code: int, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        self.status_code = status_code
        self.description = description or HTTPStatus(status_code).phrase
        self.headers = headers or {}
        super().__init__(f"{status_code} {self.description}")


class BadRequest(HTTPException):
    """Exception for 400 Bad Request HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.BAD_REQUEST, description)


class Unauthorized(HTTPException):
    """Exception for 401 Unauthorized HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.UNAUTHORIZED, description)


class PaymentRequired(HTTPException):
    """Exception for 402 Payment Required HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.PAYMENT_REQUIRED, description)


class Forbidden(HTTPException):
    """Exception for 403 Forbidden HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.FORBIDDEN, description)


class NotFound(HTTPException):
    """Exception for 404 Not Found HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.NOT_FOUND, description)


class MethodNotAllowed(HTTPException):
    """
    Exception for 405 Method Not Allowed HTTP status.

    :param allowed_methods: A list of allowed HTTP methods for the resource.
    :type allowed_methods: List[str]
    """

    def __init__(self, allowed_methods: List[str], description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        headers = {'Allow': ', '.join(sorted(set(allowed_methods)))}
        super().__init__(HTTPStatus.METHOD_NOT_ALLOWED, description, headers)
        self.allowed_methods = allowed_methods


class NotAcceptable(HTTPException):
    """Exception for 406 Not Acceptable HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.NOT_ACCEPTABLE, description)


class ProxyAuthenticationRequired(HTTPException):
    """Exception for 407 Proxy Authentication Required HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.PROXY_AUTHENTICATION_REQUIRED, description)


class RequestTimeout(HTTPException):
    """Exception for 408 Request Timeout HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.REQUEST_TIMEOUT, description)


class Conflict(HTTPException):
    """Exception for 409 Conflict HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.CONFLICT, description)


class Gone(HTTPException):
    """Exception for 410 Gone HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.GONE, description)


class LengthRequired(HTTPException):
    """Exception for 411 Length Required HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.LENGTH_REQUIRED, description)


class PreconditionFailed(HTTPException):
    """Exception for 412 Precondition Failed HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.PRECONDITION_FAILED, description)


class RequestEntityTooLarge(HTTPException):
    """Exception for 413 Request Entity Too Large HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, description)


class URITooLong(HTTPException):
    """Exception for 414 URI Too Long HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.REQUEST_URI_TOO_LONG, description)


class UnsupportedMediaType(HTTPException):
    """Exception for 415 Unsupported Media Type HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, description)


class RangeNotSatisfiable(HTTPException):
    """Exception for 416 Range Not Satisfiable HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE, description)


class ExpectationFailed(HTTPException):
    """Exception for 417 Expectation Failed HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.EXPECTATION_FAILED, description)


class ImATeapot(HTTPException):
    """Exception for 418 I'm a Teapot HTTP status (RFC 2324)."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.IM_A_TEAPOT, description)


class MisdirectedRequest(HTTPException):
    """Exception for 421 Misdirected Request HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.MISDIRECTED_REQUEST, description)


class UnprocessableEntity(HTTPException):
    """Exception for 422 Unprocessable Entity HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, description)


class Locked(HTTPException):
    """Exception for 423 Locked HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.LOCKED, description)


class FailedDependency(HTTPException):
    """Exception for 424 Failed Dependency HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.FAILED_DEPENDENCY, description)


class TooEarly(HTTPException):
    """Exception for 425 Too Early HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.TOO_EARLY, description)


class UpgradeRequired(HTTPException):
    """Exception for 426 Upgrade Required HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.UPGRADE_REQUIRED, description)


class PreconditionRequired(HTTPException):
    """Exception for 428 Precondition Required HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.PRECONDITION_REQUIRED, description)


class TooManyRequests(HTTPException):
    """Exception for 429 Too Many Requests HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.TOO_MANY_REQUESTS, description)


class RequestHeaderFieldsTooLarge(HTTPException):
    """Exception for 431 Request Header Fields Too Large HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.REQUEST_HEADER_FIELDS_TOO_LARGE, description)


class UnavailableForLegalReasons(HTTPException):
    """Exception for 451 Unavailable For Legal Reasons HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.UNAVAILABLE_FOR_LEGAL_REASONS, description)


class InternalServerError(HTTPException):
    """Exception for 500 Internal Server Error HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.INTERNAL_SERVER_ERROR, description)


class NotImplemented(HTTPException):
    """Exception for 501 Not Implemented HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.NOT_IMPLEMENTED, description)


class BadGateway(HTTPException):
    """Exception for 502 Bad Gateway HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.BAD_GATEWAY, description)


class ServiceUnavailable(HTTPException):
    """Exception for 503 Service Unavailable HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.SERVICE_UNAVAILABLE, description)


class GatewayTimeout(HTTPException):
    """Exception for 504 Gateway Timeout HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.GATEWAY_TIMEOUT, description)


class HTTPVersionNotSupported(HTTPException):
    """Exception for 505 HTTP Version Not Supported HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.HTTP_VERSION_NOT_SUPPORTED, description)


class VariantAlsoNegotiates(HTTPException):
    """Exception for 506 Variant Also Negotiates HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.VARIANT_ALSO_NEGOTIATES, description)


class InsufficientStorage(HTTPException):
    """Exception for 507 Insufficient Storage HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.INSUFFICIENT_STORAGE, description)


class LoopDetected(HTTPException):
    """Exception for 508 Loop Detected HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.LOOP_DETECTED, description)


class NotExtended(HTTPException):
    """Exception for 510 Not Extended HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.NOT_EXTENDED, description)


class NetworkAuthenticationRequired(HTTPException):
    """Exception for 511 Network Authentication Required HTTP status."""

    def __init__(self, description: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(HTTPStatus.NETWORK_AUTHENTICATION_REQUIRED, description)

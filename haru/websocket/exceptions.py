from __future__ import annotations

from typing import Optional

from ..exceptions import HaruException

__all__ = [
    "WebSocketError",
    "ConnectionError",
    "ConnectionClosed",
    "ConnectionClosedOK",
    "ConnectionClosedError",
    "ProtocolError",
    "HandshakeError",
    "InvalidHandshake",
    "SecurityError",
    "InvalidURI",
    "PayloadError",
    "FrameError",
    "HeaderError",
]


class WebSocketError(HaruException):
    """Base exception for all WebSocket related errors."""


class ConnectionError(WebSocketError):
    """Base class for connection related errors."""

    def __init__(
        self, message: str, *, code: Optional[int] = None, reason: Optional[str] = None
    ) -> None:
        super().__init__(message)
        self.code = code
        self.reason = reason

    def __str__(self) -> str:
        message = str(super().__str__())
        if self.code is not None:
            message = f"{message} (code={self.code})"
        if self.reason is not None:
            message = f"{message}, reason={self.reason!r}"
        return message


class ConnectionClosed(ConnectionError):
    """Raised when trying to interact with a closed connection."""


class ConnectionClosedOK(ConnectionClosed):
    """Connection closed normally (code=1000 or 1001)."""


class ConnectionClosedError(ConnectionClosed):
    """Connection closed with an error."""


class ProtocolError(WebSocketError):
    """Raised when a protocol error occurs."""


class HandshakeError(WebSocketError):
    """Base class for WebSocket handshake errors."""


class InvalidHandshake(HandshakeError):
    """Raised when the handshake response is invalid."""


class SecurityError(HandshakeError):
    """Raised when a security error occurs."""

    def __init__(self, message: str, recommended_action: Optional[str] = None) -> None:
        super().__init__(message)
        self.recommended_action = recommended_action

    def __str__(self) -> str:
        message = super().__str__()
        if self.recommended_action:
            message = f"{message}\nRecommended action: {self.recommended_action}"
        return message


class InvalidURI(WebSocketError):
    """Raised when an invalid WebSocket URI is provided."""

    def __init__(self, uri: str, message: str) -> None:
        super().__init__(f"Invalid WebSocket URI '{uri}': {message}")
        self.uri = uri


class PayloadError(ProtocolError):
    """Raised when there's an error with the message payload."""


class FrameError(ProtocolError):
    """Raised when there's an error with a WebSocket frame."""


class HeaderError(HandshakeError):
    """Raised when there's an error with HTTP headers."""

    def __init__(
        self,
        header_name: str,
        header_value: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        if message is None:
            if header_value is None:
                message = f"Missing {header_name} header"
            else:
                message = f"Invalid {header_name} header: {header_value}"
        super().__init__(message)
        self.header_name = header_name
        self.header_value = header_value

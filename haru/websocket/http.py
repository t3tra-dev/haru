from __future__ import annotations

import base64
import collections
import email.utils
import hashlib
import http
import re
from typing import Dict, Iterator, List, NamedTuple, Optional, Tuple, Union

from .exceptions import HandshakeError, HeaderError, SecurityError

__all__ = [
    "Headers",
    "Request",
    "Response",
    "parse_request",
    "parse_response",
    "build_response",
]


class Headers(collections.abc.MutableMapping):
    """
    Case-insensitive HTTP headers collection.

    .. note::
        Header names are case-insensitive but the original case is preserved.
        Header values are stored as strings.

    :param headers: Initial headers data
    """

    __slots__ = ('_dict', '_list')

    def __init__(self, headers: Optional[Union[Dict[str, str], List[Tuple[str, str]]]] = None) -> None:
        self._dict: Dict[str, List[str]] = {}  # lowercase_name -> [values]
        self._list: List[Tuple[str, str]] = []  # [(name, value)] with original case

        if headers:
            if isinstance(headers, dict):
                headers = headers.items()
            for name, value in headers:
                self.add(name, value)

    def add(self, name: str, value: str) -> None:
        """
        Add a header without removing existing headers of the same name.

        :param name: Header name
        :param value: Header value
        """
        name_lower = name.lower()
        self._dict.setdefault(name_lower, []).append(value)
        self._list.append((name, value))

    def get_all(self, name: str) -> List[str]:
        """
        Get all values for a header.

        :param name: Header name
        :return: List of values
        """
        return self._dict.get(name.lower(), [])

    def __getitem__(self, name: str) -> str:
        """
        Get the first value of a header.

        :param name: Header name
        :return: Header value
        :raises KeyError: If the header doesn't exist
        :raises ValueError: If there are multiple values
        """
        values = self.get_all(name)
        if not values:
            raise KeyError(name)
        if len(values) > 1:
            raise ValueError(f"Multiple values for header {name!r}")
        return values[0]

    def __setitem__(self, name: str, value: str) -> None:
        """Set a header, removing any existing values."""
        name_lower = name.lower()
        self._dict[name_lower] = [value]
        self._list = [(k, v) for k, v in self._list if k.lower() != name_lower]
        self._list.append((name, value))

    def __delitem__(self, name: str) -> None:
        """Remove all values for a header."""
        name_lower = name.lower()
        del self._dict[name_lower]
        self._list = [(k, v) for k, v in self._list if k.lower() != name_lower]

    def __iter__(self) -> Iterator[str]:
        """Iterate over header names (with original case)."""
        seen = set()
        for name, _ in self._list:
            name_lower = name.lower()
            if name_lower not in seen:
                seen.add(name_lower)
                yield name

    def __len__(self) -> int:
        """Return the number of distinct headers."""
        return len(self._dict)

    def __str__(self) -> str:
        """Format headers for HTTP/1.1 transmission."""
        return "".join(f"{k}: {v}\r\n" for k, v in self._list) + "\r\n"

    def __repr__(self) -> str:
        """Return a string representation for debugging."""
        return f"{self.__class__.__name__}({self._list!r})"


class Request(NamedTuple):
    """
    HTTP request data.

    :ivar method: HTTP method
    :ivar target: Request target (path)
    :ivar headers: Request headers
    :ivar body: Request body
    """

    method: str
    target: str
    headers: Headers
    body: Optional[bytes] = None


class Response(NamedTuple):
    """
    HTTP response data.

    :ivar status_code: HTTP status code
    :ivar reason: Status reason phrase
    :ivar headers: Response headers
    :ivar body: Response body
    """

    status_code: int
    reason: str
    headers: Headers
    body: Optional[bytes] = None


def parse_request(data: bytes) -> Tuple[Request, int]:
    """
    Parse an HTTP request.

    :param data: Raw request data
    :return: Tuple of (parsed request, bytes consumed)
    :raises HandshakeError: If the request is malformed
    """
    try:
        header_end = data.index(b"\r\n\r\n")
    except ValueError:
        raise HandshakeError("Incomplete HTTP request")

    headers_data = data[:header_end]
    consumed = header_end + 4

    try:
        lines = headers_data.decode("ascii").splitlines()
    except UnicodeDecodeError:
        raise HandshakeError("Invalid characters in request")

    if not lines:
        raise HandshakeError("Empty request")

    try:
        method, target, version = lines[0].split(" ", 2)
    except ValueError:
        raise HandshakeError("Invalid request line")

    if version != "HTTP/1.1":
        raise HandshakeError(f"Unsupported HTTP version: {version}")

    if method != "GET":
        raise HandshakeError(f"Unsupported HTTP method: {method}")

    headers = Headers()
    for line in lines[1:]:
        try:
            name, value = line.split(":", 1)
        except ValueError:
            raise HandshakeError(f"Invalid header line: {line}")

        name = name.strip()
        if not _is_valid_header_name(name):
            raise HandshakeError(f"Invalid header name: {name}")

        value = value.strip()
        if not _is_valid_header_value(value):
            raise HandshakeError(f"Invalid header value: {value}")

        headers.add(name, value)

    return Request(method, target, headers), consumed


def parse_response(data: bytes) -> Tuple[Response, int]:
    """
    Parse an HTTP response.

    :param data: Raw response data
    :return: Tuple of (parsed response, bytes consumed)
    :raises HandshakeError: If the response is malformed
    """
    try:
        header_end = data.index(b"\r\n\r\n")
    except ValueError:
        raise HandshakeError("Incomplete HTTP response")

    headers_data = data[:header_end]
    consumed = header_end + 4

    try:
        lines = headers_data.decode("ascii").splitlines()
    except UnicodeDecodeError:
        raise HandshakeError("Invalid characters in response")

    if not lines:
        raise HandshakeError("Empty response")

    try:
        version, status, *reason = lines[0].split(" ", 2)
        reason = reason[0] if reason else ""
    except ValueError:
        raise HandshakeError("Invalid status line")

    if version != "HTTP/1.1":
        raise HandshakeError(f"Unsupported HTTP version: {version}")

    try:
        status_code = int(status)
        if not 100 <= status_code <= 599:
            raise ValueError
    except ValueError:
        raise HandshakeError(f"Invalid status code: {status}")

    headers = Headers()
    for line in lines[1:]:
        try:
            name, value = line.split(":", 1)
        except ValueError:
            raise HandshakeError(f"Invalid header line: {line}")

        name = name.strip()
        if not _is_valid_header_name(name):
            raise HandshakeError(f"Invalid header name: {name}")

        value = value.strip()
        if not _is_valid_header_value(value):
            raise HandshakeError(f"Invalid header value: {value}")

        headers.add(name, value)

    return Response(status_code, reason, headers), consumed


def build_response(
    status: Union[http.HTTPStatus, int],
    headers: Optional[Headers] = None,
    body: Optional[bytes] = None,
) -> bytes:
    """
    Build an HTTP response.

    :param status: HTTP status code or HTTPStatus enum
    :param headers: Response headers
    :param body: Response body
    :return: Encoded response
    """
    if isinstance(status, http.HTTPStatus):
        status_code = status.value
        reason = status.phrase
    else:
        status_code = status
        reason = http.HTTPStatus(status).phrase

    if headers is None:
        headers = Headers()

    if "Date" not in headers:
        headers["Date"] = email.utils.formatdate(usegmt=True)

    if body is not None:
        headers["Content-Length"] = str(len(body))

    response = f"HTTP/1.1 {status_code} {reason}\r\n{headers}"
    data = response.encode("ascii")

    if body is not None:
        data += body

    return data


def validate_handshake(
    headers: Headers,
    *,
    client_mode: bool = False,
) -> None:
    """
    Validate WebSocket handshake headers according to RFC 6455.

    :param headers: Headers to validate
    :param client_mode: Whether to validate as client or server
    :raises HandshakeError: If headers are invalid
    :raises SecurityError: If security-related headers are invalid
    """
    def require_header(name: str) -> str:
        try:
            return headers[name]
        except KeyError:
            raise HeaderError(f"Missing required header: {name}")
        except ValueError as exc:
            raise HeaderError(f"Invalid header: {name}") from exc

    # Connection header must include "Upgrade"
    connection = require_header("Connection")
    if "upgrade" not in {token.strip().lower() for token in connection.split(",")}:
        raise HeaderError("Invalid Connection header: must include 'Upgrade'")

    # Upgrade header must be "websocket"
    upgrade = require_header("Upgrade")
    if upgrade.lower() != "websocket":
        raise HeaderError("Invalid Upgrade header: must be 'websocket'")

    # Sec-WebSocket-Version must be 13
    version = require_header("Sec-WebSocket-Version")
    if version != "13":
        raise HeaderError("Invalid Sec-WebSocket-Version header: must be '13'")

    if client_mode:
        # Validate Sec-WebSocket-Accept
        accept = require_header("Sec-WebSocket-Accept")
        if not _is_valid_accept(accept):
            raise SecurityError("Invalid Sec-WebSocket-Accept header")
    else:
        # Validate Sec-WebSocket-Key
        key = require_header("Sec-WebSocket-Key")
        if not _is_valid_key(key):
            raise SecurityError("Invalid Sec-WebSocket-Key header")


# Helper functions

def _is_valid_header_name(name: str) -> bool:
    """Check if a header name is valid according to RFC 7230."""
    return bool(re.match(r"^[!#$%&'*+\-.^_`|~0-9a-zA-Z]+$", name))


def _is_valid_header_value(value: str) -> bool:
    """Check if a header value is valid according to RFC 7230."""
    return bool(re.match(r"^[ \t]*[\x21-\x7E\x80-\xFF]*[ \t]*$", value))


def _is_valid_key(key: str) -> bool:
    """Check if a Sec-WebSocket-Key is valid."""
    try:
        decoded = base64.b64decode(key.encode(), validate=True)
        return len(decoded) == 16
    except Exception:
        return False


def _is_valid_accept(accept: str) -> bool:
    """Check if a Sec-WebSocket-Accept is valid."""
    try:
        decoded = base64.b64decode(accept.encode(), validate=True)
        return len(decoded) == 20
    except Exception:
        return False


def compute_accept_key(key: str) -> str:
    """
    Compute Sec-WebSocket-Accept header value.

    :param key: Sec-WebSocket-Key header value
    :return: Computed accept key
    """
    GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    accept = hashlib.sha1((key + GUID).encode()).digest()
    return base64.b64encode(accept).decode()

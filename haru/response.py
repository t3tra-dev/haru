"""
This module defines the `Response` class, which represents an HTTP response in the Haru web framework.
The `Response` class is responsible for managing the response content, headers, status code,
and other properties that are sent back to the client after processing an HTTP request.
"""

from typing import Any, Dict, Optional
import mimetypes
import os
import json
from .wrappers import FileWrapper, BytesWrapper

__all__ = ['Response', 'redirect']


class Response:
    """
    Represents an HTTP response. This class encapsulates the content, status code, headers,
    and other attributes of an HTTP response that will be sent back to the client.
    """

    def __init__(
        self,
        content: Any,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None,
        filename: Optional[str] = None,
        as_attachment: bool = False,
    ):
        self.content: Any = content
        self.status_code: int = status_code
        self.headers: Dict[str, str] = headers or {}
        self.content_type: Optional[str] = content_type
        self.filename: Optional[str] = filename
        self.as_attachment: bool = as_attachment

        # Automatically set Content-Type if not provided
        if self.content_type is None:
            self.content_type = self._infer_content_type()

        # Set Content-Type header
        self.headers.setdefault('Content-Type', self.content_type)

        # Set Content-Disposition header for file downloads
        if self.as_attachment:
            if self.filename:
                attachment_filename = os.path.basename(self.filename)
            elif isinstance(content, FileWrapper):
                attachment_filename = os.path.basename(content.filepath)
            else:
                attachment_filename = 'download'
            self.headers['Content-Disposition'] = f'attachment; filename="{attachment_filename}"'

    def _infer_content_type(self) -> str:
        """
        Infers the content type based on the content.

        :return: The inferred content type.
        :rtype: str
        """
        if isinstance(self.content, str):
            return 'text/plain; charset=utf-8'
        elif isinstance(self.content, bytes):
            return 'application/octet-stream'
        elif isinstance(self.content, (dict, list)):
            return 'application/json'
        elif isinstance(self.content, FileWrapper):
            return mimetypes.guess_type(self.content.filepath)[0] or 'application/octet-stream'
        elif isinstance(self.content, BytesWrapper):
            return 'application/octet-stream'
        else:
            return 'application/octet-stream'

    def iter_content(self):
        """
        Yield the response content in chunks. This method is useful for streaming large files
        or binary data in parts.

        :raises TypeError: If the content type is unsupported.
        :return: A generator yielding chunks of response content.
        :rtype: Iterator[bytes]
        """
        if isinstance(self.content, (bytes, str)):
            yield self.get_content()
        elif isinstance(self.content, (FileWrapper, BytesWrapper)):
            yield from self.content
        else:
            raise TypeError("Unsupported content type for response")

    def get_content(self) -> bytes:
        """
        Return the response content as bytes.

        :raises TypeError: If the content is of an unsupported type.
        :return: The response content as bytes.
        :rtype: bytes
        """
        if isinstance(self.content, bytes):
            return self.content
        elif isinstance(self.content, str):
            return self.content.encode('utf-8')
        elif isinstance(self.content, (dict, list)):
            return json.dumps(self.content).encode('utf-8')
        else:
            return str(self.content).encode('utf-8')


def redirect(location: str, status_code: int = 302) -> Response:
    """
    Returns a Response object that redirects the client to the specified location.

    :param location: The URL to redirect to.
    :type location: str
    :param status_code: The HTTP status code for the redirect (default is 302).
    :type status_code: int
    :return: A Response object configured to redirect the client.
    :rtype: Response
    """
    return Response(
        content='',
        status_code=status_code,
        headers={'Location': location}
    )

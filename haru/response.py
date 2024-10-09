"""
This module defines the `Response` class, which represents an HTTP response in the Haru web framework.
The `Response` class is responsible for managing the response content, headers, status code,
and other properties that are sent back to the client after processing an HTTP request.
"""

from typing import Any, Dict, Optional
import mimetypes
import os
from .wrappers import FileWrapper, BytesWrapper

__all__ = ['Response']


class Response:
    """
    Represents an HTTP response. This class encapsulates the content, status code, headers,
    and other attributes of an HTTP response that will be sent back to the client.

    :param content: The content of the response, which can be a string, bytes, or a file-like object.
    :type content: Any
    :param status_code: The HTTP status code for the response (default is 200).
    :type status_code: int
    :param headers: A dictionary of additional headers for the response.
    :type headers: Optional[Dict[str, str]]
    :param content_type: The MIME type of the response content. If not provided, it is inferred based on the content.
    :type content_type: Optional[str]
    :param filename: The filename for file downloads. If provided, sets the Content-Disposition header for downloads.
    :type filename: Optional[str]
    :param as_attachment: A boolean indicating whether the response should be treated as a file attachment.
    :type as_attachment: bool
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
            if isinstance(content, (str, bytes)):
                self.content_type = 'text/plain; charset=utf-8'
            elif isinstance(content, FileWrapper):
                self.content_type = mimetypes.guess_type(content.filepath)[0] or 'application/octet-stream'
            elif isinstance(content, BytesWrapper):
                self.content_type = 'application/octet-stream'
            else:
                self.content_type = 'application/octet-stream'

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
        elif isinstance(self.content, FileWrapper):
            yield from self.content
        elif isinstance(self.content, BytesWrapper):
            yield from self.content
        else:
            raise TypeError("Unsupported content type for response")

    def get_content(self) -> bytes:
        """
        Return the response content as bytes. If the content is a string, it is encoded to UTF-8.

        :raises TypeError: If the content is neither bytes nor a string.
        :return: The response content as bytes.
        :rtype: bytes
        """
        if isinstance(self.content, bytes):
            return self.content
        elif isinstance(self.content, str):
            return self.content.encode('utf-8')
        else:
            raise TypeError("Response content must be str or bytes")

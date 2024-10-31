"""
This module provides the `CompressMiddleware` class, which compresses HTTP responses based on the
Accept-Encoding header and content type. It supports gzip and deflate encoding methods.
"""

import re
import gzip
import zlib
from typing import Optional, Literal

from haru.request import Request
from haru.response import Response
from haru.middleware import Middleware

SupportedEncodings = Literal["gzip", "deflate"]

COMPRESSIBLE_CONTENT_TYPE_REGEX = re.compile(
    r"^(text/.*)|(application/(json|javascript|xml|xhtml\+xml|x-www-form-urlencoded))$",
    re.IGNORECASE,
)


class CompressMiddleware(Middleware):
    """
    Middleware to compress HTTP responses based on the Accept-Encoding header and content type.
    Supports gzip and deflate encoding methods.
    """

    def __init__(
        self, encoding: Optional[SupportedEncodings] = None, threshold: int = 1024
    ):
        """
        Initialize the CompressMiddleware.

        :param encoding: The compression encoding to use ('gzip' or 'deflate'). If None, selects based on Accept-Encoding.
        :type encoding: Optional[SupportedEncodings]
        :param threshold: The minimum response size in bytes to apply compression.
        :type threshold: int
        """
        self.encoding: Optional[SupportedEncodings] = encoding
        self.threshold: int = threshold

    async def before_response(self, request: Request, response: Response) -> None:
        """
        Modify the response before it's sent to the client, applying compression if applicable.

        :param request: The incoming HTTP request.
        :type request: Request
        :param response: The HTTP response to be sent.
        :type response: Response
        """
        # Check if response is already encoded
        if "Content-Encoding" in response.headers:
            return

        # Check if request method is HEAD
        if request.method.upper() == "HEAD":
            return

        # Get Content-Length
        content_length = response.headers.get("Content-Length")
        if content_length is not None and int(content_length) < self.threshold:
            return

        # Check if content type is compressible
        content_type = response.headers.get("Content-Type", "")
        if not self._is_compressible_content_type(content_type):
            return

        # Check Cache-Control header for 'no-transform'
        cache_control = response.headers.get("Cache-Control", "")
        if "no-transform" in cache_control.lower():
            return

        # Determine accepted encodings
        accept_encoding = request.headers.get("Accept-Encoding", "")
        supported_encodings = ["gzip", "deflate"]
        encoding = self.encoding

        if not encoding:
            # Select encoding based on client's Accept-Encoding
            for enc in supported_encodings:
                if enc in accept_encoding:
                    encoding = enc  # type: ignore
                    break

        if not encoding:
            return  # No compatible encoding found

        # Compress the response content
        original_content = await self._get_response_content(response)
        if not original_content:
            return

        compressed_content = self._compress_content(original_content, encoding)
        response.content = compressed_content
        response.headers["Content-Encoding"] = encoding
        response.headers["Content-Length"] = str(len(compressed_content))

        # Remove ETag header if present (since content has changed)
        response.headers.pop("ETag", None)

    def _is_compressible_content_type(self, content_type: str) -> bool:
        """
        Check if the content type is compressible.

        :param content_type: The Content-Type header value.
        :type content_type: str
        :return: True if compressible, False otherwise.
        :rtype: bool
        """
        return bool(COMPRESSIBLE_CONTENT_TYPE_REGEX.match(content_type))

    async def _get_response_content(self, response: Response) -> Optional[bytes]:
        """
        Retrieve the response content, handling both synchronous and asynchronous content.

        :param response: The response object.
        :type response: Response
        :return: The response content as bytes.
        :rtype: Optional[bytes]
        """
        content = response.content
        if isinstance(content, bytes):
            return content
        elif isinstance(content, str):
            return content.encode(response.charset or "utf-8")
        elif hasattr(content, "__iter__"):
            # Handle iterable content
            return b"".join(content)
        elif hasattr(content, "__aiter__"):
            # Handle asynchronous iterable content
            data = bytearray()
            async for chunk in content:
                data.extend(chunk)
            return bytes(data)
        else:
            return None

    def _compress_content(self, content: bytes, encoding: SupportedEncodings) -> bytes:
        """
        Compress the content using the specified encoding.

        :param content: The original content to compress.
        :type content: bytes
        :param encoding: The compression encoding ('gzip' or 'deflate').
        :type encoding: SupportedEncodings
        :return: The compressed content.
        :rtype: bytes
        """
        if encoding == "gzip":
            return gzip.compress(content)
        elif encoding == "deflate":
            return zlib.compress(content)
        else:
            return content  # This should not happen due to prior checks

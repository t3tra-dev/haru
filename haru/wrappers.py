"""
This module provides wrapper classes for handling file-like objects and files in the Haru web framework.
The `FileWrapper` and `BytesWrapper` classes are used to stream files and byte streams in chunks,
which is useful for sending large files or binary data as part of an HTTP response.

These classes inherit from `Response` and can be used directly as responses in route handlers.
They handle both synchronous and asynchronous contexts, adapting their behavior accordingly.
"""

import asyncio
from typing import IO, Optional, AsyncIterator, Iterator, Union

from .response import Response

__all__ = ['FileWrapper', 'BytesWrapper']


class FileWrapper(Response):
    """
    A wrapper class for reading and streaming file content in chunks.
    This class inherits from `Response` and can be returned directly from route handlers.

    It adapts to both synchronous and asynchronous contexts, handling file I/O appropriately.

    :param filepath: The path to the file to be wrapped.
    :type filepath: str
    :param chunk_size: The size of the chunks to read from the file at a time (default is 8192 bytes).
    :type chunk_size: int
    :param content_type: The MIME type of the file. If not provided, it will be guessed based on the file extension.
    :type content_type: Optional[str]
    :param headers: Additional headers to include in the response.
    :type headers: Optional[dict]
    """

    def __init__(
        self,
        filepath: str,
        chunk_size: int = 8192,
        content_type: Optional[str] = None,
        headers: Optional[dict] = None,
    ):
        super().__init__(content_type=content_type, headers=headers)
        self.filepath: str = filepath
        self.chunk_size: int = chunk_size

    def __iter__(self) -> Iterator[bytes]:
        """
        Iterate over the file content synchronously, yielding chunks of data until the entire file is read.

        :return: A generator yielding chunks of file data.
        :rtype: Iterator[bytes]
        """
        with open(self.filepath, 'rb') as f:
            while True:
                data = f.read(self.chunk_size)
                if not data:
                    break
                yield data

    async def __aiter__(self) -> AsyncIterator[bytes]:
        """
        Asynchronously iterate over the file content, yielding chunks of data by offloading I/O to a thread pool.

        :return: An asynchronous generator yielding chunks of file data.
        :rtype: AsyncIterator[bytes]
        """
        loop = asyncio.get_running_loop()
        with open(self.filepath, 'rb') as f:
            while True:
                data = await loop.run_in_executor(None, f.read, self.chunk_size)
                if not data:
                    break
                yield data

    def get_content(self) -> Union[bytes, Iterator[bytes]]:
        """
        Get the content to be sent in the response. For synchronous contexts, returns an iterator.

        :return: The content of the response.
        :rtype: Union[bytes, Iterator[bytes]]
        """
        return self

    async def get_async_content(self) -> AsyncIterator[bytes]:
        """
        Get the content as an async iterator for asynchronous contexts.

        :return: An asynchronous iterator over the content.
        :rtype: AsyncIterator[bytes]
        """
        return self


class BytesWrapper(Response):
    """
    A wrapper class for reading and streaming binary data from a file-like object in chunks.
    This class inherits from `Response` and can be returned directly from route handlers.

    It adapts to both synchronous and asynchronous contexts, handling I/O appropriately.

    :param fileobj: The file-like object (usually an in-memory byte stream) to be wrapped.
    :type fileobj: IO[bytes]
    :param chunk_size: The size of the chunks to read from the object at a time (default is 8192 bytes).
    :type chunk_size: int
    :param content_type: The MIME type of the content.
    :type content_type: Optional[str]
    :param headers: Additional headers to include in the response.
    :type headers: Optional[dict]
    """

    def __init__(
        self,
        fileobj: IO[bytes],
        chunk_size: int = 8192,
        content_type: Optional[str] = None,
        headers: Optional[dict] = None,
    ):
        super().__init__(content_type=content_type, headers=headers)
        self.fileobj: IO[bytes] = fileobj
        self.chunk_size: int = chunk_size

    def __iter__(self) -> Iterator[bytes]:
        """
        Iterate over the byte stream synchronously, yielding chunks of data until the entire stream is read.

        :return: A generator yielding chunks of byte data.
        :rtype: Iterator[bytes]
        """
        while True:
            data = self.fileobj.read(self.chunk_size)
            if not data:
                break
            yield data

    async def __aiter__(self) -> AsyncIterator[bytes]:
        """
        Asynchronously iterate over the byte stream, yielding chunks of data by offloading I/O to a thread pool.

        :return: An asynchronous generator yielding chunks of byte data.
        :rtype: AsyncIterator[bytes]
        """
        loop = asyncio.get_running_loop()
        while True:
            data = await loop.run_in_executor(None, self.fileobj.read, self.chunk_size)
            if not data:
                break
            yield data

    def get_content(self) -> Union[bytes, Iterator[bytes]]:
        """
        Get the content to be sent in the response. For synchronous contexts, returns an iterator.

        :return: The content of the response.
        :rtype: Union[bytes, Iterator[bytes]]
        """
        return self

    async def get_async_content(self) -> AsyncIterator[bytes]:
        """
        Get the content as an async iterator for asynchronous contexts.

        :return: An asynchronous iterator over the content.
        :rtype: AsyncIterator[bytes]
        """
        return self

"""
This module provides wrapper classes for handling file-like objects in the Haru web framework.
The `FileWrapper` and `BytesWrapper` classes are used to stream files and byte streams in chunks,
which is useful for sending large files or binary data as part of an HTTP response.

Additionally, `AsyncFileWrapper` and `AsyncBytesWrapper` are provided for asynchronous file streaming
in ASGI applications without external dependencies.
"""

import asyncio
from typing import IO, Optional, AsyncIterator, Iterator

__all__ = ['FileWrapper', 'BytesWrapper', 'AsyncFileWrapper', 'AsyncBytesWrapper']


class FileWrapper:
    """
    A wrapper class for reading and streaming file content in chunks. This class is typically
    used to send large files as part of an HTTP response without loading the entire file into memory.

    :param filepath: The path to the file to be wrapped.
    :type filepath: str
    :param chunk_size: The size of the chunks to read from the file at a time (default is 8192 bytes).
    :type chunk_size: int
    """

    def __init__(self, filepath: str, chunk_size: int = 8192):
        self.filepath: str = filepath
        self.chunk_size: int = chunk_size
        self.content_type: Optional[str] = None

    def __iter__(self) -> Iterator[bytes]:
        """
        Iterate over the file content, yielding chunks of data until the entire file is read.

        :return: A generator yielding chunks of file data.
        :rtype: Iterator[bytes]
        """
        with open(self.filepath, 'rb') as f:
            while True:
                data = f.read(self.chunk_size)
                if not data:
                    break
                yield data


class BytesWrapper:
    """
    A wrapper class for reading and streaming binary data from a file-like object in chunks.
    This class is useful for handling in-memory byte streams that need to be sent in chunks
    as part of an HTTP response.

    :param fileobj: The file-like object (usually an in-memory byte stream) to be wrapped.
    :type fileobj: IO[bytes]
    :param chunk_size: The size of the chunks to read from the object at a time (default is 8192 bytes).
    :type chunk_size: int
    """

    def __init__(self, fileobj: IO[bytes], chunk_size: int = 8192):
        self.fileobj: IO[bytes] = fileobj
        self.chunk_size: int = chunk_size
        self.content_type: Optional[str] = None

    def __iter__(self) -> Iterator[bytes]:
        """
        Iterate over the byte stream, yielding chunks of data until the entire stream is read.

        :return: A generator yielding chunks of byte data.
        :rtype: Iterator[bytes]
        """
        while True:
            data = self.fileobj.read(self.chunk_size)
            if not data:
                break
            yield data


class AsyncFileWrapper:
    """
    An asynchronous wrapper class for reading and streaming file content in chunks without external dependencies.
    This class is used in ASGI applications to send large files without blocking the event loop by offloading
    file I/O operations to a thread pool executor.

    :param filepath: The path to the file to be wrapped.
    :type filepath: str
    :param chunk_size: The size of the chunks to read from the file at a time (default is 8192 bytes).
    :type chunk_size: int
    """

    def __init__(self, filepath: str, chunk_size: int = 8192):
        self.filepath: str = filepath
        self.chunk_size: int = chunk_size
        self.content_type: Optional[str] = None

    async def __aiter__(self) -> AsyncIterator[bytes]:
        """
        Asynchronously iterate over the file content, yielding chunks of data by offloading I/O to a thread pool.

        :return: An asynchronous generator yielding chunks of file data.
        :rtype: AsyncIterator[bytes]
        """
        loop = asyncio.get_running_loop()
        with open(self.filepath, 'rb') as f:
            while True:
                # Read file data in executor to avoid blocking the event loop
                data = await loop.run_in_executor(None, f.read, self.chunk_size)
                if not data:
                    break
                yield data


class AsyncBytesWrapper:
    """
    An asynchronous wrapper class for reading and streaming binary data from a file-like object without external dependencies.
    Useful in ASGI applications for streaming in-memory byte streams without blocking the event loop.

    :param fileobj: The file-like object to be wrapped.
    :type fileobj: IO[bytes]
    :param chunk_size: The size of the chunks to read from the object at a time (default is 8192 bytes).
    :type chunk_size: int
    """

    def __init__(self, fileobj: IO[bytes], chunk_size: int = 8192):
        self.fileobj: IO[bytes] = fileobj
        self.chunk_size: int = chunk_size
        self.content_type: Optional[str] = None

    async def __aiter__(self) -> AsyncIterator[bytes]:
        """
        Asynchronously iterate over the byte stream, yielding chunks of data by offloading I/O to a thread pool.

        :return: An asynchronous generator yielding chunks of byte data.
        :rtype: AsyncIterator[bytes]
        """
        loop = asyncio.get_running_loop()
        while True:
            # Read data in executor to avoid blocking the event loop
            data = await loop.run_in_executor(None, self.fileobj.read, self.chunk_size)
            if not data:
                break
            yield data

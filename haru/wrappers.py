"""
This module provides wrapper classes for handling file-like objects in the Haru web framework.
The `FileWrapper` and `BytesWrapper` classes are used to stream files and byte streams in chunks,
which is useful for sending large files or binary data as part of an HTTP response.
"""

from typing import IO, Optional

__all__ = ['FileWrapper', 'BytesWrapper']


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

    def __iter__(self):
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

    def __iter__(self):
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

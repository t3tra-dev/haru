from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
from typing import Optional, Union

__all__ = [
    "BytesLike",
    "GUID",
    "generate_key",
    "compute_accept_key",
    "apply_mask",
    "Deadline",
    "compare_digest",
]

# Type alias for bytes-like objects
BytesLike = Union[bytes, bytearray, memoryview]

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def generate_key() -> str:
    """
    Generate a random key for the Sec-WebSocket-Key header.

    :return: A base64-encoded 16-byte random key
    :rtype: str
    """
    return base64.b64encode(secrets.token_bytes(16)).decode()


def compute_accept_key(key: str) -> str:
    """
    Compute the value for the Sec-WebSocket-Accept header.

    :param key: Value of the Sec-WebSocket-Key header
    :type key: str
    :return: The computed accept key
    :rtype: str
    :raises ValueError: If the key is invalid
    """
    if not key:
        raise ValueError("Key cannot be empty")

    try:
        # Verify the key is valid base64
        decoded = base64.b64decode(key.encode(), validate=True)
        if len(decoded) != 16:
            raise ValueError("Invalid key length")
    except Exception as e:
        raise ValueError(f"Invalid key format: {e}")

    accept = hashlib.sha1((key + GUID).encode()).digest()
    return base64.b64encode(accept).decode()


def apply_mask(data: BytesLike, mask: bytes) -> bytes:
    """
    Apply XOR mask to data according to the WebSocket protocol.

    :param data: Data to mask
    :type data: BytesLike
    :param mask: 4-byte mask key
    :type mask: bytes
    :return: Masked data
    :rtype: bytes
    :raises ValueError: If mask is not exactly 4 bytes
    """
    if len(mask) != 4:
        raise ValueError("Mask must be exactly 4 bytes")

    data = bytes(data)  # Convert any bytes-like object to bytes
    data_len = len(data)

    # Optimize for small messages
    if data_len < 128:
        return bytes(b ^ mask[i % 4] for i, b in enumerate(data))

    # For larger messages, use the struct module for better performance
    mask_int = struct.unpack("!I", mask)[0]
    chunks = [data[i: i + 4] for i in range(0, data_len - data_len % 4, 4)]
    result = bytearray()

    for chunk in chunks:
        chunk_int = struct.unpack("!I", chunk)[0]
        result.extend(struct.pack("!I", chunk_int ^ mask_int))

    # Handle remaining bytes
    for i in range(data_len - data_len % 4, data_len):
        result.append(data[i] ^ mask[i % 4])

    return bytes(result)


class Deadline:
    """
    Manage timeouts across multiple steps of an operation.

    :param timeout: Time available in seconds or None if no timeout
    :type timeout: Optional[float]
    """

    def __init__(self, timeout: Optional[float]) -> None:
        self.deadline = time.monotonic() + timeout if timeout is not None else None
        self._start_time = time.monotonic()

    def remaining(self) -> Optional[float]:
        """
        Get remaining time before deadline.

        :return: Remaining time in seconds or None if no deadline set.
                Returns 0 if deadline has passed
        :rtype: Optional[float]
        """
        if self.deadline is None:
            return None
        remaining = self.deadline - time.monotonic()
        return max(0.0, remaining)

    def has_expired(self) -> bool:
        """
        Check if deadline has passed.

        :return: True if deadline has passed, False otherwise
        :rtype: bool
        """
        return self.remaining() == 0 if self.deadline is not None else False

    def elapsed(self) -> float:
        """
        Get elapsed time since creation.

        :return: Time elapsed since object creation in seconds
        :rtype: float
        """
        return time.monotonic() - self._start_time


def compare_digest(a: Union[str, bytes], b: Union[str, bytes]) -> bool:
    """
    Constant-time comparison of strings or bytes.

    :param a: First value to compare
    :type a: Union[str, bytes]
    :param b: Second value to compare
    :type b: Union[str, bytes]
    :return: True if values are equal, False otherwise
    :rtype: bool
    :raises TypeError: If arguments are not both strings or both bytes
    """
    if isinstance(a, str) and isinstance(b, str):
        return hmac.compare_digest(a.encode(), b.encode())
    elif isinstance(a, bytes) and isinstance(b, bytes):
        return hmac.compare_digest(a, b)
    else:
        raise TypeError("Arguments must be both strings or both bytes")

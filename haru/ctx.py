"""
This module provides a context variable for managing request-specific data in the Haru web framework.
Context variables allow you to store and access data that is unique to a particular request
within the scope of asynchronous or concurrent execution.

The `request_context` variable is used to store and retrieve data specific to the current request context.
"""

import contextvars
from typing import Any

__all__ = ['request_context']

request_context: contextvars.ContextVar[Any] = contextvars.ContextVar('request_context', default=None)

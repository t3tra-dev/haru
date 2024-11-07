"""
This module defines models and mixins for the OAuth 2.0 implementation.
"""

from typing import Protocol

__all__ = ["UserMixin"]


class UserMixin(Protocol):
    """
    Provides default implementations for methods that a user class should have.
    """

    def get_id(self) -> str:
        """
        Return the unique identifier of the user as a string.
        """
        raise NotImplementedError(
            "Method 'get_id' must be implemented to return a unique identifier for the user"
        )

    @property
    def is_authenticated(self) -> bool:
        """
        Return True if the user is authenticated.
        """
        return True

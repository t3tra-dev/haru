"""
This module defines the base model class for the ORM.
"""

from .base import Base


class Model(Base):
    """
    Base class for all ORM models. Inherit from this class to define your models.
    """

    __abstract__ = True

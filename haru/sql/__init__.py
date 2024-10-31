"""
The haru.sql module provides ORM support using SQLAlchemy.
It allows you to define models and interact with various databases in a convenient way.
"""

try:
    import sqlalchemy  # noqa: F401
except ImportError as e:
    raise ImportError(
        "SQLAlchemy is required to use haru.sql. Install it with 'pip install haru[sql]'."
    ) from e

from .base import Base, engine_dict, get_engine
from .session import get_session, SessionManager
from .models import Model
from .types import (
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Date,
    Time,
    Text,
    LargeBinary,
    JSON,
)
from .column import Column

__all__ = [
    "Base",
    "Model",
    "engine_dict",
    "get_engine",
    "get_session",
    "SessionManager",
    "Column",
    "Integer",
    "String",
    "Float",
    "Boolean",
    "DateTime",
    "Date",
    "Time",
    "Text",
    "LargeBinary",
    "JSON",
]

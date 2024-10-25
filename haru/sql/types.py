"""
This module defines type classes that extend SQLAlchemy's types with robust type hints.
"""

from sqlalchemy import types as sql_types
from typing import Any, Optional

__all__ = [
    'Integer',
    'String',
    'Float',
    'Boolean',
    'DateTime',
    'Date',
    'Time',
    'Text',
    'LargeBinary',
    'JSON',
]


class Integer(sql_types.Integer):
    """
    Integer data type.
    """

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)


class String(sql_types.String):
    """
    String data type.

    :param length: Maximum string length.
    :type length: Optional[int]
    """

    def __init__(self, length: Optional[int] = None, **kwargs: Any):
        super().__init__(length=length, **kwargs)


class Float(sql_types.Float):
    """
    Float data type.
    """

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)


class Boolean(sql_types.Boolean):
    """
    Boolean data type.
    """

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)


class DateTime(sql_types.DateTime):
    """
    DateTime data type.
    """

    def __init__(self, timezone: bool = False, **kwargs: Any):
        super().__init__(timezone=timezone, **kwargs)


class Date(sql_types.Date):
    """
    Date data type.
    """

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)


class Time(sql_types.Time):
    """
    Time data type.
    """

    def __init__(self, timezone: bool = False, **kwargs: Any):
        super().__init__(timezone=timezone, **kwargs)


class Text(sql_types.Text):
    """
    Text data type.

    :param length: Maximum text length.
    :type length: Optional[int]
    """

    def __init__(self, length: Optional[int] = None, **kwargs: Any):
        super().__init__(length=length, **kwargs)


class LargeBinary(sql_types.LargeBinary):
    """
    LargeBinary data type.

    :param length: Maximum length.
    :type length: Optional[int]
    """

    def __init__(self, length: Optional[int] = None, **kwargs: Any):
        super().__init__(length=length, **kwargs)


class JSON(sql_types.JSON):
    """
    JSON data type.
    """

    def __init__(self, none_as_null: bool = False, astext_type: Optional[Any] = None, **kwargs: Any):
        super().__init__(none_as_null=none_as_null, astext_type=astext_type, **kwargs)

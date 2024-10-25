"""
This module defines a Column class that extends SQLAlchemy's Column with robust type hints.
"""

from sqlalchemy import Column as SAColumn
from typing import Any, Optional, Union

__all__ = ['Column']


class Column(SAColumn):
    """
    Represents a column in a database table.

    :param type_: The column's data type.
    :type type_: Any
    :param name: The name of the column.
    :type name: Optional[str]
    :param primary_key: Whether this column is a primary key.
    :type primary_key: bool
    :param nullable: Whether the column can contain NULL values.
    :type nullable: bool
    :param default: The default value of the column.
    :type default: Any
    :param autoincrement: Whether the column should auto-increment.
    :type autoincrement: Union[bool, str, None]
    :param unique: Whether the column should have a UNIQUE constraint.
    :type unique: bool
    :param index: Whether the column should be indexed.
    :type index: bool
    :param kwargs: Additional keyword arguments.
    """

    def __init__(
        self,
        type_: Any,
        name: Optional[str] = None,
        *args: Any,
        primary_key: bool = False,
        nullable: Optional[bool] = None,
        default: Any = None,
        autoincrement: Union[bool, str, None] = None,
        unique: bool = False,
        index: bool = False,
        **kwargs: Any
    ):
        super().__init__(
            name,
            type_,
            *args,
            primary_key=primary_key,
            nullable=nullable,
            default=default,
            autoincrement=autoincrement,
            unique=unique,
            index=index,
            **kwargs
        )

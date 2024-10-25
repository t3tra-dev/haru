"""
This module defines the base classes and engine management for the ORM.
"""

from typing import Dict, Optional
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine import Engine, create_engine

Base = declarative_base()

engine_dict: Dict[str, Engine] = {}


def get_engine(db_url: str, alias: Optional[str] = 'default', **kwargs) -> Engine:
    """
    Create or retrieve an SQLAlchemy engine.

    :param db_url: The database URL.
    :type db_url: str
    :param alias: An optional alias for the engine.
    :type alias: Optional[str]
    :param kwargs: Additional keyword arguments for create_engine.
    :return: The SQLAlchemy engine.
    :rtype: Engine
    """
    if alias in engine_dict:
        return engine_dict[alias]
    engine = create_engine(db_url, **kwargs)
    engine_dict[alias] = engine
    return engine

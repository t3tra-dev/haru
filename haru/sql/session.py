"""
This module provides session management for database interactions.
"""

from typing import Optional, Dict
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine

session_factory_dict: Dict[str, sessionmaker] = {}


def get_session(engine: Engine, alias: Optional[str] = "default") -> Session:
    """
    Create or retrieve a session for the given engine.

    :param engine: The SQLAlchemy engine.
    :type engine: Engine
    :param alias: An optional alias for the session factory.
    :type alias: Optional[str]
    :return: The SQLAlchemy session.
    :rtype: Session
    """
    if alias in session_factory_dict:
        session_factory = session_factory_dict[alias]
    else:
        session_factory = sessionmaker(bind=engine)
        session_factory_dict[alias] = session_factory
    return session_factory()


class SessionManager:
    """
    A context manager for SQLAlchemy sessions.

    :param session: The SQLAlchemy session to manage.
    :type session: Session
    """

    def __init__(self, session: Session):
        self.session = session

    def __enter__(self) -> Session:
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()

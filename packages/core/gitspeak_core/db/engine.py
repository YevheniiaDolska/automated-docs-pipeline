"""Database engine and session factory.

Supports both PostgreSQL (production) and SQLite (development/testing).
"""

from __future__ import annotations

import logging

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from gitspeak_core.config.settings import AppSettings, get_default_settings

logger = logging.getLogger(__name__)

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine(settings: AppSettings | None = None) -> Engine:
    """Return the global SQLAlchemy engine (lazy-created)."""
    global _engine
    if _engine is None:
        settings = settings or get_default_settings()
        connect_args = {}
        if settings.database_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        _engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
    return _engine


def get_session_factory(settings: AppSettings | None = None) -> sessionmaker[Session]:
    """Return the global session factory (lazy-created)."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(settings),
            autocommit=False,
            autoflush=False,
        )
    return _session_factory


def get_session(settings: AppSettings | None = None) -> Session:
    """Create a new database session."""
    factory = get_session_factory(settings)
    return factory()


def reset_engine() -> None:
    """Reset engine and session factory (for testing)."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None

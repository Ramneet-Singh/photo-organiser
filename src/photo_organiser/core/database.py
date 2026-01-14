"""Database initialization and connection management (single source of truth)."""

from __future__ import annotations

import logging
from collections.abc import Generator
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from ..config.settings import settings
from ..models.database import Base

logger = logging.getLogger(__name__)

engine: Engine = create_engine(
    settings.database.url,
    echo=settings.database.echo,
    connect_args={"check_same_thread": False}
    if "sqlite" in settings.database.url
    else {},
)

SessionLocal: sessionmaker[Session] = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def create_database() -> None:
    """Create all database tables."""
    try:
        if settings.database.url.startswith("sqlite:///"):
            db_path = Path(settings.database.url.removeprefix("sqlite:///"))
            db_path.parent.mkdir(parents=True, exist_ok=True)

        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as exc:
        logger.error("Failed to create database: %s", exc)
        raise


def drop_database() -> None:
    """Drop all database tables (use with caution!)."""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
    except Exception as exc:
        logger.error("Failed to drop database: %s", exc)
        raise


def get_session() -> Session:
    """Get a database session."""
    return SessionLocal()


def close_session(session: Session) -> None:
    """Close a database session."""
    try:
        session.close()
    except Exception as exc:
        logger.error("Error closing session: %s", exc)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection: Any, _connection_record: Any) -> None:
    """Enable SQLite foreign key constraints."""
    if "sqlite" in settings.database.url:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


class DatabaseManager:
    """Database manager class for handling connections and transactions."""

    def __init__(self) -> None:
        self.engine = engine
        self.SessionLocal = SessionLocal

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    def close_session(self, session: Session) -> None:
        """Close a database session."""
        close_session(session)

    def check_connection(self) -> bool:
        """Check if database connection is working."""
        try:
            from sqlalchemy import text

            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as exc:
            logger.error("Database connection check failed: %s", exc)
            return False


db_manager = DatabaseManager()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for getting database session."""
    session = get_session()
    try:
        yield session
    finally:
        session.close()

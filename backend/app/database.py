"""
ResQ-AI Database Engine & Session Configuration.
Supports dual-engine (SQLite development/test, PostgreSQL production target),
portable GUID TypeDecorator, and foreign key pragma enforcement for SQLite.
"""

import os
import uuid
import sqlite3
from typing import Any, Optional, Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base, sessionmaker, DeclarativeBase, Session
from sqlalchemy.pool import StaticPool, QueuePool

from app.config import get_settings


class GUID(TypeDecorator):
    """
    Platform-independent GUID/UUID type.
    Uses PostgreSQL's native UUID type, otherwise uses CHAR(36),
    storing as standard hyphenated hex string values.
    """
    impl = CHAR(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value: Any, dialect) -> Optional[Any]:
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            if dialect.name == "postgresql":
                return value
            return str(value)
        else:
            try:
                parsed = uuid.UUID(str(value))
            except (ValueError, AttributeError, TypeError):
                raise ValueError(f"Invalid UUID value: {value}")
            if dialect.name == "postgresql":
                return parsed
            return str(parsed)

    def process_result_value(self, value: Any, dialect) -> Optional[uuid.UUID]:
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        try:
            return uuid.UUID(str(value))
        except (ValueError, AttributeError, TypeError):
            return None


# Determine active database URL
settings = get_settings()
DATABASE_URL = settings.DATABASE_URL

# Normalize URL for SQLAlchemy dialect loader
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

is_sqlite = DATABASE_URL.startswith("sqlite")
is_memory = DATABASE_URL in ("sqlite://", "sqlite:///:memory:")

connect_args = {}
engine_kwargs = {}

if is_sqlite:
    connect_args["check_same_thread"] = False
    if is_memory:
        engine_kwargs["poolclass"] = StaticPool
else:
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,
        "poolclass": QueuePool,
    })

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    **engine_kwargs
)

# Enforce foreign key constraints in SQLite
if is_sqlite:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if isinstance(dbapi_connection, sqlite3.Connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()


class Base(DeclarativeBase):
    """Declarative base class for all SQLAlchemy 2.0 models."""
    pass


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding an isolated database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Idempotently create all registered tables."""
    # Importing models registers them with Base.metadata
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)

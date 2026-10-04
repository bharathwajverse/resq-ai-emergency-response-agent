"""
Unit Tests for ResQ-AI Database Engine & GUID TypeDecorator.
Tests portable UUID handling, SQLite PRAGMA enforcement, and session lifecycle.
"""

import uuid
import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool

from app.database import Base, GUID, get_db, SessionLocal, engine
from app.models.hospital import Hospital


def test_guid_type_decorator_coercion():
    """Verify GUID TypeDecorator handles uuid.UUID and string conversions."""
    guid_type = GUID()
    test_uuid = uuid.uuid4()
    uuid_str = str(test_uuid)

    # Binding valid UUID object
    bound_from_obj = guid_type.process_bind_param(test_uuid, engine.dialect)
    assert bound_from_obj is not None

    # Binding valid UUID string
    bound_from_str = guid_type.process_bind_param(uuid_str, engine.dialect)
    assert bound_from_str is not None

    # Processing result value
    result = guid_type.process_result_value(uuid_str, engine.dialect)
    assert isinstance(result, uuid.UUID)
    assert result == test_uuid

    # None handling
    assert guid_type.process_bind_param(None, engine.dialect) is None
    assert guid_type.process_result_value(None, engine.dialect) is None


def test_guid_type_decorator_invalid_input():
    """Verify GUID TypeDecorator raises ValueError for invalid UUID strings."""
    guid_type = GUID()
    with pytest.raises(ValueError, match="Invalid UUID value"):
        guid_type.process_bind_param("invalid-uuid-string", engine.dialect)


def test_database_session_generator():
    """Verify get_db generator yields an active session and closes cleanly."""
    gen = get_db()
    db = next(gen)
    assert db.is_active
    with pytest.raises(StopIteration):
        next(gen)


def test_sqlite_foreign_key_pragma(test_engine):
    """Verify SQLite connection pragma enforces foreign keys."""
    with test_engine.connect() as conn:
        res = conn.execute(text("PRAGMA foreign_keys")).scalar()
        assert res == 1

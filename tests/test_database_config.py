"""
Unit tests for Phase 13: PostgreSQL & Database Engine Compatibility.
"""

from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.database.database import _create_engine
from app.config import get_settings
from app.models.transaction import Transaction


def test_database_models_have_indexes():
    table_args = Transaction.__table_args__
    index_names = [idx.name for idx in table_args if hasattr(idx, "name")]

    assert "ix_txn_sender_timestamp" in index_names
    assert "ix_txn_receiver_timestamp" in index_names
    assert "ix_txn_risk_level" in index_names
    assert "ix_txn_suspicious" in index_names


def test_create_engine_sqlite_and_postgres_url_handling(monkeypatch):
    settings = get_settings()

    # Test SQLite engine configuration
    monkeypatch.setattr(settings, "database_url", "sqlite+aiosqlite:///./test_dummy.db")
    engine_sqlite = _create_engine()
    assert "sqlite" in str(engine_sqlite.url)

    # Test PostgreSQL / asyncpg configuration
    pg_url = "postgresql+asyncpg://user:pass@localhost:5432/testdb"
    monkeypatch.setattr(settings, "database_url", pg_url)
    engine_pg = _create_engine()
    assert "postgresql" in str(engine_pg.url)
    assert engine_pg.pool._pre_ping is True

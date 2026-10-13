"""
tests/conftest.py — Pytest fixtures providing isolated temporary SQLite databases and test Flask clients.
"""
import sqlite3
import pytest
from app import app
from database.db import SCHEMA_SQL


@pytest.fixture
def temp_db():
    """In-memory SQLite database connection with full schema."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def client(temp_db):
    """Configured test client with CSRF disabled for test convenience."""
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client

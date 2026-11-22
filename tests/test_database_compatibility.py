import pytest
import sqlite3
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine, text, Column, Integer, String, Table, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.database import sync_postgres_sequences, Base
from backend.main import safe_migrate_db, init_db


def test_sqlite_initialization_and_data_preservation(tmp_path):
    """Verifies SQLite initializes cleanly and safe_migrate_db preserves existing data."""
    db_file = tmp_path / "test_preservation.db"
    db_url = f"sqlite:///{db_file}"
    test_engine = create_engine(db_url, connect_args={"check_same_thread": False})
    
    # 1. First migration creates schema
    safe_migrate_db(target_engine=test_engine)

    # 2. Insert test user and profile
    with test_engine.connect() as conn:
        conn.execute(text("INSERT INTO users (email, username, full_name, hashed_password) VALUES ('preserve@test.com', 'preserve_user', 'Preserve User', 'hash123');"))
        user_id = conn.execute(text("SELECT id FROM users WHERE username = 'preserve_user'")).scalar()
        conn.execute(text(f"INSERT INTO user_profiles (user_id, is_onboarded, current_weight_kg) VALUES ({user_id}, 1, 75.0);"))
        conn.commit()

    # 3. Second migration must preserve existing records untouched
    safe_migrate_db(target_engine=test_engine)

    with test_engine.connect() as conn:
        saved_weight = conn.execute(text("SELECT current_weight_kg FROM user_profiles WHERE user_id = :uid"), {"uid": user_id}).scalar()
        assert saved_weight == 75.0
        saved_user = conn.execute(text("SELECT username FROM users WHERE id = :uid"), {"uid": user_id}).scalar()
        assert saved_user == "preserve_user"


def test_existing_user_profiles_column_migrations(tmp_path):
    """Simulates an older database lacking recent profile columns and verifies dynamic addition."""
    db_file = tmp_path / "test_legacy.db"
    db_url = f"sqlite:///{db_file}"
    test_engine = create_engine(db_url, connect_args={"check_same_thread": False})

    # Create a legacy user_profiles table lacking is_onboarded and new split columns
    with test_engine.connect() as conn:
        conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, email VARCHAR, username VARCHAR, full_name VARCHAR, hashed_password VARCHAR);"))
        conn.execute(text("CREATE TABLE user_profiles (id INTEGER PRIMARY KEY, user_id INTEGER, age INTEGER, current_weight_kg FLOAT);"))
        conn.execute(text("INSERT INTO users (id, email, username, full_name, hashed_password) VALUES (1, 'legacy@test.com', 'legacy_user', 'Legacy User', 'pass');"))
        conn.execute(text("INSERT INTO user_profiles (id, user_id, age, current_weight_kg) VALUES (1, 1, 30, 80.0);"))
        conn.commit()

    # Run dialect-independent migration
    safe_migrate_db(target_engine=test_engine)

    # Verify missing columns were added dynamically and existing accounts preserved
    with test_engine.connect() as conn:
        cur = conn.connection.cursor()
        cur.execute("PRAGMA table_info(user_profiles);")
        columns = [row[1] for row in cur.fetchall()]
        assert "is_onboarded" in columns
        assert "workout_frequency_days" in columns
        assert "preferred_split" in columns
        assert "custom_split_details" in columns

        # Verify existing account was flagged as onboarded
        is_onboarded = conn.execute(text("SELECT is_onboarded FROM user_profiles WHERE id = 1")).scalar()
        assert is_onboarded == 1


def test_migration_failure_handling():
    """Verifies that migration errors raise RuntimeError rather than failing silently."""
    mock_engine = MagicMock()
    mock_engine.dialect.name = "postgresql"

    # Simulate an error during Base.metadata.create_all
    with patch("backend.main.Base.metadata.create_all", side_effect=Exception("Connection refused")):
        with pytest.raises(RuntimeError) as exc_info:
            safe_migrate_db(target_engine=mock_engine)
        assert "Database migration failed on postgresql" in str(exc_info.value)


def test_sync_postgres_sequences_safe_on_sqlite():
    """Verifies that sync_postgres_sequences safely no-ops on SQLite without executing PG queries."""
    sqlite_engine = create_engine("sqlite:///:memory:")
    result = sync_postgres_sequences(target_engine=sqlite_engine)
    assert result == {}


def test_sync_postgres_sequences_postgresql_success():
    """Verifies that sync_postgres_sequences discovers sequences and runs setval on PostgreSQL."""
    mock_engine = MagicMock()
    mock_engine.dialect.name = "postgresql"
    mock_conn = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_conn

    # Simulate sequence name queries returning a valid sequence name, and setval returning an integer ID
    call_count = {"n": 0}
    def mock_scalar():
        call_count["n"] += 1
        if call_count["n"] % 2 == 1:
            return "public_entity_id_seq"
        return 25

    mock_conn.execute.return_value.scalar.side_effect = mock_scalar

    result = sync_postgres_sequences(target_engine=mock_engine)
    assert len(result) >= 1
    assert all(val == 25 for val in result.values())
    assert mock_conn.commit.called


def test_sync_postgres_sequences_failure_handling():
    """Verifies that sequence synchronization failures are not swallowed and raise clear exceptions."""
    mock_engine = MagicMock()
    mock_engine.dialect.name = "postgresql"
    mock_conn = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_conn

    mock_conn.execute.side_effect = Exception("Permission denied for sequence")

    with pytest.raises(RuntimeError) as exc_info:
        sync_postgres_sequences(target_engine=mock_engine)
    assert "PostgreSQL sequence synchronization failed" in str(exc_info.value)

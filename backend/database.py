import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger("desifit.database")

# Load .env before resolving DATABASE_URL; this module is imported before main.py
# finishes importing the application routers.
load_dotenv()
raw_db_url = os.getenv("DATABASE_URL", "").strip()

# 1. Fallback to local SQLite if DATABASE_URL is unset or empty
if not raw_db_url:
    DATABASE_URL = "sqlite:///./desifit.db"
else:
    # 2. Normalize PostgreSQL dialect scheme for SQLAlchemy compatibility
    if raw_db_url.startswith("postgres://"):
        DATABASE_URL = raw_db_url.replace("postgres://", "postgresql://", 1)
    else:
        DATABASE_URL = raw_db_url

# 3. Configure engine based on database dialect
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
else:
    # Neon / PostgreSQL production settings
    # pool_pre_ping=True: validates connections before use (handles serverless idle timeouts)
    # pool_recycle=300: recycles connections periodically to avoid stale connections
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=10,
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def sync_postgres_sequences(target_engine=None) -> dict:
    """
    Synchronizes all PostgreSQL sequences to the MAX(id) for each table.
    Crucial after importing records with explicit IDs from SQLite.
    Must be called after any SQLite-to-PostgreSQL data import or migration.
    Safe no-op when running on SQLite.
    Returns a dictionary of {table_name: synchronized_sequence_value}.
    """
    eng = target_engine or engine
    if eng.dialect.name != "postgresql":
        logger.debug("Sequence synchronization skipped: dialect is '%s', not PostgreSQL.", eng.dialect.name)
        return {}

    synced = {}
    with eng.connect() as conn:
        for table_name, table in Base.metadata.tables.items():
            pk_cols = [c for c in table.primary_key.columns if "INT" in str(c.type).upper()]
            if len(pk_cols) == 1:
                pk_col = pk_cols[0].name
                try:
                    # Verify if a sequence is attached to this column in PostgreSQL
                    seq_name = conn.execute(
                        text(f"SELECT pg_get_serial_sequence('{table_name}', '{pk_col}')")
                    ).scalar()

                    if not seq_name:
                        logger.debug("Table '%s' column '%s' has no associated PostgreSQL sequence.", table_name, pk_col)
                        continue

                    # Safely advance the sequence to MAX(id) or 1 if empty
                    sync_query = text(f"""
                        SELECT setval(
                            pg_get_serial_sequence('{table_name}', '{pk_col}'),
                            COALESCE((SELECT MAX({pk_col}) FROM {table_name}), 1)
                        );
                    """)
                    new_val = conn.execute(sync_query).scalar()
                    conn.commit()
                    synced[table_name] = new_val
                    logger.info("Synchronized PostgreSQL sequence '%s' for table '%s' to %s", seq_name, table_name, new_val)
                except Exception as e:
                    logger.error("Failed to synchronize sequence for table '%s' on column '%s': %s", table_name, pk_col, e)
                    raise RuntimeError(f"PostgreSQL sequence synchronization failed on {table_name}.{pk_col}: {e}") from e
    return synced


if __name__ == "__main__":
    import sys
    if "--sync-sequences" in sys.argv:
        print("[INFO] Running manual PostgreSQL sequence synchronization...")
        result = sync_postgres_sequences()
        print(f"[SUCCESS] Synchronized sequences: {result}")

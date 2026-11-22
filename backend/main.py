import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy import inspect, text

logger = logging.getLogger("desifit.migrations")

import backend.models
from backend.database import engine, Base, SessionLocal, sync_postgres_sequences
from backend.services.seed_data import seed_database_if_empty
from backend.routers import (
    auth,
    profile,
    dashboard,
    workouts,
    exercises,
    nutrition,
    progress,
    ai
)

load_dotenv()


def safe_migrate_db(target_engine=None):
    """
    Ensures safe schema migrations across both SQLite and PostgreSQL without dropping data.
    Inspects existing columns dynamically and adds missing columns with dialect-appropriate defaults.
    Raises RuntimeError on failure to prevent the application from starting with an incomplete schema.
    """
    eng = target_engine or engine
    try:
        Base.metadata.create_all(bind=eng)
        inspector = inspect(eng)
        if "user_profiles" in inspector.get_table_names():
            existing_cols = {col["name"] for col in inspector.get_columns("user_profiles")}
            is_sqlite = eng.dialect.name == "sqlite"

            with eng.connect() as conn:
                if "is_onboarded" not in existing_cols:
                    if is_sqlite:
                        conn.execute(text("ALTER TABLE user_profiles ADD COLUMN is_onboarded BOOLEAN DEFAULT 0;"))
                        conn.execute(text("UPDATE user_profiles SET is_onboarded = 1;"))
                    else:
                        conn.execute(text("ALTER TABLE user_profiles ADD COLUMN is_onboarded BOOLEAN DEFAULT FALSE;"))
                        conn.execute(text("UPDATE user_profiles SET is_onboarded = TRUE;"))
                    conn.commit()
                    logger.info("Added missing column 'is_onboarded' to user_profiles on %s", eng.dialect.name)

                if "workout_frequency_days" not in existing_cols:
                    conn.execute(text("ALTER TABLE user_profiles ADD COLUMN workout_frequency_days INTEGER;"))
                    conn.commit()
                    logger.info("Added missing column 'workout_frequency_days' to user_profiles on %s", eng.dialect.name)

                if "preferred_split" not in existing_cols:
                    conn.execute(text("ALTER TABLE user_profiles ADD COLUMN preferred_split VARCHAR(150);"))
                    conn.commit()
                    logger.info("Added missing column 'preferred_split' to user_profiles on %s", eng.dialect.name)

                if "custom_split_details" not in existing_cols:
                    conn.execute(text("ALTER TABLE user_profiles ADD COLUMN custom_split_details TEXT;"))
                    conn.commit()
                    logger.info("Added missing column 'custom_split_details' to user_profiles on %s", eng.dialect.name)
    except Exception as e:
        logger.error("Database migration error on %s: %s", eng.dialect.name, e, exc_info=True)
        raise RuntimeError(f"Database migration failed on {eng.dialect.name}: {e}") from e


def init_db(target_engine=None):
    eng = target_engine or engine
    safe_migrate_db(eng)
    if eng.dialect.name == "postgresql":
        sync_postgres_sequences(eng)
    db = SessionLocal()
    try:
        seed_database_if_empty(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="DesiFit API",
    description="Backend REST API for DesiFit – AI Fitness Companion. Serving workouts, nutrition, analytics, and intelligent fitness coaching.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    # Streamlit's Python API client calls FastAPI server-to-server. Keep browser
    # origins restricted to the local frontend instead of allowing every site.
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(profile.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(workouts.router, prefix="/api/v1")
app.include_router(exercises.router, prefix="/api/v1")
app.include_router(nutrition.router, prefix="/api/v1")
app.include_router(progress.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")


@app.get("/", tags=["Health"])
@app.get("/health", tags=["Health"])
def root():
    return {
        "app": "DesiFit API",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs"
    }

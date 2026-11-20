import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

import backend.models
from backend.database import engine, Base, SessionLocal
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


def safe_migrate_db():
    """Ensures safe schema migrations without dropping any existing user data."""
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        try:
            # Check if is_onboarded column exists in user_profiles
            cur = conn.connection.cursor()
            cur.execute("PRAGMA table_info(user_profiles);")
            cols = [r[1] for r in cur.fetchall()]
            if "is_onboarded" not in cols:
                cur.execute("ALTER TABLE user_profiles ADD COLUMN is_onboarded BOOLEAN DEFAULT 0;")
                # Preserve existing accounts by marking them as already onboarded
                cur.execute("UPDATE user_profiles SET is_onboarded = 1;")
                conn.connection.commit()
            if "workout_frequency_days" not in cols:
                cur.execute("ALTER TABLE user_profiles ADD COLUMN workout_frequency_days INTEGER;")
                conn.connection.commit()
            if "preferred_split" not in cols:
                cur.execute("ALTER TABLE user_profiles ADD COLUMN preferred_split VARCHAR(150);")
                conn.connection.commit()
            if "custom_split_details" not in cols:
                cur.execute("ALTER TABLE user_profiles ADD COLUMN custom_split_details TEXT;")
                conn.connection.commit()
        except Exception as e:
            print(f"[DB MIGRATION NOTICE] {e}")


def init_db():
    safe_migrate_db()
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

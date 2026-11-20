import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app
from backend.models import (
    User,
    UserProfile,
    NutritionLog,
    WorkoutLog,
    WorkoutLogExercise,
    WorkoutPlan,
    WorkoutPlanExercise,
    BodyMeasurement,
    AIConversation,
    Exercise,
    FoodItem,
    PasswordResetToken
)
from backend.services.seed_data import seed_database_if_empty
from backend.security.rate_limiter import reset_rate_limiters

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def cleanup_tables():
    db = TestingSessionLocal()
    try:
        db.query(WorkoutLogExercise).delete()
        db.query(WorkoutLog).delete()
        db.query(WorkoutPlanExercise).delete()
        db.query(WorkoutPlan).delete()
        db.query(NutritionLog).delete()
        db.query(BodyMeasurement).delete()
        db.query(AIConversation).delete()
        db.query(UserProfile).delete()
        db.query(PasswordResetToken).delete()
        db.query(Exercise).filter(Exercise.is_custom == True).delete()
        db.query(FoodItem).filter(FoodItem.is_custom == True).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_database_if_empty(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def isolate_database_per_test():
    """Ensures each test has an isolated database state by cleaning up before and after execution."""
    reset_rate_limiters()
    cleanup_tables()
    yield
    cleanup_tables()
    reset_rate_limiters()


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    # Register and login a test user
    reg_data = {
        "email": "testfit@example.com",
        "username": "fitwarrior",
        "full_name": "Arjun Sharma",
        "password": "StrongPassword123"
    }
    client.post("/api/v1/auth/register", json=reg_data)
    
    login_data = {
        "username": "fitwarrior",
        "password": "StrongPassword123"
    }
    res = client.post("/api/v1/auth/login", json=login_data)
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

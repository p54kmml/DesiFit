import os
import re
from unittest.mock import patch

# Explicitly isolate test environment from Render production environment variables
for env_key in [
    "ENVIRONMENT",
    "ENV",
    "RENDER",
    "RENDER_SERVICE_ID",
    "RENDER_INSTANCE_ID",
    "RENDER_EXTERNAL_URL",
    "RENDER_SERVICE_NAME",
    "RENDER_SERVICE_TYPE",
]:
    os.environ.pop(env_key, None)

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

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
    PasswordResetToken,
    AccountVerificationToken
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
        db.query(AccountVerificationToken).delete()
        db.query(Exercise).filter(Exercise.is_custom == True).delete()
        db.query(FoodItem).filter(FoodItem.is_custom == True).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    import backend.main
    backend.main.engine = engine
    backend.main.SessionLocal = TestingSessionLocal
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


class EmailOutbox:
    """In-memory test email outbox to capture outbound emails and tokens safely."""
    def __init__(self):
        self.emails = []
        self.tokens_by_email = {}
        self.latest_token = None

    def clear(self):
        self.emails.clear()
        self.tokens_by_email.clear()
        self.latest_token = None

    def get_token(self, email: str = None) -> str:
        if email and email in self.tokens_by_email:
            return self.tokens_by_email[email]
        return self.latest_token


test_outbox = EmailOutbox()


def mock_resend_send(params):
    """Safe test-only mock for resend.Emails.send that records emails and tokens."""
    to_list = params.get("to", [])
    to_email = to_list[0] if isinstance(to_list, list) and to_list else str(to_list)
    text_content = params.get("text", "") + " " + params.get("html", "")

    # Extract token from email content
    match = re.search(
        r"(?:Reset Token \(if prompted\):|Verification Token \(if prompted\):|\?token=|\?verify_token=)\s*([A-Za-z0-9_-]+)",
        text_content
    )
    token = match.group(1) if match else None

    test_outbox.emails.append({"to": to_email, "token": token, "params": params})
    if to_email and token:
        test_outbox.tokens_by_email[to_email] = token
    if token:
        test_outbox.latest_token = token

    return {"id": "mock_resend_msg_test_id"}


@pytest.fixture(autouse=True)
def mock_resend_api(monkeypatch):
    """
    Ensures tests NEVER send real emails or depend on a real Resend API key.
    Mocks resend.Emails.send and captures sent emails and tokens in test_outbox.
    """
    test_outbox.clear()
    for k in (
        "ENVIRONMENT", "ENV", "RENDER", "RENDER_SERVICE_ID",
        "RENDER_INSTANCE_ID", "RENDER_EXTERNAL_URL", "RENDER_SERVICE_NAME", "RENDER_SERVICE_TYPE"
    ):
        monkeypatch.delenv(k, raising=False)

    monkeypatch.setenv("RESEND_API_KEY", "re_test_mock_api_key_12345")
    monkeypatch.setenv("EMAIL_FROM", "DesiFit Security <onboarding@resend.dev>")
    with patch("resend.Emails.send", side_effect=mock_resend_send):
        yield test_outbox
    test_outbox.clear()


@pytest.fixture
def email_outbox():
    return test_outbox

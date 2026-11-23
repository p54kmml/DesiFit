import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from backend.models import User, AccountVerificationToken
from backend.services.email_service import (
    is_resend_configured,
    is_email_configured,
    send_password_reset_email,
    send_account_verification_email,
    get_from_email
)
from backend.auth import hash_reset_token


def test_resend_sdk_configuration(monkeypatch):
    """Verifies Resend SDK configuration detection."""
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key_12345")
    assert is_resend_configured() is True
    assert is_email_configured() is True

    monkeypatch.setenv("RESEND_API_KEY", "")
    assert is_resend_configured() is False


def test_get_from_email_resolution(monkeypatch):
    """Verifies sender email address resolution."""
    monkeypatch.setenv("EMAIL_FROM", "DesiFit Custom <custom@desifit.in>")
    assert get_from_email() == "DesiFit Custom <custom@desifit.in>"

    monkeypatch.delenv("EMAIL_FROM", raising=False)
    monkeypatch.delenv("SMTP_FROM_EMAIL", raising=False)
    monkeypatch.delenv("SMTP_USERNAME", raising=False)
    assert get_from_email() == "DesiFit <onboarding@resend.dev>"


def test_password_reset_email_delivery_via_resend(monkeypatch):
    """Verifies that send_password_reset_email dispatches via Resend SDK with proper parameters."""
    monkeypatch.setenv("RESEND_API_KEY", "re_valid_key_12345")
    monkeypatch.setenv("EMAIL_FROM", "DesiFit <onboarding@resend.dev>")
    monkeypatch.setenv("FRONTEND_URL", "http://localhost:8501")

    with patch("resend.Emails.send") as mock_send:
        mock_send.return_value = {"id": "resend_reset_msg_001"}
        success = send_password_reset_email(
            to_email="priyanshuoberoi789@gmail.com",
            reset_token="sample_reset_token_xyz"
        )
        assert success is True
        assert mock_send.called
        call_args = mock_send.call_args[0][0]
        assert call_args["to"] == ["priyanshuoberoi789@gmail.com"]
        assert "Password Reset" in call_args["subject"]
        assert "sample_reset_token_xyz" in call_args["html"]
        assert "http://localhost:8501/?token=sample_reset_token_xyz" in call_args["html"]


def test_account_verification_email_delivery_via_resend(monkeypatch):
    """Verifies that send_account_verification_email dispatches via Resend SDK with verification link."""
    monkeypatch.setenv("RESEND_API_KEY", "re_valid_key_12345")
    monkeypatch.setenv("EMAIL_FROM", "DesiFit <onboarding@resend.dev>")
    monkeypatch.setenv("FRONTEND_URL", "http://localhost:8501")

    with patch("resend.Emails.send") as mock_send:
        mock_send.return_value = {"id": "resend_verify_msg_002"}
        success = send_account_verification_email(
            to_email="priyanshuoberoi789@gmail.com",
            verification_token="sample_verify_token_abc",
            full_name="Priyanshu Oberoi"
        )
        assert success is True
        assert mock_send.called
        call_args = mock_send.call_args[0][0]
        assert call_args["to"] == ["priyanshuoberoi789@gmail.com"]
        assert "Verify Your Account" in call_args["subject"]
        assert "sample_verify_token_abc" in call_args["html"]
        assert "http://localhost:8501/?verify_token=sample_verify_token_abc" in call_args["html"]


def test_email_delivery_failure_handling_does_not_crash(monkeypatch):
    """Verifies that Resend API errors are caught, logged, and return False without throwing exceptions."""
    monkeypatch.setenv("RESEND_API_KEY", "re_mock_key_123")
    monkeypatch.setenv("SMTP_HOST", "")  # No SMTP fallback

    with patch("resend.Emails.send", side_effect=Exception("API connection timeout")):
        result_reset = send_password_reset_email("user@example.com", "token123")
        assert result_reset is False

        result_verify = send_account_verification_email("user@example.com", "token123")
        assert result_verify is False


def test_registration_creates_verification_token_and_verifies_successfully(client, db_session: Session):
    """Verifies complete account registration, verification token generation, and successful email verification."""
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": "verify_test@desifit.in",
        "username": "verify_tester",
        "full_name": "Verify Tester",
        "password": "Password!123"
    })
    assert reg_resp.status_code == 201
    user_data = reg_resp.json()
    assert user_data["username"] == "verify_tester"
    assert user_data["is_verified"] is False

    # Check token record in database
    user = db_session.query(User).filter(User.username == "verify_tester").first()
    assert user is not None
    assert user.is_verified is False

    token_rec = db_session.query(AccountVerificationToken).filter(AccountVerificationToken.user_id == user.id).first()
    assert token_rec is not None
    assert token_rec.used is False
    assert token_rec.used_at is None

    # Verify 24-hour expiration window
    now = datetime.now(timezone.utc)
    exp = token_rec.expires_at if token_rec.expires_at.tzinfo else token_rec.expires_at.replace(tzinfo=timezone.utc)
    diff = exp - now
    assert 22 <= diff.total_seconds() / 3600 <= 25

    # Retrieve dev token for testing verification
    raw_token = user_data.get("dev_verification_token")
    if not raw_token:
        # Generate token directly for testing if email was delivered
        raw_token = "test_manual_verify_token_12345"
        token_rec.token_hash = hash_reset_token(raw_token)
        db_session.commit()

    # Verify the account
    verify_resp = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert verify_resp.status_code == 200
    assert verify_resp.json()["verified"] is True

    # User in DB must now be verified
    db_session.refresh(user)
    assert user.is_verified is True
    db_session.refresh(token_rec)
    assert token_rec.used is True


def test_verification_token_single_use_enforcement(client, db_session: Session):
    """Verifies that an account verification token cannot be reused once consumed."""
    client.post("/api/v1/auth/register", json={
        "email": "single_use@desifit.in",
        "username": "single_use_user",
        "full_name": "Single Use",
        "password": "Password!123"
    })
    user = db_session.query(User).filter(User.username == "single_use_user").first()
    token_rec = db_session.query(AccountVerificationToken).filter(AccountVerificationToken.user_id == user.id).first()

    raw_token = "token_single_use_test_12345"
    token_rec.token_hash = hash_reset_token(raw_token)
    db_session.commit()

    # First use succeeds
    v1 = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert v1.status_code == 200

    # Second use must be rejected
    v2 = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert v2.status_code == 400
    assert "already been used" in v2.json()["detail"]


def test_expired_verification_token_rejection(client, db_session: Session):
    """Verifies that an expired verification token is strictly rejected."""
    client.post("/api/v1/auth/register", json={
        "email": "expired_verify@desifit.in",
        "username": "expired_user",
        "full_name": "Expired User",
        "password": "Password!123"
    })
    user = db_session.query(User).filter(User.username == "expired_user").first()
    token_rec = db_session.query(AccountVerificationToken).filter(AccountVerificationToken.user_id == user.id).first()

    raw_token = "token_expired_test_12345"
    token_rec.token_hash = hash_reset_token(raw_token)
    # Set expiration in the past
    token_rec.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.commit()

    res = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert res.status_code == 400
    assert "expired" in res.json()["detail"].lower()


def test_invalid_verification_token_rejection(client):
    """Verifies that invalid or random verification tokens are rejected."""
    res = client.post("/api/v1/auth/verify-email", json={"token": "completely_bogus_token_xyz_999"})
    assert res.status_code == 400
    assert "invalid or unrecognized" in res.json()["detail"].lower()


def test_production_mode_never_exposes_tokens(client, monkeypatch):
    """Confirms production environment never returns dev verification or recovery tokens."""
    monkeypatch.setenv("ENVIRONMENT", "production")

    # Registration
    reg_res = client.post("/api/v1/auth/register", json={
        "email": "prod_security@desifit.in",
        "username": "prod_security_user",
        "full_name": "Prod User",
        "password": "Password!123"
    })
    assert reg_res.status_code == 201
    assert reg_res.json()["dev_verification_token"] is None

    # Forgot password
    forgot_res = client.post("/api/v1/auth/forgot-password", json={"email": "prod_security@desifit.in"})
    assert forgot_res.status_code == 200
    assert forgot_res.json()["dev_token"] is None
    assert forgot_res.json()["dev_reset_link"] is None

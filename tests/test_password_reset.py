import hashlib
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy.orm import Session

from backend.models import User, PasswordResetToken
from backend.auth import verify_password
from backend.security.rate_limiter import reset_rate_limiters, email_rate_limiter, ip_rate_limiter
from backend.services.email_service import is_email_configured, send_password_reset_email


def test_existing_login_and_registration_still_work(client):
    """Verify existing registration and login functionality remains fully intact."""
    reg_res = client.post("/api/v1/auth/register", json={
        "email": "regcheck@desifit.in",
        "username": "regchecker",
        "full_name": "Registration Checker",
        "password": "Password123"
    })
    assert reg_res.status_code == 201
    assert reg_res.json()["username"] == "regchecker"

    login_res = client.post("/api/v1/auth/login", json={
        "username": "regchecker",
        "password": "Password123"
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()
    assert login_res.json()["token_type"] == "bearer"


def test_forgot_password_request_valid_email(client, db_session: Session):
    """Verify requesting password reset for a registered email generates a secure, hashed token."""
    client.post("/api/v1/auth/register", json={
        "email": "athlete1@desifit.in",
        "username": "athlete1",
        "full_name": "Athlete One",
        "password": "InitialPassword123"
    })

    res = client.post("/api/v1/auth/forgot-password", json={"email": "athlete1@desifit.in"})
    assert res.status_code == 200
    data = res.json()
    assert "If this email is registered" in data["message"]
    assert data["dev_token"] is not None
    assert data["dev_reset_link"] is not None

    raw_token = data["dev_token"]
    expected_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    # Verify database persistence & security
    user = db_session.query(User).filter(User.email == "athlete1@desifit.in").first()
    token_rec = db_session.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id).first()

    assert token_rec is not None
    # Ensure plaintext token is NEVER saved in the database
    assert token_rec.token_hash != raw_token
    assert token_rec.token_hash == expected_hash
    assert token_rec.used is False
    assert token_rec.used_at is None

    # Verify 15-minute expiration window
    now = datetime.now(timezone.utc)
    exp = token_rec.expires_at if token_rec.expires_at.tzinfo else token_rec.expires_at.replace(tzinfo=timezone.utc)
    diff = exp - now
    assert 13 <= diff.total_seconds() / 60 <= 16


def test_forgot_password_unregistered_email_does_not_leak_user_presence(client):
    """Verify forgot password does not reveal whether an email is registered or not."""
    res = client.post("/api/v1/auth/forgot-password", json={"email": "unknown_ghost_account@desifit.in"})
    assert res.status_code == 200
    data = res.json()
    assert data["message"] == "If this email is registered, a password reset link has been sent."
    assert data["dev_token"] is None
    assert data["dev_reset_link"] is None
    assert data["email_sent"] is False


def test_forgot_password_invalid_email_format(client):
    """Verify invalid email formats are rejected by schema validation."""
    res = client.post("/api/v1/auth/forgot-password", json={"email": "not-a-valid-email"})
    assert res.status_code == 422


def test_expired_token_rejection(client, db_session: Session):
    """Verify expired tokens cannot be used or verified."""
    client.post("/api/v1/auth/register", json={
        "email": "expired_test@desifit.in",
        "username": "expired_user",
        "full_name": "Expired User",
        "password": "Password123"
    })
    req_res = client.post("/api/v1/auth/forgot-password", json={"email": "expired_test@desifit.in"})
    raw_token = req_res.json()["dev_token"]

    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    token_rec = db_session.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()

    # Force expiration 10 minutes into the past
    token_rec.expires_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    db_session.commit()

    # Attempt verification
    verify_res = client.get(f"/api/v1/auth/verify-reset-token?token={raw_token}")
    assert verify_res.status_code == 400
    assert "expired" in verify_res.json()["detail"].lower()

    # Attempt reset
    reset_res = client.post("/api/v1/auth/reset-password", json={
        "token": raw_token,
        "new_password": "NewValidPassword999",
        "confirm_password": "NewValidPassword999"
    })
    assert reset_res.status_code == 400
    assert "expired" in reset_res.json()["detail"].lower()


def test_invalid_token_rejection(client):
    """Verify bogus or malformed tokens are firmly rejected."""
    verify_res = client.get("/api/v1/auth/verify-reset-token?token=random_nonexistent_token_string_123")
    assert verify_res.status_code == 400
    assert "invalid" in verify_res.json()["detail"].lower()

    reset_res = client.post("/api/v1/auth/reset-password", json={
        "token": "random_nonexistent_token_string_123",
        "new_password": "NewValidPassword999",
        "confirm_password": "NewValidPassword999"
    })
    assert reset_res.status_code == 400
    assert "invalid" in reset_res.json()["detail"].lower()


def test_successful_password_reset_and_login(client, db_session: Session):
    """Verify end-to-end password reset flow and subsequent authentication."""
    client.post("/api/v1/auth/register", json={
        "email": "reset_success@desifit.in",
        "username": "reset_success_user",
        "full_name": "Reset Success User",
        "password": "OldPassword123"
    })

    # Request recovery
    req_res = client.post("/api/v1/auth/forgot-password", json={"email": "reset_success@desifit.in"})
    raw_token = req_res.json()["dev_token"]

    # Verify token
    verify_res = client.get(f"/api/v1/auth/verify-reset-token?token={raw_token}")
    assert verify_res.status_code == 200
    assert verify_res.json()["valid"] is True

    # Complete reset
    reset_res = client.post("/api/v1/auth/reset-password", json={
        "token": raw_token,
        "new_password": "BrandNewPassword789",
        "confirm_password": "BrandNewPassword789"
    })
    assert reset_res.status_code == 200
    assert "successfully reset" in reset_res.json()["message"]

    # Token should now be flagged as used in DB
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    token_rec = db_session.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()
    assert token_rec.used is True
    assert token_rec.used_at is not None

    # Old password should no longer work
    old_login = client.post("/api/v1/auth/login", json={
        "username": "reset_success_user",
        "password": "OldPassword123"
    })
    assert old_login.status_code == 401

    # New password should authenticate successfully
    new_login = client.post("/api/v1/auth/login", json={
        "username": "reset_success_user",
        "password": "BrandNewPassword789"
    })
    assert new_login.status_code == 200
    assert "access_token" in new_login.json()


def test_single_use_token_reuse_rejected(client):
    """Verify already-used tokens cannot be reused to change passwords again."""
    client.post("/api/v1/auth/register", json={
        "email": "reuse_test@desifit.in",
        "username": "reuse_tester",
        "full_name": "Reuse Tester",
        "password": "OriginalPassword123"
    })
    req_res = client.post("/api/v1/auth/forgot-password", json={"email": "reuse_test@desifit.in"})
    raw_token = req_res.json()["dev_token"]

    # First reset succeeds
    reset_1 = client.post("/api/v1/auth/reset-password", json={
        "token": raw_token,
        "new_password": "FirstNewPassword123",
        "confirm_password": "FirstNewPassword123"
    })
    assert reset_1.status_code == 200

    # Second reset with identical token MUST fail
    reset_2 = client.post("/api/v1/auth/reset-password", json={
        "token": raw_token,
        "new_password": "SecondNewPassword123",
        "confirm_password": "SecondNewPassword123"
    })
    assert reset_2.status_code == 400
    assert "already been used" in reset_2.json()["detail"].lower()


def test_password_hashing_and_complexity(client, db_session: Session):
    """Verify new password is saved as real bcrypt hash and enforces complexity."""
    client.post("/api/v1/auth/register", json={
        "email": "complexity@desifit.in",
        "username": "complex_user",
        "full_name": "Complex User",
        "password": "StartPassword123"
    })
    req_res = client.post("/api/v1/auth/forgot-password", json={"email": "complexity@desifit.in"})
    raw_token = req_res.json()["dev_token"]

    # Test password mismatch
    mismatch_res = client.post("/api/v1/auth/reset-password", json={
        "token": raw_token,
        "new_password": "StrongPassword123",
        "confirm_password": "DifferentPassword123"
    })
    assert mismatch_res.status_code == 400
    assert "not match" in mismatch_res.json()["detail"]

    # Test too short (< 8 chars)
    short_res = client.post("/api/v1/auth/reset-password", json={
        "token": raw_token,
        "new_password": "P1a",
        "confirm_password": "P1a"
    })
    assert short_res.status_code == 422 or short_res.status_code == 400

    # Test missing uppercase
    no_upper = client.post("/api/v1/auth/reset-password", json={
        "token": raw_token,
        "new_password": "alllowercase123",
        "confirm_password": "alllowercase123"
    })
    assert no_upper.status_code == 400
    assert "uppercase" in no_upper.json()["detail"]

    # Test missing lowercase
    no_lower = client.post("/api/v1/auth/reset-password", json={
        "token": raw_token,
        "new_password": "ALLLOWERCASE123",
        "confirm_password": "ALLLOWERCASE123"
    })
    assert no_lower.status_code == 400
    assert "lowercase" in no_lower.json()["detail"]

    # Test missing number
    no_num = client.post("/api/v1/auth/reset-password", json={
        "token": raw_token,
        "new_password": "NoNumbersHereAtAll",
        "confirm_password": "NoNumbersHereAtAll"
    })
    assert no_num.status_code == 400
    assert "number" in no_num.json()["detail"]

    # Valid reset and bcrypt verification
    valid_res = client.post("/api/v1/auth/reset-password", json={
        "token": raw_token,
        "new_password": "ValidStrongPassword123",
        "confirm_password": "ValidStrongPassword123"
    })
    assert valid_res.status_code == 200

    user = db_session.query(User).filter(User.username == "complex_user").first()
    assert "ValidStrongPassword123" not in user.hashed_password
    assert user.hashed_password.startswith("$2b$") or user.hashed_password.startswith("$2a$")
    assert verify_password("ValidStrongPassword123", user.hashed_password) is True


def test_new_reset_request_invalidates_previous_active_tokens(client, db_session: Session):
    """Verify that generating a new token invalidates any previously generated active tokens for that user."""
    client.post("/api/v1/auth/register", json={
        "email": "multi_token@desifit.in",
        "username": "multi_token_user",
        "full_name": "Multi Token User",
        "password": "OriginalPassword123"
    })

    # First request
    res1 = client.post("/api/v1/auth/forgot-password", json={"email": "multi_token@desifit.in"})
    token1 = res1.json()["dev_token"]

    # Second request
    res2 = client.post("/api/v1/auth/forgot-password", json={"email": "multi_token@desifit.in"})
    token2 = res2.json()["dev_token"]

    assert token1 != token2

    # Attempting to use Token 1 must fail because Token 2 superseded it
    reset_with_token1 = client.post("/api/v1/auth/reset-password", json={
        "token": token1,
        "new_password": "NewAttemptPassword123",
        "confirm_password": "NewAttemptPassword123"
    })
    assert reset_with_token1.status_code == 400

    # Token 2 should work cleanly
    reset_with_token2 = client.post("/api/v1/auth/reset-password", json={
        "token": token2,
        "new_password": "NewAttemptPassword123",
        "confirm_password": "NewAttemptPassword123"
    })
    assert reset_with_token2.status_code == 200


def test_rate_limiting_enforcement(client):
    """Verify rate limiting triggers 429 Too Many Requests after threshold is exceeded."""
    reset_rate_limiters()
    target_email = "ratelimit_target@desifit.in"

    client.post("/api/v1/auth/register", json={
        "email": target_email,
        "username": "ratelimit_user",
        "full_name": "Rate Limit User",
        "password": "Password123"
    })

    # Allowed: requests 1, 2, 3
    for _ in range(3):
        res = client.post("/api/v1/auth/forgot-password", json={"email": target_email})
        assert res.status_code == 200

    # 4th request for same email should trigger 429
    res_blocked = client.post("/api/v1/auth/forgot-password", json={"email": target_email})
    assert res_blocked.status_code == 429
    assert "too many" in res_blocked.json()["detail"].lower()

    reset_rate_limiters()


def test_multi_user_isolation_and_security(client):
    """Verify User A's token cannot reset User B's password and accounts remain strictly isolated."""
    # Register User A
    client.post("/api/v1/auth/register", json={
        "email": "user_a@desifit.in",
        "username": "user_a",
        "full_name": "User Alpha",
        "password": "PasswordA123"
    })

    # Register User B
    client.post("/api/v1/auth/register", json={
        "email": "user_b@desifit.in",
        "username": "user_b",
        "full_name": "User Beta",
        "password": "PasswordB123"
    })

    # User A requests reset
    res_a = client.post("/api/v1/auth/forgot-password", json={"email": "user_a@desifit.in"})
    token_a = res_a.json()["dev_token"]

    # Reset with User A's token
    client.post("/api/v1/auth/reset-password", json={
        "token": token_a,
        "new_password": "NewPasswordA123",
        "confirm_password": "NewPasswordA123"
    })

    # User A can log in with new password
    login_a_new = client.post("/api/v1/auth/login", json={
        "username": "user_a",
        "password": "NewPasswordA123"
    })
    assert login_a_new.status_code == 200

    # User B's password must NOT be modified
    login_b = client.post("/api/v1/auth/login", json={
        "username": "user_b",
        "password": "PasswordB123"
    })
    assert login_b.status_code == 200

    # User B cannot log in with User A's new password
    login_b_wrong = client.post("/api/v1/auth/login", json={
        "username": "user_b",
        "password": "NewPasswordA123"
    })
    assert login_b_wrong.status_code == 401


def test_sqlite_persistence_across_sessions(client, db_session: Session):
    """Verify reset tokens and updated passwords persist reliably in SQLite database."""
    client.post("/api/v1/auth/register", json={
        "email": "persist_check@desifit.in",
        "username": "persist_checker",
        "full_name": "Persistence Checker",
        "password": "OriginalPassword123"
    })

    req_res = client.post("/api/v1/auth/forgot-password", json={"email": "persist_check@desifit.in"})
    raw_token = req_res.json()["dev_token"]

    # Expire and refresh session to verify persistence
    db_session.expire_all()
    user = db_session.query(User).filter(User.username == "persist_checker").first()
    assert len(user.password_reset_tokens) == 1
    token_db = user.password_reset_tokens[0]
    assert token_db.used is False

    # Execute reset
    client.post("/api/v1/auth/reset-password", json={
        "token": raw_token,
        "new_password": "PersistedNewPassword123",
        "confirm_password": "PersistedNewPassword123"
    })

    # Re-query across fresh query to ensure SQLite write succeeded
    db_session.expire_all()
    user_updated = db_session.query(User).filter(User.username == "persist_checker").first()
    assert verify_password("PersistedNewPassword123", user_updated.hashed_password) is True
    assert user_updated.password_reset_tokens[0].used is True


def test_email_service_behavior(monkeypatch):
    """Verify email service behavior under configured and unconfigured SMTP settings."""
    # When SMTP is not configured:
    monkeypatch.setenv("SMTP_HOST", "")
    assert is_email_configured() is False
    assert send_password_reset_email("user@example.com", "dummy_token") is False

    # When SMTP is configured:
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USERNAME", "mailer@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret123")
    monkeypatch.setenv("SMTP_FROM_EMAIL", "noreply@desifit.com")

    assert is_email_configured() is True

    # Mock smtplib to simulate real SMTP communication
    mock_smtp_instance = MagicMock()
    with patch("smtplib.SMTP", return_value=mock_smtp_instance) as mock_smtp_class:
        mock_smtp_instance.__enter__.return_value = mock_smtp_instance
        sent = send_password_reset_email("user@example.com", "dummy_token_123")
        assert sent is True
        assert mock_smtp_instance.starttls.called
        assert mock_smtp_instance.login.called
        assert mock_smtp_instance.send_message.called


def test_production_mode_never_exposes_dev_token(client, monkeypatch):
    """Verify production environment NEVER returns or exposes dev_token or dev_reset_link."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    client.post("/api/v1/auth/register", json={
        "email": "prod_user@desifit.in",
        "username": "prod_user",
        "full_name": "Prod User",
        "password": "Password123"
    })

    res = client.post("/api/v1/auth/forgot-password", json={"email": "prod_user@desifit.in"})
    assert res.status_code == 200
    data = res.json()
    assert data["dev_token"] is None
    assert data["dev_reset_link"] is None
    assert data["dev_note"] is None
    assert data["message"] == "If this email is registered, a password reset link has been sent."


def test_verify_token_endpoint_validation(client):
    """Verify /verify-reset-token rejects empty, too-short, and non-existent tokens."""
    # Too short
    short_res = client.get("/api/v1/auth/verify-reset-token?token=short")
    assert short_res.status_code == 400
    assert "invalid" in short_res.json()["detail"].lower()

    # Non-existent
    bad_res = client.get("/api/v1/auth/verify-reset-token?token=non_existent_token_1234567890123")
    assert bad_res.status_code == 400
    assert "invalid or unrecognized" in bad_res.json()["detail"].lower()


# ==============================================================================
# DEDICATED SECURITY AUDIT TEST CASES
# ==============================================================================

def test_security_case_1_old_password_cannot_authenticate(client):
    """
    SECURITY CASE 1 - OLD PASSWORD:
    After a successful password reset, verify that the previous password cannot authenticate.
    """
    email = "sec_oldpass@desifit.in"
    username = "sec_oldpass_user"
    original_pass = "OriginalPass123"
    new_pass = "NewStrongPass2026!"

    # 1. Register test user
    reg = client.post("/api/v1/auth/register", json={
        "email": email,
        "username": username,
        "full_name": "Security OldPass Tester",
        "password": original_pass
    })
    assert reg.status_code == 201

    # 2. Verify initial login works
    login_init = client.post("/api/v1/auth/login", json={
        "username": username,
        "password": original_pass
    })
    assert login_init.status_code == 200
    assert "access_token" in login_init.json()

    # 3. Request password reset
    fp_res = client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert fp_res.status_code == 200
    token = fp_res.json()["dev_token"]
    assert token is not None

    # 4. Perform password reset
    reset_res = client.post("/api/v1/auth/reset-password", json={
        "token": token,
        "new_password": new_pass,
        "confirm_password": new_pass
    })
    assert reset_res.status_code == 200
    assert "successfully reset" in reset_res.json()["message"]

    # 5. VERIFY OLD PASSWORD CANNOT AUTHENTICATE
    old_login = client.post("/api/v1/auth/login", json={
        "username": username,
        "password": original_pass
    })
    assert old_login.status_code == 401
    assert "Invalid username or password" in old_login.json()["detail"]
    assert "access_token" not in old_login.json()


def test_security_case_2_new_password_authenticates_successfully(client):
    """
    SECURITY CASE 2 - NEW PASSWORD:
    Verify that the new password works and generates a valid JWT session.
    """
    email = "sec_newpass@desifit.in"
    username = "sec_newpass_user"
    original_pass = "InitialPass123"
    new_pass = "UpdatedSecretPass2026!"

    # 1. Register test user
    client.post("/api/v1/auth/register", json={
        "email": email,
        "username": username,
        "full_name": "Security NewPass Tester",
        "password": original_pass
    })

    # 2. Request and complete password reset
    fp_res = client.post("/api/v1/auth/forgot-password", json={"email": email})
    token = fp_res.json()["dev_token"]

    reset_res = client.post("/api/v1/auth/reset-password", json={
        "token": token,
        "new_password": new_pass,
        "confirm_password": new_pass
    })
    assert reset_res.status_code == 200

    # 3. VERIFY NEW PASSWORD WORKS AND ISSUES VALID JWT
    new_login = client.post("/api/v1/auth/login", json={
        "username": username,
        "password": new_pass
    })
    assert new_login.status_code == 200
    data = new_login.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["username"] == username

    # 4. Verify access token authorizes access to protected /auth/me route
    jwt_token = data["access_token"]
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {jwt_token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email


def test_security_case_3_token_expiry_via_clock_manipulation(client, db_session: Session):
    """
    SECURITY CASE 3 - TOKEN EXPIRY:
    Generate a reset token, simulate advancing time beyond its 15-minute expiry,
    and verify that the token is rejected by both verification and reset endpoints.
    """
    email = "sec_expiry@desifit.in"
    username = "sec_expiry_user"
    original_pass = "ExpPass123"

    # 1. Register user & request token
    client.post("/api/v1/auth/register", json={
        "email": email,
        "username": username,
        "full_name": "Security Expiry Tester",
        "password": original_pass
    })
    fp_res = client.post("/api/v1/auth/forgot-password", json={"email": email})
    raw_token = fp_res.json()["dev_token"]

    # 2. Simulate advancing time by 16 minutes (beyond 15-min limit)
    # Using controlled database expiration timestamp simulation:
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    token_rec = db_session.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()
    assert token_rec is not None

    # Shift expires_at 1 minute into the past (equivalent to advancing clock 16 mins)
    token_rec.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()

    # 3. VERIFY TOKEN VERIFICATION REJECTS EXPIRED TOKEN
    verify_res = client.get(f"/api/v1/auth/verify-reset-token?token={raw_token}")
    assert verify_res.status_code == 400
    assert "expired" in verify_res.json()["detail"].lower()

    # 4. VERIFY PASSWORD RESET REJECTS EXPIRED TOKEN
    reset_res = client.post("/api/v1/auth/reset-password", json={
        "token": raw_token,
        "new_password": "FailedNewPass2026!",
        "confirm_password": "FailedNewPass2026!"
    })
    assert reset_res.status_code == 400
    assert "expired" in reset_res.json()["detail"].lower()

    # 5. Confirm original password is still active and unchanged
    still_valid = client.post("/api/v1/auth/login", json={
        "username": username,
        "password": original_pass
    })
    assert still_valid.status_code == 200


def test_security_case_4_token_reuse_rejected(client):
    """
    SECURITY CASE 4 - TOKEN REUSE:
    Generate a reset token, successfully reset the password, then attempt to use
    the same token again. It must be rejected.
    """
    email = "sec_reuse@desifit.in"
    username = "sec_reuse_user"
    original_pass = "StartPass123"
    first_new_pass = "FirstUpdatePass2026!"
    second_new_pass = "SecondUpdatePass2026!"

    # 1. Register & request token
    client.post("/api/v1/auth/register", json={
        "email": email,
        "username": username,
        "full_name": "Security Reuse Tester",
        "password": original_pass
    })
    fp_res = client.post("/api/v1/auth/forgot-password", json={"email": email})
    token = fp_res.json()["dev_token"]

    # 2. First password reset (MUST SUCCEED)
    first_reset = client.post("/api/v1/auth/reset-password", json={
        "token": token,
        "new_password": first_new_pass,
        "confirm_password": first_new_pass
    })
    assert first_reset.status_code == 200

    # 3. ATTEMPT TO REUSE THE SAME TOKEN (MUST BE REJECTED)
    second_reset = client.post("/api/v1/auth/reset-password", json={
        "token": token,
        "new_password": second_new_pass,
        "confirm_password": second_new_pass
    })
    assert second_reset.status_code == 400
    assert "already been used" in second_reset.json()["detail"].lower()

    # 4. Confirm the second password attempt did NOT take effect
    bad_login = client.post("/api/v1/auth/login", json={
        "username": username,
        "password": second_new_pass
    })
    assert bad_login.status_code == 401

    # 5. Confirm the first reset password IS what authenticates
    good_login = client.post("/api/v1/auth/login", json={
        "username": username,
        "password": first_new_pass
    })
    assert good_login.status_code == 200


def test_security_case_5_invalid_and_modified_token_rejected(client):
    """
    SECURITY CASE 5 - INVALID TOKEN:
    Verify that a random or modified token is rejected.
    """
    email = "sec_invalid@desifit.in"
    username = "sec_invalid_user"
    original_pass = "BasePass123"

    client.post("/api/v1/auth/register", json={
        "email": email,
        "username": username,
        "full_name": "Security Invalid Tester",
        "password": original_pass
    })
    fp_res = client.post("/api/v1/auth/forgot-password", json={"email": email})
    valid_token = fp_res.json()["dev_token"]

    # 1. Test Completely Random Token
    random_token = "X" * 43
    res_rand_verify = client.get(f"/api/v1/auth/verify-reset-token?token={random_token}")
    assert res_rand_verify.status_code == 400
    assert "invalid or unrecognized" in res_rand_verify.json()["detail"].lower()

    res_rand_reset = client.post("/api/v1/auth/reset-password", json={
        "token": random_token,
        "new_password": "NewAttemptPass2026!",
        "confirm_password": "NewAttemptPass2026!"
    })
    assert res_rand_reset.status_code == 400
    assert "invalid or unrecognized" in res_rand_reset.json()["detail"].lower()

    # 2. Test Tampered/Modified Valid Token (flip 4 characters)
    tampered_token = valid_token[:-4] + ("ZZZZ" if valid_token[-4:] != "ZZZZ" else "YYYY")
    res_tamp_verify = client.get(f"/api/v1/auth/verify-reset-token?token={tampered_token}")
    assert res_tamp_verify.status_code == 400
    assert "invalid or unrecognized" in res_tamp_verify.json()["detail"].lower()

    res_tamp_reset = client.post("/api/v1/auth/reset-password", json={
        "token": tampered_token,
        "new_password": "NewAttemptPass2026!",
        "confirm_password": "NewAttemptPass2026!"
    })
    assert res_tamp_reset.status_code == 400
    assert "invalid or unrecognized" in res_tamp_reset.json()["detail"].lower()

    # 3. Test Malformed / Too-Short Token
    short_token = "short123"
    res_short = client.get(f"/api/v1/auth/verify-reset-token?token={short_token}")
    assert res_short.status_code == 400
    assert "invalid token format" in res_short.json()["detail"].lower()


def test_security_case_6_single_use_guarantee_confirmed(client, db_session: Session):
    """
    SECURITY CASE 6 - SINGLE-USE:
    Confirm that a token cannot be used for a second password reset.
    Verify database state transition (used=True, used_at is set).
    """
    email = "sec_singleuse@desifit.in"
    username = "sec_singleuse_user"
    original_pass = "FirstSecret123"
    reset_pass = "ResetSecret2026!"

    client.post("/api/v1/auth/register", json={
        "email": email,
        "username": username,
        "full_name": "Security Single-Use Tester",
        "password": original_pass
    })
    fp_res = client.post("/api/v1/auth/forgot-password", json={"email": email})
    token = fp_res.json()["dev_token"]

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    token_rec = db_session.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()
    assert token_rec.used is False
    assert token_rec.used_at is None

    # Step 1: Use token for the only allowed time
    reset_ok = client.post("/api/v1/auth/reset-password", json={
        "token": token,
        "new_password": reset_pass,
        "confirm_password": reset_pass
    })
    assert reset_ok.status_code == 200

    # Verify database state transition
    db_session.refresh(token_rec)
    assert token_rec.used is True
    assert token_rec.used_at is not None

    # Step 2: Attempt second use (MUST FAIL)
    attempt_2 = client.post("/api/v1/auth/reset-password", json={
        "token": token,
        "new_password": "AnotherNewPass2026!",
        "confirm_password": "AnotherNewPass2026!"
    })
    assert attempt_2.status_code == 400
    assert "already been used" in attempt_2.json()["detail"].lower()

    # Step 3: Attempt third use (MUST FAIL)
    attempt_3 = client.post("/api/v1/auth/reset-password", json={
        "token": token,
        "new_password": "YetAnotherPass2026!",
        "confirm_password": "YetAnotherPass2026!"
    })
    assert attempt_3.status_code == 400
    assert "already been used" in attempt_3.json()["detail"].lower()

    # Step 4: Verification route also reports token as already used
    verify_consumed = client.get(f"/api/v1/auth/verify-reset-token?token={token}")
    assert verify_consumed.status_code == 400
    assert "already been used" in verify_consumed.json()["detail"].lower()

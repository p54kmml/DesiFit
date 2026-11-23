import pytest
from unittest.mock import patch
from backend.services.email_service import (
    is_production,
    is_resend_configured,
    is_email_configured,
    get_resend_api_key,
    get_from_email,
    get_frontend_url,
    send_password_reset_email,
    _deliver_email
)


# ==============================================================================
# 1. RESEND CONFIGURATION DETECTION
# ==============================================================================

def test_resend_configuration_detection(monkeypatch):
    """Verify that is_resend_configured() accurately detects valid Resend API keys."""
    # Clean environment
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("SMTP_HOST", raising=False)
    assert is_resend_configured() is False
    assert is_email_configured() is False

    # Valid key with re_ prefix
    monkeypatch.setenv("RESEND_API_KEY", "re_1234567890abcdef")
    assert is_resend_configured() is True
    assert is_email_configured() is True

    # Arbitrary strings without re_ prefix (even if long) must NOT be accepted
    monkeypatch.setenv("RESEND_API_KEY", "resend_api_key_long_value")
    assert is_resend_configured() is False

    # Invalid empty or too-short dummy strings
    monkeypatch.setenv("RESEND_API_KEY", "")
    assert is_resend_configured() is False

    monkeypatch.setenv("RESEND_API_KEY", "short")
    assert is_resend_configured() is False


# ==============================================================================
# 2. QUOTED AND UNQUOTED ENVIRONMENT VALUES
# ==============================================================================

def test_quoted_and_unquoted_environment_values(monkeypatch):
    """
    Verify that surrounding double quotes, single quotes, and accidental whitespace
    are properly stripped from RESEND_API_KEY, EMAIL_FROM, and FRONTEND_URL.
    """
    # Double-quoted values with whitespace
    monkeypatch.setenv("RESEND_API_KEY", '  "re_quoted_key_12345" \n')
    monkeypatch.setenv("EMAIL_FROM", '  "DesiFit Team <security@desifit.in>"  ')
    monkeypatch.setenv("FRONTEND_URL", '  "https://desifit-app.onrender.com/"  ')

    assert get_resend_api_key() == "re_quoted_key_12345"
    assert is_resend_configured() is True
    assert get_from_email() == "DesiFit Team <security@desifit.in>"
    assert get_frontend_url() == "https://desifit-app.onrender.com"

    # Single-quoted values with whitespace
    monkeypatch.setenv("RESEND_API_KEY", "  're_single_quoted_67890'  ")
    monkeypatch.setenv("EMAIL_FROM", "  'onboarding@resend.dev'  ")
    monkeypatch.setenv("FRONTEND_URL", "  'https://desifit.streamlit.app'  ")

    assert get_resend_api_key() == "re_single_quoted_67890"
    assert is_resend_configured() is True
    assert get_from_email() == "onboarding@resend.dev"
    assert get_frontend_url() == "https://desifit.streamlit.app"

    # Clean unquoted values
    monkeypatch.setenv("RESEND_API_KEY", "re_clean_unquoted_key_111")
    monkeypatch.setenv("EMAIL_FROM", "no-reply@desifit.com")

    assert get_resend_api_key() == "re_clean_unquoted_key_111"
    assert get_from_email() == "no-reply@desifit.com"


# ==============================================================================
# 3. PRODUCTION DETECTION ON RENDER
# ==============================================================================

def test_production_detection_on_render(monkeypatch):
    """
    Verify is_production() reliably identifies all standard Render platform indicators
    as well as standard cloud environment variables.
    """
    # Clean local state
    for k in (
        "ENVIRONMENT", "ENV", "RENDER", "RENDER_SERVICE_ID",
        "RENDER_INSTANCE_ID", "RENDER_EXTERNAL_URL", "RENDER_SERVICE_NAME", "RENDER_SERVICE_TYPE"
    ):
        monkeypatch.delenv(k, raising=False)

    assert is_production() is False

    # 1. RENDER=true
    monkeypatch.setenv("RENDER", "true")
    assert is_production() is True
    monkeypatch.delenv("RENDER", raising=False)

    # 2. RENDER=1
    monkeypatch.setenv("RENDER", "1")
    assert is_production() is True
    monkeypatch.delenv("RENDER", raising=False)

    # 3. RENDER_SERVICE_ID
    monkeypatch.setenv("RENDER_SERVICE_ID", "srv-testservice12345")
    assert is_production() is True
    monkeypatch.delenv("RENDER_SERVICE_ID", raising=False)

    # 4. RENDER_INSTANCE_ID
    monkeypatch.setenv("RENDER_INSTANCE_ID", "inst-instance67890")
    assert is_production() is True
    monkeypatch.delenv("RENDER_INSTANCE_ID", raising=False)

    # 5. RENDER_EXTERNAL_URL
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://desifit-api.onrender.com")
    assert is_production() is True
    monkeypatch.delenv("RENDER_EXTERNAL_URL", raising=False)

    # 6. RENDER_SERVICE_NAME
    monkeypatch.setenv("RENDER_SERVICE_NAME", "desifit-backend")
    assert is_production() is True
    monkeypatch.delenv("RENDER_SERVICE_NAME", raising=False)

    # 7. Standard ENVIRONMENT=production
    monkeypatch.setenv("ENVIRONMENT", "production")
    assert is_production() is True
    monkeypatch.delenv("ENVIRONMENT", raising=False)

    # 8. Standard ENV=prod
    monkeypatch.setenv("ENV", "prod")
    assert is_production() is True


# ==============================================================================
# 4. SUCCESSFUL RESEND EMAIL SENDING
# ==============================================================================

def test_successful_resend_email_sending(client, monkeypatch):
    """
    Verify that with Resend configured:
    1. /forgot-password calls Resend Emails.send with sanitized parameters.
    2. Response returns status 200 with email_sent=True.
    3. dev_token and dev_reset_link are strictly None.
    """
    # Register user
    client.post("/api/v1/auth/register", json={
        "email": "resend_success_test@desifit.in",
        "username": "resend_user",
        "full_name": "Resend Athlete",
        "password": "Password123!"
    })

    monkeypatch.setenv("RESEND_API_KEY", '"re_valid_test_key_888"')
    monkeypatch.setenv("EMAIL_FROM", '"DesiFit <onboarding@resend.dev>"')
    monkeypatch.setenv("FRONTEND_URL", "https://desifit.onrender.com")

    with patch("resend.Emails.send") as mock_send:
        mock_send.return_value = {"id": "msg_resend_test_ok_123"}

        res = client.post("/api/v1/auth/forgot-password", json={"email": "resend_success_test@desifit.in"})
        assert res.status_code == 200
        data = res.json()

        assert data["email_sent"] is True
        assert data["dev_token"] is None
        assert data["dev_reset_link"] is None
        assert data["dev_note"] is None
        assert "If this email is registered" in data["message"]

        # Verify Resend API was called with sanitized values
        assert mock_send.called
        call_params = mock_send.call_args[0][0]
        assert call_params["from"] == "DesiFit <onboarding@resend.dev>"
        assert call_params["to"] == ["resend_success_test@desifit.in"]
        assert "https://desifit.onrender.com/?token=" in call_params["html"]


# ==============================================================================
# 5. FAILED EMAIL DELIVERY WITHOUT EXPOSING RECOVERY TOKENS
# ==============================================================================

def test_failed_email_delivery_never_exposes_tokens(client, monkeypatch):
    """
    CRITICAL SECURITY CHECK:
    When Resend is configured but the delivery attempt fails (e.g. invalid domain, rate limit):
    1. The exception must be logged safely without crashing.
    2. email_sent must be False.
    3. dev_token and dev_reset_link MUST REMAIN NONE (never exposed to client).
    """
    client.post("/api/v1/auth/register", json={
        "email": "resend_fail_safe@desifit.in",
        "username": "failsafe_user",
        "full_name": "FailSafe Athlete",
        "password": "Password123!"
    })

    monkeypatch.setenv("RESEND_API_KEY", "re_live_key_configured")
    monkeypatch.setenv("EMAIL_FROM", "unverified_domain@test.com")
    monkeypatch.delenv("SMTP_HOST", raising=False)
    # Even if RENDER is not explicitly set:
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)

    with patch("resend.Emails.send", side_effect=Exception("Domain not verified in Resend")):
        res = client.post("/api/v1/auth/forgot-password", json={"email": "resend_fail_safe@desifit.in"})
        assert res.status_code == 200
        data = res.json()

        assert data["email_sent"] is False
        assert data["dev_token"] is None, "dev_token MUST NOT be exposed when email provider is configured"
        assert data["dev_reset_link"] is None, "dev_reset_link MUST NOT be exposed when email provider is configured"
        assert data["dev_note"] is None


# ==============================================================================
# 6. DEVELOPMENT FALLBACK WHEN EMAIL IS GENUINELY NOT CONFIGURED
# ==============================================================================

def test_development_fallback_when_email_unconfigured(client, monkeypatch):
    """
    Verify that in local development when email is genuinely NOT configured:
    1. dev_token and dev_reset_link are provided to facilitate offline testing.
    2. The token can be used to successfully complete password reset.
    """
    client.post("/api/v1/auth/register", json={
        "email": "local_dev_user@example.com",
        "username": "local_dev_athlete",
        "full_name": "Local Dev Athlete",
        "password": "OriginalPassword123!"
    })

    # Clear all email and production flags
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("RENDER_SERVICE_ID", raising=False)
    monkeypatch.delenv("RENDER_INSTANCE_ID", raising=False)
    monkeypatch.delenv("RENDER_EXTERNAL_URL", raising=False)
    monkeypatch.delenv("RENDER_SERVICE_NAME", raising=False)

    assert is_production() is False
    assert is_email_configured() is False

    res = client.post("/api/v1/auth/forgot-password", json={"email": "local_dev_user@example.com"})
    assert res.status_code == 200
    data = res.json()

    assert data["email_sent"] is False
    assert data["dev_token"] is not None
    assert len(data["dev_token"]) >= 32
    assert "token=" in data["dev_reset_link"]

    # Verify the dev_token can be verified and used to reset password
    dev_token = data["dev_token"]
    verify_res = client.get("/api/v1/auth/verify-reset-token", params={"token": dev_token})
    assert verify_res.status_code == 200
    assert verify_res.json()["valid"] is True

    reset_res = client.post("/api/v1/auth/reset-password", json={
        "token": dev_token,
        "new_password": "NewSecurePassword123!",
        "confirm_password": "NewSecurePassword123!"
    })
    assert reset_res.status_code == 200

    # Verify user can login with new password
    login_res = client.post("/api/v1/auth/login", json={
        "username": "local_dev_athlete",
        "password": "NewSecurePassword123!"
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

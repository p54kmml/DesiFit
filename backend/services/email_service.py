import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger("desifit.email")


def _clean_env_val(val: Optional[str]) -> str:
    """Strips whitespace and surrounding single or double quotes."""
    if not val:
        return ""
    cleaned = val.strip()
    while cleaned and (cleaned[0] in ('"', "'") or cleaned[-1] in ('"', "'")):
        cleaned = cleaned.strip('"').strip("'").strip()
    return cleaned


def is_production() -> bool:
    """
    Determines if the application is running in a production or deployed environment.
    Recognizes standard production deployment flags:
    - ENVIRONMENT in ('production', 'prod', 'staging')
    - ENV in ('production', 'prod', 'staging')
    - Render indicators: RENDER=true/1, RENDER_SERVICE_ID, RENDER_INSTANCE_ID,
      RENDER_EXTERNAL_URL, RENDER_SERVICE_NAME, RENDER_SERVICE_TYPE
    """
    env = _clean_env_val(os.getenv("ENVIRONMENT", "")).lower()
    if env in ("production", "prod", "staging"):
        return True
    env_short = _clean_env_val(os.getenv("ENV", "")).lower()
    if env_short in ("production", "prod", "staging"):
        return True

    # Render deployment detection
    render_flag = _clean_env_val(os.getenv("RENDER", "")).lower()
    if render_flag in ("true", "1", "yes"):
        return True
    for render_var in (
        "RENDER_SERVICE_ID",
        "RENDER_INSTANCE_ID",
        "RENDER_EXTERNAL_URL",
        "RENDER_SERVICE_NAME",
        "RENDER_SERVICE_TYPE",
    ):
        if bool(_clean_env_val(os.getenv(render_var, ""))):
            return True

    return False


def get_resend_api_key() -> str:
    """Returns the sanitized Resend API key, stripping surrounding quotes and whitespace."""
    return _clean_env_val(os.getenv("RESEND_API_KEY", ""))


def is_resend_configured() -> bool:
    """
    Returns True if a valid Resend API key is present.
    Requires a non-empty key starting with 're_'. Arbitrary strings based only on length are rejected.
    """
    api_key = get_resend_api_key()
    return bool(api_key and api_key.startswith("re_"))


def is_smtp_configured() -> bool:
    """Returns True if SMTP host is configured in the environment."""
    return bool(_clean_env_val(os.getenv("SMTP_HOST", "")))


def is_email_configured() -> bool:
    """Returns True if either Resend or SMTP is configured."""
    return is_resend_configured() or is_smtp_configured()


def get_frontend_url() -> str:
    """Retrieves the configured frontend base URL, stripping quotes and trailing slash."""
    url = _clean_env_val(os.getenv("FRONTEND_URL", "")).rstrip("/")
    if url:
        return url
    render_url = _clean_env_val(os.getenv("RENDER_EXTERNAL_URL", "")).rstrip("/")
    if render_url:
        return render_url
    return "http://localhost:8501"


def get_from_email() -> str:
    """Resolves the sender email address from environment variables, stripping whitespace and surrounding quotes."""
    for key in ("EMAIL_FROM", "RESEND_FROM", "SMTP_FROM_EMAIL", "SMTP_USERNAME"):
        val = _clean_env_val(os.getenv(key, ""))
        if val:
            return val
    return "DesiFit <onboarding@resend.dev>"


def _deliver_smtp(to_email: str, subject: str, html_content: str, plain_text: str) -> bool:
    """Sends email via legacy SMTP configuration."""
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port_raw = os.getenv("SMTP_PORT", "587").strip()
    try:
        smtp_port = int(smtp_port_raw)
    except ValueError:
        smtp_port = 587

    smtp_username = os.getenv("SMTP_USERNAME", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_from = get_from_email()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_from
    msg["To"] = to_email

    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10) as server:
                if smtp_username and smtp_password:
                    server.login(smtp_username, smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                if smtp_username and smtp_password:
                    server.login(smtp_username, smtp_password)
                server.send_message(msg)
        logger.info("Email delivered via SMTP to %s", to_email)
        return True
    except Exception as e:
        logger.error("Failed to deliver email via SMTP: %s", type(e).__name__)
        return False


def _deliver_email(to_email: str, subject: str, html_content: str, plain_text: str) -> bool:
    """
    Delivers an email using Resend SDK (primary) or SMTP (fallback).
    Returns True if delivery succeeded, False otherwise.
    Never exposes credentials or raw exception payloads.
    """
    if is_resend_configured():
        try:
            import resend
            resend.api_key = get_resend_api_key()
            from_email = get_from_email()

            params = {
                "from": from_email,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
                "text": plain_text
            }
            resp = resend.Emails.send(params)
            msg_id = resp.get("id") if isinstance(resp, dict) else getattr(resp, "id", None)
            if msg_id:
                logger.info("Email delivered via Resend to %s (id: %s)", to_email, msg_id)
                return True
            logger.warning("Resend send call returned no message ID for %s", to_email)
            return False
        except Exception as e:
            logger.error("Resend delivery failed for %s: %s", to_email, type(e).__name__)
            if is_smtp_configured():
                logger.info("Attempting SMTP delivery fallback for %s...", to_email)
                return _deliver_smtp(to_email, subject, html_content, plain_text)
            return False

    elif is_smtp_configured():
        return _deliver_smtp(to_email, subject, html_content, plain_text)

    else:
        logger.debug("No email delivery provider configured.")
        return False


def send_password_reset_email(to_email: str, reset_token: str, frontend_url: Optional[str] = None) -> bool:
    """
    Sends a secure password reset email via Resend or SMTP.
    Returns True if sent, False if provider is not configured or sending failed.
    """
    base_url = (frontend_url or get_frontend_url()).rstrip("/")
    reset_link = f"{base_url}/?token={reset_token}"

    subject = "DesiFit — Password Reset Request"

    plain_text = (
        "Hello,\n\n"
        "We received a request to reset your password for your DesiFit account.\n\n"
        "Click or copy this link into your browser to set a new password:\n"
        f"{reset_link}\n\n"
        f"Reset Token (if prompted): {reset_token}\n\n"
        "This link and token will expire in 15 minutes and can only be used once.\n"
        "If you did not request a password reset, you can safely ignore this email.\n\n"
        "Best regards,\n"
        "The DesiFit Team\n"
    )

    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Reset Your DesiFit Password</title>
</head>
<body style="margin: 0; padding: 24px; background-color: #0d1117; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #e6edf3;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 580px; margin: 0 auto; background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; overflow: hidden;">
    <tr>
      <td style="padding: 32px 32px 16px 32px; text-align: center; border-bottom: 1px solid #30363d;">
        <span style="font-size: 26px; font-weight: 800; color: #a3e635; letter-spacing: 1px;">⚡ DESIFIT</span>
        <div style="font-size: 13px; color: #8b949e; margin-top: 4px;">AI Fitness Companion</div>
      </td>
    </tr>
    <tr>
      <td style="padding: 32px;">
        <h2 style="margin: 0 0 16px 0; color: #ffffff; font-size: 20px; font-weight: 700;">Password Recovery</h2>
        <p style="margin: 0 0 16px 0; color: #c9d1d9; font-size: 15px; line-height: 1.5;">
          We received a request to reset the password for your DesiFit account. Click the button below to choose your new password:
        </p>
        <div style="text-align: center; margin: 28px 0;">
          <a href="{reset_link}" style="background-color: #a3e635; color: #0d1117; font-weight: 700; font-size: 15px; text-decoration: none; padding: 12px 28px; border-radius: 8px; display: inline-block;">
            Reset My Password
          </a>
        </div>
        <p style="margin: 20px 0 8px 0; color: #8b949e; font-size: 13px;">
          Or copy and paste this link into your browser:
        </p>
        <p style="margin: 0 0 20px 0; word-break: break-all; font-size: 12px; color: #58a6ff; font-family: monospace;">
          {reset_link}
        </p>
        <div style="background-color: #21262d; border: 1px solid #30363d; border-radius: 6px; padding: 12px 16px; margin: 20px 0;">
          <div style="font-size: 12px; color: #8b949e; text-transform: uppercase; font-weight: 600;">Reset Token (if prompted):</div>
          <div style="font-family: monospace; font-size: 14px; color: #a3e635; word-break: break-all; margin-top: 4px;">{reset_token}</div>
        </div>
        <p style="margin: 20px 0 0 0; color: #8b949e; font-size: 12px; line-height: 1.5;">
          ⏱️ This link and token are valid for <strong>15 minutes</strong> and will be invalidated after a single use.<br>
          If you did not request this reset, your account is secure and you can disregard this email.
        </p>
      </td>
    </tr>
    <tr>
      <td style="padding: 20px 32px; background-color: #12161c; border-top: 1px solid #30363d; text-align: center; color: #8b949e; font-size: 12px;">
        © DesiFit • Commercial Fitness SaaS Suite
      </td>
    </tr>
  </table>
 </body>
</html>"""

    return _deliver_email(to_email, subject, html_content, plain_text)


def send_account_verification_email(
    to_email: str,
    verification_token: str,
    full_name: Optional[str] = None,
    frontend_url: Optional[str] = None
) -> bool:
    """
    Sends an account verification email via Resend or SMTP.
    Returns True if sent, False if provider is not configured or sending failed.
    """
    base_url = (frontend_url or get_frontend_url()).rstrip("/")
    verify_link = f"{base_url}/?verify_token={verification_token}"
    name_display = full_name or "Athlete"

    subject = "DesiFit — Verify Your Account"

    plain_text = (
        f"Namaste {name_display},\n\n"
        "Welcome to DesiFit! Please verify your email address to confirm your account.\n\n"
        "Click or copy this link into your browser to verify:\n"
        f"{verify_link}\n\n"
        f"Verification Token (if prompted): {verification_token}\n\n"
        "This link will expire in 24 hours.\n\n"
        "Best regards,\n"
        "The DesiFit Team\n"
    )

    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Verify Your DesiFit Account</title>
</head>
<body style="margin: 0; padding: 24px; background-color: #0d1117; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #e6edf3;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 580px; margin: 0 auto; background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; overflow: hidden;">
    <tr>
      <td style="padding: 32px 32px 16px 32px; text-align: center; border-bottom: 1px solid #30363d;">
        <span style="font-size: 26px; font-weight: 800; color: #a3e635; letter-spacing: 1px;">⚡ DESIFIT</span>
        <div style="font-size: 13px; color: #8b949e; margin-top: 4px;">AI Fitness Companion</div>
      </td>
    </tr>
    <tr>
      <td style="padding: 32px;">
        <h2 style="margin: 0 0 16px 0; color: #ffffff; font-size: 20px; font-weight: 700;">Welcome to DesiFit!</h2>
        <p style="margin: 0 0 16px 0; color: #c9d1d9; font-size: 15px; line-height: 1.5;">
          Namaste <strong>{name_display}</strong>,<br>
          Thank you for creating your DesiFit account. Please verify your email address to complete your registration:
        </p>
        <div style="text-align: center; margin: 28px 0;">
          <a href="{verify_link}" style="background-color: #a3e635; color: #0d1117; font-weight: 700; font-size: 15px; text-decoration: none; padding: 12px 28px; border-radius: 8px; display: inline-block;">
            Verify My Account
          </a>
        </div>
        <p style="margin: 20px 0 8px 0; color: #8b949e; font-size: 13px;">
          Or copy and paste this verification link into your browser:
        </p>
        <p style="margin: 0 0 20px 0; word-break: break-all; font-size: 12px; color: #58a6ff; font-family: monospace;">
          {verify_link}
        </p>
        <div style="background-color: #21262d; border: 1px solid #30363d; border-radius: 6px; padding: 12px 16px; margin: 20px 0;">
          <div style="font-size: 12px; color: #8b949e; text-transform: uppercase; font-weight: 600;">Verification Token (if prompted):</div>
          <div style="font-family: monospace; font-size: 14px; color: #a3e635; word-break: break-all; margin-top: 4px;">{verification_token}</div>
        </div>
        <p style="margin: 20px 0 0 0; color: #8b949e; font-size: 12px; line-height: 1.5;">
          ⏱️ This verification link and token will expire in <strong>24 hours</strong>.<br>
          If you did not create this account, you can safely ignore this email.
        </p>
      </td>
    </tr>
    <tr>
      <td style="padding: 20px 32px; background-color: #12161c; border-top: 1px solid #30363d; text-align: center; color: #8b949e; font-size: 12px;">
        © DesiFit • Commercial Fitness SaaS Suite
      </td>
    </tr>
  </table>
</body>
</html>"""

    return _deliver_email(to_email, subject, html_content, plain_text)

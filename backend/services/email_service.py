import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger("desifit.email")


def is_email_configured() -> bool:
    """Returns True only if SMTP host is configured in the environment."""
    return bool(os.getenv("SMTP_HOST", "").strip())


def get_frontend_url() -> str:
    """Retrieves the configured frontend base URL."""
    return os.getenv("FRONTEND_URL", "http://localhost:8501").rstrip("/")


def send_password_reset_email(to_email: str, reset_token: str, frontend_url: Optional[str] = None) -> bool:
    """
    Sends a secure password reset email via configured SMTP.
    Returns True if sent, False if SMTP is not configured or sending failed.
    Never logs or exposes the reset token or email credentials.
    """
    if not is_email_configured():
        return False

    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port_raw = os.getenv("SMTP_PORT", "587").strip()
    try:
        smtp_port = int(smtp_port_raw)
    except ValueError:
        smtp_port = 587

    smtp_username = os.getenv("SMTP_USERNAME", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_from = os.getenv("SMTP_FROM_EMAIL", "").strip() or smtp_username or "noreply@desifit.com"

    base_url = (frontend_url or get_frontend_url()).rstrip("/")
    reset_link = f"{base_url}/?token={reset_token}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "DesiFit — Password Reset Request"
    msg["From"] = smtp_from
    msg["To"] = to_email

    # Plaintext fallback
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

    # Dark-themed HTML email
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
        return True
    except Exception as e:
        logger.error("Failed to deliver password reset email: %s", type(e).__name__)
        return False

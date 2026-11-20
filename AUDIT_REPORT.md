# DesiFit Project Audit & Security Review

Audit basis: uploaded `DesiFit (2).zip` source archive and subsequent secure account recovery enhancement.

## Summary

DesiFit is a full-stack commercial fitness application featuring a FastAPI backend, Streamlit frontend, SQLAlchemy/SQLite persistence, AI assistant with rule-based fallback, workout generator, nutrition/progress tracking, and a cryptographically secure Forgot Password & Account Recovery suite.

## Verified by automated tests

- **61 total backend and security tests passed (100% pass rate)**.
- **Real bcrypt cryptography verified**: All password hashes are verified with genuine bcrypt hashing (`bcrypt>=4.0.0`), without any test compatibility shims.
- Dedicated Security Audit Cases Verified:
  1. **OLD PASSWORD INACTIVATION**: Confirmed that upon successful password reset, the old password is permanently invalid and rejected with HTTP 401.
  2. **NEW PASSWORD AUTHENTICATION**: Confirmed that the newly set password generates valid JWT sessions and accesses protected user data.
  3. **TOKEN EXPIRATION ENFORCEMENT**: Confirmed that advancing time beyond the 15-minute validity window causes both token verification and reset attempts to be rejected with HTTP 400 ("expired").
  4. **TOKEN REUSE REJECTION**: Confirmed that attempting to reuse an already-consumed token is rejected with HTTP 400 ("already been used").
  5. **INVALID & TAMPERED TOKEN REJECTION**: Confirmed that random, tampered (modified characters), or malformed tokens are rejected with HTTP 400.
  6. **SINGLE-USE GUARANTEE**: Confirmed that tokens transition to `used = True` with a timestamp and can never be used for multiple resets.
- Tests cover:
  1. Authentication routes (registration, duplicate rejection, login, and JWT token issuing).
  2. Account recovery flow (`/auth/forgot-password`, `/auth/verify-reset-token`, `/auth/reset-password`).
  3. Cryptographic token generation (43-char URL-safe tokens, 256 bits entropy) and SHA-256 token hashing in the database.
  4. Token expiration enforcement (strict 15-minute validity window).
  5. Single-use token enforcement and rejection of already-used tokens.
  6. Superseeded token invalidation when a new reset request is generated for a user.
  7. Multi-tiered rate limiting by client IP (5 req/15 min) and email address (3 req/15 min).
  8. Account enumeration defense (identical responses for registered vs unregistered emails; constant-time dummy hashing to thwart timing attacks).
  9. Password strength enforcement (min 8 chars, uppercase, lowercase, numeric digit) and confirmation matching.
  10. Multi-user security isolation (User A cannot reset User B's account; User B's credentials remain unimpacted).
  11. SQLite persistence across database sessions and connections.
  12. SMTP email dispatch and error handling without logging credentials or tokens.
  13. User onboarding, Mifflin-St Jeor TDEE calibration, and zero-leaked profile defaults.
  14. Exercise and food catalog isolation, workout planning, and logging.
  15. Progress tracking and AI fallback expert system.

## Account Recovery & Security Architecture

1. **Token Generation & Storage**:
   - Reset tokens are generated using `secrets.token_urlsafe(32)`.
   - The plain token is **never stored in the database**. Only a secure SHA-256 hash (`token_hash`) is persisted in `password_reset_tokens`.
   - Tokens are strictly single-use and expire 15 minutes after issuance.
   - When a user requests a new token, any previously active reset tokens for that user are immediately invalidated (`used = True`).

2. **Rate Limiting**:
   - `backend/security/rate_limiter.py` provides a thread-safe sliding window rate limiter.
   - Enforces max 5 requests per 15 minutes per IP address.
   - Enforces max 3 requests per 15 minutes per email address.
   - Responds with `HTTP 429 Too Many Requests` when limits are exceeded.

3. **Protection Against User Enumeration**:
   - The API returns an identical response whether an email is registered or not: `"If this email is registered, a password reset link has been sent."`
   - Unregistered email requests execute constant-time dummy hash calculations to eliminate timing discrepancies.

4. **Email Configuration & Delivery**:
   - All email credentials (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `FRONTEND_URL`) are read exclusively from environment variables.
   - **Local Development**: When `SMTP_HOST` is unset, the system runs in safe development mode. The response includes an in-app developer helper box with the token for testing, and the app never pretends that an email was sent.
   - **Production**: When `ENVIRONMENT=production`, developer tokens and links are strictly omitted from API responses and client screens. Emails are sent over TLS/SSL using responsive, dark-themed HTML templates.
   - Application logs never contain reset tokens, passwords, or SMTP credentials.

5. **Frontend Experience**:
   - Dark SaaS theme consistent with DesiFit styling (`#0d1117` background, `#161b22` cards, `#a3e635` lime accents).
   - A clearly visible "Forgot Password?" link is located directly below the password input on the login view.
   - Email submission screen with real-time feedback and clear guidance.
   - Reset password screen supporting direct URL links (`?token=...`) as well as manual token entry.
   - Responsive "Back to Login" controls throughout the recovery flow.

6. **Database Integrity**:
   - `safe_migrate_db()` in `backend/main.py` creates the new `password_reset_tokens` table automatically on startup via SQLAlchemy metadata creation.
   - No existing user data, workout logs, nutrition records, or profiles are altered or dropped.

## Email Testing Guide

### Testing Locally (Without SMTP Server)
1. Ensure `SMTP_HOST` in `.env` is empty.
2. Launch DesiFit: `python run.py`.
3. Open `http://localhost:8501`.
4. Click **🔑 Forgot Password?** below the password field.
5. Enter a registered email (e.g. create an account first or use an existing one) and submit.
6. The app displays a development mode box containing the 15-minute recovery token.
7. Click **👉 Proceed to Reset Password with Token**, enter your new password, and submit.
8. Log in with the new password.

### Testing in Production (With Real SMTP Provider)
1. Add your SMTP provider credentials to `.env`:
   ```env
   SMTP_HOST="smtp.mailgun.org"       # Or smtp.sendgrid.net, smtp.gmail.com, etc.
   SMTP_PORT=587
   SMTP_USERNAME="postmaster@yourdomain.com"
   SMTP_PASSWORD="your-secure-smtp-password"
   SMTP_FROM_EMAIL="noreply@desifit.in"
   FRONTEND_URL="https://your-domain.com"
   ENVIRONMENT="production"
   ```
2. Start the services.
3. Submit a reset request for your email.
4. Check your inbox for the branded DesiFit email and click the button or link.
5. Complete password reset and log in.

## Run Locally on Windows 10

1. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```
2. **Setup Environment**:
   ```powershell
   copy .env.example .env
   ```
3. **Execute All Automated Tests**:
   ```powershell
   python -m pytest -v
   ```
4. **Launch Application**:
   ```powershell
   python run.py
   ```
   - Streamlit Frontend: `http://localhost:8501`
   - FastAPI Backend & Swagger: `http://127.0.0.1:8000/docs`

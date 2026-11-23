import os
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, UserProfile, PasswordResetToken, AccountVerificationToken, utcnow
from backend.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    VerifyResetTokenResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
    ResendVerificationRequest,
    ResendVerificationResponse
)
from backend.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    validate_password_strength,
    hash_reset_token
)
from backend.security.rate_limiter import ip_rate_limiter, email_rate_limiter
from backend.services.email_service import (
    send_password_reset_email,
    send_account_verification_email,
    is_email_configured,
    get_frontend_url,
    is_production
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if username or email already exists
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already registered"
        )
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )

    hashed_pw = hash_password(user_in.password)
    user = User(
        email=user_in.email,
        username=user_in.username,
        full_name=user_in.full_name,
        hashed_password=hashed_pw,
        is_verified=False
    )
    db.add(user)
    db.flush()

    # Create empty, un-onboarded profile for the new user (no hardcoded personal sample info)
    profile = UserProfile(
        user_id=user.id,
        is_onboarded=False
    )
    db.add(profile)

    # Generate secure, single-use account verification token (24-hour expiry)
    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_reset_token(raw_token)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=24)

    verification_record = AccountVerificationToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        used=False
    )
    db.add(verification_record)
    db.commit()
    db.refresh(user)

    # Dispatch account verification email via Resend (primary) or SMTP
    email_sent = False
    if is_email_configured():
        email_sent = send_account_verification_email(
            to_email=user.email,
            verification_token=raw_token,
            full_name=user.full_name
        )

    user.verification_email_sent = email_sent

    # Development-only fallback: never expose in production or when email provider is configured
    is_prod = is_production()
    email_configured = is_email_configured()
    if not is_prod and not email_configured and not email_sent:
        user.dev_verification_token = raw_token
    else:
        user.dev_verification_token = None

    return user


@router.post("/login", response_model=Token)
def login_user(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is disabled"
        )

    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )
    is_onboarded = user.profile.is_onboarded if user.profile else False
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        is_onboarded=is_onboarded
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(
    request_in: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Initiates password recovery:
    - Rate-limits by client IP and email.
    - Generates a cryptographically random reset token (valid for 15 mins).
    - Stores only the SHA-256 hash of the token.
    - Invalidates existing active tokens for this user.
    - Sends an email if SMTP is configured.
    - Does not reveal whether the email is registered.
    """
    # 1. Resolve client IP
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    elif request.client and request.client.host:
        client_ip = request.client.host
    else:
        client_ip = "127.0.0.1"

    # 2. Rate limiting check
    if not ip_rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset requests from this IP address. Please wait before trying again."
        )

    if not email_rate_limiter.is_allowed(request_in.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset requests for this email address. Please wait before trying again."
        )

    # 3. Lookup user
    normalized_email = request_in.email.strip().lower()
    user = db.query(User).filter(User.email.ilike(normalized_email)).first()

    now = datetime.now(timezone.utc)
    is_prod = is_production()
    email_configured = is_email_configured()

    if user and user.is_active:
        # Invalidate any previously generated unused tokens for this user
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False
        ).update({"used": True, "used_at": now})

        # Generate cryptographically secure token (43 chars, 256 bits entropy)
        raw_token = secrets.token_urlsafe(32)
        token_hash = hash_reset_token(raw_token)
        expires_at = now + timedelta(minutes=15)

        reset_record = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            used=False
        )
        db.add(reset_record)
        db.commit()

        email_sent = False
        if email_configured:
            email_sent = send_password_reset_email(to_email=user.email, reset_token=raw_token)

        # STRICT PRODUCTION SECURITY:
        # Never expose tokens or dev links in production environments, when email is configured, or in API responses.
        # Fallback dev tokens are ONLY permissible in strictly local development when email is genuinely unconfigured.
        dev_link = None
        dev_tok = None
        if not is_prod and not email_configured and not email_sent:
            frontend_url = get_frontend_url()
            dev_link = f"{frontend_url}/?token={raw_token}"
            dev_tok = raw_token

        return ForgotPasswordResponse(
            message="If this email is registered, a password reset link has been sent.",
            email_sent=email_sent,
            dev_reset_link=dev_link,
            dev_token=dev_tok
        )
    else:
        # Constant-time dummy operation to prevent timing attacks / user enumeration
        _ = hash_reset_token(secrets.token_urlsafe(32))
        dev_note = None
        if not is_prod:
            dev_note = f"Development Notice: The email '{normalized_email}' was not found in the database. Please register an account first under 'Create Account' or use a registered email address to test recovery."
        return ForgotPasswordResponse(
            message="If this email is registered, a password reset link has been sent.",
            email_sent=False,
            dev_reset_link=None,
            dev_token=None,
            dev_note=dev_note
        )


@router.get("/verify-reset-token", response_model=VerifyResetTokenResponse)
def verify_reset_token(token: str, db: Session = Depends(get_db)):
    """Verifies that a password reset token exists, is not used, and has not expired."""
    if not token or len(token.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token format."
        )

    token_hash = hash_reset_token(token)
    record = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or unrecognized password reset token."
        )

    if record.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset token has already been used."
        )

    now = datetime.now(timezone.utc)
    expires_at = record.expires_at if record.expires_at.tzinfo else record.expires_at.replace(tzinfo=timezone.utc)
    if now > expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset token has expired."
        )

    return VerifyResetTokenResponse(valid=True, message="Token is valid and active.")


@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Completes password reset:
    - Confirms passwords match and validates strength.
    - Validates token authenticity, expiration, and single-use status.
    - Hashes new password using bcrypt.
    - Invalidates the reset token immediately.
    """
    if req.new_password != req.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirmation password do not match."
        )

    is_strong, err_msg = validate_password_strength(req.new_password)
    if not is_strong:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_msg
        )

    token_hash = hash_reset_token(req.token)
    record = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or unrecognized password reset token."
        )

    if record.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset token has already been used."
        )

    now = datetime.now(timezone.utc)
    expires_at = record.expires_at if record.expires_at.tzinfo else record.expires_at.replace(tzinfo=timezone.utc)
    if now > expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset token has expired."
        )

    user = db.query(User).filter(User.id == record.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account associated with this token is invalid or inactive."
        )

    # Securely hash new password with existing bcrypt system
    user.hashed_password = hash_password(req.new_password)

    # Mark token as used (single-use)
    record.used = True
    record.used_at = now

    # Invalidate any other active tokens for this user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used == False
    ).update({"used": True, "used_at": now})

    db.commit()

    return {"message": "Password has been successfully reset. You can now log in with your new password."}


@router.post("/verify-email", response_model=VerifyEmailResponse)
def verify_email(req: VerifyEmailRequest, db: Session = Depends(get_db)):
    """
    Verifies a user's account using a secure, single-use verification token:
    - Token must not be expired (24 hours).
    - Token must not have been used previously (single-use).
    - Upon verification, sets user.is_verified = True and invalidates active tokens.
    """
    if not req.token or len(req.token.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token format."
        )

    token_hash = hash_reset_token(req.token)
    record = db.query(AccountVerificationToken).filter(
        AccountVerificationToken.token_hash == token_hash
    ).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or unrecognized verification token."
        )

    if record.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This verification token has already been used."
        )

    now = datetime.now(timezone.utc)
    expires_at = record.expires_at if record.expires_at.tzinfo else record.expires_at.replace(tzinfo=timezone.utc)
    if now > expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This verification token has expired."
        )

    user = db.query(User).filter(User.id == record.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account associated with this token was not found."
        )

    record.used = True
    record.used_at = now
    user.is_verified = True

    # Invalidate any other active verification tokens for this user
    db.query(AccountVerificationToken).filter(
        AccountVerificationToken.user_id == user.id,
        AccountVerificationToken.used == False
    ).update({"used": True, "used_at": now})

    db.commit()
    return VerifyEmailResponse(
        verified=True,
        message="Email successfully verified. Your DesiFit account is active."
    )


@router.post("/resend-verification", response_model=ResendVerificationResponse)
def resend_verification(
    req: ResendVerificationRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Resends an account verification email:
    - Rate-limited by IP and email.
    - Generates a fresh 24-hour token and invalidates previous unused tokens.
    - Sends via Resend / SMTP.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    elif request.client and request.client.host:
        client_ip = request.client.host
    else:
        client_ip = "127.0.0.1"

    if not ip_rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests from this IP address. Please wait."
        )

    if not email_rate_limiter.is_allowed(req.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many verification requests for this email address. Please wait."
        )

    normalized_email = req.email.strip().lower()
    user = db.query(User).filter(User.email.ilike(normalized_email)).first()
    now = datetime.now(timezone.utc)
    is_prod = is_production()

    if user and not user.is_verified:
        # Invalidate existing unused verification tokens
        db.query(AccountVerificationToken).filter(
            AccountVerificationToken.user_id == user.id,
            AccountVerificationToken.used == False
        ).update({"used": True, "used_at": now})

        raw_token = secrets.token_urlsafe(32)
        token_hash = hash_reset_token(raw_token)
        expires_at = now + timedelta(hours=24)

        token_record = AccountVerificationToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            used=False
        )
        db.add(token_record)
        db.commit()

        email_sent = False
        if is_email_configured():
            email_sent = send_account_verification_email(
                to_email=user.email,
                verification_token=raw_token,
                full_name=user.full_name
            )

        email_configured = is_email_configured()
        dev_token = raw_token if (not is_prod and not email_configured and not email_sent) else None
        return ResendVerificationResponse(
            message="If an unverified account exists for this email, a verification link has been sent.",
            email_sent=email_sent,
            dev_token=dev_token
        )
    else:
        # Constant time dummy operation
        _ = hash_reset_token(secrets.token_urlsafe(32))
        return ResendVerificationResponse(
            message="If an unverified account exists for this email, a verification link has been sent.",
            email_sent=False,
            dev_token=None
        )

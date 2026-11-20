import os
import hashlib
import secrets
import logging
import warnings
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from backend.database import get_db
from backend.models import User

load_dotenv()

logger = logging.getLogger("desifit.security")

DEFAULT_FALLBACK_SECRET = "desifit_ultra_secure_jwt_secret_key_change_in_production"
_raw_secret = os.getenv("SECRET_KEY", "").strip()
IS_PRODUCTION = os.getenv("ENVIRONMENT", "").lower() in ["production", "prod"]

if not _raw_secret or _raw_secret == DEFAULT_FALLBACK_SECRET:
    if IS_PRODUCTION:
        raise RuntimeError(
            "FATAL SECURITY CONFIGURATION: Insecure default or empty SECRET_KEY detected in production environment! "
            "A cryptographically secure SECRET_KEY must be provided via environment variables."
        )
    warnings.warn(
        "[SECURITY WARNING] SECRET_KEY is using an insecure default fallback. "
        "Set a strong production SECRET_KEY (e.g. 32+ characters) in your environment/.env file.",
        UserWarning,
        stacklevel=2
    )
    logger.warning("[SECURITY] Insecure default SECRET_KEY in use. Set SECRET_KEY in .env for production.")
    SECRET_KEY = DEFAULT_FALLBACK_SECRET
else:
    if len(_raw_secret) < 32:
        warnings.warn(
            "[SECURITY WARNING] SECRET_KEY is shorter than 32 characters. Consider using a 256-bit key for production.",
            UserWarning,
            stacklevel=2
        )
    SECRET_KEY = _raw_secret
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

security_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Validates password strength:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one numeric digit
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number."
    return True, None


def hash_reset_token(raw_token: str) -> str:
    """Computes SHA-256 hash of a raw reset token for secure storage."""
    return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generates a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> User:
    """Dependency that extracts and validates the JWT token, returning the authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not auth_credentials:
        raise credentials_exception

    token = auth_credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if username is None or user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id, User.username == username).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user

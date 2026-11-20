import re
from typing import Tuple


def sanitize_username(username: str) -> str:
    """Sanitizes username to alphanumeric and underscores."""
    return re.sub(r"[^a-zA-Z0-9_]", "", username.strip().lower())


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """Checks password complexity requirements."""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    return True, "Password is valid."

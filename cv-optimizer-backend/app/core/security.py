import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Union

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ─── Access Token ────────────────────────────────────────────────────────────

def create_access_token(
    subject: Union[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a short-lived JWT access token (default: ACCESS_TOKEN_EXPIRE_MINUTES)."""
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ─── Refresh Token ───────────────────────────────────────────────────────────

def generate_refresh_token() -> str:
    """
    Generate a cryptographically secure random refresh token string.
    This raw value is sent to the client; only its hash is stored in the DB.
    """
    return secrets.token_urlsafe(64)


def hash_refresh_token(raw_token: str) -> str:
    """SHA-256 hash of the raw refresh token for safe DB storage."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


def refresh_token_expiry() -> datetime:
    """Return the absolute expiry datetime for a new refresh token."""
    return datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )


# ─── Password ────────────────────────────────────────────────────────────────

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# ─── Password Reset Token ────────────────────────────────────────────────────

def create_password_reset_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode = {"exp": expire, "sub": email, "type": "password_reset"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_password_reset_token(token: str) -> Union[str, None]:
    try:
        decoded = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if decoded.get("type") != "password_reset":
            return None
        return decoded["sub"]
    except jwt.JWTError:
        return None

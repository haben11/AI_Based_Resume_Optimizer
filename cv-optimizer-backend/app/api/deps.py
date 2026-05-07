"""
FastAPI dependency: get_current_user

Token resolution order
──────────────────────
1. Authorization: Bearer <token>  header  (used by all API calls)
2. Falls back to nothing — returns 401 so the client can trigger a refresh

The refresh itself is handled by the frontend interceptor calling POST /auth/refresh.
The backend never auto-refreshes; it simply returns 401 with a specific code so
the client knows to retry.
"""

from typing import Generator

from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import TokenPayload

# Standard OAuth2 bearer — used by Swagger UI and the frontend
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token",
    auto_error=False,   # We handle the error ourselves for better messages
)


def get_current_user(
    db: Session = Depends(get_db),
    token: str | None = Depends(reusable_oauth2),
) -> User:
    """
    Validate the JWT access token and return the authenticated User.

    Returns HTTP 401 with  {"detail": "token_expired"}  when the JWT has
    expired — the frontend interceptor catches this specific code and calls
    POST /auth/refresh before retrying the original request.

    Returns HTTP 401 with  {"detail": "Could not validate credentials"}  for
    any other auth failure (missing token, bad signature, etc.).
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        token_data = TokenPayload(**payload)

    except ExpiredSignatureError:
        # Specific error code the frontend interceptor listens for
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token_expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (JWTError, Exception):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if token_data.sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user = db.query(User).filter(User.id == token_data.sub).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    return user

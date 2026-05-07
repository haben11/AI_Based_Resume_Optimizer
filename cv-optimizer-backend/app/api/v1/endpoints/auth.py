"""
Authentication endpoints.

Token strategy
──────────────
• Access token  — short-lived JWT (1 day), returned in the JSON response body.
                  The client stores it in memory / localStorage and sends it as
                  a Bearer header on every request.

• Refresh token — long-lived opaque random string (30 days), stored as an
                  HttpOnly cookie.  Only its SHA-256 hash is persisted in the
                  database so a DB breach cannot be used to forge sessions.

  Development:  cookie is SameSite=Lax, Secure=False  (works over HTTP)
  Production:   cookie is SameSite=None, Secure=True   (works cross-origin HTTPS)

Rotation
────────
Every call to /refresh invalidates the presented token and issues a new one
(one-time-use).  If a token is presented that has already been revoked we
treat it as a potential replay attack and revoke ALL tokens for that user.
"""

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.core.logging import logger
from app.crud.crud_user import user_repo
from app.db.session import get_db
from app.models.refresh_token import RefreshToken
from app.schemas.msg import Msg
from app.schemas.token import Token, TokenRefreshResponse
from app.schemas.user import User as UserSchema, UserCreate

router = APIRouter()


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    """Write the refresh token into an HttpOnly cookie."""
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=raw_token,
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        # In production: Secure=True, SameSite=None (cross-origin)
        # In development: Secure=False, SameSite=Lax (plain HTTP)
        secure=settings.is_production,
        samesite="none" if settings.is_production else "lax",
        path="/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Expire the refresh cookie immediately."""
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        httponly=True,
        secure=settings.is_production,
        samesite="none" if settings.is_production else "lax",
        path="/",
    )


def _issue_tokens(
    response: Response,
    db: Session,
    user_id: str,
    request: Request | None = None,
) -> Token:
    """
    Create a new access + refresh token pair, persist the refresh token hash,
    set the cookie, and return the access token response.
    """
    # Access token
    access_token = security.create_access_token(
        subject=user_id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    # Refresh token
    raw_refresh = security.generate_refresh_token()
    token_hash = security.hash_refresh_token(raw_refresh)
    expires_at = security.refresh_token_expiry()

    db_token = RefreshToken(
        token_hash=token_hash,
        user_id=user_id,
        expires_at=expires_at,
        user_agent=(request.headers.get("user-agent", "")[:512] if request else None),
        ip_address=(request.client.host if request and request.client else None),
    )
    db.add(db_token)
    db.commit()

    _set_refresh_cookie(response, raw_refresh)

    return Token(access_token=access_token, token_type="bearer")


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/login/access-token", response_model=Token)
def login_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2-compatible login.  Returns an access token in the body and sets
    the refresh token as an HttpOnly cookie.
    """
    user = user_repo.get_by_email(db, email=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    logger.info("user_login", user_id=str(user.id), email=user.email)
    return _issue_tokens(response, db, str(user.id), request)


@router.post("/refresh", response_model=TokenRefreshResponse)
def refresh_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    # Cookie is read automatically by FastAPI from the request
    refresh_token: str | None = Cookie(default=None, alias=settings.REFRESH_COOKIE_NAME),
) -> Any:
    """
    Exchange a valid refresh token cookie for a new access token + rotated
    refresh token.  The old refresh token is revoked immediately (one-time use).

    If the presented token is already revoked we assume a replay attack and
    revoke every refresh token for that user (force full re-login).
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not refresh_token:
        raise credentials_error

    token_hash = security.hash_refresh_token(refresh_token)
    db_token: RefreshToken | None = (
        db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    )

    if db_token is None:
        raise credentials_error

    # Replay attack detection: token exists but was already revoked
    if db_token.revoked:
        logger.warning(
            "refresh_token_replay_detected",
            user_id=str(db_token.user_id),
            token_id=str(db_token.id),
        )
        # Revoke ALL tokens for this user — force re-login on all devices
        db.query(RefreshToken).filter(
            RefreshToken.user_id == db_token.user_id,
            RefreshToken.revoked == False,  # noqa: E712
        ).update({"revoked": True})
        db.commit()
        _clear_refresh_cookie(response)
        raise credentials_error

    if db_token.is_expired:
        db_token.revoked = True
        db.commit()
        _clear_refresh_cookie(response)
        raise credentials_error

    # Rotate: revoke the old token
    db_token.revoked = True
    db.commit()

    # Issue a fresh pair
    user_id = str(db_token.user_id)
    new_tokens = _issue_tokens(response, db, user_id, request)

    logger.info("refresh_token_rotated", user_id=user_id)
    return TokenRefreshResponse(
        access_token=new_tokens.access_token,
        token_type="bearer",
    )


@router.post("/logout", response_model=Msg)
def logout(
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=settings.REFRESH_COOKIE_NAME),
) -> Any:
    """
    Revoke the current refresh token and clear the cookie.
    The client should also discard its access token from memory.
    """
    if refresh_token:
        token_hash = security.hash_refresh_token(refresh_token)
        db_token = (
            db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
        )
        if db_token and not db_token.revoked:
            db_token.revoked = True
            db.commit()
            logger.info("user_logout", user_id=str(db_token.user_id))

    _clear_refresh_cookie(response)
    return {"msg": "Successfully logged out"}


# ─── Registration / Password Reset ───────────────────────────────────────────

@router.post("/register", response_model=UserSchema)
def register_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    user = user_repo.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    return user_repo.create(db, obj_in=user_in)


@router.post("/password-recovery/{email}", response_model=Msg)
def recover_password(email: str, db: Session = Depends(get_db)) -> Any:
    user = user_repo.get_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    token = security.create_password_reset_token(email=email)
    logger.info("password_recovery_token_generated", email=email, token=token)
    return {"msg": "Password recovery email sent (check logs in dev)"}


@router.post("/reset-password/", response_model=Msg)
def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(get_db),
) -> Any:
    email = security.verify_password_reset_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = user_repo.get_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    user_repo.update(db, db_obj=user, obj_in={"password": new_password})
    return {"msg": "Password updated successfully"}

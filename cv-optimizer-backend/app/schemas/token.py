from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    """Returned in the login response body (access token only)."""
    access_token: str
    token_type: str = "bearer"


class TokenRefreshResponse(BaseModel):
    """Returned by the /refresh endpoint."""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Decoded JWT payload."""
    sub: Optional[str] = None   # user UUID as string
    type: Optional[str] = None  # "access" | "password_reset"

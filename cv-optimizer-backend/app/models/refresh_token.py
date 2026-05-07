import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class RefreshToken(Base):
    """
    Persisted refresh tokens.

    Only the SHA-256 hash of the raw token is stored — the raw value is
    never written to the database, so a DB breach cannot be used to forge
    new sessions.

    Rotation strategy: every call to /auth/refresh invalidates the
    presented token and issues a brand-new one (one-time-use tokens).
    """

    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # SHA-256 hash of the raw token sent to the client
    token_hash = Column(String(64), unique=True, nullable=False, index=True)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Soft-revoke: set to True on logout or token rotation
    revoked = Column(Boolean, default=False, nullable=False)

    # Optional: track which device/browser issued this token
    user_agent = Column(String(512), nullable=True)
    ip_address = Column(String(45), nullable=True)  # supports IPv6

    user = relationship("User", back_populates="refresh_tokens")

    # ── helpers ──────────────────────────────────────────────────────────────

    @property
    def is_expired(self) -> bool:
        from datetime import timezone
        return datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc)

    @property
    def is_valid(self) -> bool:
        return not self.revoked and not self.is_expired

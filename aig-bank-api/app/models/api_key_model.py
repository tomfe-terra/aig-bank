"""API Key model for authentication."""

from datetime import UTC, datetime
import secrets

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, func
from sqlalchemy.orm import relationship

from ..core.db import Base
from ..utils.encryption import aes_gcm_encryptor
from ..utils.id_generator import generate_uuid_str


class APIKey(Base):
    """API Key model for client/secret authentication."""

    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=generate_uuid_str, index=True)

    encrypted_secret = Column(String(512), nullable=False)

    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="api_keys")

    def __repr__(self) -> str:
        """String representation of APIKey."""
        return f"<APIKey(id={self.id}, name={self.name})>"

    @staticmethod
    def generate_secret() -> str:
        """Generate a new secret."""
        return secrets.token_urlsafe(64)

    @staticmethod
    def encrypt_secret(secret: str) -> str:
        """Encrypt the raw secret for storage using AES-GCM."""
        return aes_gcm_encryptor.encrypt(secret)

    def decrypt_secret(self) -> str | None:
        """Decrypt and return the raw secret using AES-GCM."""
        if not self.encrypted_secret:
            return None
        return aes_gcm_encryptor.decrypt(self.encrypted_secret)

    def update_last_used(self) -> None:
        """Update last used timestamp."""
        self.last_used_at = datetime.now(UTC)  # type: ignore[assignment]

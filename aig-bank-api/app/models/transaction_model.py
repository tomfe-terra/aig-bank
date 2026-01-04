"""Transaction model for banking operations."""

from typing import TYPE_CHECKING

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from ..utils.id_generator import generate_uuid_str

if TYPE_CHECKING:
    from ..core.db import Base
else:
    from ..core.db import Base


class Transaction(Base):
    """Bank transaction model."""

    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid_str, index=True)

    account_id = Column(String(36), ForeignKey("accounts.id"), nullable=False, index=True)

    type = Column(String(50), nullable=False, index=True)

    amount_cents = Column(Integer, nullable=False)

    related_account_id = Column(String(36), ForeignKey("accounts.id"), nullable=True, index=True)

    idempotency_key = Column(String(255), unique=True, nullable=False, index=True)

    meta = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    account = relationship("Account", foreign_keys=[account_id], back_populates="transactions")
    related_account = relationship("Account", foreign_keys=[related_account_id])

    def __repr__(self) -> str:
        """String representation of Transaction."""
        return f"<Transaction(id={self.id}, type={self.type}, amount={self.amount_cents})>"

    @property
    def amount_dollars(self) -> float:
        """Get amount in dollars for display purposes."""
        return float(self.amount_cents) / 100.0

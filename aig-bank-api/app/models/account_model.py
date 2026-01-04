"""Account model for banking operations."""

import secrets

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from ..core.db import Base
from ..utils.id_generator import generate_uuid_str


class Account(Base):
    """Bank account model."""

    __tablename__ = "accounts"

    id = Column(String(36), primary_key=True, default=generate_uuid_str, index=True)

    number = Column(
        String(18),
        unique=True,
        index=True,
        nullable=False,
    )

    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, unique=False, index=True)

    user = relationship("User", back_populates="accounts")
    transactions = relationship(
        "Transaction",
        back_populates="account",
        cascade="all, delete-orphan",
        foreign_keys="Transaction.account_id",
    )
    credit_cards = relationship("CreditCard", back_populates="account", cascade="all, delete-orphan")
    loans = relationship("Loan", back_populates="account", cascade="all, delete-orphan")

    balance_cents = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        """String representation of Account."""
        return f"<Account(id={self.id}, number={self.number}, balance={self.balance_cents})>"

    def __str__(self) -> str:
        """String representation of Account."""
        return f"Account {self.number} (balance: ${self.balance_dollars:.2f})"

    @classmethod
    def generate_account_number(cls) -> str:
        """Generate a unique account number."""
        return str(secrets.randbelow(999999999999) + 1000000000)[:12]

    @property
    def balance_dollars(self) -> float:
        """Get balance in dollars (for display purposes)."""
        return float(self.balance_cents) / 100.0

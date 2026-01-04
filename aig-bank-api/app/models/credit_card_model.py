"""CreditCard model for banking operations."""

from datetime import UTC

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from ..core.db import Base
from ..core.enums import CardBrand, CardStatus
from ..utils.id_generator import generate_uuid_str


class CreditCard(Base):
    """Credit card model."""

    __tablename__ = "credit_cards"

    id = Column(String(36), primary_key=True, default=generate_uuid_str, index=True)

    account_id = Column(String(36), ForeignKey("accounts.id"), nullable=False, index=True)

    pan_fingerprint = Column(
        String(128),
        nullable=False,
        index=True,
    )

    pan_ciphertext = Column(
        String(512),
        nullable=False,
    )

    cvv_ciphertext = Column(
        String(256),
        nullable=False,
    )

    last4 = Column(String(4), nullable=False)
    brand = Column(String(50), nullable=False)
    exp_month = Column(Integer, nullable=False)
    exp_year = Column(Integer, nullable=False)

    status = Column(String(20), default=CardStatus.ACTIVE, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    account = relationship("Account", back_populates="credit_cards")

    def __repr__(self) -> str:
        """String representation of CreditCard."""
        return f"<CreditCard(id={self.id}, last4={self.last4}, brand={self.brand}, status={self.status})>"

    @property
    def is_active(self) -> bool:
        """Check if card is active."""
        return self.status == CardStatus.ACTIVE

    @property
    def is_expired(self) -> bool:
        """Check if card is expired."""
        from datetime import datetime

        current_year = datetime.now(UTC).year
        current_month = datetime.now(UTC).month

        return self.exp_year < current_year or (self.exp_year == current_year and self.exp_month < current_month) 

    def cancel(self) -> None:
        """Cancel the card."""
        self.status = CardStatus.CANCELLED  

    def mark_expired(self) -> None:
        """Mark the card as expired."""
        self.status = CardStatus.EXPIRED 

    @classmethod
    def validate_expiry(cls, exp_month: int, exp_year: int) -> bool:
        """Validate that expiry date is in the future."""
        from datetime import datetime

        current_year = datetime.now(UTC).year
        current_month = datetime.now(UTC).month

        return not (exp_year < current_year or (exp_year == current_year and exp_month < current_month))

    @classmethod
    def detect_brand(cls, pan: str) -> str:
        """Detect card brand from PAN prefix.

        All PANs must be exactly 16 digits.
        """
        clean_pan = pan.replace(" ", "")

        if not clean_pan.isdigit() or len(clean_pan) != 16:
            return CardBrand.UNKNOWN

        if clean_pan.startswith(("34", "37")):
            return CardBrand.AMERICAN_EXPRESS

        if clean_pan.startswith("4"):
            return CardBrand.VISA

        if clean_pan.startswith(("51", "52", "53", "54", "55")) or (clean_pan.startswith("2221") and "2221" <= clean_pan[:4] <= "2720"):
            return CardBrand.MASTERCARD

        if (
            clean_pan.startswith("6011")
            or (clean_pan.startswith("622") and "622126" <= clean_pan[:6] <= "622925")
            or (clean_pan.startswith(("644", "645", "646", "647", "648", "649")))
            or clean_pan.startswith("65")
        ):
            return CardBrand.DISCOVER

        return CardBrand.UNKNOWN

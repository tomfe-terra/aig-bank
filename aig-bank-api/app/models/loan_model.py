"""Loan model for banking operations."""

from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from ..core.enums import LoanStatus
from ..utils.datetime_helpers import format_datetime
from ..utils.id_generator import generate_uuid_str

if TYPE_CHECKING:
    from ..core.db import Base
else:
    from ..core.db import Base


class Loan(Base):
    """Loan model."""

    __tablename__ = "loans"

    id = Column(String(36), primary_key=True, default=generate_uuid_str, index=True)

    account_id = Column(String(36), ForeignKey("accounts.id"), nullable=False, index=True)

    principal_cents = Column(Integer, nullable=False)

    repayment_cycles = Column(Integer, nullable=False)

    paid_amount_cents = Column(Integer, default=0, nullable=False)
    next_repayment_at = Column(DateTime(timezone=True), nullable=True)
    last_repayment_at = Column(DateTime(timezone=True), nullable=True)

    status = Column(String(20), default=LoanStatus.PENDING, nullable=False)

    approved_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    version = Column(Integer, default=1, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    account = relationship("Account", back_populates="loans")
    approver = relationship("User", foreign_keys=[approved_by])

    def __repr__(self) -> str:
        """String representation of Loan."""
        return f"<Loan(id={self.id}, principal={self.principal_cents}, status={self.status})>"

    @property
    def principal_dollars(self) -> float:
        """Get principal in dollars for display purposes."""
        return float(self.principal_cents) / 100.0

    @property
    def installment_amount_cents(self) -> int:
        """Calculate installment amount per cycle (rounded UP)."""
        return (int(self.principal_cents) + int(self.repayment_cycles) - 1) // int(self.repayment_cycles)

    @property
    def remaining_balance_cents(self) -> int:
        """Calculate remaining balance to be repaid."""
        return int(self.principal_cents) - int(self.paid_amount_cents)

    @property
    def is_fully_paid(self) -> bool:
        """Check if loan is fully repaid."""
        return int(self.paid_amount_cents) >= int(self.principal_cents)

    def approve(self, banker_id: str) -> None:
        """Approve the loan."""
        self.status = LoanStatus.APPROVED  # type: ignore[assignment]
        self.approved_by = banker_id  # type: ignore[assignment]

    def reject(self, banker_id: str) -> None:
        """Reject the loan."""
        self.status = LoanStatus.REJECTED  # type: ignore[assignment]
        self.approved_by = banker_id  # type: ignore[assignment]

    def activate(self) -> None:
        """Activate the loan (after disbursement)."""
        self.status = LoanStatus.ACTIVE  # type: ignore[assignment]

    def close(self) -> None:
        """Close the loan (after full repayment)."""
        self.status = LoanStatus.CLOSED  # type: ignore[assignment]

    def to_dict(self) -> dict[str, str | int | float | None]:
        """Convert loan to dictionary for serialization."""
        return {
            "id": str(self.id),
            "account_id": str(self.account_id),
            "principal_cents": self.principal_cents,  # type: ignore
            "principal_dollars": self.principal_dollars,  # type: ignore
            "repayment_cycles": self.repayment_cycles,  # type: ignore
            "installment_amount_cents": self.installment_amount_cents,  # type: ignore
            "paid_amount_cents": self.paid_amount_cents,  # type: ignore
            "remaining_balance_cents": self.remaining_balance_cents,  # type: ignore
            "status": self.status,  # type: ignore
            "approved_by": str(self.approved_by) if self.approved_by else None,
            "next_repayment_at": format_datetime(self.next_repayment_at),  # type: ignore
            "last_repayment_at": format_datetime(self.last_repayment_at),  # type: ignore
            "version": self.version,  # type: ignore
            "created_at": format_datetime(self.created_at),  # type: ignore
            "updated_at": format_datetime(self.updated_at),  # type: ignore
        }

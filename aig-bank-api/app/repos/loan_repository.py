"""Loan repository for database operations."""

from collections.abc import Sequence
from datetime import UTC

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.enums import LoanStatus
from ..core.errors import InvalidDataError, LoanNotApprovedError, ResourceNotFoundError
from ..models.loan_model import Loan


class LoanRepository:
    """Repository for Loan model operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(self, account_id: str, principal_cents: int, repayment_cycles: int) -> Loan:
        """Create a new loan (non-profit bank: no interest, hourly repayments)."""
        loan = Loan(
            account_id=account_id,
            principal_cents=principal_cents,
            repayment_cycles=repayment_cycles,
            status=LoanStatus.PENDING,
            paid_amount_cents=0,
        )

        self.session.add(loan)
        await self.session.flush()
        await self.session.refresh(loan)

        return loan

    async def get_by_id(self, loan_id: str) -> Loan | None:
        """Get loan by ID."""
        stmt = select(Loan).where(Loan.id == loan_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_with_account(self, loan_id: str) -> Loan | None:
        """Get loan by ID with account data loaded."""
        stmt = select(Loan).options(selectinload(Loan.account)).where(Loan.id == loan_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_account_id(self, account_id: str) -> Sequence[Loan]:
        """Get all loans for an account."""
        stmt = select(Loan).where(Loan.account_id == account_id).order_by(Loan.created_at.desc())

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_pending_loans(self) -> Sequence[Loan]:
        """Get all pending loans for approval."""
        stmt = select(Loan).where(Loan.status == LoanStatus.PENDING).order_by(Loan.created_at.asc())

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def approve_loan(self, loan_id: str, banker_id: str) -> Loan:
        """Approve a loan."""
        loan = await self.get_by_id(loan_id)
        if not loan:
            raise ResourceNotFoundError("Loan", f"Loan {loan_id} not found")

        if loan.status != LoanStatus.PENDING:
            raise InvalidDataError("status", loan.status.value, f"Loan {loan_id} is not pending approval")

        loan.approve(banker_id)
        self.session.add(loan)
        await self.session.flush()
        await self.session.refresh(loan)

        return loan

    async def reject_loan(self, loan_id: str, banker_id: str) -> Loan:
        """Reject a loan."""
        loan = await self.get_by_id(loan_id)
        if not loan:
            raise ResourceNotFoundError("Loan", f"Loan {loan_id} not found")

        if loan.status != LoanStatus.PENDING:
            raise InvalidDataError("status", loan.status.value, f"Loan {loan_id} is not pending approval")

        loan.reject(banker_id)
        self.session.add(loan)
        await self.session.flush()
        await self.session.refresh(loan)

        return loan

    async def activate_loan(self, loan_id: str, next_repayment_at) -> Loan:
        """Activate a loan after disbursement and set first repayment time."""
        loan = await self.get_by_id(loan_id)
        if not loan:
            raise ResourceNotFoundError("Loan", f"Loan {loan_id} not found")

        if loan.status != LoanStatus.APPROVED:
            raise LoanNotApprovedError(str(loan_id))

        loan.activate()
        loan.next_repayment_at = next_repayment_at  # type: ignore[assignment]
        self.session.add(loan)
        await self.session.flush()
        await self.session.refresh(loan)

        return loan

    async def close_loan(self, loan_id: str) -> Loan:
        """Close a loan after full repayment."""
        loan = await self.get_by_id(loan_id)
        if not loan:
            raise ResourceNotFoundError("Loan", f"Loan {loan_id} not found")

        if loan.status != LoanStatus.ACTIVE:
            raise InvalidDataError(
                "status",
                loan.status.value,
                f"Loan {loan_id} must be active before closing",
            )

        loan.close()
        loan.next_repayment_at = None  # type: ignore[assignment]
        self.session.add(loan)
        await self.session.flush()
        await self.session.refresh(loan)

        return loan

    async def update_repayment_tracking(
        self,
        loan_id: str,
        paid_amount_cents: int,
        next_repayment_at,
        last_repayment_at,
    ) -> Loan:
        """Update loan repayment tracking after a payment."""
        loan = await self.get_by_id(loan_id)
        if not loan:
            raise ResourceNotFoundError("Loan", f"Loan {loan_id} not found")

        loan.paid_amount_cents = paid_amount_cents  # type: ignore[assignment]
        loan.next_repayment_at = next_repayment_at  # type: ignore[assignment]
        loan.last_repayment_at = last_repayment_at  # type: ignore[assignment]

        self.session.add(loan)
        await self.session.flush()
        await self.session.refresh(loan)

        return loan

    async def get_due_loans(self):
        """Get all active loans where next repayment is due."""
        from datetime import datetime

        now = datetime.now(UTC)
        stmt = (
            select(Loan)
            .options(selectinload(Loan.account))
            .where(Loan.status == LoanStatus.ACTIVE, Loan.next_repayment_at <= now)
            .order_by(Loan.next_repayment_at.asc())
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

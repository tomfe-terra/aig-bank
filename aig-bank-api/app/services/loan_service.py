"""Loan service for loan business logic operations."""

from datetime import UTC
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.enums import LoanStatus, TransactionType
from ..core.errors import (
    ForbiddenError,
    InvalidAmountError,
    InvalidDataError,
    LoanNotApprovedError,
    ResourceNotFoundError,
)
from ..models.transaction_model import Transaction
from ..repos.account_repository import AccountRepository
from ..repos.loan_repository import LoanRepository
from ..repos.transaction_repository import TransactionRepository
from ..repos.user_repository import UserRepository
from ..schemas.loan_schemas import LoanRead
from ..schemas.transaction_schemas import RelatedAccountInfo, TransactionRead
from .base_service import BaseService

logger = logging.getLogger(__name__)


class LoanService(BaseService):
    """Service for loan-related business operations."""

    def __init__(self, session: AsyncSession):
        """Initialize service with database session and repositories."""
        super().__init__(session)
        self.repository = LoanRepository(session)
        self.account_repository = AccountRepository(session)
        self.transaction_repository = TransactionRepository(session)
        self.user_repository = UserRepository(session)

    async def _enrich_transaction_with_related_account(self, transaction: Transaction) -> TransactionRead:
        """Enrich transaction with related account information.

        Args:
            transaction: Transaction model instance

        Returns:
            TransactionRead: Enriched transaction with related account info
        """
        tx_dict = {
            "id": transaction.id,
            "account_id": transaction.account_id,
            "type": transaction.type,
            "amount_cents": transaction.amount_cents,
            "amount_dollars": transaction.amount_cents / 100.0,
            "idempotency_key": transaction.idempotency_key,
            "meta": transaction.meta,
            "created_at": transaction.created_at,
            "related_account_id": None,
        }

        if transaction.related_account_id:
            related_account = await self.account_repository.get_by_id(str(transaction.related_account_id))
            if related_account:
                if related_account.user_id:
                    user = await self.user_repository.get_by_id(str(related_account.user_id))
                    username = user.username if user else "Unknown"
                else:
                    username = "AIG Bank"

                tx_dict["related_account_id"] = RelatedAccountInfo(
                    account_number=related_account.number,
                    username=username,
                )

        return TransactionRead(**tx_dict)

    async def request_loan(
        self,
        account_id: str,
        principal_cents: int,
        repayment_cycles: int,
        user_id: str,
    ) -> LoanRead:
        """Request a new loan for an account (non-profit bank: no interest, hourly repayments)."""
        account = await self.account_repository.get_by_id(account_id)
        if not account:
            raise ResourceNotFoundError("Account", f"Account {account_id} not found")

        if account.user_id != user_id:
            raise ForbiddenError("Access denied to this account")

        if principal_cents <= 0:
            raise InvalidAmountError(principal_cents, "Loan principal must be positive")

        if repayment_cycles <= 0 or repayment_cycles > 8760:
            raise InvalidDataError(
                "repayment_cycles",
                str(repayment_cycles),
                "Repayment cycles must be between 1 and 8760 hours (1 year)",
            )

        loan = await self.repository.create(
            account_id=account_id,
            principal_cents=principal_cents,
            repayment_cycles=repayment_cycles,
        )

        logger.info(
            f"Loan requested: {principal_cents} cents for {repayment_cycles} cycles",
            extra={
                "loan_id": str(loan.id),
                "account_id": str(account_id),
                "user_id": str(user_id),
                "principal_cents": principal_cents,
                "repayment_cycles": repayment_cycles,
                "action": "loan_request",
            },
        )

        return LoanRead.model_validate(loan, from_attributes=True)

    async def get_loan(self, loan_id: str, user_id: str) -> LoanRead:
        """Get a loan by ID, verifying ownership."""
        loan = await self.repository.get_by_id_with_account(loan_id)
        if not loan:
            raise ResourceNotFoundError("Loan", f"Loan {loan_id} not found")

        if loan.account.user_id != user_id:
            raise ResourceNotFoundError("Loan", f"Loan {loan_id} not found")

        return LoanRead.model_validate(loan, from_attributes=True)

    async def list_user_loans(self, user_id: str) -> list[LoanRead]:
        """List all loans for a user."""
        account = await self.account_repository.get_by_user_id(user_id)
        if not account:
            return []

        account_loans = await self.repository.get_by_account_id(str(account.id))
        return [LoanRead.model_validate(loan, from_attributes=True) for loan in account_loans]

    async def approve_loan(self, loan_id: str, banker_id: str) -> LoanRead:
        """Approve a loan (banker operation)."""
        loan = await self.repository.approve_loan(loan_id, banker_id)

        logger.info(
            f"Loan approved: {loan.principal_cents} cents for loan {loan_id}",
            extra={
                "loan_id": str(loan_id),
                "banker_id": str(banker_id),
                "principal_cents": loan.principal_cents,
                "action": "loan_decision",
            },
        )

        return LoanRead.model_validate(loan, from_attributes=True)

    async def reject_loan(self, loan_id: str, banker_id: str) -> LoanRead:
        """Reject a loan (banker operation)."""
        loan = await self.repository.reject_loan(loan_id, banker_id)

        logger.info(
            f"Loan rejected: {loan.principal_cents} cents for loan {loan_id}",
            extra={
                "loan_id": str(loan_id),
                "banker_id": str(banker_id),
                "principal_cents": loan.principal_cents,
                "action": "loan_rejection",
            },
        )

        return LoanRead.model_validate(loan, from_attributes=True)

    async def disburse_loan(self, loan_id: str, banker_id: str) -> tuple[LoanRead, TransactionRead]:
        """Disburse approved loan funds from bank capital to user account."""
        from datetime import datetime, timedelta

        loan = await self.repository.get_by_id_with_account(loan_id)
        if not loan:
            raise ResourceNotFoundError("Loan", f"Loan {loan_id} not found")

        if loan.status != LoanStatus.APPROVED:
            raise LoanNotApprovedError(str(loan_id))

        if loan.approved_by != banker_id:
            raise ForbiddenError("Only the approving banker can disburse the loan")

        bank_account = await self.account_repository.get_bank_capital_account()
        if not bank_account:
            raise ResourceNotFoundError("Account", "Bank capital account not found")

        user_account = loan.account

        await self.account_repository.update_balance(
            account_id=str(bank_account.id),
            new_balance=int(bank_account.balance_cents) - int(loan.principal_cents),
        )

        await self.account_repository.update_balance(
            account_id=str(user_account.id),
            new_balance=int(user_account.balance_cents) + int(loan.principal_cents),
        )

        interval_seconds = settings.repayment_check_interval_seconds
        next_repayment_at = datetime.now(UTC) + timedelta(seconds=interval_seconds)

        loan = await self.repository.activate_loan(loan_id, next_repayment_at)

        user_tx = await self.transaction_repository.create(
            account_id=str(user_account.id),
            transaction_type=TransactionType.LOAN_DISBURSEMENT,
            amount_cents=int(loan.principal_cents),
            idempotency_key=f"loan_disbursement_{loan_id}",
            related_account_id=str(bank_account.id),
            meta={"loan_id": str(loan_id)},
        )

        await self.transaction_repository.create(
            account_id=str(bank_account.id),
            transaction_type=TransactionType.LOAN_DISBURSEMENT,
            amount_cents=-int(loan.principal_cents),
            idempotency_key=f"loan_disbursement_bank_{loan_id}",
            related_account_id=str(user_account.id),
            meta={"loan_id": str(loan_id)},
        )

        logger.info(
            f"Loan disbursed: ${loan.principal_cents / 100:.2f} from bank to user account",
            extra={
                "loan_id": str(loan_id),
                "banker_id": str(banker_id),
                "user_account_id": str(user_account.id),
                "bank_account_id": str(bank_account.id),
                "amount_cents": loan.principal_cents,
                "next_repayment_at": next_repayment_at.isoformat(),
                "action": "loan_disbursement",
            },
        )

        return (
            LoanRead.model_validate(loan, from_attributes=True),
            await self._enrich_transaction_with_related_account(user_tx),
        )

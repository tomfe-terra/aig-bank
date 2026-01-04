"""Loan repayment service for automatic hourly repayments."""

from datetime import UTC, datetime, timedelta
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.enums import TransactionType
from ..core.errors import ResourceNotFoundError
from ..repos.account_repository import AccountRepository
from ..repos.loan_repository import LoanRepository
from ..repos.transaction_repository import TransactionRepository

logger = logging.getLogger(__name__)


class LoanRepaymentService:
    """Service for processing automatic loan repayments."""

    def __init__(self, session: AsyncSession):
        """Initialize service with database session and repositories."""
        self.session = session
        self.loan_repository = LoanRepository(session)
        self.account_repository = AccountRepository(session)
        self.transaction_repository = TransactionRepository(session)

    async def process_due_repayments(self) -> dict[str, int]:
        """Process all loans with due repayments.

        Returns:
            dict with processed, failed, and total_due counts
        """
        due_loans = await self.loan_repository.get_due_loans()

        processed = 0
        failed = 0

        for loan in due_loans:
            try:
                await self._process_single_repayment(loan)
                processed += 1
            except Exception as e:
                logger.error(
                    f"Failed to process repayment for loan {loan.id}: {e}",
                    extra={
                        "loan_id": str(loan.id),
                        "error": str(e),
                        "action": "repayment_failed",
                    },
                    exc_info=True,
                )
                failed += 1

        await self.session.commit()

        logger.info(
            f"Repayment processing complete: {processed} processed, {failed} failed, {len(due_loans)} total due",
            extra={
                "processed": processed,
                "failed": failed,
                "total_due": len(due_loans),
                "action": "repayment_batch_complete",
            },
        )

        return {
            "processed": processed,
            "failed": failed,
            "total_due": len(due_loans),
        }

    async def _process_single_repayment(self, loan) -> None:
        """Process a single loan repayment.

        Args:
            loan: Loan model instance with account loaded
        """
        installment = (int(loan.principal_cents) + int(loan.repayment_cycles) - 1) // int(loan.repayment_cycles)

        remaining = int(loan.principal_cents) - int(loan.paid_amount_cents)

        payment_amount = min(installment, remaining)

        user_account = loan.account
        if not user_account:
            raise ResourceNotFoundError("Account", f"Account {loan.account_id} not found")

        bank_account = await self.account_repository.get_bank_capital_account()
        if not bank_account:
            raise ResourceNotFoundError("Account", "Bank capital account not found")

        await self.account_repository.update_balance(
            account_id=str(user_account.id),
            new_balance=int(user_account.balance_cents) - payment_amount,
        )

        await self.account_repository.update_balance(
            account_id=str(bank_account.id),
            new_balance=int(bank_account.balance_cents) + payment_amount,
        )

        await self.transaction_repository.create(
            account_id=str(user_account.id),
            transaction_type=TransactionType.LOAN_REPAYMENT,
            amount_cents=-payment_amount,
            idempotency_key=f"loan_repayment_{loan.id}_{datetime.now(UTC).timestamp()}",
            related_account_id=str(bank_account.id),
            meta={
                "loan_id": str(loan.id),
                "payment_amount": payment_amount,
                "remaining_before": remaining,
            },
        )

        await self.transaction_repository.create(
            account_id=str(bank_account.id),
            transaction_type=TransactionType.LOAN_REPAYMENT,
            amount_cents=payment_amount,
            idempotency_key=f"loan_repayment_bank_{loan.id}_{datetime.now(UTC).timestamp()}",
            related_account_id=str(user_account.id),
            meta={"loan_id": str(loan.id)},
        )

        new_paid_amount = int(loan.paid_amount_cents) + payment_amount

        if new_paid_amount >= int(loan.principal_cents):
            await self.loan_repository.update_repayment_tracking(
                loan_id=str(loan.id),
                paid_amount_cents=new_paid_amount,
                next_repayment_at=None,
                last_repayment_at=datetime.now(UTC),
            )
            await self.loan_repository.close_loan(str(loan.id))
            logger.info(
                f"Loan {loan.id} fully repaid and closed: ${loan.principal_cents / 100:.2f}",
                extra={
                    "loan_id": str(loan.id),
                    "principal_cents": loan.principal_cents,
                    "total_paid": new_paid_amount,
                    "action": "loan_closed",
                },
            )
        else:
            interval_seconds = settings.repayment_check_interval_seconds
            next_repayment = datetime.now(UTC) + timedelta(seconds=interval_seconds)
            await self.loan_repository.update_repayment_tracking(
                loan_id=str(loan.id),
                paid_amount_cents=new_paid_amount,
                next_repayment_at=next_repayment,
                last_repayment_at=datetime.now(UTC),
            )
            logger.info(
                f"Loan {loan.id} repayment processed: ${payment_amount / 100:.2f} "
                f"(${new_paid_amount / 100:.2f} / ${loan.principal_cents / 100:.2f})",
                extra={
                    "loan_id": str(loan.id),
                    "payment_amount": payment_amount,
                    "paid_amount_cents": new_paid_amount,
                    "principal_cents": loan.principal_cents,
                    "remaining_cents": loan.principal_cents - new_paid_amount,
                    "next_repayment_at": next_repayment.isoformat(),
                    "action": "loan_repayment_processed",
                },
            )

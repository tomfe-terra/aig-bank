"""Savings plan service for business logic operations."""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.constants import BANK_CAPITAL_ACCOUNT_NUMBER, SAVINGS_PLANS
from ..core.enums import TransactionType
from ..core.errors import InsufficientFundsError, ResourceNotFoundError
from ..repos.account_repository import AccountRepository
from ..repos.transaction_repository import TransactionRepository
from ..schemas.savings_schemas import (
    SavingsPlanDepositRead,
    SavingsPlanInfo,
    SavingsPlanList,
)
from .base_service import BaseService

logger = logging.getLogger(__name__)


class SavingsService(BaseService):
    """Service for savings plan operations."""

    def __init__(self, session: AsyncSession):
        """Initialize service with database session."""
        super().__init__(session)
        self.account_repository = AccountRepository(session)
        self.transaction_repository = TransactionRepository(session)

    def get_available_plans(self) -> SavingsPlanList:
        """Get list of available savings plans.

        Returns:
            SavingsPlanList: List of available savings plans
        """
        plans = [
            SavingsPlanInfo(
                id=plan["id"],
                name=plan["name"],
                display_name=plan["display_name"],
                description=plan["description"],
                tagline=plan["tagline"],
            )
            for plan in SAVINGS_PLANS
        ]
        return SavingsPlanList(plans=plans)

    async def open_savings_plan(
        self,
        user_id: str,
        plan_id: int,
        amount_cents: int,
    ) -> SavingsPlanDepositRead:
        """Open a savings plan.

        Args:
            user_id: User ID opening the savings plan
            plan_id: ID of the savings plan
            amount_cents: Amount to deposit in cents

        Returns:
            SavingsPlanDepositRead: Savings plan result with message

        Raises:
            InputValidationError: If plan ID is invalid
            InsufficientFundsError: If user has insufficient funds
        """
        plan = self._get_plan_by_id(plan_id)

        logger.info(
            f"Processing savings plan deposit for user {user_id}: {plan['name']} (ID: {plan_id}) - {amount_cents} cents",
            extra={
                "user_id": user_id,
                "plan_id": plan_id,
                "plan_name": plan["name"],
                "amount_cents": amount_cents,
                "action": "savings_plan_deposit",
            },
        )

        user_account = await self.account_repository.get_by_user_id(user_id)

        if user_account.balance_cents < amount_cents:
            raise InsufficientFundsError(
                available=user_account.balance_cents,
                required=amount_cents,
                details=f"Insufficient funds in account {user_account.number}",
            )

        bank_account = await self.account_repository.get_by_number(BANK_CAPITAL_ACCOUNT_NUMBER)
        if not bank_account:
            raise ResourceNotFoundError("Account", f"Bank capital account {BANK_CAPITAL_ACCOUNT_NUMBER} not found")

        user_account = await self.account_repository.update_balance(
            account_id=str(user_account.id),
            new_balance=int(user_account.balance_cents) - amount_cents,
        )

        bank_account = await self.account_repository.update_balance(
            account_id=str(bank_account.id),
            new_balance=int(bank_account.balance_cents) + amount_cents,
        )

        idempotency_key = f"savings_plan_{uuid.uuid4()}"
        meta = {
            "savings_plan_id": plan_id,
            "savings_plan_name": plan["name"],
            "transaction_type": "savings_plan",
            "plan_display_name": plan["display_name"],
            "amount_cents": amount_cents,
            "from_account_number": user_account.number,
            "to_account_number": BANK_CAPITAL_ACCOUNT_NUMBER,
        }

        transfer_out_tx, _transfer_in_tx = await self.transaction_repository.create_double_entry(
            source_account_id=str(user_account.id),
            dest_account_id=str(bank_account.id),
            source_transaction_type=TransactionType.TRANSFER_OUT.value,
            dest_transaction_type=TransactionType.TRANSFER_IN.value,
            amount_cents=amount_cents,
            idempotency_key=idempotency_key,
            meta=meta,
        )

        logger.info(
            f"Savings plan deposit completed for user {user_id}: {plan['name']} (ID: {plan_id})",
            extra={
                "user_id": user_id,
                "plan_id": plan_id,
                "plan_name": plan["name"],
                "amount_cents": amount_cents,
                "transaction_id": str(transfer_out_tx.id),
                "action": "savings_plan_deposit_completed",
            },
        )

        return SavingsPlanDepositRead(
            plan_id=plan_id,
            plan_name=plan["name"],
            amount_cents=amount_cents,
            message=plan["message"],
        )

    def _get_plan_by_id(self, plan_id: int) -> dict | None:
        """Get savings plan by ID.

        Args:
            plan_id: ID of the plan to retrieve

        Returns:
            dict | None: Plan details or None if not found
        """
        for plan in SAVINGS_PLANS:
            if plan["id"] == plan_id:
                return plan
        return None

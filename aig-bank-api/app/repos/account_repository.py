"""Account repository for database operations."""

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.errors import (
    ResourceNotFoundError,
)
from ..models.account_model import Account


class AccountRepository:
    """Repository for Account model operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(self, user_id: str, account_number: str) -> Account:
        """Create a new account for a user. Only USD currency is supported."""
        account = Account(
            user_id=user_id,
            number=account_number,
            balance_cents=0,
        )

        self.session.add(account)
        await self.session.flush()

        await self.session.refresh(account)

        return account

    async def get_by_id(self, account_id: str) -> Account | None:
        """Get account by ID."""
        stmt = select(Account).where(Account.id == account_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_number(self, account_number: str) -> Account | None:
        """Get account by account number."""
        stmt = select(Account).where(Account.number == account_number)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_bank_capital_account(self) -> Account | None:
        """Get the bank capital account by well-known account number."""
        from ..core.constants import BANK_CAPITAL_ACCOUNT_NUMBER

        return await self.get_by_number(BANK_CAPITAL_ACCOUNT_NUMBER)

    async def get_by_user_id(self, user_id: str) -> Account | None:
        """Get the account for a user (one account per user enforced by unique constraint)."""
        stmt = select(Account).where(Account.user_id == user_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_balance(self, account_id: str, new_balance: int) -> Account:
        """Update account balance (allows negative balances for overdraft)."""
        account = await self.get_by_id(account_id)
        if not account:
            raise ResourceNotFoundError("Account", f"Account {account_id} not found")

        account.balance_cents = new_balance  # type: ignore[assignment]

        self.session.add(account)
        await self.session.flush()
        await self.session.refresh(account)

        return account

    async def list_accounts(self, limit: int = 50, offset: int = 0, user_id: str | None = None) -> tuple[Sequence[Account], int]:
        """List accounts with optional user filtering."""
        count_stmt = select(func.count()).select_from(Account)

        if user_id:
            count_stmt = count_stmt.where(Account.user_id == user_id)

        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0

        stmt = select(Account)

        if user_id:
            stmt = stmt.where(Account.user_id == user_id)

        stmt = stmt.order_by(Account.created_at.desc()).limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        accounts = result.scalars().all()

        return accounts, total

    async def account_number_exists(self, account_number: str) -> bool:
        """Check if account number already exists."""
        stmt = select(Account).where(Account.number == account_number)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def generate_unique_account_number(self) -> str:
        """Generate a unique account number."""
        while True:
            account_number = Account.generate_account_number()
            if not await self.account_number_exists(account_number):
                return account_number

"""Transaction repository for database operations."""

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.transaction_model import Transaction
from ..schemas.core import (
    CursorPaginationParams,
    PaginationParams,
    TransactionFilterParams,
)


class TransactionRepository:
    """Repository for Transaction model operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(
        self,
        account_id: str,
        transaction_type: str,
        amount_cents: int,
        idempotency_key: str,
        related_account_id: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> Transaction:
        """Create a new transaction."""
        transaction = Transaction(
            account_id=account_id,
            type=transaction_type,
            amount_cents=amount_cents,
            related_account_id=related_account_id,
            idempotency_key=idempotency_key,
            meta=meta,
        )

        self.session.add(transaction)
        await self.session.flush()

        await self.session.refresh(transaction)

        return transaction

    async def create_double_entry(
        self,
        source_account_id: str,
        dest_account_id: str,
        source_transaction_type: str,
        dest_transaction_type: str,
        amount_cents: int,
        idempotency_key: str,
        meta: dict[str, Any] | None = None,
    ) -> tuple[Transaction, Transaction]:
        """Create a double-entry transaction pair (debit and credit).

        Args:
            source_account_id: Account to debit from
            dest_account_id: Account to credit to
            source_transaction_type: Transaction type for source (e.g., CARD_PAYMENT)
            dest_transaction_type: Transaction type for destination (e.g., TRANSFER_IN)
            amount_cents: Amount to transfer (positive value)
            idempotency_key: Base idempotency key (suffixed with :out and :in for uniqueness)
            meta: Optional metadata to attach to both transactions

        Returns:
            tuple[Transaction, Transaction]: (source_transaction, dest_transaction)
        """
        source_tx = Transaction(
            account_id=source_account_id,
            type=source_transaction_type,
            amount_cents=-amount_cents,
            related_account_id=dest_account_id,
            idempotency_key=f"{idempotency_key}:out",
            meta=meta,
        )

        dest_tx = Transaction(
            account_id=dest_account_id,
            type=dest_transaction_type,
            amount_cents=amount_cents,
            related_account_id=source_account_id,
            idempotency_key=f"{idempotency_key}:in",
            meta=meta,
        )

        self.session.add(source_tx)
        self.session.add(dest_tx)
        await self.session.flush()

        await self.session.refresh(source_tx)
        await self.session.refresh(dest_tx)

        return source_tx, dest_tx

    async def get_by_id(self, transaction_id: str) -> Transaction | None:
        """Get transaction by ID."""
        stmt = select(Transaction).where(Transaction.id == transaction_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_with_accounts(self, transaction_id: str) -> Transaction | None:
        """Get transaction by ID with account data loaded."""
        stmt = (
            select(Transaction)
            .options(selectinload(Transaction.account))
            .options(selectinload(Transaction.related_account))
            .where(Transaction.id == transaction_id)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(self, idempotency_key: str) -> Transaction | None:
        """Get transaction by idempotency key."""
        stmt = select(Transaction).where(Transaction.idempotency_key == idempotency_key)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_account_id(
        self,
        account_id: str,
        limit: int = 50,
        offset: int = 0,
        transaction_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> tuple[Sequence[Transaction], int]:
        """Get transactions for an account with filtering and pagination."""
        stmt = select(Transaction).where(Transaction.account_id == account_id)

        if transaction_type:
            stmt = stmt.where(Transaction.type == transaction_type)

        if start_date:
            stmt = stmt.where(Transaction.created_at >= start_date)

        if end_date:
            stmt = stmt.where(Transaction.created_at <= end_date)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0

        stmt = stmt.order_by(Transaction.created_at.desc()).limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        transactions = result.scalars().all()

        return transactions, total

    async def get_transactions_with_cursor(
        self,
        account_id: str | None = None,
        pagination: CursorPaginationParams | None = None,
        transaction_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> tuple[Sequence[Transaction], str | None]:
        """Get transactions using cursor-based pagination."""
        if pagination is None:
            pagination = CursorPaginationParams()

        stmt = select(Transaction)

        filter_conditions = []

        if account_id:
            filter_conditions.append(Transaction.account_id == account_id)

        if transaction_type:
            filter_conditions.append(Transaction.type == transaction_type)

        if start_date:
            filter_conditions.append(Transaction.created_at >= start_date)

        if end_date:
            filter_conditions.append(Transaction.created_at <= end_date)

        if filter_conditions:
            stmt = stmt.where(and_(*filter_conditions))

        if pagination.cursor:
            try:
                cursor_parts = pagination.cursor.split(":", 1)
                if len(cursor_parts) == 2:
                    cursor_datetime_str, cursor_id_str = cursor_parts
                    cursor_datetime = datetime.fromisoformat(cursor_datetime_str.replace("Z", "+00:00"))

                    cursor_condition = and_(
                        Transaction.created_at < cursor_datetime,
                        Transaction.id != cursor_id_str,
                    )
                    cursor_condition = Transaction.created_at > cursor_datetime
                    id_condition = and_(
                        Transaction.created_at == cursor_datetime,
                        Transaction.id > cursor_id_str,
                    )
                    stmt = stmt.where(cursor_condition | id_condition)
            except (ValueError, TypeError):
                pass

        stmt = stmt.order_by(Transaction.created_at.desc(), Transaction.id.desc())

        stmt = stmt.limit(pagination.limit + 1)

        result = await self.session.execute(stmt)
        transactions = result.scalars().all()

        has_next = len(transactions) > pagination.limit
        if has_next:
            transactions = transactions[: pagination.limit]

        next_cursor = None
        if has_next and transactions:
            last_tx = transactions[-1]
            next_cursor = f"{last_tx.created_at.isoformat()}:{last_tx.id}"

        return transactions, next_cursor

    async def list_transactions(
        self,
        pagination: PaginationParams,
        filters: TransactionFilterParams | None = None,
    ) -> tuple[Sequence[Transaction], int]:
        """List transactions with advanced filtering and pagination."""
        stmt = select(Transaction)

        filter_conditions = []

        if filters and filters.account_id:
            filter_conditions.append(Transaction.account_id == filters.account_id)

        if filters and filters.transaction_type:
            filter_conditions.append(Transaction.type == filters.transaction_type)

        if filters and filters.start_date:
            filter_conditions.append(Transaction.created_at >= filters.start_date)

        if filters and filters.end_date:
            filter_conditions.append(Transaction.created_at <= filters.end_date)

        if filters and filters.min_amount is not None:
            filter_conditions.append(Transaction.amount_cents >= filters.min_amount)

        if filters and filters.max_amount is not None:
            filter_conditions.append(Transaction.amount_cents <= filters.max_amount)

        if filter_conditions:
            stmt = stmt.where(and_(*filter_conditions))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0

        stmt = stmt.order_by(Transaction.created_at.desc()).limit(pagination.limit).offset(pagination.offset)

        result = await self.session.execute(stmt)
        transactions = result.scalars().all()

        return transactions, total

    async def get_transaction_summary(
        self,
        account_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Get transaction summary for an account."""
        base_conditions = [Transaction.account_id == account_id]

        if start_date:
            base_conditions.append(Transaction.created_at >= start_date)

        if end_date:
            base_conditions.append(Transaction.created_at <= end_date)

        type_totals = await self.session.execute(
            select(
                Transaction.type,
                func.sum(Transaction.amount_cents).label("total_cents"),
                func.count(Transaction.id).label("count"),
            )
            .where(and_(*base_conditions))
            .group_by(Transaction.type)
        )

        overall_totals = await self.session.execute(
            select(
                func.sum(Transaction.amount_cents).label("total_cents"),
                func.count(Transaction.id).label("total_count"),
                func.min(Transaction.created_at).label("earliest_date"),
                func.max(Transaction.created_at).label("latest_date"),
            ).where(and_(*base_conditions))
        )

        overall = overall_totals.first()

        return {
            "by_type": [
                {
                    "type": row.type,
                    "total_cents": row.total_cents or 0,
                    "total_dollars": (row.total_cents or 0) / 100.0,
                    "count": row.count,
                }
                for row in type_totals
            ],
            "overall": {
                "total_cents": overall.total_cents or 0 if overall else 0,
                "total_dollars": (overall.total_cents or 0) / 100.0 if overall else 0.0,
                "total_count": overall.total_count if overall else 0,
                "earliest_date": overall.earliest_date if overall else None,
                "latest_date": overall.latest_date if overall else None,
            },
        }

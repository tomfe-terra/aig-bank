"""Transaction service for business logic operations."""

from datetime import datetime
import logging
from typing import Any
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.enums import TransactionType
from ..core.errors import (
    DuplicateIdempotencyKeyError,
    InsufficientFundsError,
    ResourceNotFoundError,
)
from ..models.transaction_model import Transaction
from ..repos.account_repository import AccountRepository
from ..repos.transaction_repository import TransactionRepository
from ..repos.user_repository import UserRepository
from ..schemas.account_schemas import AccountRead
from ..schemas.core import (
    CursorPaginationParams,
    PaginationParams,
    TransactionFilterParams,
)
from ..schemas.transaction_schemas import (
    AccountTransactionList,
    CardPaymentCreate,
    RelatedAccountInfo,
    TransactionCursorList,
    TransactionRead,
    TransferCreate,
    TransferRead,
)
from .base_service import BaseService

logger = logging.getLogger(__name__)


class TransactionService(BaseService):
    """Service for transaction-related business operations."""

    def __init__(self, session: AsyncSession):
        """Initialize service with database session and repository."""
        super().__init__(session)
        self.repository = TransactionRepository(session)
        self.account_repository = AccountRepository(session)
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

    async def list_user_transactions(
        self,
        user_id: str,
        pagination: PaginationParams | None = None,
        filters: TransactionFilterParams | None = None,
    ) -> AccountTransactionList:
        """List transactions for a user's account."""
        logger.debug(f"list_user_transactions called for user_id={user_id}, pagination={pagination}, filters={filters}")

        account = await self.account_repository.get_by_user_id(user_id)

        logger.debug(f"Account lookup result for user {user_id}: account={'found' if account else 'NOT FOUND'}")

        if not account:
            logger.error(f"No account found for user {user_id}")
            raise ResourceNotFoundError("Account", f"No account found for user {user_id}")

        if filters is None:
            filters = TransactionFilterParams(account_id=str(account.id))
        else:
            filters.account_id = str(account.id)

        if pagination is None:
            pagination = PaginationParams()
        transactions, total = await self.repository.list_transactions(pagination=pagination, filters=filters)

        transaction_outs = [await self._enrich_transaction_with_related_account(tx) for tx in transactions]

        return AccountTransactionList(
            transactions=transaction_outs,
            total=total,
            limit=pagination.limit,
            offset=pagination.offset,
        )

    async def list_user_transactions_with_cursor(
        self,
        user_id: str,
        pagination: CursorPaginationParams,
        transaction_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> TransactionCursorList:
        """List user transactions with cursor-based pagination."""
        account = await self.account_repository.get_by_user_id(user_id)

        if not account:
            raise ResourceNotFoundError("Account", f"No account found for user {user_id}")

        transactions, next_cursor = await self.repository.get_transactions_with_cursor(
            account_id=account.id,
            pagination=pagination,
            transaction_type=transaction_type,
            start_date=start_date,
            end_date=end_date,
        )

        transaction_outs = [await self._enrich_transaction_with_related_account(tx) for tx in transactions]

        return TransactionCursorList(items=transaction_outs, next_cursor=next_cursor)

    async def get_user_transaction(self, transaction_id: str, user_id: str) -> TransactionRead:
        """Get a specific transaction for a user, verifying ownership."""
        logger.debug(f"get_user_transaction called for transaction_id={transaction_id}, user_id={user_id}")

        account = await self.account_repository.get_by_user_id(user_id)

        logger.debug(f"Account lookup result for user {user_id}: account={'found' if account else 'NOT FOUND'}")

        if not account:
            logger.error(f"No account found for user {user_id} when accessing transaction {transaction_id}")
            raise ResourceNotFoundError("Account", f"No account found for user {user_id}")

        transaction = await self.repository.get_by_id_with_accounts(transaction_id)
        if not transaction:
            raise ResourceNotFoundError("Transaction", f"Transaction {transaction_id} not found")

        logger.debug(f"Transaction {transaction_id} belongs to account {transaction.account_id}, user's account is {account.id}")

        if str(transaction.account_id) != str(account.id):
            logger.error(f"User {user_id} attempted to access transaction {transaction_id} belonging to different account")
            raise ResourceNotFoundError("Transaction", f"Transaction {transaction_id} not found")

        return await self._enrich_transaction_with_related_account(transaction)

    async def process_card_payment(self, request: CardPaymentCreate) -> TransactionRead:
        """Process a credit card payment.

        Args:
            request: Card payment request data

        Returns:
            TransactionRead: The payment transaction (debit from card holder's account)

        Raises:
            InvalidCardProcessingError: If card validation fails
            InsufficientFundsError: If insufficient funds
            ResourceNotFoundError: If accounts not found
        """
        from .card_service import CardService

        idempotency_key = f"card_payment_{uuid.uuid4()}"

        card_service = CardService(self.session)
        card = await card_service.validate_card_for_payment(request.pan, request.cvv, request.exp_month, request.exp_year)

        source_account = await self.account_repository.get_by_id(str(card.account_id))
        if not source_account:
            raise ResourceNotFoundError("Account", f"Source account {card.account_id} not found")

        if source_account.balance_cents < request.amount_cents:
            raise InsufficientFundsError(
                available=int(source_account.balance_cents),
                required=request.amount_cents,
                details=f"Insufficient funds in account {source_account.id}",
            )

        dest_account = await self.account_repository.get_by_number(request.to_account_number)
        if not dest_account:
            raise ResourceNotFoundError("Account", f"Destination account {request.to_account_number} not found")

        source_account = await self.account_repository.update_balance(
            account_id=str(source_account.id),
            new_balance=int(source_account.balance_cents) - request.amount_cents,
        )

        dest_account = await self.account_repository.update_balance(
            account_id=str(dest_account.id),
            new_balance=int(dest_account.balance_cents) + request.amount_cents,
        )

        card_payment_tx, _ = await self.repository.create_double_entry(
            source_account_id=str(source_account.id),
            dest_account_id=str(dest_account.id),
            source_transaction_type=TransactionType.CARD_PAYMENT.value,
            dest_transaction_type=TransactionType.TRANSFER_IN.value,
            amount_cents=request.amount_cents,
            idempotency_key=idempotency_key,
            meta={
                "card_id": str(card.id),
                "card_last4": card.last4,
                "card_brand": card.brand,
                **(request.meta or {}),
            },
        )

        logger.info(
            f"Card payment processed: {request.amount_cents} cents from card {card.id} to account {dest_account.id}",
            extra={
                "amount_cents": request.amount_cents,
                "card_id": str(card.id),
                "card_last4": card.last4,
                "card_brand": card.brand,
                "source_account_id": str(source_account.id),
                "dest_account_id": str(dest_account.id),
                "idempotency_key": idempotency_key,
                "action": "card_payment",
            },
        )

        return await self._enrich_transaction_with_related_account(card_payment_tx)

    async def transfer_funds_for_user(self, request: TransferCreate, user_id: str) -> TransferRead:
        """Transfer funds for a user, handling account lookup internally."""
        logger.debug(f"transfer_funds_for_user called for user_id={user_id}, request={request}")

        from_account = await self.account_repository.get_by_user_id(user_id)

        logger.debug(f"Account lookup result for user {user_id}: account={'found' if from_account else 'NOT FOUND'}")

        if not from_account:
            logger.error(f"No account found for user {user_id}")
            raise ResourceNotFoundError("Account", f"No account found for user {user_id}")

        transfer_out_tx, _transfer_in_tx, from_account_response, to_account_response = await self._transfer_funds(
            from_account_number=from_account.number,  # type: ignore[arg-type]
            to_account_number=request.to_account_number,
            amount_cents=request.amount_cents,
            idempotency_key=None,
            meta=request.meta,
        )

        return TransferRead(
            transaction=transfer_out_tx,
            from_account=from_account_response,
            to_account=to_account_response,
        )

    async def _transfer_funds(
        self,
        from_account_number: str,
        to_account_number: str,
        amount_cents: int,
        idempotency_key: str | None = None,
        meta: dict | None = None,
    ) -> tuple[TransactionRead, TransactionRead, Any, Any]:
        """Transfer funds between accounts atomically (internal method)."""
        if idempotency_key is None:
            idempotency_key = f"transfer_{uuid.uuid4()}"

        existing_tx = await self.repository.get_by_idempotency_key(
            f"{idempotency_key}:out"
        ) or await self.repository.get_by_idempotency_key(f"{idempotency_key}:in")
        if existing_tx:
            existing_meta = getattr(existing_tx, "meta", {})
            expected_amount = existing_meta.get("amount_cents")
            expected_from_account = existing_meta.get("from_account_number")
            expected_to_account = existing_meta.get("to_account_number")

            if expected_amount != amount_cents or expected_from_account != from_account_number or expected_to_account != to_account_number:
                raise DuplicateIdempotencyKeyError(f"Idempotency key {idempotency_key} already used with different parameters")

            if existing_tx.type == TransactionType.TRANSFER_OUT.value:
                transfer_out_tx = existing_tx
                transfer_in_tx = await self.repository.get_by_idempotency_key(f"{idempotency_key}:in")
                from_account = await self.account_repository.get_by_id(str(transfer_out_tx.account_id))
                to_account = await self.account_repository.get_by_id(str(transfer_in_tx.account_id)) if transfer_in_tx else None
            else:
                transfer_in_tx = existing_tx
                transfer_out_tx = await self.repository.get_by_idempotency_key(f"{idempotency_key}:out")
                from_account = await self.account_repository.get_by_id(str(transfer_out_tx.account_id)) if transfer_out_tx else None
                to_account = await self.account_repository.get_by_id(str(transfer_in_tx.account_id))

            if transfer_out_tx and transfer_in_tx and from_account and to_account:
                return (
                    await self._enrich_transaction_with_related_account(transfer_out_tx),
                    await self._enrich_transaction_with_related_account(transfer_in_tx),
                    AccountRead.model_validate(from_account, from_attributes=True),
                    AccountRead.model_validate(to_account, from_attributes=True),
                )

        logger.debug(f"transfer_funds: looking up source account {from_account_number}")
        from_account = await self.account_repository.get_by_number(from_account_number)
        if not from_account:
            logger.error(f"transfer_funds: source account {from_account_number} not found")
            raise ResourceNotFoundError("Account", f"Source account {from_account_number} not found")

        logger.debug(f"transfer_funds: source account found, balance={from_account.balance_cents}, amount={amount_cents}")

        if from_account.balance_cents < amount_cents:
            logger.error(f"transfer_funds: insufficient funds - balance={from_account.balance_cents}, required={amount_cents}")
            raise InsufficientFundsError(
                available=from_account.balance_cents,  # type: ignore[arg-type]
                required=amount_cents,
                details=f"Insufficient funds in source account {from_account_number}",
            )

        logger.debug(f"transfer_funds: looking up destination account {to_account_number}")
        to_account = await self.account_repository.get_by_number(to_account_number)
        if not to_account:
            logger.error(f"transfer_funds: destination account {to_account_number} not found")
            raise ResourceNotFoundError("Account", f"Destination account {to_account_number} not found")

        logger.debug("transfer_funds: destination account found, proceeding with transfer")

        from_account_id = str(from_account.id)
        to_account_id = str(to_account.id)

        from_account = await self.account_repository.update_balance(
            account_id=from_account_id,
            new_balance=int(from_account.balance_cents) - amount_cents,
        )

        to_account = await self.account_repository.update_balance(
            account_id=to_account_id,
            new_balance=int(to_account.balance_cents) + amount_cents,
        )

        transfer_meta = {
            "amount_cents": amount_cents,
            "from_account_number": from_account_number,
            "to_account_number": to_account_number,
            **(meta or {}),
        }

        transfer_out_tx, transfer_in_tx = await self.repository.create_double_entry(
            source_account_id=from_account_id,
            dest_account_id=to_account_id,
            source_transaction_type=TransactionType.TRANSFER_OUT.value,
            dest_transaction_type=TransactionType.TRANSFER_IN.value,
            amount_cents=amount_cents,
            idempotency_key=idempotency_key,
            meta=transfer_meta,
        )

        if isinstance(from_account, AccountRead):
            from_account_response = from_account
        else:
            from_account_response = AccountRead.model_validate(from_account, from_attributes=True)

        if isinstance(to_account, AccountRead):
            to_account_response = to_account
        else:
            to_account_response = AccountRead.model_validate(to_account, from_attributes=True)

        return (
            await self._enrich_transaction_with_related_account(transfer_out_tx),
            await self._enrich_transaction_with_related_account(transfer_in_tx),
            from_account_response,
            to_account_response,
        )

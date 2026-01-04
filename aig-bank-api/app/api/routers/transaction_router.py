"""Transaction API endpoints (mixed authentication)."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db import get_db
from ...core.enums import TransactionType
from ...core.errors import ErrorCode
from ...schemas.core import (
    CursorPaginationParams,
    PaginationParams,
    TransactionFilterParams,
)
from ...schemas.transaction_schemas import (
    AccountTransactionList,
    CardPaymentCreate,
    TransactionCursorList,
    TransactionRead,
    TransferCreate,
    TransferRead,
)
from ...services.transaction_service import TransactionService
from ..deps import get_current_user

router = APIRouter(tags=["Transactions"])


@router.post(
    "/payments/credit-card",
    response_model=TransactionRead,
    summary="Process Credit Card Payment",
    description="""Process a payment using credit card information.

This endpoint validates the card, checks for sufficient funds, and processes the payment in a single transaction.
The CVV is validated but never stored.
""",
    responses={
        status.HTTP_200_OK: {
            "model": TransactionRead,
            "description": "Success",
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "examples": {
                        "validation_error": {
                            "summary": "Validation error",
                            "value": {
                                "error": ErrorCode.VALIDATION_ERROR.value,
                                "details": "PAN must contain only digits",
                                "request_id": "938304120f4492de",
                            },
                        },
                        "invalid_card_processing": {
                            "summary": "Invalid card processing",
                            "value": {
                                "error": ErrorCode.INVALID_CARD_PROCESSING.value,
                                "details": "Card cannot be processed. Please check your card details and try again.",
                                "request_id": "938304120f4492de",
                            },
                        },
                        "resource_not_found": {
                            "summary": "Resource not found",
                            "value": {
                                "error": ErrorCode.RESOURCE_NOT_FOUND.value,
                                "details": "Destination account 1234567890 not found",
                                "request_id": "938304120f4492de",
                            },
                        },
                        "insufficient_funds": {
                            "summary": "Insufficient funds",
                            "value": {
                                "error": ErrorCode.INSUFFICIENT_FUNDS.value,
                                "details": "Insufficient funds: 1200 < 2500",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def process_card_payment(
    payment_data: CardPaymentCreate,
    db: AsyncSession = Depends(get_db),
) -> TransactionRead:
    """Process a credit card payment.

    Args:
        payment_data: Card payment request data
        db: Database session

    Returns:
        TransactionRead: Payment transaction
    """
    transaction_service = TransactionService(db)
    return await transaction_service.process_card_payment(payment_data)


@router.post(
    "/users/transfers",
    response_model=TransferRead,
    summary="Transfer Funds",
    description="""Transfer funds from one account to another using account numbers.

This endpoint performs an atomic transfer operation between two accounts.
The transfer is processed in a single database transaction to ensure consistency.""",
    responses={
        status.HTTP_200_OK: {
            "model": TransferRead,
            "description": "Success",
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "examples": {
                        "validation_error": {
                            "summary": "Validation error",
                            "value": {
                                "error": ErrorCode.VALIDATION_ERROR.value,
                                "details": "Amount must be positive",
                                "request_id": "938304120f4492de",
                            },
                        },
                        "resource_not_found": {
                            "summary": "Resource not found",
                            "value": {
                                "error": ErrorCode.RESOURCE_NOT_FOUND.value,
                                "details": "Destination account 9876543210 not found",
                                "request_id": "938304120f4492de",
                            },
                        },
                        "insufficient_funds": {
                            "summary": "Insufficient funds",
                            "value": {
                                "error": ErrorCode.INSUFFICIENT_FUNDS.value,
                                "details": "Insufficient funds: 1200 < 2500",
                                "request_id": "938304120f4492de",
                            },
                        },
                        "duplicate_idempotency_key": {
                            "summary": "Duplicate idempotency key",
                            "value": {
                                "error": ErrorCode.DUPLICATE_IDEMPOTENCY_KEY.value,
                                "details": "Idempotency key transfer_abc123 already used with different parameters",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "examples": {
                        "authentication_required": {
                            "summary": "Authentication required",
                            "value": {
                                "error": ErrorCode.AUTHENTICATION_REQUIRED.value,
                                "details": "Authentication is required to access this resource",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def transfer_funds(
    transfer_request: TransferCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TransferRead:
    """Transfer funds to another account.

    Args:
        transfer_request: Transfer request data
        current_user: Authenticated user context
        db: Database session

    Returns:
        TransferRead: Transfer result
    """
    transaction_service = TransactionService(db)
    return await transaction_service.transfer_funds_for_user(transfer_request, current_user["user_id"])


@router.get(
    "/users/transactions",
    response_model=AccountTransactionList,
    summary="List My Transactions",
    description="""Retrieve a paginated list of transactions for the authenticated user's accounts.

Supports optional filtering by transaction type and date range.""",
    responses={
        status.HTTP_200_OK: {
            "model": AccountTransactionList,
            "description": "Success",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "examples": {
                        "authentication_required": {
                            "summary": "Authentication required",
                            "value": {
                                "error": ErrorCode.AUTHENTICATION_REQUIRED.value,
                                "details": "Authentication is required to access this resource",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def list_my_transactions(
    transaction_type: TransactionType | None = Query(None, description="Filter by transaction type"),
    start_date: datetime | None = Query(None, description="Filter from date"),
    end_date: datetime | None = Query(None, description="Filter to date"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AccountTransactionList:
    """List transactions for the current user.

    Args:
        transaction_type: Filter by transaction type
        start_date: Filter from date
        end_date: Filter to date
        limit: Maximum number of results
        offset: Number of results to skip
        current_user: Authenticated user context
        db: Database session

    Returns:
        AccountTransactionList: Paginated transaction list
    """
    transaction_service = TransactionService(db)

    filters = None
    if transaction_type or start_date or end_date:
        filters = TransactionFilterParams(
            transaction_type=transaction_type.value if transaction_type else None,
            start_date=start_date,
            end_date=end_date,
        )

    pagination = PaginationParams(limit=limit, offset=offset)
    return await transaction_service.list_user_transactions(current_user["user_id"], pagination=pagination, filters=filters)


@router.get(
    "/users/transactions-cursor",
    response_model=TransactionCursorList,
    summary="List My Transactions (Cursor)",
    description="""Retrieve transactions using cursor-based pagination.

Provides cursor-based pagination for transaction history, which is more efficient for large datasets.
Use the next_cursor from the response to get the next page.""",
    responses={
        status.HTTP_200_OK: {
            "model": TransactionCursorList,
            "description": "Success",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "examples": {
                        "authentication_required": {
                            "summary": "Authentication required",
                            "value": {
                                "error": ErrorCode.AUTHENTICATION_REQUIRED.value,
                                "details": "Authentication is required to access this resource",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def list_my_transactions_cursor(
    transaction_type: TransactionType | None = Query(None, description="Filter by transaction type"),
    start_date: datetime | None = Query(None, description="Filter from date"),
    end_date: datetime | None = Query(None, description="Filter to date"),
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None, description="Cursor for pagination"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TransactionCursorList:
    """List transactions for the current user using cursor-based pagination.

    Args:
        transaction_type: Filter by transaction type
        start_date: Filter from date
        end_date: Filter to date
        limit: Maximum number of results
        cursor: Cursor for pagination
        current_user: Authenticated user context
        db: Database session

    Returns:
        TransactionCursorList: Cursor-paginated transaction list
    """
    transaction_service = TransactionService(db)

    pagination = CursorPaginationParams(limit=limit, cursor=cursor)
    return await transaction_service.list_user_transactions_with_cursor(
        current_user["user_id"],
        pagination=pagination,
        transaction_type=transaction_type.value if transaction_type else None,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/users/transactions/{transaction_id}",
    response_model=TransactionRead,
    summary="Get My Transaction",
    description="Retrieve a specific transaction by ID for the authenticated user.",
    responses={
        status.HTTP_200_OK: {
            "model": TransactionRead,
            "description": "Success",
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "examples": {
                        "resource_not_found": {
                            "summary": "Resource not found",
                            "value": {
                                "error": ErrorCode.RESOURCE_NOT_FOUND.value,
                                "details": "Transaction 770e8400-e29b-41d4-a716-446655440000 not found",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "examples": {
                        "authentication_required": {
                            "summary": "Authentication required",
                            "value": {
                                "error": ErrorCode.AUTHENTICATION_REQUIRED.value,
                                "details": "Authentication is required to access this resource",
                                "request_id": "938304120f4492de",
                            },
                        },
                        "forbidden": {
                            "summary": "Forbidden",
                            "value": {
                                "error": ErrorCode.FORBIDDEN.value,
                                "details": "You do not have permission to access this transaction",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def get_my_transaction(
    transaction_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TransactionRead:
    """Get a specific transaction for the current user.

    Args:
        transaction_id: Transaction ID to retrieve
        current_user: Authenticated user context
        db: Database session

    Returns:
        TransactionRead: Transaction details
    """
    transaction_service = TransactionService(db)
    return await transaction_service.get_user_transaction(transaction_id, current_user["user_id"])

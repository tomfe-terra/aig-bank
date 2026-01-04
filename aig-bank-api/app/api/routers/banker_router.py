"""Banker API endpoints (requires BANKER role authentication)."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db import get_db
from ...core.enums import RequestKind
from ...core.errors import ErrorCode
from ...schemas.card_schemas import BankerCardList, CardCancel
from ...schemas.request_schemas import (
    RequestDecision,
    RequestList,
    RequestRejection,
)
from ...services.card_service import CardService
from ...services.request_service import RequestService
from ..deps import require_banker_role

router = APIRouter(prefix="/banker", tags=["Banker"])


@router.get(
    "/requests",
    response_model=RequestList,
    status_code=status.HTTP_200_OK,
    summary="List Pending Requests",
    description="""Retrieve a paginated list of pending requests for bank staff review.

This endpoint allows bank staff to view all pending requests for loans and credit cards.
Requests can be filtered by type (LOAN or CREDIT_CARD) and support pagination for better performance with large datasets.""",
    responses={
        status.HTTP_200_OK: {
            "model": RequestList,
            "description": "Success",
            "content": {
                "application/json": {
                    "examples": {
                        "pending_requests": {
                            "summary": "List of pending requests",
                            "value": {
                                "requests": [
                                    {
                                        "id": "bb0e8400-e29b-41d4-a716-446655440000",
                                        "kind": "LOAN",
                                        "payload": {"principal_cents": 100000, "repayment_cycles": 24},
                                        "status": "PENDING",
                                        "requested_by": "550e8400-e29b-41d4-a716-446655440000",
                                        "decided_by": None,
                                        "decided_at": None,
                                        "created_at": "2025-01-01T00:00:00Z",
                                    }
                                ],
                                "total": 1,
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
                        "insufficient_permissions": {
                            "summary": "Insufficient permissions",
                            "value": {
                                "error": ErrorCode.INSUFFICIENT_PERMISSIONS.value,
                                "details": "Insufficient permissions: BANKER role required",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def list_requests(
    kind: str | None = Query(None, description="Filter by request kind (CREDIT_CARD or LOAN)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_banker_role),
    db: AsyncSession = Depends(get_db),
) -> RequestList:
    """List pending requests.

    Args:
        kind: Filter by request kind (CREDIT_CARD or LOAN)
        limit: Maximum number of results
        offset: Number of results to skip
        current_user: Authenticated banker context
        db: Database session

    Returns:
        RequestList: Paginated list of pending requests
    """
    request_service = RequestService(db)
    requests, total = await request_service.list_pending_requests(kind=kind, limit=limit, offset=offset)
    return RequestList(requests=requests, total=total)


@router.post(
    "/requests/{request_id}/approve",
    response_model=RequestDecision,
    status_code=status.HTTP_200_OK,
    summary="Approve Request",
    description="""Approve a pending request (loan or credit card application).

Bankers can approve requests that are in PENDING status. Upon decision:
- **Loan requests**: Create a loan record and disburse funds to the account
- **Credit card requests**: Issue a new credit card for the account

The decision is processed atomically to ensure data consistency.""",
    responses={
        status.HTTP_200_OK: {
            "model": RequestDecision,
            "description": "Success",
            "content": {
                "application/json": {
                    "examples": {
                        "loan_approved": {
                            "summary": "Loan request approved",
                            "value": {
                                "message": "Request approved successfully",
                                "request": {
                                    "id": "bb0e8400-e29b-41d4-a716-446655440000",
                                    "kind": "LOAN",
                                    "status": "APPROVED",
                                    "decided_by": "dd0e8400-e29b-41d4-a716-446655440000",
                                },
                                "loan": {
                                    "id": "cc0e8400-e29b-41d4-a716-446655440000",
                                    "principal_cents": 100000,
                                    "status": "ACTIVE",
                                },
                                "disbursement_transaction": {
                                    "id": "770e8400-e29b-41d4-a716-446655440000",
                                    "type": "LOAN_DISBURSEMENT",
                                    "amount_cents": 100000,
                                },
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_data": {
                            "summary": "Request not pending",
                            "value": {
                                "error": ErrorCode.INVALID_DATA.value,
                                "details": "Request bb0e8400-e29b-41d4-a716-446655440000 is not pending decision",
                                "request_id": "938304120f4492de",
                            },
                        },
                        "resource_not_found": {
                            "summary": "Request not found",
                            "value": {
                                "error": ErrorCode.RESOURCE_NOT_FOUND.value,
                                "details": "Request not found",
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
                        "insufficient_permissions": {
                            "summary": "Insufficient permissions",
                            "value": {
                                "error": ErrorCode.INSUFFICIENT_PERMISSIONS.value,
                                "details": "Insufficient permissions: BANKER role required",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def approve_request(
    request_id: str,
    current_user: dict = Depends(require_banker_role),
    db: AsyncSession = Depends(get_db),
) -> RequestDecision:
    """Approve a request.

    Args:
        request_id: Request ID to approve
        current_user: Authenticated banker context
        db: Database session

    Returns:
        RequestDecision: Decision result with side effects
    """
    request_service = RequestService(db)
    banker_id = current_user["user_id"]

    approved_request, result = await request_service.approve_request(request_id, banker_id)

    if approved_request.kind == RequestKind.LOAN and result:
        loan, disbursement_tx = result
        return RequestDecision(
            message="Request approved successfully",
            request=approved_request,
            loan=loan,
            disbursement_transaction=disbursement_tx,
        )
    elif approved_request.kind == RequestKind.CREDIT_CARD and result:
        card = result
        return RequestDecision(
            message="Request approved successfully",
            request=approved_request,
            card=card,
            loan=None,
        )
    else:
        return RequestDecision(
            message="Request approved successfully",
            request=approved_request,
        )


@router.post(
    "/requests/{request_id}/reject",
    response_model=RequestRejection,
    status_code=status.HTTP_200_OK,
    summary="Reject Request",
    description="""Reject a pending request (loan or credit card application).

Bankers can reject requests that are in PENDING status. The request will be marked as REJECTED and no further action will be taken.""",
    responses={
        status.HTTP_200_OK: {
            "model": RequestRejection,
            "description": "Success",
            "content": {
                "application/json": {
                    "examples": {
                        "request_rejected": {
                            "summary": "Request rejected",
                            "value": {
                                "message": "Request rejected successfully",
                                "request": {
                                    "id": "bb0e8400-e29b-41d4-a716-446655440000",
                                    "kind": "LOAN",
                                    "status": "REJECTED",
                                    "decided_by": "dd0e8400-e29b-41d4-a716-446655440000",
                                },
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_data": {
                            "summary": "Request not pending",
                            "value": {
                                "error": ErrorCode.INVALID_DATA.value,
                                "details": "Request bb0e8400-e29b-41d4-a716-446655440000 is not pending decision",
                                "request_id": "938304120f4492de",
                            },
                        },
                        "resource_not_found": {
                            "summary": "Request not found",
                            "value": {
                                "error": ErrorCode.RESOURCE_NOT_FOUND.value,
                                "details": "Request not found",
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
                        "insufficient_permissions": {
                            "summary": "Insufficient permissions",
                            "value": {
                                "error": ErrorCode.INSUFFICIENT_PERMISSIONS.value,
                                "details": "Insufficient permissions: BANKER role required",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def reject_request(
    request_id: str,
    current_user: dict = Depends(require_banker_role),
    db: AsyncSession = Depends(get_db),
) -> RequestRejection:
    """Reject a request.

    Args:
        request_id: Request ID to reject
        current_user: Authenticated banker context
        db: Database session

    Returns:
        RequestRejection: Rejection result
    """
    request_service = RequestService(db)
    banker_id = current_user["user_id"]

    rejected_request = await request_service.reject_request(request_id, banker_id)

    return RequestRejection(
        message="Request rejected successfully",
        request=rejected_request,
    )


@router.post(
    "/cards/{card_id}/cancel",
    response_model=CardCancel,
    status_code=status.HTTP_200_OK,
    summary="Cancel Credit Card",
    description="""Cancel a credit card issued to a user.

Bankers can cancel credit cards that are in ACTIVE status. The card will be marked as CANCELLED and can no
longer be used for transactions.""",
    responses={
        status.HTTP_200_OK: {
            "model": CardCancel,
            "description": "Success",
            "content": {
                "application/json": {
                    "examples": {
                        "card_cancelled": {
                            "summary": "Card cancelled successfully",
                            "value": {
                                "message": "Card cancelled successfully",
                                "card": {
                                    "id": "aa0e8400-e29b-41d4-a716-446655440000",
                                    "account_id": "550e8400-e29b-41d4-a716-446655440000",
                                    "last4": "1111",
                                    "brand": "VISA",
                                    "status": "CANCELLED",
                                },
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "examples": {
                        "resource_not_found": {
                            "summary": "Card not found",
                            "value": {
                                "error": ErrorCode.RESOURCE_NOT_FOUND.value,
                                "details": "Card not found",
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
                        "insufficient_permissions": {
                            "summary": "Insufficient permissions",
                            "value": {
                                "error": ErrorCode.INSUFFICIENT_PERMISSIONS.value,
                                "details": "Insufficient permissions: BANKER role required",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def cancel_card(
    card_id: str,
    current_user: dict = Depends(require_banker_role),
    db: AsyncSession = Depends(get_db),
) -> CardCancel:
    """Cancel a credit card.

    Args:
        card_id: Card ID to cancel
        current_user: Authenticated banker context
        db: Database session

    Returns:
        CardCancel: Cancellation result
    """
    card_service = CardService(db)
    banker_id = current_user["user_id"]

    cancelled_card = await card_service.cancel_card(card_id, banker_id)

    return CardCancel(
        message="Card cancelled successfully",
        card=cancelled_card,
    )


@router.get(
    "/cards",
    response_model=BankerCardList,
    status_code=status.HTTP_200_OK,
    summary="List All Credit Cards",
    description="""Retrieve a paginated list of all credit cards in the system with owner information.

This endpoint allows bank staff to view all credit cards across all users.
Only card ID, last 4 digits, and basic user information are exposed for privacy.""",
    responses={
        status.HTTP_200_OK: {
            "model": BankerCardList,
            "description": "Success",
            "content": {
                "application/json": {
                    "examples": {
                        "card_list": {
                            "summary": "List of credit cards",
                            "value": {
                                "cards": [
                                    {
                                        "id": "aa0e8400-e29b-41d4-a716-446655440000",
                                        "last4": "1111",
                                        "brand": "VISA",
                                        "status": "ACTIVE",
                                        "created_at": "2025-01-01T00:00:00Z",
                                        "owner": {
                                            "id": "550e8400-e29b-41d4-a716-446655440000",
                                            "username": "johndoe",
                                            "first_name": "John",
                                            "last_name": "Doe",
                                            "email": "john@example.com",
                                            "role": "USER",
                                        },
                                    }
                                ],
                                "total": 1,
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
                        "insufficient_permissions": {
                            "summary": "Insufficient permissions",
                            "value": {
                                "error": ErrorCode.INSUFFICIENT_PERMISSIONS.value,
                                "details": "Insufficient permissions: BANKER role required",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def list_all_cards(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: dict = Depends(require_banker_role),
    db: AsyncSession = Depends(get_db),
) -> BankerCardList:
    """List all credit cards with owner information.

    Args:
        limit: Maximum number of results
        offset: Number of results to skip
        current_user: Authenticated banker context
        db: Database session

    Returns:
        BankerCardList: Paginated list of credit cards with owner info
    """
    card_service = CardService(db)
    return await card_service.list_all_cards_for_banker(limit=limit, offset=offset)

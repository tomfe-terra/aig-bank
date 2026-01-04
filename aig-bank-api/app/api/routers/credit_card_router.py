"""Credit Card API endpoints (requires authentication)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db import get_db
from ...core.errors import ErrorCode
from ...schemas.card_schemas import CardRead, CardReveal
from ...schemas.request_schemas import CardRequestCreate, Request
from ...services.card_service import CardService
from ...services.request_service import RequestService
from ..deps import get_current_user

router = APIRouter(prefix="/users", tags=["Credit Cards"])


@router.get(
    "/cards",
    response_model=list[CardRead],
    status_code=status.HTTP_200_OK,
    summary="List My Cards",
    description="""Retrieve all credit cards associated with the authenticated user's accounts.

This endpoint returns a list of all credit cards linked to the user's accounts,
with sensitive information (PAN) masked for security. Each card includes basic
information like last 4 digits, brand, expiration date, and status.""",
    responses={
        status.HTTP_200_OK: {
            "description": "Success",
            "model": list[CardRead],
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
                                "request_id": "a1b2c3d4e5f6g7h8",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def list_my_cards(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CardRead]:
    """List all credit cards for the current user.

    Args:
        current_user: Authenticated user context
        db: Database session

    Returns:
        list[CardRead]: List of user's credit cards
    """
    card_service = CardService(db)
    return await card_service.list_user_cards(current_user["user_id"])


@router.get(
    "/cards/{card_id}/reveal",
    response_model=CardReveal,
    status_code=status.HTTP_200_OK,
    summary="Reveal Card PAN",
    description="""Reveal the full Primary Account Number (PAN) for a specific credit card.

**Security Note:** This endpoint returns sensitive card information and should be used
sparingly. The PAN is only revealed to the card owner and proper authorization is required.
This endpoint is rate-limited and should not be used for logging or caching purposes.""",
    responses={
        status.HTTP_200_OK: {
            "description": "Success",
            "model": CardReveal,
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "examples": {
                        "card_not_found": {
                            "summary": "Card not found",
                            "value": {
                                "error": ErrorCode.RESOURCE_NOT_FOUND.value,
                                "details": "Credit card aa0e8400-e29b-41d4-a716-446655440000 not found",
                                "request_id": "a1b2c3d4e5f6g7h8",
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
                                "request_id": "a1b2c3d4e5f6g7h8",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def reveal_card_pan(
    card_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CardReveal:
    """Reveal the full PAN for a specific card.

    Args:
        card_id: Card ID to reveal
        current_user: Authenticated user context
        db: Database session

    Returns:
        CardReveal: Card details with full PAN
    """
    card_service = CardService(db)
    return await card_service.reveal_pan(card_id, current_user["user_id"])


@router.post(
    "/cards/request",
    response_model=Request,
    status_code=status.HTTP_201_CREATED,
    summary="Request Card",
    description="""Submit a credit card application for review by bank staff.

This endpoint creates a card request that will be reviewed by bank staff before approval.
The card request includes PAN, expiration date, and CVV. Once approved, the card will be
issued and become active for use.""",
    responses={
        status.HTTP_201_CREATED: {
            "description": "Success",
            "model": Request,
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
                                "details": "Card type must be between 1 and 50 characters",
                                "request_id": "a1b2c3d4e5f6g7h8",
                            },
                        },
                        "account_not_found": {
                            "summary": "Account not found",
                            "value": {
                                "error": ErrorCode.RESOURCE_NOT_FOUND.value,
                                "details": "No account found for user 550e8400-e29b-41d4-a716-446655440000",
                                "request_id": "a1b2c3d4e5f6g7h8",
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
                                "request_id": "a1b2c3d4e5f6g7h8",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def request_card(
    card_request: CardRequestCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Request:
    """Request a new credit card.

    Creates a new request for a credit card for the user's single account.
    The user only needs to specify the card type (VISA, etc.). Once approved by a banker,
    the full card details will be generated and the card will be issued and become active for use.

    Args:
        card_request: Card request data
        current_user: Authenticated user context
        db: Database session

    Returns:
        Request: The created request
    """
    request_service = RequestService(db)
    result = await request_service.create_card_request_for_user(card_request, current_user["user_id"])
    return result.request

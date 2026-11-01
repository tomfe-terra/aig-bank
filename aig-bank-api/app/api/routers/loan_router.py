"""Loan API endpoints (requires authentication)."""

import logging
import urllib.error
import urllib.request

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db import get_db
from ...core.errors import ErrorCode, InvalidDataError
from ...schemas.loan_schemas import DocumentFetchResult, LoanRead
from ...schemas.request_schemas import LoanRequestCreate, Request
from ...services.loan_service import LoanService
from ...services.request_service import RequestService
from ..deps import get_current_user

router = APIRouter(prefix="/users", tags=["Loans"])
logger = logging.getLogger(__name__)


@router.post(
    "/loans/request",
    response_model=Request,
    status_code=status.HTTP_201_CREATED,
    summary="Request Loan",
    description=(
        "Submit a loan application for review by bank staff. "
        "Creates a loan request that will be reviewed before approval. "
        "Once approved, funds will be disbursed to the user's account."
    ),
    responses={
        status.HTTP_200_OK: {
            "description": "Success",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "kind": "LOAN",
                        "status": "PENDING",
                        "requested_by": "123e4567-e89b-12d3-a456-426614174000",
                        "decided_by": None,
                        "decided_at": None,
                        "created_at": "2024-01-15T10:30:00Z",
                        "payload": {
                            "principal_cents": 100000,
                            "repayment_cycles": 24,
                        },
                    }
                }
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "examples": {
                        "validation_error": {
                            "summary": "Invalid input",
                            "value": {
                                "error": ErrorCode.VALIDATION_ERROR.value,
                                "details": "Principal amount must be positive",
                                "request_id": "a1b2c3d4e5f6",
                            },
                        },
                        "resource_not_found": {
                            "summary": "Account not found",
                            "value": {
                                "error": ErrorCode.RESOURCE_NOT_FOUND.value,
                                "details": "Account not found for user",
                                "request_id": "a1b2c3d4e5f6",
                            },
                        },
                    }
                }
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "example": {
                        "error": ErrorCode.AUTHENTICATION_REQUIRED.value,
                        "details": "Authentication required",
                        "request_id": "a1b2c3d4e5f6",
                    }
                }
            },
        },
    },
)
async def request_loan(
    loan_request: LoanRequestCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Request:
    """Request a new loan.

    Args:
        loan_request: Loan request data
        current_user: Authenticated user context
        db: Database session

    Returns:
        Request: Created loan request
    """
    request_service = RequestService(db)
    result = await request_service.create_loan_request_for_user(loan_request, current_user["user_id"])
    return result.request


@router.get(
    "/loans",
    response_model=list[LoanRead],
    status_code=status.HTTP_200_OK,
    summary="List My Loans",
    description=(
        "Retrieve all loans associated with the authenticated user's accounts, including loan details, status, and payment information."
    ),
    responses={
        status.HTTP_200_OK: {
            "description": "Success",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "550e8400-e29b-41d4-a716-446655440000",
                            "account_id": "123e4567-e89b-12d3-a456-426614174000",
                            "principal_cents": 100000,
                            "repayment_cycles": 24,
                            "status": "ACTIVE",
                            "remaining_balance_cents": 75000,
                            "next_payment_at": "2024-01-16T10:30:00Z",
                            "created_at": "2024-01-15T10:30:00Z",
                        }
                    ]
                }
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "example": {
                        "error": ErrorCode.AUTHENTICATION_REQUIRED.value,
                        "details": "Authentication required",
                        "request_id": "a1b2c3d4e5f6",
                    }
                }
            },
        },
    },
)
async def list_my_loans(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[LoanRead]:
    """List all loans for the current user.

    Args:
        current_user: Authenticated user context
        db: Database session

    Returns:
        list[LoanRead]: List of user's loans
    """
    loan_service = LoanService(db)
    return await loan_service.list_user_loans(current_user["user_id"])


@router.get(
    "/loans/{loan_id}",
    response_model=LoanRead,
    status_code=status.HTTP_200_OK,
    summary="Get My Loan",
    description=(
        "Retrieve detailed information about a specific loan owned by the authenticated user, including payment details and loan status."
    ),
    responses={
        status.HTTP_200_OK: {
            "description": "Success",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "account_id": "123e4567-e89b-12d3-a456-426614174000",
                        "principal_cents": 100000,
                        "repayment_cycles_hours": 24,
                        "status": "ACTIVE",
                        "remaining_balance_cents": 75000,
                        "next_payment_at": "2024-01-16T10:30:00Z",
                        "created_at": "2024-01-15T10:30:00Z",
                    }
                }
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "example": {
                        "error": ErrorCode.RESOURCE_NOT_FOUND.value,
                        "details": "Loan not found",
                        "request_id": "a1b2c3d4e5f6",
                    }
                }
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "example": {
                        "error": ErrorCode.AUTHENTICATION_REQUIRED.value,
                        "details": "Authentication required",
                        "request_id": "a1b2c3d4e5f6",
                    }
                }
            },
        },
    },
)
async def get_my_loan(
    loan_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LoanRead:
    """Get a specific loan for the current user.

    Args:
        loan_id: Loan ID to retrieve
        current_user: Authenticated user context
        db: Database session

    Returns:
        LoanRead: Loan details
    """
    loan_service = LoanService(db)
    return await loan_service.get_loan(loan_id, current_user["user_id"])


@router.get(
    "/documents/fetch",
    response_model=DocumentFetchResult,
    status_code=status.HTTP_200_OK,
    summary="Fetch Document URL (Intentionally Vulnerable)",
    description="""Fetch a document from a URL supplied by the caller.

**SECURITY WARNING**: This endpoint is intentionally VULNERABLE to server-side request forgery for learning purposes.
The server requests the URL with no allowlist.
""",
)
async def fetch_document(
    url: str = Query(..., description="Document URL to fetch"),
    current_user: dict = Depends(get_current_user),
) -> DocumentFetchResult:
    """Fetch a remote document.

    SECURITY WARNING: Intentionally vulnerable to server-side request forgery for learning purposes.
    The URL is requested as given.

    Args:
        url: Document URL
        current_user: Authenticated user context

    Returns:
        DocumentFetchResult: Status and the start of the response body
    """
    logger.info("document fetch requested by user %s", current_user["user_id"])
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            raw = response.read(8192)
            status_code = int(getattr(response, "status", 200))
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise InvalidDataError("url", url, f"Could not fetch document: {exc}") from exc

    return DocumentFetchResult(
        url=url,
        status_code=status_code,
        body=raw.decode("utf-8", errors="replace"),
    )

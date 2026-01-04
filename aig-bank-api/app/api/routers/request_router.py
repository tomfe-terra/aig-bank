"""Request API endpoints (requires authentication)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db import get_db
from ...core.errors import ErrorCode
from ...schemas.request_schemas import Request
from ...services.request_service import RequestService
from ..deps import get_current_user

router = APIRouter(prefix="/users", tags=["Requests"])


@router.get(
    "/requests",
    response_model=list[Request],
    status_code=status.HTTP_200_OK,
    summary="List My Requests",
    description="""Retrieve all requests submitted by the authenticated user.

This endpoint returns a list of all requests (loans and credit cards) that the user
has submitted, including their current status.""",
    responses={
        status.HTTP_200_OK: {
            "description": "Success",
            "model": list[Request],
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
async def list_my_requests(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Request]:
    """List all requests for the current user.

    Args:
        current_user: Authenticated user context
        db: Database session

    Returns:
        list[Request]: List of user's requests
    """
    request_service = RequestService(db)
    return await request_service.list_user_requests(current_user["user_id"])


@router.get(
    "/requests/{request_id}",
    response_model=Request,
    status_code=status.HTTP_200_OK,
    summary="Get Request",
    description="""Retrieve a specific request by ID for the authenticated user.

This endpoint allows users to get detailed information about a specific request
they submitted, including the current status and decision details.""",
    responses={
        status.HTTP_200_OK: {
            "description": "Success",
            "model": Request,
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "examples": {
                        "resource_not_found": {
                            "summary": "Request not found",
                            "value": {
                                "error": ErrorCode.RESOURCE_NOT_FOUND.value,
                                "details": "Request bb0e8400-e29b-41d4-a716-446655440000 not found",
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
async def get_request(
    request_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Request:
    """Get a specific request for the current user.

    Args:
        request_id: Request ID to retrieve
        current_user: Authenticated user context
        db: Database session

    Returns:
        Request: Request details
    """
    request_service = RequestService(db)
    return await request_service.get_request(request_id, current_user["user_id"])

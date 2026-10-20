"""Request API endpoints (requires authentication)."""

from fastapi import APIRouter, Depends, Query, status
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
    summary="List My Requests (Intentionally Vulnerable)",
    description="""Retrieve requests. 
    
    **SECURITY WARNING**: This endpoint is intentionally VULNERABLE to IDOR for learning purposes.
    It allows fetching any user's requests by providing a user_id query parameter.
    """,
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
    user_id: str | None = Query(None, description="The user ID to fetch requests for (IDOR override)"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Request]:
    """List requests.

    Args:
        user_id: Optional user ID to override the current user (IDOR vulnerability)
        current_user: Authenticated user context
        db: Database session

    Returns:
        list[Request]: List of requests
    """
    request_service = RequestService(db)
    
    # Intentionally vulnerable: use user_id from query if provided,
    # otherwise fallback to the authenticated user.
    target_user_id = user_id if user_id else current_user["user_id"]
    
    return await request_service.list_user_requests(target_user_id)


@router.get(
    "/requests/{request_id}",
    response_model=Request,
    status_code=status.HTTP_200_OK,
    summary="Get Request (Intentionally Vulnerable)",
    description="""Retrieve a specific request by ID.
    
    **SECURITY WARNING**: This endpoint is intentionally VULNERABLE to IDOR for learning purposes.
    It allows any authenticated user to view any request by ID, bypassing ownership checks.
    """,
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
    """Get a specific request.

    Args:
        request_id: Request ID to retrieve
        current_user: Authenticated user context
        db: Database session

    Returns:
        Request: Request details
    """
    request_service = RequestService(db)
    
    # To introduce the vulnerability, we bypass the service's ownership check
    # or pass a 'decided_by' ID that matches the user to trick it.
    # The current get_request implementation in RequestService is:
    # if request.requested_by != user_id and request.decided_by != user_id:
    #     raise ResourceNotFoundError(...)
    
    # We'll call the repository directly or fetch it then return it without checking ownership.
    request_data = await request_service.repository.get_by_id_with_users(request_id)
    if not request_data:
        from ...core.errors import ResourceNotFoundError
        raise ResourceNotFoundError("Request", f"Request {request_id} not found")
        
    return Request.model_validate(request_data.to_dict())

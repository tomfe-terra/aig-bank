"""API Key management endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.deps import get_current_user
from ...core.db import get_db
from ...core.errors import ErrorCode
from ...schemas.api_key_schemas import (
    APIKeyCreate,
    APIKeyList,
    APIKeyRead,
    APIKeySecretRead,
    APIKeyUpdate,
)
from ...schemas.general import Message
from ...services.api_key_service import APIKeyService

router = APIRouter(prefix="/users", tags=["API Keys"])


@router.post(
    "/api-keys",
    response_model=APIKeySecretRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create API Key",
    description="""Create a new API key for the authenticated user.

The response includes the API key ID and secret. **Store the secret securely as it will not be returned again.**""",
    responses={
        status.HTTP_201_CREATED: {
            "model": APIKeySecretRead,
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
                                "details": "Name: Name must be 1-100 characters, alphanumeric with spaces, underscores and hyphens only",
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
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIKeySecretRead:
    """Create a new API key for the current user.

    Args:
        api_key_data: API key creation data including name
        current_user: Authenticated user context
        db: Database session

    Returns:
        APIKeySecretRead: Created API key with client_id and secret
    """
    api_key_service = APIKeyService(db)
    return await api_key_service.create_api_key(
        user_id=current_user["user_id"],
        request=api_key_data,
    )


@router.get(
    "/api-keys",
    response_model=APIKeyList,
    summary="List API Keys",
    description="""List API keys for the authenticated user.

By default, only active API keys are returned. Set `include_revoked=true` to also include revoked keys.""",
    responses={
        status.HTTP_200_OK: {
            "model": APIKeyList,
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
async def list_api_keys(
    include_revoked: bool | None = False,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIKeyList:
    """List API keys for the current user.

    Args:
        include_revoked: Whether to include revoked (inactive) keys in the response
        current_user: Authenticated user context
        db: Database session

    Returns:
        APIKeyList: List of API keys with total count
    """
    api_key_service = APIKeyService(db)

    api_keys, count = await api_key_service.list_api_keys_for_user(
        user_id=current_user["user_id"],
        active_only=not include_revoked,
    )

    return APIKeyList(
        api_keys=api_keys,
        total=count,
    )


@router.patch(
    "/api-keys/{api_key_id}",
    response_model=APIKeyRead,
    summary="Update API Key",
    description="""Update an API key's name for the authenticated user.

Only the name can be updated. The client_id and secret cannot be changed.""",
    responses={
        status.HTTP_200_OK: {
            "model": APIKeyRead,
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
                                "details": "Name: Name must be 1-100 characters, alphanumeric with spaces, underscores and hyphens only",
                                "request_id": "938304120f4492de",
                            },
                        },
                        "resource_not_found": {
                            "summary": "API key not found",
                            "value": {
                                "error": ErrorCode.RESOURCE_NOT_FOUND.value,
                                "details": "API key not found",
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
async def update_api_key(
    api_key_id: str,
    api_key_data: APIKeyUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIKeyRead:
    """Update an API key's name.

    Args:
        api_key_id: API key ID to update
        api_key_data: Update data with new name
        current_user: Authenticated user context
        db: Database session

    Returns:
        APIKeyRead: Updated API key
    """
    api_key_service = APIKeyService(db)
    updated_key = await api_key_service.update_api_key(
        api_key_id=api_key_id,
        user_id=current_user["user_id"],
        request=api_key_data,
    )

    return APIKeyRead.model_validate(updated_key)


@router.delete(
    "/api-keys/{api_key_id}",
    response_model=Message,
    summary="Revoke API Key",
    description="""Revoke (deactivate) an API key for the authenticated user.

**Note:** This is a soft delete - the API key is marked as inactive but not permanently removed.""",
    responses={
        status.HTTP_200_OK: {
            "model": Message,
            "description": "Success",
            "content": {
                "application/json": {
                    "examples": {
                        "api_key_revoked": {
                            "summary": "API key revoked successfully",
                            "value": {
                                "message": "API key revoked successfully",
                                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
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
                            "summary": "API key not found",
                            "value": {
                                "error": ErrorCode.RESOURCE_NOT_FOUND.value,
                                "details": "API key not found",
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
async def revoke_api_key(
    api_key_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Message:
    """Revoke an API key by ID.

    Args:
        api_key_id: API key ID to revoke
        current_user: Authenticated user context
        db: Database session

    Returns:
        Message: Success message with revoked API key ID
    """
    api_key_service = APIKeyService(db)
    await api_key_service.revoke_api_key(
        api_key_id=api_key_id,
        user_id=current_user["user_id"],
    )

    return Message(message="API key revoked successfully", id=api_key_id)

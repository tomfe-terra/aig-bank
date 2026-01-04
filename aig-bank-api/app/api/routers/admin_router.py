"""Admin API endpoints (requires ADMIN role authentication)."""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Response, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db import get_db
from ...core.errors import ErrorCode
from ...schemas.admin_schemas import (
    BankCapitalBalance,
    LogFileContent,
    LogFileDownloadRequest,
    LogFileList,
    TokenBlacklist,
    UserList,
    UserRoleUpdate,
    UserRoleUpdateResult,
    UserUnlockResult,
)
from ...services.admin_service import AdminService
from ...services.user_service import UserService
from ..deps import require_admin_role

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get(
    "/users",
    response_model=UserList,
    status_code=status.HTTP_200_OK,
    summary="List All Users",
    description="""List all users in the system with pagination.

Admins can view all registered users including their roles and status for user management purposes.""",
    responses={
        status.HTTP_200_OK: {
            "model": UserList,
            "description": "Success",
            "content": {
                "application/json": {
                    "examples": {
                        "users_list": {
                            "summary": "List of users",
                            "value": {
                                "users": [
                                    {
                                        "id": "550e8400-e29b-41d4-a716-446655440000",
                                        "username": "johndoe",
                                        "email": "john.doe@example.com",
                                        "role": "USER",
                                        "status": "ENABLED",
                                        "is_locked": False,
                                        "has_avatar": True,
                                        "avatar_url": "/api/v1/admin/users/550e8400-e29b-41d4-a716-446655440000/avatar",
                                        "created_at": "2025-01-01T00:00:00Z",
                                    },
                                    {
                                        "id": "660e8400-e29b-41d4-a716-446655440001",
                                        "username": "jane.banker",
                                        "email": "jane.banker@bank.com",
                                        "role": "BANKER",
                                        "status": "ENABLED",
                                        "is_locked": False,
                                        "has_avatar": False,
                                        "avatar_url": None,
                                        "created_at": "2025-01-02T00:00:00Z",
                                    },
                                ],
                                "total": 2,
                                "limit": 50,
                                "offset": 0,
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
                                "details": "Insufficient permissions: ADMIN role required",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def list_users(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of users to return"),
    offset: int = Query(0, ge=0, description="Number of users to skip"),
    current_user: dict = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
) -> UserList:
    """List all users with pagination.

    Args:
        limit: Maximum number of users to return
        offset: Number of users to skip
        current_user: Authenticated admin context
        db: Database session

    Returns:
        UserList: Paginated list of users
    """
    admin_service = AdminService(db)
    return await admin_service.list_users(limit=limit, offset=offset)


@router.get(
    "/users/{user_id}/avatar",
    status_code=status.HTTP_200_OK,
    summary="Get User Avatar",
    description="""Get a user's avatar image by user ID.

Returns the avatar as a WebP image. Requires ADMIN role authentication.""",
    responses={
        status.HTTP_200_OK: {
            "description": "Avatar image",
            "content": {
                "image/webp": {
                    "example": "<binary image data>",
                },
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "No avatar",
            "content": {
                "application/json": {
                    "examples": {
                        "no_avatar": {
                            "summary": "User has no avatar",
                            "value": {
                                "error": ErrorCode.RESOURCE_NOT_FOUND.value,
                                "details": "User 550e8400-e29b-41d4-a716-446655440000 has no avatar",
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
                                "details": "Insufficient permissions: ADMIN role required",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def get_user_avatar(
    user_id: UUID,
    current_user: dict = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Get a user's avatar by user ID.

    Args:
        user_id: User ID to get avatar for
        current_user: Authenticated admin context
        db: Database session

    Returns:
        Response: Avatar image with WebP content-type
    """
    user_service = UserService(db)
    avatar_bytes = await user_service.get_avatar(str(user_id))

    return Response(
        content=avatar_bytes,
        media_type="image/webp",
        headers={
            "Cache-Control": "private, max-age=3600",
            "Content-Disposition": f'inline; filename="avatar-{user_id}.webp"',
        },
    )


@router.patch(
    "/users/{user_id}/role",
    response_model=UserRoleUpdateResult,
    status_code=status.HTTP_200_OK,
    summary="Update User Role",
    description="""Update a user's role.

Admins can change user roles between USER, BANKER, and ADMIN. Cannot change own role to prevent lockout.""",
    responses={
        status.HTTP_200_OK: {
            "model": UserRoleUpdateResult,
            "description": "Success",
            "content": {
                "application/json": {
                    "examples": {
                        "role_updated": {
                            "summary": "User role updated",
                            "value": {
                                "message": "User role updated to BANKER",
                                "user": {
                                    "id": "550e8400-e29b-41d4-a716-446655440000",
                                    "username": "johndoe",
                                    "email": "john.doe@example.com",
                                    "role": "BANKER",
                                    "status": "ENABLED",
                                    "has_avatar": True,
                                    "avatar_url": "/api/v1/admin/users/550e8400-e29b-41d4-a716-446655440000/avatar",
                                    "created_at": "2025-01-01T00:00:00Z",
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
                        "cannot_change_own_role": {
                            "summary": "Cannot change own role",
                            "value": {
                                "error": ErrorCode.INVALID_DATA.value,
                                "details": "Cannot change your own role",
                                "request_id": "938304120f4492de",
                            },
                        },
                        "user_not_found": {
                            "summary": "User not found",
                            "value": {
                                "error": ErrorCode.RESOURCE_NOT_FOUND.value,
                                "details": "User not found",
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
                                "details": "Insufficient permissions: ADMIN role required",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def update_user_role(
    user_id: UUID,
    role_update: UserRoleUpdate,
    current_user: dict = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
) -> UserRoleUpdateResult:
    """Update a user's role.

    Args:
        user_id: User ID to update
        role_update: New role data
        current_user: Authenticated admin context
        db: Database session

    Returns:
        UserRoleUpdateResult: Update result with user info
    """
    admin_service = AdminService(db)
    return await admin_service.update_user_role(
        target_user_id=user_id,
        new_role=role_update.role,
        admin_user_id=UUID(current_user["user_id"]),
    )


@router.post(
    "/users/{user_id}/unlock",
    response_model=UserUnlockResult,
    status_code=status.HTTP_200_OK,
    summary="Unlock User Account",
    description="""Unlock a user account by resetting failed login attempts.

This endpoint resets the failed_login_attempts counter and clears the locked_until timestamp,
allowing the user to log in again. Useful when a user has been locked out due to too many
failed authentication attempts.""",
    responses={
        status.HTTP_200_OK: {
            "model": UserUnlockResult,
            "description": "Success",
            "content": {
                "application/json": {
                    "examples": {
                        "user_unlocked": {
                            "summary": "User account unlocked",
                            "value": {
                                "message": "User account unlocked successfully",
                                "id": "938304120f4492de",
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
                        "cannot_unlock_own_account": {
                            "summary": "Cannot unlock own account",
                            "value": {
                                "error": ErrorCode.INVALID_DATA.value,
                                "details": "An admin cannot unlock their own account.",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "examples": {
                        "user_not_found": {
                            "summary": "User not found",
                            "value": {
                                "error": ErrorCode.RESOURCE_NOT_FOUND.value,
                                "details": "User 550e8400-e29b-41d4-a716-446655440000 not found",
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
                                "details": "Insufficient permissions: ADMIN role required",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def unlock_user(
    user_id: UUID,
    current_user: dict = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
) -> UserUnlockResult:
    """Unlock a user account by resetting failed login attempts.

    Args:
        user_id: User ID to unlock
        current_user: Authenticated admin context
        db: Database session

    Returns:
        UserUnlockResult: Unlock result with user info
    """
    admin_service = AdminService(db)
    return await admin_service.unlock_user(
        target_user_id=user_id,
        admin_user_id=UUID(current_user["user_id"]),
    )


@router.get(
    "/bank/capital",
    response_model=BankCapitalBalance,
    status_code=status.HTTP_200_OK,
    summary="Get Bank Capital Balance",
    description="""Get the bank's capital account balance.

Admins can monitor the bank's capital account to track overall financial health.""",
    responses={
        status.HTTP_200_OK: {
            "model": BankCapitalBalance,
            "description": "Success",
            "content": {
                "application/json": {
                    "examples": {
                        "capital_balance": {
                            "summary": "Bank capital balance",
                            "value": {
                                "account_number": "BANK-CAPITAL-001",
                                "balance_cents": 1000000000,
                                "balance_dollars": 10000000.0,
                                "updated_at": "2025-01-01T00:00:00Z",
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
                                "details": "Insufficient permissions: ADMIN role required",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def get_bank_capital_balance(
    current_user: dict = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
) -> BankCapitalBalance:
    """Get bank capital account balance.

    Args:
        current_user: Authenticated admin context
        db: Database session

    Returns:
        BankCapitalBalance: Bank capital account information
    """
    admin_service = AdminService(db)
    return await admin_service.get_bank_capital_balance()


@router.get(
    "/logs/files",
    response_model=LogFileList,
    status_code=status.HTTP_200_OK,
    summary="List Log Files",
    description="""List all log files in the logs directory.

Admins can view available log files including their sizes and modification timestamps.""",
    responses={
        status.HTTP_200_OK: {
            "model": LogFileList,
            "description": "Success",
            "content": {
                "application/json": {
                    "examples": {
                        "log_files": {
                            "summary": "List of log files",
                            "value": {
                                "files": [
                                    {
                                        "filename": "info.log",
                                        "size_bytes": 1048576,
                                        "modified_at": "2025-01-01T00:00:00Z",
                                    },
                                    {
                                        "filename": "error.log",
                                        "size_bytes": 524288,
                                        "modified_at": "2025-01-01T00:00:00Z",
                                    },
                                    {
                                        "filename": "access.log",
                                        "size_bytes": 2097152,
                                        "modified_at": "2025-01-01T00:00:00Z",
                                    },
                                ],
                                "total": 3,
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
                                "details": "Insufficient permissions: ADMIN role required",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def list_log_files(
    current_user: dict = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
) -> LogFileList:
    """List all log files.

    Args:
        current_user: Authenticated admin context
        db: Database session

    Returns:
        LogFileList: List of log files with metadata
    """
    admin_service = AdminService(db)
    return admin_service.list_log_files()


@router.get(
    "/logs/content",
    response_model=LogFileContent,
    status_code=status.HTTP_200_OK,
    summary="Get Info Log Content",
    description="""Get parsed content from the info.log file.

Returns the last N lines from the info.log file. This endpoint always reads from info.log for security.

Security: Only the info.log file can be accessed through this endpoint.""",
    responses={
        status.HTTP_200_OK: {
            "description": "Success",
            "content": {
                "application/json": {
                    "examples": {
                        "log_content": {
                            "summary": "Parsed log content",
                            "value": {
                                "filename": "info.log",
                                "lines": [
                                    "2025-01-01 00:00:00,000 - INFO - Application started",
                                    "2025-01-01 00:01:00,000 - INFO - User logged in",
                                    "2025-01-01 00:02:00,000 - INFO - Transaction processed",
                                ],
                                "total_lines": 10000,
                                "returned_lines": 1000,
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
                        "file_not_found": {
                            "summary": "File not found",
                            "value": {
                                "error": ErrorCode.RESOURCE_NOT_FOUND.value,
                                "details": "Log file not found",
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
                                "details": "Insufficient permissions: ADMIN role required",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def get_log_content(
    max_lines: int = Query(1000, ge=1, le=10000, description="Maximum number of lines to return"),
    current_user: dict = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Get parsed info.log content.

    Args:
        max_lines: Maximum number of lines to return
        current_user: Authenticated admin context
        db: Database session

    Returns:
        LogFileContent: Parsed log file content from info.log
    """
    admin_service = AdminService(db)
    return admin_service.get_log_file_content("info.log", max_lines)


@router.post(
    "/logs/download",
    status_code=status.HTTP_200_OK,
    summary="Download Log File",
    description="""Download a raw log file.

Downloads any log file from the logs directory as plain text.

Security: Only files in the logs directory can be accessed. Path traversal is prevented.""",
    responses={
        status.HTTP_200_OK: {
            "description": "Success",
            "content": {
                "text/plain": {
                    "example": "2025-01-01 00:00:00,000 - INFO - Application started\n2025-01-01 00:01:00,000 - INFO - User logged in\n",
                },
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_filename": {
                            "summary": "Invalid filename",
                            "value": {
                                "error": ErrorCode.VALIDATION_ERROR.value,
                                "details": "Filename cannot contain parent directory references",
                                "request_id": "938304120f4492de",
                            },
                        },
                        "file_not_found": {
                            "summary": "File not found",
                            "value": {
                                "error": ErrorCode.RESOURCE_NOT_FOUND.value,
                                "details": "Log file not found",
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
                                "details": "Insufficient permissions: ADMIN role required",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def download_log_file(
    request: LogFileDownloadRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Download raw log file.

    Args:
        request: Log file download request with filename
        background_tasks: Background tasks for cleanup
        current_user: Authenticated admin context
        db: Database session

    Returns:
        FileResponse: Raw log file download
    """
    admin_service = AdminService(db)
    file_path, cleanup_callback = admin_service.download_log_file(request.filename)

    background_tasks.add_task(cleanup_callback)

    return FileResponse(
        path=str(file_path),
        filename=request.filename,
        media_type="text/plain",
    )


@router.get(
    "/settings",
    status_code=status.HTTP_200_OK,
    summary="Get Application Settings",
    description="""Get all application configuration settings.

This endpoint displays all configuration values for the application.
Useful for debugging and monitoring purposes.""",
    responses={
        status.HTTP_200_OK: {
            "description": "Success",
            "content": {
                "application/json": {
                    "examples": {
                        "settings": {
                            "summary": "Application settings",
                            "value": {
                                "app_name": "AIG Bank API",
                                "debug": False,
                                "host": "127.0.0.1",
                                "port": 8000,
                                "log_level": "INFO",
                                "logs_directory": "logs",
                                "jwt_expiration_minutes": 60,
                                "jwt_refresh_expiration_days": 30,
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
                                "details": "Insufficient permissions: ADMIN role required",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def get_settings(
    current_user: dict = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get application settings.

    Args:
        current_user: Authenticated admin context
        db: Database session

    Returns:
        dict: All application configuration settings
    """
    admin_service = AdminService(db)
    return admin_service.get_application_settings()


@router.get(
    "/token-blacklist",
    response_model=TokenBlacklist,
    status_code=status.HTTP_200_OK,
    summary="Get Token Blacklist",
    description="""Get all blacklisted tokens.

This endpoint shows all tokens that have been revoked/blacklisted
and can no longer be used for authentication.""",
    responses={
        status.HTTP_200_OK: {
            "description": "Success",
            "content": {
                "application/json": {
                    "examples": {
                        "blacklist": {
                            "summary": "Token blacklist",
                            "value": {
                                "blacklisted_tokens": [
                                    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                                    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                                ],
                                "count": 2,
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
                                "details": "Insufficient permissions: ADMIN role required",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def get_token_blacklist(
    current_user: dict = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
) -> TokenBlacklist:
    """Get all blacklisted tokens.

    Args:
        current_user: Authenticated admin context
        db: Database session

    Returns:
        TokenBlacklist: Blacklisted tokens and count
    """
    admin_service = AdminService(db)
    return admin_service.get_token_blacklist()

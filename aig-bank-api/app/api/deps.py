"""API dependencies for authentication and authorization.

This module provides FastAPI dependencies for handling authentication and authorization
across the bank API. It supports multiple authentication methods:

1. OAuth2 Bearer tokens (primary method) - enables Swagger UI "Authorize" button
2. HMAC signature authentication (for API keys)

The module follows security best practices including:
- Token validation and blacklist checking
- User account status verification
- Role-based access control
- Proper error handling and logging

All authentication logic is delegated to the AuthService for consistency.
"""

from fastapi import Depends, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_db
from ..core.enums import UserRole
from ..core.errors import (
    InsufficientPermissionsError,
)
from ..services.auth_service import AuthService

bearer_scheme = HTTPBearer(
    scheme_name="Bearer",
    description="""
**JWT Bearer Token Authentication**

Authenticate using an access token from the login endpoint. Login requires username, password, and OTP code.

Enter your token below (without "Bearer" prefix).
    """,
    auto_error=False,
)


async def get_current_user(
    request: Request,
    credentials=Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Authenticate current user using multiple methods in order of preference.

    Authentication methods attempted in order:
    1. JWT Bearer token (Authorization header)
    2. HMAC signature (X-AGI-AUTH-ID + X-AGI-AUTH-SECRET headers)

    This follows a fallback pattern where each method is tried until one succeeds.
    If all methods fail, an UnauthorizedError is raised.

    All authentication logic is delegated to the AuthService.

    Args:
        request: FastAPI Request object
        credentials: Bearer token credentials from Authorization header
        db: Database session

    Returns:
        Dictionary containing authenticated user information

    Raises:
        UnauthorizedError: If no valid authentication method succeeds
    """
    auth_service = AuthService(db)

    bearer_token = credentials.credentials if credentials else None

    return await auth_service.authenticate_request(request, bearer_token)


async def require_banker_role(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Dependency that requires the current user to have BANKER or ADMIN role.

    This enforces role-based access control at the endpoint level.
    Users with BANKER or ADMIN role are allowed to access endpoints using this dependency.
    Admins have access to all banker functionality.

    Args:
        current_user: User context dictionary from authentication

    Returns:
        User context dictionary if role is valid

    Raises:
        InsufficientPermissionsError: If user doesn't have BANKER or ADMIN role
    """
    user_role = current_user.get("role")

    if user_role not in [UserRole.BANKER.value, UserRole.ADMIN.value]:
        raise InsufficientPermissionsError(required_role=UserRole.BANKER.value)

    return current_user


async def require_admin_role(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Require ADMIN role for access.

    Validates that the authenticated user has ADMIN role permissions.

    Args:
        current_user: User context dictionary from authentication

    Returns:
        User context dictionary if role is valid

    Raises:
        InsufficientPermissionsError: If user doesn't have ADMIN role
    """
    user_role = current_user.get("role")

    if user_role != UserRole.ADMIN.value:
        raise InsufficientPermissionsError(required_role=UserRole.ADMIN.value)

    return current_user

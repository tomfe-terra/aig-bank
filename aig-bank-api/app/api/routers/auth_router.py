"""Authentication endpoints."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.deps import get_current_user
from ...core.db import get_db
from ...core.errors import ErrorCode
from ...schemas.auth_schemas import (
    AccessToken,
    Login,
    Logout,
    LogoutConfirmation,
    PasswordResetConfirmation,
    PasswordResetWithAnswers,
    ProfileRead,
    RefreshToken,
    SecurityQuestions,
    SecurityQuestionsLookup,
    TokenPair,
)
from ...services.auth_service import AuthService

router = APIRouter(prefix="/users/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=TokenPair,
    status_code=status.HTTP_200_OK,
    summary="Authenticate User",
    description="""Authenticate a user with username, password, and OTP code.""",
    responses={
        status.HTTP_200_OK: {
            "model": TokenPair,
            "description": "Success",
            "content": {
                "application/json": {
                    "examples": {
                        "authenticated": {
                            "summary": "Successfully authenticated",
                            "value": {
                                "access_token": (
                                    "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9."
                                    "eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJyb2xlIjoiVVNFUiIsImV4cCI6MTczNTc0NzIwMH0."
                                    "abcdef123456"
                                ),
                                "access_token_expires_at": "2025-12-02T12:00:00Z",
                                "refresh_token": (
                                    "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9."
                                    "eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJ0eXBlIjoicmVmcmVzaCIsImV4cCI6MTczNjM1MjAwMH0."
                                    "xyz789"
                                ),
                                "refresh_token_expires_at": "2026-01-01T12:00:00Z",
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
                        "validation_error": {
                            "summary": "Validation error",
                            "value": {
                                "error": ErrorCode.VALIDATION_ERROR.value,
                                "details": "OTP code must be exactly 6 digits",
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
                        "invalid_credentials": {
                            "summary": "Invalid username, password, or OTP",
                            "value": {
                                "error": ErrorCode.INVALID_CREDENTIALS.value,
                                "details": "Incorrect username, password, or OTP code",
                                "request_id": "938304120f4492de",
                            },
                        },
                        "account_locked": {
                            "summary": "Account locked",
                            "value": {
                                "error": ErrorCode.ACCOUNT_LOCKED.value,
                                "details": "Account is locked due to security policy. Please try again later or contact support.",
                                "request_id": "938304120f4492de",
                            },
                        },
                        "account_disabled": {
                            "summary": "Account disabled",
                            "value": {
                                "error": ErrorCode.ACCOUNT_DISABLED.value,
                                "details": "Account has been disabled",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def login(login_data: Login, db: AsyncSession = Depends(get_db)) -> TokenPair:
    """Authenticate user and return access and refresh tokens.

    Args:
        login_data: Login credentials (username, password, and OTP)
        db: Database session

    Returns:
        TokenPair: Access token, refresh token, and expiration timestamps for both
    """
    auth_service = AuthService(db)
    return await auth_service.authenticate_user(login_data)


@router.post(
    "/refresh",
    response_model=AccessToken,
    status_code=status.HTTP_200_OK,
    summary="Refresh Access Token",
    description="""Refresh an expired access token using a valid refresh token.

The refresh token must be provided in the request body.
Returns a new access token for continued API access.
""",
    responses={
        status.HTTP_200_OK: {
            "model": AccessToken,
            "description": "Success",
            "content": {
                "application/json": {
                    "examples": {
                        "token_refreshed": {
                            "summary": "Token refreshed successfully",
                            "value": {
                                "access_token": (
                                    "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9."
                                    "eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJyb2xlIjoiVVNFUiIsImV4cCI6MTczNTc0NzIwMH0."
                                    "abcdef123456"
                                ),
                                "access_token_expires_at": "2025-12-02T12:00:00Z",
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
                        "invalid_token": {
                            "summary": "Invalid or revoked token",
                            "value": {
                                "error": ErrorCode.INVALID_TOKEN.value,
                                "details": "Invalid token type",
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
async def refresh_token(
    refresh_data: RefreshToken,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AccessToken:
    """Refresh access token using refresh token.

    Args:
        refresh_data: Refresh token data
        current_user: Authenticated user context
        db: Database session

    Returns:
        AccessToken: New access token and expiration timestamp
    """
    auth_service = AuthService(db)
    return await auth_service.refresh_access_token(refresh_data)


@router.post(
    "/logout",
    response_model=LogoutConfirmation,
    status_code=status.HTTP_200_OK,
    summary="Logout User",
    description="""Logout the current user session.

Blacklists the current access token and optionally blacklists the provided refresh token.
This ensures both tokens cannot be used for future authentication, providing enhanced security.
""",
    responses={
        status.HTTP_200_OK: {
            "model": LogoutConfirmation,
            "description": "Success",
            "content": {
                "application/json": {
                    "examples": {
                        "logged_out": {
                            "summary": "Successfully logged out",
                            "value": {"message": "Successfully logged out"},
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
async def logout(
    logout_data: Logout,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LogoutConfirmation:
    """Logout user by blacklisting their access token.

    Args:
        logout_data: Logout data with optional refresh token
        request: HTTP request object
        current_user: Authenticated user context
        db: Database session

    Returns:
        LogoutConfirmation: Confirmation message
    """
    auth_service = AuthService(db)
    return await auth_service.logout_user(request, logout_data.refresh_token)


@router.get(
    "/me",
    response_model=ProfileRead,
    status_code=status.HTTP_200_OK,
    summary="Get Current User Profile",
    description="""Retrieve the profile information for the currently authenticated user.""",
    responses={
        status.HTTP_200_OK: {
            "model": ProfileRead,
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
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileRead:
    """Get current user profile information.

    Args:
        current_user: Authenticated user context
        db: Database session

    Returns:
        ProfileRead: Complete user profile including accounts and API keys
    """
    auth_service = AuthService(db)
    user_id = current_user["user"].id
    return await auth_service.get_user_profile(user_id)


@router.post(
    "/password-reset/security-questions",
    response_model=SecurityQuestions,
    status_code=status.HTTP_200_OK,
    summary="Get Security Questions for Password Reset",
    description="""Get security questions for a user account.

Provide your username to retrieve your security questions.
You will need to answer all 3 questions correctly to reset your password.
""",
    responses={
        status.HTTP_200_OK: {
            "model": SecurityQuestions,
            "description": "Security questions retrieved",
            "content": {
                "application/json": {
                    "examples": {
                        "questions_retrieved": {
                            "summary": "Security questions retrieved",
                            "value": {
                                "questions": [
                                    "What was the name of your first pet?",
                                    "What city were you born in?",
                                    "What is your mother's maiden name?",
                                ],
                                "message": "Please answer all security questions to reset your password",
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
                        "validation_error": {
                            "summary": "Validation error",
                            "value": {
                                "error": ErrorCode.VALIDATION_ERROR.value,
                                "details": "Username: Username must be 3-50 characters, alphanumeric with underscores and hyphens only",
                                "request_id": "938304120f4492de",
                            },
                        },
                        "security_questions_not_available": {
                            "summary": "Security questions not available",
                            "value": {
                                "error": ErrorCode.SECURITY_QUESTIONS_NOT_AVAILABLE.value,
                                "details": "Security questions not available for this account",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def get_security_questions_for_reset(
    request: SecurityQuestionsLookup,
    db: AsyncSession = Depends(get_db),
) -> SecurityQuestions:
    """Get security questions for password reset.

    Args:
        request: Username lookup
        db: Database session

    Returns:
        SecurityQuestions: List of security questions
    """
    auth_service = AuthService(db)
    return await auth_service.get_security_questions_for_reset(request.username)


@router.post(
    "/password-reset/security-answers",
    response_model=PasswordResetConfirmation,
    status_code=status.HTTP_200_OK,
    summary="Reset Password with Security Answers",
    description="""Reset your password using security question answers.

Provide your username, answers to all 3 security questions, and your new password.
If all answers are correct, your password will be reset immediately.
""",
    responses={
        status.HTTP_200_OK: {
            "model": PasswordResetConfirmation,
            "description": "Success",
            "content": {
                "application/json": {
                    "examples": {
                        "password_reset": {
                            "summary": "Password reset successfully",
                            "value": {"message": "Password has been successfully reset"},
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
                        "validation_error": {
                            "summary": "Validation error",
                            "value": {
                                "error": ErrorCode.VALIDATION_ERROR.value,
                                "details": "Username: Username must be 3-50 characters, alphanumeric with underscores and hyphens only",
                                "request_id": "938304120f4492de",
                            },
                        },
                        "password_policy_error": {
                            "summary": "Password policy error",
                            "value": {
                                "error": ErrorCode.PASSWORD_POLICY_ERROR.value,
                                "details": "Password must be at least 8 characters long",
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
                        "invalid_credentials": {
                            "summary": "Invalid credentials",
                            "value": {
                                "error": ErrorCode.INVALID_CREDENTIALS.value,
                                "details": "Invalid username or incorrect answers",
                                "request_id": "938304120f4492de",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def reset_password_with_security_answers(
    request: PasswordResetWithAnswers,
    db: AsyncSession = Depends(get_db),
) -> PasswordResetConfirmation:
    """Reset password using security question answers.

    Args:
        request: Password reset data with username, answers, and new password
        db: Database session

    Returns:
        PasswordResetConfirmation: Success confirmation
    """
    auth_service = AuthService(db)
    await auth_service.reset_password_with_security_answers(
        request.username,
        request.answers,
        request.new_password,
    )

    return PasswordResetConfirmation(message="Password has been successfully reset")

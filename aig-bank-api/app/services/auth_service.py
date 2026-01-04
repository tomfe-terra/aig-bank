"""Authentication service for user authentication operations.

This service handles all authentication-related operations including:
- User login/logout with username and password
- JWT token verification and validation
- Token refresh operations
- Cookie management
- Token blacklisting
- User identity verification
"""

from datetime import UTC, datetime, timedelta
import logging

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.constants import SECURITY_QUESTIONS
from ..core.enums import UserStatus
from ..core.errors import (
    AccountDisabledError,
    AccountLockedError,
    AuthenticationRequiredError,
    InvalidCredentialsError,
    InvalidTokenError,
    SecurityQuestionsNotAvailableError,
)
from ..repos.account_repository import AccountRepository
from ..repos.api_key_repository import APIKeyRepository
from ..repos.user_repository import UserRepository
from ..schemas.account_schemas import AccountRead
from ..schemas.api_key_schemas import APIKeyRead
from ..schemas.auth_schemas import (
    AccessToken,
    Login,
    LogoutConfirmation,
    ProfileRead,
    RefreshToken,
    SecurityQuestions,
    TokenPair,
)
from ..schemas.user_schemas import UserRead
from ..utils.hmac_auth import HMACAuthenticator
from ..utils.jwt import JWTManager
from ..utils.otp import otp_manager
from ..utils.password import PasswordManager
from ..utils.token_blacklist import token_blacklist
from .base_service import BaseService

logger = logging.getLogger(__name__)


class AuthService(BaseService):
    """Service for authentication operations.

    This service is the single source of truth for all authentication operations.
    It handles user authentication, token management, and identity verification.
    """

    def __init__(self, session: AsyncSession):
        """Initialize service with database session and repository."""
        super().__init__(session)
        self.user_repo = UserRepository(session)

        self.account_repo = AccountRepository(session)
        self.api_key_repo = APIKeyRepository(session)

    async def authenticate_user(self, request: Login) -> TokenPair:
        """Authenticate user with username, password, and OTP (2FA).

        Implements automatic account lockout mechanism:
        - Tracks failed login attempts
        - Locks account after max failed attempts
        - Resets counter on successful login
        - Auto-unlocks after lockout duration expires
        - Requires valid OTP code for 2FA
        """
        user = await self.user_repo.get_by_username(request.username)
        if not user:
            raise InvalidCredentialsError("Incorrect username, password, or OTP code")

        if user.is_disabled:
            raise AccountDisabledError()

        if user.locked_until and not user.is_locked:
            user.reset_failed_attempts()
            await self.user_repo.update(user)

        if user.is_locked:
            raise AccountLockedError()

        if not PasswordManager.verify_password(request.password, str(user.password_hash)):
            await self.user_repo.record_failed_login_attempt(user)

            raise InvalidCredentialsError("Incorrect username, password, or OTP code")

        if not otp_manager.verify_otp(str(user.otp_secret), request.otp_code):
            await self.user_repo.record_failed_login_attempt(user)

            raise InvalidCredentialsError("Incorrect username, password, or OTP code")

        if user.failed_login_attempts > 0:
            user.reset_failed_attempts()

        user.update_last_login()
        await self.user_repo.update(user)

        access_token, refresh_token = JWTManager.create_token_pair(subject=str(user.id), role=str(user.role))

        now = datetime.now(tz=UTC)
        access_expires_at = now + timedelta(minutes=settings.jwt_expiration_minutes)
        refresh_expires_at = now + timedelta(days=settings.jwt_refresh_expiration_days)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            access_token_expires_at=access_expires_at,
            refresh_token_expires_at=refresh_expires_at,
        )

    async def refresh_access_token(self, request: RefreshToken) -> AccessToken:
        """Refresh access token using refresh token."""
        payload = JWTManager.decode_token(request.refresh_token)

        if payload.get("type") != "refresh":
            raise InvalidTokenError("Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenError("Invalid token payload")

        if token_blacklist.is_blacklisted(request.refresh_token):
            raise InvalidTokenError("Refresh token has been revoked")

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise InvalidTokenError("User not found")

        access_token = JWTManager.create_access_token(subject=str(user.id), role=str(user.role))

        now = datetime.now(tz=UTC)
        access_expires_at = now + timedelta(minutes=settings.jwt_expiration_minutes)

        return AccessToken(
            access_token=access_token,
            access_token_expires_at=access_expires_at,
        )

    async def logout_user(self, request: Request, refresh_token: str | None = None) -> LogoutConfirmation:
        """Logout user by invalidating access and refresh tokens.

        Args:
            request: FastAPI Request object to extract access token from
            refresh_token: Optional refresh token to blacklist

        Returns:
            LogoutConfirmation
        """
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            access_token = auth_header[7:]
            if access_token:
                try:
                    payload = JWTManager.decode_token(access_token)
                    if payload.get("type") == "access":
                        token_blacklist.add_token(access_token)
                except Exception:
                    pass

        if refresh_token:
            try:
                payload = JWTManager.decode_token(refresh_token)
                if payload.get("type") == "refresh":
                    token_blacklist.add_token(refresh_token)
            except Exception:
                pass

        return LogoutConfirmation()

    async def verify_jwt_token_and_get_user(self, token: str) -> dict:
        """Verify JWT token and return user information.

        This method performs the following validations:
        1. Token signature and expiration verification
        2. Token blacklist checking for revoked tokens
        3. User existence and active status verification

        Args:
            token: JWT token string

        Returns:
            Dictionary containing user information and metadata

        Raises:
            InvalidTokenError: If token is invalid, blacklisted, or user is inactive
        """
        payload = JWTManager.decode_token(token)

        token_type = payload.get("type")
        if token_type in ["access", "refresh"] and token_blacklist.is_blacklisted(token):
            raise InvalidTokenError("Token has been revoked")

        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenError("Token missing user ID")

        user = await self.user_repo.get_by_id(user_id)

        if not user:
            raise InvalidTokenError("User not found")

        if not user.status == UserStatus.ENABLED:
            raise InvalidTokenError("User account is deactivated")

        return {
            "user": user,
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }

    async def authenticate_request(self, request: Request, bearer_token: str | None = None) -> dict:
        """Authenticate request using multiple methods in order of preference.

        Authentication methods attempted in order:
        1. JWT Bearer token (Authorization header via OAuth2)
        2. HMAC signature (X-AGI-AUTH-ID + X-AGI-AUTH-SECRET headers)

        Note: Cookie authentication has been removed. Use OAuth2 Bearer tokens instead.

        Args:
            request: FastAPI Request object
            bearer_token: Bearer token from Authorization header (optional)

        Returns:
            Dictionary containing authenticated user information

        Raises:
            AuthenticationRequiredError: If no valid authentication method succeeds
        """
        if bearer_token:
            try:
                user_info = await self.verify_jwt_token_and_get_user(bearer_token)
                return user_info
            except (InvalidTokenError, InvalidCredentialsError):
                pass

        api_key_id, _ = HMACAuthenticator.extract_headers(request)
        if api_key_id:
            try:
                api_key = await self.api_key_repo.get_by_api_key_id(api_key_id)
                if api_key and api_key.is_active:
                    try:
                        stored_secret = api_key.decrypt_secret()
                        if stored_secret and await HMACAuthenticator.verify_request(request, stored_secret):
                            user = await self.user_repo.get_by_id(api_key.user_id)
                            if user and user.can_authenticate():
                                api_key.update_last_used()

                                return {
                                    "user": user,
                                    "user_id": str(user.id),
                                    "email": user.email,
                                    "role": user.role,
                                    "first_name": user.first_name,
                                    "last_name": user.last_name,
                                }
                    except Exception:
                        pass
            except Exception:
                pass

        raise AuthenticationRequiredError()

    async def get_user_profile(self, user_id: str) -> ProfileRead:
        """Get comprehensive user profile including user details, account, and API keys.

        Args:
            user_id: User ID to retrieve profile for

        Returns:
            ProfileRead: Comprehensive user profile with user details, account, and API keys
        """
        user = await self.user_repo.get_by_id(user_id)

        account = await self.account_repo.get_by_user_id(user_id)
        api_keys, _ = await self.api_key_repo.get_by_user_id(user_id)

        return ProfileRead(
            user=UserRead.model_validate(user),
            account=AccountRead.model_validate(account) if account else None,
            api_keys=[APIKeyRead.model_validate(api_key) for api_key in api_keys],
        )

    async def get_security_questions_for_reset(self, username: str):
        """Get security questions for a user (for password reset).

        Args:
            username: Username of the account

        Returns:
            SecurityQuestions: Security questions with instructions

        Raises:
            SecurityQuestionsNotAvailableError: If user not found or doesn't have security questions
        """
        user = await self.user_repo.get_by_username(username)

        if not user:
            raise SecurityQuestionsNotAvailableError()

        if not user.has_all_security_questions():
            raise SecurityQuestionsNotAvailableError()

        return SecurityQuestions(
            questions=[
                SECURITY_QUESTIONS.get(user.security_question_1_id, "Unknown question"),
                SECURITY_QUESTIONS.get(user.security_question_2_id, "Unknown question"),
                SECURITY_QUESTIONS.get(user.security_question_3_id, "Unknown question"),
            ]
        )

    async def reset_password_with_security_answers(self, username: str, answers: list[str], new_password: str) -> bool:
        """Reset password using security question answers.

        Args:
            username: Username
            answers: List of 3 answers to security questions
            new_password: New password

        Returns:
            True if successful

        Raises:
            InvalidCredentialsError: If answers are incorrect
        """
        logger.debug(f"reset_password_with_security_answers called for username={username}")

        user = await self.user_repo.get_by_username(username)

        logger.debug(f"User lookup result for username {username}: user={'found' if user else 'NOT FOUND'}")

        if not user:
            logger.error(f"Password reset failed: user not found for username={username}")
            raise InvalidCredentialsError("Invalid username or incorrect answers")

        if not user.has_all_security_questions():
            logger.error(f"Password reset failed: user {username} doesn't have all security questions set")
            raise InvalidCredentialsError("Invalid username or incorrect answers")

        if len(answers) != 3:
            logger.error(f"Password reset failed: expected 3 answers, got {len(answers)}")
            raise InvalidCredentialsError("All 3 security answers are required")

        for i, answer in enumerate(answers, start=1):
            if not user.verify_security_answer(i, answer):
                logger.error(f"Password reset failed: incorrect answer for question {i}")
                raise InvalidCredentialsError("Invalid username or incorrect answers")

        logger.debug(f"All security answers verified for user {username}, proceeding with password reset")

        new_password_hash = PasswordManager.hash_password(new_password)
        user.password_hash = new_password_hash  # type: ignore[assignment]

        if user.failed_login_attempts > 0:
            user.reset_failed_attempts()

        if user.is_locked:
            user.status = UserStatus.ENABLED 

        await self.user_repo.update(user)

        logger.debug(f"Password reset successful for user {username}")

        return True

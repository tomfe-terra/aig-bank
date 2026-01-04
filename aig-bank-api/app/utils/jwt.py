"""JWT token creation and validation utilities."""

from datetime import UTC, datetime, timedelta
import secrets
from typing import Any, TypedDict

from jose import JWTError, jwt

from ..core.config import settings
from ..core.constants import JWT_ALGORITHM
from ..core.errors import InvalidCredentialsError


class TokenPayload(TypedDict):
    """Standard token payload structure."""

    sub: str  # Subject (user ID)
    role: str  # User role
    exp: int  # Expiration timestamp
    iat: int  # Issued at timestamp
    type: str  # Token type ("access" or "refresh")
    jti: str  # JWT ID for token tracking


class JWTManager:
    """JWT token creation and validation utilities."""

    @staticmethod
    def create_access_token(
        subject: str,
        role: str,
        expires_delta: timedelta | None = None,
        token_id: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Create a JWT access token."""
        if expires_delta is None:
            expires_delta = timedelta(minutes=settings.jwt_expiration_minutes)

        expire = datetime.now(UTC) + expires_delta

        if token_id is None:
            token_id = secrets.token_urlsafe(16)

        payload_dict = {
            "sub": subject,
            "role": role,
            "exp": int(expire.timestamp()),
            "iat": int(datetime.now(UTC).timestamp()),
            "type": "access",
            "jti": token_id,
            **kwargs,
        }

        encoded_jwt = jwt.encode(payload_dict, settings.jwt_secret_key, algorithm=JWT_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(
        subject: str,
        role: str,
        expires_delta: timedelta | None = None,
        token_id: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Create a JWT refresh token."""
        if expires_delta is None:
            expires_delta = timedelta(days=settings.jwt_refresh_expiration_days)

        expire = datetime.now(UTC) + expires_delta

        if token_id is None:
            token_id = secrets.token_urlsafe(16)

        payload_dict = {
            "sub": subject,
            "role": role,
            "exp": int(expire.timestamp()),
            "iat": int(datetime.now(UTC).timestamp()),
            "type": "refresh",
            "jti": token_id,
            **kwargs,
        }

        encoded_jwt = jwt.encode(payload_dict, settings.jwt_secret_key, algorithm=JWT_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_token_pair(
        subject: str,
        role: str,
        access_expires_delta: timedelta | None = None,
        refresh_expires_delta: timedelta | None = None,
    ) -> tuple[str, str]:
        """Create both access and refresh tokens."""
        token_id = secrets.token_urlsafe(16)

        access_token = JWTManager.create_access_token(
            subject=subject,
            role=role,
            expires_delta=access_expires_delta,
            token_id=token_id,
        )

        refresh_token = JWTManager.create_refresh_token(
            subject=subject,
            role=role,
            expires_delta=refresh_expires_delta,
            token_id=token_id,
        )

        return access_token, refresh_token

    @staticmethod
    def decode_token(token: str) -> dict[str, Any]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[JWT_ALGORITHM])
            if not all(key in payload for key in ["sub", "role", "exp", "iat", "type", "jti"]):
                raise InvalidCredentialsError("Token missing required fields")
            return payload
        except JWTError as e:
            raise InvalidCredentialsError(f"Invalid token: {e!s}") from e

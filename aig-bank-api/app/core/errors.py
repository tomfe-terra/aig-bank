"""Application-specific exceptions and error handlers."""

from enum import Enum
import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.schemas.general import ErrorResponse

from .config import settings

logger = logging.getLogger(__name__)


class BaseAppError(Exception):
    """Base exception for application errors. Returns 400 Bad Request by default."""

    def __init__(
        self,
        error: str,
        details: str | None = None,
    ):
        """Initialize base application error."""
        super().__init__(details or error)
        self.error = error
        self.details = details


class UnauthorizedError(Exception):
    """Base class for 401 Unauthorized errors (authentication/authorization issues)."""

    def __init__(self, error: str = "Unauthorized", details: str | None = None):
        """Initialize unauthorized error."""
        super().__init__(details or error)
        self.error = error
        self.details = details


class InvalidCredentialsError(UnauthorizedError):
    """Invalid login credentials."""

    def __init__(self, details: str | None = None):
        """Initialize invalid credentials error."""
        super().__init__(error="InvalidCredentials", details=details)


class ForbiddenError(UnauthorizedError):
    """Access forbidden - insufficient permissions."""

    def __init__(self, details: str | None = None):
        """Initialize forbidden error."""
        super().__init__(error="Forbidden", details=details)


class AccountDisabledError(UnauthorizedError):
    """Account has been disabled."""

    def __init__(self, details: str | None = None):
        """Initialize account disabled error."""
        super().__init__(error="AccountDisabled", details=details or "Account has been disabled")


class AccountLockedError(UnauthorizedError):
    """Account is locked due to security policy."""

    def __init__(self, details: str | None = None):
        """Initialize account locked error."""
        super().__init__(
            error="AccountLocked",
            details=details or "Account is locked due to security policy. Please try again later or contact support.",
        )


class AuthenticationRequiredError(UnauthorizedError):
    """Authentication is required to access this resource."""

    def __init__(self, details: str | None = None):
        """Initialize authentication required error."""
        super().__init__(
            error="AuthenticationRequired",
            details=details or "Authentication is required to access this resource",
        )


class InsufficientPermissionsError(UnauthorizedError):
    """Insufficient permissions to perform this action."""

    def __init__(self, required_role: str | None = None, details: str | None = None):
        """Initialize insufficient permissions error."""
        if details is None and required_role:
            details = f"Insufficient permissions: {required_role} role required"
        super().__init__(
            error="InsufficientPermissions",
            details=details or "Insufficient permissions to perform this action",
        )


class ResourceNotFoundError(BaseAppError):
    """Resource not found."""

    def __init__(self, resource: str, details: str | None = None):
        """Initialize resource not found error."""
        message = f"{resource} not found"
        super().__init__(error="ResourceNotFound", details=details or message)


class AlreadyExistsError(BaseAppError):
    """Resource already exists."""

    def __init__(self, resource: str, details: str | None = None):
        """Initialize already exists error."""
        message = f"{resource} already exists"
        super().__init__(error="AlreadyExists", details=details or message)


class PasswordPolicyError(BaseAppError):
    """Password policy violated."""

    def __init__(self, details: str | None = None):
        """Initialize password policy error."""
        super().__init__(error="PasswordPolicyError", details=details)


class InsufficientFundsError(BaseAppError):
    """Insufficient funds for transaction."""

    def __init__(self, available: int, required: int, details: str | None = None):
        """Initialize insufficient funds error."""
        message = f"Insufficient funds: {available} < {required}"
        super().__init__(error="InsufficientFunds", details=details or message)


class DuplicateIdempotencyKeyError(BaseAppError):
    """Duplicate idempotency key with different payload."""

    def __init__(self, key: str, details: str | None = None):
        """Initialize duplicate idempotency key error."""
        message = f"Idempotency key '{key}' already used with different payload"
        super().__init__(error="DuplicateIdempotencyKey", details=details or message)


class CardValidationError(BaseAppError):
    """Card validation failed."""

    def __init__(self, details: str | None = None):
        """Initialize card validation error."""
        super().__init__(error="CardValidationError", details=details)


class LoanNotApprovedError(BaseAppError):
    """Operation on unapproved loan."""

    def __init__(self, loan_id: str, details: str | None = None):
        """Initialize loan not approved error."""
        message = f"Loan {loan_id} is not approved"
        super().__init__(error="LoanNotApproved", details=details or message)


class InvalidAmountError(BaseAppError):
    """Invalid amount for transaction."""

    def __init__(self, amount: int, details: str | None = None):
        """Initialize InvalidAmountError."""
        message = f"Invalid amount: {amount}"
        super().__init__(error="InvalidAmount", details=details or message)


class InvalidDataError(BaseAppError):
    """Invalid data provided."""

    def __init__(self, field: str, value: str | None = None, details: str | None = None):
        """Initialize InvalidDataError."""
        message = f"Invalid {field}: {value}" if value else f"Invalid {field}"
        super().__init__(error="InvalidData", details=details or message)


class InvalidCardProcessingError(BaseAppError):
    """Card cannot be processed (consolidates all card validation errors for security)."""

    def __init__(self, details: str | None = None):
        """Initialize InvalidCardProcessingError.

        This error consolidates all card validation failures (expired, inactive, invalid CVV, etc.)
        to prevent information leakage about card status.
        """
        super().__init__(
            error="InvalidCardProcessing",
            details=details or "Card cannot be processed. Please check your card details and try again.",
        )


class InvalidOTPError(BaseAppError):
    """Invalid OTP code provided."""

    def __init__(self, details: str | None = None):
        """Initialize InvalidOTPError."""
        super().__init__(error="InvalidOTP", details=details or "Invalid OTP code")


class InvalidPaddingError(BaseAppError):
    """Invalid padding in encrypted data - oracle signal for padding oracle attack."""

    def __init__(self, details: str | None = None):
        """Initialize InvalidPaddingError."""
        super().__init__(error="InvalidPadding", details=details or "Invalid padding in encrypted data")


class InvalidTokenError(BaseAppError):
    """Invalid token data after successful decryption - oracle signal for valid padding."""

    def __init__(self, details: str | None = None):
        """Initialize InvalidTokenError."""
        super().__init__(error="InvalidToken", details=details or "Invalid or corrupted token data")


class InputValidationError(BaseAppError):
    """Input validation error for pattern-based validation."""

    def __init__(self, details: str):
        """Initialize input validation error."""
        super().__init__(error="ValidationError", details=details)


class SecurityQuestionsNotAvailableError(BaseAppError):
    """Security questions not available for account."""

    def __init__(self, details: str | None = None):
        """Initialize security questions not available error."""
        super().__init__(
            error="SecurityQuestionsNotAvailable",
            details=details or "Security questions not available for this account",
        )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for application-specific exceptions only.

    Handles:
    - UnauthorizedError → 401 Unauthorized
    - BaseAppError → 400 Bad Request

    All other exceptions → 500 Internal Server Error
    """
    request_id = getattr(request.state, "request_id", None)

    if isinstance(exc, UnauthorizedError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorResponse(error=exc.error, details=exc.details, request_id=request_id).model_dump(),
        )

    elif isinstance(exc, BaseAppError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(error=exc.error, details=exc.details, request_id=request_id).model_dump(),
        )

    else:
        logger.error(
            f"Unhandled exception: {type(exc).__name__}: {exc}",
            exc_info=exc,
            extra={"request_id": request_id, "path": request.url.path},
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error="InternalServerError",
                details=("An internal server error occurred" if not settings.debug else str(exc)),
                request_id=request_id,
            ).model_dump(),
        )


class ErrorCode(str, Enum):
    """Error codes for consistent API documentation.

    Each error code maps to the exact error string returned in API responses.
    """

    UNAUTHORIZED = "Unauthorized"
    INVALID_CREDENTIALS = "InvalidCredentials"
    FORBIDDEN = "Forbidden"
    ACCOUNT_DISABLED = "AccountDisabled"
    ACCOUNT_LOCKED = "AccountLocked"
    AUTHENTICATION_REQUIRED = "AuthenticationRequired"
    INSUFFICIENT_PERMISSIONS = "InsufficientPermissions"

    VALIDATION_ERROR = "ValidationError"
    RESOURCE_NOT_FOUND = "ResourceNotFound"
    ALREADY_EXISTS = "AlreadyExists"
    PASSWORD_POLICY_ERROR = "PasswordPolicyError"
    INSUFFICIENT_FUNDS = "InsufficientFunds"
    DUPLICATE_IDEMPOTENCY_KEY = "DuplicateIdempotencyKey"
    CARD_VALIDATION_ERROR = "CardValidationError"
    LOAN_NOT_APPROVED = "LoanNotApproved"
    INVALID_AMOUNT = "InvalidAmount"
    INVALID_DATA = "InvalidData"
    INVALID_CARD_PROCESSING = "InvalidCardProcessing"
    INVALID_OTP = "InvalidOTP"
    INVALID_PADDING = "InvalidPadding"
    INVALID_TOKEN = "InvalidToken"
    SECURITY_QUESTIONS_NOT_AVAILABLE = "SecurityQuestionsNotAvailable"


__all__ = [
    "AccountDisabledError",
    "AccountLockedError",
    "AlreadyExistsError",
    "AuthenticationRequiredError",
    "BaseAppError",
    "CardValidationError",
    "DuplicateIdempotencyKeyError",
    "ErrorCode",
    "ForbiddenError",
    "InputValidationError",
    "InsufficientFundsError",
    "InsufficientPermissionsError",
    "InvalidAmountError",
    "InvalidCardProcessingError",
    "InvalidCredentialsError",
    "InvalidDataError",
    "InvalidOTPError",
    "InvalidPaddingError",
    "InvalidTokenError",
    "LoanNotApprovedError",
    "PasswordPolicyError",
    "ResourceNotFoundError",
    "SecurityQuestionsNotAvailableError",
    "UnauthorizedError",
    "global_exception_handler",
]

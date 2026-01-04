"""Enumeration types for the banking API."""

from enum import Enum


class UserRole(str, Enum):
    """User role enumeration."""

    USER = "USER"
    BANKER = "BANKER"
    ADMIN = "ADMIN"


class UserStatus(str, Enum):
    """User account status enumeration."""

    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    LOCKED = "LOCKED"


class CardStatus(str, Enum):
    """Credit card status enumeration."""

    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class LoanStatus(str, Enum):
    """Loan status enumeration."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class TransactionType(str, Enum):
    """Transaction type enumeration."""

    TRANSFER_OUT = "TRANSFER_OUT"
    TRANSFER_IN = "TRANSFER_IN"
    CARD_PAYMENT = "CARD_PAYMENT"
    LOAN_DISBURSEMENT = "LOAN_DISBURSEMENT"
    LOAN_REPAYMENT = "LOAN_REPAYMENT"
    FEE = "FEE"
    REFUND = "REFUND"


class RequestKind(str, Enum):
    """Request kind enumeration."""

    CREDIT_CARD = "CREDIT_CARD"
    LOAN = "LOAN"


class RequestStatus(str, Enum):
    """Request status enumeration."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class CardBrand(str, Enum):
    """Credit card brand enumeration."""

    VISA = "VISA"
    MASTERCARD = "MASTERCARD"
    AMERICAN_EXPRESS = "AMERICAN_EXPRESS"
    DISCOVER = "DISCOVER"


class DocsVerbosity(str, Enum):
    """Documentation verbosity levels."""

    FULL = "full"  # All documentation including examples, descriptions, tags, security, securitySchemes, and all response statuses
    MEDIUM = "medium"  # Strip examples but keep descriptions, tags, security, securitySchemes, and response statuses
    MINIMAL = "minimal"  # Strip examples, descriptions, tags, security, securitySchemes, and non-2xx response statuses

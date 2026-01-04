"""Transaction service schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from ..core.enums import TransactionType
from .account_schemas import AccountRead
from .core import MoneyCents, MoneyDollars


class RelatedAccountInfo(BaseModel):
    """Related account information for transactions."""

    account_number: str = Field(
        ...,
        description="Related account number",
        examples=["1234567890", "BANK-CAPITAL-001"],
    )
    username: str = Field(
        ...,
        description="Username of the account owner",
        examples=["john_doe", "AIG Bank"],
    )

    model_config = ConfigDict(title="Related Account Info")


class TransactionRead(BaseModel):
    """Transaction response schema."""

    id: UUID = Field(
        ...,
        description="Unique transaction identifier",
        examples=["770e8400-e29b-41d4-a716-446655440000"],
    )
    account_id: UUID = Field(
        ...,
        description="Account ID associated with this transaction",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    type: TransactionType = Field(
        ...,
        description="Transaction type",
        examples=[
            TransactionType.TRANSFER_OUT,
            TransactionType.TRANSFER_IN,
            TransactionType.CARD_PAYMENT,
            TransactionType.LOAN_DISBURSEMENT,
        ],
    )
    amount_cents: MoneyCents = Field(..., description="Transaction amount in cents", examples=[50000, -25000])
    amount_dollars: MoneyDollars = Field(..., description="Transaction amount in dollars", examples=[500.0, -250.0])
    related_account_id: RelatedAccountInfo | None = Field(
        default=None,
        description="Related account information for transfers and payments",
        examples=[{"account_number": "9876543210", "username": "jane_smith"}],
    )
    idempotency_key: str = Field(
        ...,
        description="Unique idempotency key for duplicate prevention",
        examples=["transfer_abc123", "payment_xyz789"],
    )
    meta: dict[str, Any] | None = Field(
        default=None,
        description="Additional metadata for the transaction",
        examples=[{"source": "ATM", "location": "Downtown Branch"}],
    )
    created_at: datetime = Field(
        ...,
        description="Transaction creation timestamp",
        examples=["2025-01-01T00:00:00Z"],
    )

    model_config = ConfigDict(from_attributes=True, title="Transaction")

    @field_serializer("id", "account_id")
    def serialize_uuid_fields(self, value: UUID | None) -> str | None:
        """Convert UUID fields to strings."""
        if value is None:
            return None
        return str(value)


class TransactionCursorList(BaseModel):
    """Transaction cursor-based list schema."""

    items: list[TransactionRead] = Field(
        ...,
        description="List of transactions",
        examples=[
            [
                {
                    "id": "770e8400-e29b-41d4-a716-446655440000",
                    "account_id": "550e8400-e29b-41d4-a716-446655440000",
                    "type": "TRANSFER_OUT",
                    "amount_cents": -50000,
                    "amount_dollars": -500.0,
                    "related_account_id": {"account_number": "9876543210", "username": "jane_smith"},
                    "idempotency_key": "transfer_abc123",
                    "meta": {"note": "Payment for services"},
                    "created_at": "2025-01-01T00:00:00Z",
                }
            ]
        ],
    )
    next_cursor: str | None = Field(
        default=None,
        description="Cursor for next page",
        examples=["2025-01-01T00:00:00Z:770e8400-e29b-41d4-a716-446655440000"],
    )

    model_config = ConfigDict(title="Transaction List")


class CardPaymentCreate(BaseModel):
    """Card payment creation schema."""

    pan: str = Field(
        ...,
        description="Primary Account Number (PAN)",
        examples=["4111111111111111"],
    )
    exp_month: int = Field(
        ...,
        description="Expiration month",
        examples=[12],
    )
    exp_year: int = Field(
        ...,
        description="Expiration year (4 digits)",
        examples=[2025],
    )
    cvv: str = Field(
        ...,
        description="Card Verification Value",
        examples=["123"],
    )
    to_account_number: str = Field(
        ...,
        description="Destination account number",
        examples=["1234567890"],
    )
    amount_cents: MoneyCents = Field(
        ...,
        description="Amount to charge in cents",
        examples=[50000],
    )
    meta: dict[str, Any] | None = Field(
        default=None,
        description="Additional metadata",
        examples=[{"merchant": "Online Store", "order_id": "ORD-12345"}],
    )

    model_config = ConfigDict(title="Create Card Payment")

    @field_validator("pan")
    @classmethod
    def validate_pan(cls, v: str) -> str:
        """Validate PAN format."""
        from ..utils.validators import InputValidator

        return InputValidator.validate_pan(v)

    @field_validator("exp_month")
    @classmethod
    def validate_exp_month(cls, v: int) -> int:
        """Validate expiration month."""
        from ..utils.validators import InputValidator

        return InputValidator.validate_expiration_month(v)

    @field_validator("exp_year")
    @classmethod
    def validate_exp_year(cls, v: int) -> int:
        """Validate expiration year."""
        from ..utils.validators import InputValidator

        return InputValidator.validate_expiration_year(v)

    @field_validator("cvv")
    @classmethod
    def validate_cvv(cls, v: str) -> str:
        """Validate CVV format."""
        from ..utils.validators import InputValidator

        return InputValidator.validate_cvv(v)

    @field_validator("amount_cents")
    @classmethod
    def validate_amount_cents(cls, v: int) -> int:
        """Validate amount is positive."""
        from ..utils.validators import InputValidator

        return InputValidator.validate_positive_amount(v, "Amount")


class TransferCreate(BaseModel):
    """Transfer creation request."""

    to_account_number: str = Field(
        ...,
        description="Destination account number",
        examples=["0987654321"],
    )
    amount_cents: MoneyCents = Field(
        ...,
        description="Amount to transfer in cents",
        examples=[50000, 100000],
    )
    meta: dict[str, Any] | None = Field(
        default=None,
        description="Additional metadata for the transfer",
        examples=[{"note": "Payment for services", "invoice_id": "INV-12345"}],
    )

    model_config = ConfigDict(title="Create Transfer")

    @field_validator("to_account_number")
    @classmethod
    def validate_to_account_number(cls, v: str) -> str:
        """Validate account number format."""
        from ..utils.validators import InputValidator

        return InputValidator.validate_account_number(v)

    @field_validator("amount_cents")
    @classmethod
    def validate_amount_cents(cls, v: int) -> int:
        """Validate amount is positive."""
        from ..utils.validators import InputValidator

        return InputValidator.validate_positive_amount(v, "Amount")


class TransferRead(BaseModel):
    """Transfer response schema.

    Returns the user's outgoing transaction along with both account details.
    """

    transaction: TransactionRead = Field(..., description="The user's outgoing transaction")
    from_account: AccountRead = Field(..., description="Source account details")
    to_account: AccountRead = Field(..., description="Destination account details")

    model_config = ConfigDict(from_attributes=True, title="Transfer")


class AccountTransactionList(BaseModel):
    """Account transaction list schema (offset-based pagination)."""

    transactions: list[TransactionRead] = Field(
        ...,
        description="List of transactions",
        examples=[
            [
                {
                    "id": "770e8400-e29b-41d4-a716-446655440000",
                    "account_id": "550e8400-e29b-41d4-a716-446655440000",
                    "type": "TRANSFER_OUT",
                    "amount_cents": -50000,
                    "amount_dollars": -500.0,
                    "related_account_id": {"account_number": "9876543210", "username": "jane_smith"},
                    "idempotency_key": "transfer_abc123",
                    "meta": {"note": "Payment for services"},
                    "created_at": "2025-01-01T00:00:00Z",
                }
            ]
        ],
    )
    total: int = Field(..., description="Total number of transactions", examples=[100])
    limit: int = Field(..., description="Number of items per page", examples=[50])
    offset: int = Field(..., description="Number of items skipped", examples=[0])

    model_config = ConfigDict(title="Account Transaction List")


__all__ = [
    "AccountTransactionList",
    "CardPaymentCreate",
    "RelatedAccountInfo",
    "TransactionCursorList",
    "TransactionRead",
    "TransferCreate",
    "TransferRead",
]

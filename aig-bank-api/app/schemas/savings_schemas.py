"""Savings plan schemas."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..core.constants import SAVINGS_PLANS
from ..utils.validators import InputValidator
from .core import MoneyCents


class SavingsPlanInfo(BaseModel):
    """Savings plan information schema."""

    id: int = Field(
        ...,
        description="Unique identifier for the savings plan",
        examples=[1, 2],
    )
    name: str = Field(
        ...,
        description="Internal name of the savings plan",
        examples=["money_market_mutual_fund"],
    )
    display_name: str = Field(
        ...,
        description="Human-readable name of the savings plan",
        examples=["Money Market Mutual Fund"],
    )
    description: str = Field(
        ...,
        description="Detailed description of the savings plan",
        examples=[
            "High-yield money market account with automatic reinvestment into foreign currency accounts " "featuring compounding interest."
        ],
    )
    tagline: str = Field(
        ...,
        description="Catchy tagline for the savings plan",
        examples=["Compounding interest on foreign currencies"],
    )

    model_config = ConfigDict(title="Savings Plan Info")


class SavingsPlanList(BaseModel):
    """List of available savings plans."""

    plans: list[SavingsPlanInfo] = Field(
        ...,
        description="Available savings plans",
        examples=[
            [
                {
                    "id": 1,
                    "name": "money_market_mutual_fund",
                    "display_name": "Money Market Mutual Fund",
                    "description": (
                        "High-yield money market account with automatic reinvestment into foreign currency "
                        "accounts featuring compounding interest."
                    ),
                    "tagline": "Compounding interest on foreign currencies",
                }
            ]
        ],
    )

    model_config = ConfigDict(title="Savings Plan List")


class SavingsPlanDepositCreate(BaseModel):
    """Savings plan deposit request schema."""

    plan_id: int = Field(
        ...,
        description="ID of the savings plan to open",
        examples=[1, 2, 3],
    )
    amount_cents: MoneyCents = Field(
        ...,
        description="Amount to deposit in cents",
        examples=[50000, 100000],
    )

    model_config = ConfigDict(title="Create Savings Plan Deposit")

    @field_validator("plan_id")
    @classmethod
    def validate_plan_id(cls, v: int) -> int:
        """Validate plan ID is within valid range."""
        min_id = min(plan["id"] for plan in SAVINGS_PLANS)
        max_id = max(plan["id"] for plan in SAVINGS_PLANS)
        return InputValidator.validate_range(v, min_id, max_id, "Plan ID")

    @field_validator("amount_cents")
    @classmethod
    def validate_amount_cents(cls, v: int) -> int:
        """Validate amount is positive."""
        return InputValidator.validate_positive_amount(v, "Amount")


class SavingsPlanDepositRead(BaseModel):
    """Savings plan deposit response schema."""

    plan_id: int = Field(
        ...,
        description="ID of the savings plan opened",
        examples=[1, 2],
    )
    plan_name: str = Field(
        ...,
        description="Name of the savings plan opened",
        examples=["money_market_mutual_fund"],
    )
    amount_cents: MoneyCents = Field(
        ...,
        description="Amount deposited in cents",
        examples=[50000, 100000],
    )
    message: str = Field(
        ...,
        description="Confirmation message for opening the savings plan",
        examples=[
            "Well that's fantastic, a really smart decision, young man. We can put that deposit in a "
            "Money Market Mutual Fund, then we'll reinvest the earnings into foreign currency accounts "
            "with compounding interest aaand it's gone."
        ],
    )

    model_config = ConfigDict(title="Savings Plan Deposit")


__all__ = [
    "SavingsPlanDepositCreate",
    "SavingsPlanDepositRead",
    "SavingsPlanInfo",
    "SavingsPlanList",
]

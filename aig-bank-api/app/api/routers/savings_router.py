"""Savings plan API endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db import get_db
from ...core.errors import ErrorCode
from ...schemas.savings_schemas import (
    SavingsPlanDepositCreate,
    SavingsPlanDepositRead,
    SavingsPlanList,
)
from ...services.savings_service import SavingsService
from ..deps import get_current_user

router = APIRouter(tags=["Savings Plans"])


@router.get(
    "/savings-plans",
    response_model=SavingsPlanList,
    summary="List Available Savings Plans",
    description="""Retrieve the list of available savings plans.""",
    responses={
        status.HTTP_200_OK: {
            "model": SavingsPlanList,
            "description": "Success",
        },
    },
)
async def list_savings_plans(
    db: AsyncSession = Depends(get_db),
) -> SavingsPlanList:
    """List all available savings plans.

    Args:
        db: Database session

    Returns:
        SavingsPlanList: List of available savings plans
    """
    savings_service = SavingsService(db)
    return savings_service.get_available_plans()


@router.post(
    "/users/savings-plans/open",
    response_model=SavingsPlanDepositRead,
    summary="Open Savings Plan",
    description="""Open a savings plan by depositing funds into the selected plan.""",
    responses={
        status.HTTP_200_OK: {
            "model": SavingsPlanDepositRead,
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
                                "details": "Plan ID must be between 1 and 5",
                                "request_id": "938304120f4492de",
                            },
                        },
                        "insufficient_funds": {
                            "summary": "Insufficient funds",
                            "value": {
                                "error": ErrorCode.INSUFFICIENT_FUNDS.value,
                                "details": "Insufficient funds in account 1000000000001",
                                "request_id": "938304120f4492de",
                            },
                        },
                        "resource_not_found": {
                            "summary": "Resource not found",
                            "value": {
                                "error": ErrorCode.RESOURCE_NOT_FOUND.value,
                                "details": "Bank capital account BANK-CAPITAL-001 not found",
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
async def open_savings_plan(
    deposit_request: SavingsPlanDepositCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SavingsPlanDepositRead:
    """Open a savings plan.

    Args:
        deposit_request: Savings plan deposit request data
        current_user: Authenticated user context
        db: Database session

    Returns:
        SavingsPlanDepositRead: Savings plan result with message
    """
    savings_service = SavingsService(db)
    return await savings_service.open_savings_plan(
        user_id=current_user["user_id"],
        plan_id=deposit_request.plan_id,
        amount_cents=deposit_request.amount_cents,
    )

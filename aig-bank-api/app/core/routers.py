"""Application router configuration."""

from fastapi import FastAPI

from ..api.routers.admin_router import router as admin_router
from ..api.routers.api_keys_router import router as api_keys_router
from ..api.routers.auth_router import router as auth_router
from ..api.routers.banker_router import router as banker_router
from ..api.routers.credit_card_router import router as credit_card_router
from ..api.routers.health_router import router as health_router
from ..api.routers.loan_router import router as loan_router
from ..api.routers.registration_router import router as registration_router
from ..api.routers.request_router import router as request_router
from ..api.routers.savings_router import router as savings_router
from ..api.routers.transaction_router import router as transaction_router
from ..api.routers.user_router import router as user_router


def setup_routers(app: FastAPI, api_prefix: str) -> None:
    """Set up application routers."""
    app.include_router(health_router)

    app.include_router(registration_router, prefix=api_prefix)
    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(user_router, prefix=api_prefix)
    app.include_router(api_keys_router, prefix=api_prefix)
    app.include_router(credit_card_router, prefix=api_prefix)
    app.include_router(loan_router, prefix=api_prefix)
    app.include_router(request_router, prefix=api_prefix)
    app.include_router(transaction_router, prefix=api_prefix)
    app.include_router(savings_router, prefix=api_prefix)
    app.include_router(banker_router, prefix=api_prefix)
    app.include_router(admin_router, prefix=api_prefix)

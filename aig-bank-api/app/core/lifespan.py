"""Application lifespan management for startup and shutdown."""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress
import logging

from fastapi import FastAPI

from ..utils.background_tasks import background_runner
from .db import create_tables, init_db, seed_bank_capital_account, seed_default_users


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan context manager."""
    logger = logging.getLogger(__name__)
    logger.info("Starting AIG Bank API")

    await init_db()
    logger.info("Database initialized")

    await create_tables()
    logger.info("Database tables created")

    await seed_bank_capital_account()
    logger.info("Bank capital account seeded")

    await seed_default_users()
    logger.info("Default users seeded")

    background_task = asyncio.create_task(background_runner.start())
    logger.info("Background task runner started for automatic loan repayments")

    yield

    logger.info("Shutting down AIG Bank API")
    await background_runner.stop()
    background_task.cancel()
    with suppress(asyncio.CancelledError):
        await background_task
    logger.info("Background task runner stopped")

"""Background task scheduler for loan repayments."""

import asyncio
import logging

from ..core.config import settings
from ..core.db import async_session
from ..services.loan_repayment_service import LoanRepaymentService

logger = logging.getLogger(__name__)


class BackgroundTaskRunner:
    """Runs background tasks periodically."""

    def __init__(self):
        """Initialize the background task runner."""
        self.running = False
        self._task = None

    async def start(self):
        """Start the background task runner."""
        self.running = True
        logger.info("Background task runner started")

        while self.running:
            try:
                logger.debug("Processing due loan repayments...")

                async with async_session() as session:
                    repayment_service = LoanRepaymentService(session)
                    result = await repayment_service.process_due_repayments()

                logger.info(
                    f"Repayment processing complete: "
                    f"{result['processed']} processed, {result['failed']} failed, "
                    f"{result['total_due']} total due"
                )
            except Exception as e:
                logger.error(f"Error in background task runner: {e}", exc_info=True)

            await asyncio.sleep(settings.repayment_check_interval_seconds)

    async def stop(self):
        """Stop the background task runner."""
        self.running = False
        logger.info("Background task runner stopped")


background_runner = BackgroundTaskRunner()

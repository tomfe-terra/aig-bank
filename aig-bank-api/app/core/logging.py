"""Logging configuration with file handlers."""

import logging
import logging.handlers
from pathlib import Path

from .config import settings
from .constants import LOG_FORMAT


def setup_logging(log_level: str) -> None:
    """Set up structured logging with multiple file handlers.

    Creates four log files in the configured logs directory:
    1. access.log - HTTP request logs from middleware
    2. error.log - Error level logs
    3. info.log - Info level logs (excluding middleware)
    4. debug.log - All logs (debug and above)

    Args:
        log_level: Minimum log level for console output (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logs_dir = Path(settings.logs_directory)
    logs_dir.mkdir(exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    root_logger.handlers.clear()

    formatter = logging.Formatter(LOG_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    debug_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "debug.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(formatter)
    root_logger.addHandler(debug_handler)

    info_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "info.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)

    class ExcludeMiddlewareFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            return not record.name.startswith("app.core.middleware")

    info_handler.addFilter(ExcludeMiddlewareFilter())
    root_logger.addHandler(info_handler)

    error_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "error.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)

    access_logger = logging.getLogger("app.core.middleware")
    access_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "access.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    access_handler.setLevel(logging.INFO)
    access_handler.setFormatter(formatter)
    access_logger.addHandler(access_handler)

    access_logger.propagate = True

    class SuppressAppErrorsFilter(logging.Filter):
        """Suppress logging of application errors that are handled by our exception handler."""

        def filter(self, record: logging.LogRecord) -> bool:
            if record.name == "uvicorn.error" and "Exception in ASGI application" in record.getMessage() and record.exc_info:
                exc_type = record.exc_info[0]
                if exc_type and exc_type.__module__.startswith("app.core.errors"):
                    return False
            return True

    uvicorn_error_logger = logging.getLogger("uvicorn.error")
    uvicorn_error_logger.addFilter(SuppressAppErrorsFilter())

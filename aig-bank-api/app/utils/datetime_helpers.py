"""Datetime utility functions for serialization."""

from datetime import datetime


def format_datetime(dt: datetime | None) -> str | None:
    """Convert datetime to ISO format string.

    Args:
        dt: Datetime object or None

    Returns:
        ISO format string or None if input is None
    """
    return dt.isoformat() if dt else None

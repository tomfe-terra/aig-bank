"""UUID generation utility for database models."""

import uuid


def generate_uuid_str() -> str:
    """Generate a UUID as a string."""
    return str(uuid.uuid4())

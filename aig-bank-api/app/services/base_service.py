"""Base service class for business logic operations."""

from typing import Any, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.errors import ResourceNotFoundError

T = TypeVar("T")


class BaseService:
    """Base service class providing common functionality."""

    def __init__(self, session: AsyncSession):
        """Initialize service with database session."""
        self.session = session

    async def _get_by_id(self, repository: Any, model_id: str) -> Any:
        """Generic get by ID with error handling."""
        entity = await repository.get_by_id(model_id)
        if not entity:
            raise ResourceNotFoundError(
                repository.__class__.__name__.replace("Repository", ""),
                f"{model_id} not found",
            )
        return entity

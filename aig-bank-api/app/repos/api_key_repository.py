"""API Key repository for database operations."""

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.errors import ResourceNotFoundError
from ..models.api_key_model import APIKey


class APIKeyRepository:
    """Repository for API Key model operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(
        self,
        encrypted_secret: str,
        name: str,
        user_id: str,
        description: str | None = None,
        is_active: bool = True,
    ) -> APIKey:
        """Create a new API key."""
        api_key = APIKey(
            encrypted_secret=encrypted_secret,
            name=name,
            description=description,
            user_id=user_id,
            is_active=is_active,
        )

        self.session.add(api_key)
        await self.session.flush()

        await self.session.refresh(api_key)

        return api_key

    async def get_by_id(self, api_key_id: str) -> APIKey | None:
        """Get API key by ID."""
        stmt = select(APIKey).where(APIKey.id == api_key_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_api_key_id(self, api_key_id: str) -> APIKey | None:
        """Get API key by API key ID (same as get_by_id)."""
        return await self.get_by_id(api_key_id)

    async def get_by_user_id(
        self, user_id: str, active_only: bool = True, limit: int | None = None, offset: int = 0
    ) -> tuple[list[APIKey], int]:
        """Get API keys for a user with pagination.

        Args:
            user_id: User ID
            active_only: If True, only return active keys. If False, return all keys.
            limit: Maximum number of keys to return
            offset: Number of keys to skip

        Returns:
            Tuple of (list of API keys, total count)
        """
        where_clause = and_(APIKey.user_id == user_id, APIKey.is_active) if active_only else APIKey.user_id == user_id

        stmt = select(APIKey).where(where_clause).order_by(APIKey.created_at.desc()).limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        api_keys = list(result.scalars().all())

        count_stmt = select(APIKey).where(where_clause)
        count_result = await self.session.execute(count_stmt)
        total = len(count_result.scalars().all())

        return api_keys, total

    async def update(self, api_key: APIKey) -> APIKey:
        """Update API key in database."""
        self.session.add(api_key)
        await self.session.flush()
        await self.session.refresh(api_key)
        return api_key

    async def delete(self, api_key_id: str) -> None:
        """Soft delete API key by setting is_active to False."""
        api_key = await self.get_by_id(api_key_id)
        if not api_key:
            raise ResourceNotFoundError("API Key", f"API Key {api_key_id} not found")

        api_key.is_active = False  # type: ignore[assignment]
        self.session.add(api_key)
        await self.session.flush()

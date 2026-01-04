"""API Key service for API key management operations."""

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.errors import ResourceNotFoundError
from ..models.api_key_model import APIKey
from ..repos.api_key_repository import APIKeyRepository
from ..schemas.api_key_schemas import APIKeyCreate, APIKeySecretRead, APIKeyUpdate


class APIKeyService:
    """Service for API key-related operations."""

    def __init__(self, db_session: AsyncSession):
        """Initialize API key service."""
        self.db_session = db_session
        self.repo = APIKeyRepository(db_session)

    async def create_api_key(self, user_id: str, request: APIKeyCreate) -> APIKeySecretRead:
        """Create a new API key for a user."""
        secret = APIKey.generate_secret()

        encrypted_secret = APIKey.encrypt_secret(secret)

        api_key = await self.repo.create(
            encrypted_secret=encrypted_secret,
            name=request.name,
            description=request.description,
            user_id=user_id,
        )

        return APIKeySecretRead(
            id=api_key.id,  # type: ignore[arg-type]
            secret=secret,
            name=request.name,
            description=request.description,
            user_id=user_id,
            is_active=api_key.is_active,
            created_at=api_key.created_at,  # type: ignore[arg-type]
            last_used=api_key.last_used_at,
        )

    async def get_api_key_by_id(self, api_key_id: str) -> APIKey | None:
        """Get API key by ID."""
        try:
            return await self.repo.get_by_id(api_key_id)
        except ValueError:
            return None

    async def get_api_key_by_api_key_id(self, api_key_id: str) -> APIKey | None:
        """Get API key by API key ID (same as get_by_id)."""
        return await self.repo.get_by_api_key_id(api_key_id)

    async def list_api_keys_for_user(
        self, user_id: str, active_only: bool = True, limit: int = 50, offset: int = 0
    ) -> tuple[list[APIKey], int]:
        """List API keys for a user.

        Args:
            user_id: User ID
            active_only: If True, only return active keys. If False, return all keys.
            limit: Maximum number of keys to return
            offset: Number of keys to skip

        Returns:
            Tuple of (list of API keys, total count)
        """
        return await self.repo.get_by_user_id(user_id=user_id, active_only=active_only, limit=limit, offset=offset)

    async def update_api_key(self, api_key_id: str, user_id: str, request: APIKeyUpdate) -> APIKey:
        """Update an API key's name.

        Args:
            api_key_id: API key ID to update
            user_id: User ID to verify ownership
            request: Update request with new name

        Returns:
            Updated API key

        Raises:
            ResourceNotFoundError: If API key not found or doesn't belong to user
        """
        api_key = await self.get_api_key_by_id(api_key_id)
        if not api_key or api_key.user_id != user_id:
            raise ResourceNotFoundError("API Key", "API Key not found")

        update_data = request.create_update_dict()

        for field, value in update_data.items():
            setattr(api_key, field, value)

        return await self.repo.update(api_key)

    async def revoke_api_key(self, api_key_id: str, user_id: str) -> None:
        """Revoke (soft delete) an API key.

        Args:
            api_key_id: API key ID to revoke
            user_id: User ID to verify ownership

        Raises:
            ResourceNotFoundError: If API key not found or doesn't belong to user
        """
        api_key = await self.get_api_key_by_id(api_key_id)
        if not api_key or api_key.user_id != user_id:
            raise ResourceNotFoundError("API Key", "API Key not found")

        await self.repo.delete(api_key.id)

    def create_request_signature(self, secret: str, method: str, path: str, body: str) -> str:
        """Create HMAC signature for a request (for testing/documentation).

        Args:
            secret: The API secret
            method: HTTP method
            path: Request path
            body: Request body

        Returns:
            HMAC signature as hex string
        """
        import hashlib
        import hmac

        message_parts = [method.upper(), path, body]
        message = "\n".join(message_parts).encode("utf-8")

        signature = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()

        return signature

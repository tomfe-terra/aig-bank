"""User repository for database operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.enums import UserStatus
from ..core.errors import ResourceNotFoundError
from ..models.user_model import User, UserRole


class UserRepository:
    """Repository for User model operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(
        self,
        username: str,
        password_hash: str,
        first_name: str,
        last_name: str,
        otp_secret: str,
        security_question_1_id: int,
        security_answer_1_hash: str,
        security_question_2_id: int,
        security_answer_2_hash: str,
        security_question_3_id: int,
        security_answer_3_hash: str,
        role: str = UserRole.USER,
        email: str | None = None,
        phone: str | None = None,
        address: str | None = None,
    ) -> User:
        """Create a new user with all required security fields.

        Args:
            username: Unique username
            password_hash: Hashed password (use PasswordManager.hash_password)
            first_name: User's first name
            last_name: User's last name
            otp_secret: OTP secret for 2FA (use otp_manager.generate_secret)
            security_question_1_id: First security question ID
            security_answer_1_hash: Hashed answer to first question
            security_question_2_id: Second security question ID
            security_answer_2_hash: Hashed answer to second question
            security_question_3_id: Third security question ID
            security_answer_3_hash: Hashed answer to third question
            role: User role (default: USER)
            email: Optional email address
            phone: Optional phone number
            address: Optional address

        Returns:
            User: Created user object
        """
        user = User(
            username=username,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            role=role,
            email=email,
            phone=phone,
            address=address,
            status=UserStatus.ENABLED,
            otp_secret=otp_secret,
            security_question_1_id=security_question_1_id,
            security_answer_1_hash=security_answer_1_hash,
            security_question_2_id=security_question_2_id,
            security_answer_2_hash=security_answer_2_hash,
            security_question_3_id=security_question_3_id,
            security_answer_3_hash=security_answer_3_hash,
        )

        self.session.add(user)
        await self.session.flush()

        await self.session.refresh(user)

        return user

    async def get_by_id(self, user_id: str) -> User | None:
        """Get user by ID (only enabled users)."""
        stmt = select(User).where(User.id == user_id).where(User.status == UserStatus.ENABLED)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """Get user by username (all statuses for authentication check)."""
        stmt = select(User).where(User.username == username)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email (optional field)."""
        if not email:
            return None
        stmt = select(User).where(User.email == email).where(User.status == UserStatus.ENABLED)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, user: User) -> User:
        """Update user in database."""
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update_profile(self, user_id: str, **fields) -> User:
        """Update user profile fields.

        Args:
            user_id: User ID to update
            **fields: Fields to update (first_name, last_name, email, phone, address)

        Returns:
            User: Updated user object

        Raises:
            ResourceNotFoundError: If user not found
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", user_id)

        for field, value in fields.items():
            if hasattr(user, field):
                setattr(user, field, value)

        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update_avatar(self, user_id: str, avatar_blob: bytes) -> User:
        """Update user avatar.

        Args:
            user_id: User ID to update
            avatar_blob: Compressed WebP avatar bytes

        Returns:
            User: Updated user object

        Raises:
            ResourceNotFoundError: If user not found
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", user_id)

        user.avatar_blob = avatar_blob  # type: ignore[assignment]
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def get_avatar(self, user_id: str) -> bytes | None:
        """Get user avatar blob.

        Args:
            user_id: User ID

        Returns:
            bytes | None: Avatar blob or None if no avatar

        Raises:
            ResourceNotFoundError: If user not found
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", user_id)

        return user.avatar_blob  # type: ignore[return-value]

    async def delete_avatar(self, user_id: str) -> User:
        """Delete user avatar.

        Args:
            user_id: User ID

        Returns:
            User: Updated user object

        Raises:
            ResourceNotFoundError: If user not found
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", user_id)

        user.avatar_blob = None  # type: ignore[assignment]
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def record_failed_login_attempt(self, user: User) -> None:
        """Record a failed login attempt and lock account if threshold reached.

        This method commits the changes in a separate transaction to ensure
        failed attempts are persisted even when authentication fails.

        Args:
            user: User object to update
        """
        from ..core.db import async_session

        user.increment_failed_attempts()

        async with async_session() as independent_session:
            merged_user = await independent_session.merge(user)
            await independent_session.commit()

            user.failed_login_attempts = merged_user.failed_login_attempts
            user.locked_until = merged_user.locked_until
            user.last_failed_login_at = merged_user.last_failed_login_at

    async def unlock_user(self, user_id: str) -> User:
        """Unlock a user account by resetting failed login attempts.

        Args:
            user_id: ID of the user to unlock

        Returns:
            User: Updated user object

        Raises:
            ResourceNotFoundError: If user not found
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", user_id)

        user.reset_failed_attempts()

        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)

        return user

    async def delete(self, user_id: str) -> None:
        """Soft delete user by setting status to DISABLED."""
        user = await self.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", f"User {user_id} not found")

        user.status = UserStatus.DISABLED 
        self.session.add(user)
        await self.session.flush()

    async def list_users(self, limit: int = 50, offset: int = 0) -> tuple[list[User], int]:
        """List users with pagination and total count (only enabled users)."""
        stmt = select(User).where(User.status == UserStatus.ENABLED)
        stmt = stmt.order_by(User.created_at.desc()).limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        users = list(result.scalars().all())

        count_stmt = select(User).where(User.status == UserStatus.ENABLED)
        count_result = await self.session.execute(count_stmt)
        total = len(count_result.scalars().all())

        return users, total

    async def username_exists(self, username: str) -> bool:
        """Check if username already exists."""
        stmt = select(User).where(User.username == username)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def update_user_role(self, user_id: str, new_role: UserRole) -> User:
        """Update a user's role.

        Args:
            user_id: ID of the user to update
            new_role: New role for the user

        Returns:
            User: Updated user object

        Raises:
            ResourceNotFoundError: If user not found
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", str(user_id))

        user.role = new_role 
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

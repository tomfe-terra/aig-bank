"""Admin service for administrative operations."""

from collections.abc import Callable
import logging
from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.constants import BANK_CAPITAL_ACCOUNT_NUMBER
from ..core.enums import UserRole
from ..core.errors import InvalidDataError, ResourceNotFoundError
from ..repos.account_repository import AccountRepository
from ..repos.user_repository import UserRepository
from ..schemas.admin_schemas import (
    BankCapitalBalance,
    LogFileContent,
    LogFileInfo,
    LogFileList,
    TokenBlacklist,
    UserList,
    UserListItem,
    UserRoleUpdateResult,
    UserUnlockResult,
)
from ..utils.log_manager import LogManager
from ..utils.token_blacklist import token_blacklist
from .base_service import BaseService

logger = logging.getLogger(__name__)


class AdminService(BaseService):
    """Service for admin-only operations."""

    def __init__(self, db_session: AsyncSession):
        """Initialize admin service.

        Args:
            db_session: Database session
        """
        super().__init__(db_session)
        self.user_repository = UserRepository(db_session)
        self.account_repository = AccountRepository(db_session)
        self.log_manager = LogManager()

    async def list_users(self, limit: int = 50, offset: int = 0) -> UserList:
        """List all users with pagination.

        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip

        Returns:
            UserList: Paginated list of users
        """
        users, total = await self.user_repository.list_users(limit=limit, offset=offset)
        user_items = []
        for user in users:
            user_item = UserListItem.model_validate(user)
            if user.has_avatar:
                user_item.avatar_url = f"/api/v1/admin/users/{user.id}/avatar"
            user_items.append(user_item)
        return UserList(users=user_items, total=total, limit=limit, offset=offset)

    async def update_user_role(self, target_user_id: UUID, new_role: UserRole, admin_user_id: UUID) -> UserRoleUpdateResult:
        """Update a user's role.

        Args:
            target_user_id: ID of the user to update
            new_role: New role to assign
            admin_user_id: ID of the admin performing the update

        Returns:
            UserRoleUpdateResult: Result of the role update

        Raises:
            InvalidDataError: If trying to change own role or demote another admin
            ResourceNotFoundError: If target user not found
        """
        if target_user_id == admin_user_id:
            raise InvalidDataError(
                "user_id",
                str(target_user_id),
                "An admin cannot change their own role.",
            )

        target_user = await self.user_repository.get_by_id(str(target_user_id))
        if not target_user:
            raise ResourceNotFoundError("User", str(target_user_id))

        updated_user = await self.user_repository.update_user_role(str(target_user_id), new_role)

        old_role_str = target_user.role.value if hasattr(target_user.role, "value") else str(target_user.role)
        new_role_str = new_role.value if hasattr(new_role, "value") else str(new_role)

        logger.info(
            "Admin %s changed role of user %s from %s to %s",
            str(admin_user_id),
            str(target_user_id),
            old_role_str,
            new_role_str,
            extra={
                "admin_id": str(admin_user_id),
                "target_user_id": str(target_user_id),
                "old_role": old_role_str,
                "new_role": new_role_str,
                "action": "user_role_update",
            },
        )

        user_item = UserListItem.model_validate(updated_user)
        if updated_user.has_avatar:
            user_item.avatar_url = f"/api/v1/admin/users/{updated_user.id}/avatar"

        return UserRoleUpdateResult(
            message=f"User role updated to {new_role.value}",
            user=user_item,
        )

    async def unlock_user(self, target_user_id: UUID, admin_user_id: UUID) -> UserUnlockResult:
        """Unlock a user account by resetting failed login attempts.

        This will reset the failed_login_attempts counter and clear the locked_until timestamp,
        allowing the user to log in again.

        Args:
            target_user_id: ID of the user to unlock
            admin_user_id: ID of the admin performing the unlock

        Returns:
            UserUnlockResult: Result of the unlock operation

        Raises:
            InvalidDataError: If trying to unlock own account
            ResourceNotFoundError: If target user not found
        """
        await self.user_repository.unlock_user(str(target_user_id))

        logger.info(
            "Admin %s unlocked user %s",
            str(admin_user_id),
            str(target_user_id),
            extra={
                "admin_id": str(admin_user_id),
                "target_user_id": str(target_user_id),
                "action": "user_unlock",
            },
        )

        return UserUnlockResult(
            message="User account unlocked successfully",
        )

    async def get_bank_capital_balance(self) -> BankCapitalBalance:
        """Get the bank's capital account balance.

        Returns:
            BankCapitalBalance: Bank capital account balance

        Raises:
            ResourceNotFoundError: If bank capital account not found
        """
        account = await self.account_repository.get_by_number(BANK_CAPITAL_ACCOUNT_NUMBER)
        if not account:
            raise ResourceNotFoundError("BankCapitalAccount", BANK_CAPITAL_ACCOUNT_NUMBER)

        return BankCapitalBalance.model_validate(account)

    def list_log_files(self) -> LogFileList:
        """List all log files in the logs directory.

        Returns:
            LogFileList: List of log files with metadata
        """
        files_data = self.log_manager.list_files()
        files = [LogFileInfo(**file_data) for file_data in files_data]
        return LogFileList(files=files, total=len(files))

    def get_log_file_content(self, filename: str, max_lines: int = 1000) -> LogFileContent:
        """Get parsed content from a log file.

        Args:
            filename: Name of the log file
            max_lines: Maximum number of lines to return

        Returns:
            LogFileContent: Parsed log file content

        Raises:
            InputValidationError: If filename is invalid
            ResourceNotFoundError: If log file not found
            InvalidDataError: If error reading or parsing log file
        """
        content_data = self.log_manager.get_parsed_content(filename, max_lines)
        return LogFileContent(**content_data)

    def download_log_file(self, filename: str) -> tuple[Path, Callable[[], None]]:
        """Get the path to a log file for download.

        Creates a temporary snapshot of the log file to avoid race conditions
        and returns a cleanup callback to remove it after download completes.

        Args:
            filename: Name of the log file

        Returns:
            tuple[Path, Callable]: Temporary file path and cleanup callback

        Raises:
            InputValidationError: If filename is invalid or path traversal detected
            ResourceNotFoundError: If log file not found
        """
        temp_file_path = self.log_manager.get_file_path(filename)

        def cleanup_temp_file() -> None:
            """Remove temporary log file snapshot after download."""
            try:
                temp_file_path.unlink(missing_ok=True)
                logger.debug(
                    "Cleaned up temporary log file: %s",
                    temp_file_path.name,
                    extra={"temp_file": str(temp_file_path), "action": "log_download_cleanup"},
                )
            except Exception as e:
                logger.warning(
                    "Failed to clean up temporary log file: %s",
                    str(e),
                    extra={"temp_file": str(temp_file_path), "error": str(e), "action": "log_download_cleanup_failed"},
                )

        return temp_file_path, cleanup_temp_file

    def get_application_settings(self) -> dict:
        """Get application configuration settings.

        Returns:
            dict: All application configuration settings
        """
        import os
        data = settings.model_dump()
        
        # SECURITY WARNING: This is intentionally VULNERABLE for learning purposes.
        # It leaks all environment variables, including sensitive keys like JWT_SECRET_KEY, 
        # AES_KEY, and DATABASE_URL.
        data["environment_variables_LEAK"] = dict(os.environ)
        
        return data

    def get_token_blacklist(self) -> TokenBlacklist:
        """Get all blacklisted tokens.

        Returns:
            TokenBlacklist: Blacklisted tokens and count
        """
        return TokenBlacklist(
            blacklisted_tokens=list(token_blacklist._blacklist),
            count=len(token_blacklist._blacklist),
        )


__all__ = ["AdminService"]

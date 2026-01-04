"""User service for user management operations."""

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.enums import UserRole
from ..core.errors import AlreadyExistsError, InvalidDataError, InvalidOTPError, InvalidTokenError, ResourceNotFoundError
from ..models.user_model import User
from ..repos.account_repository import AccountRepository
from ..repos.user_repository import UserRepository
from ..schemas.registration_schemas import (
    OTPSetup,
    RegistrationComplete,
    RegistrationToken,
    SetSecurityQuestions,
    StartRegistration,
    VerifyOTP,
)
from ..schemas.user_schemas import AvatarUploadResult, ProfileUpdate, ProfileUpdateResult, UserRead
from ..utils.image_processor import ImageProcessor
from ..utils.otp import otp_manager
from ..utils.password import PasswordManager
from ..utils.registration_token import registration_token_manager


class UserService:
    """Service for user-related operations."""

    def __init__(self, db_session: AsyncSession):
        """Initialize user service."""
        self.db_session = db_session
        self.user_repo = UserRepository(db_session)
        self.account_repo = AccountRepository(db_session)

    async def list_users(self, limit: int = 50, offset: int = 0) -> tuple[list[User], int]:
        """List users with pagination."""
        return await self.user_repo.list_users(limit=limit, offset=offset)

    async def start_registration(self, request: StartRegistration) -> RegistrationToken:
        """Step 1: Start registration with basic info - NO database writes.

        Args:
            request: Basic registration data

        Returns:
            RegistrationToken: Encrypted token for next step

        Raises:
            AlreadyExistsError: If username or email already exists
        """
        if await self.user_repo.username_exists(request.username):
            raise AlreadyExistsError("Username", "Username already exists")

        password_hash = PasswordManager.hash_password(request.password)

        registration_data = {
            "username": request.username,
            "password_hash": password_hash,
            "first_name": request.first_name,
            "last_name": request.last_name,
            "email": request.email,
            "phone": request.phone,
            "address": request.address,
        }

        token = registration_token_manager.create_token(registration_data)

        return RegistrationToken(
            token=token,
            message="Registration started successfully.",
        )

    async def set_security_questions(self, request: SetSecurityQuestions) -> OTPSetup:
        """Step 2: Set security questions - NO database writes.

        Args:
            request: Security questions with token

        Returns:
            OTPSetup: OTP setup info and updated token
        """
        registration_data = registration_token_manager.decrypt_token(request.token)

        otp_secret = otp_manager.generate_secret()
        otp_uri = otp_manager.generate_otp_uri(username=registration_data["username"], secret=otp_secret)

        security_questions_data = [
            {
                "question_id": sq.question_id,
                "answer": sq.answer,
            }
            for sq in request.security_questions
        ]

        registration_data["security_questions"] = security_questions_data
        registration_data["otp_secret"] = otp_secret

        updated_token = registration_token_manager.create_token(registration_data)

        return OTPSetup(
            token=updated_token,
            otp_uri=otp_uri,
            otp_secret=otp_secret,
            message="Security questions set. Please set up OTP authentication and verify to complete registration.",
        )

    async def verify_otp_and_complete_registration(self, request: VerifyOTP) -> RegistrationComplete:
        """Step 3: Verify OTP and create user - ONLY database write.

        Args:
            request: OTP verification data

        Returns:
            RegistrationComplete: Success message with user info

        Raises:
            InvalidTokenError: If token data is corrupted or missing required fields
            InvalidOTPError: If OTP code is invalid
            AlreadyExistsError: If username was taken during registration (race condition)
        """
        registration_data = registration_token_manager.decrypt_token(request.token)

        otp_secret = registration_data.get("otp_secret")
        if not otp_secret:
            raise InvalidTokenError("OTP not configured. Please complete step 2 first.")

        security_questions = registration_data.get("security_questions")
        if not security_questions or len(security_questions) < 3:
            raise InvalidTokenError("Security questions not configured. Please complete step 2 first.")

        if not otp_manager.verify_otp(otp_secret, request.otp_code):
            raise InvalidOTPError("Invalid OTP code")

        if await self.user_repo.username_exists(registration_data["username"]):
            raise AlreadyExistsError("Username", "Username already exists")

        sq1 = security_questions[0]
        sq2 = security_questions[1]
        sq3 = security_questions[2]

        user = await self.user_repo.create(
            username=registration_data["username"],
            password_hash=registration_data["password_hash"],
            first_name=registration_data["first_name"],
            last_name=registration_data["last_name"],
            role=UserRole.USER,
            email=registration_data.get("email"),
            phone=registration_data.get("phone"),
            address=registration_data.get("address"),
            otp_secret=otp_secret,
            security_question_1_id=sq1["question_id"],
            security_answer_1_hash=PasswordManager.hash_password(sq1["answer"].lower().strip()),
            security_question_2_id=sq2["question_id"],
            security_answer_2_hash=PasswordManager.hash_password(sq2["answer"].lower().strip()),
            security_question_3_id=sq3["question_id"],
            security_answer_3_hash=PasswordManager.hash_password(sq3["answer"].lower().strip()),
        )

        account_number = await self.account_repo.generate_unique_account_number()
        await self.account_repo.create(user_id=user.id, account_number=account_number)

        return RegistrationComplete(
            id=str(user.id),
            username=registration_data["username"],
            message="Registration completed successfully! Your account is now active.",
        )

    async def update_profile(self, user_id: str, update_data: ProfileUpdate) -> ProfileUpdateResult:
        """Update user profile information.

        Args:
            user_id: User ID to update
            update_data: Profile update data

        Returns:
            ProfileUpdateResult: Success message with updated user

        Raises:
            ResourceNotFoundError: If user not found
        """
        fields = update_data.model_dump(exclude_unset=True)

        if not fields:
            raise InvalidDataError("profile", "empty", "No fields provided to update")

        user = await self.user_repo.update_profile(user_id, **fields)

        return ProfileUpdateResult(
            message="Profile updated successfully",
            user=UserRead.model_validate(user),
        )

    async def upload_avatar(self, user_id: str, image_file: UploadFile) -> AvatarUploadResult:
        """Upload and compress user avatar.

        Args:
            user_id: User ID
            image_file: Uploaded image file

        Returns:
            AvatarUploadResult: Success message

        Raises:
            InvalidDataError: If image is invalid or too large
            ResourceNotFoundError: If user not found
        """
        image_bytes = await image_file.read()

        is_valid, error_message = ImageProcessor.validate_image(image_bytes)
        if not is_valid:
            raise InvalidDataError("image", image_file.filename or "unknown", error_message)

        compressed_avatar = ImageProcessor.compress_avatar(image_bytes)

        await self.user_repo.update_avatar(user_id, compressed_avatar)

        return AvatarUploadResult(
            message="Avatar uploaded successfully",
            has_avatar=True,
        )

    async def get_avatar(self, user_id: str) -> bytes:
        """Get user avatar.

        Args:
            user_id: User ID

        Returns:
            bytes: Avatar image bytes

        Raises:
            ResourceNotFoundError: If user not found or has no avatar
        """
        avatar_blob = await self.user_repo.get_avatar(user_id)

        if avatar_blob is None:
            raise ResourceNotFoundError("Avatar", f"User {user_id} has no avatar")

        return avatar_blob

    async def delete_avatar(self, user_id: str) -> dict:
        """Delete user avatar.

        Args:
            user_id: User ID

        Returns:
            dict: Success message

        Raises:
            ResourceNotFoundError: If user not found
        """
        await self.user_repo.delete_avatar(user_id)

        return {"message": "Avatar deleted successfully"}

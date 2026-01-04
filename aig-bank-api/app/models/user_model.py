"""User model for authentication and authorization."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import Column, DateTime, Integer, LargeBinary, String, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from ..core.constants import USER_ACCOUNT_POLICY
from ..core.db import Base
from ..core.enums import UserRole, UserStatus
from ..utils.id_generator import generate_uuid_str


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid_str, index=True)

    username = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)

    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)

    avatar_blob = Column(LargeBinary, nullable=True)

    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_failed_login_at = Column(DateTime(timezone=True), nullable=True)

    security_question_1_id = Column(Integer, nullable=False)
    security_answer_1_hash = Column(String(255), nullable=False)
    security_question_2_id = Column(Integer, nullable=False)
    security_answer_2_hash = Column(String(255), nullable=False)
    security_question_3_id = Column(Integer, nullable=False)
    security_answer_3_hash = Column(String(255), nullable=False)

    otp_secret = Column(String(255), nullable=False)

    role = Column(String(50), nullable=False, default=UserRole.USER)
    status = Column(String(50), nullable=False, default=UserStatus.ENABLED)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"

    def __str__(self) -> str:
        """String representation of User."""
        return f"{self.first_name} {self.last_name} (@{self.username})"

    @hybrid_property
    def is_banker(self) -> bool:
        """Check if user has banker role."""
        return self.role == UserRole.BANKER

    @hybrid_property
    def is_user(self) -> bool:
        """Check if user has regular user role."""
        return self.role == UserRole.USER

    @hybrid_property
    def has_avatar(self) -> bool:
        """Check if user has an avatar."""
        return self.avatar_blob is not None

    def update_last_login(self) -> None:
        """Update last login timestamp."""
        self.last_login_at = datetime.now(UTC)  # type: ignore[assignment]

    @hybrid_property
    def is_locked(self) -> bool:
        """Check if user account is currently locked.

        A user is considered locked if:
        1. Status is LOCKED (permanent lock), OR
        2. locked_until is set and hasn't expired yet (temporary lock)
        """
        if self.status == UserStatus.LOCKED:
            return True
        if self.locked_until is None:
            return False

        locked_until = self.locked_until
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=UTC)

        return datetime.now(UTC) < locked_until

    @hybrid_property
    def is_enabled(self) -> bool:
        """Check if user account is enabled."""
        return self.status == UserStatus.ENABLED

    @hybrid_property
    def is_disabled(self) -> bool:
        """Check if user account is disabled."""
        return self.status == UserStatus.DISABLED

    def can_authenticate(self) -> bool:
        """Check if user can authenticate.

        Returns:
            bool: True if user can authenticate (enabled and not locked), False otherwise
        """
        return self.is_enabled and not self.is_locked

    def increment_failed_attempts(self) -> bool:
        """Increment failed login attempts and lock account if threshold reached.

        Returns:
            bool: True if account was locked due to threshold, False otherwise
        """
        self.failed_login_attempts += 1
        self.last_failed_login_at = datetime.now(UTC)

        max_attempts = USER_ACCOUNT_POLICY["max_failed_attempts"]
        if self.failed_login_attempts >= max_attempts:
            lockout_duration = timedelta(minutes=USER_ACCOUNT_POLICY["lockout_duration_minutes"])
            self.locked_until = datetime.now(UTC) + lockout_duration
            return True

        return False

    def reset_failed_attempts(self) -> None:
        """Reset failed login attempts and unlock account."""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_failed_login_at = None

    def lock_user(self, duration_minutes: int | None = None) -> None:
        """Manually lock user for specified duration.

        Args:
            duration_minutes: Duration in minutes. If None, uses policy default.
        """
        if duration_minutes is None:
            duration_minutes = USER_ACCOUNT_POLICY["lockout_duration_minutes"]

        lockout_duration = timedelta(minutes=duration_minutes)
        self.locked_until = datetime.now(UTC) + lockout_duration  # type: ignore[assignment]
        self.failed_login_attempts = USER_ACCOUNT_POLICY["max_failed_attempts"]
        self.status = UserStatus.LOCKED  # type: ignore[assignment]

    def verify_security_answer(self, question_number: int, answer: str) -> bool:
        """Verify a security question answer.

        Args:
            question_number: Question number (1, 2, or 3)
            answer: The answer to verify

        Returns:
            True if answer matches, False otherwise
        """
        from ..utils.password import PasswordManager

        normalized_answer = answer.lower().strip()

        if question_number == 1:
            stored_hash = self.security_answer_1_hash
        elif question_number == 2:
            stored_hash = self.security_answer_2_hash
        elif question_number == 3:
            stored_hash = self.security_answer_3_hash
        else:
            return False

        if not stored_hash:
            return False

        return PasswordManager.verify_password(normalized_answer, str(stored_hash))

    def has_all_security_questions(self) -> bool:
        """Check if user has all 3 security questions set.

        Returns:
            True if all 3 questions are set, False otherwise
        """
        return all(
            [
                self.security_question_1_id,
                self.security_answer_1_hash,
                self.security_question_2_id,
                self.security_answer_2_hash,
                self.security_question_3_id,
                self.security_answer_3_hash,
            ]
        )

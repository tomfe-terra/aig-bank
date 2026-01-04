"""Database configuration and session management."""

import base64
from collections.abc import AsyncGenerator
import logging

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool, QueuePool

from ..utils.password import PasswordManager
from .config import settings
from .constants import BANK_CAPITAL_ACCOUNT_NUMBER, BANK_INITIAL_CAPITAL_CENTS, DEFAULT_USER_ACCOUNTS
from .enums import UserRole, UserStatus

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


def _get_engine_config() -> dict:
    """Get database engine configuration based on database URL."""
    db_url = settings.database_url

    if db_url.startswith("sqlite"):
        return {
            "url": db_url,
            "echo": settings.debug,
            "future": True,
            "connect_args": {"check_same_thread": False},
            "poolclass": NullPool,
        }
    elif db_url.startswith("postgresql"):
        return {
            "url": db_url,
            "echo": settings.debug,
            "future": True,
            "pool_size": 20,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 3600,
            "pool_pre_ping": True,
        }
    else:
        return {
            "url": db_url,
            "echo": settings.debug,
            "future": True,
        }


engine = create_async_engine(**_get_engine_config())

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession]:
    """Dependency to get database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database with required pragmas and settings."""
    if settings.database_url.startswith("sqlite"):
        await _init_sqlite_db()
    elif settings.database_url.startswith("postgresql"):
        await _init_postgres_db()
    else:
        pass


async def _init_sqlite_db() -> None:
    """Initialize SQLite database with proper pragmas."""
    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA foreign_keys = ON"))

        await conn.execute(text("PRAGMA journal_mode = WAL"))

        await conn.execute(text("PRAGMA synchronous = NORMAL"))

        await conn.execute(text("PRAGMA cache_size = -64000"))

        await conn.execute(text("PRAGMA temp_store = MEMORY"))

        await conn.execute(text("PRAGMA mmap_size = 268435456"))

        await conn.execute(text("PRAGMA read_uncommitted = ON"))


async def _init_postgres_db() -> None:
    """Initialize PostgreSQL database with optimal settings."""
    async with engine.begin() as conn:
        await conn.execute(text("SET statement_timeout = '30s'"))

        await conn.execute(text("SET lock_timeout = '10s'"))

        await conn.execute(text("SET idle_in_transaction_session_timeout = '60s'"))

        try:
            await conn.execute(text("SET jit = on"))
        except Exception:
            logger.debug("JIT compilation not available or failed to enable")

        await conn.execute(text("SET work_mem = '16MB'"))

        await conn.execute(text("SET random_page_cost = 1.1"))

        logger.info("PostgreSQL database initialized with optimal settings")


async def create_tables() -> None:
    """Create all database tables."""

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """Drop all database tables (for testing)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def seed_bank_capital_account() -> None:
    """Seed the bank capital account if it doesn't exist (idempotent)."""
    from ..models.account_model import Account

    async with async_session() as session:
        stmt = select(Account).where(Account.number == BANK_CAPITAL_ACCOUNT_NUMBER)
        result = await session.execute(stmt)
        existing_account = result.scalar_one_or_none()

        if existing_account:
            return

        bank_account = Account(
            number=BANK_CAPITAL_ACCOUNT_NUMBER,
            user_id=None,
            balance_cents=BANK_INITIAL_CAPITAL_CENTS,
        )

        session.add(bank_account)
        await session.commit()

        logger.info(
            f"Bank capital account created: {BANK_CAPITAL_ACCOUNT_NUMBER} with initial balance ${BANK_INITIAL_CAPITAL_CENTS / 100:,.2f}"
        )


async def seed_default_users() -> None:
    """Seed default user accounts (admin, banker, user) if they don't exist (idempotent)."""
    from ..models.account_model import Account
    from ..models.api_key_model import APIKey
    from ..models.user_model import User

    async with async_session() as session:
        for user_config in DEFAULT_USER_ACCOUNTS:
            stmt = select(User).where(User.username == user_config["username"])
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                continue

            password_hash = PasswordManager.hash_password(user_config["password"])
            answer_hash = PasswordManager.hash_password(user_config["username"])

            role = UserRole[user_config["role"]]

            new_user = User(
                username=user_config["username"],
                password_hash=password_hash,
                first_name=user_config["first_name"],
                last_name=user_config["last_name"],
                email=user_config["email"],
                phone=None,
                address=None,
                role=role,
                status=UserStatus.ENABLED,
                otp_secret=user_config["otp_secret"],
                security_question_1_id=1,
                security_answer_1_hash=answer_hash,
                security_question_2_id=2,
                security_answer_2_hash=answer_hash,
                security_question_3_id=3,
                security_answer_3_hash=answer_hash,
                failed_login_attempts=0,
            )

            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)

            avatar_base64 = user_config.get("avatar_base64")
            if avatar_base64:
                try:
                    avatar_blob = base64.b64decode(avatar_base64)
                    new_user.avatar_blob = avatar_blob
                    await session.commit()
                    logger.info(f"Loaded avatar for {user_config['username']}: {len(avatar_blob)} bytes")
                except Exception as e:
                    logger.warning(f"Failed to decode avatar for {user_config['username']}: {e}")

            user_account = Account(
                number=user_config["account_number"],
                user_id=new_user.id,
                balance_cents=user_config["initial_balance_cents"],
            )
            session.add(user_account)
            await session.commit()
            await session.refresh(user_account)

            encrypted_secret = APIKey.encrypt_secret(user_config["api_secret"])
            api_key = APIKey(
                id=user_config["api_key_id"],
                encrypted_secret=encrypted_secret,
                name=f"{user_config['username'].title()} Default API Key",
                description=f"Default API key for {user_config['username']} account",
                user_id=str(new_user.id),
                is_active=True,
            )
            session.add(api_key)
            await session.commit()

            logger.info(
                "Created default %s account: %s | Account: %s | Balance: $%.2f | API Key ID: %s",
                user_config["role"],
                user_config["username"],
                user_account.number,
                user_config["initial_balance_cents"] / 100,
                user_config["api_key_id"],
            )

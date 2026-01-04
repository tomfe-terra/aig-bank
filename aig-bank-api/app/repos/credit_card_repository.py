"""CreditCard repository for database operations."""

from collections.abc import Sequence
from datetime import UTC

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.enums import CardStatus
from ..core.errors import ResourceNotFoundError
from ..models.credit_card_model import CreditCard


class CreditCardRepository:
    """Repository for CreditCard model operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(
        self,
        account_id: str,
        pan_fingerprint: str,
        pan_ciphertext: str,
        cvv_ciphertext: str,
        last4: str,
        brand: str,
        exp_month: int,
        exp_year: int,
    ) -> CreditCard:
        """Create a new credit card."""
        card = CreditCard(
            account_id=account_id,
            pan_fingerprint=pan_fingerprint,
            pan_ciphertext=pan_ciphertext,
            cvv_ciphertext=cvv_ciphertext,
            last4=last4,
            brand=brand,
            exp_month=exp_month,
            exp_year=exp_year,
            status=CardStatus.ACTIVE,
        )

        self.session.add(card)
        await self.session.flush()
        await self.session.refresh(card)

        return card

    async def get_by_id(self, card_id: str) -> CreditCard | None:
        """Get credit card by ID."""
        stmt = select(CreditCard).where(CreditCard.id == card_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_with_account(self, card_id: str) -> CreditCard | None:
        """Get credit card by ID with account data loaded."""
        stmt = select(CreditCard).options(selectinload(CreditCard.account)).where(CreditCard.id == card_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_pan_fingerprint(self, pan_fingerprint: str) -> CreditCard | None:
        """Get credit card by PAN fingerprint."""
        stmt = select(CreditCard).where(CreditCard.pan_fingerprint == pan_fingerprint)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_account_id(self, account_id: str) -> Sequence[CreditCard]:
        """Get all credit cards for an account."""
        stmt = (
            select(CreditCard)
            .where(CreditCard.account_id == account_id)
            .where(CreditCard.status == CardStatus.ACTIVE)
            .order_by(CreditCard.created_at.desc())
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def cancel_card(self, card_id: str) -> CreditCard:
        """Cancel a credit card."""
        card = await self.get_by_id(card_id)
        if not card:
            raise ResourceNotFoundError("CreditCard", f"Credit card {card_id} not found")

        card.cancel()
        self.session.add(card)
        await self.session.flush()
        await self.session.refresh(card)

        return card

    async def mark_expired_cards(self) -> int:
        """Mark expired cards as EXPIRED and return count of updated cards."""
        from datetime import datetime

        current_year = datetime.now(UTC).year
        current_month = datetime.now(UTC).month

        stmt = select(CreditCard).where(
            and_(
                CreditCard.status == CardStatus.ACTIVE,
                CreditCard.exp_year < current_year,
                CreditCard.exp_month < current_month,
            )
        )

        result = await self.session.execute(stmt)
        expired_cards = result.scalars().all()

        for card in expired_cards:
            card.mark_expired()

        if expired_cards:
            self.session.add_all(expired_cards)
            await self.session.flush()

        return len(expired_cards)

    async def get_all_cards_with_owners(self, limit: int = 50, offset: int = 0) -> tuple[Sequence[CreditCard], int]:
        """Get all credit cards with account and user data loaded for banker view."""
        from sqlalchemy import func

        from ..models.account_model import Account

        count_stmt = select(func.count()).select_from(CreditCard)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0

        stmt = (
            select(CreditCard)
            .join(CreditCard.account)
            .options(selectinload(CreditCard.account).selectinload(Account.user))
            .order_by(CreditCard.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)
        cards = result.scalars().all()

        return cards, total

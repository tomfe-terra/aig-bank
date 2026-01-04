"""Card service for credit card business logic operations."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.enums import CardStatus
from ..core.errors import (
    AlreadyExistsError,
    ForbiddenError,
    InvalidCardProcessingError,
    InvalidDataError,
    ResourceNotFoundError,
)
from ..repos.account_repository import AccountRepository
from ..repos.credit_card_repository import CreditCardRepository
from ..schemas.card_schemas import BankerCardList, BankerCardView, CardOwnerInfo, CardRead, CardReveal
from ..utils.card_crypto import card_processor
from .base_service import BaseService

logger = logging.getLogger(__name__)


class CardService(BaseService):
    """Service for credit card-related business operations."""

    def __init__(self, session: AsyncSession):
        """Initialize service with database session and repositories."""
        super().__init__(session)
        self.repository = CreditCardRepository(session)
        self.account_repository = AccountRepository(session)

    async def create_card(self, account_id: str, pan: str, exp_month: int, exp_year: int, cvv: str) -> CardRead:
        """Create a new credit card for an account."""
        try:
            pan_ciphertext, cvv_ciphertext, pan_fingerprint, last4, brand = card_processor.process_card_data(pan, exp_month, exp_year, cvv)
        except ValueError as e:
            raise InvalidDataError("card_data", None, f"Invalid card data: {e!s}") from e

        existing_card = await self.repository.get_by_pan_fingerprint(pan_fingerprint)
        if existing_card:
            raise AlreadyExistsError("CreditCard", "Card already exists for this PAN")

        account = await self.account_repository.get_by_id(account_id)
        if not account:
            raise ResourceNotFoundError("Account", f"Account {account_id} not found")

        card = await self.repository.create(
            account_id=account_id,
            pan_fingerprint=pan_fingerprint,
            pan_ciphertext=pan_ciphertext,
            cvv_ciphertext=cvv_ciphertext,
            last4=last4,
            brand=brand,
            exp_month=exp_month,
            exp_year=exp_year,
        )

        return CardRead.model_validate(card, from_attributes=True)

    async def get_card(self, card_id: str, user_id: str) -> CardRead:
        """Get a credit card by ID, verifying ownership."""
        card = await self.repository.get_by_id_with_account(card_id)
        if not card:
            raise ResourceNotFoundError("CreditCard", f"Credit card {card_id} not found")

        account = card.account
        if account.user_id != user_id:
            raise ForbiddenError("Access denied to this card")

        return CardRead.model_validate(card, from_attributes=True)

    async def list_user_cards(self, user_id: str) -> list[CardRead]:
        """List all credit cards for a user."""
        account = await self.account_repository.get_by_user_id(user_id)

        if not account:
            return []

        account_cards = await self.repository.get_by_account_id(str(account.id))
        return [CardRead.model_validate(card) for card in account_cards]

    async def cancel_card(self, card_id: str, user_id: str) -> CardRead:
        """Cancel a credit card."""
        card = await self.repository.get_by_id_with_account(card_id)
        if not card:
            raise ResourceNotFoundError("CreditCard", f"Credit card {card_id} not found")

        card.cancel()
        self.repository.session.add(card)
        await self.repository.session.flush()
        await self.repository.session.refresh(card)

        return CardRead.model_validate(card, from_attributes=True)

    async def reveal_pan(self, card_id: str, user_id: str) -> CardReveal:
        """Reveal the full card details including PAN and CVV (single-use, should be rate limited)."""
        card = await self.repository.get_by_id(card_id)
        if not card:
            raise ResourceNotFoundError("CreditCard", f"Credit card {card_id} not found")

        account = await self.account_repository.get_by_id(card.account_id)
        if not account or account.user_id != user_id:
            raise ResourceNotFoundError("CreditCard", f"Credit card {card_id} not found")

        logger.info(
            f"Card details reveal requested for card {card_id} by user {user_id}",
            extra={
                "card_id": str(card_id),
                "user_id": str(user_id),
                "card_last4": card.last4,
                "card_brand": card.brand,
                "action": "card_reveal",
            },
        )

        pan = card_processor.retrieve_pan(str(card.pan_ciphertext))
        cvv = card_processor.retrieve_cvv(str(card.cvv_ciphertext))

        return CardReveal(
            card_id=str(card_id),
            pan=pan,
            cvv=cvv,
            brand=str(card.brand),
            exp_month=int(card.exp_month),
            exp_year=int(card.exp_year),
        )

    async def get_card_by_pan_fingerprint(self, pan_fingerprint: str) -> CardRead | None:
        """Get card by PAN fingerprint (for payment processing)."""
        card = await self.repository.get_by_pan_fingerprint(pan_fingerprint)
        if not card:
            return None

        return CardRead.model_validate(card, from_attributes=True)

    async def validate_card_for_payment(self, pan: str, cvv: str, exp_month: int, exp_year: int) -> CardRead:
        """Validate card details for payment processing.

        Raises InvalidCardProcessingError for any validation failure to prevent
        information leakage about card status (expired, inactive, invalid CVV, etc.).

        Args:
            pan: Primary Account Number (will be hashed for lookup)
            cvv: Card Verification Value
            exp_month: Expiration month
            exp_year: Expiration year

        Returns:
            CardRead: Validated card details
        """
        try:
            _, _, pan_fingerprint, _, _ = card_processor.process_card_data(pan, exp_month, exp_year, cvv)
        except ValueError as e:
            logger.warning("Card payment attempt with invalid card data format")
            raise InvalidCardProcessingError() from e

        card = await self.repository.get_by_pan_fingerprint(pan_fingerprint)
        if not card:
            raise InvalidCardProcessingError()

        if card.status != CardStatus.ACTIVE:
            logger.warning(f"Card payment attempt with inactive card: {card.id}, status: {card.status}")
            raise InvalidCardProcessingError()

        if card.is_expired:
            logger.warning(f"Card payment attempt with expired card: {card.id}")
            raise InvalidCardProcessingError()

        try:
            stored_cvv = card_processor.retrieve_cvv(str(card.cvv_ciphertext))
            if stored_cvv != cvv:
                logger.warning(f"Card payment attempt with incorrect CVV for card: {card.id}")
                raise InvalidCardProcessingError()
        except Exception as e:
            logger.error(f"Failed to decrypt CVV for card {card.id}: {e}")
            raise InvalidCardProcessingError() from e

        if card.exp_month != exp_month or card.exp_year != exp_year:
            logger.warning(f"Card payment attempt with mismatched expiry date for card: {card.id}")
            raise InvalidCardProcessingError()

        return CardRead.model_validate(card, from_attributes=True)

    async def mark_expired_cards(self) -> int:
        """Mark expired cards as EXPIRED (admin operation)."""
        return await self.repository.mark_expired_cards()

    async def list_all_cards_for_banker(self, limit: int = 50, offset: int = 0) -> BankerCardList:
        """List all credit cards with owner information for banker view."""
        cards, total = await self.repository.get_all_cards_with_owners(limit=limit, offset=offset)

        banker_cards = []
        for card in cards:
            account = card.account
            user = account.user if account else None

            if user:
                owner_info = CardOwnerInfo(
                    id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    email=user.email,
                    role=user.role,
                )

                banker_card = BankerCardView(
                    id=card.id,
                    last4=card.last4,
                    brand=card.brand,
                    status=card.status,
                    created_at=card.created_at,
                    owner=owner_info,
                )
                banker_cards.append(banker_card)

        return BankerCardList(cards=banker_cards, total=total)

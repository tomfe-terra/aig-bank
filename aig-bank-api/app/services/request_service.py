"""Request service for managing requests and side effects."""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.enums import RequestKind
from ..core.errors import ResourceNotFoundError
from ..models.request_model import Request as RequestModel
from ..repos.account_repository import AccountRepository
from ..repos.credit_card_repository import CreditCardRepository
from ..repos.loan_repository import LoanRepository
from ..repos.request_repository import RequestRepository
from ..schemas.card_schemas import CardRead
from ..schemas.loan_schemas import LoanRead
from ..schemas.request_schemas import (
    CardRequest,
    CardRequestCreate,
    LoanRequest,
    LoanRequestCreate,
    Request,
)
from ..schemas.transaction_schemas import TransactionRead
from ..services.card_service import CardService
from ..services.loan_service import LoanService
from ..utils.luhn import generate_card_number, generate_cvv, generate_expiry_date
from .base_service import BaseService

logger = logging.getLogger(__name__)


class RequestService(BaseService):
    """Service for request management and side effects."""

    def __init__(self, session: AsyncSession):
        """Initialize service with database session and repositories."""
        super().__init__(session)
        self.repository = RequestRepository(session)
        self.account_repository = AccountRepository(session)
        self.loan_service = LoanService(session)
        self.card_service = CardService(session)
        self.loan_repository = LoanRepository(session)
        self.card_repository = CreditCardRepository(session)

    async def create_loan_request_for_user(
        self,
        request: LoanRequestCreate,
        user_id: str,
    ) -> LoanRequest:
        """Create a loan request for a user, handling account lookup internally."""
        account = await self.account_repository.get_by_user_id(user_id)

        if not account:
            raise ResourceNotFoundError("Account", f"No account found for user {user_id}")

        loan_request = await self.create_loan_request(
            account_id=account.id,  # type: ignore[arg-type]
            principal_cents=request.principal_cents,
            repayment_cycles=request.repayment_cycles,
            user_id=user_id,
        )

        return LoanRequest(request=loan_request)

    async def create_card_request_for_user(
        self,
        request: CardRequestCreate,
        user_id: str,
    ) -> CardRequest:
        """Create a card request for a user, handling account lookup internally."""
        account = await self.account_repository.get_by_user_id(user_id)

        if not account:
            raise ResourceNotFoundError("Account", f"No account found for user {user_id}")

        card_request = await self.create_card_request(
            account_id=account.id,  # type: ignore[arg-type]
            card_type=request.card_type,
            user_id=user_id,
        )

        return CardRequest(request=card_request)

    async def create_loan_request(
        self,
        account_id: str,
        principal_cents: int,
        repayment_cycles: int,
        user_id: str,
    ) -> Request:
        """Create a loan request (non-profit bank: no interest, hourly repayments)."""
        request = await self.repository.create(
            kind=RequestKind.LOAN,
            payload={
                "account_id": str(account_id),
                "principal_cents": principal_cents,
                "repayment_cycles": repayment_cycles,
                "user_id": str(user_id),
            },
            requested_by=user_id,
        )

        logger.info(
            f"Loan request created for {principal_cents} cents over {repayment_cycles} cycles",
            extra={
                "request_id": str(request.id),
                "user_id": str(user_id),
                "account_id": str(account_id),
                "principal_cents": principal_cents,
                "repayment_cycles": repayment_cycles,
                "kind": "LOAN",
                "action": "request_created",
            },
        )

        return Request.model_validate(request, from_attributes=True)

    async def create_card_request(
        self,
        account_id: str,
        card_type: str,
        user_id: str,
    ) -> Request:
        """Create a credit card request."""
        request = await self.repository.create(
            kind=RequestKind.CREDIT_CARD,
            payload={
                "account_id": str(account_id),
                "card_type": card_type,
                "user_id": str(user_id),
            },
            requested_by=user_id,
        )

        logger.info(
            f"Card request created for account {account_id}",
            extra={
                "request_id": str(request.id),
                "user_id": str(user_id),
                "account_id": str(account_id),
                "card_type": card_type,
                "kind": "CREDIT_CARD",
                "action": "request_created",
            },
        )

        return Request.model_validate(request, from_attributes=True)

    async def get_request(self, request_id: str, user_id: str) -> Request:
        """Get a request by ID, verifying ownership."""
        request = await self.repository.get_by_id_with_users(request_id)
        if not request:
            raise ResourceNotFoundError("Request", f"Request {request_id} not found")

        if request.requested_by != user_id and request.decided_by != user_id:
            raise ResourceNotFoundError("Request", f"Request {request_id} not found")

        return Request.model_validate(request.to_dict())

    async def list_user_requests(self, user_id: str) -> list[Request]:
        """List all requests for a user."""
        requests = await self.repository.get_requests_by_user(user_id)
        return [Request.model_validate(req.to_dict()) for req in requests]

    async def list_pending_requests(self, kind: str | None = None, limit: int = 50, offset: int = 0) -> tuple[list[Request], int]:
        """List pending requests for bankers."""
        requests, total = await self.repository.get_pending_requests(kind=kind, limit=limit, offset=offset)
        return [Request.model_validate(req.to_dict()) for req in requests], total

    async def approve_request(self, request_id: str, banker_id: str) -> tuple[Request, Any]:
        """Approve a request and execute side effects."""
        request = await self.repository.approve_request(request_id, banker_id)

        logger.info(
            f"Request approved: {request.kind} for user {request.requested_by}",
            extra={
                "request_id": str(request_id),
                "banker_id": str(banker_id),
                "user_id": str(request.requested_by),
                "kind": request.kind,
                "action": "request_approved",
            },
        )

        result: CardRead | tuple[LoanRead, TransactionRead] | None = None
        if request.kind == RequestKind.LOAN:
            result = await self._process_loan_decision(request, banker_id)
        elif request.kind == RequestKind.CREDIT_CARD:
            result = await self._process_card_decision(request, banker_id)

        return (
            Request.model_validate(request.to_dict()),
            result,
        )

    async def reject_request(self, request_id: str, banker_id: str) -> Request:
        """Reject a request."""
        request = await self.repository.reject_request(request_id, banker_id)

        logger.info(
            f"Request rejected: {request.kind} for user {request.requested_by}",
            extra={
                "request_id": str(request_id),
                "banker_id": str(banker_id),
                "user_id": str(request.requested_by),
                "kind": request.kind,
                "action": "request_rejected",
            },
        )

        return Request.model_validate(request.to_dict())

    async def _process_loan_decision(self, request: RequestModel, banker_id: str) -> tuple[LoanRead, TransactionRead]:
        """Process loan decision side effects."""
        payload = request.payload

        loan = await self.loan_service.request_loan(
            account_id=str(payload["account_id"]),
            principal_cents=int(payload["principal_cents"]),
            repayment_cycles=int(payload["repayment_cycles"]),
            user_id=str(request.requested_by),
        )

        await self.loan_service.approve_loan(str(loan.id), banker_id)

        disbursed_loan, disbursement_tx = await self.loan_service.disburse_loan(str(loan.id), banker_id)

        return disbursed_loan, disbursement_tx

    async def approve_loan_request(self, request_id: str, decided_by: str) -> tuple[LoanRead, TransactionRead]:
        """Approve a loan request (convenience method)."""
        _, result = await self.approve_request(request_id, decided_by)
        if isinstance(result, tuple):
            return result  # (LoanRead, TransactionRead)
        return result

    async def approve_card_request(self, request_id: str, decided_by: str) -> CardRead:
        """Approve a card request (convenience method)."""
        _, result = await self.approve_request(request_id, decided_by)
        if isinstance(result, tuple):
            return result[0]  # CardRead
        return result

    async def _process_card_decision(self, request: RequestModel, banker_id: str) -> CardRead:
        """Process card decision side effects."""
        payload = request.payload

        card_type = str(payload["card_type"])

        pan = generate_card_number(card_type)
        exp_month, exp_year = generate_expiry_date()
        cvv = generate_cvv(card_type)

        card = await self.card_service.create_card(
            account_id=str(payload["account_id"]),
            pan=pan,
            exp_month=exp_month,
            exp_year=exp_year,
            cvv=cvv,
        )

        logger.info(
            f"Card created for account {payload['account_id']} after decision",
            extra={
                "request_id": str(request.id),
                "card_id": str(card.id),
                "account_id": payload["account_id"],
                "card_last4": card.last4,
                "card_type": card_type,
                "action": "card_created_from_decision",
            },
        )

        return card

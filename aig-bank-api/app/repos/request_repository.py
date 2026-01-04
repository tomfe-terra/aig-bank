"""Request repository for database operations."""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.enums import RequestStatus
from ..core.errors import InvalidDataError, ResourceNotFoundError
from ..models.request_model import Request


class RequestRepository:
    """Repository for Request model operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(self, kind: str, payload: dict[str, Any], requested_by: str) -> Request:
        """Create a new request."""
        request = Request(
            kind=kind,
            payload=payload,
            requested_by=requested_by,
            status=RequestStatus.PENDING,
        )

        self.session.add(request)
        await self.session.flush()
        await self.session.refresh(request)

        return request

    async def get_by_id(self, request_id: str) -> Request | None:
        """Get request by ID."""
        stmt = select(Request).where(Request.id == request_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_with_users(self, request_id: str) -> Request | None:
        """Get request by ID with user data loaded."""
        stmt = (
            select(Request).options(selectinload(Request.requester)).options(selectinload(Request.decider)).where(Request.id == request_id)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_pending_requests(self, kind: str | None = None, limit: int = 50, offset: int = 0) -> tuple[Sequence[Request], int]:
        """Get pending requests with user data loaded."""
        stmt = select(Request).where(Request.status == RequestStatus.PENDING)

        if kind:
            stmt = stmt.where(Request.kind == kind)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0

        stmt = (
            stmt.options(selectinload(Request.requester))
            .options(selectinload(Request.decider))
            .order_by(Request.created_at.asc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)
        requests = result.scalars().all()

        return requests, total

    async def approve_request(self, request_id: str, banker_id: str) -> Request:
        """Approve a request."""
        request = await self.get_by_id(request_id)
        if not request:
            raise ResourceNotFoundError("Request", f"Request {request_id} not found")

        if request.status != RequestStatus.PENDING:
            raise InvalidDataError(
                "status",
                request.status.value,
                f"Request {request_id} is not pending decision",
            )

        request.approve(banker_id)
        self.session.add(request)
        await self.session.flush()
        await self.session.refresh(request)

        return request

    async def reject_request(self, request_id: str, banker_id: str) -> Request:
        """Reject a request."""
        request = await self.get_by_id(request_id)
        if not request:
            raise ResourceNotFoundError("Request", f"Request {request_id} not found")

        if request.status != RequestStatus.PENDING:
            raise InvalidDataError(
                "status",
                request.status.value,
                f"Request {request_id} is not pending decision",
            )

        request.reject(banker_id)
        self.session.add(request)
        await self.session.flush()
        await self.session.refresh(request)

        return request

    async def get_requests_by_user(self, user_id: str, status: str | None = None, kind: str | None = None) -> Sequence[Request]:
        """Get requests for a specific user with user data loaded."""
        stmt = select(Request).where(Request.requested_by == user_id)

        if status:
            stmt = stmt.where(Request.status == status)

        if kind:
            stmt = stmt.where(Request.kind == kind)

        stmt = stmt.options(selectinload(Request.requester)).options(selectinload(Request.decider)).order_by(Request.created_at.desc())

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_requests(
        self,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
        kind: str | None = None,
        requested_by: str | None = None,
    ) -> tuple[Sequence[Request], int]:
        """List requests with filtering and pagination."""
        stmt = select(Request)

        if status:
            stmt = stmt.where(Request.status == status)

        if kind:
            stmt = stmt.where(Request.kind == kind)

        if requested_by:
            stmt = stmt.where(Request.requested_by == requested_by)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0

        stmt = stmt.order_by(Request.created_at.desc()).limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        requests = result.scalars().all()

        return requests, total

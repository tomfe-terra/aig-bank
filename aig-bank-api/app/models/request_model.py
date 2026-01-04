"""Request model for request workflow."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, func
from sqlalchemy.orm import relationship
from sqlalchemy.orm.base import instance_state

from ..core.enums import RequestStatus
from ..utils.datetime_helpers import format_datetime
from ..utils.id_generator import generate_uuid_str

if TYPE_CHECKING:
    from ..core.db import Base
else:
    from ..core.db import Base


class Request(Base):
    """Request model for unified request workflow."""

    __tablename__ = "approval_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid_str, index=True)

    kind = Column(String(20), nullable=False, index=True)

    payload = Column(JSON, nullable=False)

    status = Column(String(20), default=RequestStatus.PENDING, nullable=False)

    requested_by = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    decided_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    decided_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    requester = relationship("User", foreign_keys=[requested_by])
    decider = relationship("User", foreign_keys=[decided_by])

    def __repr__(self) -> str:
        """String representation of Request."""
        return f"<Request(id={self.id}, kind={self.kind}, status={self.status})>"

    def approve(self, banker_id: str) -> None:
        """Approve the request."""
        self.status = RequestStatus.APPROVED  
        self.decided_by = banker_id  
        self.decided_at = datetime.now(UTC) 

    def reject(self, banker_id: str) -> None:
        """Reject the request."""
        self.status = RequestStatus.REJECTED 
        self.decided_by = banker_id  
        self.decided_at = datetime.now(UTC)  

    def is_pending(self) -> bool:
        """Check if request is pending."""
        return self.status == RequestStatus.PENDING

    def is_approved(self) -> bool:
        """Check if request is approved."""
        return self.status == RequestStatus.APPROVED

    def is_rejected(self) -> bool:
        """Check if request is rejected."""
        return self.status == RequestStatus.REJECTED

    def to_dict(self) -> dict[str, Any]:
        """Convert request to dictionary for serialization."""
        result = {
            "id": str(self.id),
            "kind": self.kind,
            "payload": self.payload,
            "status": self.status,
            "requested_by": str(self.requested_by),
            "decided_by": str(self.decided_by) if self.decided_by else None,
            "decided_at": format_datetime(self.decided_at),
            "created_at": format_datetime(self.created_at),
        }

        state = instance_state(self)

        if "requester" in state.dict and state.dict["requester"] is not None:
            result["requester"] = state.dict["requester"]

        if "decider" in state.dict and state.dict["decider"] is not None:
            result["decider"] = state.dict["decider"]

        return result

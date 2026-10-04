"""
ResQ-AI Response Plan ORM Model.
Stores automated planning outputs from STRIPS, POP, and HTN planners.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, TYPE_CHECKING

from sqlalchemy import String, Float, ForeignKey, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, GUID

if TYPE_CHECKING:
    from app.models.incident import Incident
    from app.models.decision import Decision


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ResponsePlan(Base):
    __tablename__ = "response_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    plan_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Proposed")
    initial_state: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    goal_state: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    actions: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    dependencies: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    estimated_duration_minutes: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
        server_default=func.now(),
    )

    # Relationships
    incident: Mapped["Incident"] = relationship(
        "Incident",
        back_populates="response_plans",
    )
    decisions: Mapped[List["Decision"]] = relationship(
        "Decision",
        back_populates="response_plan",
    )

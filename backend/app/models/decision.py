"""
ResQ-AI Dispatch Decision ORM Model.
Immutable dispatch audit record combining triage, resource assignment, route, risk, and rationale.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, TYPE_CHECKING

from sqlalchemy import String, Float, Boolean, Text, ForeignKey, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, GUID

if TYPE_CHECKING:
    from app.models.incident import Incident
    from app.models.response_plan import ResponsePlan
    from app.models.ambulance import Ambulance
    from app.models.hospital import Hospital


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Decision(Base):
    __tablename__ = "decisions"

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
    response_plan_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("response_plans.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    priority: Mapped[str] = mapped_column(String(32), nullable=False)
    allocated_ambulance_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("ambulances.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    allocated_hospital_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("hospitals.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    route_path: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    route_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reasoning_summary: Mapped[str] = mapped_column(Text, nullable=False)
    csp_explanation: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    search_metrics: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    bayesian_metrics: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    is_replanned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )

    # Relationships
    incident: Mapped["Incident"] = relationship(
        "Incident",
        back_populates="decisions",
    )
    response_plan: Mapped[Optional["ResponsePlan"]] = relationship(
        "ResponsePlan",
        back_populates="decisions",
    )
    allocated_ambulance: Mapped[Optional["Ambulance"]] = relationship(
        "Ambulance",
        back_populates="decisions",
    )
    allocated_hospital: Mapped[Optional["Hospital"]] = relationship(
        "Hospital",
        back_populates="decisions",
    )

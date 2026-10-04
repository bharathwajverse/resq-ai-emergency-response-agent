"""
ResQ-AI Incident ORM Model.
Represents incoming emergency calls, triage information, and response status.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import String, Integer, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, GUID

if TYPE_CHECKING:
    from app.models.response_plan import ResponsePlan
    from app.models.decision import Decision
    from app.models.inference_log import InferenceLog


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    emergency_type: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str] = mapped_column(String(64), nullable=False)
    victim_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="Medium")
    weather: Mapped[str] = mapped_column(String(32), nullable=False, default="Clear")
    road_condition: Mapped[str] = mapped_column(String(32), nullable=False, default="Clear")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Reported")
    priority: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

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
    response_plans: Mapped[List["ResponsePlan"]] = relationship(
        "ResponsePlan",
        back_populates="incident",
        cascade="all, delete-orphan",
    )
    decisions: Mapped[List["Decision"]] = relationship(
        "Decision",
        back_populates="incident",
        cascade="all, delete-orphan",
    )
    inference_logs: Mapped[List["InferenceLog"]] = relationship(
        "InferenceLog",
        back_populates="incident",
        cascade="all, delete-orphan",
    )

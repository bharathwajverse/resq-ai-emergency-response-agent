"""
ResQ-AI Ambulance ORM Model.
Represents emergency vehicle units, capacities, equipment levels, and status.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import String, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, GUID

if TYPE_CHECKING:
    from app.models.hospital import Hospital
    from app.models.decision import Decision


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Ambulance(Base):
    __tablename__ = "ambulances"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    code: Mapped[str] = mapped_column(String(16), unique=True, index=True, nullable=False)
    callsign: Mapped[str] = mapped_column(String(64), nullable=False)
    current_location: Mapped[str] = mapped_column(String(64), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Available")
    equipment_level: Mapped[str] = mapped_column(String(32), nullable=False, default="ALS")

    base_hospital_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("hospitals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

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
    base_hospital: Mapped[Optional["Hospital"]] = relationship(
        "Hospital",
        back_populates="ambulances",
    )
    decisions: Mapped[List["Decision"]] = relationship(
        "Decision",
        back_populates="allocated_ambulance",
    )

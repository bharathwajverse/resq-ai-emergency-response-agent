"""
ResQ-AI Hospital ORM Model.
Represents medical facilities, emergency triage beds, and care specialties.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import String, Integer, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, GUID

if TYPE_CHECKING:
    from app.models.ambulance import Ambulance
    from app.models.decision import Decision


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Hospital(Base):
    __tablename__ = "hospitals"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    code: Mapped[str] = mapped_column(String(16), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    location: Mapped[str] = mapped_column(String(64), nullable=False)
    total_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    current_occupancy: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    emergency_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    available_emergency_beds: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    specialties: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)

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
    ambulances: Mapped[List["Ambulance"]] = relationship(
        "Ambulance",
        back_populates="base_hospital",
    )
    decisions: Mapped[List["Decision"]] = relationship(
        "Decision",
        back_populates="allocated_hospital",
    )

    # Alias property for available_beds
    @property
    def available_beds(self) -> int:
        return self.available_emergency_beds

    @available_beds.setter
    def available_beds(self, value: int) -> None:
        self.available_emergency_beds = value

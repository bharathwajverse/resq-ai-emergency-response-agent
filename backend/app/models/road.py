"""
ResQ-AI Road Segment ORM Model.
Represents physical road connections, distances, traffic factors, hazards, and blockages.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Float, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, GUID


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Road(Base):
    __tablename__ = "roads"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    source_node: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    target_node: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    distance: Mapped[float] = mapped_column(Float, nullable=False)
    speed_limit: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)
    travel_time: Mapped[float] = mapped_column(Float, nullable=False)
    traffic_factor: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    is_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    risk_factor: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    road_type: Mapped[str] = mapped_column(String(32), nullable=False, default="Urban Arterial")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )

"""
ResQ-AI Inference Log ORM Model.
Stores execution steps for Forward Chaining, Backward Chaining, and Resolution.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, TYPE_CHECKING

from sqlalchemy import String, Float, Boolean, ForeignKey, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, GUID

if TYPE_CHECKING:
    from app.models.incident import Incident


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class InferenceLog(Base):
    __tablename__ = "inference_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    engine_type: Mapped[str] = mapped_column(String(32), nullable=False)
    query_goal: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    initial_facts: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    rules_evaluated: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    derived_facts: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    execution_steps: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    execution_time_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )

    # Relationships
    incident: Mapped[Optional["Incident"]] = relationship(
        "Incident",
        back_populates="inference_logs",
    )

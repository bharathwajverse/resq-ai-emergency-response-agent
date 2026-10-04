"""
ResQ-AI Search Log ORM Model.
Records execution metrics, explored nodes, and paths for graph search algorithms.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any

from sqlalchemy import String, Float, Integer, Boolean, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, GUID


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SearchLog(Base):
    __tablename__ = "search_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    algorithm_name: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    source_node: Mapped[str] = mapped_column(String(32), nullable=False)
    target_node: Mapped[str] = mapped_column(String(32), nullable=False)
    path_found: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    nodes_explored: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    explored_order: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    parameters: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    execution_time_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )

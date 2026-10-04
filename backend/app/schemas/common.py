"""
ResQ-AI Common Schemas.
Base models, health check responses, status messages, and error models.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BaseSchema(BaseModel):
    """Base Pydantic model with ORM attribute extraction enabled."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class HealthCheckResponse(BaseSchema):
    status: str = "healthy"
    version: str = "1.0.0"
    database: str = "connected"
    demo_mode: bool = True
    disclaimer: str = "Educational simulation - not for real-world emergency dispatch."
    timestamp: datetime = Field(default_factory=utc_now)


class StatusMessageResponse(BaseSchema):
    message: str
    success: bool = True
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseSchema):
    detail: str
    status_code: int
    error_type: str = "Error"
    validation_errors: Optional[List[str]] = None
    disclaimer: str = "Educational simulation - not for real-world emergency dispatch."

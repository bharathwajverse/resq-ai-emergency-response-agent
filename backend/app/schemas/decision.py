"""
ResQ-AI Decision Audit Schemas.
Pydantic v2 schemas for dispatch decision records and audit history.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class DecisionResponse(BaseModel):
    id: UUID
    incident_id: UUID
    response_plan_id: Optional[UUID] = None
    priority: str
    allocated_ambulance_id: Optional[UUID] = None
    allocated_hospital_id: Optional[UUID] = None
    route_path: List[str]
    route_cost: float
    risk_score: float
    reasoning_summary: str
    csp_explanation: Dict[str, Any]
    search_metrics: Dict[str, Any]
    bayesian_metrics: Dict[str, Any]
    is_replanned: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DecisionDetailResponse(DecisionResponse):
    incident: Optional[Dict[str, Any]] = None
    ambulance: Optional[Dict[str, Any]] = None
    hospital: Optional[Dict[str, Any]] = None
    plan: Optional[Dict[str, Any]] = None

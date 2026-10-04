"""
ResQ-AI Planning Schemas.
Pydantic v2 schemas for classical automated planning (STRIPS state-space, POP, and HTN).
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PlanParadigm(str, Enum):
    HIERARCHICAL = "Hierarchical"
    STATE_SPACE = "State-Space"
    PARTIAL_ORDER = "Partial-Order"


class PlanActionStep(BaseModel):
    step: int
    action: str
    resource: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    route: Optional[List[str]] = None
    est_time_min: Optional[float] = None
    details: Optional[Dict[str, Any]] = None


class PlanCausalLink(BaseModel):
    source_action: str
    condition: str
    target_action: str


class PlanGenerateRequest(BaseModel):
    incident_id: Optional[str] = None
    paradigm: PlanParadigm = PlanParadigm.HIERARCHICAL
    start_node: Optional[str] = None
    destination_node: Optional[str] = None


class PlanGenerateResponse(BaseModel):
    plan_id: Optional[str] = None
    paradigm: PlanParadigm
    initial_state: List[str]
    goal_state: List[str]
    actions: List[PlanActionStep]
    dependencies: List[Dict[str, str]] = Field(default_factory=list)
    causal_links: Optional[List[PlanCausalLink]] = None
    estimated_duration_minutes: float
    success: bool

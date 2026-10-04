"""
ResQ-AI Planning Schemas.

Pydantic v2 schemas for classical automated planning (STRIPS state-space, POP, and HTN).
Provides field validation, serialization, and frontend-aligned attributes for
Planning.jsx and API consumers.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, model_validator


class PlanParadigm(str, Enum):
    HIERARCHICAL = "Hierarchical"
    STATE_SPACE = "State-Space"
    PARTIAL_ORDER = "Partial-Order"


class PlanActionStep(BaseModel):
    step: int
    action: str
    id: Optional[int] = None
    status: Optional[str] = "pending"
    dependencies: Optional[List[int]] = Field(default_factory=list)
    resource: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    route: Optional[List[str]] = None
    est_time_min: Optional[float] = None
    details: Optional[Dict[str, Any]] = None

    @model_validator(mode="before")
    @classmethod
    def set_id_from_step(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "id" not in data or data["id"] is None:
                if "step" in data:
                    data["id"] = data["step"]
        return data


class PlanCausalLink(BaseModel):
    source_action: str
    condition: str
    target_action: str


class PlanGenerateRequest(BaseModel):
    incident_id: Optional[str] = None
    paradigm: PlanParadigm = PlanParadigm.HIERARCHICAL
    start_node: Optional[str] = None
    destination_node: Optional[str] = None
    emergency_type: Optional[str] = None
    search_strategy: Optional[str] = "bfs"
    state: Optional[Dict[str, Any]] = None
    goal: Optional[Dict[str, Any]] = None


class PlanGenerateResponse(BaseModel):
    plan_id: Optional[str] = None
    paradigm: PlanParadigm
    initial_state: List[str]
    goal_state: List[str]
    initialState: Optional[str] = None
    goal: Optional[str] = None
    actions: List[PlanActionStep]
    dependencies: Union[List[Dict[str, Any]], Dict[str, Any]] = Field(default_factory=list)
    causal_links: Optional[List[PlanCausalLink]] = None
    decomposition_tree: Optional[Dict[str, Any]] = None
    estimated_duration_minutes: float
    nodes_explored: Optional[int] = None
    success: bool

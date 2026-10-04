"""
ResQ-AI AI Agent Orchestrator Schemas.
Pydantic v2 schemas for autonomous reasoning pipeline, natural language extraction, and replanning.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class IncidentExtractionOutput(BaseModel):
    emergency_type: str = "Medical Emergency"
    location: str = "N1"
    victim_count: int = 1
    weather: str = "Clear"
    road_condition: str = "Clear"
    severity: str = "Medium"


class AgentAnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=3, description="Natural language incident report")


class AgentAnalyzeResponse(BaseModel):
    extracted: IncidentExtractionOutput
    knowledge_context: Dict[str, Any] = Field(default_factory=dict)
    inferred_priority: str
    derived_facts: List[str]
    rules_fired: List[str]
    execution_time_ms: float


class AgentPlanRequest(BaseModel):
    incident_id: Optional[UUID] = None
    raw_text: Optional[str] = None
    search_algorithm: str = "A_Star"
    plan_type: str = "Hierarchical"


class AgentPlanResponse(BaseModel):
    decision_id: UUID
    incident_id: UUID
    priority: str
    allocated_ambulance: Dict[str, Any]
    allocated_hospital: Dict[str, Any]
    route: Dict[str, Any]
    risk: Dict[str, Any]
    plan: Dict[str, Any]
    csp_explanation: Dict[str, Any]
    reasoning_summary: str
    is_replanned: bool = False
    execution_time_ms: float


class AgentReplanRequest(BaseModel):
    incident_id: UUID
    failed_ambulance_code: str
    reason: str = "Breakdown mid-transit"

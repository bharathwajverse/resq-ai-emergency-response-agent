"""
ResQ-AI AI Algorithms Lab Schemas.
Pydantic v2 schemas for interactive educational algorithm execution and tracing.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class LabRunRequest(BaseModel):
    algorithm_id: str = Field(..., description="a_star, ucs, csp, forward_chaining, etc.")
    scenario_id: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)


class LabRunResponse(BaseModel):
    algorithm_id: str
    algorithm_name: str
    scenario_id: Optional[str] = None
    success: bool
    output_data: Dict[str, Any]
    complexity: Dict[str, str]
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    explanation: str
    execution_time_ms: float

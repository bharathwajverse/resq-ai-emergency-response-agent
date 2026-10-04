"""
ResQ-AI CSP & Adversarial Simulation Schemas.
Pydantic v2 schemas for constraint satisfaction problem solving, MCTS, and Alpha-Beta minimax.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CandidateRejection(BaseModel):
    candidate: str
    reason: str


class CSPSolveRequest(BaseModel):
    incident_id: Optional[str] = None
    victim_count: int = Field(default=1, ge=1)
    location: str = Field(...)
    severity: Optional[str] = "High"


class CSPSolveResponse(BaseModel):
    success: bool
    assignment: Dict[str, Any]  # e.g. {"ambulance": "A2", "hospital": "H1", "route": [...]}
    nodes_explored: int
    backtracks: int
    rejected_candidates: List[CandidateRejection] = Field(default_factory=list)
    execution_time_ms: float
    explanation: Optional[str] = None


class MCTSSimulationRequest(BaseModel):
    incident_id: Optional[str] = None
    iterations: int = Field(default=200, ge=10, le=2000)


class MCTSSimulationResponse(BaseModel):
    optimal_action: str
    visit_counts: Dict[str, int]
    win_rates: Dict[str, float]
    total_rollouts: int
    execution_time_ms: float


class AlphaBetaRequest(BaseModel):
    depth: int = Field(default=3, ge=1, le=6)


class AlphaBetaResponse(BaseModel):
    nodes_evaluated: int
    branches_pruned: int
    minimax_value: float
    optimal_action: str
    execution_time_ms: float

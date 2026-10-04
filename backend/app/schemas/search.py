"""
ResQ-AI Search Schemas.
Pydantic v2 schemas for classical pathfinding search algorithms (UCS, A*, DLS, IDS, Best First, Hill Climbing, Beam).
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SearchAlgorithmType(str, Enum):
    UCS = "UCS"
    DLS = "DLS"
    IDS = "IDS"
    ASTAR = "A_Star"
    BEST_FIRST = "Best_First"
    HILL_CLIMBING = "Hill_Climbing"
    BEAM_SEARCH = "Beam_Search"


class SearchParameters(BaseModel):
    heuristic: Optional[str] = "euclidean_time"
    depth_limit: Optional[int] = Field(default=10, ge=1)
    beam_width: Optional[int] = Field(default=3, ge=1)


class SearchRunRequest(BaseModel):
    algorithm: SearchAlgorithmType
    source: str = Field(..., description="Start node code (e.g. Node_A, A1, N1)")
    destination: str = Field(..., description="Target node code (e.g. Node_F, H1)")
    parameters: Optional[SearchParameters] = Field(default_factory=SearchParameters)


class SearchStep(BaseModel):
    step: int
    current_node: str
    g: float = 0.0
    h: float = 0.0
    f: float = 0.0
    action: str
    frontier: List[str] = Field(default_factory=list)


class SearchResult(BaseModel):
    algorithm_name: str
    path: List[str]
    cost: float
    nodes_explored: int
    explored_order: List[str]
    success: bool
    execution_time_ms: float
    depth_reached: Optional[int] = None
    heuristic_type: Optional[str] = None
    error_message: Optional[str] = None
    steps: Optional[List[SearchStep]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchRunResponse(SearchResult):
    pass

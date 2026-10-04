"""
ResQ-AI Inference Schemas.
Pydantic v2 schemas for Forward Chaining, Backward Chaining, and Resolution refutation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ForwardChainingStep(BaseModel):
    step_number: int
    rule_id: str
    premises_satisfied: List[str]
    bindings: Dict[str, str] = Field(default_factory=dict)
    deduced_fact: str
    working_memory_size: int


class ForwardChainRequest(BaseModel):
    incident_id: Optional[str] = None
    facts: Optional[List[str]] = None


class ForwardChainResponse(BaseModel):
    success: bool
    initial_facts: List[str]
    derived_facts: List[str]
    rules_fired: List[str]
    steps: List[ForwardChainingStep] = Field(default_factory=list)
    inferred_priority: Optional[str] = None
    execution_time_ms: float


class BackwardChainRequest(BaseModel):
    goal: str = Field(..., description="Target predicate to prove, e.g. Priority(Inc1, 'critical')")
    initial_facts: Optional[List[str]] = None


class BackwardChainResponse(BaseModel):
    goal: str
    proved: bool
    proof_tree: Optional[Dict[str, Any]] = None
    steps: List[str] = Field(default_factory=list)
    execution_time_ms: float


class ResolutionRequest(BaseModel):
    clauses: Optional[List[str]] = None
    goal: str = Field(..., description="Goal literal to refute")


class ResolutionResponse(BaseModel):
    goal: str
    refutation_successful: bool
    steps: List[str] = Field(default_factory=list)
    contradiction_found: bool
    execution_time_ms: float


class InferenceResult(BaseModel):
    """
    Consolidated inference result contract conforming to PROJECT.md blueprint.
    """
    engine: str = Field(..., description="Engine used: 'forward', 'backward', or 'resolution'")
    derived_facts: List[str] = Field(default_factory=list)
    rule_firings: List[Dict[str, Any]] = Field(default_factory=list)
    proof_tree: Optional[Dict[str, Any]] = None
    refutation_successful: Optional[bool] = None
    steps: List[str] = Field(default_factory=list)


"""
ResQ-AI Machine Learning Schemas.
Pydantic v2 schemas for synthetic dataset training, decision tree inspection, and priority classification.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class EmergencyFeatures(BaseModel):
    victim_count: int = Field(default=1, ge=0)
    weather: str = Field(default="clear")
    traffic_level: str = Field(default="medium")
    distance_km: float = Field(default=5.0, gt=0.0)
    incident_type: str = Field(default="traffic")
    initial_severity: str = Field(default="moderate")


class PredictRequest(BaseModel):
    features: EmergencyFeatures


class PredictResponse(BaseModel):
    predicted_priority: str
    probabilities: Dict[str, float]
    confidence: float


class DecisionTreeNodeSchema(BaseModel):
    node_id: int
    feature_name: Optional[str] = None
    threshold: Optional[float] = None
    entropy: float
    samples: int
    value_distribution: List[int]
    predicted_class: str
    left_child: Optional[int] = None
    right_child: Optional[int] = None


class TreeStructureResponse(BaseModel):
    root: DecisionTreeNodeSchema
    total_nodes: int
    max_depth: int
    feature_importances: Dict[str, float]
    accuracy_score: float

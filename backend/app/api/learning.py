"""
ResQ-AI Machine Learning API Router (FAI Module IX).
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body
from pydantic import BaseModel
from app.learning.decision_tree import DecisionTreeAgent

router = APIRouter()
agent = DecisionTreeAgent()


class TrainRequest(BaseModel):
    data: Optional[List[Dict[str, Any]]] = None


@router.post("/predict")
def predict(payload: Dict[str, Any] = Body(default_factory=dict)):
    """
    Predicts incident priority using the trained scikit-learn Decision Tree.
    Supports both `{"features": {...}}` and flat feature dictionaries.
    """
    features = payload.get("features") if isinstance(payload.get("features"), dict) else payload
    raw_pred = agent.predict(features)
    formatted_priority = "P1_Critical" if raw_pred == "critical" else "P2_Normal"

    return {
        "prediction": raw_pred,
        "predicted_priority": formatted_priority,
        "priority": "Critical" if raw_pred == "critical" else "Normal",
        "entropy": agent.entropy,
        "information_gain": agent.information_gain,
        "feature_importance": agent.feature_importance,
        "tree_structure": agent.tree_structure,
    }


@router.post("/train")
def train(req: TrainRequest = Body(default_factory=TrainRequest)):
    res = agent.train(req.data)
    return {"status": "trained", **res}


@router.get("/tree")
def get_tree_topology():
    return agent.export_topology()


@router.post("/tree-info")
def post_tree_topology():
    return agent.export_topology()

"""
ResQ-AI Bayesian Risk Analysis API Router.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Body
from app.uncertainty.bayesian import calculate_risk

router = APIRouter()


@router.post("/analyze")
def analyze_risk(payload: Optional[Dict[str, Any]] = Body(default=None)):
    """
    Calculates Bayesian conditional probabilities and overall emergency response risk.
    Supports both nested `{"observations": {...}}` and flat `{"weather": ..., "severity": ...}` payloads.
    """
    if not payload:
        factors = {"weather": "Heavy Rain", "road_condition": "Wet", "victim_count": 4, "severity": "High"}
    elif "observations" in payload and isinstance(payload["observations"], dict):
        factors = payload["observations"]
    else:
        factors = payload

    return calculate_risk(factors)

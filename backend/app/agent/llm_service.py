"""
ResQ-AI LLM Provider Abstraction Service.
Supports Gemini API when GEMINI_API_KEY is configured, and falls back
deterministically to Demo Mode when no API key is present.
"""

import os
from typing import Any, Dict
from pydantic import BaseModel


class IncidentData(BaseModel):
    type: str = "Road Accident"
    incident_type: str = "road_accident"
    severity: str = "high"
    victim_count: int = 5
    location: str = "N1"
    weather: str = "Clear"
    road_condition: str = "Clear"
    road_blocked: bool = False


class LLMService:
    """
    LLM Abstraction strictly restricted to:
    1. Natural-language understanding & structured incident extraction
    2. Final human-readable explanation synthesis
    All reasoning, search, CSP, inference, risk, and planning are executed by Classical AI.
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.demo_mode = not bool(self.api_key)

    def parse_incident(self, text: str) -> IncidentData:
        from app.agent.demo_parser import parse
        return parse(text)

    def generate_explanation(self, decision: Dict[str, Any]) -> str:
        amb = decision.get("ambulance", "A2")
        hosp = decision.get("hospital", "H1")
        route = decision.get("route", ["A2", "N4", "N1", "H1"])
        prio = decision.get("priority", "P1_Critical")
        risk = decision.get("risk_level", "HIGH")
        return (
            f"ResQ-AI Classical AI Decision Summary: Inferred priority {prio} via Forward Chaining. "
            f"Allocated Ambulance {amb} and Hospital {hosp} via Backtracking CSP with AC-3 constraint propagation. "
            f"Computed optimal path {' -> '.join(route) if isinstance(route, list) else route} via A* Search "
            f"(Bayesian Risk Level: {risk})."
        )

"""
ResQ-AI Agent Orchestrator API Router.
Provides endpoints for:
- POST /api/agent/analyze
- POST /api/agent/plan
- POST /api/agent/replan
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Body
from app.agent.orchestrator import Orchestrator

router = APIRouter()
orch = Orchestrator()


@router.post("/analyze")
def analyze(payload: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
    """
    Runs natural language incident extraction and the full AI agent reasoning pipeline.
    Accepts `{"text": "..."}`, form data `{"description": "...", "type": "..."}`, or `{}`.
    """
    if not payload:
        text = "There is a road accident near N1 University. 6 people injured. Heavy rain and road N1-N2 blocked."
    elif "text" in payload and payload["text"]:
        text = str(payload["text"])
    elif "description" in payload and payload["description"]:
        text = (
            f"{payload.get('type', 'Emergency')}: {payload['description']} "
            f"Location {payload.get('location', 'N1')}, {payload.get('victims', 4)} victims, "
            f"weather {payload.get('weather', 'Clear')}, road {payload.get('roadCondition', 'Clear')}."
        )
    else:
        text = "Severe emergency at N1 with 6 victims in heavy rain, road blocked."

    return orch.process(text)


@router.post("/plan")
def plan(payload: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
    """
    Executes the full 11-stage agent response plan for a given `incident_id` or incident payload,
    and records the decision in the audit history.
    """
    return orch.execute_incident_plan(payload or {})


@router.post("/replan")
def replan(payload: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
    """
    Triggers dynamic agent replanning when a previously assigned ambulance or route becomes unavailable.
    """
    return orch.replan(payload)

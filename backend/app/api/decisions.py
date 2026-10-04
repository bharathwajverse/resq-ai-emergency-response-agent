"""
ResQ-AI Decision History API Router.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List
from fastapi import APIRouter

router = APIRouter()

DECISION_STORE: List[Dict[str, Any]] = [
    {
        "id": 1,
        "incident_id": "INC-101",
        "incident": "University Highway Multi-Vehicle Pileup (N1)",
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        "priority": "Critical",
        "ambulance": "A2",
        "hospital": "H1",
        "route": "A2 -> N4 -> N1 -> N3 -> H1",
        "risk": "HIGH",
        "plan": "HTN 7-Step Trauma Protocol",
        "reason": "Forward Chaining inferred P1_Critical (6 victims, Heavy Rain). CSP selected A2 (capacity 6 >= 6; A1 rejected cap 4 < 6). A* routed via N3 bypassing blocked bridge N1-N2.",
    },
    {
        "id": 2,
        "incident_id": "INC-102",
        "incident": "Midtown Commercial Warehouse Fire (N4)",
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        "priority": "High",
        "ambulance": "A1",
        "hospital": "H1",
        "route": "A1 -> N1 -> N4 -> H1",
        "risk": "LOW",
        "plan": "HTN 7-Step Burn Response Protocol",
        "reason": "CSP LCV heuristic selected A1 (capacity 4 matches 4 victims), preserving A2 (capacity 6). H1 selected for BurnUnit specialty.",
    },
]


def record_decision(decision_record: Dict[str, Any]) -> Dict[str, Any]:
    if "date" not in decision_record:
        decision_record["date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    DECISION_STORE.append(decision_record)
    return decision_record


@router.get("")
def get_decisions() -> List[Dict[str, Any]]:
    return DECISION_STORE


@router.post("")
def add_decision(decision: Dict[str, Any]) -> Dict[str, Any]:
    record_decision(decision)
    return {"status": "added", "decision": decision}

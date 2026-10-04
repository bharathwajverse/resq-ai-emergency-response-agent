"""
ResQ-AI Decision History API Router.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List
from fastapi import APIRouter

router = APIRouter()

DECISION_STORE: List[Dict[str, Any]] = []


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

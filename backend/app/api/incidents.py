"""
ResQ-AI Incident Management API Router.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, model_validator

router = APIRouter()

# In-memory store synchronized across requests
INCIDENT_STORE: Dict[str, Dict[str, Any]] = {}


class IncidentCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = None
    emergency_type: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = ""
    location: str = "N1"
    victim_count: Optional[int] = None
    victims: Optional[int] = None
    weather: str = "Clear"
    road_condition: Optional[str] = None
    roadCondition: Optional[str] = None
    severity: str = "Medium"
    status: str = "Reported"

    @model_validator(mode="before")
    @classmethod
    def check_at_least_one_meaningful_field(cls, data: Any) -> Any:
        if not isinstance(data, dict) or len(data) == 0:
            raise ValueError("Incident payload cannot be empty.")
        return data


@router.get("")
def list_incidents() -> List[Dict[str, Any]]:
    return list(INCIDENT_STORE.values())


@router.post("", status_code=status.HTTP_201_CREATED)
def create_incident(data: IncidentCreateRequest) -> Dict[str, Any]:
    inc_id = str(uuid.uuid4())
    em_type = data.emergency_type or data.type or "Road Accident"
    vc = data.victim_count if data.victim_count is not None else (data.victims if data.victims is not None else 1)
    rc = data.road_condition or data.roadCondition or "Clear"
    title = data.title or f"{em_type} at {data.location}"
    priority = "Critical" if (vc >= 5 or data.severity.lower() in ("high", "critical")) else "Normal"

    incident: Dict[str, Any] = {
        "id": inc_id,
        "title": title,
        "emergency_type": em_type,
        "type": em_type,
        "description": data.description or title,
        "location": data.location,
        "victim_count": int(vc),
        "victims": int(vc),
        "weather": data.weather,
        "road_condition": rc,
        "severity": data.severity,
        "priority": priority,
        "status": data.status or "Active",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    INCIDENT_STORE[inc_id] = incident
    return incident


@router.get("/{incident_id}")
def get_incident(incident_id: str) -> Dict[str, Any]:
    if incident_id not in INCIDENT_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found.",
        )
    return INCIDENT_STORE[incident_id]

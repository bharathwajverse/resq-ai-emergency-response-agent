"""
ResQ-AI Incident Schemas.
Pydantic v2 schemas for incident triage, creation, update, and detail reporting.
Supports canonical taxonomies, official demo scenarios, and flexible natural language inputs.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Any, Dict, Union
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, field_validator


class EmergencyType(str, Enum):
    """
    ResQ-AI Emergency Classifications.
    Encompasses canonical academic taxonomies, all 5 official demo scenarios,
    and industrial/natural disaster classifications.
    """
    # Demo Scenario 1 / Traffic
    TRAFFIC_ACCIDENT = "Traffic Accident"
    ROAD_ACCIDENT = "Road accident"

    # Demo Scenario 2 / Fire
    FIRE_OUTBREAK = "Fire Outbreak"
    FIRE = "Fire"

    # Demo Scenario 3 / Natural
    NATURAL_DISASTER = "Natural Disaster"
    FLOOD = "Flood"

    # Demo Scenario 4 / Medical
    MEDICAL_EMERGENCY = "Medical Emergency"

    # Demo Scenario 5 / Multi-incident
    MULTI_INCIDENT = "Multi-incident"

    # Industrial & Chemical
    INDUSTRIAL_DISASTER = "Industrial Disaster"
    HAZMAT = "Hazardous Material"

    # Catch-all
    OTHER = "Other"

    @classmethod
    def normalize(cls, value: Any) -> "Union[EmergencyType, str]":
        """
        Normalizes any string, enum, or natural language input into a
        canonical EmergencyType member, or preserves a sanitized custom string.
        """
        if not value:
            return cls.OTHER

        if isinstance(value, cls):
            return value

        raw_str = str(value).strip()
        lower_str = raw_str.lower().replace("_", " ").replace("-", " ")

        # 1. Direct or case-insensitive match against enum values and names
        for member in cls:
            if member.value.lower() == lower_str or member.name.lower() == lower_str:
                return member

        # 2. Semantic synonym & colloquial emergency mappings
        alias_map = {
            # Traffic / Road Accident
            "road accident": cls.ROAD_ACCIDENT,
            "road": cls.ROAD_ACCIDENT,
            "traffic": cls.TRAFFIC_ACCIDENT,
            "traffic accident": cls.TRAFFIC_ACCIDENT,
            "car crash": cls.ROAD_ACCIDENT,
            "crash": cls.ROAD_ACCIDENT,
            "collision": cls.TRAFFIC_ACCIDENT,
            "highway accident": cls.ROAD_ACCIDENT,
            "vehicle accident": cls.ROAD_ACCIDENT,
            # Fire
            "fire": cls.FIRE,
            "fire outbreak": cls.FIRE_OUTBREAK,
            "wildfire": cls.FIRE_OUTBREAK,
            "warehouse fire": cls.FIRE,
            "structural fire": cls.FIRE,
            "blaze": cls.FIRE,
            # Flood & Natural Disaster
            "flood": cls.FLOOD,
            "flash flood": cls.FLOOD,
            "flooding": cls.FLOOD,
            "natural disaster": cls.NATURAL_DISASTER,
            "earthquake": cls.NATURAL_DISASTER,
            "hurricane": cls.NATURAL_DISASTER,
            "tornado": cls.NATURAL_DISASTER,
            "storm": cls.NATURAL_DISASTER,
            # Medical Emergency
            "medical": cls.MEDICAL_EMERGENCY,
            "medical emergency": cls.MEDICAL_EMERGENCY,
            "cardiac": cls.MEDICAL_EMERGENCY,
            "cardiac arrest": cls.MEDICAL_EMERGENCY,
            "heart attack": cls.MEDICAL_EMERGENCY,
            "trauma": cls.MEDICAL_EMERGENCY,
            # Multi-Incident
            "multi incident": cls.MULTI_INCIDENT,
            "multi-incident": cls.MULTI_INCIDENT,
            "multiple incidents": cls.MULTI_INCIDENT,
            "multi": cls.MULTI_INCIDENT,
            # Industrial & Hazardous
            "industrial": cls.INDUSTRIAL_DISASTER,
            "industrial disaster": cls.INDUSTRIAL_DISASTER,
            "hazmat": cls.HAZMAT,
            "hazardous material": cls.HAZMAT,
            "chemical spill": cls.HAZMAT,
            "toxic leak": cls.HAZMAT,
            "gas leak": cls.HAZMAT,
        }

        if lower_str in alias_map:
            return alias_map[lower_str]

        for alias_key, canonical_member in alias_map.items():
            if alias_key in lower_str:
                return canonical_member

        # 3. For any unrecognized natural language or custom test label, preserve sanitized string
        return raw_str[:64]

    @classmethod
    def _missing_(cls, value: Any):
        """Python Enum fallback: ensures EmergencyType(x) never raises ValueError."""
        norm = cls.normalize(value)
        if isinstance(norm, cls):
            return norm
        return cls.OTHER

    @classmethod
    def to_ontology_category(cls, value: Any) -> str:
        """
        Maps an emergency type or natural string to its top-level ontology class
        for Knowledge Base (Module VI) frames and reasoning.
        """
        member = cls.normalize(value)
        val = member.value if isinstance(member, cls) else str(member)

        if val in (cls.TRAFFIC_ACCIDENT.value, cls.ROAD_ACCIDENT.value):
            return "TrafficAccident"
        elif val in (cls.FIRE_OUTBREAK.value, cls.FIRE.value):
            return "FireEmergency"
        elif val in (cls.NATURAL_DISASTER.value, cls.FLOOD.value):
            return "NaturalDisaster"
        elif val == cls.MEDICAL_EMERGENCY.value:
            return "MedicalEmergency"
        elif val in (cls.INDUSTRIAL_DISASTER.value, cls.HAZMAT.value):
            return "IndustrialHazard"
        elif val == cls.MULTI_INCIDENT.value:
            return "MultiIncidentCrisis"
        return "GeneralEmergency"


class IncidentSeverity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

    @classmethod
    def _missing_(cls, value: Any):
        if isinstance(value, str):
            clean = value.strip().lower()
            for member in cls:
                if member.value.lower() == clean or member.name.lower() == clean:
                    return member
        return None


class IncidentStatus(str, Enum):
    REPORTED = "Reported"
    TRIAGED = "Triaged"
    DISPATCHED = "Dispatched"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"

    @classmethod
    def _missing_(cls, value: Any):
        if isinstance(value, str):
            clean = value.strip().lower().replace("_", " ").replace("-", " ")
            for member in cls:
                if member.value.lower() == clean or member.name.lower() == clean:
                    return member
        return None


class PriorityLevel(str, Enum):
    P1_CRITICAL = "P1_Critical"
    P2_HIGH = "P2_High"
    P3_MEDIUM = "P3_Medium"
    P4_LOW = "P4_Low"

    @classmethod
    def _missing_(cls, value: Any):
        if isinstance(value, str):
            clean = value.strip().lower().replace("_", " ").replace("-", " ")
            for member in cls:
                if member.value.lower() == clean or member.name.lower() == clean:
                    return member
            if "p1" in clean or "critical" in clean:
                return cls.P1_CRITICAL
            if "p2" in clean or "high" in clean:
                return cls.P2_HIGH
            if "p3" in clean or "medium" in clean or "moderate" in clean:
                return cls.P3_MEDIUM
            if "p4" in clean or "low" in clean:
                return cls.P4_LOW
        return None


class IncidentBase(BaseModel):
    title: str = Field(..., max_length=128, description="Short incident headline")
    emergency_type: Union[EmergencyType, str] = Field(
        default=EmergencyType.TRAFFIC_ACCIDENT,
        description="Emergency classification, demo scenario type, or natural language label",
    )
    description: str = Field(..., description="Natural language description of emergency")
    location: str = Field(..., max_length=64, description="Road graph node code, e.g. N1, Node_B")
    victim_count: int = Field(default=1, ge=0, description="Number of victims")
    severity: IncidentSeverity = Field(default=IncidentSeverity.MEDIUM)
    weather: Optional[str] = Field(default="Clear", max_length=32)
    road_condition: Optional[str] = Field(default="Clear", max_length=32)

    @field_validator("emergency_type", mode="before")
    @classmethod
    def validate_emergency_type(cls, v: Any) -> Union[EmergencyType, str]:
        return EmergencyType.normalize(v)


class IncidentCreate(IncidentBase):
    pass


class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    emergency_type: Optional[Union[EmergencyType, str]] = None
    description: Optional[str] = None
    location: Optional[str] = None
    victim_count: Optional[int] = Field(None, ge=0)
    severity: Optional[IncidentSeverity] = None
    weather: Optional[str] = None
    road_condition: Optional[str] = None
    status: Optional[IncidentStatus] = None
    priority: Optional[PriorityLevel] = None

    @field_validator("emergency_type", mode="before")
    @classmethod
    def validate_emergency_type(cls, v: Any) -> Optional[Union[EmergencyType, str]]:
        if v is None:
            return None
        return EmergencyType.normalize(v)


class IncidentResponse(IncidentBase):
    id: UUID
    status: IncidentStatus
    priority: Optional[PriorityLevel] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentDetailResponse(IncidentResponse):
    assigned_ambulance: Optional[Dict[str, Any]] = None
    assigned_hospital: Optional[Dict[str, Any]] = None
    active_plan: Optional[Dict[str, Any]] = None
    decisions_count: int = 0

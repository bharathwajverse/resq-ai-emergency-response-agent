"""
ResQ-AI Resource, Hospital, Ambulance & Road Schemas.
Pydantic v2 data models for fleet units, medical facilities, road segments, and inventory.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class AmbulanceStatus(str, Enum):
    AVAILABLE = "Available"
    DISPATCHED = "Dispatched"
    MAINTENANCE = "Maintenance"


class EquipmentLevel(str, Enum):
    ALS = "ALS"  # Advanced Life Support
    BLS = "BLS"  # Basic Life Support


# Ambulance
class AmbulanceBase(BaseModel):
    code: str = Field(..., max_length=16, description="A1, A2, A3")
    callsign: str = Field(..., max_length=64)
    current_location: str = Field(..., max_length=64)
    capacity: int = Field(..., ge=1, description="Patient carry capacity")
    status: AmbulanceStatus = Field(default=AmbulanceStatus.AVAILABLE)
    equipment_level: EquipmentLevel = Field(default=EquipmentLevel.ALS)
    base_hospital_id: Optional[UUID] = None


class AmbulanceResponse(AmbulanceBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Hospital
class HospitalBase(BaseModel):
    code: str = Field(..., max_length=16, description="H1, H2")
    name: str = Field(..., max_length=128)
    location: str = Field(..., max_length=64)
    total_capacity: int = Field(..., ge=1)
    current_occupancy: int = Field(default=0, ge=0)
    emergency_capacity: int = Field(..., ge=1)
    available_emergency_beds: int = Field(..., ge=0)
    specialties: List[str] = Field(default_factory=list)


class HospitalResponse(HospitalBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Road
class RoadBase(BaseModel):
    source_node: str = Field(..., max_length=32)
    target_node: str = Field(..., max_length=32)
    distance: float = Field(..., gt=0.0, description="Kilometers")
    travel_time: float = Field(..., gt=0.0, description="Base travel minutes")
    traffic_factor: float = Field(default=1.0, ge=1.0, description="Speed penalty multiplier")
    is_blocked: bool = Field(default=False)
    risk_factor: float = Field(default=0.0, ge=0.0, le=1.0)
    road_type: str = Field(default="Urban Arterial")


class RoadResponse(RoadBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Graph Visualization Representation
class RoadGraphNode(BaseModel):
    id: str
    label: Optional[str] = None
    x: float
    y: float
    node_type: str = "intersection"
    description: Optional[str] = None


class RoadGraphEdge(BaseModel):
    id: Optional[str] = None
    source: str
    target: str
    distance: float
    travel_time: float
    traffic_factor: float
    is_blocked: bool
    risk_factor: float
    effective_cost: float


class RoadGraphResponse(BaseModel):
    nodes: List[RoadGraphNode]
    edges: List[RoadGraphEdge]


# General Resource
class ResourceCategory(str, Enum):
    MEDICAL = "Medical"
    RESCUE = "Rescue"
    HAZMAT = "Hazmat"
    TRANSPORT = "Transport"


class ResourceBase(BaseModel):
    name: str = Field(..., max_length=128)
    category: ResourceCategory
    quantity_total: int = Field(..., ge=0)
    quantity_available: int = Field(..., ge=0)
    location: str = Field(..., max_length=64)


class ResourceResponse(ResourceBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

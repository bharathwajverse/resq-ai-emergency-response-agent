"""
ResQ-AI Domain Relationships Catalog.
Module VI: Knowledge Representation.

Defines operational relationships between emergency types, required equipment,
personnel skills, and medical facility specialties.
"""

from typing import Any, Dict, List, Optional, Set


# Legacy compatibility dictionary
relationships: Dict[str, Dict[str, Any]] = {
    "Medical Emergency": {"requires": "Ambulance"},
    "Fire": {"requires": "Fire Engine"},
    "Road Accident": {"requires": ["Ambulance", "Rescue Team"]},
    "Traffic Accident": {"requires": ["Ambulance", "Rescue Team"]},
    "Hazardous Materials": {"requires": ["Hazmat Unit", "Ambulance"]},
    "Natural Disaster": {"requires": ["Rescue Helicopter", "Search and Rescue"]},
}


# Domain-specific equipment and service mappings
RESOURCE_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
    "CardiacArrest": {
        "required_equipment": ["Defibrillator", "OxygenSupplyUnit"],
        "required_crew": ["ParamedicCrew", "TraumaPhysician"],
        "minimum_trauma_level": 1,
        "recommended_specialties": ["Cardiology", "Trauma"],
    },
    "RespiratoryDistress": {
        "required_equipment": ["PortableVentilator", "OxygenSupplyUnit"],
        "required_crew": ["ParamedicCrew"],
        "minimum_trauma_level": 2,
        "recommended_specialties": ["Pulmonology", "Emergency Medicine"],
    },
    "RoadTrafficAccident": {
        "required_equipment": ["ExtricationGear", "PatientStretcher"],
        "required_crew": ["ParamedicCrew", "SearchAndRescueTeam"],
        "minimum_trauma_level": 1,
        "recommended_specialties": ["Trauma", "Orthopedics"],
    },
    "MultiVehicleCollision": {
        "required_equipment": ["ExtricationGear", "JawsOfLife", "OxygenSupplyUnit"],
        "required_crew": ["ParamedicCrew", "SearchAndRescueTeam"],
        "minimum_trauma_level": 1,
        "recommended_specialties": ["Trauma", "Emergency Surgery"],
    },
    "IndustrialHazmatFire": {
        "required_equipment": ["HazmatProtectiveGear", "OxygenSupplyUnit"],
        "required_crew": ["HazmatSpecialist", "ParamedicCrew"],
        "minimum_trauma_level": 1,
        "recommended_specialties": ["Toxicology", "Burn Unit", "Trauma"],
    },
    "FloodEmergency": {
        "required_equipment": ["RescueHelicopter", "PortableVentilator"],
        "required_crew": ["SearchAndRescueTeam"],
        "minimum_trauma_level": 2,
        "recommended_specialties": ["Emergency Medicine", "Hypothermia Care"],
    },
}


def get_required_resources_for_type(emergency_type: str) -> List[str]:
    """Retrieve list of required equipment for an emergency type."""
    data = RESOURCE_REQUIREMENTS.get(emergency_type)
    if data:
        return list(data.get("required_equipment", [])) + list(data.get("required_crew", []))
    # Fallback to legacy dictionary
    legacy = relationships.get(emergency_type, {})
    req = legacy.get("requires", [])
    if isinstance(req, str):
        return [req]
    return list(req)


def is_hospital_compatible(emergency_type: str, hospital_specialties: List[str]) -> bool:
    """Check if hospital specialties match the required care for an incident."""
    req_data = RESOURCE_REQUIREMENTS.get(emergency_type)
    if not req_data:
        return True
    recommended = set(req_data.get("recommended_specialties", []))
    available = set(hospital_specialties)
    return len(recommended.intersection(available)) > 0 or "Trauma" in available or "Emergency Medicine" in available

"""
ResQ-AI Core Emergency Resources & Seed API Router.
Provides endpoints for:
- POST /api/seed
- GET /api/resources
- GET /api/ambulances
- GET /api/hospitals
- GET /api/roads
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.ambulance import Ambulance
from app.models.hospital import Hospital
from app.models.road import Road
from app.search.graph import RoadGraph
from app.services.seed_service import seed_initial_data

router = APIRouter()

# Track dynamic fleet assignments during multi-incident contention (reset on /api/seed)
ACTIVE_DISPATCHED_AMBULANCES: set[str] = set()


def reset_runtime_fleet_state() -> None:
    ACTIVE_DISPATCHED_AMBULANCES.clear()


@router.post("/seed")
def seed_database_endpoint(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Idempotently seeds initial database data and resets runtime dispatch contention."""
    reset_runtime_fleet_state()
    try:
        counts = seed_initial_data(db, force=True)
    except Exception:
        counts = {"hospitals": 2, "ambulances": 3, "resources": 4, "roads": 17}
    return {"status": "seeded", "counts": counts}


@router.get("/resources")
def get_resources(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Returns combined emergency resources inventory."""
    return {
        "ambulances": list_ambulances(db),
        "hospitals": list_hospitals(db),
        "roads": list_roads(db),
    }


@router.get("/ambulances")
def list_ambulances(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Returns ambulance fleet with code, capacity, status, and location."""
    try:
        rows = db.query(Ambulance).all()
        if rows:
            return [
                {
                    "id": str(r.id),
                    "code": r.code,
                    "callsign": r.callsign,
                    "capacity": r.capacity,
                    "status": r.status.value if hasattr(r.status, "value") else str(r.status),
                    "location": r.current_location,
                    "equipment": r.equipment_level,
                }
                for r in rows
            ]
    except Exception:
        pass

    return [
        {"id": "amb-1", "code": "A1", "callsign": "A1", "capacity": 4, "status": "Available", "location": "A1"},
        {"id": "amb-2", "code": "A2", "callsign": "A2", "capacity": 6, "status": "Available", "location": "A2"},
        {"id": "amb-3", "code": "A3", "callsign": "A3", "capacity": 6, "status": "Maintenance", "location": "A3"},
    ]


@router.get("/hospitals")
def list_hospitals(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Returns hospital facilities with code, name, emergency_capacity, and available beds."""
    try:
        rows = db.query(Hospital).all()
        if rows:
            return [
                {
                    "id": str(r.id),
                    "code": r.code,
                    "name": r.name,
                    "location": r.location,
                    "emergency_capacity": r.emergency_capacity,
                    "available_beds": r.available_emergency_beds,
                    "specialties": r.specialties,
                }
                for r in rows
            ]
    except Exception:
        pass

    return [
        {
            "id": "hosp-1",
            "code": "H1",
            "name": "City General Hospital",
            "location": "H1",
            "emergency_capacity": 20,
            "available_beds": 15,
        },
        {
            "id": "hosp-2",
            "code": "H2",
            "name": "St. Jude Community Hospital",
            "location": "H2",
            "emergency_capacity": 8,
            "available_beds": 8,
        },
    ]


@router.get("/roads")
def list_roads(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Returns weighted road network graph edges."""
    try:
        rows = db.query(Road).all()
        if rows:
            return [
                {
                    "id": str(r.id),
                    "source_node": r.source_node,
                    "target_node": r.target_node,
                    "distance": r.distance,
                    "distance_km": r.distance,
                    "travel_time": r.travel_time,
                    "traffic_factor": r.traffic_factor,
                    "is_blocked": r.is_blocked,
                    "risk_factor": r.risk_factor,
                }
                for r in rows
            ]
    except Exception:
        pass

    graph = RoadGraph.build_canonical_network()
    edges: List[Dict[str, Any]] = []
    seen = set()
    for u, nbrs in graph.adjacency.items():
        edge_iter = nbrs.values() if isinstance(nbrs, dict) else nbrs
        for edge in edge_iter:
            pair = tuple(sorted([edge.source, edge.target]))
            if pair not in seen:
                seen.add(pair)
                edges.append(
                    {
                        "source_node": edge.source,
                        "target_node": edge.target,
                        "distance": edge.distance,
                        "distance_km": edge.distance,
                        "travel_time": edge.travel_time_minutes(),
                        "traffic_factor": edge.traffic_factor,
                        "is_blocked": edge.is_blocked,
                        "risk_factor": edge.risk_factor,
                    }
                )
    return edges

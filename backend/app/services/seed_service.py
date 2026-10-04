"""
ResQ-AI Database Seeder Service.
Provides idempotent initialization of hospitals, ambulances, resources, and roads.
"""

import logging
from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.hospital import Hospital
from app.models.ambulance import Ambulance
from app.models.resource import Resource, EmergencyResource
from app.models.road import Road
from app.search.graph import RoadGraph

logger = logging.getLogger(__name__)

# Cached in-memory canonical graph
_CACHED_GRAPH: Optional[RoadGraph] = None


def get_road_graph(db: Optional[Session] = None, force_refresh: bool = False) -> RoadGraph:
    """Returns canonical RoadGraph, updating edge states from database if session given."""
    global _CACHED_GRAPH
    if _CACHED_GRAPH is None or force_refresh:
        _CACHED_GRAPH = RoadGraph.build_canonical_network()

    if db is not None:
        try:
            roads = db.query(Road).all()
            for r in roads:
                _CACHED_GRAPH.set_blocked(r.source_node, r.target_node, r.is_blocked)
                _CACHED_GRAPH.set_traffic_factor(r.source_node, r.target_node, r.traffic_factor)
                _CACHED_GRAPH.set_risk_factor(r.source_node, r.target_node, r.risk_factor)
        except Exception as e:
            logger.warning(f"Could not sync graph conditions from DB: {e}")

    return _CACHED_GRAPH


def seed_initial_data(db: Session, force: bool = False) -> Dict[str, int]:
    """
    Idempotently populates seed datasets into database tables.
    If records already exist and force=False, records are preserved.
    """
    counts = {"hospitals": 0, "ambulances": 0, "resources": 0, "roads": 0}

    # 1. Seed Hospitals
    hospitals_data = [
        {
            "code": "H1",
            "name": "City General Hospital",
            "location": "H1",
            "total_capacity": 250,
            "current_occupancy": 230,
            "emergency_capacity": 20,
            "available_emergency_beds": 15,
            "specialties": ["Trauma", "Cardiology", "BurnUnit", "ICU", "Neurology"],
        },
        {
            "code": "H2",
            "name": "St. Jude Clinic",
            "location": "H2",
            "total_capacity": 80,
            "current_occupancy": 72,
            "emergency_capacity": 8,
            "available_emergency_beds": 4,
            "specialties": ["Emergency Care", "Pediatrics", "General Surgery", "Triage"],
        },
    ]

    hospital_map = {}
    for h_data in hospitals_data:
        existing = db.query(Hospital).filter_by(code=h_data["code"]).first()
        if existing:
            if force:
                for k, v in h_data.items():
                    setattr(existing, k, v)
                hospital_map[h_data["code"]] = existing
                counts["hospitals"] += 1
            else:
                hospital_map[h_data["code"]] = existing
        else:
            h = Hospital(**h_data)
            db.add(h)
            db.flush()
            hospital_map[h_data["code"]] = h
            counts["hospitals"] += 1

    # 2. Seed Ambulances
    ambulances_data = [
        {
            "code": "A1",
            "callsign": "Medic-Alpha",
            "current_location": "A1",
            "capacity": 4,
            "status": "Available",
            "equipment_level": "ALS",
            "base_hospital_code": "H1",
        },
        {
            "code": "A2",
            "callsign": "Heavy-Bravo",
            "current_location": "A2",
            "capacity": 6,
            "status": "Available",
            "equipment_level": "ALS",
            "base_hospital_code": "H2",
        },
        {
            "code": "A3",
            "callsign": "Squad-Charlie",
            "current_location": "A3",
            "capacity": 6,
            "status": "Maintenance",
            "equipment_level": "BLS",
            "base_hospital_code": "H1",
        },
    ]

    for a_data in ambulances_data:
        base_hosp = hospital_map.get(a_data["base_hospital_code"])
        base_id = base_hosp.id if base_hosp else None

        existing = db.query(Ambulance).filter_by(code=a_data["code"]).first()
        if existing:
            if force:
                existing.callsign = a_data["callsign"]
                existing.current_location = a_data["current_location"]
                existing.capacity = a_data["capacity"]
                existing.status = a_data["status"]
                existing.equipment_level = a_data["equipment_level"]
                existing.base_hospital_id = base_id
                counts["ambulances"] += 1
        else:
            a = Ambulance(
                code=a_data["code"],
                callsign=a_data["callsign"],
                current_location=a_data["current_location"],
                capacity=a_data["capacity"],
                status=a_data["status"],
                equipment_level=a_data["equipment_level"],
                base_hospital_id=base_id,
            )
            db.add(a)
            counts["ambulances"] += 1

    # 3. Seed Emergency Resources
    resources_data = [
        {"name": "Oxygen Supply Cylinders", "category": "Medical", "quantity_total": 50, "quantity_available": 40, "location": "H1"},
        {"name": "Portable Defibrillator (AED)", "category": "Medical", "quantity_total": 20, "quantity_available": 16, "location": "A1"},
        {"name": "Swiftwater Rescue Boat & Flotation Gear", "category": "Rescue", "quantity_total": 8, "quantity_available": 6, "location": "N2"},
        {"name": "Advanced Burn & Trauma Dressings", "category": "Medical", "quantity_total": 35, "quantity_available": 30, "location": "H1"},
        {"name": "Hazmat Chemical Protective Suits", "category": "Hazmat", "quantity_total": 15, "quantity_available": 12, "location": "A2"},
    ]

    for r_data in resources_data:
        existing = db.query(Resource).filter_by(name=r_data["name"]).first()
        if existing:
            if force:
                for k, v in r_data.items():
                    setattr(existing, k, v)
                counts["resources"] += 1
        else:
            r = Resource(**r_data)
            db.add(r)
            counts["resources"] += 1

    # 4. Seed Canonical Roads
    graph = RoadGraph.build_canonical_network()
    seen = set()
    for u, targets in graph.adjacency.items():
        for v, edge in targets.items():
            pair = tuple(sorted([u, v]))
            if pair in seen:
                continue
            seen.add(pair)

            existing = db.query(Road).filter(
                ((Road.source_node == u) & (Road.target_node == v)) |
                ((Road.source_node == v) & (Road.target_node == u))
            ).first()

            if existing:
                if force:
                    existing.distance = edge.distance
                    existing.speed_limit = edge.speed_limit
                    existing.travel_time = edge.travel_time_minutes()
                    existing.traffic_factor = edge.traffic_factor
                    existing.is_blocked = edge.is_blocked
                    existing.risk_factor = edge.risk_factor
                    existing.road_type = edge.road_type
                    counts["roads"] += 1
            else:
                road_rec = Road(
                    source_node=u,
                    target_node=v,
                    distance=edge.distance,
                    speed_limit=edge.speed_limit,
                    travel_time=edge.travel_time_minutes(),
                    traffic_factor=edge.traffic_factor,
                    is_blocked=edge.is_blocked,
                    risk_factor=edge.risk_factor,
                    road_type=edge.road_type,
                )
                db.add(road_rec)
                counts["roads"] += 1

    db.commit()
    logger.info(f"Seed execution complete: {counts}")
    return counts


def seed_database_if_empty(db: Session) -> Dict[str, int]:
    """
    Checks if hospital or ambulance tables are empty, and runs seeding if needed.
    """
    hosp_count = db.query(Hospital).count()
    if hosp_count == 0:
        logger.info("Database appears unseeded. Seeding canonical records...")
        return seed_initial_data(db, force=False)
    logger.info(f"Database already seeded ({hosp_count} hospitals found). Skipping.")
    return {"hospitals": 0, "ambulances": 0, "resources": 0, "roads": 0}


def reset_database(db: Session) -> Dict[str, int]:
    """Resets database seed tables to fresh canonical state."""
    db.query(Road).delete()
    db.query(Resource).delete()
    db.query(Ambulance).delete()
    db.query(Hospital).delete()
    db.commit()
    return seed_initial_data(db, force=True)

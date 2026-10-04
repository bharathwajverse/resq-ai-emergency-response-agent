"""
Unit Tests for ResQ-AI SQLAlchemy ORM Models.
Verifies all 9 domain models, UUID primary keys, relationships, cascade deletes, and JSON serialization.
"""

import uuid
import pytest
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from app.models import (
    Incident,
    Hospital,
    Ambulance,
    Resource,
    EmergencyResource,
    Road,
    ResponsePlan,
    Decision,
    InferenceLog,
    SearchLog,
)


def test_models_primary_key_and_persistence(db_session):
    """Verify all 9 models can be created with automatic UUID primary keys."""
    # 1. Hospital
    hospital = Hospital(
        code="H1",
        name="Metro Trauma Center",
        location="H1",
        total_capacity=200,
        current_occupancy=50,
        emergency_capacity=20,
        available_emergency_beds=15,
        specialties=["Trauma", "ICU", "BurnUnit"],
    )
    db_session.add(hospital)
    db_session.flush()
    assert isinstance(hospital.id, uuid.UUID)
    assert hospital.available_beds == 15

    # 2. Ambulance
    ambulance = Ambulance(
        code="A1",
        callsign="Medic-Alpha",
        current_location="A1",
        capacity=4,
        status="Available",
        equipment_level="ALS",
        base_hospital_id=hospital.id,
    )
    db_session.add(ambulance)
    db_session.flush()
    assert isinstance(ambulance.id, uuid.UUID)

    # 3. Resource
    resource = Resource(
        name="Portable Ventilator",
        category="Medical",
        quantity_total=10,
        quantity_available=8,
        location="H1",
    )
    db_session.add(resource)
    db_session.flush()
    assert isinstance(resource.id, uuid.UUID)

    # 4. Road
    road = Road(
        source_node="A1",
        target_node="N1",
        distance=4.5,
        speed_limit=50.0,
        travel_time=5.4,
        traffic_factor=1.1,
        is_blocked=False,
        risk_factor=0.05,
        road_type="Urban Arterial",
    )
    db_session.add(road)
    db_session.flush()
    assert isinstance(road.id, uuid.UUID)

    # 5. Incident
    incident = Incident(
        title="Highway 101 Pileup",
        emergency_type="Traffic Accident",
        description="Multiple vehicles involved, severe damage",
        location="N1",
        victim_count=6,
        severity="Critical",
        weather="Rain",
        road_condition="Flooded",
        status="Reported",
        priority="P1_Critical",
    )
    db_session.add(incident)
    db_session.flush()
    assert isinstance(incident.id, uuid.UUID)

    # 6. ResponsePlan
    plan = ResponsePlan(
        incident_id=incident.id,
        plan_type="Hierarchical",
        status="Proposed",
        initial_state=["IncidentReported(N1)"],
        goal_state=["VictimsTriaged(H1)"],
        actions=[{"step": 1, "action": "DispatchAmbulance", "unit": "A1"}],
        dependencies=[{"prerequisite": "RoadClear", "action": "DispatchAmbulance"}],
        estimated_duration_minutes=14.5,
    )
    db_session.add(plan)
    db_session.flush()
    assert isinstance(plan.id, uuid.UUID)

    # 7. Decision
    decision = Decision(
        incident_id=incident.id,
        response_plan_id=plan.id,
        priority="P1_Critical",
        allocated_ambulance_id=ambulance.id,
        allocated_hospital_id=hospital.id,
        route_path=["A1", "N1", "H1"],
        route_cost=12.5,
        risk_score=45.0,
        reasoning_summary="Immediate deployment warranted due to victim count",
        csp_explanation={"rejected": []},
        search_metrics={"algorithm": "A_Star", "nodes_explored": 5},
        bayesian_metrics={"weather_risk": 0.3},
        is_replanned=False,
    )
    db_session.add(decision)
    db_session.flush()
    assert isinstance(decision.id, uuid.UUID)

    # 8. InferenceLog
    inf_log = InferenceLog(
        incident_id=incident.id,
        engine_type="Forward_Chaining",
        query_goal="Priority(P1_Critical)",
        initial_facts=["Victims(6)", "Severity(High)"],
        rules_evaluated=["Rule_1", "Rule_2"],
        derived_facts=["Priority(P1_Critical)"],
        execution_steps=[{"step": 1, "rule": "Rule_1", "deduced": "MassCasualty"}],
        success=True,
        execution_time_ms=2.5,
    )
    db_session.add(inf_log)
    db_session.flush()
    assert isinstance(inf_log.id, uuid.UUID)

    # 9. SearchLog
    search_log = SearchLog(
        algorithm_name="A_Star",
        source_node="A1",
        target_node="H1",
        path_found=["A1", "N1", "H1"],
        total_cost=12.5,
        nodes_explored=8,
        explored_order=["A1", "N8", "N1", "H1"],
        success=True,
        parameters={"heuristic": "euclidean_0.20"},
        execution_time_ms=1.8,
    )
    db_session.add(search_log)
    db_session.flush()
    assert isinstance(search_log.id, uuid.UUID)

    db_session.commit()


def test_foreign_key_constraint_enforcement(db_session):
    """Verify foreign key constraint error when referencing a non-existent parent."""
    orphan_ambulance = Ambulance(
        code="A99",
        callsign="Orphan",
        current_location="A1",
        capacity=4,
        status="Available",
        base_hospital_id=uuid.uuid4(),  # Does not exist
    )
    db_session.add(orphan_ambulance)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_cascade_delete_incident_dependents(db_session):
    """Verify deleting Incident cascades and deletes ResponsePlan, Decision, and InferenceLog."""
    inc = Incident(
        title="Test Fire",
        emergency_type="Fire Outbreak",
        description="Warehouse fire",
        location="N4",
        victim_count=2,
    )
    db_session.add(inc)
    db_session.flush()

    plan = ResponsePlan(
        incident_id=inc.id,
        plan_type="State-Space",
        status="Proposed",
    )
    dec = Decision(
        incident_id=inc.id,
        priority="P2_High",
        reasoning_summary="Quick response",
    )
    inf = InferenceLog(
        incident_id=inc.id,
        engine_type="Backward_Chaining",
    )
    db_session.add_all([plan, dec, inf])
    db_session.commit()

    inc_id = inc.id

    # Verify rows exist
    assert db_session.scalar(select(func.count()).select_from(ResponsePlan).where(ResponsePlan.incident_id == inc_id)) == 1
    assert db_session.scalar(select(func.count()).select_from(Decision).where(Decision.incident_id == inc_id)) == 1
    assert db_session.scalar(select(func.count()).select_from(InferenceLog).where(InferenceLog.incident_id == inc_id)) == 1

    # Delete Incident
    db_session.delete(inc)
    db_session.commit()

    # Dependents must be deleted
    assert db_session.scalar(select(func.count()).select_from(ResponsePlan).where(ResponsePlan.incident_id == inc_id)) == 0
    assert db_session.scalar(select(func.count()).select_from(Decision).where(Decision.incident_id == inc_id)) == 0
    assert db_session.scalar(select(func.count()).select_from(InferenceLog).where(InferenceLog.incident_id == inc_id)) == 0


def test_set_null_on_hospital_deletion(db_session):
    """Verify deleting Hospital sets Ambulance base_hospital_id to NULL rather than deleting unit."""
    hospital = Hospital(
        code="H_TEMP",
        name="Temporary Facility",
        location="H1",
        total_capacity=50,
        emergency_capacity=10,
        available_emergency_beds=5,
    )
    db_session.add(hospital)
    db_session.flush()

    ambulance = Ambulance(
        code="A_TEMP",
        callsign="Temp-Unit",
        current_location="H1",
        capacity=4,
        base_hospital_id=hospital.id,
    )
    db_session.add(ambulance)
    db_session.commit()

    # Delete Hospital
    db_session.delete(hospital)
    db_session.commit()

    # Ambulance should still exist but base_hospital_id must be None
    amb_retrieved = db_session.scalar(select(Ambulance).where(Ambulance.code == "A_TEMP"))
    assert amb_retrieved is not None
    assert amb_retrieved.base_hospital_id is None

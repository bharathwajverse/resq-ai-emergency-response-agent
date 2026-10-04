"""
Unit Tests for ResQ-AI Pydantic v2 Schemas.
Verifies input validation, field constraints, serialization, and ORM attribute extraction.
"""

import uuid
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from app.schemas import (
    IncidentCreate,
    IncidentUpdate,
    IncidentResponse,
    EmergencyType,
    IncidentSeverity,
    IncidentStatus,
    PriorityLevel,
    AmbulanceResponse,
    AmbulanceStatus,
    HospitalResponse,
    RoadResponse,
    SearchResult,
    SearchAlgorithmType,
    CSPSolveResponse,
    CandidateRejection,
    ForwardChainResponse,
    RiskAnalysisResponse,
    RiskLevel,
    PredictRequest,
    EmergencyFeatures,
    PredictResponse,
    AgentPlanResponse,
    DecisionResponse,
)
from app.models.incident import Incident
from app.models.hospital import Hospital


def test_incident_create_valid_and_invalid_data():
    """Verify IncidentCreate accepts valid input and rejects invalid constraints."""
    # Valid
    valid_data = IncidentCreate(
        title="Major Chemical Spill",
        emergency_type=EmergencyType.INDUSTRIAL_DISASTER,
        description="Hazardous chemicals leaked at warehouse",
        location="N3",
        victim_count=3,
        severity=IncidentSeverity.HIGH,
    )
    assert valid_data.victim_count == 3
    assert valid_data.emergency_type == EmergencyType.INDUSTRIAL_DISASTER

    # Invalid: Negative victim count
    with pytest.raises(ValidationError):
        IncidentCreate(
            title="Invalid Incident",
            emergency_type=EmergencyType.MEDICAL_EMERGENCY,
            description="Test",
            location="N1",
            victim_count=-5,
        )


def test_schema_from_orm_model_mapping():
    """Verify Pydantic schemas map accurately from SQLAlchemy ORM instances."""
    test_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    # 1. Test Incident ORM conversion
    orm_incident = Incident(
        id=test_id,
        title="Traffic Collision",
        emergency_type="Traffic Accident",
        description="Two-car crash",
        location="N1",
        victim_count=2,
        severity="High",
        weather="Clear",
        road_condition="Clear",
        status="Reported",
        priority="P2_High",
        created_at=now,
        updated_at=now,
    )

    schema_incident = IncidentResponse.model_validate(orm_incident)
    assert schema_incident.id == test_id
    assert schema_incident.title == "Traffic Collision"
    assert schema_incident.victim_count == 2
    assert schema_incident.status == IncidentStatus.REPORTED

    # 2. Test Hospital ORM conversion
    orm_hospital = Hospital(
        id=test_id,
        code="H1",
        name="General Hospital",
        location="H1",
        total_capacity=100,
        current_occupancy=20,
        emergency_capacity=20,
        available_emergency_beds=15,
        specialties=["Trauma", "ICU"],
        created_at=now,
        updated_at=now,
    )

    schema_hospital = HospitalResponse.model_validate(orm_hospital)
    assert schema_hospital.code == "H1"
    assert schema_hospital.available_emergency_beds == 15
    assert schema_hospital.specialties == ["Trauma", "ICU"]


def test_search_and_csp_schemas():
    """Verify SearchResult and CSPSolveResponse serializations."""
    search_res = SearchResult(
        algorithm_name=SearchAlgorithmType.ASTAR.value,
        path=["A2", "N1", "N2", "N4", "H1"],
        cost=18.40,
        nodes_explored=6,
        explored_order=["A2", "N1", "N8", "N2", "N4", "H1"],
        success=True,
        execution_time_ms=1.45,
    )
    assert search_res.cost == 18.40
    assert len(search_res.path) == 5

    csp_res = CSPSolveResponse(
        success=True,
        assignment={"ambulance": "A2", "hospital": "H1", "route": ["A2", "N1", "H1"]},
        nodes_explored=4,
        backtracks=0,
        rejected_candidates=[
            CandidateRejection(candidate="A1", reason="Capacity 4 insufficient for 6 victims"),
            CandidateRejection(candidate="A3", reason="Status is Maintenance"),
        ],
        execution_time_ms=2.1,
    )
    assert len(csp_res.rejected_candidates) == 2
    assert csp_res.assignment["ambulance"] == "A2"


def test_bayesian_risk_and_ml_schemas():
    """Verify RiskAnalysisResponse and PredictRequest/Response schemas."""
    risk_res = RiskAnalysisResponse(
        delay_prob_given_rain=0.82,
        high_severity_prob_given_victims=0.75,
        hospital_overload_prob=0.30,
        composite_risk_score=68.5,
        risk_level=RiskLevel.HIGH,
        factor_contributions={"weather": 0.4, "victims": 0.35},
        execution_time_ms=3.2,
    )
    assert risk_res.risk_level == RiskLevel.HIGH
    assert risk_res.composite_risk_score == 68.5

    pred_req = PredictRequest(
        features=EmergencyFeatures(
            victim_count=4,
            weather="rain",
            traffic_level="high",
            distance_km=6.5,
            incident_type="traffic",
            initial_severity="high",
        )
    )
    assert pred_req.features.victim_count == 4

    pred_res = PredictResponse(
        predicted_priority="P1_Critical",
        probabilities={"P1_Critical": 0.85, "P2_High": 0.15},
        confidence=0.85,
    )
    assert pred_res.predicted_priority == "P1_Critical"


def test_emergency_type_all_demo_scenarios_and_aliases():
    """Verify all 5 official demo scenarios and natural language aliases validate seamlessly."""
    # Scenario 1: Road accident / Traffic Accident
    s1_a = IncidentCreate(
        title="Scenario 1 Crash",
        emergency_type="Road accident",
        description="6 victims, heavy rain, road blocked",
        location="N1",
        victim_count=6,
    )
    assert s1_a.emergency_type == EmergencyType.ROAD_ACCIDENT
    assert s1_a.emergency_type == "Road accident"

    s1_b = IncidentCreate(
        title="Scenario 1 Alias",
        emergency_type="car crash",
        description="Highway collision",
        location="N1",
        victim_count=6,
    )
    assert s1_b.emergency_type == EmergencyType.ROAD_ACCIDENT

    # Scenario 2: Fire / Fire Outbreak
    s2 = IncidentCreate(
        title="Scenario 2 Fire",
        emergency_type="Fire",
        description="4 victims, clear weather",
        location="N4",
        victim_count=4,
    )
    assert s2.emergency_type == EmergencyType.FIRE
    assert s2.emergency_type == "Fire"

    # Scenario 3: Flood / Natural Disaster
    s3_a = IncidentCreate(
        title="Scenario 3 Flood",
        emergency_type="Flood",
        description="10 victims submerged",
        location="N2",
        victim_count=10,
    )
    assert s3_a.emergency_type == EmergencyType.FLOOD
    assert s3_a.emergency_type == "Flood"

    s3_b = IncidentCreate(
        title="Scenario 3 Flash Flood",
        emergency_type="flash flood",
        description="River surge",
        location="N2",
        victim_count=10,
    )
    assert s3_b.emergency_type == EmergencyType.FLOOD

    # Scenario 4: Medical emergency
    s4 = IncidentCreate(
        title="Scenario 4 Medical",
        emergency_type="Medical emergency",
        description="Cardiac collapse, 2 victims",
        location="N8",
        victim_count=2,
    )
    assert s4.emergency_type == EmergencyType.MEDICAL_EMERGENCY
    assert s4.emergency_type == "Medical Emergency"

    # Scenario 5: Multi-incident
    s5 = IncidentCreate(
        title="Scenario 5 Dual",
        emergency_type="Multi-incident",
        description="Two simultaneous incidents",
        location="N1",
        victim_count=10,
    )
    assert s5.emergency_type == EmergencyType.MULTI_INCIDENT
    assert s5.emergency_type == "Multi-incident"


def test_emergency_type_custom_and_unforeseen_strings():
    """Verify custom or unrecognized natural language strings are accepted gracefully."""
    custom = IncidentCreate(
        title="Structural Collapse",
        emergency_type="Building Structural Failure",
        description="Unprecedented event",
        location="N5",
        victim_count=5,
    )
    assert custom.emergency_type == "Building Structural Failure"


def test_incident_orm_mapping_with_demo_scenario_types():
    """Verify IncidentResponse converts ORM models with Flood, Fire, and Test emergency types."""
    test_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    # ORM with "Flood"
    orm_flood = Incident(
        id=test_id,
        title="River Flood",
        emergency_type="Flood",
        description="Flooded streets",
        location="N2",
        victim_count=8,
        severity="Critical",
        weather="Heavy Rain",
        road_condition="Flooded",
        status="Reported",
        created_at=now,
        updated_at=now,
    )
    resp_flood = IncidentResponse.model_validate(orm_flood)
    assert resp_flood.emergency_type == EmergencyType.FLOOD

    # ORM with raw test string
    orm_test = Incident(
        id=test_id,
        title="Test Incident",
        emergency_type="Test",
        description="Test record",
        location="N1",
        victim_count=1,
        severity="Low",
        weather="Clear",
        road_condition="Clear",
        status="Reported",
        created_at=now,
        updated_at=now,
    )
    resp_test = IncidentResponse.model_validate(orm_test)
    assert resp_test.emergency_type == "Test"


def test_severity_and_priority_case_insensitive_coercion():
    """Verify lowercase severity and priority inputs are normalized gracefully."""
    inc = IncidentCreate(
        title="Low Severity Case",
        emergency_type="Road accident",
        description="Minor bump",
        location="N1",
        victim_count=1,
        severity="critical",  # Lowercase
    )
    assert inc.severity == IncidentSeverity.CRITICAL

    update = IncidentUpdate(priority="p1_critical")
    assert update.priority == PriorityLevel.P1_CRITICAL

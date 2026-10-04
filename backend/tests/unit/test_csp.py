"""
Unit Tests for Module IV: Constraint Satisfaction Problem (CSP) Solver.
Verifies variable domains, availability, capacity, hospital bed constraints,
AC-3 arc consistency, forward checking, and multi-incident mutual exclusion.
"""

import pytest

from app.csp.problem import DispatchCSP, IncidentSpec, AmbulanceSpec, HospitalSpec
from app.csp.solver import CSPSolver
from app.search.graph import RoadGraph


@pytest.fixture
def graph() -> RoadGraph:
    return RoadGraph.build_canonical_network()


def test_csp_scenario_1_capacity_and_maintenance_rejection(graph: RoadGraph):
    """
    Scenario 1: 6 victims at N1.
    - Ambulance A1 has capacity 4 -> REJECTED (Capacity insufficient)
    - Ambulance A3 has status Maintenance -> REJECTED (Status is Maintenance)
    - Ambulance A2 has capacity 6 and status Available -> SELECTED
    - Hospital H1 (capacity 20) -> SELECTED
    """
    incident = IncidentSpec(id="INC-001", location="N1", victim_count=6, severity="Critical")
    csp = DispatchCSP(incident=incident, graph=graph)
    solver = CSPSolver(use_ac3=True, use_forward_checking=True)

    result = solver.solve(csp)

    assert result.success is True
    assert result.assignment["ambulance"] == "A2"
    assert result.assignment["hospital"] in ("H1", "H2")
    assert "route" in result.assignment
    assert len(result.assignment["route"]) > 0

    # Verify rejected candidates with explicit reasons
    rejection_map = {r.candidate: r.reason for r in result.rejected_candidates}
    assert "A1" in rejection_map
    assert "insufficient" in rejection_map["A1"].lower()

    assert "A3" in rejection_map
    assert "maintenance" in rejection_map["A3"].lower()


def test_csp_hospital_bed_capacity_exhaustion(graph: RoadGraph):
    """Verify CSP rejects hospitals that lack sufficient emergency bed capacity."""
    # 10 victims: H2 only has 5 available beds, H1 has 15 beds
    incident = IncidentSpec(id="INC-002", location="N2", victim_count=10, severity="Critical")

    # Fleet with large unit
    fleet = [
        AmbulanceSpec(code="A_HEAVY", status="Available", capacity=12, location="A2"),
    ]
    hospitals = [
        HospitalSpec(code="H_SMALL", name="Small Clinic", location="H2", available_emergency_beds=5),
        HospitalSpec(code="H_LARGE", name="Trauma Center", location="H1", available_emergency_beds=15),
    ]

    csp = DispatchCSP(incident=incident, ambulances=fleet, hospitals=hospitals, graph=graph)
    solver = CSPSolver()

    result = solver.solve(csp)
    assert result.success is True
    assert result.assignment["hospital"] == "H_LARGE"

    rejection_map = {r.candidate: r.reason for r in result.rejected_candidates}
    assert "H_SMALL" in rejection_map
    assert "insufficient" in rejection_map["H_SMALL"].lower()


def test_csp_complete_domain_exhaustion_failure(graph: RoadGraph):
    """Verify CSP returns failure when no available ambulance can satisfy capacity."""
    incident = IncidentSpec(id="INC-003", location="N1", victim_count=8, severity="Critical")
    # All ambulances have max capacity 6
    csp = DispatchCSP(incident=incident, graph=graph)
    solver = CSPSolver()

    result = solver.solve(csp)
    assert result.success is False
    assert result.assignment == {}
    assert len(result.rejected_candidates) >= 3


def test_csp_multi_incident_mutual_exclusion(graph: RoadGraph):
    """
    Scenario 5: Two simultaneous incidents requiring ambulances.
    Verify mutual exclusion: the same ambulance cannot be allocated to both incidents.
    """
    inc1 = IncidentSpec(id="INC-1", location="N1", victim_count=3)
    inc2 = IncidentSpec(id="INC-2", location="N4", victim_count=3)

    solver = CSPSolver()
    multi_res = solver.solve_multi_incident(
        incidents=[inc1, inc2],
        graph=graph,
    )

    assert multi_res["success"] is True
    sol1 = multi_res["incident_solutions"]["INC-1"]
    sol2 = multi_res["incident_solutions"]["INC-2"]

    assert sol1.success is True
    assert sol2.success is True

    amb1 = sol1.assignment["ambulance"]
    amb2 = sol2.assignment["ambulance"]

    # Mutual exclusion check: ambulances must be distinct!
    assert amb1 != amb2
    assert set([amb1, amb2]) == {"A1", "A2"}

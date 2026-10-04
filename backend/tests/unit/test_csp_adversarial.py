"""
Adversarial and Empirical Stress-Test Suite for ResQ-AI CSP Solver.
Module IV: Constraint Satisfaction Problem.

Empirical Challenger 2 Verification:
1. Over-constrained scenarios (insufficient fleet, 0-bed hospitals, extreme victim counts).
2. Exact boundary tests for capacity and bed thresholds.
3. Multi-incident concurrent dispatch, mutual exclusion, and fleet starvation.
4. AC-3 arc consistency:
   - Partial domain pruning of unreachable ambulances.
   - Full domain wipeout detection with zero search tree expansion.
   - Comparison of AC-3 enabled vs disabled (search tree pruning efficiency).
5. MRV (Minimum Remaining Values) and LCV (Least Constraining Value) ordering verification.
"""

import pytest
from typing import List

from app.csp.problem import DispatchCSP, IncidentSpec, AmbulanceSpec, HospitalSpec
from app.csp.solver import CSPSolver
from app.search.graph import RoadGraph


@pytest.fixture
def graph() -> RoadGraph:
    return RoadGraph.build_canonical_network()


def test_csp_overconstrained_all_ambulances_in_maintenance(graph: RoadGraph):
    """Stress-test: All ambulances in maintenance -> unary filter fails with 0 nodes explored."""
    incident = IncidentSpec(id="INC-OVER-1", location="N1", victim_count=2, severity="High")
    fleet = [
        AmbulanceSpec(code="A1", status="Maintenance", capacity=4, location="A1"),
        AmbulanceSpec(code="A2", status="Maintenance", capacity=6, location="A2"),
        AmbulanceSpec(code="A3", status="Busy", capacity=6, location="A3"),
    ]

    csp = DispatchCSP(incident=incident, ambulances=fleet, graph=graph)
    solver = CSPSolver(use_ac3=True, use_forward_checking=True)
    result = solver.solve(csp)

    assert result.success is False
    assert result.assignment == {}
    assert result.nodes_explored == 0
    assert result.backtracks == 0
    assert "empty during unary constraint filtering" in result.explanation

    # All 3 ambulances must have explicit rejection logs
    rejections = {r.candidate: r.reason for r in result.rejected_candidates}
    assert len(rejections) == 3
    assert "status is maintenance" in rejections["A1"].lower()
    assert "status is maintenance" in rejections["A2"].lower()
    assert "status is busy" in rejections["A3"].lower()


def test_csp_overconstrained_empty_fleet_and_hospitals(graph: RoadGraph):
    """Stress-test: Empty fleet or empty hospital registry -> immediate graceful failure."""
    incident = IncidentSpec(id="INC-OVER-2", location="N1", victim_count=2)

    # Empty fleet
    csp_no_fleet = DispatchCSP(incident=incident, ambulances=[], graph=graph)
    solver = CSPSolver()
    res_no_fleet = solver.solve(csp_no_fleet)
    assert res_no_fleet.success is False
    assert res_no_fleet.nodes_explored == 0
    assert res_no_fleet.backtracks == 0

    # Empty hospitals
    csp_no_hosp = DispatchCSP(incident=incident, hospitals=[], graph=graph)
    res_no_hosp = solver.solve(csp_no_hosp)
    assert res_no_hosp.success is False
    assert res_no_hosp.nodes_explored == 0
    assert res_no_hosp.backtracks == 0


def test_csp_overconstrained_extreme_victim_count(graph: RoadGraph):
    """Stress-test: 500 victims exceeds all known fleet and hospital capacities."""
    incident = IncidentSpec(id="INC-MASS-CASUALTY", location="N2", victim_count=500, severity="Catastrophic")
    csp = DispatchCSP(incident=incident, graph=graph)
    solver = CSPSolver()

    result = solver.solve(csp)
    assert result.success is False
    assert result.assignment == {}
    assert result.nodes_explored == 0

    rejections = {r.candidate: r.reason for r in result.rejected_candidates}
    # Ambulances rejected for capacity
    for amb in ["A1", "A2", "A3"]:
        assert amb in rejections
    # Hospitals rejected for capacity
    for hosp in ["H1", "H2"]:
        assert hosp in rejections
        assert "insufficient" in rejections[hosp].lower()


def test_csp_exact_boundary_conditions(graph: RoadGraph):
    """Empirically test exact boundary transitions for capacity and beds."""
    solver = CSPSolver()

    # Ambulance Capacity Boundary (capacity=5)
    test_amb = AmbulanceSpec(code="A_TEST", status="Available", capacity=5, location="A1")
    hosp = HospitalSpec(code="H_TEST", name="Test Hospital", location="H1", available_emergency_beds=50)

    # Boundary Pass: victim_count == 5
    csp_pass = DispatchCSP(
        incident=IncidentSpec(id="INC-B5", location="N1", victim_count=5),
        ambulances=[test_amb],
        hospitals=[hosp],
        graph=graph,
    )
    res_pass = solver.solve(csp_pass)
    assert res_pass.success is True
    assert res_pass.assignment["ambulance"] == "A_TEST"

    # Boundary Fail: victim_count == 6
    csp_fail = DispatchCSP(
        incident=IncidentSpec(id="INC-B6", location="N1", victim_count=6),
        ambulances=[test_amb],
        hospitals=[hosp],
        graph=graph,
    )
    res_fail = solver.solve(csp_fail)
    assert res_fail.success is False
    rejections = {r.candidate: r.reason for r in res_fail.rejected_candidates}
    assert "A_TEST" in rejections
    assert "insufficient for 6 victims" in rejections["A_TEST"].lower()

    # Hospital Beds Boundary (beds=10)
    test_hosp = HospitalSpec(code="H_BOUND", name="Boundary Hosp", location="H1", available_emergency_beds=10)
    large_amb = AmbulanceSpec(code="A_LARGE", status="Available", capacity=50, location="A1")

    # Pass: 10 victims
    csp_hosp_pass = DispatchCSP(
        incident=IncidentSpec(id="INC-HB10", location="N1", victim_count=10),
        ambulances=[large_amb],
        hospitals=[test_hosp],
        graph=graph,
    )
    assert solver.solve(csp_hosp_pass).success is True

    # Fail: 11 victims
    csp_hosp_fail = DispatchCSP(
        incident=IncidentSpec(id="INC-HB11", location="N1", victim_count=11),
        ambulances=[large_amb],
        hospitals=[test_hosp],
        graph=graph,
    )
    res_hosp_fail = solver.solve(csp_hosp_fail)
    assert res_hosp_fail.success is False
    h_rejections = {r.candidate: r.reason for r in res_hosp_fail.rejected_candidates}
    assert "H_BOUND" in h_rejections
    assert "insufficient for 11 victims" in h_rejections["H_BOUND"].lower()


def test_csp_multi_incident_starvation_and_fleet_depletion(graph: RoadGraph):
    """
    Stress-test: 4 simultaneous incidents with only 2 available ambulances.
    Verifies graceful partial allocation, fleet starvation handling, and mutual exclusion.
    """
    incidents = [
        IncidentSpec(id="INC-1", location="N1", victim_count=2),
        IncidentSpec(id="INC-2", location="N2", victim_count=3),
        IncidentSpec(id="INC-3", location="N3", victim_count=2),
        IncidentSpec(id="INC-4", location="N4", victim_count=1),
    ]

    fleet = [
        AmbulanceSpec(code="A1", status="Available", capacity=4, location="A1"),
        AmbulanceSpec(code="A2", status="Available", capacity=6, location="A2"),
    ]

    solver = CSPSolver()
    multi_res = solver.solve_multi_incident(
        incidents=incidents,
        ambulances=fleet,
        graph=graph,
    )

    # Total batch success must be False because fleet is exhausted
    assert multi_res["success"] is False

    # Exactly 2 ambulances were assigned
    assigned = multi_res["assigned_ambulances"]
    assert len(assigned) == 2
    assert set(assigned) == {"A1", "A2"}

    # First two incidents successfully assigned distinct ambulances
    sol1 = multi_res["incident_solutions"]["INC-1"]
    sol2 = multi_res["incident_solutions"]["INC-2"]
    assert sol1.success is True
    assert sol2.success is True
    assert sol1.assignment["ambulance"] != sol2.assignment["ambulance"]

    # Incidents 3 and 4 failed due to empty fleet
    sol3 = multi_res["incident_solutions"]["INC-3"]
    sol4 = multi_res["incident_solutions"]["INC-4"]
    assert sol3.success is False
    assert sol4.success is False
    assert sol3.assignment == {}
    assert sol4.assignment == {}


def test_csp_ac3_partial_domain_pruning(graph: RoadGraph):
    """
    Verify AC-3 prunes unreachable ambulances while preserving reachable ones.
    Setup: A1 is blocked from reaching incident N1, but A2 has a clear path.
    Unary constraints: Both A1 and A2 are Available with capacity 4 (incident victim_count=2).
    """
    # Block road connecting A1 to N1
    graph.set_blocked("A1", "N8", True)
    graph.set_blocked("A1", "N3", True)

    incident = IncidentSpec(id="INC-AC3-PRUNE", location="N1", victim_count=2)
    fleet = [
        AmbulanceSpec(code="A1", status="Available", capacity=4, location="A1"),
        AmbulanceSpec(code="A2", status="Available", capacity=6, location="A2"),
    ]
    csp = DispatchCSP(incident=incident, ambulances=fleet, graph=graph)
    solver = CSPSolver(use_ac3=True)

    result = solver.solve(csp)

    assert result.success is True
    # A1 was pruned by AC-3, so A2 was selected
    assert result.assignment["ambulance"] == "A2"

    # A1 must be listed in rejected candidates via AC-3
    rejections = {r.candidate: r.reason for r in result.rejected_candidates}
    assert "A1" in rejections
    assert "ac-3 arc consistency pruned" in rejections["A1"].lower()


def test_csp_ac3_empty_domain_wipeout_detected(graph: RoadGraph):
    """
    Stress-test: Total domain wipeout during AC-3 arc consistency.
    Setup: Incident at N1. Unary constraints pass for all ambulances and hospitals.
    All roads connecting N1 to the road network are blocked, isolating the incident.
    """
    for neighbor in graph.get_neighbors("N1"):
        graph.set_blocked("N1", neighbor, True)

    incident = IncidentSpec(id="INC-ISOLATED", location="N1", victim_count=2)
    csp = DispatchCSP(incident=incident, graph=graph)
    solver = CSPSolver(use_ac3=True)

    result = solver.solve(csp)

    assert result.success is False
    assert result.assignment == {}
    # AC-3 detected exhaustion before any backtracking nodes were explored
    assert result.nodes_explored == 0
    assert result.backtracks == 0
    assert "AC-3 arc consistency detected domain exhaustion" in result.explanation
    assert len(result.rejected_candidates) > 0


def test_csp_ac3_vs_no_ac3_search_efficiency(graph: RoadGraph):
    """
    Empirical comparison: AC-3 enabled vs AC-3 disabled.
    When a variable value has no valid binary connection, AC-3 catches it with 0 nodes explored,
    whereas backtracking without AC-3 explores search tree nodes.
    """
    # Isolate hospital H1 by blocking all incident roads to H1
    for neighbor in graph.get_neighbors("H1"):
        graph.set_blocked("H1", neighbor, True)

    # Fleet with available ambulance, only H1 as hospital
    fleet = [AmbulanceSpec(code="A1", status="Available", capacity=4, location="A1")]
    hospitals = [HospitalSpec(code="H1", name="Cut Off Hospital", location="H1", available_emergency_beds=20)]

    incident = IncidentSpec(id="INC-EFF", location="N1", victim_count=2)

    # 1. With AC-3
    csp_ac3 = DispatchCSP(incident=incident, ambulances=fleet, hospitals=hospitals, graph=graph)
    solver_ac3 = CSPSolver(use_ac3=True)
    res_ac3 = solver_ac3.solve(csp_ac3)

    assert res_ac3.success is False
    assert res_ac3.nodes_explored == 0
    assert res_ac3.backtracks == 0

    # 2. Without AC-3 (pure backtracking + forward checking)
    csp_no_ac3 = DispatchCSP(incident=incident, ambulances=fleet, hospitals=hospitals, graph=graph)
    solver_no_ac3 = CSPSolver(use_ac3=False, use_forward_checking=True)
    res_no_ac3 = solver_no_ac3.solve(csp_no_ac3)

    assert res_no_ac3.success is False
    # Backtracking actually explored assignment nodes before failing
    assert res_no_ac3.nodes_explored >= 1
    assert res_no_ac3.backtracks >= 1


def test_csp_heuristic_variable_and_value_ordering(graph: RoadGraph):
    """
    Verify MRV selects variable with smaller domain and LCV orders by distance.
    """
    incident = IncidentSpec(id="INC-ORDER", location="N1", victim_count=2)
    # 2 ambulances, 1 hospital
    fleet = [
        AmbulanceSpec(code="A2", status="Available", capacity=6, location="A2"),
        AmbulanceSpec(code="A1", status="Available", capacity=4, location="A1"),
    ]
    hospitals = [
        HospitalSpec(code="H1", name="Gen", location="H1", available_emergency_beds=20),
    ]

    csp = DispatchCSP(incident=incident, ambulances=fleet, hospitals=hospitals, graph=graph)
    solver = CSPSolver()
    result = solver.solve(csp)

    assert result.success is True
    # In canonical network, A2 is closer to N1 than A1.
    # LCV should prefer A2 first.
    assert result.assignment["ambulance"] == "A2"
    assert result.backtracks == 0

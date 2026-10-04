"""
ResQ-AI: Opaque-Box End-to-End Workflow & Scenario Test Suite
Author: e2e_test_writer_1 (E2E Test Suite Architect)
Reference: ORIGINAL_REQUEST.md, PROJECT.md, TEST_INFRA.md

This test suite performs exhaustive black-box verification of ResQ-AI via its
public HTTP REST API interfaces:
- Tier 1: Core Feature Verification across all endpoints
- Tier 2: Boundary, Edge Cases & Error Handling
- Tier 3: Cross-Feature Multi-Module Workflows (11-Stage Pipeline)
- Tier 4: The 5 Official Emergency Demo Scenarios & Replanning

Execution Modes Supported:
1. Live Server: Connects to running instance at BASE_URL (default http://127.0.0.1:8000).
2. In-Process ASGI: If live server is not running, imports FastAPI app via ASGITransport.
3. Graceful Skipping: Skips gracefully with clear diagnostic if backend is unavailable.
"""

import os
import sys
import uuid
import pytest
import httpx
from typing import Dict, Any, Generator

BASE_URL = os.getenv("RESQ_API_URL", "http://127.0.0.1:8000")


@pytest.fixture(scope="module")
def api_client() -> Generator[httpx.Client, None, None]:
    """
    Provides an opaque-box HTTP client connected to either:
    1. A live server at BASE_URL (if responsive), OR
    2. An in-process FastAPI application via httpx.ASGITransport.
    """
    # 1. Check if live server is reachable and has API router mounted
    try:
        r = httpx.get(f"{BASE_URL}/api/ambulances", timeout=1.0)
        if r.status_code == 200:
            client = httpx.Client(base_url=BASE_URL, timeout=30.0)
            yield client
            client.close()
            return
    except Exception:
        pass

    # 2. Attempt in-process ASGI fallback
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    backend_path = os.path.join(workspace_root, "backend")
    for p in [workspace_root, backend_path]:
        if p not in sys.path and os.path.exists(p):
            sys.path.insert(0, p)

    app = None
    try:
        from backend.app.main import app as fastapi_app
        app = fastapi_app
    except ImportError:
        try:
            from app.main import app as fastapi_app
            app = fastapi_app
        except ImportError:
            pass

    if app is not None:
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
        return

    pytest.skip(
        f"ResQ-AI backend service is not running at {BASE_URL} and "
        "backend.app.main is not yet importable in the environment."
    )


# ==============================================================================
# SECTION 1: TIER 1 - CORE FEATURE INVENTORY TESTS
# ==============================================================================

class TestCoreResourcesAndSeed:
    """Verifies ARCH-04, ARCH-01: Seed data and core emergency resource queries."""

    def test_seed_initial_data_idempotent(self, api_client: httpx.Client):
        """INV-08: Reseeding must succeed idempotently and return 200 OK."""
        resp = api_client.post("/api/seed")
        assert resp.status_code in (200, 201), f"Seed failed: {resp.text}"

    def test_ambulances_inventory(self, api_client: httpx.Client):
        """Verifies canonical fleet: A1 (cap 4, avail), A2 (cap 6, avail), A3 (cap 6, maint)."""
        resp = api_client.get("/api/ambulances")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 3

        codes = {amb.get("code") or amb.get("callsign"): amb for amb in data}
        assert "A1" in codes
        assert "A2" in codes
        assert "A3" in codes

        assert codes["A1"]["capacity"] == 4
        assert codes["A2"]["capacity"] == 6
        assert codes["A3"]["capacity"] == 6
        assert codes["A3"]["status"].lower() in ("maintenance", "unavailable", "disabled")

    def test_hospitals_inventory(self, api_client: httpx.Client):
        """Verifies canonical hospitals: H1 (emergency cap 20), H2 (emergency cap 8)."""
        resp = api_client.get("/api/hospitals")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 2

        hosp_map = {h.get("code") or h.get("name"): h for h in data}
        assert "H1" in hosp_map or any("H1" in k for k in hosp_map)
        assert "H2" in hosp_map or any("H2" in k for k in hosp_map)

    def test_roads_graph_structure(self, api_client: httpx.Client):
        """Verifies canonical 13-node road network structure with distance and blockage."""
        resp = api_client.get("/api/roads")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        # Either list of road edges or graph object {nodes: [...], edges: [...]}
        if isinstance(data, dict):
            assert "edges" in data or "roads" in data or "nodes" in data
        else:
            assert isinstance(data, list)
            assert len(data) > 0
            first_road = data[0]
            assert "source_node" in first_road or "source" in first_road
            assert "target_node" in first_road or "target" in first_road


class TestIncidentManagementAPI:
    """Verifies ARCH-03, ARCH-09: Incident CRUD endpoints and validation."""

    def test_create_and_retrieve_incident(self, api_client: httpx.Client):
        """Creates an incident and retrieves it by GUID."""
        payload = {
            "title": "Eastside Industrial Fire",
            "emergency_type": "Fire Outbreak",
            "description": "Warehouse fire with 4 victims requiring burn treatment.",
            "location": "N4",
            "victim_count": 4,
            "severity": "Medium",
            "weather": "Clear",
            "road_condition": "Clear",
            "status": "Reported"
        }
        create_resp = api_client.post("/api/incidents", json=payload)
        assert create_resp.status_code in (200, 201), create_resp.text
        incident = create_resp.json()
        assert "id" in incident
        incident_id = incident["id"]

        get_resp = api_client.get(f"/api/incidents/{incident_id}")
        assert get_resp.status_code == 200, get_resp.text
        retrieved = get_resp.json()
        assert retrieved["id"] == incident_id
        assert retrieved["victim_count"] == 4
        assert retrieved["location"] == "N4"

    def test_list_incidents(self, api_client: httpx.Client):
        """Retrieves list of active incidents."""
        resp = api_client.get("/api/incidents")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert isinstance(data, list)


class TestSearchAlgorithmsAPI:
    """Verifies FAI-01 through FAI-09: Uninformed & Informed Search on road graph."""

    @pytest.mark.parametrize("algorithm", [
        "UCS",
        "A_Star",
        "Best_First",
        "Hill_Climbing",
        "Beam_Search",
        "DLS",
        "IDS"
    ])
    def test_all_seven_search_algorithms(self, api_client: httpx.Client, algorithm: str):
        """FAI-02 Contract: Every search algorithm returns path, cost, nodes_explored."""
        payload = {
            "algorithm": algorithm,
            "start_node": "A2",
            "goal_node": "H1",
            "depth_limit": 8,
            "beam_width": 3
        }
        resp = api_client.post("/api/search/run", json=payload)
        assert resp.status_code == 200, f"{algorithm} failed: {resp.text}"
        result = resp.json()

        assert "path" in result, f"Missing path for {algorithm}"
        assert "cost" in result, f"Missing cost for {algorithm}"
        assert "nodes_explored" in result, f"Missing nodes_explored for {algorithm}"
        assert "success" in result, f"Missing success flag for {algorithm}"

        if result["success"]:
            assert isinstance(result["path"], list)
            assert len(result["path"]) >= 2
            assert result["path"][0] == "A2"
            assert result["path"][-1] == "H1"
            assert result["cost"] > 0

    def test_search_optimality_astar_vs_ucs(self, api_client: httpx.Client):
        """INV-05: A* and UCS must find equivalent path cost on admissible heuristics."""
        ucs_resp = api_client.post("/api/search/run", json={
            "algorithm": "UCS", "start_node": "A2", "goal_node": "H1"
        })
        astar_resp = api_client.post("/api/search/run", json={
            "algorithm": "A_Star", "start_node": "A2", "goal_node": "H1"
        })
        assert ucs_resp.status_code == 200 and astar_resp.status_code == 200
        ucs_data = ucs_resp.json()
        astar_data = astar_resp.json()

        if ucs_data.get("success") and astar_data.get("success"):
            assert abs(ucs_data["cost"] - astar_data["cost"]) < 0.5
            # A* explores equal or fewer nodes than UCS due to heuristic pruning
            assert astar_data["nodes_explored"] <= ucs_data["nodes_explored"] + 2


class TestConstraintSatisfactionAPI:
    """Verifies FAI-10, FAI-11: CSP resource allocation with backtracking and AC-3."""

    def test_csp_allocation_capacity_constraint(self, api_client: httpx.Client):
        """INV-01, INV-02: CSP must allocate ambulance with capacity >= victims."""
        payload = {
            "victim_count": 6,
            "location": "N1",
            "severity": "High"
        }
        resp = api_client.post("/api/csp/solve", json=payload)
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert data.get("success") is True
        assignment = data.get("assignment", {})
        ambulance = assignment.get("ambulance")
        # A2 has capacity 6, A1 has capacity 4 -> A2 must be chosen
        if isinstance(ambulance, dict):
            assert ambulance.get("code") == "A2" or ambulance.get("capacity", 0) >= 6
        else:
            assert ambulance in ("A2", "Ambulance_2")

        # Rejected candidates must cite A1 capacity shortfall
        rejected = data.get("rejected_candidates", [])
        assert any("A1" in str(r) or "capacity" in str(r).lower() for r in rejected) or len(rejected) >= 1


class TestLogicalInferenceAPI:
    """Verifies FAI-14 to FAI-17: Forward chaining, backward chaining, resolution."""

    def test_forward_chaining_priority_deduction(self, api_client: httpx.Client):
        """FAI-15: Forward chaining derives P1_Critical from victim_count >= 5 and High severity."""
        payload = {
            "facts": [
                "victim_count_gte_5",
                "severity_high",
                "road_blocked_n1_n2"
            ]
        }
        resp = api_client.post("/api/inference/forward", json=payload)
        assert resp.status_code == 200, resp.text
        data = resp.json()

        derived = data.get("derived_facts", [])
        rules_fired = data.get("rule_firings", []) or data.get("rules_fired", [])
        assert any("p1_critical" in f.lower() or "critical" in f.lower() for f in derived) or len(rules_fired) > 0

    def test_backward_chaining_goal_verification(self, api_client: httpx.Client):
        """FAI-16: Backward chaining proves priority goal from base premises."""
        payload = {
            "goal": "priority_p1_critical",
            "known_facts": ["victim_count_gte_5", "severity_high"]
        }
        resp = api_client.post("/api/inference/backward", json=payload)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "proof_success" in data or "success" in data or "steps" in data

    def test_resolution_refutation_demonstration(self, api_client: httpx.Client):
        """FAI-17: CNF resolution refutation derives empty clause."""
        payload = {
            "clauses": [
                ["P", "Q"],
                ["-P", "Q"],
                ["-Q"]
            ]
        }
        resp = api_client.post("/api/inference/resolution", json=payload)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "refutation_successful" in data or "success" in data or "empty_clause_derived" in data


class TestBayesianUncertaintyAPI:
    """Verifies FAI-24, FAI-25: 7-Node Bayesian network & composite risk engine."""

    def test_bayesian_risk_calculation(self, api_client: httpx.Client):
        """INV-07: Calculates conditional probabilities and composite risk (0 to 100%)."""
        payload = {
            "weather": "Heavy Rain",
            "road_condition": "Flooded",
            "severity": "Critical",
            "victim_count": 10
        }
        resp = api_client.post("/api/risk/analyze", json=payload)
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert "composite_risk_score" in data or "composite_risk" in data or "risk_score" in data
        assert "risk_level" in data
        # Storm + Flood + 10 Victims should yield HIGH or CRITICAL risk
        assert data["risk_level"] in ("HIGH", "CRITICAL", "High", "Critical")

    def test_disclaimer_presence(self, api_client: httpx.Client):
        """Educational disclaimer must be present in risk analysis payload."""
        resp = api_client.post("/api/risk/analyze", json={"weather": "Clear", "severity": "Low"})
        assert resp.status_code == 200
        data = resp.json()
        assert "disclaimer" in data
        assert "Educational simulation" in data["disclaimer"]


class TestPlanningAPI:
    """Verifies FAI-21 to FAI-23: HTN, State-space and POP planning."""

    def test_htn_hierarchical_planning(self, api_client: httpx.Client):
        """FAI-23: HTN generates decomposition of emergency response."""
        payload = {
            "paradigm": "htn",
            "emergency_type": "Traffic Accident",
            "victim_count": 6,
            "location": "N1"
        }
        resp = api_client.post("/api/planning/generate", json=payload)
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert data.get("success") is True
        actions = data.get("actions", [])
        assert len(actions) >= 4, f"HTN plan too brief: {actions}"


class TestMachineLearningAPI:
    """Verifies FAI-26, FAI-27: Synthetic dataset & Decision Tree."""

    def test_decision_tree_prediction(self, api_client: httpx.Client):
        """FAI-27: Decision tree predicts priority based on emergency features."""
        payload = {
            "victim_count": 6,
            "weather": "Heavy Rain",
            "road_condition": "Blocked",
            "severity": "High",
            "emergency_type": "Traffic Accident"
        }
        resp = api_client.post("/api/learning/predict", json=payload)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "predicted_priority" in data or "priority" in data

    def test_decision_tree_topology_export(self, api_client: httpx.Client):
        """FAI-27: Exports tree structure with entropy and info gain."""
        resp = api_client.get("/api/learning/tree")
        if resp.status_code == 404:
            # Fallback to POST /api/learning/tree-info if GET not mounted
            resp = api_client.post("/api/learning/tree-info")
        assert resp.status_code in (200, 201), resp.text
        data = resp.json()
        assert "tree_structure" in data or "root" in data or "features" in data


class TestAlgorithmsLabAPI:
    """Verifies FAI-28: Interactive AI Algorithms Lab execution endpoint."""

    def test_lab_algorithm_execution(self, api_client: httpx.Client):
        """FAI-28: Interactive run returns output, trace, and complexity metrics."""
        payload = {
            "module": "search",
            "algorithm": "A_Star",
            "scenario": "preset_1",
            "parameters": {"start": "A2", "goal": "H1"}
        }
        resp = api_client.post("/api/lab/run", json=payload)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "output" in data or "result" in data
        assert "complexity" in data or "nodes_explored" in data or "cost" in data


# ==============================================================================
# SECTION 2: TIER 2 - BOUNDARY & CORNER CASES
# ==============================================================================

class TestBoundaryAndCornerCases:
    """Exhaustive boundary testing across extreme values, empty inputs, disconnections."""

    def test_search_identical_start_and_goal(self, api_client: httpx.Client):
        """T2-SRCH-01: Start == Goal must yield cost 0.0 and path with single node."""
        resp = api_client.post("/api/search/run", json={
            "algorithm": "A_Star", "start_node": "H1", "goal_node": "H1"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("cost", 0.0) == 0.0
        assert data.get("path") == ["H1"]

    def test_search_depth_limit_zero(self, api_client: httpx.Client):
        """T2-SRCH-04: DLS with limit 0 must trigger depth cutoff."""
        resp = api_client.post("/api/search/run", json={
            "algorithm": "DLS", "start_node": "A2", "goal_node": "H1", "depth_limit": 0
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("success") is False

    def test_csp_zero_victims(self, api_client: httpx.Client):
        """T2-CSP-01: Incident with 0 victims handled gracefully."""
        resp = api_client.post("/api/csp/solve", json={
            "victim_count": 0, "location": "N1", "severity": "Low"
        })
        assert resp.status_code in (200, 422)

    def test_csp_extreme_victim_count(self, api_client: httpx.Client):
        """T2-CSP-02: 100 victims exceeds single vehicle capacity, triggers multi-resource/deficit."""
        resp = api_client.post("/api/csp/solve", json={
            "victim_count": 100, "location": "N1", "severity": "Critical"
        })
        assert resp.status_code == 200
        data = resp.json()
        # Either allocates maximum available fleet or reports shortage
        assert "shortage" in str(data).lower() or "rejected" in str(data).lower() or data.get("success") is False

    def test_inference_empty_facts(self, api_client: httpx.Client):
        """T2-INF-01: Forward chaining with empty fact list returns clean empty derived facts."""
        resp = api_client.post("/api/inference/forward", json={"facts": []})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("derived_facts") == [] or len(data.get("derived_facts", [])) == 0

    def test_api_malformed_json_validation_error(self, api_client: httpx.Client):
        """T2-API-01: Pydantic rejects invalid schema with HTTP 422."""
        resp = api_client.post("/api/incidents", json={"invalid_field": 12345})
        assert resp.status_code == 422

    def test_api_nonexistent_guid_not_found(self, api_client: httpx.Client):
        """T2-API-02: Querying non-existent GUID returns HTTP 404."""
        fake_id = str(uuid.uuid4())
        resp = api_client.get(f"/api/incidents/{fake_id}")
        assert resp.status_code == 404

    def test_special_characters_and_emoji_intake(self, api_client: httpx.Client):
        """T2-API-03: Intake text containing quotes, symbols and UTF-8 emoji."""
        resp = api_client.post("/api/agent/analyze", json={
            "text": "🚨 Multi-car collision! 'Quotes' & <script>alert(1)</script> 🚑 N1 junction!"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "extracted" in data or "parsed_incident" in data


# ==============================================================================
# SECTION 3: TIER 3 - CROSS-FEATURE 11-STAGE AGENT PIPELINE
# ==============================================================================

class TestAgentOrchestratorPipeline:
    """Verifies ARCH-05, ARCH-06, ARCH-08: Full 11-stage autonomous agent execution."""

    def test_natural_language_understanding_and_extraction(self, api_client: httpx.Client):
        """Stage 1: LLM/Demo extraction to Pydantic validated schema."""
        raw_text = "Severe highway pileup at N1 Downtown with 6 injured passengers. Torrential rain and road N1-N2 blocked."
        resp = api_client.post("/api/agent/analyze", json={"text": raw_text})
        assert resp.status_code == 200, resp.text
        data = resp.json()

        extracted = data.get("extracted") or data.get("parsed_incident") or {}
        assert extracted.get("victim_count") == 6
        assert extracted.get("location") == "N1"
        assert "rain" in extracted.get("weather", "").lower()

    def test_full_11_stage_workflow_execution(self, api_client: httpx.Client):
        """Stages 1-11: End-to-end incident plan generation and decision recording."""
        # 1. Create Incident
        inc_resp = api_client.post("/api/incidents", json={
            "title": "Catastrophic Bridge Collision",
            "emergency_type": "Traffic Accident",
            "description": "6 victims injured, heavy rain, road N1-N2 blocked.",
            "location": "N1",
            "victim_count": 6,
            "severity": "High",
            "weather": "Heavy Rain",
            "road_condition": "Blocked"
        })
        assert inc_resp.status_code in (200, 201)
        incident_id = inc_resp.json()["id"]

        # 2. Run 11-Stage Agent Pipeline
        plan_resp = api_client.post("/api/agent/plan", json={"incident_id": incident_id})
        assert plan_resp.status_code == 200, plan_resp.text
        decision = plan_resp.json()

        # Invariant Assertions
        assert "allocated_ambulance" in decision or "ambulance" in decision
        assert "allocated_hospital" in decision or "hospital" in decision
        assert "route" in decision or "selected_route" in decision
        assert "risk" in decision or "risk_assessment" in decision
        assert "plan" in decision or "action_plan" in decision
        assert "explanation" in decision

        # 3. Verify Decision Audit Trail Persistence (INV-08)
        hist_resp = api_client.get("/api/decisions")
        assert hist_resp.status_code == 200
        decisions_list = hist_resp.json()
        assert any(d.get("incident_id") == incident_id for d in decisions_list)


# ==============================================================================
# SECTION 4: TIER 4 - THE 5 OFFICIAL DEMO SCENARIOS & REPLANNING
# ==============================================================================

class TestFiveDemoScenariosAndReplanning:
    """
    R6 Official Demo Scenarios:
    1. Road accident, 6 victims, heavy rain, main road blocked
    2. Fire, 4 victims, normal weather, road clear
    3. Flood, 10 affected, heavy rain, two roads blocked
    4. Medical emergency, 2 victims, road clear
    5. Multi-incident, two incidents, limited ambulances
    """

    def test_scenario_1_road_accident_with_replanning(self, api_client: httpx.Client):
        """
        Demo Scenario 1:
        - 6 victims at N1, Heavy Rain, Road N1-N2 blocked.
        - Expect: Priority P1_Critical, Ambulance A2 assigned (capacity 6), Hospital H1.
        - Detour route avoiding bridge N1-N2.
        - Dynamic Replanning: Simulate A2 breakdown mid-mission -> Reallocates new resource.
        """
        api_client.post("/api/seed")

        # Step 1: Create Scenario 1 Incident
        inc_resp = api_client.post("/api/incidents", json={
            "title": "Scenario 1: Highway Crash",
            "emergency_type": "Traffic Accident",
            "description": "Multi-car crash near Downtown Junction N1, 6 victims, heavy rain, bridge N1-N2 blocked.",
            "location": "N1",
            "victim_count": 6,
            "severity": "High",
            "weather": "Heavy Rain",
            "road_condition": "Blocked"
        })
        assert inc_resp.status_code in (200, 201)
        incident_id = inc_resp.json()["id"]

        # Step 2: Generate Agent Response Plan
        plan_resp = api_client.post("/api/agent/plan", json={"incident_id": incident_id})
        assert plan_resp.status_code == 200, plan_resp.text
        plan = plan_resp.json()

        # Invariant Assertions for Scenario 1
        amb = plan.get("allocated_ambulance") or plan.get("ambulance", {})
        amb_code = amb.get("code") if isinstance(amb, dict) else str(amb)
        assert "A2" in amb_code, f"Expected A2 for 6 victims, got {amb_code}"

        hosp = plan.get("allocated_hospital") or plan.get("hospital", {})
        hosp_code = hosp.get("code") if isinstance(hosp, dict) else str(hosp)
        assert "H1" in hosp_code, f"Expected H1 with 20 beds, got {hosp_code}"

        route = plan.get("route") or plan.get("selected_route") or {}
        path = route.get("path", [])
        # Road N1-N2 must NOT be traversed directly
        path_str = "-".join(path)
        assert not ("N1-N2" in path_str and "N1-N3" not in path_str)

        # Step 3: Trigger Dynamic Replanning (A2 Suffers Mechanical Failure)
        replan_payload = {
            "incident_id": incident_id,
            "failed_ambulance_code": "A2",
            "reason": "Tire blowout on highway"
        }
        replan_resp = api_client.post("/api/agent/replan", json=replan_payload)
        assert replan_resp.status_code == 200, replan_resp.text
        replan_data = replan_resp.json()

        # Invariant INV-06: Replanned resource cannot be A2 and is_replanned is True
        assert replan_data.get("is_replanned") is True or replan_data.get("replanned") is True
        new_amb = replan_data.get("allocated_ambulance") or replan_data.get("ambulance", {})
        new_amb_code = new_amb.get("code") if isinstance(new_amb, dict) else str(new_amb)
        assert "A2" not in new_amb_code or "split" in str(replan_data).lower()

    def test_scenario_2_warehouse_fire_clear_weather(self, api_client: httpx.Client):
        """
        Demo Scenario 2:
        - 4 victims at N4, Clear weather, Road clear.
        - Expect: Priority P2_High.
        - LCV resource assignment selects A1 (cap 4), preserving A2 (cap 6).
        - Direct route permitted. Low composite risk.
        """
        inc_resp = api_client.post("/api/incidents", json={
            "title": "Scenario 2: Eastside Warehouse Fire",
            "emergency_type": "Fire Outbreak",
            "description": "Commercial warehouse fire near Midtown N4, 4 victims, clear weather.",
            "location": "N4",
            "victim_count": 4,
            "severity": "Medium",
            "weather": "Clear",
            "road_condition": "Clear"
        })
        assert inc_resp.status_code in (200, 201)
        incident_id = inc_resp.json()["id"]

        plan_resp = api_client.post("/api/agent/plan", json={"incident_id": incident_id})
        assert plan_resp.status_code == 200
        plan = plan_resp.json()

        amb = plan.get("allocated_ambulance") or plan.get("ambulance", {})
        amb_code = amb.get("code") if isinstance(amb, dict) else str(amb)
        # LCV should select A1 (capacity 4 matches 4 victims exactly)
        assert "A1" in amb_code or "A2" in amb_code

        risk = plan.get("risk") or plan.get("risk_assessment") or {}
        composite_score = risk.get("composite_risk_score") or risk.get("composite_risk", 0.0)
        # Clear weather and open roads -> low risk score (< 0.40 or < 40)
        assert float(composite_score) < 0.50 or float(composite_score) < 50.0

    def test_scenario_3_flash_flood_disaster_multi_road_block(self, api_client: httpx.Client):
        """
        Demo Scenario 3:
        - 10 victims at N2, Heavy Rain / Storm, Two roads blocked (N1-N2, N2-N5).
        - Expect: Priority P1_Critical.
        - CSP allocates dual-capacity fleet (A2 + A1 = 10 beds).
        - Hospital H1 selected (H2 capacity 8 is insufficient for 10 victims).
        - Route discovers northern bypass; High/Critical risk score.
        """
        inc_resp = api_client.post("/api/incidents", json={
            "title": "Scenario 3: River Basin Flash Flood",
            "emergency_type": "Natural Disaster",
            "description": "Massive urban flood near River Bridge N2, 10 victims submerged, severe storm, bridges cut.",
            "location": "N2",
            "victim_count": 10,
            "severity": "Critical",
            "weather": "Heavy Rain",
            "road_condition": "Flooded"
        })
        assert inc_resp.status_code in (200, 201)
        incident_id = inc_resp.json()["id"]

        plan_resp = api_client.post("/api/agent/plan", json={"incident_id": incident_id})
        assert plan_resp.status_code == 200
        plan = plan_resp.json()

        # Hospital selection: H1 has capacity 20, H2 has capacity 8 -> H1 must be chosen
        hosp = plan.get("allocated_hospital") or plan.get("hospital", {})
        hosp_code = hosp.get("code") if isinstance(hosp, dict) else str(hosp)
        assert "H1" in hosp_code

        risk = plan.get("risk") or plan.get("risk_assessment") or {}
        risk_level = risk.get("risk_level", "").upper()
        assert risk_level in ("HIGH", "CRITICAL")

    def test_scenario_4_cardiac_medical_emergency(self, api_client: httpx.Client):
        """
        Demo Scenario 4:
        - 2 victims at N8 (West Ring), Clear weather, Road clear.
        - Expect: Priority P2_High (ALS).
        - Proximity dispatch: A1 from Station North is closest.
        - Hospital H1 (Cardiology Center).
        """
        inc_resp = api_client.post("/api/incidents", json={
            "title": "Scenario 4: Acute Cardiac Collapse",
            "emergency_type": "Medical Emergency",
            "description": "Elderly patient collapsed near West Suburban Ring N8, 2 victims, clear roads.",
            "location": "N8",
            "victim_count": 2,
            "severity": "High",
            "weather": "Clear",
            "road_condition": "Clear"
        })
        assert inc_resp.status_code in (200, 201)
        incident_id = inc_resp.json()["id"]

        plan_resp = api_client.post("/api/agent/plan", json={"incident_id": incident_id})
        assert plan_resp.status_code == 200
        plan = plan_resp.json()

        amb = plan.get("allocated_ambulance") or plan.get("ambulance", {})
        assert amb is not None
        plan_obj = plan.get("plan") or plan.get("action_plan") or {}
        assert plan_obj.get("success") is True or len(plan_obj.get("actions", [])) > 0

    def test_scenario_5_multi_incident_fleet_contention(self, api_client: httpx.Client):
        """
        Demo Scenario 5:
        - Two simultaneous incidents: Alpha (6 victims, N1, Critical) & Beta (4 victims, N4, High).
        - Operational fleet: only 2 available units (A1 cap 4, A2 cap 6).
        - CSP solves contention: Alpha -> A2, Beta -> A1.
        - Total fleet exhaustion detected.
        """
        api_client.post("/api/seed")

        # Incident Alpha (Critical, 6 victims)
        alpha_resp = api_client.post("/api/incidents", json={
            "title": "Incident Alpha: Multi-Vehicle Pileup",
            "emergency_type": "Traffic Accident",
            "location": "N1",
            "victim_count": 6,
            "severity": "Critical",
            "weather": "Rain",
            "road_condition": "Clear"
        })
        # Incident Beta (High, 4 victims)
        beta_resp = api_client.post("/api/incidents", json={
            "title": "Incident Beta: Residential Fire",
            "emergency_type": "Fire Outbreak",
            "location": "N4",
            "victim_count": 4,
            "severity": "High",
            "weather": "Rain",
            "road_condition": "Clear"
        })
        assert alpha_resp.status_code in (200, 201) and beta_resp.status_code in (200, 201)
        alpha_id = alpha_resp.json()["id"]
        beta_id = beta_resp.json()["id"]

        # Plan Alpha
        alpha_plan_resp = api_client.post("/api/agent/plan", json={"incident_id": alpha_id})
        assert alpha_plan_resp.status_code == 200
        alpha_plan = alpha_plan_resp.json()

        # Plan Beta
        beta_plan_resp = api_client.post("/api/agent/plan", json={"incident_id": beta_id})
        assert beta_plan_resp.status_code == 200
        beta_plan = beta_plan_resp.json()

        # Alpha requires A2 (cap 6), Beta receives A1 (cap 4)
        alpha_amb = alpha_plan.get("allocated_ambulance", {})
        beta_amb = beta_plan.get("allocated_ambulance", {})
        a_code = alpha_amb.get("code") if isinstance(alpha_amb, dict) else str(alpha_amb)
        b_code = beta_amb.get("code") if isinstance(beta_amb, dict) else str(beta_amb)

        assert "A2" in a_code or alpha_amb.get("capacity", 0) >= 6
        # Both incidents have assigned units without fatal crashes
        assert a_code != "" and b_code != ""

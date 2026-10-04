"""
Unit Tests for ResQ-AI Automated Planning (Module VII).

Verifies:
1. STRIPS Domain & Action Operators (schemas, grounding, preconditions, effects, transitions)
2. Forward Progression State-Space Planner (BFS, heuristic A*, cycle prevention, trajectories, dict mode)
3. Partial-Order Planner (causal links, open conditions, threat clobbering & resolution, topological linearization)
4. Hierarchical Task Network (5 emergency decomposition methods, decomposition trees, dependencies, orchestrator contract)
5. Planning Schemas & REST API Integration (/api/planning/generate across all paradigms, empty frontend request)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.planning import (
    STRIPSAction,
    create_canonical_action_schemas,
    create_emergency_planning_problem,
    StateSpacePlanner,
    StateSpacePlanResult,
    PlanPath,
    PartialOrderPlanner,
    POPPlan,
    CausalLink,
    OrderingConstraint,
    HTNPlanner,
    Task,
    HTNMethod,
)
from app.planning.hierarchical import HTNPlanner as ReExportedHTNPlanner
from app.planning.partial_order import PartialOrderPlanner as ReExportedPOPPlanner
from app.schemas.planning import (
    PlanActionStep,
    PlanCausalLink,
    PlanGenerateRequest,
    PlanGenerateResponse,
    PlanParadigm,
)


@pytest.fixture
def client():
    return TestClient(app)


# =============================================================================
# 1. STRIPS Action Operators & Domain Tests
# =============================================================================

class TestSTRIPSDomain:
    """Tests for STRIPS action schemas, state transitions, and ground problem generation."""

    def test_canonical_schemas_structure(self):
        schemas = create_canonical_action_schemas()
        assert len(schemas) == 6
        names = {s.name for s in schemas}
        expected = {
            "DispatchAmbulance",
            "Navigate",
            "TreatVictim",
            "TransportVictim",
            "PrepareHospitalBed",
            "AdmitVictim",
        }
        assert names == expected

    def test_strips_action_applicability_and_apply(self):
        action = STRIPSAction(
            name="DispatchAmbulance",
            preconditions=frozenset({"Available(A1)", "At(A1, Base)", "IncidentReported(INC-1, Scene)"}),
            add_effects=frozenset({"Dispatched(A1, INC-1)", "EnRoute(A1, Base, Scene)"}),
            delete_effects=frozenset({"Available(A1)", "At(A1, Base)"}),
        )

        state = frozenset({"Available(A1)", "At(A1, Base)", "IncidentReported(INC-1, Scene)", "Hospital(H1)"})
        assert action.is_applicable(state) is True

        new_state = action.apply(state)
        assert "Available(A1)" not in new_state
        assert "At(A1, Base)" not in new_state
        assert "Dispatched(A1, INC-1)" in new_state
        assert "EnRoute(A1, Base, Scene)" in new_state
        assert "Hospital(H1)" in new_state

    def test_strips_action_unmet_preconditions_raises_error(self):
        action = STRIPSAction(
            name="TreatVictim",
            preconditions=frozenset({"At(A1, Scene)", "Dispatched(A1, INC-1)"}),
            add_effects=frozenset({"VictimsTreated(INC-1)"}),
            delete_effects=frozenset(),
        )
        invalid_state = frozenset({"At(A1, Base)"})
        assert action.is_applicable(invalid_state) is False
        with pytest.raises(ValueError, match="preconditions .* not met"):
            action.apply(invalid_state)

    def test_grounding_parameterized_schema(self):
        schema = STRIPSAction(
            name="Navigate",
            params=("?amb", "?from", "?to"),
            preconditions=frozenset({"EnRoute(?amb, ?from, ?to)"}),
            add_effects=frozenset({"At(?amb, ?to)"}),
            delete_effects=frozenset({"EnRoute(?amb, ?from, ?to)"}),
        )
        grounded = schema.ground({"?amb": "A2", "?from": "Central_Base", "?to": "Hospital_H1"})
        assert "A2" in grounded.params
        assert "EnRoute(A2, Central_Base, Hospital_H1)" in grounded.preconditions
        assert "At(A2, Hospital_H1)" in grounded.add_effects
        assert "EnRoute(A2, Central_Base, Hospital_H1)" in grounded.delete_effects

    def test_create_emergency_planning_problem(self):
        s0, goal, actions = create_emergency_planning_problem(
            ambulance="A1",
            station="Station_1",
            incident="INC-99",
            scene="Scene_X",
            hospital="Hosp_Z",
            include_bed_prep=True,
        )
        assert "Available(A1)" in s0
        assert "At(A1, Station_1)" in s0
        assert "IncidentReported(INC-99, Scene_X)" in s0
        assert "Admitted(INC-99, Hosp_Z)" in goal
        assert "BedPrepared(Hosp_Z, INC-99)" in goal
        assert len(actions) == 6


# =============================================================================
# 2. Forward Progression State-Space Planner Tests
# =============================================================================

class TestStateSpacePlanner:
    """Tests for forward state-space progression planning (BFS and Heuristic)."""

    def test_state_space_bfs_solves_canonical_problem(self):
        s0, goal, actions = create_emergency_planning_problem(include_bed_prep=False)
        planner = StateSpacePlanner(s0, goal, actions)
        plan = planner.plan(search_strategy="bfs")

        assert isinstance(plan, list)
        assert plan.success is True
        assert len(plan) >= 4  # Dispatch, Navigate, Treat, Transport, Admit
        assert "DispatchAmbulance" in plan[0]

        # Verify that applying the plan actions leads to a goal state
        curr_state = s0
        for act in plan.actions:
            curr_state = act.apply(curr_state)
        assert goal.issubset(curr_state)

    def test_state_space_heuristic_astar_solves_canonical_problem(self):
        s0, goal, actions = create_emergency_planning_problem(include_bed_prep=True)
        planner = StateSpacePlanner(s0, goal, actions)
        res = planner.plan_detailed(search_strategy="heuristic")

        assert res.success is True
        assert len(res.plan) >= 5
        assert res.nodes_explored > 0
        assert res.cost > 0.0
        assert res.duration_minutes > 0.0

        # Check trajectory continuity
        assert len(res.trajectory) == len(res.plan) + 1
        assert res.trajectory[0] == s0
        assert goal.issubset(res.trajectory[-1])

    def test_state_space_cycle_prevention(self):
        # Action that toggles back and forth between two states
        a1 = STRIPSAction(
            name="ToggleForward",
            preconditions=frozenset({"P"}),
            add_effects=frozenset({"Q"}),
            delete_effects=frozenset({"P"}),
        )
        a2 = STRIPSAction(
            name="ToggleBack",
            preconditions=frozenset({"Q"}),
            add_effects=frozenset({"P"}),
            delete_effects=frozenset({"Q"}),
        )
        planner = StateSpacePlanner(
            initial_state=frozenset({"P"}),
            goal_state=frozenset({"GoalUnreachable"}),
            actions=[a1, a2],
            max_expansions=50,
        )
        res = planner.plan_detailed()
        assert res.success is False
        assert res.plan == []

    def test_state_space_backward_compatibility_dict_mode(self):
        # Legacy dictionary interface from early prototype
        initial = {"loc": "A", "victim": "untreated"}
        goal = {"loc": "B", "victim": "treated"}
        actions = [
            {"name": "treat", "preconditions": {"loc": "A"}, "effects": {"victim": "treated"}},
            {"name": "move", "preconditions": {"victim": "treated"}, "effects": {"loc": "B"}},
        ]
        planner = StateSpacePlanner(initial, goal, actions)
        plan = planner.plan()

        assert plan == ["treat", "move"]
        assert plan.success is True
        assert len(plan) == 2


# =============================================================================
# 3. Partial-Order Planner (POP) Tests
# =============================================================================

class TestPartialOrderPlanner:
    """Tests for least-commitment Partial-Order Planning, causal links, and threat clobbering."""

    def test_pop_canonical_problem_with_causal_links(self):
        s0, goal, actions = create_emergency_planning_problem(include_bed_prep=True)
        pop = PartialOrderPlanner(domain_actions=actions)
        plan = pop.solve(s0, goal, actions)

        assert plan.success is True
        assert len(plan.causal_links) > 0
        assert len(plan.orderings) > 0
        assert len(plan.linearized_plan) >= 5

        # Inspect causal links
        link_conditions = {cl.condition for cl in plan.causal_links}
        assert any("VictimsTreated" in c for c in link_conditions)
        assert any("BedPrepared" in c for c in link_conditions)

    def test_pop_threat_clobbering_and_resolution(self):
        """
        Verify that when an action deletes a condition required by another action,
        POP resolves the threat by introducing ordering constraints.
        """
        s0, goal, actions = create_emergency_planning_problem(include_bed_prep=False)
        pop = PartialOrderPlanner(domain_actions=actions)
        plan = pop.solve(s0, goal, actions)

        assert plan.success is True
        linear = plan.linearized_plan

        # TransportVictim deletes At(A1, Accident_Site), while TreatVictim requires At(A1, Accident_Site).
        # In any valid linearization, TreatVictim must be ordered before TransportVictim!
        treat_idx = next(i for i, name in enumerate(linear) if "TreatVictim" in name)
        transport_idx = next(i for i, name in enumerate(linear) if "TransportVictim" in name)
        assert treat_idx < transport_idx, "TreatVictim must execute before TransportVictim clobbers scene location"

    def test_pop_parallel_action_independence(self):
        """
        PrepareHospitalBed does not depend on or delete ambulance transit,
        so in the partial order graph it is an independent parallel branch.
        """
        s0, goal, actions = create_emergency_planning_problem(include_bed_prep=True)
        pop = PartialOrderPlanner(domain_actions=actions)
        plan = pop.solve(s0, goal, actions)

        assert plan.success is True
        # Verify causal link to AdmitVictim or Finish for BedPrepared
        bed_links = [cl for cl in plan.causal_links if "BedPrepared" in cl.condition]
        assert len(bed_links) > 0
        assert all("PrepareHospitalBed" in cl.source_id for cl in bed_links)
        assert any("AdmitVictim" in cl.target_id or "Finish" in cl.target_id for cl in bed_links)

    def test_pop_backward_compatibility_plan_method(self):
        pop = ReExportedPOPPlanner()
        res = pop.plan()
        assert res["success"] is True
        assert "actions" in res
        assert "linearized_plan" in res
        assert "causal_links" in res


# =============================================================================
# 4. Hierarchical Task Network (HTN) Planner Tests
# =============================================================================

class TestHTNPlanner:
    """Tests for HTN hierarchical decomposition across all 5 emergency types."""

    @pytest.mark.parametrize("emergency_type,expected_method,expected_keyword", [
        ("Road accident", "DecomposeRoadAccident", "C-spine immobilization"),
        ("Fire", "DecomposeFireResponse", "Burn"),
        ("Flood", "DecomposeFloodResponse", "Hypothermia"),
        ("Medical emergency", "DecomposeMedicalEmergency", "Cardiac"),
        ("Multi-incident", "DecomposeMultiIncident", "START"),
    ])
    def test_htn_all_5_emergency_methods(self, emergency_type, expected_method, expected_keyword):
        planner = HTNPlanner()
        res = planner.plan_emergency(
            emergency_type=emergency_type,
            incident_id="INC-TEST",
            ambulance="A1",
            hospital="City_General",
            location="Test_Location",
            victims=5,
        )

        assert res["success"] is True
        assert res["method"] == expected_method
        assert len(res["actions"]) == 7
        assert len(res["final_plan"]) == 7

        # Check decomposition tree
        tree = res["decomposition_tree"]
        assert tree["task"] == "ResolveEmergency"
        assert tree["method"] == expected_method
        assert len(tree["subtasks"]) == 7

        # Verify incident-specific domain keyword in actions or parameters
        action_text = " ".join(
            f"{a['action']} {a.get('details', {})}" for a in res["actions"]
        )
        assert expected_keyword.lower() in action_text.lower()

    def test_htn_orchestrator_backward_compatibility(self):
        """
        Verify that HTNPlanner.plan() matches the exact contract expected by
        app/agent/orchestrator.py:
        plan_res = self.planner.plan(self.state["facts"], {"status": "Complete"})
        self.state["current_plan"] = plan_res["final_plan"]
        """
        planner = ReExportedHTNPlanner()
        facts = {
            "emergency_type": "Fire",
            "incident_id": "INC-42",
            "location": "Warehouse_Dist",
            "victim_count": 3,
        }
        res = planner.plan(facts, {"status": "Complete"})

        assert isinstance(res, dict)
        assert "final_plan" in res
        assert isinstance(res["final_plan"], list)
        assert len(res["final_plan"]) == 7
        assert "actions" in res
        assert "initial_state" in res
        assert "goal_state" in res
        assert "dependencies" in res

    def test_htn_action_dependencies_structure(self):
        planner = HTNPlanner()
        res = planner.plan_emergency("Road accident")
        actions = res["actions"]

        # Step 1 has no dependencies
        assert actions[0]["dependencies"] == []
        # Step 2 and 3 depend on step 1
        assert actions[1]["dependencies"] == [1]
        assert actions[2]["dependencies"] == [1]
        # Step 7 depends on steps 3 and 6
        assert actions[6]["dependencies"] == [3, 6]


# =============================================================================
# 5. Planning API & Schemas Integration Tests
# =============================================================================

class TestPlanningAPIAndSchemas:
    """Tests for REST API endpoints and Pydantic schemas."""

    def test_api_generate_empty_payload_default_frontend_behavior(self, client):
        """
        Frontend Planning.jsx calls generatePlan({}) with empty body.
        Must return HTTP 200 with complete hierarchical plan.
        """
        resp = client.post("/api/planning/generate", json={})
        assert resp.status_code == 200
        data = resp.json()

        assert data["success"] is True
        assert data["paradigm"] == "Hierarchical"
        assert "initialState" in data
        assert "goal" in data
        assert len(data["actions"]) == 7

        # Ensure action fields needed by Planning.jsx exist
        step1 = data["actions"][0]
        assert "id" in step1
        assert "action" in step1
        assert "status" in step1
        assert step1["status"] == "done"
        assert "dependencies" in step1

    def test_api_generate_state_space_paradigm(self, client):
        resp = client.post(
            "/api/planning/generate",
            json={
                "paradigm": "State-Space",
                "start_node": "Central_Base",
                "destination_node": "Accident_Site",
                "search_strategy": "heuristic",
            },
        )
        assert resp.status_code == 200
        data = resp.json()

        assert data["success"] is True
        assert data["paradigm"] == "State-Space"
        assert len(data["actions"]) >= 5
        assert data["nodes_explored"] is not None
        assert data["estimated_duration_minutes"] > 0

    def test_api_generate_partial_order_paradigm(self, client):
        resp = client.post(
            "/api/planning/generate",
            json={
                "paradigm": "Partial-Order",
                "start_node": "Central_Base",
                "destination_node": "Accident_Site",
            },
        )
        assert resp.status_code == 200
        data = resp.json()

        assert data["success"] is True
        assert data["paradigm"] == "Partial-Order"
        assert len(data["actions"]) >= 5
        assert data["causal_links"] is not None
        assert len(data["causal_links"]) > 0

        # Verify causal link schema structure
        cl0 = data["causal_links"][0]
        assert "source_action" in cl0
        assert "condition" in cl0
        assert "target_action" in cl0

    def test_planning_schemas_validation(self):
        # Verify PlanGenerateRequest defaults
        req = PlanGenerateRequest()
        assert req.paradigm == PlanParadigm.HIERARCHICAL
        assert req.search_strategy == "bfs"

        # Verify PlanActionStep automatic id population from step
        step = PlanActionStep(step=3, action="Test Action")
        assert step.id == 3
        assert step.status == "pending"

        # Verify PlanGenerateResponse schema
        resp = PlanGenerateResponse(
            paradigm=PlanParadigm.HIERARCHICAL,
            initial_state=["Init"],
            goal_state=["Goal"],
            actions=[step],
            estimated_duration_minutes=15.0,
            success=True,
        )
        assert resp.success is True
        assert len(resp.actions) == 1

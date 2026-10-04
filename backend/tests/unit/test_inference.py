"""
ResQ-AI Module V: Classical Logical Inference Unit Test Suite.

Verifies:
1. Fact, Predicate, and Working Memory representation with variable unification.
2. The 8 canonical Horn clause rules (R1 - R8) and priority escalation rules.
3. Forward chaining engine (data-driven fixpoint deduction, 2-hop chaining, step tracking).
4. Backward chaining engine (goal-directed AND-OR search, recursive proof tree, cycle detection).
5. Propositional CNF resolution refutation engine (complementary resolution, empty clause □).
6. InferenceEngine façade and backwards compatibility with Agent Orchestrator.
"""

import pytest

from app.inference.facts import Fact, WorkingMemory
from app.inference.rules import (
    ALL_OPERATIONAL_RULES,
    CANONICAL_HORN_RULES,
    HornRule,
    PREDEFINED_RULES,
    R1_LANDSLIDE,
    R2_TRAUMA_CENTER,
    R3_ROAD_IMPASSABLE,
    R4_REROUTE,
    R5_HAZMAT,
    R6_DISPATCH_DELAY,
    R7_REFUEL,
    R8_HOSPITAL_DIVERT,
    R9_CRITICAL_PRIORITY,
    R10_HIGH_PRIORITY,
    R11_AVOID_BLOCKED,
)
from app.inference.forward_chaining import ForwardChainingEngine
from app.inference.backward_chaining import BackwardChainingEngine
from app.inference.resolution import (
    PropositionalResolutionEngine,
    demonstrate_resolution,
    negate_literal,
    parse_clause_string,
    resolve,
)
from app.inference.engine import InferenceEngine
from app.schemas.inference import (
    BackwardChainResponse,
    ForwardChainingStep,
    ForwardChainResponse,
    InferenceResult,
    ResolutionResponse,
)


# ============================================================================
# 1. Fact & Working Memory Unit Tests
# ============================================================================

def test_fact_propositional_creation():
    f = Fact("HeavyRain")
    assert f.name == "HeavyRain"
    assert f.args == ()
    assert f.is_propositional is True
    assert f.is_ground is True
    assert f.variables == set()
    assert str(f) == "HeavyRain"


def test_fact_relational_and_variable_creation():
    f1 = Fact("RoadFlooded", ("N2",))
    assert f1.name == "RoadFlooded"
    assert f1.args == ("N2",)
    assert f1.is_propositional is False
    assert f1.is_ground is True
    assert f1.variables == set()
    assert str(f1) == "RoadFlooded(N2)"

    f2 = Fact("RoadFlooded", ("?r",))
    assert f2.is_ground is False
    assert f2.variables == {"?r"}
    assert str(f2) == "RoadFlooded(?r)"


def test_fact_from_string_parsing():
    f1 = Fact.from_string("HeavyRain")
    assert f1 == Fact("HeavyRain")

    f2 = Fact.from_string("RoadFlooded(N2)")
    assert f2.name == "RoadFlooded"
    assert f2.args == ("N2",)

    f3 = Fact.from_string("Priority('critical')")
    assert f3.name == "Priority"
    assert f3.args == ("critical",)

    f4 = Fact.from_string("Link(N1, N2)")
    assert f4.name == "Link"
    assert f4.args == ("N1", "N2")


def test_fact_equality_and_hashing():
    f1 = Fact("RoadFlooded", ("N2",))
    f2 = Fact.from_string("RoadFlooded(N2)")
    f3 = Fact("RoadFlooded", ("N3",))

    assert f1 == f2
    assert f1 != f3
    assert hash(f1) == hash(f2)
    assert len({f1, f2, f3}) == 2


def test_fact_substitution():
    pattern = Fact("RoadFlooded", ("?r",))
    ground = pattern.substitute({"?r": "N2"})
    assert ground.is_ground is True
    assert ground == Fact("RoadFlooded", ("N2",))

    # Chained substitution
    pattern2 = Fact("Link", ("?x", "?y"))
    sub2 = pattern2.substitute({"?x": "?z", "?z": "N1", "?y": "N2"})
    assert sub2 == Fact("Link", ("N1", "N2"))


def test_fact_unification_positive():
    pattern = Fact("RoadFlooded", ("?r",))
    ground = Fact("RoadFlooded", ("N2",))
    theta = pattern.unify(ground)
    assert theta == {"?r": "N2"}

    prop1 = Fact("HeavyRain")
    prop2 = Fact("HeavyRain")
    assert prop1.unify(prop2) == {}


def test_fact_unification_negative():
    f1 = Fact("RoadFlooded", ("N2",))
    f2 = Fact("RoadImpassable", ("N2",))
    assert f1.unify(f2) is None  # Different predicate

    f3 = Fact("Link", ("N1",))
    f4 = Fact("Link", ("N1", "N2"))
    assert f3.unify(f4) is None  # Arity mismatch

    f5 = Fact("RoadFlooded", ("N2",))
    f6 = Fact("RoadFlooded", ("N4",))
    assert f5.unify(f6) is None  # Conflicting constants


def test_working_memory_operations():
    wm = WorkingMemory(["HeavyRain", "RoadFlooded(N2)"])
    assert len(wm) == 2
    assert wm.contains("HeavyRain") is True
    assert wm.contains(Fact("RoadFlooded", ("N2",))) is True
    assert wm.contains("RoadFlooded(N4)") is False

    # Deduplication
    added = wm.add("HeavyRain")
    assert added is False
    assert len(wm) == 2

    # Removal
    removed = wm.remove("HeavyRain")
    assert removed is True
    assert len(wm) == 1
    assert wm.contains("HeavyRain") is False


def test_working_memory_pattern_matching():
    wm = WorkingMemory(["RoadFlooded(N2)", "RoadFlooded(N4)", "HeavyRain"])
    pattern = Fact("RoadFlooded", ("?r",))
    matches = wm.match(pattern)
    assert len(matches) == 2
    bindings = [m[1]["?r"] for m in matches]
    assert set(bindings) == {"N2", "N4"}


def test_working_memory_from_dict():
    raw = {
        "HeavyRain": True,
        "road_blocked": True,
        "priority": "critical",
        "victim_count": 6,
    }
    wm = WorkingMemory.from_dict(raw)
    assert wm.contains("HeavyRain") is True
    assert wm.contains("RoadBlocked") is True
    assert wm.contains("Priority(critical)") is True


# ============================================================================
# 2. Canonical Horn Clause Rules Unit Tests
# ============================================================================

def test_canonical_eight_rules_structure():
    assert len(CANONICAL_HORN_RULES) == 8
    rule_ids = [r.rule_id for r in CANONICAL_HORN_RULES]
    assert rule_ids == ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"]

    for rule in CANONICAL_HORN_RULES:
        assert isinstance(rule.rule_id, str)
        assert isinstance(rule.name, str)
        assert len(rule.premises) >= 1
        assert isinstance(rule.consequent, Fact)
        assert len(rule.description) > 0


def test_rule_instantiation_and_cnf_conversion():
    r = R1_LANDSLIDE
    instantiated = r.instantiate({"?r": "N2"})
    assert instantiated.consequent == Fact("HighLandslideRisk", ("N2",))
    assert instantiated.premises[1] == Fact("MountainRoad", ("N2",))

    cnf_clause = instantiated.to_cnf_clause()
    assert "~HeavyRain" in cnf_clause
    assert "~MountainRoad(N2)" in cnf_clause
    assert "HighLandslideRisk(N2)" in cnf_clause


# ============================================================================
# 3. Forward Chaining Engine Unit Tests
# ============================================================================

def test_forward_chaining_single_rule_r1_landslide():
    engine = ForwardChainingEngine()
    initial = ["HeavyRain", "MountainRoad(N2)"]
    resp = engine.infer(initial)

    assert resp.success is True
    assert "HighLandslideRisk(N2)" in resp.derived_facts
    assert "R1" in resp.rules_fired
    assert resp.execution_time_ms >= 0.0


def test_forward_chaining_single_rule_r5_hazmat():
    engine = ForwardChainingEngine()
    initial = ["Fire", "ChemicalWarehouse"]
    resp = engine.infer(initial)

    assert resp.success is True
    assert "HazmatProtocol" in resp.derived_facts
    assert "R5" in resp.rules_fired


def test_forward_chaining_single_rule_r6_delay():
    engine = ForwardChainingEngine()
    initial = ["HighTraffic", "RushHour"]
    resp = engine.infer(initial)

    assert resp.success is True
    assert "DispatchDelayLikely" in resp.derived_facts
    assert "R6" in resp.rules_fired


def test_forward_chaining_single_rule_r7_refuel():
    engine = ForwardChainingEngine()
    initial = ["LowFuel(A1)"]
    resp = engine.infer(initial)

    assert resp.success is True
    assert "RefuelRequired(A1)" in resp.derived_facts
    assert "R7" in resp.rules_fired


def test_forward_chaining_single_rule_r8_divert():
    engine = ForwardChainingEngine()
    initial = ["CriticalIncident", "HospitalAtCapacity(H1)"]
    resp = engine.infer(initial)

    assert resp.success is True
    assert "DivertToSecondaryHospital(H1)" in resp.derived_facts
    assert "R8" in resp.rules_fired


def test_forward_chaining_two_hop_cascade_reroute():
    """
    R3: RoadFlooded(?r) => RoadImpassable(?r)
    R4: RoadImpassable(?r) ^ OnDispatchRoute(?r) => RerouteRequired
    """
    engine = ForwardChainingEngine()
    initial = ["RoadFlooded(N2)", "OnDispatchRoute(N2)"]
    resp = engine.infer(initial)

    assert resp.success is True
    assert "RoadImpassable(N2)" in resp.derived_facts
    assert "RerouteRequired" in resp.derived_facts
    assert "R3" in resp.rules_fired
    assert "R4" in resp.rules_fired

    # Verify chronological step ordering
    step_rules = [s.rule_id for s in resp.steps]
    assert step_rules.index("R3") < step_rules.index("R4")


def test_forward_chaining_priority_determination():
    engine = ForwardChainingEngine()
    # R9: SevereInjuries ^ HighSeverity => Priority(critical)
    initial = ["SevereInjuries", "HighSeverity"]
    resp = engine.infer(initial)

    assert resp.success is True
    assert "Priority(critical)" in resp.derived_facts
    assert resp.inferred_priority == "critical"

    # R2 + R10: SevereInjuries => TraumaCenterRequired => Priority(high)
    resp2 = engine.infer(["SevereInjuries"])
    assert "TraumaCenterRequired" in resp2.derived_facts
    assert resp2.inferred_priority == "high"


def test_forward_chaining_idempotency_and_fixpoint():
    engine = ForwardChainingEngine()
    initial = ["HeavyRain", "MountainRoad(N2)"]
    resp1 = engine.infer(initial)
    assert len(resp1.derived_facts) == 1

    # Running with derived fact already present should derive nothing new
    resp2 = engine.infer(initial + resp1.derived_facts)
    assert len(resp2.derived_facts) == 0
    assert len(resp2.rules_fired) == 0


def test_forward_chaining_step_schema_compliance():
    engine = ForwardChainingEngine()
    resp = engine.infer(["RoadFlooded(N2)", "OnDispatchRoute(N2)"])

    assert len(resp.steps) >= 2
    for s in resp.steps:
        assert isinstance(s, ForwardChainingStep)
        assert s.step_number > 0
        assert s.rule_id in ["R3", "R4"]
        assert len(s.premises_satisfied) > 0
        assert isinstance(s.deduced_fact, str)
        assert s.working_memory_size > 0


# ============================================================================
# 4. Backward Chaining Engine Unit Tests
# ============================================================================

def test_backward_chaining_leaf_fact():
    engine = BackwardChainingEngine()
    resp = engine.prove("HeavyRain", ["HeavyRain", "MountainRoad(N2)"])

    assert resp.proved is True
    assert resp.goal == "HeavyRain"
    assert resp.proof_tree["status"] == "PROVED_FACT"
    assert resp.proof_tree["children"] == []


def test_backward_chaining_single_rule_proof_tree():
    engine = BackwardChainingEngine()
    resp = engine.prove("HighLandslideRisk(N2)", ["HeavyRain", "MountainRoad(N2)"])

    assert resp.proved is True
    assert resp.proof_tree["status"] == "PROVED_RULE"
    assert resp.proof_tree["rule_id"] == "R1"
    assert resp.proof_tree["bindings"]["?r"] == "N2"
    assert len(resp.proof_tree["children"]) == 2
    assert resp.proof_tree["children"][0]["status"] == "PROVED_FACT"
    assert resp.proof_tree["children"][1]["status"] == "PROVED_FACT"


def test_backward_chaining_two_hop_proof_tree():
    engine = BackwardChainingEngine()
    initial = ["RoadFlooded(N2)", "OnDispatchRoute(N2)"]
    resp = engine.prove("RerouteRequired", initial)

    assert resp.proved is True
    tree = resp.proof_tree
    assert tree["status"] == "PROVED_RULE"
    assert tree["rule_id"] == "R4"

    # Premise 0 of R4: RoadImpassable(N2) proved via R3
    child_r3 = tree["children"][0]
    assert child_r3["status"] == "PROVED_RULE"
    assert child_r3["rule_id"] == "R3"
    assert child_r3["children"][0]["status"] == "PROVED_FACT"
    assert child_r3["children"][0]["goal"] == "RoadFlooded(N2)"

    # Premise 1 of R4: OnDispatchRoute(N2) proved directly as base fact
    child_fact = tree["children"][1]
    assert child_fact["status"] == "PROVED_FACT"
    assert child_fact["goal"] == "OnDispatchRoute(N2)"


def test_backward_chaining_unprovable_goal():
    engine = BackwardChainingEngine()
    # Missing MountainRoad(N2)
    resp = engine.prove("HighLandslideRisk(N2)", ["HeavyRain"])

    assert resp.proved is False
    assert resp.proof_tree["status"] == "FAILED_NO_PROOF"


def test_backward_chaining_cycle_detection():
    # Construct cyclic rules: A => B, B => A
    rule_a_to_b = HornRule(
        rule_id="CYCLE_1",
        name="Cycle 1",
        premises=[Fact("A")],
        consequent=Fact("B"),
    )
    rule_b_to_a = HornRule(
        rule_id="CYCLE_2",
        name="Cycle 2",
        premises=[Fact("B")],
        consequent=Fact("A"),
    )
    engine = BackwardChainingEngine([rule_a_to_b, rule_b_to_a])

    # Goal A with empty knowledge base
    resp = engine.prove("A", [])
    assert resp.proved is False
    # Cycle detection must prevent recursion overflow
    assert any("Cycle detected" in step for step in resp.steps)


# ============================================================================
# 5. Propositional CNF Resolution Refutation Unit Tests
# ============================================================================

def test_resolution_refutation_modus_ponens():
    """
    KB: P, P => Q  (CNF: P, ~P | Q)
    Prove: Q
    Refutation: add ~Q.
    Resolve (~P | Q) and (~Q) on Q -> ~P
    Resolve (~P) and (P) on P -> empty clause □!
    """
    engine = PropositionalResolutionEngine([])
    clauses = ["P", "~P | Q"]
    resp = engine.resolve(goal="Q", clauses=clauses)

    assert resp.refutation_successful is True
    assert resp.contradiction_found is True
    assert any("□" in step for step in resp.steps)


def test_resolution_refutation_emergency_hazmat():
    """
    KB: Fire, ChemicalWarehouse, ~Fire | ~ChemicalWarehouse | HazmatProtocol
    Goal: HazmatProtocol
    """
    engine = PropositionalResolutionEngine([])
    clauses = ["Fire", "ChemicalWarehouse", "~Fire | ~ChemicalWarehouse | HazmatProtocol"]
    resp = engine.resolve(goal="HazmatProtocol", clauses=clauses)

    assert resp.refutation_successful is True
    assert resp.contradiction_found is True


def test_resolution_refutation_landslide():
    engine = PropositionalResolutionEngine([])
    clauses = ["HeavyRain", "MountainRoad_N2", "~HeavyRain | ~MountainRoad_N2 | HighLandslideRisk_N2"]
    resp = engine.resolve(goal="HighLandslideRisk_N2", clauses=clauses)

    assert resp.refutation_successful is True
    assert resp.contradiction_found is True


def test_resolution_unentailed_goal_fails_cleanly():
    """
    KB: Fire (missing ChemicalWarehouse)
    Goal: HazmatProtocol
    Cannot derive empty clause □.
    """
    engine = PropositionalResolutionEngine([])
    clauses = ["Fire", "~Fire | ~ChemicalWarehouse | HazmatProtocol"]
    resp = engine.resolve(goal="HazmatProtocol", clauses=clauses)

    assert resp.refutation_successful is False
    assert resp.contradiction_found is False
    assert any("Fixpoint reached" in step for step in resp.steps)


def test_resolution_helpers_and_legacy_compatibility():
    # Helper negation
    assert negate_literal("P") == "~P"
    assert negate_literal("~P") == "P"
    assert negate_literal("not P") == "P"
    assert negate_literal("!P") == "P"

    # Single-step resolution function
    res = resolve(["A", "B"], ["~B", "C"])
    assert res == ["A", "C"]

    # Legacy demo
    demo = demonstrate_resolution()
    assert demo["resolvent"] == ["A", "C"]


# ============================================================================
# 6. Unified InferenceEngine Façade Unit Tests
# ============================================================================

def test_inference_engine_legacy_dict_forward():
    raw_facts = {
        "victim_count": 6,
        "severity": "high",
        "road_blocked": True,
    }
    engine = InferenceEngine(raw_facts, PREDEFINED_RULES)
    result = engine.forward_chain()

    assert result["facts"]["priority"] == "critical"
    assert result["facts"]["avoid_blocked_routes"] is True
    assert any("priority = 'critical'" in log for log in result["logs"])


def test_inference_engine_legacy_dict_backward():
    raw_facts = {
        "victim_count": 6,
        "severity": "high",
    }
    engine = InferenceEngine(raw_facts, PREDEFINED_RULES)
    result = engine.backward_chain("priority")

    assert result["proved"] is True
    assert result["value"] == "critical"


def test_inference_engine_hybrid_horn_rules():
    facts = ["RoadFlooded(N2)", "OnDispatchRoute(N2)"]
    engine = InferenceEngine(facts)
    result = engine.forward_chain()

    assert "RoadImpassable(N2)" in result["inferred"]
    assert "RerouteRequired" in result["inferred"]


def test_inference_engine_run_resolution():
    engine = InferenceEngine()
    clauses = ["SevereInjuries", "~SevereInjuries | TraumaCenterRequired"]
    resp = engine.run_resolution(goal="TraumaCenterRequired", clauses=clauses)

    assert resp.refutation_successful is True
    assert resp.contradiction_found is True


def test_inference_result_schema_contract():
    res = InferenceResult(
        engine="forward",
        derived_facts=["RoadImpassable(N2)", "RerouteRequired"],
        rule_firings=[{"rule_id": "R3"}, {"rule_id": "R4"}],
        steps=["Step 1", "Step 2"],
    )
    assert res.engine == "forward"
    assert len(res.derived_facts) == 2

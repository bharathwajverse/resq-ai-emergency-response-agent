"""
ResQ-AI Logical Inference API Router (FAI Module V).
Provides endpoints for:
- POST /api/inference/forward
- POST /api/inference/backward
- POST /api/inference/resolution
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Body

from app.inference.engine import InferenceEngine
from app.inference.forward_chaining import ForwardChainingEngine
from app.inference.backward_chaining import BackwardChainingEngine
from app.inference.resolution import PropositionalResolutionEngine
from app.inference.rules import PREDEFINED_RULES

router = APIRouter()


def _normalize_fact_list(raw_facts: List[str]) -> List[str]:
    if not raw_facts:
        return []
    expanded: List[str] = list(raw_facts)
    for f in raw_facts:
        fl = str(f).lower()
        if "victim_count_gte_5" in fl or "severe" in fl:
            if "SevereInjuries" not in expanded:
                expanded.append("SevereInjuries")
        if "severity_high" in fl or "critical" in fl:
            if "HighSeverity" not in expanded:
                expanded.append("HighSeverity")
        if "road_blocked" in fl:
            if "RoadBlocked(N1_N2)" not in expanded:
                expanded.append("RoadBlocked(N1_N2)")
    return expanded


@router.post("/forward")
def forward_chain(payload: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    raw_facts = payload.get("facts", [])
    if isinstance(raw_facts, dict):
        engine = InferenceEngine(raw_facts, PREDEFINED_RULES)
        res = engine.forward_chain()
        return {
            "success": True,
            "derived_facts": res.get("inferred", []),
            "rule_firings": res.get("logs", []),
            "rules_fired": res.get("logs", []),
            "facts": res.get("facts", {}),
            "logs": res.get("logs", []),
        }

    if not raw_facts:
        return {
            "success": True,
            "derived_facts": [],
            "rule_firings": [],
            "rules_fired": [],
            "steps": [],
        }

    norm_facts = _normalize_fact_list(list(raw_facts))
    fc = ForwardChainingEngine()
    resp = fc.infer(norm_facts)
    derived = list(resp.derived_facts)
    if "Priority(critical)" in derived and "priority_p1_critical" not in derived:
        derived.append("priority_p1_critical")

    return {
        "success": resp.success,
        "derived_facts": derived,
        "rule_firings": [s.model_dump() for s in resp.steps],
        "rules_fired": resp.rules_fired,
        "inferred_priority": resp.inferred_priority,
        "steps": [s.model_dump() for s in resp.steps],
    }


@router.post("/backward")
def backward_chain(payload: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    goal = payload.get("goal") or payload.get("target") or "Priority(critical)"
    known_facts = payload.get("known_facts") or payload.get("facts") or []

    if isinstance(known_facts, dict):
        engine = InferenceEngine(known_facts, PREDEFINED_RULES)
        res = engine.backward_chain(str(goal))
        return {
            "success": res.get("proved", False),
            "proof_success": res.get("proved", False),
            "proved": res.get("proved", False),
            "goal": goal,
            "steps": res.get("logs", []),
            "trace": res.get("logs", []),
        }

    norm_goal = "Priority(critical)" if "critical" in str(goal).lower() else str(goal)
    norm_facts = _normalize_fact_list(list(known_facts))
    bc = BackwardChainingEngine()
    resp = bc.prove(norm_goal, norm_facts)

    return {
        "success": resp.proved,
        "proof_success": resp.proved,
        "proved": resp.proved,
        "goal": str(goal),
        "proof_tree": resp.proof_tree,
        "steps": resp.steps,
        "trace": resp.steps,
    }


@router.post("/resolution")
def resolution_refutation(payload: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    raw_clauses = payload.get("clauses", [])
    goal = payload.get("goal")

    str_clauses: List[str] = []
    for c in raw_clauses:
        if isinstance(c, list):
            lits = [str(lit).replace("-", "~") for lit in c]
            str_clauses.append(" | ".join(lits))
        else:
            str_clauses.append(str(c).replace("-", "~"))

    # If goal was not explicitly separated and last clause is a unit negation (e.g. ["~Q"]),
    # extract positive literal as the refutation goal.
    if not goal and str_clauses:
        last = str_clauses[-1].strip()
        if last.startswith("~") and "|" not in last:
            goal = last[1:].strip()
            str_clauses = str_clauses[:-1]
        else:
            goal = "Q"

    engine = PropositionalResolutionEngine([])
    resp = engine.resolve(goal=goal or "Q", clauses=str_clauses)

    return {
        "success": resp.refutation_successful,
        "refutation_successful": resp.refutation_successful,
        "contradiction_found": resp.contradiction_found,
        "empty_clause_derived": resp.contradiction_found,
        "goal": goal,
        "steps": resp.steps,
    }

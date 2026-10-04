"""
ResQ-AI Forward Chaining Inference Engine.
Module V: Classical Logical Inference.

Implements data-driven, bottom-up deduction with multi-premise unification,
monotonic fixpoint calculation, and detailed step explanation logging.
"""

from __future__ import annotations
import time
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Union

from app.inference.facts import Fact, WorkingMemory
from app.inference.rules import ALL_OPERATIONAL_RULES, CANONICAL_HORN_RULES, HornRule
from app.schemas.inference import ForwardChainingStep, ForwardChainResponse


class ForwardChainingEngine:
    """
    Data-driven forward chaining inference engine.
    Derives all logically entailed ground facts from initial facts and Horn rules.
    """

    def __init__(self, rules: Optional[List[HornRule]] = None):
        self.rules: List[HornRule] = list(rules) if rules is not None else list(ALL_OPERATIONAL_RULES)

    def _find_satisfying_bindings(
        self, premises: List[Fact], working_memory: WorkingMemory
    ) -> List[Dict[str, str]]:
        """
        Backtracking search to find all variable substitutions satisfying
        the conjunction of rule premises against the current working memory.
        """
        results: List[Dict[str, str]] = []
        seen_binding_keys: Set[Tuple[Tuple[str, str], ...]] = set()

        def _backtrack(premise_idx: int, current_bindings: Dict[str, str]):
            if premise_idx == len(premises):
                key = tuple(sorted(current_bindings.items()))
                if key not in seen_binding_keys:
                    seen_binding_keys.add(key)
                    results.append(dict(current_bindings))
                return

            premise = premises[premise_idx].substitute(current_bindings)
            for fact in working_memory.facts:
                theta = premise.unify(fact, current_bindings)
                if theta is not None:
                    _backtrack(premise_idx + 1, theta)

        _backtrack(0, {})
        return results

    def infer(
        self,
        initial_facts: Optional[Union[List[str], WorkingMemory, Dict[str, Any]]] = None,
        incident_id: Optional[str] = None,
        max_iterations: int = 100,
    ) -> ForwardChainResponse:
        """
        Executes forward chaining until a fixed point is reached or max_iterations is exceeded.
        """
        start_time = time.perf_counter()

        # Initialize working memory
        if initial_facts is None:
            wm = WorkingMemory()
        elif isinstance(initial_facts, WorkingMemory):
            wm = initial_facts.copy()
        elif isinstance(initial_facts, dict):
            wm = WorkingMemory.from_dict(initial_facts)
        else:
            wm = WorkingMemory.from_iterable(initial_facts)

        initial_facts_list = wm.all_facts()
        derived_facts: List[str] = []
        rules_fired: List[str] = []
        steps: List[ForwardChainingStep] = []
        step_number = 1

        # Iterative fixpoint cycle
        iteration = 0
        changed = True

        while changed and iteration < max_iterations:
            iteration += 1
            changed = False

            for rule in self.rules:
                matching_bindings = self._find_satisfying_bindings(rule.premises, wm)
                for bindings in matching_bindings:
                    ground_consequent = rule.consequent.substitute(bindings)
                    if not ground_consequent.is_ground:
                        continue

                    # If this fact is novel, assert into working memory
                    if not wm.contains(ground_consequent):
                        wm.add(ground_consequent)
                        consequent_str = str(ground_consequent)
                        derived_facts.append(consequent_str)
                        if rule.rule_id not in rules_fired:
                            rules_fired.append(rule.rule_id)

                        # Record explanation step
                        satisfied_premises = [
                            str(p.substitute(bindings)) for p in rule.premises
                        ]
                        steps.append(
                            ForwardChainingStep(
                                step_number=step_number,
                                rule_id=rule.rule_id,
                                premises_satisfied=satisfied_premises,
                                bindings=bindings,
                                deduced_fact=consequent_str,
                                working_memory_size=len(wm),
                            )
                        )
                        step_number += 1
                        changed = True

        # Compute inferred priority
        inferred_priority = self._determine_priority(wm)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return ForwardChainResponse(
            success=True,
            initial_facts=initial_facts_list,
            derived_facts=derived_facts,
            rules_fired=rules_fired,
            steps=steps,
            inferred_priority=inferred_priority,
            execution_time_ms=round(elapsed_ms, 3),
        )

    def _determine_priority(self, wm: WorkingMemory) -> Optional[str]:
        """Infers the incident priority label from working memory state."""
        # 1. Direct Priority facts
        for fact in wm.facts:
            if fact.name == "Priority" and fact.args:
                val = fact.args[0].lower()
                if "critical" in val:
                    return "critical"
            if str(fact).lower() == "priority=critical":
                return "critical"

        for fact in wm.facts:
            if fact.name == "Priority" and fact.args:
                val = fact.args[0].lower()
                if "high" in val:
                    return "high"
            if str(fact).lower() == "priority=high":
                return "high"

        # 2. Key trigger facts
        if wm.contains("TraumaCenterRequired"):
            return "high"
        for fact in wm.facts:
            if fact.name == "HighLandslideRisk" or fact.name == "HazmatProtocol":
                return "high"

        for fact in wm.facts:
            if fact.name == "Priority" and fact.args:
                val = fact.args[0].lower()
                if "medium" in val:
                    return "medium"

        return None

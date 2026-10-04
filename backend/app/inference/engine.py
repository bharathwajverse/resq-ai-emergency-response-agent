"""
ResQ-AI Inference Engine Façade.
Module V: Classical Logical Inference.

Provides a unified interface combining Forward Chaining, Backward Chaining,
and Resolution Refutation, while preserving backwards compatibility with
the AI Agent Orchestrator and existing REST endpoints.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Union

from app.inference.facts import Fact, WorkingMemory
from app.inference.rules import (
    ALL_OPERATIONAL_RULES,
    CANONICAL_HORN_RULES,
    HornRule,
    PREDEFINED_RULES,
    Rule,
)
from app.inference.forward_chaining import ForwardChainingEngine
from app.inference.backward_chaining import BackwardChainingEngine
from app.inference.resolution import PropositionalResolutionEngine
from app.schemas.inference import (
    BackwardChainResponse,
    ForwardChainResponse,
    ResolutionResponse,
)


class InferenceEngine:
    """
    Unified Inference Engine façade.
    Supports both legacy dict-based evaluation for Orchestrator compatibility
    and classical First-Order / Horn clause forward/backward chaining.
    """

    def __init__(
        self,
        facts: Optional[Union[Dict[str, Any], List[str], WorkingMemory]] = None,
        rules: Optional[List[Any]] = None,
    ):
        # Working state
        self.raw_facts: Dict[str, Any] = {}
        if isinstance(facts, dict):
            self.raw_facts = facts.copy()
            self.working_memory = WorkingMemory.from_dict(facts)
        elif isinstance(facts, WorkingMemory):
            self.working_memory = facts.copy()
            self.raw_facts = {str(f): True for f in self.working_memory.facts}
        elif isinstance(facts, list):
            self.working_memory = WorkingMemory.from_iterable(facts)
            self.raw_facts = {str(f): True for f in self.working_memory.facts}
        else:
            self.working_memory = WorkingMemory()
            self.raw_facts = {}

        self.facts = self.raw_facts.copy()
        self.rules = rules if rules is not None else PREDEFINED_RULES
        self.logs: List[str] = []

        # Classical engines
        horn_rules = [r for r in self.rules if isinstance(r, HornRule)]
        if not horn_rules:
            horn_rules = list(ALL_OPERATIONAL_RULES)
        self.forward_engine = ForwardChainingEngine(horn_rules)
        self.backward_engine = BackwardChainingEngine(horn_rules)
        self.resolution_engine = PropositionalResolutionEngine(horn_rules)

    def _eval_condition(self, condition_str: str) -> bool:
        """Safely evaluates legacy rule condition string against dict facts."""
        local_vars = self.facts.copy()
        try:
            cond = condition_str.replace("true", "True").replace("false", "False")
            cond = cond.replace(" AND ", " and ").replace(" OR ", " or ")
            return bool(eval(cond, {}, local_vars))
        except Exception:
            return False

    def forward_chain(self) -> Dict[str, Any]:
        """
        Executes forward chaining.
        Maintains backward compatibility with Agent Orchestrator:
        returns dict with 'facts', 'logs', 'inferred', and 'response'.
        """
        changed = True
        inferred: List[str] = []

        # 1. Legacy rule evaluation for string condition/action rules
        while changed:
            changed = False
            for rule in self.rules:
                if isinstance(rule, Rule) or hasattr(rule, "condition"):
                    if self._eval_condition(rule.condition):
                        if "=" in rule.action:
                            var, val = [x.strip() for x in rule.action.split("=", 1)]
                            val_clean = val.strip("'\"")
                            if val_clean.isdigit():
                                parsed_val = int(val_clean)
                            elif val_clean.lower() == "true":
                                parsed_val = True
                            elif val_clean.lower() == "false":
                                parsed_val = False
                            else:
                                parsed_val = val_clean

                            if var not in self.facts or self.facts[var] != parsed_val:
                                self.facts[var] = parsed_val
                                inferred.append(f"{var}={parsed_val}")
                                self.logs.append(f"Fired: IF {rule.condition} THEN {rule.action}")
                                changed = True
                                # Sync into working memory
                                self.working_memory.add(f"{var}={parsed_val}")

        # 2. Modern First-Order / Horn clause forward chaining
        resp = self.forward_engine.infer(self.working_memory)
        for derived in resp.derived_facts:
            if derived not in inferred:
                inferred.append(derived)
                self.facts[derived] = True
        for step in resp.steps:
            self.logs.append(
                f"Fired {step.rule_id}: {step.premises_satisfied} => {step.deduced_fact}"
            )
        if resp.inferred_priority:
            self.facts["priority"] = resp.inferred_priority

        return {
            "facts": self.facts,
            "logs": self.logs,
            "inferred": inferred,
            "response": resp,
        }

    def backward_chain(self, goal_var: str) -> Dict[str, Any]:
        """
        Executes backward chaining to prove goal_var.
        Maintains backward compatibility with Agent Orchestrator:
        returns dict with 'goal', 'proved', 'value', 'logs', and 'proof_tree'.
        """
        # 1. Check legacy dict variables
        if goal_var in self.facts:
            return {
                "goal": goal_var,
                "proved": True,
                "value": self.facts.get(goal_var),
                "logs": self.logs + [f"Direct fact proved: {goal_var}"],
                "proof_tree": {"goal": goal_var, "status": "PROVED_FACT", "children": []},
            }

        # 2. Check legacy rules (Rule with condition/action)
        visited = set()

        def _prove_legacy(var: str) -> bool:
            if var in self.facts:
                return True
            if var in visited:
                return False
            visited.add(var)
            for rule in self.rules:
                if isinstance(rule, Rule) or hasattr(rule, "condition"):
                    if "=" in rule.action:
                        r_var, r_val = [x.strip() for x in rule.action.split("=", 1)]
                        if r_var == var:
                            self.logs.append(
                                f"Trying to prove {var} via rule: IF {rule.condition} THEN {rule.action}"
                            )
                            if self._eval_condition(rule.condition):
                                val_clean = r_val.strip("'\"")
                                if val_clean.isdigit():
                                    parsed = int(val_clean)
                                elif val_clean.lower() == "true":
                                    parsed = True
                                elif val_clean.lower() == "false":
                                    parsed = False
                                else:
                                    parsed = val_clean
                                self.facts[var] = parsed
                                self.logs.append(f"Proved {var} = {parsed}")
                                return True
            return False

        if _prove_legacy(goal_var):
            return {
                "goal": goal_var,
                "proved": True,
                "value": self.facts.get(goal_var),
                "logs": self.logs,
                "proof_tree": {
                    "goal": goal_var,
                    "status": "PROVED_RULE",
                    "value": self.facts.get(goal_var),
                    "children": [],
                },
            }

        # 3. Try modern recursive backward chaining engine
        resp = self.backward_engine.prove(goal_var, self.working_memory)
        self.logs.extend(resp.steps)

        return {
            "goal": goal_var,
            "proved": resp.proved,
            "value": self.facts.get(goal_var, resp.proved),
            "logs": self.logs,
            "proof_tree": resp.proof_tree,
        }

    def run_resolution(
        self,
        goal: str,
        clauses: Optional[List[str]] = None,
        initial_facts: Optional[List[str]] = None,
    ) -> ResolutionResponse:
        """Executes propositional resolution refutation."""
        facts_list = initial_facts or self.working_memory.all_facts()
        return self.resolution_engine.resolve(
            goal=goal, clauses=clauses, initial_facts=facts_list
        )
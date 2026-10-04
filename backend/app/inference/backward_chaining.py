"""
ResQ-AI Backward Chaining Inference Engine.
Module V: Classical Logical Inference.

Implements goal-directed, top-down reasoning with recursive AND-OR tree search,
variable unifications, cycle detection, and structured proof tree generation.
"""

from __future__ import annotations
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from app.inference.facts import Fact, WorkingMemory
from app.inference.rules import ALL_OPERATIONAL_RULES, HornRule
from app.schemas.inference import BackwardChainResponse


class BackwardChainingEngine:
    """
    Goal-driven backward chaining engine.
    Constructs proof trees demonstrating logical entailment of a target hypothesis.
    """

    def __init__(self, rules: Optional[List[HornRule]] = None):
        self.rules: List[HornRule] = list(rules) if rules is not None else list(ALL_OPERATIONAL_RULES)

    def prove(
        self,
        goal: Union[str, Fact],
        initial_facts: Optional[Union[List[str], WorkingMemory, Dict[str, Any]]] = None,
    ) -> BackwardChainResponse:
        """
        Attempts to prove target goal from initial facts using recursive AND-OR search.
        """
        start_time = time.perf_counter()

        goal_fact = goal if isinstance(goal, Fact) else Fact.from_string(goal)

        # Initialize working memory
        if initial_facts is None:
            wm = WorkingMemory()
        elif isinstance(initial_facts, WorkingMemory):
            wm = initial_facts.copy()
        elif isinstance(initial_facts, dict):
            wm = WorkingMemory.from_dict(initial_facts)
        else:
            wm = WorkingMemory.from_iterable(initial_facts)

        steps: List[str] = []

        def _prove_subgoal(
            current_goal: Fact,
            call_stack: Set[str],
            current_bindings: Dict[str, str],
        ) -> Tuple[bool, Dict[str, Any], Dict[str, str]]:
            instantiated_goal = current_goal.substitute(current_bindings)
            goal_key = str(instantiated_goal)

            # Cycle detection
            if goal_key in call_stack:
                steps.append(f"Cycle detected for '{goal_key}'; pruning branch.")
                return (
                    False,
                    {
                        "goal": goal_key,
                        "status": "FAILED_CYCLE_DETECTED",
                        "children": [],
                    },
                    current_bindings,
                )

            # 1. Check direct fact in working memory (Base Case)
            for fact in wm.facts:
                theta = instantiated_goal.unify(fact, current_bindings)
                if theta is not None:
                    steps.append(f"Leaf fact matched: '{fact}' satisfies '{instantiated_goal}'.")
                    return (
                        True,
                        {
                            "goal": str(fact),
                            "status": "PROVED_FACT",
                            "children": [],
                        },
                        theta,
                    )

            # 2. Search rules whose consequent unifies with goal (OR-branch)
            new_stack = call_stack | {goal_key}

            for rule in self.rules:
                rule_theta = instantiated_goal.unify(rule.consequent, current_bindings)
                if rule_theta is None:
                    continue

                steps.append(
                    f"Testing Rule {rule.rule_id} [{rule.name}] to prove '{instantiated_goal}'."
                )

                # Prove all premises of the rule (AND-branch)
                all_premises_proved = True
                child_trees: List[Dict[str, Any]] = []
                running_bindings = dict(rule_theta)

                for premise in rule.premises:
                    sub_premise = premise.substitute(running_bindings)
                    premise_proved, premise_tree, updated_bindings = _prove_subgoal(
                        sub_premise, new_stack, running_bindings
                    )
                    child_trees.append(premise_tree)

                    if not premise_proved:
                        steps.append(
                            f"Premise '{sub_premise}' for Rule {rule.rule_id} could not be proved."
                        )
                        all_premises_proved = False
                        break

                    running_bindings.update(updated_bindings)

                if all_premises_proved:
                    ground_goal_str = str(current_goal.substitute(running_bindings))
                    steps.append(
                        f"Rule {rule.rule_id} [{rule.name}] proved: derived '{ground_goal_str}'."
                    )
                    proof_tree_node = {
                        "goal": ground_goal_str,
                        "status": "PROVED_RULE",
                        "rule_id": rule.rule_id,
                        "bindings": running_bindings,
                        "children": child_trees,
                    }
                    return True, proof_tree_node, running_bindings

            # Goal cannot be proved
            steps.append(f"Failed to prove goal '{instantiated_goal}': no applicable rules or facts.")
            return (
                False,
                {
                    "goal": goal_key,
                    "status": "FAILED_NO_PROOF",
                    "children": [],
                },
                current_bindings,
            )

        proved, proof_tree, _ = _prove_subgoal(goal_fact, set(), {})

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return BackwardChainResponse(
            goal=str(goal),
            proved=proved,
            proof_tree=proof_tree if proved else proof_tree,
            steps=steps,
            execution_time_ms=round(elapsed_ms, 3),
        )

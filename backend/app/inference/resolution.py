"""
ResQ-AI Propositional CNF Resolution Refutation Engine.
Module V: Classical Logical Inference.

Implements clause normalization, complementary literal resolution,
iterative clause derivation, and contradiction detection (empty clause □).
"""

from __future__ import annotations
import itertools
import re
import time
from typing import Any, Dict, FrozenSet, Iterable, List, Optional, Set, Tuple, Union

from app.inference.facts import Fact
from app.inference.rules import CANONICAL_HORN_RULES, HornRule
from app.schemas.inference import ResolutionResponse


def negate_literal(literal: str) -> str:
    """Returns the negated literal string."""
    clean = literal.strip()
    if clean.startswith("~"):
        return clean[1:]
    if clean.startswith("not "):
        return clean[4:].strip()
    if clean.startswith("!"):
        return clean[1:].strip()
    return f"~{clean}"


def is_tautology(clause: FrozenSet[str]) -> bool:
    """Returns True if clause contains both a literal and its negation."""
    for lit in clause:
        if negate_literal(lit) in clause:
            return True
    return False


def format_clause(clause: FrozenSet[str]) -> str:
    """Formats a clause frozenset into readable mathematical/logical string."""
    if not clause:
        return "□ (Empty Clause)"
    return "{" + ", ".join(sorted(clause)) + "}"


def parse_clause_string(clause_str: str) -> FrozenSet[str]:
    """
    Parses a string representing a disjunction of literals into a FrozenSet[str].
    Supports delimiters '|', 'OR', 'or', and ','.
    
    Examples:
        "~P | Q" -> frozenset({"~P", "Q"})
        "A, B" -> frozenset({"A", "B"})
        "RoadFlooded" -> frozenset({"RoadFlooded"})
    """
    clean = clause_str.strip().strip("{}[]()")
    if not clean:
        return frozenset()
    
    # Split by | or OR or comma
    tokens = re.split(r"\s*\|\s*|\s+OR\s+|\s+or\s+|\s*,\s*", clean)
    literals = set()
    for t in tokens:
        t_clean = t.strip()
        if t_clean:
            literals.add(t_clean)
    return frozenset(literals)


def resolve(clause1: Iterable[str], clause2: Iterable[str]) -> Optional[List[str]]:
    """
    Single-step resolution on first complementary literal pair found.
    Retained for backward compatibility with legacy demonstration code.
    """
    c1 = set(clause1)
    c2 = set(clause2)
    for lit in c1:
        neg = negate_literal(lit)
        if neg in c2:
            resolvent = (c1 - {lit}) | (c2 - {neg})
            return sorted(list(resolvent))
    return None


def demonstrate_resolution() -> Dict[str, Any]:
    """
    Educational demonstration of a single resolution step.
    Retained for backward compatibility.
    """
    c1 = ["A", "B"]
    c2 = ["~B", "C"]
    res = resolve(c1, c2)
    return {"clause1": c1, "clause2": c2, "resolvent": res}


class PropositionalResolutionEngine:
    """
    Classical Propositional Resolution Refutation Engine.
    To verify KB |= Goal, asserts KB union {~Goal} and attempts to derive the empty clause □.
    """

    def __init__(self, rules: Optional[List[HornRule]] = None):
        self.rules: List[HornRule] = list(rules) if rules is not None else list(CANONICAL_HORN_RULES)

    def resolve(
        self,
        goal: str,
        clauses: Optional[List[str]] = None,
        initial_facts: Optional[List[str]] = None,
        max_steps: int = 150,
    ) -> ResolutionResponse:
        """
        Executes resolution refutation to determine if KB |= goal.
        """
        start_time = time.perf_counter()
        steps: List[str] = []

        # 1. Build initial clause set in CNF
        clause_set: Set[FrozenSet[str]] = set()

        # Add explicit clauses if provided
        if clauses:
            for c in clauses:
                parsed = parse_clause_string(c)
                if parsed and not is_tautology(parsed):
                    clause_set.add(parsed)

        # Convert initial facts to unit clauses
        if initial_facts:
            for f in initial_facts:
                f_clean = f.strip()
                if f_clean:
                    clause_set.add(frozenset({f_clean}))

        # If no explicit clauses or facts provided, translate relevant Horn rules
        if not clauses:
            for rule in self.rules:
                cnf_clause = frozenset(rule.to_cnf_clause())
                if not is_tautology(cnf_clause):
                    clause_set.add(cnf_clause)

        # 2. Add negated goal to clause set (Refutation Hypothesis)
        neg_goal = negate_literal(goal.strip())
        neg_goal_clause = frozenset({neg_goal})
        clause_set.add(neg_goal_clause)

        steps.append(f"Hypothesis asserted for refutation: Negated goal '{neg_goal}' added as {format_clause(neg_goal_clause)}")
        steps.append(f"Initial clause set ({len(clause_set)} clauses): {', '.join(format_clause(c) for c in sorted(clause_set, key=lambda x: (len(x), sorted(x))))}")

        # 3. Iterative Resolution Loop
        step_count = 0
        contradiction_found = False

        while step_count < max_steps:
            new_clauses: Set[FrozenSet[str]] = set()
            found_empty_in_cycle = False

            # Generate pairs of clauses
            sorted_clauses = sorted(clause_set, key=lambda c: (len(c), sorted(c)))
            for c1, c2 in itertools.combinations(sorted_clauses, 2):
                # Search for complementary literal
                for lit in c1:
                    neg_lit = negate_literal(lit)
                    if neg_lit in c2:
                        resolvent = frozenset((c1 - {lit}) | (c2 - {neg_lit}))

                        # Tautology elimination
                        if is_tautology(resolvent):
                            continue

                        step_count += 1
                        steps.append(
                            f"Step {step_count}: Resolved {format_clause(c1)} and {format_clause(c2)} on literal '{lit}' -> {format_clause(resolvent)}"
                        )

                        # Empty clause derived: Contradiction found!
                        if len(resolvent) == 0:
                            contradiction_found = True
                            found_empty_in_cycle = True
                            steps.append(
                                f"Contradiction found! Derived empty clause □ at step {step_count}. "
                                f"KB logically entails goal '{goal}' by refutation."
                            )
                            break

                        if resolvent not in clause_set:
                            new_clauses.add(resolvent)

                if found_empty_in_cycle:
                    break

            if contradiction_found:
                break

            # If no new non-tautological, non-redundant clauses were derived, we have reached fixpoint
            if not new_clauses or new_clauses.issubset(clause_set):
                steps.append(
                    f"Fixpoint reached after {step_count} resolution steps with no new clauses. "
                    f"Contradiction cannot be derived. Goal '{goal}' is NOT entailed by KB."
                )
                break

            clause_set.update(new_clauses)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return ResolutionResponse(
            goal=goal,
            refutation_successful=contradiction_found,
            steps=steps,
            contradiction_found=contradiction_found,
            execution_time_ms=round(elapsed_ms, 3),
        )

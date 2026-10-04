"""
ResQ-AI Facts and Working Memory Representation.
Module V: Classical Logical Inference.

Implements First-Order Logic (FOL) inspired facts, propositional atoms,
variable substitution, Robinson unification, and working memory storage.
"""

from __future__ import annotations
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple, Union


class Fact:
    """
    Represents a logical ground fact or pattern atom.
    
    Examples:
        - Propositional: Fact("HeavyRain") or Fact.from_string("HeavyRain")
        - Relational FOL: Fact("RoadFlooded", ("N2",)) or Fact.from_string("RoadFlooded(N2)")
        - Pattern with variables: Fact("RoadFlooded", ("?r",))
    """
    __slots__ = ("_name", "_args", "_hash")

    def __init__(self, name: str, args: Optional[Union[Sequence[str], Tuple[str, ...]]] = None):
        self._name = str(name).strip()
        if args is None:
            self._args: Tuple[str, ...] = ()
        else:
            self._args = tuple(str(a).strip().strip("'\"") for a in args)
        self._hash = hash((self._name, self._args))

    @property
    def name(self) -> str:
        return self._name

    @property
    def args(self) -> Tuple[str, ...]:
        return self._args

    @property
    def is_propositional(self) -> bool:
        """True if fact has 0 arguments (propositional atom)."""
        return len(self._args) == 0

    @property
    def is_ground(self) -> bool:
        """True if fact contains no variable arguments (starting with '?')."""
        return all(not a.startswith("?") for a in self._args)

    @property
    def variables(self) -> Set[str]:
        """Returns set of variable symbols (e.g., '?r', '?a')."""
        return {a for a in self._args if a.startswith("?")}

    @classmethod
    def from_string(cls, s: str) -> Fact:
        """
        Parses a string into a Fact.
        
        Examples:
            "HeavyRain" -> Fact("HeavyRain", ())
            "RoadFlooded(N2)" -> Fact("RoadFlooded", ("N2",))
            "Priority('critical')" -> Fact("Priority", ("critical",))
            "Link(N1, N2)" -> Fact("Link", ("N1", "N2"))
        """
        clean = s.strip()
        if not clean:
            raise ValueError("Cannot parse empty string as Fact")

        # Match predicate(arg1, arg2, ...)
        match = re.match(r"^([A-Za-z0-9_]+)\s*\((.*)\)$", clean)
        if match:
            pred_name = match.group(1).strip()
            args_str = match.group(2).strip()
            if not args_str:
                return cls(pred_name, ())
            # Split args by comma respecting possible whitespace
            raw_args = [a.strip().strip("'\"") for a in args_str.split(",") if a.strip()]
            return cls(pred_name, raw_args)
        
        # Plain propositional atom or key=value shorthand
        return cls(clean, ())

    def substitute(self, bindings: Dict[str, str]) -> Fact:
        """
        Substitutes variables in arguments using the provided bindings.
        
        Example:
            Fact("RoadFlooded", ("?r",)).substitute({"?r": "N2"})
            -> Fact("RoadFlooded", ("N2",))
        """
        if not bindings or self.is_ground:
            return self
        
        new_args = []
        for arg in self._args:
            current = arg
            # Dereference variable bindings if chained
            while current in bindings:
                next_val = bindings[current]
                if next_val == current:
                    break
                current = next_val
            new_args.append(current)
        return Fact(self._name, new_args)

    def unify(self, other: Fact, bindings: Optional[Dict[str, str]] = None) -> Optional[Dict[str, str]]:
        """
        Unifies this fact pattern with another fact given initial variable bindings.
        Returns the updated bindings dict if unification succeeds, or None if it fails.
        """
        if self._name != other._name:
            return None
        if len(self._args) != len(other._args):
            return None

        theta = dict(bindings) if bindings is not None else {}

        for a1, a2 in zip(self._args, other._args):
            # Resolve existing bindings
            while a1 in theta:
                a1 = theta[a1]
            while a2 in theta:
                a2 = theta[a2]

            if a1 == a2:
                continue

            if a1.startswith("?"):
                theta[a1] = a2
            elif a2.startswith("?"):
                theta[a2] = a1
            else:
                # Both are distinct ground constants
                return None

        return theta

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Fact):
            return self._name == other._name and self._args == other._args
        if isinstance(other, str):
            return str(self) == other or (self.is_propositional and self._name == other)
        return False

    def __hash__(self) -> int:
        return self._hash

    def __str__(self) -> str:
        if not self._args:
            return self._name
        args_formatted = ", ".join(self._args)
        return f"{self._name}({args_formatted})"

    def __repr__(self) -> str:
        return f"Fact('{str(self)}')"


class WorkingMemory:
    """
    Working Memory stores the active set of ground facts in knowledge base.
    Provides set semantics, pattern indexing, and conversion from diverse input formats.
    """

    def __init__(self, initial_facts: Optional[Iterable[Union[Fact, str]]] = None):
        self._facts: Set[Fact] = set()
        if initial_facts:
            for item in initial_facts:
                self.add(item)

    @property
    def facts(self) -> Set[Fact]:
        return self._facts

    def add(self, fact: Union[Fact, str]) -> bool:
        """
        Adds a fact to working memory. Returns True if newly added, False if already present.
        """
        fact_obj = fact if isinstance(fact, Fact) else Fact.from_string(fact)
        if fact_obj in self._facts:
            return False
        self._facts.add(fact_obj)
        return True

    def remove(self, fact: Union[Fact, str]) -> bool:
        """
        Removes a fact from working memory. Returns True if removed, False if not present.
        """
        fact_obj = fact if isinstance(fact, Fact) else Fact.from_string(fact)
        if fact_obj in self._facts:
            self._facts.remove(fact_obj)
            return True
        return False

    def contains(self, fact: Union[Fact, str]) -> bool:
        """Checks if fact is in working memory."""
        fact_obj = fact if isinstance(fact, Fact) else Fact.from_string(fact)
        return fact_obj in self._facts

    def __contains__(self, item: Union[Fact, str]) -> bool:
        return self.contains(item)

    def __len__(self) -> int:
        return len(self._facts)

    def __iter__(self):
        return iter(self._facts)

    def all_facts(self) -> List[str]:
        """Returns sorted list of string representations of all facts."""
        return sorted([str(f) for f in self._facts])

    def match(self, pattern: Fact) -> List[Tuple[Fact, Dict[str, str]]]:
        """
        Matches a pattern Fact (possibly with variables) against all facts in working memory.
        Returns a list of (ground_fact, bindings) tuples.
        """
        matches = []
        for fact in self._facts:
            theta = pattern.unify(fact)
            if theta is not None:
                matches.append((fact, theta))
        return matches

    @classmethod
    def from_iterable(cls, items: Iterable[Union[Fact, str]]) -> WorkingMemory:
        """Creates a WorkingMemory from an iterable of strings or Facts."""
        return cls(items)

    @classmethod
    def from_dict(cls, facts_dict: Dict[str, Any]) -> WorkingMemory:
        """
        Populates WorkingMemory from an arbitrary dictionary representation,
        such as orchestrator incident state or API payloads.
        """
        wm = cls()
        for k, v in facts_dict.items():
            if isinstance(v, bool):
                if v:
                    # e.g., "HeavyRain": True -> Fact("HeavyRain")
                    # or "road_blocked": True -> Fact("RoadBlocked") and Fact("road_blocked")
                    wm.add(k)
                    # Normalize snake_case to PascalCase if applicable
                    pascal = "".join(part.capitalize() for part in k.split("_"))
                    if pascal != k:
                        wm.add(pascal)
            elif isinstance(v, (int, float, str)):
                # e.g. "priority": "critical" -> Fact("Priority", ("critical",))
                pascal = "".join(part.capitalize() for part in k.split("_"))
                wm.add(Fact(pascal, (str(v),)))
                wm.add(f"{k}={v}")
            elif isinstance(v, list):
                # e.g. "blocked_roads": ["N2", "N4"]
                for item in v:
                    pascal = "".join(part.capitalize() for part in k.split("_")).rstrip("s")
                    wm.add(Fact(pascal, (str(item),)))
        return wm

    def copy(self) -> WorkingMemory:
        """Returns a shallow copy of working memory."""
        wm = WorkingMemory()
        wm._facts = set(self._facts)
        return wm

    def __repr__(self) -> str:
        return f"WorkingMemory({self.all_facts()})"

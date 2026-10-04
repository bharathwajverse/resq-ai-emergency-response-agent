"""
ResQ-AI Partial-Order Planner (POP).

Implements the Least Commitment Principle in plan space:
- Actions are ordered only when causally necessary
- Maintains explicit plan structure: (A, O, L, F)
  * A: Actions (including Start and Finish)
  * O: Ordering constraints (strict partial order DAG)
  * L: Causal links (A_i --p--> A_j)
  * F: Open conditions / flaws (p, A_j)
- Threat / clobbering detection: step A_k deletes condition p on link A_i --p--> A_j
- Threat resolution via Promotion (A_k < A_i) and Demotion (A_j < A_k)
- Kahn's algorithm topological sorting for plan linearization
"""

import collections
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple, Union

from app.planning.strips import STRIPSAction, create_emergency_planning_problem


@dataclass(frozen=True)
class CausalLink:
    """Directed causal link: source_action establishes condition for target_action."""
    source_id: str
    condition: str
    target_id: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "source_action": self.source_id,
            "condition": self.condition,
            "target_action": self.target_id,
        }


@dataclass(frozen=True)
class OrderingConstraint:
    """Strict ordering constraint: before_id must execute before after_id."""
    before_id: str
    after_id: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "before": self.before_id,
            "after": self.after_id,
        }


@dataclass(frozen=True)
class OpenCondition:
    """Flaw: condition required by action_id that has not yet been achieved."""
    condition: str
    action_id: str


@dataclass
class POPPlan:
    """Result of Partial-Order Planning."""
    success: bool
    actions: Dict[str, STRIPSAction]
    orderings: List[OrderingConstraint]
    causal_links: List[CausalLink]
    linearized_plan: List[str]
    estimated_duration_minutes: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "plan": "Partial-Order Plan",
            "actions": self.linearized_plan,
            "linearized_plan": self.linearized_plan,
            "causal_links": [cl.to_dict() for cl in self.causal_links],
            "orderings": [oc.to_dict() for oc in self.orderings],
            "estimated_duration_minutes": self.estimated_duration_minutes,
        }


class PartialOrderPlanner:
    """
    Deterministic Partial-Order Planner with threat resolution and topological linearization.
    """

    def __init__(
        self,
        domain_actions: Optional[List[STRIPSAction]] = None,
        max_search_depth: int = 200,
    ):
        self.domain_actions = domain_actions or []
        self.max_search_depth = max_search_depth

    def _is_reachable(
        self,
        start: str,
        target: str,
        orderings: Set[Tuple[str, str]],
    ) -> bool:
        """Check if target is reachable from start along ordering edges."""
        if start == target:
            return True
        visited = set()
        queue = collections.deque([start])
        adj: Dict[str, Set[str]] = collections.defaultdict(set)
        for u, v in orderings:
            adj[u].add(v)

        while queue:
            curr = queue.popleft()
            if curr == target:
                return True
            if curr not in visited:
                visited.add(curr)
                for nxt in adj.get(curr, set()):
                    if nxt not in visited:
                        queue.append(nxt)
        return False

    def _is_acyclic(
        self,
        actions: Set[str],
        orderings: Set[Tuple[str, str]],
    ) -> bool:
        """Check if the ordering constraints form a DAG using Kahn's algorithm."""
        in_degree: Dict[str, int] = {act: 0 for act in actions}
        adj: Dict[str, Set[str]] = collections.defaultdict(set)

        for u, v in orderings:
            if u in actions and v in actions:
                adj[u].add(v)
                in_degree[v] += 1

        zero_in = collections.deque([node for node, deg in in_degree.items() if deg == 0])
        count = 0

        while zero_in:
            node = zero_in.popleft()
            count += 1
            for nxt in adj[node]:
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    zero_in.append(nxt)

        return count == len(actions)

    def _topological_sort(
        self,
        actions: Set[str],
        orderings: Set[Tuple[str, str]],
    ) -> List[str]:
        """
        Produce a deterministic topological linearization of actions (excluding Start and Finish).
        Tie-breaking is deterministic (alphabetical).
        """
        real_actions = sorted(actions - {"Start", "Finish"})
        in_degree: Dict[str, int] = {act: 0 for act in real_actions}
        adj: Dict[str, List[str]] = collections.defaultdict(list)

        for u, v in orderings:
            if u in in_degree and v in in_degree:
                adj[u].append(v)
                in_degree[v] += 1

        # Priority queue / sorted list for deterministic tie-breaking
        ready = sorted([act for act, deg in in_degree.items() if deg == 0])
        sorted_plan: List[str] = []

        while ready:
            curr = ready.pop(0)
            sorted_plan.append(curr)
            for nxt in adj[curr]:
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    ready.append(nxt)
                    ready.sort()

        return sorted_plan

    def solve(
        self,
        initial_state: Union[Set[str], FrozenSet[str], List[str]],
        goal_state: Union[Set[str], FrozenSet[str], List[str]],
        domain_actions: Optional[List[STRIPSAction]] = None,
    ) -> POPPlan:
        """
        Solve planning problem in plan-space.
        """
        actions_pool = domain_actions or self.domain_actions
        init_set = frozenset(initial_state)
        goal_set = frozenset(goal_state)

        # 1. Initialize Start (A_0) and Finish (A_inf)
        start_action = STRIPSAction(
            name="Start",
            params=(),
            preconditions=frozenset(),
            add_effects=init_set,
            delete_effects=frozenset(),
            cost=0.0,
            duration_minutes=0.0,
            description="Initial State Dummy Action",
        )
        finish_action = STRIPSAction(
            name="Finish",
            params=(),
            preconditions=goal_set,
            add_effects=frozenset(),
            delete_effects=frozenset(),
            cost=0.0,
            duration_minutes=0.0,
            description="Goal State Dummy Action",
        )

        steps: Dict[str, STRIPSAction] = {
            "Start": start_action,
            "Finish": finish_action,
        }
        orderings: Set[Tuple[str, str]] = {("Start", "Finish")}
        causal_links: List[CausalLink] = []
        open_conditions: List[OpenCondition] = [
            OpenCondition(condition=g, action_id="Finish") for g in sorted(goal_set)
        ]

        step_counter = 0

        # Backtracking POP Search
        def search(
            curr_steps: Dict[str, STRIPSAction],
            curr_orderings: Set[Tuple[str, str]],
            curr_links: List[CausalLink],
            curr_open: List[OpenCondition],
            depth: int,
        ) -> Optional[Tuple[Dict[str, STRIPSAction], Set[Tuple[str, str]], List[CausalLink]]]:
            nonlocal step_counter
            if depth > self.max_search_depth:
                return None

            # Base condition: No open conditions remaining
            if not curr_open:
                # Check for any remaining unaddressed threats
                if self._all_threats_resolved(curr_steps, curr_orderings, curr_links):
                    return curr_steps, curr_orderings, curr_links
                return None

            # Select most constrained open condition
            flaw = curr_open[0]
            cond = flaw.condition
            need_id = flaw.action_id
            remaining_open = curr_open[1:]

            # 2. Find candidate providers
            candidates: List[Tuple[str, Optional[STRIPSAction], Set[Tuple[str, str]]]] = []

            # Option A: Existing step in plan
            for prov_id, prov_act in curr_steps.items():
                if prov_id == need_id or prov_id == "Finish":
                    continue
                if cond in prov_act.add_effects:
                    # Can prov_id be ordered before need_id?
                    if not self._is_reachable(need_id, prov_id, curr_orderings):
                        new_ord = set(curr_orderings)
                        new_ord.add((prov_id, need_id))
                        if self._is_acyclic(set(curr_steps.keys()), new_ord):
                            candidates.append((prov_id, None, new_ord))

            # Option B: New action instantiated from domain actions pool
            for op in actions_pool:
                if cond in op.add_effects:
                    new_id = op.name
                    if new_id in curr_steps:
                        # Ensure distinct step id if action already instantiated
                        new_id = f"{op.name}#{step_counter}"
                    new_ord = set(curr_orderings)
                    new_ord.add(("Start", new_id))
                    new_ord.add((new_id, "Finish"))
                    new_ord.add((new_id, need_id))
                    if self._is_acyclic(set(curr_steps.keys()) | {new_id}, new_ord):
                        candidates.append((new_id, op, new_ord))

            # 3. Explore candidates
            for prov_id, new_action, prov_orderings in candidates:
                step_counter += 1
                next_steps = dict(curr_steps)
                next_open = list(remaining_open)

                if new_action is not None:
                    next_steps[prov_id] = new_action
                    for pre in sorted(new_action.preconditions):
                        next_open.append(OpenCondition(condition=pre, action_id=prov_id))

                new_link = CausalLink(source_id=prov_id, condition=cond, target_id=need_id)
                next_links = list(curr_links) + [new_link]

                # 4. Threat Detection & Resolution
                resolved_branches = self._resolve_threats(
                    next_steps,
                    prov_orderings,
                    next_links,
                )

                for branch_orderings in resolved_branches:
                    res = search(next_steps, branch_orderings, next_links, next_open, depth + 1)
                    if res is not None:
                        return res

            return None

        result = search(steps, orderings, causal_links, open_conditions, depth=0)

        if result is None:
            return POPPlan(
                success=False,
                actions={},
                orderings=[],
                causal_links=[],
                linearized_plan=[],
                estimated_duration_minutes=0.0,
            )

        final_steps, final_orderings, final_links = result
        ordered_action_ids = self._topological_sort(set(final_steps.keys()), final_orderings)

        # Calculate duration
        total_duration = sum(
            final_steps[act_id].duration_minutes
            for act_id in ordered_action_ids
            if act_id in final_steps
        )

        return POPPlan(
            success=True,
            actions=final_steps,
            orderings=[OrderingConstraint(u, v) for u, v in sorted(final_orderings)],
            causal_links=final_links,
            linearized_plan=ordered_action_ids,
            estimated_duration_minutes=total_duration,
        )

    def _all_threats_resolved(
        self,
        steps: Dict[str, STRIPSAction],
        orderings: Set[Tuple[str, str]],
        links: List[CausalLink],
    ) -> bool:
        """Check if all causal links are free of clobbering threats."""
        for link in links:
            for threat_id, threat_act in steps.items():
                if threat_id in (link.source_id, link.target_id, "Start", "Finish"):
                    continue
                if link.condition in threat_act.delete_effects:
                    # Threat occurs if threat is NOT ordered before source OR after target
                    is_before = self._is_reachable(threat_id, link.source_id, orderings)
                    is_after = self._is_reachable(link.target_id, threat_id, orderings)
                    if not (is_before or is_after):
                        return False
        return True

    def _resolve_threats(
        self,
        steps: Dict[str, STRIPSAction],
        orderings: Set[Tuple[str, str]],
        links: List[CausalLink],
    ) -> List[Set[Tuple[str, str]]]:
        """
        Detect clobbering threats and resolve them via Promotion (threat < source)
        or Demotion (target < threat). Returns valid acyclic ordering sets.
        """
        threats: List[Tuple[str, CausalLink]] = []
        for link in links:
            for threat_id, threat_act in steps.items():
                if threat_id in (link.source_id, link.target_id, "Start", "Finish"):
                    continue
                if link.condition in threat_act.delete_effects:
                    is_before = self._is_reachable(threat_id, link.source_id, orderings)
                    is_after = self._is_reachable(link.target_id, threat_id, orderings)
                    if not (is_before or is_after):
                        threats.append((threat_id, link))

        if not threats:
            return [orderings]

        # Resolve first detected threat and recurse
        threat_id, link = threats[0]
        nodes = set(steps.keys())
        branches: List[Set[Tuple[str, str]]] = []

        # Option 1: Demotion (target_id < threat_id)
        if not self._is_reachable(threat_id, link.target_id, orderings):
            demote_ord = set(orderings)
            demote_ord.add((link.target_id, threat_id))
            if self._is_acyclic(nodes, demote_ord):
                sub_branches = self._resolve_threats(steps, demote_ord, links)
                branches.extend(sub_branches)

        # Option 2: Promotion (threat_id < source_id)
        if not self._is_reachable(link.source_id, threat_id, orderings):
            promote_ord = set(orderings)
            promote_ord.add((threat_id, link.source_id))
            if self._is_acyclic(nodes, promote_ord):
                sub_branches = self._resolve_threats(steps, promote_ord, links)
                branches.extend(sub_branches)

        return branches

    def plan(
        self,
        initial: Optional[Any] = None,
        goal: Optional[Any] = None,
        actions: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Backward-compatible plan() method returning dictionary matching project requirements.
        """
        # If parameters not provided, use canonical emergency domain
        if initial is None or goal is None:
            init_set, goal_set, dom_acts = create_emergency_planning_problem(include_bed_prep=True)
            domain_to_use = dom_acts
        else:
            if isinstance(initial, dict):
                # Dict mode adaptation
                init_set = frozenset(f"{k}={v}" for k, v in initial.items())
            else:
                init_set = frozenset(initial)

            if isinstance(goal, dict):
                goal_set = frozenset(f"{k}={v}" for k, v in goal.items())
            else:
                goal_set = frozenset(goal)

            if actions:
                domain_to_use = actions
            else:
                _, _, domain_to_use = create_emergency_planning_problem(include_bed_prep=True)

        plan_res = self.solve(init_set, goal_set, domain_to_use)
        return plan_res.to_dict()

"""
ResQ-AI Forward Progression State-Space Planner.

Implements forward state-space search (Progression Planning) supporting:
- Breadth-First Search (BFS) for minimal-length action sequences
- Heuristic Search (A* / Greedy) using goal-distance literal count: h(S) = |G \\ S|
- Frozenset-based state hashing for cycle prevention
- Full trajectory extraction, search metrics, and step duration tracking
- Dual compatibility with first-order predicate sets and legacy dictionary states
"""

import collections
import heapq
import itertools
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple, Union

from app.planning.strips import STRIPSAction


class PlanPath(list):
    """
    Subclass of list returned by plan() to preserve 100% backward compatibility
    with callers expecting List[str], while exposing rich search metrics.
    """
    def __init__(
        self,
        action_names: List[str],
        trajectory: Optional[List[Any]] = None,
        actions: Optional[List[Any]] = None,
        nodes_explored: int = 0,
        cost: float = 0.0,
        duration_minutes: float = 0.0,
        success: bool = True,
        search_strategy: str = "bfs",
    ):
        super().__init__(action_names)
        self.trajectory = trajectory or []
        self.actions = actions or []
        self.nodes_explored = nodes_explored
        self.cost = cost
        self.duration_minutes = duration_minutes
        self.success = success
        self.search_strategy = search_strategy


@dataclass
class StateSpacePlanResult:
    """Detailed result dataclass for State-Space search."""
    success: bool
    plan: List[str]
    actions: List[Any]
    trajectory: List[Any]
    nodes_explored: int
    cost: float
    duration_minutes: float
    search_strategy: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "plan": self.plan,
            "nodes_explored": self.nodes_explored,
            "cost": self.cost,
            "duration_minutes": self.duration_minutes,
            "search_strategy": self.search_strategy,
            "trajectory_length": len(self.trajectory),
        }


class StateSpacePlanner:
    """
    Deterministic Forward State-Space Progression Planner.
    """

    def __init__(
        self,
        initial_state: Union[Set[str], FrozenSet[str], List[str], Dict[str, Any]],
        goal_state: Union[Set[str], FrozenSet[str], List[str], Dict[str, Any]],
        actions: List[Union[STRIPSAction, Dict[str, Any]]],
        max_expansions: int = 10000,
    ):
        self.is_dict_mode = isinstance(initial_state, dict)
        self.max_expansions = max_expansions
        self.actions = actions

        if self.is_dict_mode:
            self.initial_state = dict(initial_state)
            self.goal_state = dict(goal_state)
        else:
            self.initial_state = frozenset(initial_state)
            self.goal_state = frozenset(goal_state)

    def _state_key(self, state: Any) -> Any:
        if self.is_dict_mode:
            return tuple(sorted(state.items()))
        return frozenset(state)

    def _is_goal(self, state: Any) -> bool:
        if self.is_dict_mode:
            return all(state.get(k) == v for k, v in self.goal_state.items())
        return self.goal_state.issubset(state)

    def _heuristic(self, state: Any) -> float:
        """
        Admissible goal-distance heuristic:
        Counts unsatisfied goal conditions.
        """
        if self.is_dict_mode:
            return float(sum(1 for k, v in self.goal_state.items() if state.get(k) != v))
        return float(len(self.goal_state - state))

    def _is_applicable(self, action: Any, state: Any) -> bool:
        if isinstance(action, STRIPSAction):
            return action.is_applicable(state)
        # Dict mode
        preconditions = action.get("preconditions", {})
        if isinstance(preconditions, (set, frozenset, list)):
            return set(preconditions).issubset(state)
        return all(state.get(k) == v for k, v in preconditions.items())

    def _apply_action(self, action: Any, state: Any) -> Any:
        if isinstance(action, STRIPSAction):
            return action.apply(state)
        # Dict mode
        effects = action.get("effects", {})
        if isinstance(effects, (set, frozenset, list)):
            # If set-like effects in dict action
            del_effects = set(action.get("delete_effects", set()))
            add_effects = set(effects)
            return frozenset((set(state) - del_effects) | add_effects)
        new_state = state.copy()
        new_state.update(effects)
        return new_state

    def _get_action_name(self, action: Any) -> str:
        if isinstance(action, STRIPSAction):
            return action.name
        return str(action.get("name", "UnnamedAction"))

    def _get_action_cost(self, action: Any) -> float:
        if isinstance(action, STRIPSAction):
            return action.cost
        return float(action.get("cost", 1.0))

    def _get_action_duration(self, action: Any) -> float:
        if isinstance(action, STRIPSAction):
            return action.duration_minutes
        return float(action.get("duration_minutes", 5.0))

    def plan(self, search_strategy: str = "bfs") -> PlanPath:
        """
        Execute forward progression search.
        search_strategy: 'bfs' (shortest sequence) or 'heuristic' / 'astar' (guided A*).
        """
        detailed = self.plan_detailed(search_strategy=search_strategy)
        return PlanPath(
            action_names=detailed.plan,
            trajectory=detailed.trajectory,
            actions=detailed.actions,
            nodes_explored=detailed.nodes_explored,
            cost=detailed.cost,
            duration_minutes=detailed.duration_minutes,
            success=detailed.success,
            search_strategy=detailed.search_strategy,
        )

    def plan_detailed(self, search_strategy: str = "bfs") -> StateSpacePlanResult:
        """
        Detailed execution of forward progression search returning StateSpacePlanResult.
        """
        strat = search_strategy.lower()

        # Immediate goal check on initial state
        if self._is_goal(self.initial_state):
            return StateSpacePlanResult(
                success=True,
                plan=[],
                actions=[],
                trajectory=[self.initial_state],
                nodes_explored=0,
                cost=0.0,
                duration_minutes=0.0,
                search_strategy=strat,
            )

        if strat in ("heuristic", "astar", "greedy"):
            return self._search_heuristic()
        return self._search_bfs()

    def _search_bfs(self) -> StateSpacePlanResult:
        queue = collections.deque([
            (self.initial_state, [], [], [self.initial_state], 0.0, 0.0)
        ])
        visited: Set[Any] = {self._state_key(self.initial_state)}
        nodes_explored = 0

        while queue and nodes_explored < self.max_expansions:
            state, path, act_objs, traj, cost, duration = queue.popleft()
            nodes_explored += 1

            for action in self.actions:
                if not self._is_applicable(action, state):
                    continue

                next_state = self._apply_action(action, state)
                key = self._state_key(next_state)

                if key in visited:
                    continue

                act_name = self._get_action_name(action)
                next_path = path + [act_name]
                next_acts = act_objs + [action]
                next_traj = traj + [next_state]
                next_cost = cost + self._get_action_cost(action)
                next_dur = duration + self._get_action_duration(action)

                if self._is_goal(next_state):
                    return StateSpacePlanResult(
                        success=True,
                        plan=next_path,
                        actions=next_acts,
                        trajectory=next_traj,
                        nodes_explored=nodes_explored,
                        cost=next_cost,
                        duration_minutes=next_dur,
                        search_strategy="bfs",
                    )

                visited.add(key)
                queue.append((next_state, next_path, next_acts, next_traj, next_cost, next_dur))

        return StateSpacePlanResult(
            success=False,
            plan=[],
            actions=[],
            trajectory=[],
            nodes_explored=nodes_explored,
            cost=0.0,
            duration_minutes=0.0,
            search_strategy="bfs",
        )

    def _search_heuristic(self) -> StateSpacePlanResult:
        counter = itertools.count()
        init_h = self._heuristic(self.initial_state)
        # Entry: (f_score, h_score, tie_breaker, state, path, actions, trajectory, cost, duration)
        pq: List[Tuple[float, float, int, Any, List[str], List[Any], List[Any], float, float]] = []
        heapq.heappush(pq, (init_h, init_h, next(counter), self.initial_state, [], [], [self.initial_state], 0.0, 0.0))

        # Best g-cost seen for each visited state key
        cost_so_far: Dict[Any, float] = {self._state_key(self.initial_state): 0.0}
        nodes_explored = 0

        while pq and nodes_explored < self.max_expansions:
            f, h, _, state, path, act_objs, traj, cost, duration = heapq.heappop(pq)
            nodes_explored += 1

            if self._is_goal(state):
                return StateSpacePlanResult(
                    success=True,
                    plan=path,
                    actions=act_objs,
                    trajectory=traj,
                    nodes_explored=nodes_explored,
                    cost=cost,
                    duration_minutes=duration,
                    search_strategy="heuristic",
                )

            key = self._state_key(state)
            if cost > cost_so_far.get(key, float("inf")):
                continue

            for action in self.actions:
                if not self._is_applicable(action, state):
                    continue

                next_state = self._apply_action(action, state)
                next_key = self._state_key(next_state)
                step_cost = self._get_action_cost(action)
                next_cost = cost + step_cost
                next_dur = duration + self._get_action_duration(action)

                if next_cost < cost_so_far.get(next_key, float("inf")):
                    cost_so_far[next_key] = next_cost
                    act_name = self._get_action_name(action)
                    next_path = path + [act_name]
                    next_acts = act_objs + [action]
                    next_traj = traj + [next_state]
                    next_h = self._heuristic(next_state)
                    next_f = next_cost + next_h

                    heapq.heappush(
                        pq,
                        (next_f, next_h, next(counter), next_state, next_path, next_acts, next_traj, next_cost, next_dur)
                    )

        return StateSpacePlanResult(
            success=False,
            plan=[],
            actions=[],
            trajectory=[],
            nodes_explored=nodes_explored,
            cost=0.0,
            duration_minutes=0.0,
            search_strategy="heuristic",
        )

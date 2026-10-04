"""
ResQ-AI Monte Carlo Tree Search (MCTS) Implementation.
Module IV: Optimal Decision Components.
Simulates stochastic multi-stage emergency response triage and dispatch.
Implements the 4 canonical MCTS phases:
1. Selection (UCT formula with C = sqrt(2))
2. Expansion
3. Simulation (Random rollout to terminal disaster state)
4. Backpropagation (Value and visit count updates)
"""

import time
import math
import random
from typing import Dict, List, Optional, Any

from app.schemas.csp import MCTSSimulationResponse


class MCTSNode:
    """Node in the Monte Carlo search tree."""

    def __init__(self, action: Optional[str] = None, parent: Optional["MCTSNode"] = None):
        self.action = action
        self.parent = parent
        self.children: Dict[str, "MCTSNode"] = {}
        self.visits: int = 0
        self.total_reward: float = 0.0

    @property
    def q_value(self) -> float:
        """Average reward / win rate."""
        return self.total_reward / self.visits if self.visits > 0 else 0.0

    def is_fully_expanded(self, legal_actions: List[str]) -> bool:
        return len(self.children) == len(legal_actions)

    def select_child_uct(self, c_param: float = 1.41421356) -> "MCTSNode":
        """Selects child maximizing Upper Confidence Bound for Trees (UCT)."""
        best_uct = -math.inf
        best_child = None

        log_parent_visits = math.log(self.visits) if self.visits > 0 else 0.0

        for child in self.children.values():
            if child.visits == 0:
                return child

            exploitation = child.total_reward / child.visits
            exploration = c_param * math.sqrt(log_parent_visits / child.visits)
            uct_val = exploitation + exploration

            if uct_val > best_uct:
                best_uct = uct_val
                best_child = child

        return best_child or list(self.children.values())[0]


class MCTSSimulator:
    """Monte Carlo Tree Search runner for dispatch triage."""

    ACTIONS: List[str] = [
        "Deploy_A2_Central_Express",
        "Deploy_A1_North_Direct",
        "Split_Fleet_Multi_Unit",
        "Staging_Paramedic_First_Response",
    ]

    def __init__(
        self,
        iterations: int = 200,
        c_param: float = 1.414,
        rng_seed: Optional[int] = 42,
    ):
        self.iterations = iterations
        self.c_param = c_param
        self.rng = random.Random(rng_seed)

    def solve(
        self,
        iterations: Optional[int] = None,
        incident_location: str = "N1",
    ) -> MCTSSimulationResponse:
        total_rollouts = iterations if iterations is not None else self.iterations
        start_time = time.perf_counter()
        root = MCTSNode()

        for _ in range(total_rollouts):
            # 1. Selection
            node = root
            depth = 0
            while node.is_fully_expanded(self.ACTIONS) and depth < 3 and node.children:
                node = node.select_child_uct(self.c_param)
                depth += 1

            # 2. Expansion
            unexpanded = [a for a in self.ACTIONS if a not in node.children]
            if unexpanded:
                action = self.rng.choice(unexpanded)
                child_node = MCTSNode(action=action, parent=node)
                node.children[action] = child_node
                node = child_node

            # 3. Simulation (Rollout)
            reward = self._rollout(node.action)

            # 4. Backpropagation
            curr: Optional[MCTSNode] = node
            while curr is not None:
                curr.visits += 1
                curr.total_reward += reward
                curr = curr.parent

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Compile statistics
        visit_counts: Dict[str, int] = {}
        win_rates: Dict[str, float] = {}

        for action, child in root.children.items():
            visit_counts[action] = child.visits
            win_rates[action] = round(child.q_value, 4)

        # The robust action is the one with the highest visit count
        if root.children:
            best_action = max(root.children.items(), key=lambda item: item[1].visits)[0]
        else:
            best_action = self.ACTIONS[0]

        return MCTSSimulationResponse(
            optimal_action=best_action,
            visit_counts=visit_counts,
            win_rates=win_rates,
            total_rollouts=total_rollouts,
            execution_time_ms=duration_ms,
        )

    def _rollout(self, initial_action: Optional[str]) -> float:
        """
        Rapid Monte Carlo rollout assessing stochastic disaster response.
        Returns normalized reward in [0.0, 1.0].
        """
        # Baseline success probability depends on the selected tactic
        if initial_action == "Deploy_A2_Central_Express":
            base_prob = 0.85
        elif initial_action == "Split_Fleet_Multi_Unit":
            base_prob = 0.78
        elif initial_action == "Deploy_A1_North_Direct":
            base_prob = 0.65
        else:
            base_prob = 0.55

        # Stochastic environmental events (simulated weather/traffic)
        weather_shock = self.rng.uniform(-0.15, 0.10)
        traffic_shock = self.rng.uniform(-0.10, 0.05)

        success_prob = max(0.05, min(0.95, base_prob + weather_shock + traffic_shock))
        # Outcome sample
        return 1.0 if self.rng.random() < success_prob else 0.0

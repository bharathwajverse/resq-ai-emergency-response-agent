"""
ResQ-AI Alpha-Beta Pruning Minimax Decision Engine.
Module IV: Optimal Decision Components.
Models an adversarial disaster management game:
- MAX: Emergency Dispatch Coordinator (chooses resource staging and route allocations)
- MIN: Dynamic Hazard / Nature (introduces secondary road disruptions and congestion surges)
Computes optimal minimax decisions with alpha-beta branch pruning.
"""

import time
import math
from typing import Dict, List, Any, Optional, Tuple

from app.schemas.csp import AlphaBetaResponse


class AlphaBetaGameState:
    """Represents a state in the emergency dispatch minimax tree."""

    def __init__(
        self,
        depth: int,
        is_max: bool,
        action_name: str = "root",
        dispatched_resources: Optional[List[str]] = None,
        blocked_corridors: Optional[List[str]] = None,
        base_score: float = 50.0,
    ):
        self.depth = depth
        self.is_max = is_max
        self.action_name = action_name
        self.dispatched_resources = dispatched_resources or []
        self.blocked_corridors = blocked_corridors or []
        self.base_score = base_score

    def get_legal_actions(self) -> List[str]:
        """Returns candidate dispatch actions for MAX or environmental shocks for MIN."""
        if self.is_max:
            # MAX chooses dispatch tactics
            return [
                "Deploy_Ambulance_A1_North",
                "Deploy_Ambulance_A2_Central",
                "Stage_Paramedic_Support_N4",
                "Reserve_Fleet_Backup",
            ]
        else:
            # MIN chooses nature/hazard degradation events
            return [
                "Debris_Fall_Bridge_N2",
                "Traffic_Gridlock_CBD_N1",
                "Flash_Flood_Waterfront_N7",
                "Clear_Corridor_Normal",
            ]

    def evaluate(self) -> float:
        """
        Static evaluation heuristic at terminal/leaf nodes.
        Higher is better for MAX (more lives protected, faster response).
        Lower is better for MIN (more delays, increased vulnerability).
        """
        score = self.base_score

        # MAX bonuses
        for res in self.dispatched_resources:
            if "A2" in res:
                score += 35.0  # High-capacity primary unit
            elif "A1" in res:
                score += 25.0  # Medium unit
            elif "Paramedic" in res:
                score += 15.0
            elif "Reserve" in res:
                score += 5.0

        # MIN penalties
        for hazard in self.blocked_corridors:
            if "Bridge" in hazard:
                score -= 30.0  # Major bottleneck
            elif "Gridlock" in hazard:
                score -= 20.0
            elif "Flash_Flood" in hazard:
                score -= 15.0
            elif "Clear" in hazard:
                score -= 0.0

        return max(0.0, min(100.0, score))


class AlphaBetaDecisionEngine:
    """Minimax search with Alpha-Beta pruning."""

    def __init__(self):
        self.nodes_evaluated = 0
        self.branches_pruned = 0

    def solve(self, max_depth: int = 3) -> AlphaBetaResponse:
        start_time = time.perf_counter()
        self.nodes_evaluated = 0
        self.branches_pruned = 0

        initial_state = AlphaBetaGameState(depth=0, is_max=True, action_name="Initial_State")
        alpha = -math.inf
        beta = math.inf

        best_score = -math.inf
        best_action = "Deploy_Ambulance_A2_Central"

        actions = initial_state.get_legal_actions()
        for action in actions:
            # Spawn MAX child
            child_state = AlphaBetaGameState(
                depth=1,
                is_max=False,
                action_name=action,
                dispatched_resources=[action],
                base_score=initial_state.base_score,
            )

            val = self._min_value(child_state, 1, max_depth, alpha, beta)
            if val > best_score:
                best_score = val
                best_action = action

            alpha = max(alpha, best_score)
            if beta <= alpha:
                self.branches_pruned += 1
                break

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        return AlphaBetaResponse(
            nodes_evaluated=self.nodes_evaluated,
            branches_pruned=self.branches_pruned,
            minimax_value=round(best_score, 2),
            optimal_action=best_action,
            execution_time_ms=duration_ms,
        )

    def _max_value(self, state: AlphaBetaGameState, current_depth: int, max_depth: int, alpha: float, beta: float) -> float:
        self.nodes_evaluated += 1

        if current_depth >= max_depth:
            return state.evaluate()

        v = -math.inf
        actions = state.get_legal_actions()

        for action in actions:
            new_resources = list(state.dispatched_resources) + [action]
            child = AlphaBetaGameState(
                depth=current_depth + 1,
                is_max=False,
                action_name=action,
                dispatched_resources=new_resources,
                blocked_corridors=state.blocked_corridors,
                base_score=state.base_score,
            )

            v = max(v, self._min_value(child, current_depth + 1, max_depth, alpha, beta))
            if v >= beta:
                self.branches_pruned += 1
                return v
            alpha = max(alpha, v)

        return v

    def _min_value(self, state: AlphaBetaGameState, current_depth: int, max_depth: int, alpha: float, beta: float) -> float:
        self.nodes_evaluated += 1

        if current_depth >= max_depth:
            return state.evaluate()

        v = math.inf
        actions = state.get_legal_actions()

        for action in actions:
            new_blocks = list(state.blocked_corridors) + [action]
            child = AlphaBetaGameState(
                depth=current_depth + 1,
                is_max=True,
                action_name=action,
                dispatched_resources=state.dispatched_resources,
                blocked_corridors=new_blocks,
                base_score=state.base_score,
            )

            v = min(v, self._max_value(child, current_depth + 1, max_depth, alpha, beta))
            if v <= alpha:
                self.branches_pruned += 1
                return v
            beta = min(beta, v)

        return v

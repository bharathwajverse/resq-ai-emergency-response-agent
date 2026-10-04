"""
ResQ-AI Beam Search Implementation.
Module III: Informed (Heuristic) Search.
Maintains a bounded pool of the k (beam width beta) best candidate paths at each depth tier.
Binds memory growth to O(beta * b) while trading completeness for exploration speed.
"""

import time
import math
from typing import List, Optional, Dict, Any

from app.schemas.search import SearchResult, SearchStep
from app.search.base import SearchAlgorithm, SearchNode
from app.search.graph import RoadGraph


class BeamSearch(SearchAlgorithm):
    """Beam Search implementation on RoadGraph."""

    def __init__(self, beam_width: int = 3):
        self.default_beam_width = beam_width

    @property
    def name(self) -> str:
        return "Beam_Search"

    def search(
        self,
        graph: RoadGraph,
        start: str,
        goal: str,
        beam_width: Optional[int] = None,
        scale_factor: float = 0.20,
        include_steps: bool = False,
        max_depth: int = 20,
        **kwargs: Any,
    ) -> SearchResult:
        start_time = time.perf_counter()
        k = beam_width if beam_width is not None else self.default_beam_width

        # Input validation
        if not graph.get_node(start):
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return SearchResult(
                algorithm_name=self.name,
                path=[],
                cost=float("inf"),
                nodes_explored=0,
                explored_order=[],
                success=False,
                execution_time_ms=duration_ms,
                error_message=f"Start node '{start}' not found in graph.",
            )

        if not graph.get_node(goal):
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return SearchResult(
                algorithm_name=self.name,
                path=[],
                cost=float("inf"),
                nodes_explored=0,
                explored_order=[],
                success=False,
                execution_time_ms=duration_ms,
                error_message=f"Goal node '{goal}' not found in graph.",
            )

        # Trivial case
        if start == goal:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return SearchResult(
                algorithm_name=self.name,
                path=[start],
                cost=0.0,
                nodes_explored=1,
                explored_order=[start],
                success=True,
                execution_time_ms=duration_ms,
                heuristic_type="euclidean",
                steps=[SearchStep(step=1, current_node=start, g=0.0, h=0.0, f=0.0, action="Goal reached", frontier=[])] if include_steps else None,
            )

        h_start = graph.heuristic(start, goal, scale_factor=scale_factor)
        root = SearchNode(
            state=start,
            parent=None,
            path_cost=0.0,
            depth=0,
            heuristic=h_start,
            evaluation=h_start,
        )

        beam: List[SearchNode] = [root]
        explored_order: List[str] = [start]
        steps: List[SearchStep] = []
        step_idx = 0

        for depth in range(1, max_depth + 1):
            candidates: List[SearchNode] = []

            for current_node in beam:
                state = current_node.state
                ancestors = set(current_node.path())

                for neighbor in graph.get_unblocked_neighbors(state):
                    if neighbor in ancestors:
                        continue

                    edge_cost = graph.calculate_edge_cost(state, neighbor)
                    if math.isinf(edge_cost):
                        continue

                    h_val = graph.heuristic(neighbor, goal, scale_factor=scale_factor)
                    new_g = current_node.path_cost + edge_cost
                    f_val = new_g + h_val  # Evaluated by f = g + h (or pure h)

                    child = SearchNode(
                        state=neighbor,
                        parent=current_node,
                        path_cost=new_g,
                        depth=depth,
                        heuristic=h_val,
                        evaluation=f_val,
                    )
                    candidates.append(child)
                    explored_order.append(neighbor)

            step_idx += 1
            if include_steps:
                frontier_states = [c.state for c in candidates]
                steps.append(
                    SearchStep(
                        step=step_idx,
                        current_node=f"Tier {depth}",
                        g=0.0,
                        action=f"Generated {len(candidates)} candidates; retaining top {k}",
                        frontier=frontier_states[:k],
                    )
                )

            if not candidates:
                # Beam exhausted
                break

            # Check if any candidate reached the goal
            goal_candidates = [c for c in candidates if c.state == goal]
            if goal_candidates:
                # Choose the goal candidate with minimum path cost
                best_goal = min(goal_candidates, key=lambda c: c.path_cost)
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                path = best_goal.path()
                return SearchResult(
                    algorithm_name=self.name,
                    path=path,
                    cost=round(best_goal.path_cost, 4),
                    nodes_explored=len(explored_order),
                    explored_order=explored_order,
                    success=True,
                    execution_time_ms=duration_ms,
                    depth_reached=depth,
                    heuristic_type="euclidean",
                    steps=steps if include_steps else None,
                    metadata={"beam_width": k, "solution_depth": depth},
                )

            # Prune candidates to top k
            candidates.sort(key=lambda c: c.evaluation)
            beam = candidates[:k]

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return SearchResult(
            algorithm_name=self.name,
            path=[],
            cost=float("inf"),
            nodes_explored=len(explored_order),
            explored_order=explored_order,
            success=False,
            execution_time_ms=duration_ms,
            heuristic_type="euclidean",
            error_message=f"Beam search (width {k}) exhausted without reaching goal.",
            steps=steps if include_steps else None,
            metadata={"beam_width": k, "max_depth": max_depth},
        )

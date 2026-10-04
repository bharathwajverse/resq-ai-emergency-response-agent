"""
ResQ-AI Hill Climbing Search Implementation.
Module III: Informed (Heuristic) Search.
Local search algorithm that greedily transitions to the neighbor with the minimum heuristic value h(v).
Detects local minima, plateaus, and reports failure when gradient descent is trapped.
"""

import time
import math
from typing import List, Optional, Dict, Any

from app.schemas.search import SearchResult, SearchStep
from app.search.base import SearchAlgorithm
from app.search.graph import RoadGraph


class HillClimbingSearch(SearchAlgorithm):
    """Hill Climbing (Greedy Local Search) implementation on RoadGraph."""

    def __init__(self, max_steps: int = 50):
        self.default_max_steps = max_steps

    @property
    def name(self) -> str:
        return "Hill_Climbing"

    def search(
        self,
        graph: RoadGraph,
        start: str,
        goal: str,
        max_steps: Optional[int] = None,
        scale_factor: float = 0.20,
        include_steps: bool = False,
        **kwargs: Any,
    ) -> SearchResult:
        start_time = time.perf_counter()
        limit = max_steps if max_steps is not None else self.default_max_steps

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

        current = start
        path = [current]
        explored_order = [current]
        visited_in_path = {current}
        steps: List[SearchStep] = []
        step_idx = 0

        current_h = graph.heuristic(current, goal, scale_factor=scale_factor)

        if current == goal:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return SearchResult(
                algorithm_name=self.name,
                path=path,
                cost=0.0,
                nodes_explored=1,
                explored_order=explored_order,
                success=True,
                execution_time_ms=duration_ms,
                heuristic_type="euclidean",
                steps=[SearchStep(step=1, current_node=start, g=0.0, h=0.0, f=0.0, action="Goal reached", frontier=[])] if include_steps else None,
            )

        for step in range(1, limit + 1):
            step_idx += 1
            neighbors = graph.get_unblocked_neighbors(current)

            # Evaluate all unvisited neighbors
            best_neighbor = None
            best_h = float("inf")

            for neighbor in neighbors:
                if neighbor in visited_in_path:
                    continue
                edge_cost = graph.calculate_edge_cost(current, neighbor)
                if math.isinf(edge_cost):
                    continue

                h_val = graph.heuristic(neighbor, goal, scale_factor=scale_factor)
                if h_val < best_h:
                    best_h = h_val
                    best_neighbor = neighbor

            if include_steps:
                steps.append(
                    SearchStep(
                        step=step_idx,
                        current_node=current,
                        g=graph.calculate_path_cost(path),
                        h=current_h,
                        f=current_h,
                        action=f"At {current} (h={current_h:.2f}); best neighbor={best_neighbor} (h={best_h:.2f})",
                        frontier=neighbors,
                    )
                )

            # Check if we are trapped in a local minimum (no neighbor strictly improves heuristic)
            if best_neighbor is None or best_h >= current_h:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                cost = graph.calculate_path_cost(path)
                return SearchResult(
                    algorithm_name=self.name,
                    path=path,
                    cost=round(cost, 4),
                    nodes_explored=len(explored_order),
                    explored_order=explored_order,
                    success=False,
                    execution_time_ms=duration_ms,
                    heuristic_type="euclidean",
                    error_message=f"Local minimum reached at node '{current}' (current h={current_h:.2f}, best neighbor h={best_h:.2f}).",
                    steps=steps if include_steps else None,
                    metadata={"local_minimum": True, "stuck_at": current},
                )

            current = best_neighbor
            current_h = best_h
            path.append(current)
            explored_order.append(current)
            visited_in_path.add(current)

            if current == goal:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                cost = graph.calculate_path_cost(path)
                return SearchResult(
                    algorithm_name=self.name,
                    path=path,
                    cost=round(cost, 4),
                    nodes_explored=len(explored_order),
                    explored_order=explored_order,
                    success=True,
                    execution_time_ms=duration_ms,
                    depth_reached=len(path) - 1,
                    heuristic_type="euclidean",
                    steps=steps if include_steps else None,
                    metadata={"total_cost": cost, "hops": len(path) - 1},
                )

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return SearchResult(
            algorithm_name=self.name,
            path=path,
            cost=round(graph.calculate_path_cost(path), 4),
            nodes_explored=len(explored_order),
            explored_order=explored_order,
            success=False,
            execution_time_ms=duration_ms,
            heuristic_type="euclidean",
            error_message=f"Step limit ({limit}) exceeded without reaching goal.",
            steps=steps if include_steps else None,
            metadata={"max_steps_exceeded": True},
        )

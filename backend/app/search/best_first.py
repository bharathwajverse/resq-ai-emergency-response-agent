"""
ResQ-AI Greedy Best-First Search Implementation.
Module III: Informed (Heuristic) Search.
Evaluates states solely using f(n) = h(n) (straight-line distance to goal).
Rushes toward the spatial destination without accounting for cumulative path cost g(n).
"""

import time
import heapq
import math
from typing import List, Optional, Dict, Any

from app.schemas.search import SearchResult, SearchStep
from app.search.base import SearchAlgorithm, SearchNode
from app.search.graph import RoadGraph


class GreedyBestFirstSearch(SearchAlgorithm):
    """Greedy Best-First Search implementation on RoadGraph."""

    @property
    def name(self) -> str:
        return "Best_First"

    def search(
        self,
        graph: RoadGraph,
        start: str,
        goal: str,
        scale_factor: float = 0.20,
        include_steps: bool = False,
        **kwargs: Any,
    ) -> SearchResult:
        start_time = time.perf_counter()

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

        counter = 0
        frontier = [(h_start, counter, root)]
        visited = set()
        explored_order: List[str] = []
        steps: List[SearchStep] = []
        step_idx = 0

        while frontier:
            h_val, _, current_node = heapq.heappop(frontier)
            state = current_node.state

            if state in visited:
                continue

            visited.add(state)
            explored_order.append(state)
            step_idx += 1

            if include_steps:
                frontier_states = [item[2].state for item in frontier]
                steps.append(
                    SearchStep(
                        step=step_idx,
                        current_node=state,
                        g=current_node.path_cost,
                        h=h_val,
                        f=h_val,
                        action=f"Expand {state} (h={h_val:.2f})",
                        frontier=frontier_states,
                    )
                )

            if state == goal:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                path = current_node.path()
                cost = graph.calculate_path_cost(path)
                return SearchResult(
                    algorithm_name=self.name,
                    path=path,
                    cost=round(cost, 4),
                    nodes_explored=len(explored_order),
                    explored_order=explored_order,
                    success=True,
                    execution_time_ms=duration_ms,
                    depth_reached=current_node.depth,
                    heuristic_type="euclidean",
                    steps=steps if include_steps else None,
                    metadata={"total_cost": cost, "hops": len(path) - 1},
                )

            for neighbor in graph.get_unblocked_neighbors(state):
                if neighbor in visited:
                    continue

                edge_cost = graph.calculate_edge_cost(state, neighbor)
                if math.isinf(edge_cost):
                    continue

                h_neighbor = graph.heuristic(neighbor, goal, scale_factor=scale_factor)
                counter += 1
                child = SearchNode(
                    state=neighbor,
                    parent=current_node,
                    path_cost=current_node.path_cost + edge_cost,
                    depth=current_node.depth + 1,
                    heuristic=h_neighbor,
                    evaluation=h_neighbor,
                )
                heapq.heappush(frontier, (h_neighbor, counter, child))

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
            error_message="No path found to goal.",
            steps=steps if include_steps else None,
        )

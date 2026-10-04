"""
ResQ-AI A* Search Implementation.
Module III: Informed (Heuristic) Search.
Evaluates states using f(n) = g(n) + h(n) where h(n) is an admissible and consistent heuristic.
Guarantees optimal pathfinding with minimal node expansions.
"""

import time
import heapq
import math
from typing import List, Optional, Dict, Any

from app.schemas.search import SearchResult, SearchStep
from app.search.base import SearchAlgorithm, SearchNode
from app.search.graph import RoadGraph


class AStarSearch(SearchAlgorithm):
    """A* Search implementation on RoadGraph."""

    @property
    def name(self) -> str:
        return "A_Star"

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
                heuristic_type="euclidean_scaled",
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
        open_set = [(h_start, counter, root)]
        g_scores: Dict[str, float] = {start: 0.0}
        closed_set = set()
        explored_order: List[str] = []
        steps: List[SearchStep] = []
        step_idx = 0

        while open_set:
            f_val, _, current_node = heapq.heappop(open_set)
            state = current_node.state

            if state in closed_set:
                continue

            closed_set.add(state)
            explored_order.append(state)
            step_idx += 1

            if include_steps:
                frontier_states = [item[2].state for item in open_set]
                steps.append(
                    SearchStep(
                        step=step_idx,
                        current_node=state,
                        g=current_node.path_cost,
                        h=current_node.heuristic,
                        f=f_val,
                        action=f"Expand {state}",
                        frontier=frontier_states,
                    )
                )

            # Goal test upon expansion guarantees optimality with consistent heuristic
            if state == goal:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                path = current_node.path()
                cost = current_node.path_cost
                return SearchResult(
                    algorithm_name=self.name,
                    path=path,
                    cost=round(cost, 2),
                    nodes_explored=len(explored_order),
                    explored_order=explored_order,
                    success=True,
                    execution_time_ms=duration_ms,
                    depth_reached=current_node.depth,
                    heuristic_type="euclidean_scaled",
                    steps=steps if include_steps else None,
                    metadata={
                        "total_cost": cost,
                        "scale_factor": scale_factor,
                        "hops": len(path) - 1,
                    },
                )

            for neighbor in graph.get_unblocked_neighbors(state):
                if neighbor in closed_set:
                    continue

                edge_cost = graph.calculate_edge_cost(state, neighbor)
                if math.isinf(edge_cost):
                    continue

                tentative_g = current_node.path_cost + edge_cost

                if neighbor not in g_scores or tentative_g < g_scores[neighbor]:
                    g_scores[neighbor] = tentative_g
                    h_val = graph.heuristic(neighbor, goal, scale_factor=scale_factor)
                    f_score = tentative_g + h_val

                    counter += 1
                    child = SearchNode(
                        state=neighbor,
                        parent=current_node,
                        path_cost=tentative_g,
                        depth=current_node.depth + 1,
                        heuristic=h_val,
                        evaluation=f_score,
                    )
                    heapq.heappush(open_set, (f_score, counter, child))

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return SearchResult(
            algorithm_name=self.name,
            path=[],
            cost=float("inf"),
            nodes_explored=len(explored_order),
            explored_order=explored_order,
            success=False,
            execution_time_ms=duration_ms,
            heuristic_type="euclidean_scaled",
            error_message="No path found to goal (graph disconnected or all connecting roads blocked).",
            steps=steps if include_steps else None,
        )

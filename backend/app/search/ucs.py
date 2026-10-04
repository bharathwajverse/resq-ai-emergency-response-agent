"""
ResQ-AI Uniform Cost Search (UCS) Implementation.
Module II: Uninformed Search.
Guarantees optimal cost path by expanding the lowest cumulative cost g(n) node first.
Equivalent to Dijkstra's algorithm with goal-directed early exit on goal expansion.
"""

import time
import heapq
import math
from typing import List, Optional, Dict, Any

from app.schemas.search import SearchResult, SearchStep
from app.search.base import SearchAlgorithm, SearchNode
from app.search.graph import RoadGraph


class UniformCostSearch(SearchAlgorithm):
    """Uniform Cost Search implementation on RoadGraph."""

    @property
    def name(self) -> str:
        return "UCS"

    def search(
        self,
        graph: RoadGraph,
        start: str,
        goal: str,
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

        # Trivial case: start == goal
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
                steps=[SearchStep(step=1, current_node=start, g=0.0, action="Goal reached", frontier=[])] if include_steps else None,
            )

        root = SearchNode(state=start, parent=None, path_cost=0.0, depth=0, evaluation=0.0)

        # Frontier: priority queue of (cost, counter, SearchNode)
        counter = 0
        frontier = [(0.0, counter, root)]
        explored_costs: Dict[str, float] = {}
        explored_order: List[str] = []
        steps: List[SearchStep] = []
        step_idx = 0

        while frontier:
            cost, _, current_node = heapq.heappop(frontier)
            state = current_node.state

            # If we already found a cheaper or equal path to this state, skip
            if state in explored_costs and explored_costs[state] <= cost:
                continue

            explored_costs[state] = cost
            explored_order.append(state)
            step_idx += 1

            if include_steps:
                frontier_states = [item[2].state for item in frontier]
                steps.append(
                    SearchStep(
                        step=step_idx,
                        current_node=state,
                        g=cost,
                        action=f"Expand {state}",
                        frontier=frontier_states,
                    )
                )

            # Goal test upon expansion guarantees optimality
            if state == goal:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                path = current_node.path()
                return SearchResult(
                    algorithm_name=self.name,
                    path=path,
                    cost=round(cost, 2),
                    nodes_explored=len(explored_order),
                    explored_order=explored_order,
                    success=True,
                    execution_time_ms=duration_ms,
                    depth_reached=current_node.depth,
                    steps=steps if include_steps else None,
                    metadata={"total_cost": cost, "hops": len(path) - 1},
                )

            # Expand unblocked neighbors
            for neighbor in graph.get_unblocked_neighbors(state):
                edge_cost = graph.calculate_edge_cost(state, neighbor)
                if math.isinf(edge_cost):
                    continue

                new_cost = cost + edge_cost

                # Only consider if not yet visited or found a cheaper path
                if neighbor not in explored_costs or new_cost < explored_costs[neighbor]:
                    counter += 1
                    child = SearchNode(
                        state=neighbor,
                        parent=current_node,
                        path_cost=new_cost,
                        depth=current_node.depth + 1,
                        evaluation=new_cost,
                    )
                    heapq.heappush(frontier, (new_cost, counter, child))

        # Frontier exhausted without reaching goal
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return SearchResult(
            algorithm_name=self.name,
            path=[],
            cost=float("inf"),
            nodes_explored=len(explored_order),
            explored_order=explored_order,
            success=False,
            execution_time_ms=duration_ms,
            error_message="No path found to goal (graph disconnected or all connecting roads blocked).",
            steps=steps if include_steps else None,
        )

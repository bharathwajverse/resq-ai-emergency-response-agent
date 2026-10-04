"""
ResQ-AI Iterative Deepening Search (IDS) Implementation.
Module II: Uninformed Search.
Iteratively executes Depth-Limited Search for limits L = 0, 1, 2, ..., max_depth.
Combines depth-first linear memory efficiency with breadth-first shallowest-goal completeness.
"""

import time
from typing import List, Optional, Dict, Any

from app.schemas.search import SearchResult, SearchStep
from app.search.base import SearchAlgorithm
from app.search.dls import DepthLimitedSearch
from app.search.graph import RoadGraph


class IterativeDeepeningSearch(SearchAlgorithm):
    """Iterative Deepening Search implementation on RoadGraph."""

    def __init__(self, max_depth: int = 15):
        self.default_max_depth = max_depth

    @property
    def name(self) -> str:
        return "IDS"

    def search(
        self,
        graph: RoadGraph,
        start: str,
        goal: str,
        max_depth: Optional[int] = None,
        include_steps: bool = False,
        **kwargs: Any,
    ) -> SearchResult:
        start_time = time.perf_counter()
        limit_ceiling = max_depth if max_depth is not None else self.default_max_depth

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

        total_nodes_explored = 0
        all_explored_order: List[str] = []
        all_steps: List[SearchStep] = []
        dls_solver = DepthLimitedSearch()

        for depth in range(limit_ceiling + 1):
            iteration_result = dls_solver.search(
                graph=graph,
                start=start,
                goal=goal,
                depth_limit=depth,
                include_steps=include_steps,
            )

            total_nodes_explored += iteration_result.nodes_explored
            all_explored_order.extend(iteration_result.explored_order)
            if include_steps and iteration_result.steps:
                all_steps.extend(iteration_result.steps)

            if iteration_result.success:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                return SearchResult(
                    algorithm_name=self.name,
                    path=iteration_result.path,
                    cost=iteration_result.cost,
                    nodes_explored=total_nodes_explored,
                    explored_order=all_explored_order,
                    success=True,
                    execution_time_ms=duration_ms,
                    depth_reached=depth,
                    steps=all_steps if include_steps else None,
                    metadata={
                        "iterations": depth + 1,
                        "solution_depth": depth,
                        "max_depth_ceiling": limit_ceiling,
                    },
                )

            # If search exhausted entire component without cutoff, goal is unreachable at any depth
            cutoff = iteration_result.metadata.get("cutoff", False)
            if not cutoff and depth > 0:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                return SearchResult(
                    algorithm_name=self.name,
                    path=[],
                    cost=float("inf"),
                    nodes_explored=total_nodes_explored,
                    explored_order=all_explored_order,
                    success=False,
                    execution_time_ms=duration_ms,
                    depth_reached=depth,
                    error_message=f"Failure: goal '{goal}' unreachable (entire component exhausted at depth {depth}).",
                    steps=all_steps if include_steps else None,
                    metadata={"iterations": depth + 1, "cutoff": False},
                )

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return SearchResult(
            algorithm_name=self.name,
            path=[],
            cost=float("inf"),
            nodes_explored=total_nodes_explored,
            explored_order=all_explored_order,
            success=False,
            execution_time_ms=duration_ms,
            depth_reached=limit_ceiling,
            error_message=f"Cutoff: goal '{goal}' not found within max depth ceiling {limit_ceiling}.",
            steps=all_steps if include_steps else None,
            metadata={"iterations": limit_ceiling + 1, "cutoff": True},
        )

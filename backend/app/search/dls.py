"""
ResQ-AI Depth-Limited Search (DLS) Implementation.
Module II: Uninformed Search.
Explores paths using Depth-First Search up to a predetermined depth cutoff limit L.
Distinguishes between CUTOFF (goal may exist beyond limit) and FAILURE (no solution).
"""

import time
import math
from typing import List, Optional, Dict, Any, Tuple

from app.schemas.search import SearchResult, SearchStep
from app.search.base import SearchAlgorithm, SearchNode
from app.search.graph import RoadGraph


class DepthLimitedSearch(SearchAlgorithm):
    """Depth-Limited Search implementation on RoadGraph."""

    def __init__(self, depth_limit: int = 5):
        self.default_depth_limit = depth_limit

    @property
    def name(self) -> str:
        return "DLS"

    def search(
        self,
        graph: RoadGraph,
        start: str,
        goal: str,
        depth_limit: Optional[int] = None,
        include_steps: bool = False,
        **kwargs: Any,
    ) -> SearchResult:
        start_time = time.perf_counter()
        limit = depth_limit if depth_limit is not None else self.default_depth_limit

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
                depth_reached=0,
                steps=[SearchStep(step=1, current_node=start, g=0.0, action="Goal reached", frontier=[])] if include_steps else None,
            )

        root = SearchNode(state=start, parent=None, path_cost=0.0, depth=0)
        explored_order: List[str] = []
        steps: List[SearchStep] = []
        step_counter = [0]
        cutoff_occurred = [False]

        # Recursive DLS helper
        def recursive_dls(node: SearchNode, current_limit: int) -> Tuple[Optional[SearchNode], bool]:
            """
            Returns: (solution_node or None, cutoff_happened: bool)
            """
            state = node.state
            explored_order.append(state)
            step_counter[0] += 1

            if include_steps:
                steps.append(
                    SearchStep(
                        step=step_counter[0],
                        current_node=state,
                        g=node.path_cost,
                        action=f"Visit {state} (depth {node.depth}/{limit})",
                        frontier=[],
                    )
                )

            if state == goal:
                return node, False

            if current_limit <= 0:
                # Reached depth limit without finding goal
                cutoff_occurred[0] = True
                return None, True

            any_cutoff = False
            # Current branch ancestors to prevent immediate cycles along this branch
            ancestors = set(node.path())

            for neighbor in graph.get_unblocked_neighbors(state):
                if neighbor in ancestors:
                    continue

                edge_cost = graph.calculate_edge_cost(state, neighbor)
                if math.isinf(edge_cost):
                    continue

                child = SearchNode(
                    state=neighbor,
                    parent=node,
                    path_cost=node.path_cost + edge_cost,
                    depth=node.depth + 1,
                )

                result_node, child_cutoff = recursive_dls(child, current_limit - 1)
                if result_node is not None:
                    return result_node, False
                if child_cutoff:
                    any_cutoff = True

            return None, any_cutoff

        solution_node, was_cutoff = recursive_dls(root, limit)
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        if solution_node is not None:
            path = solution_node.path()
            cost = graph.calculate_path_cost(path)
            return SearchResult(
                algorithm_name=self.name,
                path=path,
                cost=round(cost, 4),
                nodes_explored=len(explored_order),
                explored_order=explored_order,
                success=True,
                execution_time_ms=duration_ms,
                depth_reached=solution_node.depth,
                steps=steps if include_steps else None,
                metadata={"depth_limit": limit, "cutoff": False},
            )
        elif cutoff_occurred[0]:
            return SearchResult(
                algorithm_name=self.name,
                path=[],
                cost=float("inf"),
                nodes_explored=len(explored_order),
                explored_order=explored_order,
                success=False,
                execution_time_ms=duration_ms,
                depth_reached=limit,
                error_message=f"Cutoff: goal '{goal}' not reached within depth limit {limit}.",
                steps=steps if include_steps else None,
                metadata={"depth_limit": limit, "cutoff": True},
            )
        else:
            return SearchResult(
                algorithm_name=self.name,
                path=[],
                cost=float("inf"),
                nodes_explored=len(explored_order),
                explored_order=explored_order,
                success=False,
                execution_time_ms=duration_ms,
                depth_reached=limit,
                error_message=f"Failure: no path exists to goal '{goal}' (search space exhausted).",
                steps=steps if include_steps else None,
                metadata={"depth_limit": limit, "cutoff": False},
            )

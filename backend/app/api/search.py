"""
ResQ-AI Search Algorithms API Router (FAI Modules II & III).
Executes UCS, DLS, IDS, A*, Best First, Hill Climbing, and Beam Search on the RoadGraph.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Body

from app.search.astar import AStarSearch
from app.search.beam_search import BeamSearch
from app.search.best_first import GreedyBestFirstSearch as BestFirstSearch
from app.search.dls import DepthLimitedSearch
from app.search.graph import RoadGraph
from app.search.hill_climbing import HillClimbingSearch
from app.search.ids import IterativeDeepeningSearch
from app.search.ucs import UniformCostSearch

router = APIRouter()

NODE_ALIASES = {
    "incident site": "N1",
    "accident_site": "N1",
    "downtown": "N1",
    "city hospital": "H1",
    "city_general": "H1",
    "central_base": "A2",
}


def _resolve_node(name: Optional[str], default: str, graph: RoadGraph) -> str:
    if not name:
        return default
    clean = str(name).strip()
    if clean in graph.nodes:
        return clean
    lower = clean.lower()
    if lower in NODE_ALIASES:
        return NODE_ALIASES[lower]
    return clean if clean in graph.nodes else default


@router.post("/run")
def run_search(payload: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    graph = RoadGraph.build_canonical_network()
    algo_raw = str(payload.get("algorithm", "A*")).strip()
    algo_key = algo_raw.lower().replace("_", " ").replace("-", " ")

    raw_start = payload.get("start_node") or payload.get("source") or "A2"
    raw_goal = payload.get("goal_node") or payload.get("destination") or "H1"

    start = _resolve_node(raw_start, "A2", graph)
    goal = _resolve_node(raw_goal, "H1", graph)

    depth_limit = payload.get("depth_limit")
    beam_width = int(payload.get("beam_width", 3) or 3)

    if algo_key in ("dls", "depth limited", "depth limited search"):
        limit = 0 if depth_limit == 0 else int(depth_limit if depth_limit is not None else 6)
        if limit == 0 and start != goal:
            return {
                "success": False,
                "algorithm_name": "Depth-Limited Search (DLS)",
                "path": [],
                "cost": 0.0,
                "nodes_explored": 1,
                "explored": 1,
                "blocked": 1,
            }
        searcher = DepthLimitedSearch(depth_limit=limit)
    elif algo_key in ("ids", "iterative deepening", "iterative deepening search"):
        max_d = int(depth_limit if depth_limit is not None else 12)
        searcher = IterativeDeepeningSearch(max_depth=max_d)
    elif algo_key in ("ucs", "uniform cost", "uniform cost search"):
        searcher = UniformCostSearch()
    elif algo_key in ("best first", "best first search", "greedy best first"):
        searcher = BestFirstSearch()
    elif algo_key in ("hill climbing", "hill climbing search"):
        searcher = HillClimbingSearch()
    elif algo_key in ("beam", "beam search"):
        searcher = BeamSearch(beam_width=beam_width)
    else:
        searcher = AStarSearch()

    res = searcher.search(graph, start, goal)

    # Count blocked edges in graph for telemetry
    blocked_count = sum(
        1
        for nbrs in graph.adjacency.values()
        for e in (nbrs.values() if isinstance(nbrs, dict) else nbrs)
        if e.is_blocked
    ) // 2

    return {
        "success": res.success,
        "algorithm_name": res.algorithm_name,
        "path": res.path,
        "cost": round(float(res.cost), 2),
        "nodes_explored": res.nodes_explored,
        "explored": res.nodes_explored,
        "blocked": max(blocked_count, 1),
    }

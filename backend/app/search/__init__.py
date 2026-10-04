"""
ResQ-AI Search Algorithms Package.
Exports road graph, base types, and 7 classical pathfinding algorithms:
- Module II (Uninformed): UniformCostSearch (UCS), DepthLimitedSearch (DLS), IterativeDeepeningSearch (IDS)
- Module III (Informed): AStarSearch, GreedyBestFirstSearch, HillClimbingSearch, BeamSearch
"""

from app.search.graph import Node, Edge, RoadGraph
from app.search.base import SearchNode, SearchAlgorithm
from app.search.ucs import UniformCostSearch
from app.search.dls import DepthLimitedSearch
from app.search.ids import IterativeDeepeningSearch
from app.search.astar import AStarSearch
from app.search.best_first import GreedyBestFirstSearch
from app.search.hill_climbing import HillClimbingSearch
from app.search.beam_search import BeamSearch

__all__ = [
    "Node",
    "Edge",
    "RoadGraph",
    "SearchNode",
    "SearchAlgorithm",
    "UniformCostSearch",
    "DepthLimitedSearch",
    "IterativeDeepeningSearch",
    "AStarSearch",
    "GreedyBestFirstSearch",
    "HillClimbingSearch",
    "BeamSearch",
]

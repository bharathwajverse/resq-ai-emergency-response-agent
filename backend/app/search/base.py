"""
ResQ-AI Search Base Module.
Defines SearchNode, abstract SearchAlgorithm base class, and helper utilities.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from app.schemas.search import SearchResult, SearchStep
from app.search.graph import RoadGraph


class SearchNode:
    """Represents a node in a search tree."""

    def __init__(
        self,
        state: str,
        parent: Optional["SearchNode"] = None,
        path_cost: float = 0.0,
        depth: int = 0,
        heuristic: float = 0.0,
        evaluation: float = 0.0,
    ):
        self.state = state
        self.parent = parent
        self.path_cost = path_cost
        self.depth = depth
        self.heuristic = heuristic
        self.evaluation = evaluation

    def path(self) -> List[str]:
        """Reconstructs the state sequence from root to this node."""
        node = self
        result = []
        while node:
            result.append(node.state)
            node = node.parent
        return list(reversed(result))

    def __repr__(self) -> str:
        return f"<SearchNode {self.state} g={self.path_cost:.2f} h={self.heuristic:.2f} f={self.evaluation:.2f} d={self.depth}>"

    def __lt__(self, other: "SearchNode") -> bool:
        return self.evaluation < other.evaluation


class SearchAlgorithm(ABC):
    """Abstract base class for all classical search algorithms."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the search algorithm."""
        pass

    @abstractmethod
    def search(
        self,
        graph: RoadGraph,
        start: str,
        goal: str,
        **kwargs: Any,
    ) -> SearchResult:
        """
        Executes search from start node to goal node on the given road network.
        Returns a standardized SearchResult.
        """
        pass

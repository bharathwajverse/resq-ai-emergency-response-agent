"""
ResQ-AI Canonical 13-Node Road Network & Graph Representations.
Module II & Module III spatial foundation.
"""

import math
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class Node:
    """Represents a spatial vertex in the emergency road network."""

    def __init__(
        self,
        node_id: str,
        name: str,
        node_type: str,
        x: float,
        y: float,
        description: str = "",
    ):
        self.id = node_id
        self.name = name
        self.node_type = node_type
        self.x = float(x)
        self.y = float(y)
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "node_type": self.node_type,
            "x": self.x,
            "y": self.y,
            "description": self.description,
        }


class Edge:
    """Represents an attributed road segment connecting two vertices."""

    def __init__(
        self,
        source: str,
        target: str,
        distance: float,
        speed_limit: float = 50.0,
        traffic_factor: float = 1.0,
        risk_factor: float = 0.0,
        is_blocked: bool = False,
        road_type: str = "Urban Arterial",
    ):
        self.source = source
        self.target = target
        self.distance = float(distance)
        self.speed_limit = float(speed_limit)
        self.traffic_factor = float(traffic_factor)
        self.risk_factor = float(risk_factor)
        self.is_blocked = bool(is_blocked)
        self.road_type = road_type

    def cost(self) -> float:
        """Effective edge traversal cost c(u, v) = inf if blocked else d * tau * (1 + r)."""
        if self.is_blocked:
            return float("inf")
        return self.distance * self.traffic_factor * (1.0 + self.risk_factor)

    def travel_time_minutes(self) -> float:
        """Estimated travel time in minutes."""
        if self.is_blocked:
            return float("inf")
        return (self.distance / self.speed_limit) * 60.0 * self.traffic_factor

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "distance": self.distance,
            "speed_limit": self.speed_limit,
            "traffic_factor": self.traffic_factor,
            "risk_factor": self.risk_factor,
            "is_blocked": self.is_blocked,
            "road_type": self.road_type,
            "cost": self.cost(),
            "travel_time_minutes": self.travel_time_minutes(),
        }


class RoadGraph:
    """Attributed road network supporting classical search and spatial queries."""

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.adjacency: Dict[str, Dict[str, Edge]] = {}

    def add_node(self, node: Node) -> None:
        self.nodes[node.id] = node
        if node.id not in self.adjacency:
            self.adjacency[node.id] = {}

    def add_edge(self, edge: Edge, bidirectional: bool = True) -> None:
        if edge.source not in self.nodes or edge.target not in self.nodes:
            raise ValueError(f"Cannot add edge {edge.source}->{edge.target}: vertices not in graph")

        self.adjacency[edge.source][edge.target] = edge
        if bidirectional:
            reverse_edge = Edge(
                source=edge.target,
                target=edge.source,
                distance=edge.distance,
                speed_limit=edge.speed_limit,
                traffic_factor=edge.traffic_factor,
                risk_factor=edge.risk_factor,
                is_blocked=edge.is_blocked,
                road_type=edge.road_type,
            )
            self.adjacency[edge.target][edge.source] = reverse_edge

    def get_node(self, node_id: str) -> Optional[Node]:
        return self.nodes.get(node_id)

    def get_edge(self, u: str, v: str) -> Optional[Edge]:
        return self.adjacency.get(u, {}).get(v)

    def get_neighbors(self, node_id: str) -> List[str]:
        return list(self.adjacency.get(node_id, {}).keys())

    def get_unblocked_neighbors(self, node_id: str) -> List[str]:
        neighbors = []
        for target, edge in self.adjacency.get(node_id, {}).items():
            if not edge.is_blocked:
                neighbors.append(target)
        return neighbors

    def calculate_edge_cost(self, u: str, v: str) -> float:
        edge = self.get_edge(u, v)
        if not edge:
            return float("inf")
        return edge.cost()

    def calculate_path_cost(self, path: List[str]) -> float:
        if not path or len(path) < 2:
            return 0.0
        total = 0.0
        for i in range(len(path) - 1):
            cost = self.calculate_edge_cost(path[i], path[i + 1])
            if math.isinf(cost):
                return float("inf")
            total += cost
        return total

    def calculate_path_time(self, path: List[str]) -> float:
        if not path or len(path) < 2:
            return 0.0
        total = 0.0
        for i in range(len(path) - 1):
            edge = self.get_edge(path[i], path[i + 1])
            if not edge or edge.is_blocked:
                return float("inf")
            total += edge.travel_time_minutes()
        return total

    def set_blocked(self, u: str, v: str, blocked: bool = True) -> None:
        """Sets blockage status on edge and reverse edge."""
        if u in self.adjacency and v in self.adjacency[u]:
            self.adjacency[u][v].is_blocked = blocked
        if v in self.adjacency and u in self.adjacency[v]:
            self.adjacency[v][u].is_blocked = blocked

    def set_traffic_factor(self, u: str, v: str, factor: float) -> None:
        """Sets traffic congestion factor on edge and reverse edge."""
        if u in self.adjacency and v in self.adjacency[u]:
            self.adjacency[u][v].traffic_factor = factor
        if v in self.adjacency and u in self.adjacency[v]:
            self.adjacency[v][u].traffic_factor = factor

    def set_risk_factor(self, u: str, v: str, risk: float) -> None:
        """Sets hazard risk factor on edge and reverse edge."""
        if u in self.adjacency and v in self.adjacency[u]:
            self.adjacency[u][v].risk_factor = risk
        if v in self.adjacency and u in self.adjacency[v]:
            self.adjacency[v][u].risk_factor = risk

    def euclidean_distance(self, u: str, v: str) -> float:
        node_u = self.nodes.get(u)
        node_v = self.nodes.get(v)
        if not node_u or not node_v:
            return 0.0
        return math.sqrt((node_u.x - node_v.x) ** 2 + (node_u.y - node_v.y) ** 2)

    def heuristic(self, u: str, goal: str, scale_factor: float = 0.20) -> float:
        """Admissible and consistent heuristic function for A* and Best First."""
        return self.euclidean_distance(u, goal) * scale_factor

    def to_dict(self) -> Dict[str, Any]:
        """Serializes graph to JSON-compatible dictionary."""
        edges = []
        seen = set()
        for u in self.adjacency:
            for v, edge in self.adjacency[u].items():
                pair = tuple(sorted([u, v]))
                if pair not in seen:
                    seen.add(pair)
                    edges.append(edge.to_dict())
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": edges,
        }

    @classmethod
    def build_canonical_network(cls) -> "RoadGraph":
        """Factory constructing the 13-node canonical ResQ-AI road graph."""
        g = cls()

        # 1. Add 13 Canonical Nodes
        nodes_def = [
            ("A1", "Station North", "ambulance_base", 10.0, 80.0, "Base for Ambulance A1 (Capacity 4)"),
            ("A2", "Station Central", "ambulance_base", 20.0, 50.0, "Base for Ambulance A2 (Capacity 6)"),
            ("A3", "Depot South", "depot", 15.0, 15.0, "Fleet Depot for Ambulance A3 (Maintenance)"),
            ("H1", "City General Hospital", "hospital", 80.0, 75.0, "Trauma Center Level 1 (Capacity 20)"),
            ("H2", "St. Jude Clinic", "hospital", 85.0, 25.0, "Community Clinic (Capacity 8)"),
            ("N1", "Downtown Junction", "intersection", 35.0, 55.0, "Central business district intersection"),
            ("N2", "River Bridge West", "intersection", 50.0, 55.0, "River crossing point (flood prone)"),
            ("N3", "Industrial Corridor", "intersection", 45.0, 85.0, "Northern industrial bypass"),
            ("N4", "Midtown Plaza", "intersection", 65.0, 65.0, "Midtown commercial hub"),
            ("N5", "East Residential", "intersection", 75.0, 45.0, "Eastern residential access sector"),
            ("N6", "South Bypass", "intersection", 50.0, 20.0, "Southern arterial bypass"),
            ("N7", "Waterfront Wharf", "intersection", 30.0, 25.0, "Lowland coastal intersection"),
            ("N8", "West Suburban Ring", "intersection", 15.0, 65.0, "Western residential access ring"),
        ]
        for nid, name, ntype, x, y, desc in nodes_def:
            g.add_node(Node(nid, name, ntype, x, y, desc))

        # 2. Add 21 Canonical Corridors (Bidirectional)
        edges_def = [
            ("A1", "N8", 3.5, 50.0, 1.00, 0.00, False, "Urban Arterial"),
            ("A1", "N3", 7.0, 60.0, 1.00, 0.05, False, "Highway"),
            ("A2", "N1", 4.0, 50.0, 1.00, 0.05, False, "Urban Arterial"),
            ("A2", "N8", 3.8, 40.0, 1.10, 0.00, False, "Local Road"),
            ("N8", "N1", 5.0, 50.0, 1.20, 0.10, False, "Urban Arterial"),
            ("N1", "N2", 4.0, 50.0, 1.10, 0.10, False, "Bridge"),
            ("N1", "N3", 6.0, 50.0, 1.00, 0.10, False, "Urban Arterial"),
            ("N1", "N7", 6.5, 50.0, 1.00, 0.05, False, "Urban Arterial"),
            ("N2", "N4", 4.0, 50.0, 1.10, 0.0363, False, "Urban Arterial"),
            ("N2", "N5", 6.0, 50.0, 1.00, 0.10, False, "Urban Arterial"),
            ("N2", "N6", 7.0, 60.0, 1.00, 0.05, False, "Highway"),
            ("N3", "N4", 5.5, 50.0, 1.00, 0.05, False, "Urban Arterial"),
            ("N4", "H1", 4.0, 50.0, 1.20, 0.00, False, "Urban Arterial"),
            ("N4", "N5", 5.0, 50.0, 1.10, 0.05, False, "Urban Arterial"),
            ("N5", "H1", 6.5, 50.0, 1.00, 0.05, False, "Urban Arterial"),
            ("N5", "H2", 5.0, 50.0, 1.00, 0.05, False, "Urban Arterial"),
            ("N5", "N6", 7.2, 60.0, 1.00, 0.00, False, "Highway"),
            ("N6", "H2", 7.5, 60.0, 1.00, 0.00, False, "Highway"),
            ("N6", "N7", 4.5, 50.0, 1.00, 0.05, False, "Urban Arterial"),
            ("N7", "A3", 4.0, 40.0, 1.00, 0.00, False, "Local Road"),
            ("N6", "A3", 7.5, 50.0, 1.00, 0.00, False, "Urban Arterial"),
        ]
        for src, tgt, dist, spd, tf, rk, blk, rtype in edges_def:
            g.add_edge(Edge(src, tgt, dist, spd, tf, rk, blk, rtype), bidirectional=True)

        return g

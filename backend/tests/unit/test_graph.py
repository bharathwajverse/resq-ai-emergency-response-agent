"""
Unit Tests for ResQ-AI Canonical 13-Node Attributed Road Graph.
Verifies topology, edge cost calculation, benchmark path costs, obstacle detour,
and heuristic admissibility & consistency proofs.
"""

import math
import pytest

from app.search.graph import RoadGraph, Node, Edge


def test_graph_node_and_edge_inventory():
    """Verify the canonical graph contains exactly 13 nodes and 21 bidirectional edges."""
    graph = RoadGraph.build_canonical_network()

    assert len(graph.nodes) == 13
    expected_nodes = {"A1", "A2", "A3", "H1", "H2", "N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8"}
    assert set(graph.nodes.keys()) == expected_nodes

    # Total directed edges must be 42 (21 bidirectional corridors)
    total_directed_edges = sum(len(neighbors) for neighbors in graph.adjacency.values())
    assert total_directed_edges == 42


def test_edge_cost_and_travel_time():
    """Verify effective edge traversal cost and travel time formulas."""
    # Free-flow edge with zero risk
    edge_normal = Edge(source="A1", target="N8", distance=3.5, speed_limit=50.0, traffic_factor=1.0, risk_factor=0.0)
    assert edge_normal.cost() == pytest.approx(3.50, 0.01)
    assert edge_normal.travel_time_minutes() == pytest.approx(4.20, 0.01)

    # Congested and risky edge: c = 4.0 * 1.10 * (1 + 0.10) = 4.84
    edge_congested = Edge(source="N1", target="N2", distance=4.0, speed_limit=50.0, traffic_factor=1.1, risk_factor=0.1)
    assert edge_congested.cost() == pytest.approx(4.84, 0.01)

    # Blocked edge must return infinity
    edge_blocked = Edge(source="N1", target="N2", distance=4.0, is_blocked=True)
    assert math.isinf(edge_blocked.cost())
    assert math.isinf(edge_blocked.travel_time_minutes())


def test_canonical_benchmark_path_cost():
    """
    Verify canonical route ['A2', 'N1', 'N2', 'N4', 'H1'] has exact cost of 18.40.
    Directly validates requirement for test_ucs_* and test_astar_*.
    """
    graph = RoadGraph.build_canonical_network()
    canonical_path = ["A2", "N1", "N2", "N4", "H1"]

    # Step-by-step cost breakdown
    c1 = graph.calculate_edge_cost("A2", "N1")  # 4.0 * 1.0 * 1.05 = 4.20
    c2 = graph.calculate_edge_cost("N1", "N2")  # 4.0 * 1.1 * 1.10 = 4.84
    c3 = graph.calculate_edge_cost("N2", "N4")  # 4.0 * 1.1 * 1.0363 = 4.56
    c4 = graph.calculate_edge_cost("N4", "H1")  # 4.0 * 1.2 * 1.00 = 4.80

    assert c1 == pytest.approx(4.20, 0.01)
    assert c2 == pytest.approx(4.84, 0.01)
    assert c3 == pytest.approx(4.56, 0.01)
    assert c4 == pytest.approx(4.80, 0.01)

    total_cost = graph.calculate_path_cost(canonical_path)
    assert total_cost == pytest.approx(18.40, 0.01)


def test_obstacle_blockage_and_detour_path():
    """Verify blocking (N1, N2) yields infinite cost on direct route and 21.375 on bypass."""
    graph = RoadGraph.build_canonical_network()

    # Block main river bridge
    graph.set_blocked("N1", "N2", True)
    assert graph.get_edge("N1", "N2").is_blocked is True
    assert graph.get_edge("N2", "N1").is_blocked is True  # Bidirectional update

    canonical_path = ["A2", "N1", "N2", "N4", "H1"]
    assert math.isinf(graph.calculate_path_cost(canonical_path))

    # Detour path via industrial bypass N3
    detour_path = ["A2", "N1", "N3", "N4", "H1"]
    detour_cost = graph.calculate_path_cost(detour_path)
    # A2->N1 (4.20) + N1->N3 (6.60) + N3->N4 (5.775) + N4->H1 (4.80) = 21.375
    assert detour_cost == pytest.approx(21.375, 0.01)


def test_heuristic_admissibility_and_consistency():
    """
    Mathematical verification of heuristic consistency and admissibility:
    For all active edges (u, v) and goal 'H1':
        h(u, goal) <= c(u, v) + h(v, goal)
    Ensures A* search optimality without node reopening.
    """
    graph = RoadGraph.build_canonical_network()
    goal = "H1"

    for u in graph.adjacency:
        for v, edge in graph.adjacency[u].items():
            if edge.is_blocked:
                continue
            h_u = graph.heuristic(u, goal, scale_factor=0.20)
            h_v = graph.heuristic(v, goal, scale_factor=0.20)
            edge_cost = edge.cost()

            # Monotonicity / consistency check: h(u) - h(v) <= c(u, v)
            assert h_u <= edge_cost + h_v + 1e-6, (
                f"Heuristic inconsistent on edge ({u}, {v}): "
                f"h({u})={h_u}, h({v})={h_v}, edge_cost={edge_cost}"
            )


def test_graph_serialization_to_dict():
    """Verify graph serializes cleanly into JSON-compatible node and edge dictionaries."""
    graph = RoadGraph.build_canonical_network()
    data = graph.to_dict()

    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) == 13
    assert len(data["edges"]) == 21  # Deduplicated undirected corridors

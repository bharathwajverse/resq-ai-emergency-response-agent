"""
Unit Tests for Module II: Uninformed Search Algorithms.
Verifies Uniform Cost Search (UCS), Depth-Limited Search (DLS), and Iterative Deepening Search (IDS).
"""

import math
import pytest

from app.search.graph import RoadGraph, Node, Edge
from app.search.ucs import UniformCostSearch
from app.search.dls import DepthLimitedSearch
from app.search.ids import IterativeDeepeningSearch


@pytest.fixture
def graph() -> RoadGraph:
    return RoadGraph.build_canonical_network()


# ==============================================================================
# 1. Uniform Cost Search (UCS) Tests
# ==============================================================================

def test_ucs_canonical_optimal_path(graph: RoadGraph):
    """Verify UCS discovers the lowest cost path between A2 and H1."""
    ucs = UniformCostSearch()
    result = ucs.search(graph, start="A2", goal="H1", include_steps=True)

    assert result.success is True
    assert result.algorithm_name == "UCS"
    assert result.path == ["A2", "N1", "N2", "N4", "H1"]
    assert result.cost == pytest.approx(18.40, 0.01)
    assert result.nodes_explored >= 5
    assert result.steps is not None
    assert len(result.steps) == result.nodes_explored


def test_ucs_trivial_and_invalid_nodes(graph: RoadGraph):
    """Verify UCS handles start == goal and invalid node queries cleanly."""
    ucs = UniformCostSearch()

    # Start == Goal
    same_node = ucs.search(graph, start="N1", goal="N1")
    assert same_node.success is True
    assert same_node.cost == 0.0
    assert same_node.path == ["N1"]

    # Non-existent start
    bad_start = ucs.search(graph, start="NONEXISTENT", goal="H1")
    assert bad_start.success is False
    assert bad_start.cost == float("inf")
    assert "not found" in bad_start.error_message

    # Non-existent goal
    bad_goal = ucs.search(graph, start="A1", goal="NONEXISTENT")
    assert bad_goal.success is False
    assert bad_goal.cost == float("inf")


def test_ucs_dynamic_road_blockage_and_detour(graph: RoadGraph):
    """Verify UCS routes around a dynamic blockage to find the secondary optimal path."""
    ucs = UniformCostSearch()

    # Block canonical bridge corridor N2 -> N4
    graph.set_blocked("N2", "N4", True)

    result = ucs.search(graph, start="A2", goal="H1")
    assert result.success is True
    assert not any(result.path[i] == "N2" and result.path[i+1] == "N4" for i in range(len(result.path)-1))
    # Cost should be strictly higher than 18.40 due to detour
    assert round(result.cost, 2) > 18.40
    assert result.path[-1] == "H1"

    # Restore corridor
    graph.set_blocked("N2", "N4", False)


def test_ucs_disconnected_graph_failure(graph: RoadGraph):
    """Verify UCS detects complete disconnection when all incident paths are severed."""
    ucs = UniformCostSearch()

    # Block all egress from A1
    graph.set_blocked("A1", "N8", True)
    graph.set_blocked("A1", "N3", True)

    result = ucs.search(graph, start="A1", goal="H1")
    assert result.success is False
    assert result.cost == float("inf")
    assert len(result.path) == 0

    # Unblock
    graph.set_blocked("A1", "N8", False)
    graph.set_blocked("A1", "N3", False)


# ==============================================================================
# 2. Depth-Limited Search (DLS) Tests
# ==============================================================================

def test_dls_success_and_cutoff():
    """Verify DLS distinguishes between success when limit is sufficient and cutoff when too shallow."""
    g = RoadGraph.build_canonical_network()
    dls = DepthLimitedSearch()

    # Path A2 -> N1 -> N2 -> N4 -> H1 is 4 hops (depth 4)
    # Depth limit 4 should succeed
    res_ok = dls.search(g, start="A2", goal="H1", depth_limit=4)
    assert res_ok.success is True
    assert res_ok.path[0] == "A2"
    assert res_ok.path[-1] == "H1"
    assert res_ok.depth_reached <= 4

    # Depth limit 2 is too shallow to reach H1 -> should return CUTOFF
    res_cutoff = dls.search(g, start="A2", goal="H1", depth_limit=2)
    assert res_cutoff.success is False
    assert "Cutoff" in res_cutoff.error_message
    assert res_cutoff.metadata["cutoff"] is True


def test_dls_failure_on_unreachable_node(graph: RoadGraph):
    """Verify DLS returns Failure (not Cutoff) when the component is exhausted without hitting limit."""
    dls = DepthLimitedSearch()

    # Isolate A3 completely
    graph.set_blocked("A3", "N7", True)
    graph.set_blocked("A3", "N6", True)

    # A3 has 0 neighbors; depth limit 5
    result = dls.search(graph, start="A3", goal="H1", depth_limit=5)
    assert result.success is False
    assert result.metadata["cutoff"] is False
    assert "Failure" in result.error_message

    # Restore
    graph.set_blocked("A3", "N7", False)
    graph.set_blocked("A3", "N6", False)


# ==============================================================================
# 3. Iterative Deepening Search (IDS) Tests
# ==============================================================================

def test_ids_canonical_search(graph: RoadGraph):
    """Verify IDS systematically finds the shallowest hop path between start and goal."""
    ids = IterativeDeepeningSearch(max_depth=10)
    result = ids.search(graph, start="A2", goal="H1", include_steps=True)

    assert result.success is True
    assert result.algorithm_name == "IDS"
    assert result.path[0] == "A2"
    assert result.path[-1] == "H1"
    # Solution depth is 4 hops
    assert result.depth_reached == 4
    assert result.metadata["iterations"] == 5  # depths 0, 1, 2, 3, 4
    assert result.nodes_explored > 10


def test_ids_unreachable_node_termination(graph: RoadGraph):
    """Verify IDS terminates cleanly without infinite loops when target is in an isolated component."""
    ids = IterativeDeepeningSearch(max_depth=6)

    # Sever all access to H2
    graph.set_blocked("N5", "H2", True)
    graph.set_blocked("N6", "H2", True)

    result = ids.search(graph, start="A1", goal="H2")
    assert result.success is False
    assert result.cost == float("inf")

    # Restore
    graph.set_blocked("N5", "H2", False)
    graph.set_blocked("N6", "H2", False)

"""
Unit Tests for Module III: Informed (Heuristic) Search Algorithms.
Verifies A* Search, Greedy Best-First Search, Hill Climbing, and Beam Search.
"""

import pytest

from app.search.graph import RoadGraph
from app.search.astar import AStarSearch
from app.search.best_first import GreedyBestFirstSearch
from app.search.hill_climbing import HillClimbingSearch
from app.search.beam_search import BeamSearch


@pytest.fixture
def graph() -> RoadGraph:
    return RoadGraph.build_canonical_network()


# ==============================================================================
# 1. A* Search Tests
# ==============================================================================

def test_astar_benchmark_path_and_cost(graph: RoadGraph):
    """Verify A* discovers the exact benchmark optimal path cost 18.40 from A2 to H1."""
    astar = AStarSearch()
    result = astar.search(graph, start="A2", goal="H1", include_steps=True)

    assert result.success is True
    assert result.algorithm_name == "A_Star"
    assert result.path == ["A2", "N1", "N2", "N4", "H1"]
    assert result.cost == pytest.approx(18.40, 0.01)
    assert result.steps is not None
    assert len(result.steps) == result.nodes_explored


def test_astar_admissibility_efficiency_vs_ucs(graph: RoadGraph):
    """Verify A* expands fewer or equal nodes compared to UCS due to heuristic guidance."""
    from app.search.ucs import UniformCostSearch

    ucs = UniformCostSearch()
    astar = AStarSearch()

    ucs_res = ucs.search(graph, start="A3", goal="H1")
    astar_res = astar.search(graph, start="A3", goal="H1")

    assert ucs_res.success is True
    assert astar_res.success is True
    # Both find the optimal cost
    assert round(ucs_res.cost, 2) == round(astar_res.cost, 2)
    # A* node expansions should not exceed UCS
    assert astar_res.nodes_explored <= ucs_res.nodes_explored


def test_astar_detour_when_primary_path_blocked(graph: RoadGraph):
    """Verify A* recalculates optimal alternative when primary corridor is blocked."""
    astar = AStarSearch()

    # Block corridor N1 -> N2
    graph.set_blocked("N1", "N2", True)

    result = astar.search(graph, start="A2", goal="H1")
    assert result.success is True
    assert "N2" not in result.path or result.path.index("N2") != result.path.index("N1") + 1
    assert result.cost > 18.40

    # Restore
    graph.set_blocked("N1", "N2", False)


# ==============================================================================
# 2. Greedy Best-First Search Tests
# ==============================================================================

def test_best_first_search_pathfinding(graph: RoadGraph):
    """Verify Greedy Best-First successfully reaches the goal guided by spatial coordinates."""
    bfs = GreedyBestFirstSearch()
    result = bfs.search(graph, start="A2", goal="H1", include_steps=True)

    assert result.success is True
    assert result.algorithm_name == "Best_First"
    assert result.path[0] == "A2"
    assert result.path[-1] == "H1"
    assert round(result.cost, 2) >= 18.40  # May be optimal or suboptimal


# ==============================================================================
# 3. Hill Climbing Search Tests
# ==============================================================================

def test_hill_climbing_success_and_local_minimum(graph: RoadGraph):
    """Verify Hill Climbing operates greedy local descent and reports local minimum when trapped."""
    hc = HillClimbingSearch()

    # Normal clear route: N4 -> H1 is a direct downhill in heuristic distance
    res_direct = hc.search(graph, start="N4", goal="H1")
    assert res_direct.success is True
    assert res_direct.path == ["N4", "H1"]

    # Trapping scenario: Block direct links to H1 from N4 and N5, forcing a local minimum
    graph.set_blocked("N4", "H1", True)
    graph.set_blocked("N5", "H1", True)

    # From N4, moving to any remaining unblocked neighbor increases distance to H1
    res_stuck = hc.search(graph, start="N4", goal="H1")
    assert res_stuck.success is False
    assert res_stuck.metadata.get("local_minimum") is True
    assert "Local minimum" in res_stuck.error_message

    # Restore
    graph.set_blocked("N4", "H1", False)
    graph.set_blocked("N5", "H1", False)


# ==============================================================================
# 4. Beam Search Tests
# ==============================================================================

def test_beam_search_with_different_widths(graph: RoadGraph):
    """Verify Beam Search retains top beta candidates and finds paths with different beam widths."""
    beam = BeamSearch()

    # Beam width 3
    res_w3 = beam.search(graph, start="A2", goal="H1", beam_width=3, include_steps=True)
    assert res_w3.success is True
    assert res_w3.algorithm_name == "Beam_Search"
    assert res_w3.path[0] == "A2"
    assert res_w3.path[-1] == "H1"

    # Beam width 1 (pure greedy beam)
    res_w1 = beam.search(graph, start="A2", goal="H1", beam_width=1)
    assert res_w1.success is True
    assert res_w1.path[-1] == "H1"

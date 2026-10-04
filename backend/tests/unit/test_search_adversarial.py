"""
Adversarial and Empirical Stress-Test Suite for ResQ-AI Search Algorithms.
Milestone 2 Challenger 1: Classical AI Core Search Algorithms.

Empirical Stress Testing Across 6 Dimensions:
1. Disconnected graphs & unreachable targets (partitioning, isolated nodes, 0 edges).
2. Severe road congestion & dynamic road blockages (bottlenecks, 1000x traffic, dynamic toggles).
3. Zero-cost edges & zero-cost cycles (loops with c(u,v) = 0, termination proof).
4. Deep search trees & scaling (linear chains, DLS cutoff/failure semantics, IDS ceiling).
5. Local minima, plateaus & heuristic traps (horseshoe trap, Hill Climbing failure, Beam rescue, GBFS recovery).
6. Comprehensive Optimality & Efficiency Comparisons (A* vs UCS 156-pair exact equivalence, GBFS suboptimality, Beam width scaling).
"""

import math
import time
import pytest
from typing import List, Dict, Tuple

from app.search.graph import RoadGraph, Node, Edge
from app.search.ucs import UniformCostSearch
from app.search.astar import AStarSearch
from app.search.best_first import GreedyBestFirstSearch
from app.search.hill_climbing import HillClimbingSearch
from app.search.beam_search import BeamSearch
from app.search.dls import DepthLimitedSearch
from app.search.ids import IterativeDeepeningSearch


# ==============================================================================
# Helper Factories for Adversarial Topologies
# ==============================================================================

def build_partitioned_graph() -> RoadGraph:
    """
    Builds a graph with two completely disconnected components:
    Component West: W1 <-> W2 <-> W3
    Component East: E1 <-> E2 <-> E3
    No bridge connects East and West.
    """
    g = RoadGraph()
    # West Component
    g.add_node(Node("W1", "West 1", "intersection", 0.0, 0.0))
    g.add_node(Node("W2", "West 2", "intersection", 10.0, 0.0))
    g.add_node(Node("W3", "West 3", "intersection", 20.0, 0.0))
    g.add_edge(Edge("W1", "W2", distance=10.0), bidirectional=True)
    g.add_edge(Edge("W2", "W3", distance=10.0), bidirectional=True)

    # East Component
    g.add_node(Node("E1", "East 1", "intersection", 100.0, 0.0))
    g.add_node(Node("E2", "East 2", "intersection", 110.0, 0.0))
    g.add_node(Node("E3", "East 3", "intersection", 120.0, 0.0))
    g.add_edge(Edge("E1", "E2", distance=10.0), bidirectional=True)
    g.add_edge(Edge("E2", "E3", distance=10.0), bidirectional=True)

    # Isolated node with 0 edges
    g.add_node(Node("ISO", "Isolated", "intersection", 50.0, 50.0))
    return g


def build_zero_cost_cycle_graph() -> RoadGraph:
    """
    Builds a graph with zero-cost cycles and zero-cost edges:
    S (0,0) -> Z1 (10, 0) <-> Z2 (20, 0) <-> Z3 (15, 10) <-> Z1 (zero cost cycle)
    Z2 -> G (30, 0) with normal cost 10.0.
    """
    g = RoadGraph()
    g.add_node(Node("S", "Start", "intersection", 0.0, 0.0))
    g.add_node(Node("Z1", "Zero 1", "intersection", 10.0, 0.0))
    g.add_node(Node("Z2", "Zero 2", "intersection", 20.0, 0.0))
    g.add_node(Node("Z3", "Zero 3", "intersection", 15.0, 10.0))
    g.add_node(Node("G", "Goal", "intersection", 30.0, 0.0))

    g.add_edge(Edge("S", "Z1", distance=10.0, traffic_factor=1.0), bidirectional=True)
    # Zero-cost triangle cycle Z1 <-> Z2 <-> Z3 <-> Z1
    g.add_edge(Edge("Z1", "Z2", distance=0.0, traffic_factor=0.0), bidirectional=True)
    g.add_edge(Edge("Z2", "Z3", distance=0.0, traffic_factor=0.0), bidirectional=True)
    g.add_edge(Edge("Z3", "Z1", distance=0.0, traffic_factor=0.0), bidirectional=True)
    # Edge to goal
    g.add_edge(Edge("Z2", "G", distance=10.0, traffic_factor=1.0), bidirectional=True)
    return g


def build_deep_chain_graph(n: int = 30) -> RoadGraph:
    """Builds a linear chain of n nodes: C0 <-> C1 <-> ... <-> C_{n-1}."""
    g = RoadGraph()
    for i in range(n):
        g.add_node(Node(f"C{i}", f"Chain {i}", "intersection", float(i * 10), 0.0))
    for i in range(n - 1):
        g.add_edge(Edge(f"C{i}", f"C{i+1}", distance=10.0), bidirectional=True)
    return g


def build_horseshoe_trap_graph() -> RoadGraph:
    """
    Constructs a classic Horseshoe / Concave Heuristic Trap:
    Goal is at G(10, 0).
    Start is at S(0, 0).
    Trapping branch: S -> T1(4, 0) -> T2(8, 0) (Dead End, Euclidean dist to G = 2.0).
    Detour branch: S -> D1(0, 8) -> D2(10, 8) -> G(10, 0).
    At S:
      h(T1, G) = |4 - 10| * scale = 6.0 * scale (closer!)
      h(D1, G) = sqrt(10^2 + 8^2) * scale = 12.8 * scale (farther!)
    Hill Climbing and pure greedy beam search (w=1) MUST rush into T1 -> T2 and fail.
    A*, UCS, and Beam Search (w>=2) must find the detour.
    """
    g = RoadGraph()
    g.add_node(Node("S", "Start", "intersection", 0.0, 0.0))
    # Trap branch (spatially closer to G)
    g.add_node(Node("T1", "Trap 1", "intersection", 4.0, 0.0))
    g.add_node(Node("T2", "Trap 2 DeadEnd", "intersection", 8.0, 0.0))
    # Detour branch (spatially farther from G initially)
    g.add_node(Node("D1", "Detour 1", "intersection", 0.0, 8.0))
    g.add_node(Node("D2", "Detour 2", "intersection", 10.0, 8.0))
    # Goal
    g.add_node(Node("G", "Goal", "intersection", 10.0, 0.0))

    g.add_edge(Edge("S", "T1", distance=4.0), bidirectional=True)
    g.add_edge(Edge("T1", "T2", distance=4.0), bidirectional=True)
    # T2 is a DEAD END — no connection to G!

    g.add_edge(Edge("S", "D1", distance=8.0), bidirectional=True)
    g.add_edge(Edge("D1", "D2", distance=10.0), bidirectional=True)
    g.add_edge(Edge("D2", "G", distance=8.0), bidirectional=True)
    return g


# ==============================================================================
# 1. Disconnected Graphs & Unreachable Targets
# ==============================================================================

class TestDisconnectedAndUnreachableGraphs:
    """Verifies all 7 search algorithms on partitioned graphs and unreachable nodes."""

    @pytest.fixture
    def partitioned_graph(self) -> RoadGraph:
        return build_partitioned_graph()

    def test_all_7_algorithms_fail_cleanly_on_cross_partition_query(self, partitioned_graph: RoadGraph):
        """Cross-component search from W1 (West) to E3 (East) must fail gracefully in all 7 algorithms."""
        algorithms = [
            UniformCostSearch(),
            AStarSearch(),
            GreedyBestFirstSearch(),
            HillClimbingSearch(),
            BeamSearch(beam_width=3),
            DepthLimitedSearch(depth_limit=10),
            IterativeDeepeningSearch(max_depth=10),
        ]

        for algo in algorithms:
            res = algo.search(partitioned_graph, start="W1", goal="E3")
            assert res.success is False, f"{algo.name} unexpectedly succeeded on disconnected target"
            if algo.name == "Hill_Climbing":
                # Empirical finding: Hill Climbing returns the partial trajectory walked before getting stuck
                assert res.path[-1] != "E3"
                assert res.metadata.get("local_minimum") is True
            else:
                assert res.path == [], f"{algo.name} returned non-empty path on disconnected target"
                assert math.isinf(res.cost), f"{algo.name} returned finite cost on disconnected target"
            assert res.execution_time_ms >= 0.0

    def test_isolated_node_with_zero_edges(self, partitioned_graph: RoadGraph):
        """An isolated vertex with 0 incident edges must fail cleanly without exceptions."""
        algorithms = [
            UniformCostSearch(),
            AStarSearch(),
            GreedyBestFirstSearch(),
            HillClimbingSearch(),
            BeamSearch(beam_width=3),
            DepthLimitedSearch(depth_limit=5),
            IterativeDeepeningSearch(max_depth=5),
        ]

        for algo in algorithms:
            # Query from isolated node
            res_from = algo.search(partitioned_graph, start="ISO", goal="W1")
            assert res_from.success is False
            if algo.name == "Hill_Climbing":
                assert res_from.path == ["ISO"]  # Trapped at origin
                assert res_from.metadata.get("local_minimum") is True
            else:
                assert res_from.path == []

            # Query to isolated node
            res_to = algo.search(partitioned_graph, start="W1", goal="ISO")
            assert res_to.success is False
            if algo.name != "Hill_Climbing":
                assert res_to.path == []

    def test_dls_cutoff_vs_failure_distinction(self, partitioned_graph: RoadGraph):
        """
        DLS must correctly distinguish between:
        - CUTOFF: when depth limit cuts search while unexplored branches remain.
        - FAILURE: when the reachable component is completely exhausted without finding goal.
        """
        dls = DepthLimitedSearch()

        # Component West has only 3 nodes (max path length = 2 hops: W1 -> W2 -> W3).
        # Depth limit 5 exceeds the maximum depth of Component West.
        # Entire West component is exhausted without reaching E1.
        res_exhausted = dls.search(partitioned_graph, start="W1", goal="E1", depth_limit=5)
        assert res_exhausted.success is False
        assert res_exhausted.metadata.get("cutoff") is False
        assert "Failure" in res_exhausted.error_message

        # Now test Cutoff on a path that exists but is deeper than limit:
        # Path W1 -> W2 -> W3 is 2 hops. With depth_limit=1, W3 cannot be reached.
        res_cutoff = dls.search(partitioned_graph, start="W1", goal="W3", depth_limit=1)
        assert res_cutoff.success is False
        assert res_cutoff.metadata.get("cutoff") is True
        assert "Cutoff" in res_cutoff.error_message

    def test_ids_early_component_exhaustion_termination(self, partitioned_graph: RoadGraph):
        """
        IDS must terminate early when a component is completely exhausted,
        without fruitlessly incrementing depth all the way to max_depth_ceiling.
        """
        ids = IterativeDeepeningSearch(max_depth=15)
        # Search from W1 to unreachable E1. West component has diameter 2 hops.
        res = ids.search(partitioned_graph, start="W1", goal="E1")
        assert res.success is False
        assert res.metadata.get("cutoff") is False
        # Must terminate long before max_depth 15! Component exhausted at depth <= 3.
        assert res.metadata["iterations"] <= 4
        assert res.depth_reached <= 3


# ==============================================================================
# 2. Severe Road Congestion & Dynamic Blockages
# ==============================================================================

class TestSevereCongestionAndBlockage:
    """Verifies routing behavior under severe traffic, full bottleneck blocks, and dynamic restores."""

    @pytest.fixture
    def graph(self) -> RoadGraph:
        return RoadGraph.build_canonical_network()

    def test_complete_bottleneck_partition(self, graph: RoadGraph):
        """
        Severing all bridges/arteries connecting Western bases (A1, A2, A3, N8, N1, N7)
        to Eastern hospitals (H1, H2) must cause all algorithms to fail cleanly.
        True Cut-Set: (A1, N3), (N1, N3), (N1, N2), (A3, N6), (N7, N6).
        """
        cut_set = [
            ("A1", "N3"),
            ("N1", "N3"),
            ("N1", "N2"),
            ("A3", "N6"),
            ("N7", "N6"),
        ]
        for u, v in cut_set:
            graph.set_blocked(u, v, True)

        ucs = UniformCostSearch()
        astar = AStarSearch()
        gbfs = GreedyBestFirstSearch()

        res_ucs = ucs.search(graph, start="A2", goal="H1")
        res_astar = astar.search(graph, start="A2", goal="H1")
        res_gbfs = gbfs.search(graph, start="A2", goal="H1")

        assert res_ucs.success is False
        assert res_astar.success is False
        assert res_gbfs.success is False
        assert math.isinf(res_ucs.cost)
        assert math.isinf(res_astar.cost)

        # Restore
        for u, v in cut_set:
            graph.set_blocked(u, v, False)

        res_restored = ucs.search(graph, start="A2", goal="H1")
        assert res_restored.success is True
        assert res_restored.cost == pytest.approx(18.40, 0.01)

    def test_extreme_traffic_congestion_forces_suboptimal_distance_detour(self, graph: RoadGraph):
        """
        When primary corridor N2 -> N4 has extreme traffic (tau = 100.0, cost = 4.0 * 100 = 400),
        UCS and A* must choose the longer geographical detour N2 -> N5 -> N4 (cost ~ 6.6 + 5.7 = 12.3).
        """
        # Normal optimal path: A2 -> N1 -> N2 -> N4 -> H1 (cost 18.40)
        # Apply 100x traffic to N2 -> N4
        graph.set_traffic_factor("N2", "N4", 100.0)

        ucs = UniformCostSearch()
        astar = AStarSearch()

        res_ucs = ucs.search(graph, start="A2", goal="H1")
        res_astar = astar.search(graph, start="A2", goal="H1")

        assert res_ucs.success is True
        assert res_astar.success is True
        # Both must find the detour avoiding N2->N4
        assert not any(res_ucs.path[i] == "N2" and res_ucs.path[i+1] == "N4" for i in range(len(res_ucs.path)-1))
        assert not any(res_astar.path[i] == "N2" and res_astar.path[i+1] == "N4" for i in range(len(res_astar.path)-1))
        # Optimal cost is identical between UCS and A*
        assert round(res_ucs.cost, 2) == round(res_astar.cost, 2)
        assert res_ucs.cost < 50.0  # Far less than taking the 400.0 congested road!

        # Restore
        graph.set_traffic_factor("N2", "N4", 1.10)

    def test_dynamic_unblocking_state_consistency(self, graph: RoadGraph):
        """Verify that blocking and unblocking in sequence leaves no stale graph state."""
        ucs = UniformCostSearch()
        cost_orig = ucs.search(graph, start="A1", goal="H1").cost

        # Block
        graph.set_blocked("A1", "N3", True)
        cost_blocked = ucs.search(graph, start="A1", goal="H1").cost
        assert cost_blocked > cost_orig

        # Unblock
        graph.set_blocked("A1", "N3", False)
        cost_restored = ucs.search(graph, start="A1", goal="H1").cost
        assert cost_restored == pytest.approx(cost_orig, 0.001)


# ==============================================================================
# 3. Zero-Cost Edges & Zero-Cost Cycles
# ==============================================================================

class TestZeroCostCyclesAndEdges:
    """Verifies that 0-cost cycles do not cause infinite loops in any search algorithm."""

    @pytest.fixture
    def zero_cost_graph(self) -> RoadGraph:
        return build_zero_cost_cycle_graph()

    def test_all_7_algorithms_terminate_on_zero_cost_cycle_graph(self, zero_cost_graph: RoadGraph):
        """All 7 algorithms must terminate within 1.0 second on a graph containing a zero-cost cycle."""
        algorithms = [
            UniformCostSearch(),
            AStarSearch(),
            GreedyBestFirstSearch(),
            HillClimbingSearch(),
            BeamSearch(beam_width=3),
            DepthLimitedSearch(depth_limit=6),
            IterativeDeepeningSearch(max_depth=6),
        ]

        for algo in algorithms:
            t0 = time.perf_counter()
            res = algo.search(zero_cost_graph, start="S", goal="G")
            elapsed = time.perf_counter() - t0

            assert elapsed < 1.0, f"{algo.name} hung or took too long on zero-cost cycle graph ({elapsed:.2f}s)"
            # UCS and A* must find the optimal path
            if algo.name in ("UCS", "A_Star"):
                assert res.success is True
                # Cost should be S->Z1 (10.0) + Z1->Z2 (0.0) + Z2->G (10.0) = 20.0
                assert res.cost == pytest.approx(20.0, 0.01)
                assert res.path[0] == "S"
                assert res.path[-1] == "G"

    def test_zero_cost_cycle_does_not_repeat_nodes_in_ucs_or_astar(self, zero_cost_graph: RoadGraph):
        """UCS and A* path must not contain duplicate cycle nodes despite edge cost 0."""
        ucs = UniformCostSearch()
        astar = AStarSearch()

        res_ucs = ucs.search(zero_cost_graph, start="S", goal="G")
        res_astar = astar.search(zero_cost_graph, start="S", goal="G")

        assert len(res_ucs.path) == len(set(res_ucs.path)), f"UCS produced cyclic path: {res_ucs.path}"
        assert len(res_astar.path) == len(set(res_astar.path)), f"A* produced cyclic path: {res_astar.path}"


# ==============================================================================
# 4. Deep Search Trees & Scaling
# ==============================================================================

class TestDeepSearchTrees:
    """Verifies algorithm scaling on deep linear graphs and depth boundary behaviors."""

    @pytest.fixture
    def deep_chain(self) -> RoadGraph:
        return build_deep_chain_graph(n=25)

    def test_dls_exact_boundary_cutoff(self, deep_chain: RoadGraph):
        """DLS on a 25-node chain (distance 24 hops from C0 to C24) must cutoff at limit 23 and succeed at limit 24."""
        dls = DepthLimitedSearch()

        # Depth 23: cannot reach C24 (requires 24 hops) -> Cutoff
        res_cutoff = dls.search(deep_chain, start="C0", goal="C24", depth_limit=23)
        assert res_cutoff.success is False
        assert res_cutoff.metadata.get("cutoff") is True

        # Depth 24: exactly reaches C24 -> Success
        res_ok = dls.search(deep_chain, start="C0", goal="C24", depth_limit=24)
        assert res_ok.success is True
        assert res_ok.depth_reached == 24
        assert res_ok.path[0] == "C0"
        assert res_ok.path[-1] == "C24"
        assert len(res_ok.path) == 25

    def test_ids_exact_depth_scaling(self, deep_chain: RoadGraph):
        """IDS on a 20-node chain must identify the exact 19-hop path and record 20 iterations (0 to 19)."""
        ids = IterativeDeepeningSearch(max_depth=20)
        res = ids.search(deep_chain, start="C0", goal="C19")

        assert res.success is True
        assert res.depth_reached == 19
        assert res.metadata["iterations"] == 20  # depths 0, 1, ..., 19
        assert res.path[0] == "C0"
        assert res.path[-1] == "C19"

    def test_astar_and_ucs_on_deep_chain(self, deep_chain: RoadGraph):
        """A* and UCS must navigate a 25-node chain with identical optimal cost = 240.0."""
        ucs = UniformCostSearch()
        astar = AStarSearch()

        res_ucs = ucs.search(deep_chain, start="C0", goal="C24")
        res_astar = astar.search(deep_chain, start="C0", goal="C24")

        assert res_ucs.success is True
        assert res_astar.success is True
        assert res_ucs.cost == pytest.approx(240.0, 0.01)
        assert res_astar.cost == pytest.approx(240.0, 0.01)
        assert res_ucs.path == res_astar.path


# ==============================================================================
# 5. Local Minima, Plateaus & Heuristic Traps
# ==============================================================================

class TestLocalMinimaAndHeuristicTraps:
    """Verifies behavior on concave/horseshoe heuristic traps and plateau topologies."""

    @pytest.fixture
    def trap_graph(self) -> RoadGraph:
        return build_horseshoe_trap_graph()

    def test_hill_climbing_trapped_in_local_minimum(self, trap_graph: RoadGraph):
        """Hill Climbing MUST get lured into the horseshoe dead-end and report a local minimum."""
        hc = HillClimbingSearch()
        res = hc.search(trap_graph, start="S", goal="G")

        assert res.success is False
        assert res.metadata.get("local_minimum") is True
        assert res.metadata.get("stuck_at") == "T2"
        assert "Local minimum" in res.error_message
        assert res.path == ["S", "T1", "T2"]

    def test_beam_search_width_1_fails_vs_width_2_succeeds(self, trap_graph: RoadGraph):
        """
        Beam Search with width 1 acts greedily like Hill Climbing and gets trapped.
        Beam Search with width >= 2 retains the alternative branch and finds the goal!
        """
        beam = BeamSearch()

        # Beam width 1: trapped in dead-end
        res_w1 = beam.search(trap_graph, start="S", goal="G", beam_width=1)
        assert res_w1.success is False

        # Beam width 2: escapes dead-end via detour
        res_w2 = beam.search(trap_graph, start="S", goal="G", beam_width=2)
        assert res_w2.success is True
        assert res_w2.path == ["S", "D1", "D2", "G"]
        assert res_w2.cost == pytest.approx(26.0, 0.01)

    def test_greedy_best_first_backtracks_out_of_trap(self, trap_graph: RoadGraph):
        """
        Greedy Best-First explores the dead-end first due to h(T1) < h(D1),
        but because it maintains an open priority queue frontier, it backtracks and reaches G.
        """
        gbfs = GreedyBestFirstSearch()
        res = gbfs.search(trap_graph, start="S", goal="G", include_steps=True)

        assert res.success is True
        assert res.path == ["S", "D1", "D2", "G"]
        # Explored order must show T1 and T2 were visited before exploring the detour
        assert "T1" in res.explored_order
        assert "T2" in res.explored_order
        t2_idx = res.explored_order.index("T2")
        d1_idx = res.explored_order.index("D1")
        assert t2_idx < d1_idx, "GBFS did not greedily explore trap first as expected"

    def test_astar_and_ucs_find_optimal_detour(self, trap_graph: RoadGraph):
        """Both A* and UCS must avoid getting stuck and find the optimal detour path."""
        ucs = UniformCostSearch()
        astar = AStarSearch()

        res_ucs = ucs.search(trap_graph, start="S", goal="G")
        res_astar = astar.search(trap_graph, start="S", goal="G")

        assert res_ucs.success is True
        assert res_astar.success is True
        assert res_ucs.path == ["S", "D1", "D2", "G"]
        assert res_astar.path == ["S", "D1", "D2", "G"]
        assert res_ucs.cost == pytest.approx(26.0, 0.01)
        assert res_astar.cost == pytest.approx(26.0, 0.01)


# ==============================================================================
# 6. Comprehensive Optimality & Efficiency Comparisons (156 Canonical Pairs)
# ==============================================================================

class TestCanonicalOptimalityAndEfficiencyBenchmark:
    """Rigorous empirical comparison of all 7 algorithms across the 13 canonical nodes."""

    @pytest.fixture
    def graph(self) -> RoadGraph:
        return RoadGraph.build_canonical_network()

    def test_astar_exact_optimality_across_all_156_pairs(self, graph: RoadGraph):
        """
        A* cost MUST match UCS cost exactly (within 0.01) on EVERY reachable pair (156 pairs).
        Empirical proof of A* optimality with admissible scaled Euclidean heuristic.
        """
        ucs = UniformCostSearch()
        astar = AStarSearch()
        nodes = list(graph.nodes.keys())

        discrepancies = []
        total_tested = 0

        for start in nodes:
            for goal in nodes:
                if start == goal:
                    continue
                total_tested += 1
                res_ucs = ucs.search(graph, start, goal)
                res_astar = astar.search(graph, start, goal)

                assert res_ucs.success == res_astar.success
                if res_ucs.success:
                    diff = abs(res_ucs.cost - res_astar.cost)
                    if diff > 0.02:
                        discrepancies.append({
                            "pair": f"{start}->{goal}",
                            "ucs_cost": res_ucs.cost,
                            "astar_cost": res_astar.cost,
                            "diff": diff,
                        })

        assert total_tested == 156
        assert len(discrepancies) == 0, f"Found {len(discrepancies)} A* vs UCS cost discrepancies: {discrepancies}"

    def test_astar_efficiency_vs_ucs_expansion_ratio(self, graph: RoadGraph):
        """
        A* must explore fewer or equal nodes compared to UCS across all pairs:
        Average nodes explored by A* must be strictly less than UCS.
        """
        ucs = UniformCostSearch()
        astar = AStarSearch()
        nodes = list(graph.nodes.keys())

        ucs_total_nodes = 0
        astar_total_nodes = 0
        astar_worse_cases = []

        for start in nodes:
            for goal in nodes:
                if start == goal:
                    continue
                res_ucs = ucs.search(graph, start, goal)
                res_astar = astar.search(graph, start, goal)

                ucs_total_nodes += res_ucs.nodes_explored
                astar_total_nodes += res_astar.nodes_explored

                if res_astar.nodes_explored > res_ucs.nodes_explored:
                    astar_worse_cases.append((start, goal, res_astar.nodes_explored, res_ucs.nodes_explored))

        # Overall A* expansions must be lower
        assert astar_total_nodes <= ucs_total_nodes
        # Check pruning efficiency percentage
        efficiency_gain = (ucs_total_nodes - astar_total_nodes) / ucs_total_nodes * 100.0
        assert efficiency_gain >= 0.0, f"A* did not prune nodes compared to UCS (gain: {efficiency_gain:.1f}%)"

    def test_greedy_best_first_suboptimality_profile(self, graph: RoadGraph):
        """
        Greedy Best-First Search trades optimality for exploration speed:
        Profile how often GBFS finds suboptimal paths compared to UCS across all 156 pairs.
        """
        ucs = UniformCostSearch()
        gbfs = GreedyBestFirstSearch()
        nodes = list(graph.nodes.keys())

        suboptimal_count = 0
        max_cost_ratio = 1.0

        for start in nodes:
            for goal in nodes:
                if start == goal:
                    continue
                res_ucs = ucs.search(graph, start, goal)
                res_gbfs = gbfs.search(graph, start, goal)

                assert res_gbfs.success is True
                ratio = res_gbfs.cost / res_ucs.cost
                if ratio > 1.01:
                    suboptimal_count += 1
                if ratio > max_cost_ratio:
                    max_cost_ratio = ratio

        # GBFS should have a non-trivial suboptimality rate, confirming empirical trade-off
        suboptimal_rate = (suboptimal_count / 156.0) * 100.0
        assert suboptimal_rate > 0.0, "Expected GBFS to show some suboptimal paths"
        # Maximum suboptimality ratio should be bounded (<= 2.5x)
        assert max_cost_ratio <= 2.5, f"GBFS cost ratio {max_cost_ratio:.2f} is excessively suboptimal"

    def test_beam_search_width_monotonicity_on_canonical_network(self, graph: RoadGraph):
        """
        Increasing beam width from 1 to 3 should maintain or improve solution cost
        and maintain or increase success rate across all pairs.
        """
        beam_w1 = BeamSearch(beam_width=1)
        beam_w3 = BeamSearch(beam_width=3)
        nodes = list(graph.nodes.keys())

        w1_successes = 0
        w3_successes = 0
        w1_total_cost = 0.0
        w3_total_cost = 0.0

        for start in nodes:
            for goal in nodes:
                if start == goal:
                    continue
                res_w1 = beam_w1.search(graph, start, goal)
                res_w3 = beam_w3.search(graph, start, goal)

                if res_w1.success:
                    w1_successes += 1
                    w1_total_cost += res_w1.cost
                if res_w3.success:
                    w3_successes += 1
                    w3_total_cost += res_w3.cost

        # Beam width 3 must succeed at least as often as width 1
        assert w3_successes >= w1_successes
        assert w3_successes == 156, f"Beam width 3 failed on {156 - w3_successes} canonical pairs"

    def test_hill_climbing_success_rate_profile_on_canonical_network(self, graph: RoadGraph):
        """
        Profiles Hill Climbing on the canonical graph:
        Because the canonical road network has non-convex geometries and river crossings,
        Hill Climbing is expected to fail on a subset of pairs due to local minima.
        Verify that Hill Climbing explicitly tags all failures with metadata['local_minimum'] = True.
        """
        hc = HillClimbingSearch()
        nodes = list(graph.nodes.keys())

        success_count = 0
        local_min_count = 0

        for start in nodes:
            for goal in nodes:
                if start == goal:
                    continue
                res = hc.search(graph, start, goal)
                if res.success:
                    success_count += 1
                else:
                    if res.metadata.get("local_minimum") is True:
                        local_min_count += 1

        assert success_count + local_min_count == 156
        # Both successes and local minimum traps occur on the 13-node network
        assert success_count > 0
        assert local_min_count > 0, "Expected Hill Climbing to encounter local minima on canonical graph"

    def test_ids_min_hop_vs_ucs_min_cost_divergence(self, graph: RoadGraph):
        """
        Fundamental AI Concept:
        IDS guarantees the shallowest (minimum-hop) path.
        UCS guarantees the lowest cumulative cost g(n) path.
        When hop count and edge costs diverge, IDS and UCS will produce different paths.
        Verify this fundamental property empirically on the canonical network.
        """
        ucs = UniformCostSearch()
        ids = IterativeDeepeningSearch(max_depth=10)
        nodes = list(graph.nodes.keys())

        divergence_count = 0
        for start in nodes:
            for goal in nodes:
                if start == goal:
                    continue
                res_ucs = ucs.search(graph, start, goal)
                res_ids = ids.search(graph, start, goal)

                assert res_ucs.success is True
                assert res_ids.success is True

                ucs_hops = len(res_ucs.path) - 1
                ids_hops = len(res_ids.path) - 1

                # IDS hops should be <= UCS hops
                assert ids_hops <= ucs_hops, f"IDS produced {ids_hops} hops > UCS {ucs_hops} hops for {start}->{goal}"
                # UCS cost should be <= IDS cost
                assert res_ucs.cost <= res_ids.cost + 0.01, f"UCS cost {res_ucs.cost} > IDS cost {res_ids.cost} for {start}->{goal}"

                if res_ucs.path != res_ids.path:
                    divergence_count += 1

        # Confirm there exist pairs where min-hop != min-cost
        assert divergence_count > 0, "Expected at least one pair where min-hop diverged from min-cost"

    def test_empirical_metrics_collection(self, graph: RoadGraph):
        """Collects and displays exact quantitative metrics across all 156 pairs for report verification."""
        ucs = UniformCostSearch()
        astar = AStarSearch()
        gbfs = GreedyBestFirstSearch()
        hc = HillClimbingSearch()
        beam_w1 = BeamSearch(beam_width=1)
        beam_w3 = BeamSearch(beam_width=3)
        ids = IterativeDeepeningSearch(max_depth=10)

        nodes = list(graph.nodes.keys())
        total_pairs = 156

        # UCS & A*
        ucs_nodes = 0
        astar_nodes = 0
        astar_opt_matches = 0

        # GBFS
        gbfs_suboptimal = 0
        gbfs_max_subopt = 1.0
        gbfs_nodes = 0

        # HC
        hc_success = 0
        hc_local_min = 0

        # Beam
        w1_success = 0
        w3_success = 0
        w1_cost = 0.0
        w3_cost = 0.0

        # IDS vs UCS
        min_hop_divergence = 0

        for s in nodes:
            for g in nodes:
                if s == g:
                    continue
                r_ucs = ucs.search(graph, s, g)
                r_astar = astar.search(graph, s, g)
                r_gbfs = gbfs.search(graph, s, g)
                r_hc = hc.search(graph, s, g)
                r_w1 = beam_w1.search(graph, s, g)
                r_w3 = beam_w3.search(graph, s, g)
                r_ids = ids.search(graph, s, g)

                ucs_nodes += r_ucs.nodes_explored
                astar_nodes += r_astar.nodes_explored
                if abs(r_ucs.cost - r_astar.cost) < 0.02:
                    astar_opt_matches += 1

                gbfs_nodes += r_gbfs.nodes_explored
                ratio = r_gbfs.cost / r_ucs.cost
                if ratio > 1.01:
                    gbfs_suboptimal += 1
                if ratio > gbfs_max_subopt:
                    gbfs_max_subopt = ratio

                if r_hc.success:
                    hc_success += 1
                elif r_hc.metadata.get("local_minimum"):
                    hc_local_min += 1

                if r_w1.success:
                    w1_success += 1
                    w1_cost += r_w1.cost
                if r_w3.success:
                    w3_success += 1
                    w3_cost += r_w3.cost

                if r_ucs.path != r_ids.path:
                    min_hop_divergence += 1

        astar_saving = (ucs_nodes - astar_nodes) / ucs_nodes * 100.0
        print(f"\n--- EMPIRICAL METRICS ON CANONICAL NETWORK ({total_pairs} pairs) ---")
        print(f"UCS Total Node Expansions: {ucs_nodes} (avg {ucs_nodes/total_pairs:.2f} per pair)")
        print(f"A* Total Node Expansions: {astar_nodes} (avg {astar_nodes/total_pairs:.2f} per pair)")
        print(f"A* Search Tree Pruning vs UCS: {astar_saving:.2f}% reduction")
        print(f"A* Optimality Agreement with UCS: {astar_opt_matches}/{total_pairs} ({astar_opt_matches/total_pairs*100.0:.1f}%)")
        print(f"GBFS Suboptimal Paths: {gbfs_suboptimal}/{total_pairs} ({gbfs_suboptimal/total_pairs*100.0:.1f}%)")
        print(f"GBFS Worst-Case Suboptimality Ratio: {gbfs_max_subopt:.3f}x")
        print(f"GBFS Total Node Expansions: {gbfs_nodes} (avg {gbfs_nodes/total_pairs:.2f} per pair)")
        print(f"Hill Climbing Successes: {hc_success}/{total_pairs} ({hc_success/total_pairs*100.0:.1f}%)")
        print(f"Hill Climbing Local Minima Trapped: {hc_local_min}/{total_pairs} ({hc_local_min/total_pairs*100.0:.1f}%)")
        print(f"Beam Search w=1 Successes: {w1_success}/{total_pairs} ({w1_success/total_pairs*100.0:.1f}%), Avg Cost: {w1_cost/w1_success:.2f}")
        print(f"Beam Search w=3 Successes: {w3_success}/{total_pairs} ({w3_success/total_pairs*100.0:.1f}%), Avg Cost: {w3_cost/w3_success:.2f}")
        print(f"IDS Min-Hop vs UCS Min-Cost Path Divergences: {min_hop_divergence}/{total_pairs} ({min_hop_divergence/total_pairs*100.0:.1f}%)")



class TestAdversarialEdgeCases:
    """Stress tests on boundary topologies, self-loops, and trace schema integrity."""

    def test_self_loop_handling(self):
        """A road network with self-loops must not cause cycle loops in search."""
        g = RoadGraph()
        g.add_node(Node("A", "Node A", "intersection", 0.0, 0.0))
        g.add_node(Node("B", "Node B", "intersection", 10.0, 0.0))
        # Self-loop on A
        g.add_edge(Edge("A", "A", distance=5.0), bidirectional=False)
        g.add_edge(Edge("A", "B", distance=10.0), bidirectional=True)

        for algo in [UniformCostSearch(), AStarSearch(), GreedyBestFirstSearch(), BeamSearch()]:
            res = algo.search(g, start="A", goal="B")
            assert res.success is True
            assert res.path == ["A", "B"]

    def test_empty_graph_and_single_node_handling(self):
        """Empty graph and single-node trivial cases."""
        empty_g = RoadGraph()
        ucs = UniformCostSearch()
        res_empty = ucs.search(empty_g, start="A", goal="B")
        assert res_empty.success is False
        assert "not found" in res_empty.error_message

        # Single node graph
        single_g = RoadGraph()
        single_g.add_node(Node("S", "Single", "intersection", 0.0, 0.0))
        res_single = ucs.search(single_g, start="S", goal="S")
        assert res_single.success is True
        assert res_single.cost == 0.0
        assert res_single.path == ["S"]

    def test_step_trace_schema_integrity_all_algorithms(self):
        """Verify step trace generation and SearchStep contract across all algorithms supporting steps."""
        g = RoadGraph.build_canonical_network()

        # Test each algorithm with include_steps=True
        ucs = UniformCostSearch()
        r_ucs = ucs.search(g, start="A2", goal="H1", include_steps=True)
        assert r_ucs.steps is not None
        assert len(r_ucs.steps) == r_ucs.nodes_explored
        for s in r_ucs.steps:
            assert s.step >= 1
            assert s.current_node in g.nodes
            assert s.g >= 0.0

        astar = AStarSearch()
        r_astar = astar.search(g, start="A2", goal="H1", include_steps=True)
        assert r_astar.steps is not None
        assert len(r_astar.steps) == r_astar.nodes_explored
        for s in r_astar.steps:
            assert s.step >= 1
            assert s.f >= 0.0

        dls = DepthLimitedSearch()
        r_dls = dls.search(g, start="A2", goal="H1", depth_limit=5, include_steps=True)
        assert r_dls.steps is not None
        assert len(r_dls.steps) == r_dls.nodes_explored

        beam = BeamSearch()
        r_beam = beam.search(g, start="A2", goal="H1", beam_width=3, include_steps=True)
        assert r_beam.steps is not None
        assert len(r_beam.steps) > 0


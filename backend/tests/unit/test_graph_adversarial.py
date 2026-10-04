"""
Adversarial and Stress-Test Harness for ResQ-AI Canonical 13-Node Road Graph.
Milestone 1 Empirical Verification:
- Triangle inequality & heuristic consistency across all 42 directed edges and all goals.
- Strict heuristic admissibility h(u, g) <= h*(u, g).
- Blocked corridor dynamics and cost/neighbor restoration.
- Extreme traffic factor (tau >> 1.0) and risk factor (r = 1.0) scaling.
- Disconnected / isolated node handling and graph partitioning.
- Cycle handling, loop traversals, and non-adjacent path costs.
"""

import math
import heapq
import pytest

from app.search.graph import RoadGraph, Node, Edge


def compute_all_pairs_shortest_paths(graph: RoadGraph) -> dict:
    """Computes exact shortest path costs between all node pairs via Dijkstra."""
    all_dists = {}
    for start in graph.nodes:
        dist = {n: float("inf") for n in graph.nodes}
        dist[start] = 0.0
        pq = [(0.0, start)]
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist[u]:
                continue
            for v in graph.get_unblocked_neighbors(u):
                edge_cost = graph.calculate_edge_cost(u, v)
                if dist[u] + edge_cost < dist[v]:
                    dist[v] = dist[u] + edge_cost
                    heapq.heappush(pq, (dist[v], v))
        all_dists[start] = dist
    return all_dists


def test_heuristic_consistency_all_42_edges_all_13_goals():
    """
    Mathematically verify the triangle inequality (consistency/monotonicity):
        h(u, g) <= c(u, v) + h(v, g)
    for ALL 42 directed edges and ALL 13 goals (including H1, H2, N1..N8, A1..A3).
    Total evaluated pairs: 42 * 13 = 546 edge-goal combinations.
    """
    graph = RoadGraph.build_canonical_network()
    all_goals = list(graph.nodes.keys())

    violations = []
    min_slack = float("inf")
    evaluated_count = 0

    for goal in all_goals:
        for u in graph.adjacency:
            for v, edge in graph.adjacency[u].items():
                if edge.is_blocked:
                    continue
                h_u = graph.heuristic(u, goal, scale_factor=0.20)
                h_v = graph.heuristic(v, goal, scale_factor=0.20)
                edge_cost = edge.cost()
                
                # Consistency condition: slack = c(u, v) + h(v, g) - h(u, g) >= 0
                slack = edge_cost + h_v - h_u
                evaluated_count += 1

                if slack < -1e-9:
                    violations.append({
                        "u": u,
                        "v": v,
                        "goal": goal,
                        "h_u": h_u,
                        "h_v": h_v,
                        "cost": edge_cost,
                        "slack": slack,
                    })
                if slack < min_slack:
                    min_slack = slack

    assert evaluated_count == 42 * 13, f"Expected 546 evaluations, got {evaluated_count}"
    assert len(violations) == 0, f"Found {len(violations)} consistency violations: {violations}"
    assert min_slack >= 0.118, f"Minimum slack {min_slack} is unexpectedly low"


def test_heuristic_strict_admissibility_all_pairs():
    """
    Verify strict admissibility:
        h(u, g) <= h*(u, g)
    for all 169 (u, g) pairs in the canonical graph.
    Also verify strictness: h(u, g) < h*(u, g) whenever u != g.
    """
    graph = RoadGraph.build_canonical_network()
    shortest_paths = compute_all_pairs_shortest_paths(graph)

    violations = []
    max_ratio = 0.0
    min_positive_slack = float("inf")

    for u in graph.nodes:
        for g in graph.nodes:
            h_star = shortest_paths[u][g]
            h_val = graph.heuristic(u, g, scale_factor=0.20)

            # Strict admissibility: h(u, g) <= h*(u, g)
            slack = h_star - h_val
            if slack < -1e-9:
                violations.append((u, g, h_val, h_star, slack))

            if u == g:
                assert h_val == 0.0
                assert h_star == 0.0
            else:
                assert h_val > 0.0
                assert h_star > 0.0
                ratio = h_val / h_star
                if ratio > max_ratio:
                    max_ratio = ratio
                if slack < min_positive_slack:
                    min_positive_slack = slack

    assert len(violations) == 0, f"Admissibility violations found: {violations}"
    assert max_ratio <= 1.0, f"Max heuristic to h* ratio {max_ratio} exceeds 1.0"
    assert min_positive_slack > 0.10, f"Min positive slack {min_positive_slack} too close to zero"


def test_theoretical_upper_bound_scaling_factor():
    """
    Verify that scale_factor=0.20 is below the exact theoretical threshold s* = min(c(u,v)/D(u,v)).
    Empirically confirms that s > s* breaks consistency on edge (N5, N6).
    """
    graph = RoadGraph.build_canonical_network()

    # Find the critical edge that limits scale_factor
    min_ratio = float("inf")
    critical_edge = None
    for u in graph.adjacency:
        for v, edge in graph.adjacency[u].items():
            d_euclid = graph.euclidean_distance(u, v)
            ratio = edge.cost() / d_euclid
            if ratio < min_ratio:
                min_ratio = ratio
                critical_edge = (u, v)

    assert critical_edge == ("N5", "N6") or critical_edge == ("N6", "N5")
    assert pytest.approx(min_ratio, 0.001) == 0.2036

    # Verify standard scale factor 0.20 is safely below 0.2036
    assert 0.20 < min_ratio

    # Adversarial check: verify that an aggressive scale factor (e.g. 0.25) VIOLATES consistency
    violating_scale = 0.25
    h_u = graph.heuristic("N5", "N6", scale_factor=violating_scale)
    h_v = graph.heuristic("N6", "N6", scale_factor=violating_scale)  # 0.0
    cost = graph.calculate_edge_cost("N5", "N6")
    # For goal N6: h(N5) - h(N6) > cost
    assert h_u - h_v > cost, "Aggressive scale factor 0.25 should fail consistency on critical edge"


def test_dynamic_corridor_blockage_and_unblocking_lifecycle():
    """
    Test dynamic blockage lifecycle:
    1. Edge cost initially finite.
    2. Blocking immediately sets cost to infinity in BOTH directions.
    3. Unblocked neighbor queries exclude blocked edge.
    4. Path costs and times containing blocked edge become infinity.
    5. Unblocking immediately restores exact original cost and travel time.
    """
    graph = RoadGraph.build_canonical_network()
    u, v = "N1", "N2"

    orig_edge_uv = graph.get_edge(u, v)
    orig_edge_vu = graph.get_edge(v, u)
    initial_cost = orig_edge_uv.cost()
    initial_time = orig_edge_uv.travel_time_minutes()
    assert initial_cost == pytest.approx(4.84, 0.01)

    # 1. Dynamically block corridor
    graph.set_blocked(u, v, True)

    assert orig_edge_uv.is_blocked is True
    assert orig_edge_vu.is_blocked is True
    assert math.isinf(graph.calculate_edge_cost(u, v))
    assert math.isinf(graph.calculate_edge_cost(v, u))
    assert math.isinf(orig_edge_uv.travel_time_minutes())
    assert math.isinf(orig_edge_vu.travel_time_minutes())

    assert v not in graph.get_unblocked_neighbors(u)
    assert u not in graph.get_unblocked_neighbors(v)

    canonical_path = ["A2", "N1", "N2", "N4", "H1"]
    assert math.isinf(graph.calculate_path_cost(canonical_path))
    assert math.isinf(graph.calculate_path_time(canonical_path))

    # 2. Dynamically unblock corridor
    graph.set_blocked(u, v, False)

    assert orig_edge_uv.is_blocked is False
    assert orig_edge_vu.is_blocked is False
    assert graph.calculate_edge_cost(u, v) == pytest.approx(initial_cost, 0.001)
    assert graph.calculate_edge_cost(v, u) == pytest.approx(initial_cost, 0.001)
    assert orig_edge_uv.travel_time_minutes() == pytest.approx(initial_time, 0.001)
    assert orig_edge_vu.travel_time_minutes() == pytest.approx(initial_time, 0.001)

    assert v in graph.get_unblocked_neighbors(u)
    assert u in graph.get_unblocked_neighbors(v)

    assert graph.calculate_path_cost(canonical_path) == pytest.approx(18.40, 0.01)


def test_multiple_simultaneous_blockages():
    """Verify that multiple simultaneous blockages correctly compound on paths."""
    graph = RoadGraph.build_canonical_network()

    # Block both primary bridge and northern detour
    graph.set_blocked("N1", "N2", True)
    graph.set_blocked("N1", "N3", True)

    # Primary path A2-N1-N2-N4-H1 blocked
    assert math.isinf(graph.calculate_path_cost(["A2", "N1", "N2", "N4", "H1"]))
    # Bypass path A2-N1-N3-N4-H1 also blocked
    assert math.isinf(graph.calculate_path_cost(["A2", "N1", "N3", "N4", "H1"]))

    # Unblocking N1-N3 restores bypass path
    graph.set_blocked("N1", "N3", False)
    assert graph.calculate_path_cost(["A2", "N1", "N3", "N4", "H1"]) == pytest.approx(21.375, 0.01)


def test_extreme_traffic_and_risk_factors():
    """
    Test extreme traffic factors tau >> 1.0 and risk factor r = 1.0.
    Verifies linear scaling, decoupling of risk from travel time, and bidirectional propagation.
    """
    graph = RoadGraph.build_canonical_network()
    u, v = "N2", "N4"
    edge = graph.get_edge(u, v)
    base_dist = edge.distance
    base_speed = edge.speed_limit

    # 1. Extreme traffic factor tau = 10.0
    graph.set_traffic_factor(u, v, 10.0)
    assert edge.traffic_factor == 10.0
    assert graph.get_edge(v, u).traffic_factor == 10.0
    expected_cost_tau10 = base_dist * 10.0 * (1.0 + edge.risk_factor)
    assert edge.cost() == pytest.approx(expected_cost_tau10, 0.001)
    expected_time_tau10 = (base_dist / base_speed) * 60.0 * 10.0
    assert edge.travel_time_minutes() == pytest.approx(expected_time_tau10, 0.001)

    # 2. Maximum risk factor r = 1.0 (doubles cost)
    graph.set_risk_factor(u, v, 1.0)
    assert edge.risk_factor == 1.0
    assert graph.get_edge(v, u).risk_factor == 1.0
    expected_cost_r1 = base_dist * 10.0 * (1.0 + 1.0)
    assert edge.cost() == pytest.approx(expected_cost_r1, 0.001)

    # 3. Travel time MUST NOT depend on risk factor
    assert edge.travel_time_minutes() == pytest.approx(expected_time_tau10, 0.001)

    # 4. Astronomical traffic stress tau = 1000.0
    graph.set_traffic_factor(u, v, 1000.0)
    assert edge.cost() == pytest.approx(base_dist * 1000.0 * 2.0, 0.001)
    assert edge.travel_time_minutes() == pytest.approx((base_dist / base_speed) * 60.0 * 1000.0, 0.001)


def test_disconnected_and_isolated_node_queries():
    """
    Adversarial edge cases for non-existent and isolated vertices:
    - Missing node lookup and graceful handling
    - Explicit isolated node injection
    - Graph partitioning resulting in unreachable components
    """
    graph = RoadGraph.build_canonical_network()

    # 1. Nonexistent node queries
    assert graph.get_node("UNKNOWN_NODE") is None
    assert graph.get_neighbors("UNKNOWN_NODE") == []
    assert graph.get_unblocked_neighbors("UNKNOWN_NODE") == []
    assert math.isinf(graph.calculate_edge_cost("UNKNOWN_NODE", "N1"))
    assert math.isinf(graph.calculate_edge_cost("N1", "UNKNOWN_NODE"))
    assert graph.euclidean_distance("UNKNOWN_NODE", "N1") == 0.0
    assert graph.heuristic("UNKNOWN_NODE", "N1") == 0.0

    # set_blocked and factors on nonexistent edge should not throw exceptions
    graph.set_blocked("UNKNOWN_NODE", "N1", True)
    graph.set_traffic_factor("UNKNOWN_NODE", "N1", 2.0)
    graph.set_risk_factor("UNKNOWN_NODE", "N1", 0.5)

    # 2. Inject isolated node
    iso_node = Node("ISO_ISLAND", "Isolated Island", "intersection", 0.0, 0.0)
    graph.add_node(iso_node)

    assert graph.get_node("ISO_ISLAND") is not None
    assert graph.get_neighbors("ISO_ISLAND") == []
    assert graph.get_unblocked_neighbors("ISO_ISLAND") == []
    assert math.isinf(graph.calculate_path_cost(["ISO_ISLAND", "N1"]))
    assert math.isinf(graph.calculate_path_time(["ISO_ISLAND", "N1"]))

    # Heuristic from isolated node is purely spatial and well-defined
    expected_dist = math.sqrt((0.0 - 35.0) ** 2 + (0.0 - 55.0) ** 2)
    assert graph.euclidean_distance("ISO_ISLAND", "N1") == pytest.approx(expected_dist, 0.001)
    assert graph.heuristic("ISO_ISLAND", "N1") == pytest.approx(expected_dist * 0.20, 0.001)

    # 3. Graph partitioning: block all edges connecting A1 to the network
    # A1 is connected only to N8 and N3
    graph.set_blocked("A1", "N8", True)
    graph.set_blocked("A1", "N3", True)
    assert graph.get_unblocked_neighbors("A1") == []
    assert math.isinf(graph.calculate_path_cost(["A1", "N8", "N1", "N2", "N4", "H1"]))


def test_cycle_handling_and_path_topologies():
    """
    Stress-test path topologies:
    - Empty and 1-element paths (0.0 cost)
    - Consecutive self-loops without edges (infinite cost)
    - Cyclic loops and repeated visits
    - 100-cycle stress traversal
    """
    graph = RoadGraph.build_canonical_network()

    # Empty and single-node paths
    assert graph.calculate_path_cost([]) == 0.0
    assert graph.calculate_path_cost(["N1"]) == 0.0
    assert graph.calculate_path_time([]) == 0.0
    assert graph.calculate_path_time(["N1"]) == 0.0

    # Self-loop where no edge exists
    assert math.isinf(graph.calculate_path_cost(["N1", "N1"]))
    assert math.isinf(graph.calculate_path_time(["N1", "N1"]))

    # Cyclic paths (oscillating back and forth)
    cost_n1_n2 = graph.calculate_edge_cost("N1", "N2")
    cycle_2 = ["N1", "N2", "N1"]
    assert graph.calculate_path_cost(cycle_2) == pytest.approx(cost_n1_n2 * 2, 0.001)

    # Loop: N1 -> N2 -> N4 -> N3 -> N1
    closed_loop = ["N1", "N2", "N4", "N3", "N1"]
    loop_cost = (
        graph.calculate_edge_cost("N1", "N2")
        + graph.calculate_edge_cost("N2", "N4")
        + graph.calculate_edge_cost("N4", "N3")
        + graph.calculate_edge_cost("N3", "N1")
    )
    assert graph.calculate_path_cost(closed_loop) == pytest.approx(loop_cost, 0.001)

    # 100-cycle stress traversal
    stress_path = ["N1", "N2"] * 100
    expected_stress_cost = cost_n1_n2 * 199
    assert graph.calculate_path_cost(stress_path) == pytest.approx(expected_stress_cost, 0.01)


def test_all_42_edges_bidirectional_symmetry():
    """Verify that all 21 corridors are strictly bidirectional and symmetric."""
    graph = RoadGraph.build_canonical_network()

    for u in graph.adjacency:
        for v, edge_forward in graph.adjacency[u].items():
            edge_reverse = graph.get_edge(v, u)
            assert edge_reverse is not None, f"Missing reverse edge for ({u}, {v})"
            assert edge_forward.distance == edge_reverse.distance
            assert edge_forward.speed_limit == edge_reverse.speed_limit
            assert edge_forward.traffic_factor == edge_reverse.traffic_factor
            assert edge_forward.risk_factor == edge_reverse.risk_factor
            assert edge_forward.cost() == pytest.approx(edge_reverse.cost(), 0.001)
            assert edge_forward.travel_time_minutes() == pytest.approx(edge_reverse.travel_time_minutes(), 0.001)


def test_path_cost_monotonicity_under_traffic_increase():
    """Verify that increasing traffic factor strictly increases or maintains path cost."""
    graph = RoadGraph.build_canonical_network()
    path = ["A2", "N1", "N2", "N4", "H1"]
    base_cost = graph.calculate_path_cost(path)

    # Increase traffic on N1-N2
    graph.set_traffic_factor("N1", "N2", 1.5)
    elevated_cost = graph.calculate_path_cost(path)
    assert elevated_cost > base_cost

    # Increasing risk on N2-N4 further increases cost
    graph.set_risk_factor("N2", "N4", 0.5)
    further_elevated_cost = graph.calculate_path_cost(path)
    assert further_elevated_cost > elevated_cost

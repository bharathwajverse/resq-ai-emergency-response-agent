"""
ResQ-AI Search Algorithms Test Suite (Unified Module II & Module III).
Aggregates Uninformed Search (UCS, DLS, IDS) and Informed Search (A*, Best First, Hill Climbing, Beam Search).
"""

from tests.unit.test_search_uninformed import (
    graph,
    test_ucs_canonical_optimal_path,
    test_ucs_trivial_and_invalid_nodes,
    test_ucs_dynamic_road_blockage_and_detour,
    test_ucs_disconnected_graph_failure,
    test_dls_success_and_cutoff,
    test_dls_failure_on_unreachable_node,
    test_ids_canonical_search,
    test_ids_unreachable_node_termination,
)

from tests.unit.test_search_informed import (
    test_astar_benchmark_path_and_cost,
    test_astar_admissibility_efficiency_vs_ucs,
    test_astar_detour_when_primary_path_blocked,
    test_best_first_search_pathfinding,
    test_hill_climbing_success_and_local_minimum,
    test_beam_search_with_different_widths,
)

__all__ = [
    "graph",
    "test_ucs_canonical_optimal_path",
    "test_ucs_trivial_and_invalid_nodes",
    "test_ucs_dynamic_road_blockage_and_detour",
    "test_ucs_disconnected_graph_failure",
    "test_dls_success_and_cutoff",
    "test_dls_failure_on_unreachable_node",
    "test_ids_canonical_search",
    "test_ids_unreachable_node_termination",
    "test_astar_benchmark_path_and_cost",
    "test_astar_admissibility_efficiency_vs_ucs",
    "test_astar_detour_when_primary_path_blocked",
    "test_best_first_search_pathfinding",
    "test_hill_climbing_success_and_local_minimum",
    "test_beam_search_with_different_widths",
]

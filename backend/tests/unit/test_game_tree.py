"""
Unit Tests for Module IV: Game Trees and Adversarial Decision Making.
Verifies Alpha-Beta Pruning minimax engine and Monte Carlo Tree Search (MCTS).
"""

import pytest

from app.csp.alpha_beta import AlphaBetaDecisionEngine, AlphaBetaGameState
from app.csp.mcts import MCTSSimulator, MCTSNode


def test_alpha_beta_pruning_and_minimax_value():
    """Verify Alpha-Beta evaluates game tree, achieves non-zero pruning, and determines optimal action."""
    engine = AlphaBetaDecisionEngine()
    result = engine.solve(max_depth=3)

    assert result.nodes_evaluated > 0
    assert result.branches_pruned > 0, "Alpha-Beta pruning should prune branches in the game tree"
    assert result.minimax_value >= 0.0 and result.minimax_value <= 100.0
    assert result.optimal_action is not None
    assert "Ambulance" in result.optimal_action or "Paramedic" in result.optimal_action


def test_alpha_beta_depth_scaling():
    """Verify deeper minimax trees evaluate more nodes while retaining pruning effectiveness."""
    engine = AlphaBetaDecisionEngine()

    res_d2 = engine.solve(max_depth=2)
    res_d3 = engine.solve(max_depth=3)

    assert res_d3.nodes_evaluated > res_d2.nodes_evaluated
    assert res_d3.branches_pruned >= res_d2.branches_pruned


def test_mcts_simulation_phases_and_convergence():
    """Verify MCTS executes all 4 phases, produces visit distribution, and selects robust action."""
    simulator = MCTSSimulator(iterations=150, rng_seed=42)
    result = simulator.solve(iterations=150, incident_location="N1")

    assert result.total_rollouts == 150
    assert result.optimal_action in simulator.ACTIONS

    # Visit counts must sum to iteration count (across root's children)
    total_visits = sum(result.visit_counts.values())
    assert total_visits == 150

    # Win rates must be valid probabilities in [0.0, 1.0]
    for action, win_rate in result.win_rates.items():
        assert 0.0 <= win_rate <= 1.0

    # Optimal action must be the one with the maximum visit count
    max_visited_action = max(result.visit_counts.items(), key=lambda x: x[1])[0]
    assert result.optimal_action == max_visited_action


def test_mcts_init_iterations_and_defaults():
    """Verify MCTSSimulator defaults to 200 iterations and respects __init__ configuration."""
    default_sim = MCTSSimulator()
    assert default_sim.iterations == 200
    res_default = default_sim.solve()
    assert res_default.total_rollouts == 200
    assert sum(res_default.visit_counts.values()) == 200

    custom_sim = MCTSSimulator(iterations=80, rng_seed=99)
    assert custom_sim.iterations == 80
    res_custom = custom_sim.solve()
    assert res_custom.total_rollouts == 80
    assert sum(res_custom.visit_counts.values()) == 80

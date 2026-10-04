"""
ResQ-AI Interactive AI Algorithms Lab API Router (FAI Module Lab).
Executes real algorithms for the educational AI Algorithms Lab page.
"""

from typing import Any, Dict
from fastapi import APIRouter, Body

from app.csp.alpha_beta import AlphaBetaDecisionEngine as AlphaBetaSimulator
from app.csp.mcts import MCTSSimulator
from app.csp.problem import DispatchCSP, IncidentSpec
from app.csp.solver import CSPSolver
from app.inference.backward_chaining import BackwardChainingEngine
from app.inference.forward_chaining import ForwardChainingEngine
from app.search.astar import AStarSearch
from app.search.beam_search import BeamSearch
from app.search.best_first import GreedyBestFirstSearch as BestFirstSearch
from app.search.dls import DepthLimitedSearch
from app.search.graph import RoadGraph
from app.search.hill_climbing import HillClimbingSearch
from app.search.ids import IterativeDeepeningSearch
from app.search.ucs import UniformCostSearch

router = APIRouter()


@router.post("/run")
def run_lab(payload: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    """
    Executes the selected AI algorithm against a scenario and returns real execution
    metrics, solution path/assignment, explored node count, explanation, and complexity.
    """
    algo_raw = str(payload.get("algorithm", "A*")).strip()
    algo_key = algo_raw.lower().replace("_", " ").replace("-", " ")
    scenario = payload.get("scenario", "Scenario 1 (Road Accident)")
    params = payload.get("parameters") if isinstance(payload.get("parameters"), dict) else {}

    graph = RoadGraph.build_canonical_network()
    start = str(params.get("start", "A2"))
    goal = str(params.get("goal", "H1"))
    if start not in graph.nodes:
        start = "A2"
    if goal not in graph.nodes:
        goal = "H1"

    # 1. Search Algorithms
    if algo_key in ("ucs", "uniform cost", "dls", "ids", "a*", "a star", "best first", "hill climbing", "beam search"):
        if algo_key in ("ucs", "uniform cost"):
            runner = UniformCostSearch()
            comp = "Time: O(b^(1 + floor(C*/eps))), Space: O(b^(1 + floor(C*/eps)))"
        elif algo_key == "dls":
            runner = DepthLimitedSearch(depth_limit=6)
            comp = "Time: O(b^l), Space: O(b*l)"
        elif algo_key == "ids":
            runner = IterativeDeepeningSearch(max_depth=10)
            comp = "Time: O(b^d), Space: O(b*d)"
        elif algo_key == "best first":
            runner = BestFirstSearch()
            comp = "Time: O(b^m), Space: O(b^m)"
        elif algo_key == "hill climbing":
            runner = HillClimbingSearch()
            comp = "Time: O(d), Space: O(1)"
        elif algo_key == "beam search":
            runner = BeamSearch(beam_width=3)
            comp = "Time: O(k * b * d), Space: O(k)"
        else:
            runner = AStarSearch()
            comp = "Time: O(b^d) with admissible heuristic f(n)=g(n)+h(n), Space: O(b^d)"

        res = runner.search(graph, start, goal)
        sol_str = " -> ".join(res.path) if res.path else "No path found"
        return {
            "status": "Success" if res.success else "Cutoff/Failed",
            "algorithm": algo_raw,
            "scenario": scenario,
            "input": f"RoadGraph (13 nodes), start={start}, goal={goal}",
            "output": sol_str,
            "result": sol_str,
            "solution": sol_str,
            "path": res.path,
            "cost": f"{res.cost:.2f} min",
            "nodes_explored": res.nodes_explored,
            "explored": res.nodes_explored,
            "complexity": comp,
            "explanation": f"{res.algorithm_name} explored {res.nodes_explored} states and found path {sol_str} with cost {res.cost:.2f}.",
        }

    # 2. CSP & Backtracking
    if algo_key in ("csp", "backtracking"):
        solver = CSPSolver()
        prob = DispatchCSP(incident=IncidentSpec(id="INC-LAB", location="N1", victim_count=6, severity="high"), graph=graph)
        res = solver.solve(prob)
        sol_str = f"Ambulance={res.assignment.get('ambulance')}, Hospital={res.assignment.get('hospital')}"
        return {
            "status": "Success" if res.success else "Failed",
            "algorithm": algo_raw,
            "scenario": scenario,
            "input": "Incident(6 victims at N1), Fleet=[A1(4), A2(6), A3(maint)], Hospitals=[H1(20), H2(8)]",
            "output": sol_str,
            "result": sol_str,
            "solution": sol_str,
            "cost": f"{res.execution_time_ms:.2f} ms",
            "nodes_explored": res.nodes_explored,
            "explored": res.nodes_explored,
            "complexity": "Time: O(d^n) reduced by MRV + LCV + AC-3, Space: O(n*d)",
            "explanation": res.explanation,
        }

    # 3. Monte Carlo Tree Search (MCTS)
    if algo_key == "mcts":
        mcts = MCTSSimulator(iterations=150, seed=42)
        res = mcts.run()
        sol_str = f"Best Strategy: {res.best_action} (Win/Success Rate: {res.expected_utility:.3f})"
        return {
            "status": "Success",
            "algorithm": algo_raw,
            "scenario": scenario,
            "input": "Emergency Dispatch Strategy Tree (150 UCB1 rollouts)",
            "output": sol_str,
            "result": sol_str,
            "solution": sol_str,
            "cost": f"{res.expected_utility:.3f} utility",
            "nodes_explored": res.iterations,
            "explored": res.iterations,
            "complexity": "Time: O(N * depth), Space: O(|Tree|)",
            "explanation": res.explanation,
        }

    # 4. Alpha-Beta Pruning
    if algo_key in ("alpha beta", "alphabeta"):
        ab = AlphaBetaSimulator()
        res = ab.run()
        sol_str = f"Optimal Action: {res.best_action} (Minimax Value: {res.optimal_value})"
        return {
            "status": "Success",
            "algorithm": algo_raw,
            "scenario": scenario,
            "input": "Adversarial Disaster-vs-Dispatcher Minimax Tree (depth=3)",
            "output": sol_str,
            "result": sol_str,
            "solution": sol_str,
            "cost": f"Value {res.optimal_value} ({res.pruned_branches} branches pruned)",
            "nodes_explored": res.nodes_evaluated,
            "explored": res.nodes_evaluated,
            "complexity": "Time: O(b^(m/2)) best case with pruning vs O(b^m) Minimax",
            "explanation": res.explanation,
        }

    # 5. Forward Chaining & Backward Chaining
    if "backward" in algo_key:
        bc = BackwardChainingEngine()
        resp = bc.prove("RerouteRequired", ["RoadFlooded(N2)", "OnDispatchRoute(N2)"])
        sol_str = f"Goal 'RerouteRequired' Proved={resp.proved}"
        return {
            "status": "Success",
            "algorithm": algo_raw,
            "scenario": scenario,
            "input": "Goal: RerouteRequired | Facts: RoadFlooded(N2), OnDispatchRoute(N2)",
            "output": sol_str,
            "result": sol_str,
            "solution": sol_str,
            "cost": f"{len(resp.steps)} proof steps",
            "nodes_explored": len(resp.steps),
            "explored": len(resp.steps),
            "complexity": "Time: O(|Rules| * |Facts|), Space: O(depth)",
            "explanation": " -> ".join(resp.steps),
        }

    fc = ForwardChainingEngine()
    resp = fc.infer(["SevereInjuries", "HighSeverity", "RoadFlooded(N2)", "OnDispatchRoute(N2)"])
    sol_str = ", ".join(resp.derived_facts)
    return {
        "status": "Success",
        "algorithm": algo_raw,
        "scenario": scenario,
        "input": "Facts: SevereInjuries, HighSeverity, RoadFlooded(N2), OnDispatchRoute(N2)",
        "output": sol_str,
        "result": sol_str,
        "solution": sol_str,
        "cost": f"{len(resp.rules_fired)} rules fired",
        "nodes_explored": len(resp.steps),
        "explored": len(resp.steps),
        "complexity": "Time: O(|Rules| * |Facts|) fixpoint evaluation",
        "explanation": f"Fired rules {resp.rules_fired} to derive: {sol_str}",
    }

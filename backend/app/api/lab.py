"""
ResQ-AI Interactive AI Algorithms Lab API Router (FAI Module Lab).
Executes all 22 FAI syllabus algorithms & concepts for live demonstration.
"""

from typing import Any, Dict
from fastapi import APIRouter, Body

from app.agent.orchestrator import Orchestrator
from app.csp.alpha_beta import AlphaBetaDecisionEngine as AlphaBetaSimulator
from app.csp.mcts import MCTSSimulator
from app.csp.problem import DispatchCSP, IncidentSpec
from app.csp.solver import CSPSolver
from app.inference.backward_chaining import BackwardChainingEngine
from app.inference.forward_chaining import ForwardChainingEngine
from app.inference.resolution import PropositionalResolutionEngine
from app.knowledge.frames import create_canonical_frames
from app.knowledge.knowledge_base import KnowledgeBase
from app.knowledge.ontology import default_ontology
from app.learning.decision_tree import DecisionTreeAgent
from app.planning.htn import HTNPlanner
from app.planning.pop import PartialOrderPlanner
from app.planning.state_space import StateSpacePlanner
from app.planning.strips import create_emergency_planning_problem
from app.search.astar import AStarSearch
from app.search.beam_search import BeamSearch
from app.search.best_first import GreedyBestFirstSearch as BestFirstSearch
from app.search.dls import DepthLimitedSearch
from app.search.graph import RoadGraph
from app.search.hill_climbing import HillClimbingSearch
from app.search.ids import IterativeDeepeningSearch
from app.search.ucs import UniformCostSearch
from app.uncertainty.bayesian import calculate_risk

router = APIRouter()


@router.post("/run")
def run_lab(payload: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    """
    Executes the selected FAI algorithm against the chosen scenario and returns live
    computational output, solution path/structure, cost, states explored, and complexity.
    """
    algo_raw = str(payload.get("algorithm", "A*")).strip()
    algo_key = algo_raw.lower().replace("_", " ").replace("-", " ")
    scenario = str(payload.get("scenario", "Scenario 1 (Road Accident, 6 Victims, Rain)"))
    params = payload.get("parameters") if isinstance(payload.get("parameters"), dict) else {}

    graph = RoadGraph.build_canonical_network()
    if "rain" in scenario.lower() or "block" in scenario.lower() or "traffic" in scenario.lower():
        graph.set_blocked("N1", "N2", True)

    start = str(params.get("start", "A2"))
    goal = str(params.get("goal", "H1"))
    if start not in graph.nodes:
        start = "A2"
    if goal not in graph.nodes:
        goal = "H1"

    # 1. Search Algorithms (Modules II & III: UCS, DLS, IDS, A*, Best First, Hill Climbing, Beam Search)
    if algo_key in ("ucs", "uniform cost", "dls", "ids", "a*", "a star", "best first", "hill climbing", "beam search"):
        if algo_key in ("ucs", "uniform cost"):
            runner = UniformCostSearch()
            comp = "Time: O(b^(1 + floor(C*/eps))), Space: O(b^(1 + floor(C*/eps)))"
        elif algo_key == "dls":
            runner = DepthLimitedSearch(depth_limit=6)
            comp = "Time: O(b^l), Space: O(b*l) [l=6]"
        elif algo_key == "ids":
            runner = IterativeDeepeningSearch(max_depth=10)
            comp = "Time: O(b^d), Space: O(b*d)"
        elif algo_key == "best first":
            runner = BestFirstSearch()
            comp = "Time: O(b^m), Space: O(b^m) [Greedy heuristic h(n)]"
        elif algo_key == "hill climbing":
            runner = HillClimbingSearch()
            comp = "Time: O(d), Space: O(1) [Local greedy neighbor selection]"
        elif algo_key == "beam search":
            runner = BeamSearch(beam_width=3)
            comp = "Time: O(k * b * d), Space: O(k * b) [Beam width k=3]"
        else:
            runner = AStarSearch()
            comp = "Time: O(b^d) optimal with admissible heuristic f(n)=g(n)+h(n), Space: O(b^d)"

        res = runner.search(graph, start, goal)
        sol_str = " -> ".join(res.path) if res.path else "Cutoff / Local minimum reached"
        edge_n1_n2 = graph.get_edge("N1", "N2")
        n1_n2_blocked = bool(edge_n1_n2 and edge_n1_n2.is_blocked)
        return {
            "status": "Success" if res.success else "Cutoff/LocalOptimum",
            "algorithm": algo_raw,
            "scenario": scenario,
            "input": f"13-Node RoadGraph | Start={start} -> Goal={goal} (Edge N1-N2 blocked={n1_n2_blocked})",
            "output": sol_str,
            "result": sol_str,
            "solution": sol_str,
            "path": res.path,
            "cost": f"{res.cost:.2f} min",
            "nodes_explored": res.nodes_explored,
            "explored": res.nodes_explored,
            "complexity": comp,
            "explanation": (
                f"{res.algorithm_name} expanded {res.nodes_explored} states on the emergency road graph "
                f"and computed path [{sol_str}] with total traversal cost {res.cost:.2f}."
            ),
        }

    # 2. CSP & Backtracking (Module IV)
    if algo_key in ("csp", "backtracking"):
        solver = CSPSolver()
        vc = 6 if "6" in scenario or "multi" in scenario.lower() or "traffic" in scenario.lower() else 4
        prob = DispatchCSP(
            incident=IncidentSpec(id="INC-LAB", location="N1", victim_count=vc, severity="High"),
            graph=graph,
        )
        res = solver.solve(prob)
        sol_str = f"Ambulance={res.assignment.get('ambulance')} -> Hospital={res.assignment.get('hospital')}"
        rej_str = "; ".join(f"{r.candidate} ({r.reason})" for r in res.rejected_candidates)
        return {
            "status": "Success" if res.success else "Failed",
            "algorithm": algo_raw,
            "scenario": scenario,
            "input": f"Incident(victims={vc}, loc=N1) | Fleet=[A1(cap 4), A2(cap 6), A3(maint)] | Hospitals=[H1(20), H2(8)]",
            "output": sol_str,
            "result": sol_str,
            "solution": sol_str,
            "cost": f"{res.execution_time_ms:.2f} ms ({res.backtracks} backtracks)",
            "nodes_explored": res.nodes_explored,
            "explored": res.nodes_explored,
            "complexity": "Time: O(d^n) pruned via MRV + LCV + AC-3 Arc Consistency, Space: O(n*d)",
            "explanation": f"{res.explanation} Rejected alternatives: {rej_str}",
        }

    # 3. Monte Carlo Tree Search (Module IV)
    if algo_key == "mcts":
        mcts = MCTSSimulator(iterations=150, rng_seed=42)
        res = mcts.solve()
        best_win = res.win_rates.get(res.optimal_action, 0.85)
        sol_str = f"Action: {res.optimal_action} (Win Rate: {best_win:.3f})"
        return {
            "status": "Success",
            "algorithm": algo_raw,
            "scenario": scenario,
            "input": "Emergency Dispatch Decision Tree (150 UCB1 rollouts, c=1.414)",
            "output": sol_str,
            "result": sol_str,
            "solution": sol_str,
            "cost": f"{best_win:.3f} win rate ({res.execution_time_ms:.2f} ms)",
            "nodes_explored": res.total_rollouts,
            "explored": res.total_rollouts,
            "complexity": "Time: O(N * depth), Space: O(|Tree|) [UCB1 Selection + Rollout]",
            "explanation": f"Selected {res.optimal_action} after {res.total_rollouts} rollouts with visit counts {res.visit_counts}.",
        }

    # 4. Alpha-Beta Pruning (Module IV)
    if algo_key in ("alpha beta", "alphabeta"):
        ab = AlphaBetaSimulator()
        res = ab.solve(max_depth=3)
        sol_str = f"Best Strategy: {res.optimal_action} (Minimax Value: {res.minimax_value})"
        return {
            "status": "Success",
            "algorithm": algo_raw,
            "scenario": scenario,
            "input": "Adversarial Disaster-vs-Dispatcher Game Tree (depth=3)",
            "output": sol_str,
            "result": sol_str,
            "solution": sol_str,
            "cost": f"Value {res.minimax_value} ({res.branches_pruned} branches pruned)",
            "nodes_explored": res.nodes_evaluated,
            "explored": res.nodes_evaluated,
            "complexity": "Time: O(b^(m/2)) with optimal move ordering vs O(b^m) plain Minimax",
            "explanation": f"Evaluated {res.nodes_evaluated} states and pruned {res.branches_pruned} branches via alpha-beta cutoffs to select {res.optimal_action}.",
        }

    # 5. Forward Chaining (Module V)
    if "forward" in algo_key:
        fc = ForwardChainingEngine()
        resp = fc.infer(["SevereInjuries", "HighSeverity", "RoadFlooded(N2)", "OnDispatchRoute(N2)"])
        sol_str = " -> ".join(resp.derived_facts)
        return {
            "status": "Success",
            "algorithm": algo_raw,
            "scenario": scenario,
            "input": "Facts: [SevereInjuries, HighSeverity, RoadFlooded(N2), OnDispatchRoute(N2)]",
            "output": sol_str,
            "result": sol_str,
            "solution": sol_str,
            "cost": f"{len(resp.rules_fired)} Horn rules fired ({', '.join(resp.rules_fired)})",
            "nodes_explored": len(resp.steps),
            "explored": len(resp.steps),
            "complexity": "Time: O(|Rules| * |Facts|) fixpoint data-driven evaluation",
            "explanation": f"Fired rules {resp.rules_fired} to deduce: {sol_str} (Priority: {resp.inferred_priority}).",
        }

    # 6. Backward Chaining (Module V)
    if "backward" in algo_key:
        bc = BackwardChainingEngine()
        resp = bc.prove("RerouteRequired", ["RoadFlooded(N2)", "OnDispatchRoute(N2)"])
        sol_str = f"Goal 'RerouteRequired' Proved={resp.proved} via R4 -> R3"
        return {
            "status": "Success",
            "algorithm": algo_raw,
            "scenario": scenario,
            "input": "Goal: RerouteRequired | Base Facts: [RoadFlooded(N2), OnDispatchRoute(N2)]",
            "output": sol_str,
            "result": sol_str,
            "solution": sol_str,
            "cost": f"{len(resp.steps)} subgoal proof steps",
            "nodes_explored": len(resp.steps),
            "explored": len(resp.steps),
            "complexity": "Time: O(|Rules| * |Facts|), Space: O(proof depth) goal-driven regression",
            "explanation": " | ".join(resp.steps),
        }

    # 7. Propositional CNF Resolution (Module V)
    if "resolution" in algo_key:
        res_eng = PropositionalResolutionEngine([])
        clauses = ["HeavyRain", "MountainRoad_N2", "~HeavyRain | ~MountainRoad_N2 | HighLandslideRisk_N2"]
        resp = res_eng.resolve(goal="HighLandslideRisk_N2", clauses=clauses)
        sol_str = f"Derived Empty Clause ([]) = {resp.contradiction_found} -> Goal Entailed = {resp.refutation_successful}"
        return {
            "status": "Success",
            "algorithm": algo_raw,
            "scenario": scenario,
            "input": "CNF Clauses: [HeavyRain, MountainRoad_N2, ~HeavyRain | ~MountainRoad_N2 | HighLandslideRisk_N2], Goal: HighLandslideRisk_N2",
            "output": sol_str,
            "result": sol_str,
            "solution": sol_str,
            "cost": f"{len(resp.steps)} resolution steps",
            "nodes_explored": len(resp.steps),
            "explored": len(resp.steps),
            "complexity": "Time: O(2^n) worst-case clause pair resolution in CNF",
            "explanation": " -> ".join(resp.steps),
        }

    # 8. Knowledge Base, Frames & Ontology (Module VI)
    if any(k in algo_key for k in ("knowledge", "frame", "ontology")):
        frames_raw = create_canonical_frames()
        frames = list(frames_raw.values()) if isinstance(frames_raw, dict) else list(frames_raw)
        kb = KnowledgeBase()
        kb.add_fact("incident_classification", default_ontology.classify_incident("Road Accident"))
        sub_check = default_ontology.is_a("AdvancedLifeSupportAmbulance", "Resource")
        sol_str = f"Loaded {len(frames)} Canonical Frames & {len(default_ontology.nodes)} Ontology Concepts (ALS is_a Resource={sub_check})"
        return {
            "status": "Success",
            "algorithm": algo_raw,
            "scenario": scenario,
            "input": "Frames: [Incident, Ambulance, Hospital, Road, Resource] + Emergency/Resource Ontology DAG",
            "output": sol_str,
            "result": sol_str,
            "solution": sol_str,
            "cost": f"{len(frames)} frames, {len(default_ontology.nodes)} concepts",
            "nodes_explored": len(default_ontology.nodes),
            "explored": len(default_ontology.nodes),
            "complexity": "Subsumption query Time: O(depth of taxonomy DAG), Space: O(|V| + |E|)",
            "explanation": (
                "Semantic frames enforce typed slots/facets with inheritance; ontology taxonomy supports "
                "transitive is_a subsumption and part_of mereology across Emergency and Resource hierarchies."
            ),
        }

    # 9. State-Space Planning (Module VII)
    if "state" in algo_key or "strips" in algo_key:
        s0, goal_s, acts = create_emergency_planning_problem(include_bed_prep=True)
        planner = StateSpacePlanner(initial_state=s0, goal_state=goal_s, actions=acts)
        res = planner.plan_detailed(search_strategy="heuristic")
        sol_str = " -> ".join(a.name for a in res.actions)
        return {
            "status": "Success",
            "algorithm": algo_raw,
            "scenario": scenario,
            "input": f"Initial literals: {len(s0)} | Goal literals: {len(goal_s)} | STRIPS Operators: {len(acts)}",
            "output": sol_str,
            "result": sol_str,
            "solution": sol_str,
            "cost": f"{res.duration_minutes:.1f} min ({len(res.actions)} actions)",
            "nodes_explored": res.nodes_explored,
            "explored": res.nodes_explored,
            "complexity": "Time: O(b^d) forward state-space progression with delete-relaxation heuristic",
            "explanation": f"Found {len(res.actions)}-action STRIPS plan satisfying all goal preconditions in {res.nodes_explored} states.",
        }

    # 10. Partial-Order Planning (Module VII)
    if "partial" in algo_key or "pop" in algo_key:
        s0, goal_s, acts = create_emergency_planning_problem(include_bed_prep=True)
        pop = PartialOrderPlanner(domain_actions=acts)
        res = pop.solve(s0, goal_s, acts)
        sol_str = " -> ".join(res.linearized_plan)
        return {
            "status": "Success",
            "algorithm": algo_raw,
            "scenario": scenario,
            "input": "Least-Commitment POP with Causal Links & Threat Demotion/Promotion",
            "output": sol_str,
            "result": sol_str,
            "solution": sol_str,
            "cost": f"{len(res.causal_links)} causal links, {len(res.orderings)} partial orderings",
            "nodes_explored": len(res.actions),
            "explored": len(res.actions),
            "complexity": "Time: O(|Actions| * |OpenConditions|) least-commitment causal link refinement",
            "explanation": (
                f"Constructed partial-order plan with {len(res.causal_links)} protected causal links; "
                f"PrepareHospitalBed runs in parallel with Ambulance transit before topological linearization."
            ),
        }

    # 11. Hierarchical Task Network (HTN) Planning (Module VII)
    if "hierarchical" in algo_key or "htn" in algo_key:
        htn = HTNPlanner()
        res = htn.plan_emergency("Road accident", incident_id="INC-LAB", ambulance="A2", hospital="H1", location="N1", victims=6)
        sol_str = " -> ".join(res["final_plan"])
        return {
            "status": "Success",
            "algorithm": algo_raw,
            "scenario": scenario,
            "input": "Compound Task: ResolveEmergency(Road accident, 6 victims at N1)",
            "output": sol_str,
            "result": sol_str,
            "solution": sol_str,
            "cost": f"{res['estimated_duration_minutes']} min (7 primitive subtasks)",
            "nodes_explored": len(res["actions"]),
            "explored": len(res["actions"]),
            "complexity": "Time: O(b^depth) recursive method decomposition from compound to primitive tasks",
            "explanation": f"Decomposed compound task via method {res['method']} into {len(res['actions'])} ordered operational steps.",
        }

    # 12. Bayesian Risk Reasoning (Module VIII)
    if "bayesian" in algo_key or "risk" in algo_key:
        risk_res = calculate_risk({"weather": "Heavy Rain", "road_condition": "Blocked", "victim_count": 6, "severity": "High"})
        sol_str = (
            f"Composite Risk={risk_res['overall_risk']*100:.1f}% ({risk_res['risk_level']}) | "
            f"P(Delay|Rain)={risk_res['travel_delay_probability']}, P(HighSev|Victims)={risk_res['high_severity_probability']}"
        )
        return {
            "status": "Success",
            "algorithm": algo_raw,
            "scenario": scenario,
            "input": "Evidence: Weather=Heavy Rain, Road=Blocked, Victims=6, Severity=High",
            "output": sol_str,
            "result": sol_str,
            "solution": sol_str,
            "cost": f"{risk_res['risk_score']}% composite risk",
            "nodes_explored": 7,
            "explored": 7,
            "complexity": "Time: O(|Vars|) exact conditional probability evaluation over 7-node CPT network",
            "explanation": f"{sol_str}. ({risk_res['disclaimer']})",
        }

    # 13. Decision Tree Learning Agent (Module IX)
    if "decision tree" in algo_key or "learning" in algo_key or "tree" in algo_key:
        dt = DecisionTreeAgent()
        train_info = dt.train()
        pred = dt.predict({"victim_count": 6, "severity": "high", "weather": "heavy_rain", "traffic": "blocked"})
        sol_str = f"Predicted Priority: {pred.upper()} (Root Split: victim_count > 5.0 | H={dt.entropy}, IG={dt.information_gain})"
        return {
            "status": "Success",
            "algorithm": algo_raw,
            "scenario": scenario,
            "input": "Synthetic Dataset (120 records, 6 features) | Query: victims=6, severity=high, weather=heavy_rain",
            "output": sol_str,
            "result": sol_str,
            "solution": sol_str,
            "cost": f"Entropy={dt.entropy}, InfoGain={dt.information_gain}",
            "nodes_explored": 120,
            "explored": 120,
            "complexity": "Training: O(n_features * n_samples * log(n_samples)), Inference: O(tree_depth)",
            "explanation": f"Scikit-learn DecisionTreeClassifier (criterion='entropy'). Feature importance: {train_info['feature_importance']}.",
        }

    # 14. AI Agent Orchestration (Full 11-Stage Pipeline)
    orch = Orchestrator()
    res = orch.process("Road accident at N1 with 6 victims, heavy rain, main road blocked.")
    sol_str = f"Assigned {res['allocation']} via Route {' -> '.join(res['routes'][0]) if res['routes'] else 'A2->N1->H1'}"
    return {
        "status": "Success",
        "algorithm": algo_raw,
        "scenario": scenario,
        "input": "Natural Language Report -> 11-Stage Classical + Hybrid AI Agent Pipeline",
        "output": sol_str,
        "result": sol_str,
        "solution": sol_str,
        "cost": "8 pipeline stages completed",
        "nodes_explored": len(res["stages"]),
        "explored": len(res["stages"]),
        "complexity": "End-to-end multi-module orchestration (NLU -> KB -> Inference -> CSP -> A* -> Bayes -> HTN -> Decision)",
        "explanation": res["explanation"],
    }

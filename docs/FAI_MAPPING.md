# FAI Module Mapping — ResQ-AI

> This document maps every Fundamentals of Artificial Intelligence (FAI) syllabus module to the exact source files, UI pages, classes, and functions in ResQ-AI.

---

## Module II — Uninformed Search

| Item | Details |
|------|---------|
| **Algorithms** | Uniform Cost Search (UCS), Depth-Limited Search (DLS), Iterative Deepening Search (IDS) |
| **Source Files** | [`backend/app/search/ucs.py`](../backend/app/search/ucs.py), [`backend/app/search/dls.py`](../backend/app/search/dls.py), [`backend/app/search/ids.py`](../backend/app/search/ids.py), [`backend/app/search/base.py`](../backend/app/search/base.py) |
| **Key Classes** | `UniformCostSearch`, `DepthLimitedSearch`, `IterativeDeepeningSearch` |
| **Key Methods** | `.search(graph, start, goal)` → returns `SearchResult(path, cost, nodes_explored, success, algorithm_name)` |
| **UI Pages** | Route Search (`/search`), AI Algorithms Lab (`/lab`) |
| **Tests** | [`backend/tests/unit/test_search_uninformed.py`](../backend/tests/unit/test_search_uninformed.py) |
| **Graph** | [`backend/app/search/graph.py`](../backend/app/search/graph.py) — 13-node weighted road graph with distance, travel time, traffic factor, blocked status, risk factor |
| **How Used** | Agent orchestrator calls search algorithms to find routes from incident location to hospital via ambulance pickup. User can also run algorithms manually on the Route Search page. |

---

## Module III — Informed Search

| Item | Details |
|------|---------|
| **Algorithms** | A* Search, Greedy Best-First Search, Hill Climbing, Beam Search |
| **Source Files** | [`backend/app/search/astar.py`](../backend/app/search/astar.py), [`backend/app/search/best_first.py`](../backend/app/search/best_first.py), [`backend/app/search/hill_climbing.py`](../backend/app/search/hill_climbing.py), [`backend/app/search/beam_search.py`](../backend/app/search/beam_search.py) |
| **Key Classes** | `AStarSearch`, `BestFirstSearch`, `HillClimbingSearch`, `BeamSearch` |
| **Key Methods** | `.search(graph, start, goal)` → `SearchResult` |
| **Heuristic** | A* uses `f(n) = g(n) + h(n)` where `h(n)` is the estimated remaining travel cost (admissible heuristic based on straight-line distance / max speed) |
| **UI Pages** | Route Search (`/search`), AI Algorithms Lab (`/lab`) |
| **Tests** | [`backend/tests/unit/test_search_informed.py`](../backend/tests/unit/test_search_informed.py) |
| **How Used** | A* is the primary search algorithm used by the agent for optimal route finding. Other algorithms are available for comparison in the Algorithms Lab. |

---

## Module IV — CSP / Optimal Decision

| Item | Details |
|------|---------|
| **Algorithms** | Constraint Satisfaction Problem (CSP) with Backtracking + Constraint Propagation (AC-3/Forward Checking), Monte Carlo Tree Search (MCTS), Alpha-Beta Pruning |
| **Source Files** | [`backend/app/csp/solver.py`](../backend/app/csp/solver.py), [`backend/app/csp/problem.py`](../backend/app/csp/problem.py), [`backend/app/csp/mcts.py`](../backend/app/csp/mcts.py), [`backend/app/csp/alpha_beta.py`](../backend/app/csp/alpha_beta.py) |
| **Key Classes** | `CSPSolver`, `EmergencyCSPProblem`, `MCTSSimulator`, `AlphaBetaSearch` |
| **Key Methods** | `CSPSolver.solve()`, `MCTSSimulator.search()`, `AlphaBetaSearch.search()` |
| **CSP Variables** | incident → ambulance → hospital → route |
| **CSP Constraints** | ambulance must be available, ambulance capacity ≥ victim count, one ambulance per incident, hospital capacity sufficient, blocked roads excluded |
| **UI Pages** | Resource Allocation (`/allocation`), AI Algorithms Lab (`/lab`) |
| **Tests** | [`backend/tests/unit/test_csp.py`](../backend/tests/unit/test_csp.py), [`backend/tests/unit/test_game_tree.py`](../backend/tests/unit/test_game_tree.py) |
| **How Used** | CSP solver is the primary resource allocation engine. MCTS and Alpha-Beta are educational demonstrations in the Algorithms Lab. |

---

## Module V — Inference

| Item | Details |
|------|---------|
| **Algorithms** | Forward Chaining, Backward Chaining, Resolution |
| **Source Files** | [`backend/app/inference/engine.py`](../backend/app/inference/engine.py), [`backend/app/inference/resolution.py`](../backend/app/inference/resolution.py), [`backend/app/inference/rules.py`](../backend/app/inference/rules.py) |
| **Key Classes** | `ForwardChainingEngine`, `BackwardChainingEngine`, `ResolutionProver` |
| **Key Methods** | `ForwardChainingEngine.infer(facts)`, `BackwardChainingEngine.query(goal, facts)`, `ResolutionProver.prove(kb, query)` |
| **Example Rules** | `IF victim_count > 5 AND severity == high THEN priority = critical` · `IF road_blocked THEN avoid_blocked_routes` · `IF hospital_capacity <= 0 THEN hospital_unavailable` · `IF ambulance_available AND capacity >= victims THEN ambulance_feasible` |
| **Fact Types** | Propositional-style facts, FOL-inspired structured facts |
| **UI Pages** | AI Agent Console (`/agent`), AI Algorithms Lab (`/lab`) |
| **Tests** | Unit tests for forward chaining, backward chaining, and resolution |
| **How Used** | Agent uses forward chaining to derive priority from incident facts, backward chaining to verify goal conditions, and resolution for proof demonstrations. All inference steps are logged. |

---

## Module VI — Knowledge Representation

| Item | Details |
|------|---------|
| **Concepts** | Knowledge Base, Frames, Categories, Events, Relationships, Ontology |
| **Source Files** | [`backend/app/knowledge/knowledge_base.py`](../backend/app/knowledge/knowledge_base.py), [`backend/app/knowledge/frames.py`](../backend/app/knowledge/frames.py), [`backend/app/knowledge/ontology.py`](../backend/app/knowledge/ontology.py), [`backend/app/knowledge/relationships.py`](../backend/app/knowledge/relationships.py) |
| **Key Classes** | `KnowledgeBase`, `Frame`, `Ontology`, `Relationship` |
| **Frames** | `IncidentFrame`, `AmbulanceFrame`, `HospitalFrame`, `RoadFrame`, `EmergencyResourceFrame` |
| **Ontology Tree** | Emergency → {Medical Emergency, Road Accident, Fire, Flood, Natural Disaster} · Resource → {Ambulance, Fire Engine, Rescue Team, Hospital} |
| **UI Pages** | Dashboard (`/`), AI Agent Console (`/agent`) |
| **How Used** | The knowledge base stores structured facts about the emergency domain. Frames represent entity templates. The ontology classifies emergency and resource types. The agent queries the KB during reasoning. Frontend visualizes knowledge relationships. |

---

## Module VII — Planning

| Item | Details |
|------|---------|
| **Algorithms** | State-Space Planning, Partial-Order Planning (POP), Hierarchical Task Network (HTN) Planning |
| **Source Files** | [`backend/app/planning/state_space.py`](../backend/app/planning/state_space.py), [`backend/app/planning/partial_order.py`](../backend/app/planning/partial_order.py), [`backend/app/planning/hierarchical.py`](../backend/app/planning/hierarchical.py) |
| **Key Classes** | `StateSpacePlanner`, `PartialOrderPlanner`, `HierarchicalPlanner` |
| **Key Methods** | `.plan(initial_state, goal_state)` → `Plan(actions, dependencies, initial_state, goal_state)` |
| **HTN Example** | Emergency Response → {Assess Incident, Allocate Resources, Navigate, Transfer Victims, Complete Incident} |
| **UI Pages** | Planning (`/planning`), AI Algorithms Lab (`/lab`) |
| **How Used** | Agent uses hierarchical planning to generate multi-step response plans. State-space and POP provide alternative planning strategies. All plans show initial state, goal, actions, and dependencies. |

---

## Module VIII — Uncertainty / Bayesian Reasoning

| Item | Details |
|------|---------|
| **Algorithm** | Bayesian Risk Engine with Conditional Probability Tables |
| **Source Files** | [`backend/app/uncertainty/bayesian.py`](../backend/app/uncertainty/bayesian.py) |
| **Key Classes** | `BayesianRiskEngine` |
| **Key Methods** | `.calculate_risk(evidence)` → risk scores for each variable |
| **Variables** | Weather, Road Condition, Traffic, Travel Delay, Victim Severity, Hospital Capacity, Response Risk |
| **Example Calculations** | `P(delay \| heavy_rain)`, `P(high_severity \| victim_count > 5)`, `P(hospital_overload \| multiple_incidents)` |
| **UI Pages** | Risk Analysis (`/risk`) |
| **⚠️ Disclaimer** | All probabilities are **simulated/educational** — not real-world medical statistics |
| **How Used** | Agent calculates response risk after route selection. Risk analysis page shows all probabilities with charts. |

---

## Module IX — Learning Agent

| Item | Details |
|------|---------|
| **Algorithm** | Decision Tree (scikit-learn) |
| **Source Files** | [`backend/app/learning/decision_tree.py`](../backend/app/learning/decision_tree.py) |
| **Key Classes** | `DecisionTreeLearner` |
| **Key Methods** | `.train(dataset)`, `.predict(features)`, `.get_tree_structure()`, `.get_feature_importance()` |
| **Synthetic Dataset** | Features: victim_count, weather, traffic, distance, incident_type, severity → Target: priority |
| **Metrics Shown** | Tree structure, entropy, information gain, feature importance, prediction accuracy |
| **UI Pages** | AI Algorithms Lab (`/lab`) |
| **How Used** | Decision tree learns from synthetic emergency data to predict incident priority. Shows the tree structure with entropy and information gain at each node. |

---

## Cross-Cutting: AI Agent Orchestrator

| Item | Details |
|------|---------|
| **Source Files** | [`backend/app/agent/orchestrator.py`](../backend/app/agent/orchestrator.py), [`backend/app/agent/llm_service.py`](../backend/app/agent/llm_service.py), [`backend/app/agent/demo_parser.py`](../backend/app/agent/demo_parser.py) |
| **Key Class** | `AgentOrchestrator` |
| **Agent Tools** | `parse_incident()`, `query_knowledge_base()`, `run_forward_chaining()`, `run_backward_chaining()`, `allocate_resources()`, `run_search()`, `calculate_bayesian_risk()`, `generate_plan()`, `evaluate_plan()`, `replan()`, `generate_explanation()` |
| **Pipeline** | NL Input → Extraction → KB → Inference → Priority → CSP → Search → Risk → Planning → Evaluation → Decision → Explanation |
| **LLM Usage** | Only for NLU parsing and final explanation generation |
| **Classical AI** | Inference, search, CSP, planning, Bayesian reasoning, learning |
| **Demo Mode** | Deterministic fallback parsing when no LLM API key is configured |
| **UI Pages** | AI Agent Console (`/agent`), Report Emergency (`/report`) |

---

## Summary Table

| FAI Module | Topic | Algorithms | Source Directory | Primary UI Page |
|------------|-------|------------|------------------|-----------------|
| II | Uninformed Search | UCS, DLS, IDS | `backend/app/search/` | Route Search |
| III | Informed Search | A*, Best First, Hill Climbing, Beam Search | `backend/app/search/` | Route Search |
| IV | CSP / Optimal Decision | CSP+Backtracking, MCTS, Alpha-Beta | `backend/app/csp/` | Resource Allocation |
| V | Inference | Forward Chaining, Backward Chaining, Resolution | `backend/app/inference/` | Agent Console |
| VI | Knowledge Rep | KB, Frames, Ontology | `backend/app/knowledge/` | Dashboard |
| VII | Planning | State-Space, POP, HTN | `backend/app/planning/` | Planning |
| VIII | Uncertainty | Bayesian Risk Engine | `backend/app/uncertainty/` | Risk Analysis |
| IX | Learning | Decision Tree | `backend/app/learning/` | Algorithms Lab |
| — | Agent | Orchestrator + LLM Service | `backend/app/agent/` | Agent Console |

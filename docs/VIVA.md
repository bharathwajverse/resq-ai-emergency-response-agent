# ResQ-AI — Comprehensive Viva Voce Defense & Q&A Guide

> **Course**: Fundamentals of Artificial Intelligence (FAI)  
> **Project**: ResQ-AI — Intelligent Emergency Response & Resource Planning Agent  
> **Disclaimer**: *Educational simulation — not for real-world emergency dispatch.*

---

## 1. Project Overview & Core Architecture

### Q1.1: What is ResQ-AI, and what problem does it solve?
**Answer**:  
ResQ-AI is an autonomous decision-support web application for emergency dispatch and resource planning. When a natural-language emergency report arrives (e.g., *"There is a road accident near the university at N1. Six people may be injured. Heavy rain is causing traffic and the main road is blocked."*), the AI Agent:
1. Extracts structured entities (`incident_type`, `location`, `victim_count`, `weather`, `road_blocked`, `severity`).
2. Queries a **Knowledge Base** of Semantic Frames and a 53-concept **Domain Ontology**.
3. Runs **Forward and Backward Chaining** over Horn rules to infer incident priority and route constraints.
4. Solves a **Constraint Satisfaction Problem (CSP)** with Backtracking, MRV, LCV, and AC-3 arc consistency to allocate feasible ambulances and hospitals.
5. Executes classical graph search (**A\***, **UCS**, **IDS**, **DLS**, **Best-First**, **Hill Climbing**, **Beam Search**) over a 13-node, 17-edge weighted road network.
6. Evaluates a 7-variable **Bayesian Conditional Probability Table (CPT)** network to estimate travel delay and hospital overload risk.
7. Generates an executable response plan using **Hierarchical Task Network (HTN)**, **State-Space (STRIPS)**, or **Partial-Order Planning (POP)**.
8. Supports **Dynamic Replanning** if a dispatched ambulance breaks down or becomes unavailable mid-operation.

---

## 2. AI Agent Architecture (`backend/app/agent/orchestrator.py`)

### Q2.1: What is an AI Agent, and how is your `Orchestrator` structured?
**Answer**:  
In Russell & Norvig's framework, an **AI Agent** perceives its environment through sensors and acts upon that environment using actuators/tools to maximize performance.  
In `backend/app/agent/orchestrator.py`, the `Orchestrator` class maintains explicit **Agent State**:
- `incident`, `resources`, `ambulances`, `hospitals`, `roads`
- `facts`, `inferences`, `constraints`, `candidate_routes`, `risk`
- `current_plan`, `selected_plan`, `decision`

And invokes 11 modular **Agent Tools**:
1. `parse_incident()`
2. `query_knowledge_base()`
3. `run_forward_chaining()`
4. `run_backward_chaining()`
5. `allocate_resources()`
6. `run_search()`
7. `calculate_bayesian_risk()`
8. `generate_plan()`
9. `evaluate_plan()`
10. `replan()`
11. `generate_explanation()`

### Q2.2: How does Dynamic Replanning work when an ambulance breaks down?
**Answer**:  
When `replan()` (`POST /api/agent/replan`) is triggered with `unavailable_ambulance="A2"`, the agent:
1. Marks `A2` as `Unavailable` in the active fleet state and releases its lock.
2. Re-runs the CSP solver over the remaining fleet (`A1`, capacity 4; `A3`, maintenance).
3. If a 6-victim incident exceeds `A1`'s single-unit capacity (4), the CSP solver triggers a **multi-unit / split-dispatch fallback** assigning `A1` (`N8`) and recalculating the optimal A* route (`A1 -> N8 -> N1 -> N3 -> N4 -> H1`).
4. Regenerates the HTN response plan and logs an auditable replanning decision.

---

## 3. Why LLM vs. Why Classical AI?

### Q3.1: Why use an LLM at all, and what is it restricted from doing?
**Answer**:  
- **What the LLM does**: Natural-language understanding (converting unstructured emergency calls into structured JSON validated by Pydantic schemas) and generating human-readable summaries of the final decision (`backend/app/agent/llm_service.py`).
- **What the LLM is NEVER allowed to do**: The LLM does **not** choose routes, allocate ambulances, check capacity constraints, or invent probabilities. LLMs hallucinate on graph shortest-path problems and hard combinatorial constraints.
- **Demo Mode Fallback**: When no `GEMINI_API_KEY` is configured, `backend/app/agent/demo_parser.py` performs deterministic keyword/regex NLU extraction so the entire system runs 100% offline.

### Q3.2: Why use Classical AI for routing, allocation, inference, and planning?
**Answer**:  
Classical AI algorithms provide **formal guarantees**:
- **Completeness & Optimality**: A* and UCS mathematically guarantee the minimum-cost unblocked path.
- **Soundness**: Horn-clause Forward/Backward Chaining and CNF Resolution only derive logically entailed conclusions.
- **Hard Constraint Satisfaction**: Backtracking CSP with AC-3 guarantees no unavailable or under-capacity ambulance is ever assigned.

---

## 4. Uninformed & Informed Search (FAI Modules II & III)

### Q4.1: Explain Uniform Cost Search (UCS). When is it optimal?
**Answer**:  
UCS (`backend/app/search/ucs.py`) expands the frontier node with the lowest cumulative path cost $g(n)$ using a min-priority queue. It is **complete and optimal** whenever all edge costs satisfy $c(u, v) \ge \epsilon > 0$. In ResQ-AI, blocked edges have $c(u, v) = \infty$ and unblocked edges have positive traversal cost $d \times \tau \times (1 + r)$.

### Q4.2: Explain A* Search and prove why your heuristic $h(n)$ is admissible.
**Answer**:  
A* (`backend/app/search/astar.py`) evaluates nodes by:
$$f(n) = g(n) + h(n)$$
where $g(n)$ is the exact cost from start to $n$, and $h(n)$ is the estimated cost from $n$ to the goal.  
In `RoadGraph.heuristic(u, goal)` (`backend/app/search/graph.py`), we use scaled Euclidean distance:
$$h(n) = \text{EuclideanDistance}(n, \text{goal}) \times 0.20$$
Because Euclidean straight-line distance is the shortest possible geometric distance between two coordinates and traffic/risk multipliers satisfies $\tau \ge 1.0, r \ge 0.0$, $h(n) \le h^*(n)$ (true remaining cost) for all nodes. Thus $h(n)$ is **admissible and consistent**, guaranteeing A* finds the optimal route while exploring fewer states than UCS (6 nodes vs. 11 nodes on `A2 -> H1`).

### Q4.3: Compare Depth-Limited Search (DLS) and Iterative Deepening Search (IDS).
**Answer**:  
- **DLS (`dls.py`)**: Performs DFS bounded by depth limit $\ell$. Time $O(b^\ell)$, Space $O(b\ell)$. Incomplete if the shallowest goal lies at depth $d > \ell$, and non-optimal.
- **IDS (`ids.py`)**: Repeatedly runs DLS for $\ell = 0, 1, 2, \dots, d_{\max}$. Combines DFS's linear space complexity $O(bd)$ with BFS's completeness on unweighted hops.

### Q4.4: Compare Greedy Best-First Search, Hill Climbing, and Beam Search.
**Answer**:  
- **Greedy Best-First (`best_first.py`)**: Expands $f(n) = h(n)$ using a global priority queue. Fast (5 nodes explored), but non-optimal.
- **Hill Climbing (`hill_climbing.py`)**: Memoryless local search ($O(1)$ space) that moves greedily to the neighbor with lowest $h(n)$, terminating at local minima/plateaus if no neighbor improves $h$.
- **Beam Search (`beam_search.py`)**: Breadth-first expansion that retains only the top $k$ ($k=3$) lowest-cost states at each level, bounding memory to $O(k \cdot b)$.

---

## 5. CSP, MCTS & Alpha-Beta Pruning (FAI Module IV)

### Q5.1: Formulate the Emergency Resource Allocation problem as a CSP.
**Answer**:  
In `backend/app/csp/problem.py` (`DispatchCSP`):
- **Variables**: $X = \{\text{ambulance}, \text{hospital}, \text{route}\}$
- **Domains**:
  - $D_{\text{ambulance}} = \{A1, A2, A3\}$
  - $D_{\text{hospital}} = \{H1, H2\}$
- **Constraints**:
  1. $\text{status}(\text{ambulance}) = \text{Available}$ (`A3` rejected: in Maintenance)
  2. $\text{capacity}(\text{ambulance}) \ge \text{victim\_count}$ (for 6 victims, `A1` rejected: capacity $4 < 6$)
  3. $\text{ambulance} \notin \text{ACTIVE\_DISPATCHED\_AMBULANCES}$ (no double-booking across concurrent incidents)
  4. $\text{emergency\_beds}(\text{hospital}) \ge \text{victim\_count}$
  5. $\text{route}$ contains zero blocked road edges ($c(u, v) < \infty$).

### Q5.2: How do MRV, LCV, and AC-3 improve Backtracking Search?
**Answer**:  
In `backend/app/csp/solver.py`:
- **MRV (Minimum Remaining Values)**: Chooses the unassigned variable with the smallest legal domain first (fail-first principle).
- **LCV (Least Constraining Value)**: Orders domain values to leave maximum flexibility for remaining variables.
- **AC-3 (Arc Consistency)**: Propagates unary and binary constraints before search using a worklist of arcs $(X_i, X_j)$, pruning inconsistent domain values early.

### Q5.3: How are MCTS and Alpha-Beta Pruning used in ResQ-AI?
**Answer**:  
- **MCTS (`mcts.py`)**: Executes 4 phases — **Selection** (using Upper Confidence Bound for Trees: $\text{UCT} = \frac{W_i}{N_i} + c\sqrt{\frac{\ln N_p}{N_i}}$), **Expansion**, **Simulation (Rollout)** under stochastic weather/traffic shocks, and **Backpropagation**.
- **Alpha-Beta Pruning (`alpha_beta.py`)**: Models an adversarial game between `MAX` (Emergency Dispatcher selecting staging tactics) and `MIN` (Nature/Hazard introducing bridge debris or gridlock), pruning branches whenever $\beta \le \alpha$.

---

## 6. Logical Inference & Knowledge Representation (FAI Modules V & VI)

### Q6.1: Contrast Forward Chaining, Backward Chaining, and CNF Resolution.
**Answer**:  
- **Forward Chaining (`forward_chaining.py`)**: Data-driven fixpoint iteration. Starts from initial facts (`SevereInjuries`, `RoadFlooded(N2)`) and fires Horn rules (`R1`–`R12`) until no new facts can be derived.
- **Backward Chaining (`backward_chaining.py`)**: Goal-driven regression. Starts from query `RerouteRequired`, finds rules concluding `RerouteRequired` (`R4: RoadImpassable(N2) ^ OnDispatchRoute(N2) -> RerouteRequired`), and recursively proves subgoals.
- **Propositional Resolution (`resolution.py`)**: Proof by contradiction (refutation). Adds negated goal $\neg G$ to CNF clauses and resolves complementary literals $(A \vee C)$ and $(\neg A \vee D) \vdash (C \vee D)$ until deriving the Empty Clause `([])`.

### Q6.2: How are Semantic Frames and Ontologies implemented?
**Answer**:  
- **Frames (`frames.py`)**: Structured Minsky frames for `Incident`, `Ambulance`, `Hospital`, `Road`, and `Resource` with typed slots, default facets (`IF-NEEDED`), and constraint facets.
- **Ontology (`ontology.py`)**: Directed Acyclic Graph (DAG) of 53 concepts supporting transitive `is_a` subsumption queries (e.g., `is_a("AdvancedLifeSupportAmbulance", "Resource") == True`) and `part_of` relationships.

---

## 7. Automated Planning (FAI Module VII)

### Q7.1: Compare State-Space (STRIPS), Partial-Order (POP), and Hierarchical (HTN) Planning.
**Answer**:  
- **State-Space Planning (`state_space.py`)**: Searches forward from `initial_state` applying STRIPS operators (`Preconditions`, `Add-List`, `Delete-List`) using a delete-relaxation heuristic until `goal_state` literals are satisfied.
- **Partial-Order Planning (`pop.py`)**: Least-commitment planner that maintains partial ordering constraints ($A \prec B$) and protected **Causal Links** ($A \xrightarrow{p} B$). Allows independent actions (e.g., `PrepareHospitalBed` and `DispatchAmbulance`) to remain unordered/parallel until final topological linearization.
- **Hierarchical Task Network (`htn.py`)**: Decomposes compound task `ResolveEmergency` into sub-tasks (`Assess Incident` $\rightarrow$ `Allocate Resources` $\rightarrow$ `Navigate` $\rightarrow$ `Transfer Victims` $\rightarrow$ `Complete Incident`) using domain methods.

---

## 8. Uncertainty & Machine Learning (FAI Modules VIII & IX)

### Q8.1: How does the Bayesian Risk Engine compute conditional probabilities?
**Answer**:  
In `backend/app/uncertainty/bayesian.py`, the engine evaluates a 7-variable Conditional Probability Table (CPT) network over `Weather`, `Road Condition`, `Traffic`, `Travel Delay`, `Victim Severity`, `Hospital Capacity`, and `Response Risk`:
- $P(\text{Delay} \mid \text{Heavy Rain}, \text{Blocked}) = 0.88$
- $P(\text{High Severity} \mid \text{Victims} \ge 6) = 0.90$
- $P(\text{Hospital Overload} \mid \text{Load}) = 0.38$
All probabilities are explicitly labeled as **Simulated/Educational Probabilities**.

### Q8.2: How does the Decision Tree Learning Agent work?
**Answer**:  
In `backend/app/learning/decision_tree.py`, `DecisionTreeAgent` uses `scikit-learn`'s `DecisionTreeClassifier(criterion="entropy", max_depth=5)` trained on a 120-record synthetic emergency dataset (`victim_count`, `weather`, `traffic`, `distance`, `incident_type`, `severity` $\rightarrow$ `priority`). It computes root **Shannon Entropy**:
$$H(S) = -\sum_{c} p_c \log_2(p_c) \approx 1.976$$
and **Information Gain** $IG(S, A) = H(S) - \sum_{v} \frac{|S_v|}{|S|} H(S_v) \approx 0.658$, identifying `victim_count > 5.0` as the highest-gain root split.

---

## 9. System Limitations & Future Enhancements

- **Current Limitations**:
  1. Uses a static 13-node canonical city graph rather than live OpenStreetMap GIS tiles.
  2. Bayesian CPT parameters and the 120-row Decision Tree dataset are synthetically calibrated for educational demonstration rather than clinical trauma registries.
- **Future Enhancements**:
  1. Live GPS telemetry and real-time OpenStreetMap/OSRM road network ingestion.
  2. Multi-agent auction protocols (Contract Net Protocol) for decentralized fleet coordination.
  3. Reinforcement Learning (MDP/Q-Learning) for proactive ambulance repositioning before emergencies occur.

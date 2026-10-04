# ResQ-AI REST API Reference

Base URL: `http://localhost:8000`  
Interactive Swagger UI: `http://localhost:8000/docs`  
ReDoc Reference: `http://localhost:8000/redoc`

> **Academic Disclaimer Header**: All HTTP responses include `X-ResQ-AI-Disclaimer: Educational simulation - not for real-world emergency dispatch.` and `X-Response-Time-Ms`.

---

## 1. System & Seed Endpoints

### `GET /health`
Verifies API status and live database connectivity (`SELECT 1`).
- **Response (`200 OK`)**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "demo_mode": true,
  "disclaimer": "Educational simulation — not for real-world emergency dispatch."
}
```

### `POST /api/seed`
Idempotently seeds canonical hospitals (`H1`, `H2`), ambulances (`A1`, `A2`, `A3`), resources, and the 13-node road network graph.

---

## 2. Incidents (`backend/app/api/incidents.py`)

### `GET /api/incidents`
Returns all active/reported emergency incidents.

### `POST /api/incidents`
Creates a new validated emergency incident.
- **Request Body**:
```json
{
  "title": "Scenario 1: Highway Crash",
  "emergency_type": "Traffic Accident",
  "description": "Multi-car crash near Downtown Junction N1, 6 victims, heavy rain, bridge N1-N2 blocked.",
  "location": "N1",
  "victim_count": 6,
  "severity": "High",
  "weather": "Heavy Rain",
  "road_condition": "Blocked"
}
```
- **Response (`201 Created`)**: Returns created incident with UUID `id`, `priority`, and `created_at`.

### `GET /api/incidents/{incident_id}`
Retrieves a single incident by UUID or returns `404 Not Found`.

---

## 3. Emergency Resources (`backend/app/api/resources.py`)

- `GET /api/resources`: Returns combined `{ "ambulances": [...], "hospitals": [...], "roads": [...] }`.
- `GET /api/ambulances`: Returns fleet (`A1` cap 4 Available, `A2` cap 6 Available, `A3` cap 6 Maintenance).
- `GET /api/hospitals`: Returns hospitals (`H1` emergency capacity 20, `H2` emergency capacity 8).
- `GET /api/roads`: Returns 13-node road graph edges (`source_node`, `target_node`, `distance_km`, `travel_time`, `traffic_factor`, `is_blocked`, `risk_factor`).

---

## 4. AI Agent Orchestrator (`backend/app/api/agent.py`)

### `POST /api/agent/analyze`
Parses natural language emergency text (via Gemini API or deterministic Demo Parser) and runs the stage-by-stage reasoning pipeline.
- **Request Body**:
```json
{
  "text": "Severe highway pileup at N1 Downtown with 6 injured passengers. Torrential rain and road N1-N2 blocked."
}
```
- **Response (`200 OK`)**: Returns `extracted`, `inferences`, `risk`, `allocation`, `routes`, `plan`, `stages`, and `explanation`.

### `POST /api/agent/plan`
Executes the full 11-stage autonomous agent workflow for an incident and records the decision in the audit trail.
- **Request Body**: `{"incident_id": "<uuid>"}`
- **Response (`200 OK`)**: Returns `priority`, `allocated_ambulance`, `allocated_hospital`, `route`, `risk`, `plan`, and `explanation`.

### `POST /api/agent/replan`
Triggers dynamic replanning when a dispatched ambulance becomes unavailable or a road is blocked mid-mission.
- **Request Body**:
```json
{
  "incident_id": "<uuid>",
  "failed_ambulance_code": "A2",
  "reason": "Tire blowout on highway"
}
```
- **Response (`200 OK`)**: Returns `is_replanned: true`, alternate `allocated_ambulance`, updated detour `route`, and `new_plan`.

---

## 5. Uninformed & Informed Route Search (`backend/app/api/search.py`)

### `POST /api/search/run`
Executes any of the 7 search algorithms (`UCS`, `DLS`, `IDS`, `A_Star`, `Best_First`, `Hill_Climbing`, `Beam_Search`) on the 13-node road graph.
- **Request Body**:
```json
{
  "algorithm": "A_Star",
  "start_node": "A2",
  "goal_node": "H1",
  "depth_limit": 8,
  "beam_width": 3
}
```
- **Response (`200 OK`)**:
```json
{
  "success": true,
  "algorithm_name": "A* Search",
  "path": ["A2", "N4", "N1", "N3", "H1"],
  "cost": 18.4,
  "nodes_explored": 5,
  "blocked": 1
}
```

---

## 6. CSP Resource Allocation (`backend/app/api/csp.py`)

### `POST /api/csp/solve`
Runs Backtracking search with MRV, LCV, Forward Checking, and AC-3 constraint propagation.
- **Request Body**: `{"victim_count": 6, "location": "N1", "severity": "High"}`
- **Response (`200 OK`)**: Returns `success`, `assignment` (`ambulance`, `hospital`), `nodes_explored`, `backtracks`, and `rejected_candidates` with rejection reasons.

---

## 7. Logical Inference (`backend/app/api/inference.py`)

- `POST /api/inference/forward`: Fixpoint Forward Chaining over Horn rules (`{"facts": ["victim_count_gte_5", "severity_high"]}`).
- `POST /api/inference/backward`: Goal-driven recursive Backward Chaining proof tree (`{"goal": "priority_p1_critical", "known_facts": [...]}`).
- `POST /api/inference/resolution`: Propositional CNF Resolution Refutation (`{"clauses": [["P", "Q"], ["-P", "Q"], ["-Q"]]}`).

---

## 8. Classical & Hierarchical Planning (`backend/app/api/planning.py`)

### `POST /api/planning/generate`
Generates emergency response plans across `Hierarchical` (HTN), `State-Space` (STRIPS BFS/Heuristic), and `Partial-Order` (POP with causal links) paradigms.
- **Request Body**: `{"paradigm": "Hierarchical", "emergency_type": "Traffic Accident", "victim_count": 6, "location": "N1"}`

---

## 9. Bayesian Risk Engine (`backend/app/api/risk.py`)

### `POST /api/risk/analyze`
Computes conditional probabilities `P(delay | weather, road)`, `P(high_severity | victims)`, `P(hospital_overload | incidents)`, composite risk score, and simulated disclaimer.
- **Request Body**: `{"weather": "Heavy Rain", "road_condition": "Flooded", "severity": "Critical", "victim_count": 10}`

---

## 10. Decision Tree Learning Agent (`backend/app/api/learning.py`)

- `POST /api/learning/predict`: Predicts incident priority from emergency features and returns Shannon entropy, information gain, and feature importances.
- `GET /api/learning/tree`: Exports the trained Decision Tree topology and split thresholds.

---

## 11. Interactive AI Algorithms Lab & Audit History

- `POST /api/lab/run`: Executes any of the 13 FAI algorithms (`UCS`, `DLS`, `IDS`, `A*`, `Best First`, `Hill Climbing`, `Beam Search`, `CSP`, `Backtracking`, `MCTS`, `Alpha-Beta`, `Forward Chaining`, `Backward Chaining`) and returns live output, path/solution, cost, nodes explored, and complexity analysis.
- `GET /api/decisions`: Returns the audit log of all AI-driven dispatch decisions.

# API Documentation

## Incidents
- `GET /api/incidents`: List all incidents
  - **Response**: `[{"id": "...", "title": "Fire", "severity": "high", "status": "active"}]`
- `POST /api/incidents`: Create a new incident
  - **Request Body**: `{"title": "Accident", "description": "Car crash", "severity": "high"}`
  - **Response**: `{"id": "...", "status": "created"}`
- `GET /api/incidents/{id}`: Get incident details
  - **Response**: `{"id": "...", "title": "Accident", "description": "Car crash", ...}`

## Resources
- `GET /api/resources`: List resources
  - **Response**: `[{"id": "...", "name": "Defibrillator 1", "type": "Medical Equipment", "status": "available"}]`
- `GET /api/ambulances`: List ambulances
  - **Response**: `[{"id": "...", "name": "A1", "status": "available", "capacity": 4}]`
- `GET /api/hospitals`: List hospitals
  - **Response**: `[{"id": "...", "name": "H1", "emergency_capacity": 20}]`

## Agent
- `POST /api/agent/query`: Send natural language query to the AI agent
  - **Request Body**: `{"query": "Allocate an ambulance to the fire"}`
  - **Response**: `{"response": "Agent decided to allocate A1", "decisions": [...]}`

## Search
- `POST /api/search/route`: Find a route using specified algorithm
  - **Request Body**: `{"algorithm": "astar", "source": "H1", "destination": "H2"}`
  - **Response**: `{"path": ["H1", "N1", "N2", "H2"], "cost": 12.0}`

## Inference
- `POST /api/inference/query`: Run logical inference
  - **Request Body**: `{"facts": ["fire_present"], "query": "severity_high"}`
  - **Response**: `{"result": true, "proof": "..."}`

## CSP
- `POST /api/csp/solve`: Allocate resources
  - **Request Body**: `{"incidents": [...], "resources": [...]}`
  - **Response**: `{"allocation": {"incident_1": "ambulance_A1"}}`

## Risk
- `POST /api/risk/calculate`: Calculate Bayesian risk
  - **Request Body**: `{"weather": "rain", "road_type": "highway"}`
  - **Response**: `{"risk_factor": 0.45}`

## Planning
- `POST /api/planning/generate`: Generate response plan
  - **Request Body**: `{"incident_type": "earthquake", "severity": "critical"}`
  - **Response**: `{"plan": ["Triage", "Dispatch Medics", "Evacuate"]}`

## Learning
- `POST /api/learning/predict`: Predict incident priority
  - **Request Body**: `{"description": "Massive fire with multiple injuries"}`
  - **Response**: `{"priority": "critical", "confidence": 0.89}`

## Algorithms Lab
- `GET /api/lab/status`: Get health and availability of lab modules
  - **Response**: `{"status": "online", "modules": ["search", "csp", "learning"]}`

# Testing Documentation

## Testing Strategy
ResQ-AI employs a three-tiered testing strategy to ensure both the LLM integration and the classical algorithms remain robust.

1. **Unit Tests**:
   - Focus on testing Classical AI modules in complete isolation from the database and LLM.
   - Example: Verifying that A* finds the optimal path on a mock in-memory graph.
2. **Integration Tests**:
   - Verify the Agent Orchestrator correctly selects tools based on mock LLM outputs.
   - Verify database repositories correctly read/write to the PostgreSQL instance.
3. **End-to-End (E2E) Tests**:
   - Simulate a full HTTP request hitting the API, interacting with the real database, and verifying the complete response payload.

## How to Run Tests
All tests are orchestrated using `pytest`.

```bash
# Run all tests
pytest backend/tests/

# Run tests with verbose output
pytest -v backend/tests/

# Run specifically unit tests for algorithms
pytest backend/tests/unit/test_search.py
```

## Test File Locations
- `backend/tests/unit/`: Tests for individual algorithms (e.g., `test_astar.py`, `test_csp.py`).
- `backend/tests/integration/`: Tests for database and agent tool calling.
- `backend/tests/e2e/`: Full API endpoint tests using `TestClient`.

## Coverage Information
We aim for >85% test coverage on classical algorithms to guarantee safety-critical reliability.
To generate a coverage report:
```bash
pytest --cov=backend/app backend/tests/
```

## Demo Scenarios
When evaluating the system, use these manual demo scenarios:
1. **Optimal Routing**: Block a central node in the UI and request an ambulance dispatch; verify the system routes *around* the blockage.
2. **Resource Constraint**: Create 5 simultaneous high-priority incidents and watch the CSP module prioritize and queue requests based on limited ambulance capacity.
3. **Inference Cascading**: Manually set `Weather=Storm` and `Traffic=High`; observe the Bayesian risk factor increase and trigger alternate planning rules.

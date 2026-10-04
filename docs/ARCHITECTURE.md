# System Architecture

## System Overview
ResQ-AI uses a modern hybrid architecture combining the flexibility of Large Language Models with the reliability of Classical AI algorithms.

```text
+---------------------+      REST      +------------------------+
|   Frontend (React)  | <============> |   FastAPI (Backend)    |
| - Dashboard         |                |                        |
| - Agent Console     |                |  +------------------+  |
| - Algorithms Lab    |                |  |Agent Orchestrator|  |
+---------------------+                |  +------------------+  |
                                       |      |          |      |
                                       |   [LLM]   [Classical]  |
                                       |             [Tools]    |
                                       +------------------------+
                                                   | SQL
                                       +------------------------+
                                       | Database (PostgreSQL)  |
                                       | - incidents, resources |
                                       | - roads, search_logs   |
                                       +------------------------+
```

## Component Descriptions
- **Frontend**: A React application providing intuitive interfaces for users to view incidents, chat with the AI Agent, and experiment with AI algorithms in the Lab.
- **Backend (FastAPI)**: A high-performance Python backend that exposes a RESTful API. It handles HTTP requests, connects to the database, and hosts the AI logic.
- **Agent Orchestrator**: The core controller. It takes user input, queries the LLM to determine intent, and executes necessary Classical AI Tools.
- **Database (PostgreSQL)**: A relational database ensuring data persistence, integrity, and ACID compliance for critical emergency data.

## Data Flow
1. **Input**: User submits a natural language request via the Frontend.
2. **API**: Request is sent to the FastAPI backend.
3. **Orchestration**: Agent Orchestrator sends the prompt to the LLM.
4. **Tool Selection**: LLM decides a tool (e.g., `find_route`) is needed and responds with tool call arguments.
5. **Execution**: Orchestrator executes the Classical AI algorithm (e.g., A*).
6. **Persistence**: Execution logs and results are stored in PostgreSQL.
7. **Response**: Final results are returned through the API to the Frontend.

## Module Interaction Diagram
```text
[User Request] -> (LLM) -> [Intent & Params] -> (Tool Registry)
                                                    |
                                    +---------------+---------------+
                                    |               |               |
                               [Search]         [Inference]       [CSP]
                               (A*, UCS)      (F/B Chaining)    (Backtracking)
```

## Technology Choices and Rationale
- **FastAPI**: Chosen for its async support, high performance, and automatic Swagger documentation.
- **PostgreSQL**: Selected for strict schema enforcement and spatial/graph extensions if needed in the future.
- **Python**: The standard for AI, allowing seamless integration of search algorithms and LLM SDKs.
- **React**: Enables dynamic, responsive UI for real-time dashboard updates.

## Separation of Concerns: LLM vs Classical AI vs Agent
- **LLM**: Strictly used as a natural language interface. It handles ambiguity, parses intent, and extracts parameters. It **never** executes logical operations directly.
- **Classical AI**: Handles all deterministic operations. Routing, scheduling, logical inference, and constraint satisfaction are strictly algorithmic to guarantee optimality and safety.
- **Agent Orchestrator**: Acts as the bridge. It manages the LLM context, invokes the tools, handles tool errors, and maintains conversational state.

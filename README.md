# 🚨 ResQ-AI — Intelligent Emergency Response & Resource Planning Agent

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18+-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-5+-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-3+-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3+-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)

**An AI-powered emergency response decision-support system demonstrating classical AI techniques alongside modern LLM capabilities.**

⚠️ *Educational simulation — not for real-world emergency dispatch.*

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [AI Modules](#-ai-modules)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Demo Mode](#-demo-mode)
- [API Documentation](#-api-documentation)
- [Testing](#-testing)
- [FAI Module Mapping](#-fai-module-mapping)
- [Deployment](#-deployment)
- [Documentation](#-documentation)
- [License](#-license)

---

## 🔍 Overview

ResQ-AI is an **Intelligent Emergency Response & Resource Planning Agent** built as a college **Fundamentals of Artificial Intelligence (FAI)** project. It demonstrates how classical AI algorithms work alongside modern LLM capabilities in a real-world emergency management scenario.

### What Makes This Different?

This is **NOT** a simple chatbot. The system uses a carefully designed separation of concerns:

| Component | Role | Technology |
|-----------|------|------------|
| **LLM** | Natural language understanding + structured extraction + explanation | Gemini API (or Demo Mode fallback) |
| **Classical AI** | Inference, search, CSP, planning, Bayesian reasoning, learning | Custom implementations + scikit-learn |
| **AI Agent** | Orchestration, tool selection, state management, decision workflow | Custom Agent Orchestrator |

### Key Features

- 🧠 **AI Agent Orchestrator** — Multi-step reasoning pipeline with replanning capability
- 🔍 **7 Search Algorithms** — UCS, DLS, IDS, A*, Best First, Hill Climbing, Beam Search
- 🧩 **Constraint Satisfaction** — CSP with backtracking and constraint propagation
- 📐 **Inference Engine** — Forward chaining, backward chaining, and resolution
- 📊 **Bayesian Risk Analysis** — Probabilistic risk assessment with conditional probabilities
- 🌳 **Decision Tree Learning** — scikit-learn based priority prediction
- 📋 **Planning System** — State-space, partial-order, and hierarchical planning
- 🏗️ **Knowledge Base** — Frames, ontology, and relationship modeling
- 🎓 **AI Algorithms Lab** — Interactive educational page for algorithm exploration

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + Vite)                   │
│  Dashboard │ Report │ Agent Console │ Algorithms Lab │ ...   │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST API
┌─────────────────────────┴───────────────────────────────────┐
│                   BACKEND (FastAPI + Python)                  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              AI AGENT ORCHESTRATOR                     │   │
│  │  parse → knowledge → inference → CSP → search →       │   │
│  │  risk → planning → evaluation → decision              │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │ Search  │ │   CSP   │ │Inference│ │Planning │          │
│  │ Module  │ │ Module  │ │ Module  │ │ Module  │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │Knowledge│ │Bayesian │ │Learning │ │  LLM    │          │
│  │  Base   │ │  Risk   │ │ Agent   │ │ Service │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│                   DATABASE (PostgreSQL)                       │
│  incidents │ ambulances │ hospitals │ roads │ decisions │ ... │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧠 AI Modules

### FAI Module Mapping

| Module | Topic | Implementation |
|--------|-------|----------------|
| **II** | Uninformed Search | UCS, DLS, IDS |
| **III** | Informed Search | A*, Best First, Hill Climbing, Beam Search |
| **IV** | CSP / Optimal Decision | Backtracking, Constraint Propagation, MCTS, Alpha-Beta |
| **V** | Inference | Forward Chaining, Backward Chaining, Resolution |
| **VI** | Knowledge Representation | Knowledge Base, Frames, Ontology |
| **VII** | Planning | State-Space, Partial-Order, Hierarchical |
| **VIII** | Uncertainty | Bayesian Risk Engine |
| **IX** | Learning Agent | Decision Tree (scikit-learn) |

> See [FAI_MAPPING.md](docs/FAI_MAPPING.md) for detailed source file mapping.

---

## 🛠️ Tech Stack

### Frontend
- **React 18** with Vite for fast development
- **Tailwind CSS** for responsive, modern UI
- **React Router** for client-side navigation
- **Recharts** for data visualization

### Backend
- **Python 3.11+** with FastAPI
- **SQLAlchemy 2.0** ORM with Pydantic v2 validation
- **scikit-learn** for Decision Tree implementation
- **NetworkX** for graph operations (where useful)

### Database
- **PostgreSQL** (production) / **SQLite** (development fallback)

### AI/ML
- **LLM Provider Abstraction** — supports Gemini API, with deterministic Demo Mode fallback
- **Custom Algorithm Implementations** — all classical AI algorithms built from scratch

---

## 📁 Project Structure

```
resq-ai/
├── frontend/                    # React + Vite frontend
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   ├── pages/               # 10 application pages
│   │   ├── services/            # API client services
│   │   └── App.jsx              # Root component + routing
│   ├── package.json
│   └── vite.config.js
│
├── backend/                     # Python FastAPI backend
│   ├── app/
│   │   ├── api/                 # REST API endpoints
│   │   ├── agent/               # AI Agent Orchestrator
│   │   ├── search/              # Search algorithms (UCS, A*, etc.)
│   │   ├── csp/                 # Constraint Satisfaction Problem
│   │   ├── inference/           # Forward/Backward Chaining
│   │   ├── knowledge/           # Knowledge Base & Ontology
│   │   ├── planning/            # State-Space, POP, Hierarchical
│   │   ├── uncertainty/         # Bayesian Risk Engine
│   │   ├── learning/            # Decision Tree Learning
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic validation schemas
│   │   ├── services/            # Business logic services
│   │   ├── main.py              # FastAPI application entry
│   │   └── config.py            # Configuration management
│   ├── tests/                   # Unit & integration tests
│   └── requirements.txt         # Python dependencies
│
├── database/                    # Database schemas & migrations
├── docs/                        # Documentation
│   ├── ARCHITECTURE.md
│   ├── ALGORITHMS.md
│   ├── FAI_MAPPING.md
│   ├── API.md
│   ├── DATABASE.md
│   ├── TESTING.md
│   └── VIVA.md
│
├── scripts/                     # Utility scripts
├── tests/                       # E2E test suites
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm
- **PostgreSQL 15+** (optional — SQLite fallback available)

### 1. Clone the Repository

```bash
git clone https://github.com/bharathwajverse/resq-ai-emergency-response-agent.git
cd resq-ai-emergency-response-agent
```

### 2. Backend Setup

```bash
# Create virtual environment
cd backend
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp ../.env.example ../.env

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
# Install dependencies
cd frontend
npm install

# Start development server
npm run dev
```

### 4. Database Setup

The application automatically creates tables on startup. To seed demo data:

```bash
cd backend
python seed_data.py
```

### 5. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 🎭 Demo Mode

ResQ-AI runs fully in **Demo Mode** when no LLM API key is configured:

- ✅ Deterministic incident parsing (no LLM required)
- ✅ All AI algorithms execute normally
- ✅ Complete workflow: report → analyze → plan → decide
- ✅ All 5 demo scenarios available

To enable LLM features, add your API key to `.env`:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
```

---

## 📡 API Documentation

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/incidents` | List all incidents |
| `POST` | `/api/incidents` | Create new incident |
| `GET` | `/api/resources` | Get all resources |
| `GET` | `/api/ambulances` | List ambulances |
| `GET` | `/api/hospitals` | List hospitals |
| `GET` | `/api/roads` | Get road network |
| `POST` | `/api/agent/analyze` | Run AI agent analysis |
| `POST` | `/api/agent/plan` | Generate response plan |
| `POST` | `/api/agent/replan` | Trigger replanning |
| `POST` | `/api/search/run` | Execute search algorithm |
| `POST` | `/api/inference/forward` | Run forward chaining |
| `POST` | `/api/inference/backward` | Run backward chaining |
| `POST` | `/api/csp/solve` | Solve CSP allocation |
| `POST` | `/api/risk/analyze` | Bayesian risk analysis |
| `POST` | `/api/planning/generate` | Generate plan |
| `POST` | `/api/learning/predict` | Decision tree prediction |
| `GET` | `/api/decisions` | Decision history |

> See [API.md](docs/API.md) for full documentation.

---

## 🧪 Testing

```bash
# Run all tests
python scripts/run_all_tests.py

# Run backend unit tests
cd backend
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run E2E tests
pytest tests/e2e/ -v
```

### Test Coverage

- ✅ Search algorithms (UCS, A*, DLS, IDS, Best First, Hill Climbing, Beam Search)
- ✅ CSP solver with backtracking
- ✅ Forward & backward chaining inference
- ✅ Bayesian risk engine
- ✅ Decision tree learning
- ✅ Agent orchestration
- ✅ API integration tests
- ✅ 5 demo scenario E2E tests

---

## 🎓 FAI Module Mapping

| FAI Module | Algorithms | Source Files | UI Page |
|------------|-----------|--------------|---------|
| Module II | UCS, DLS, IDS | `backend/app/search/` | Route Search, Algorithms Lab |
| Module III | A*, Best First, Hill Climbing, Beam Search | `backend/app/search/` | Route Search, Algorithms Lab |
| Module IV | CSP, Backtracking, MCTS, Alpha-Beta | `backend/app/csp/` | Resource Allocation, Algorithms Lab |
| Module V | Forward/Backward Chaining, Resolution | `backend/app/inference/` | AI Agent Console, Algorithms Lab |
| Module VI | KB, Frames, Ontology | `backend/app/knowledge/` | Dashboard, Agent Console |
| Module VII | State-Space, POP, Hierarchical | `backend/app/planning/` | Planning, Algorithms Lab |
| Module VIII | Bayesian Network | `backend/app/uncertainty/` | Risk Analysis |
| Module IX | Decision Tree | `backend/app/learning/` | Algorithms Lab |

> See [FAI_MAPPING.md](docs/FAI_MAPPING.md) for detailed mapping with line numbers.

---

## 🚢 Deployment

### Frontend (Vercel)

```bash
cd frontend
npm run build
# Deploy dist/ to Vercel
```

### Backend (Render)

```bash
# Use render.yaml or configure:
# Build: pip install -r requirements.txt
# Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Database

- Use any PostgreSQL provider (Supabase, Railway, Render, etc.)
- Set `DATABASE_URL` in environment variables

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and design decisions |
| [ALGORITHMS.md](docs/ALGORITHMS.md) | Detailed algorithm explanations |
| [FAI_MAPPING.md](docs/FAI_MAPPING.md) | FAI syllabus → source code mapping |
| [API.md](docs/API.md) | REST API documentation |
| [DATABASE.md](docs/DATABASE.md) | Database schema documentation |
| [TESTING.md](docs/TESTING.md) | Testing strategy and coverage |
| [VIVA.md](docs/VIVA.md) | Viva voce preparation guide |

---

## ⚠️ Disclaimer

> **This is an educational simulation — not for real-world emergency dispatch.**
>
> - All data is fictional and simulated
> - Probabilities are educational demonstrations, not real-world statistics
> - Do not use for actual emergency response decisions
> - No real patient data is used

---

## 📄 License

This project is created for academic purposes as part of the Fundamentals of Artificial Intelligence course.

---

<div align="center">

**Built with ❤️ for FAI**

*ResQ-AI — Where Classical AI Meets Modern Intelligence*

</div>

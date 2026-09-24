# 🗓️ Smart AI Scheduling & Task Assistant Backend

> An intelligent, context-aware scheduling backend built with **FastAPI**, **PostgreSQL + pgvector**, and **Google Gemini**. Designed to understand multi-intent natural language, manage tasks and calendar schedules, retrieve context using vector embeddings, and remember important facts across conversations.

---

## 💡 Why I Built This

As a student juggling coursework, coding projects, and everyday life, I constantly found myself struggling with traditional to-do lists. Standard productivity apps are rigid:
- If you write: *"Remind me to study Operating Systems tomorrow at 5 PM, and also show me how productive I've been this week,"* a regular app completely chokes.
- You have to open one screen to create a task, navigate to another screen for analytics, and remember your own context.

I wanted to build an assistant that feels like a real chief of staff — something you can just talk to in plain English (or messy student English!). It figures out what you want to do, splits multi-part requests into concrete actions, remembers your preferences over time, and retrieves past notes and tasks using semantic search rather than exact keyword matches.

---

## 🧠 Key Features & System Design

### 1. 🤖 Master-Worker Multi-Agent Orchestrator
Instead of throwing a raw prompt at an LLM and hoping it does everything at once, the system uses a **Master Orchestrator** pattern:
- **Master Orchestrator (`MasterOrchestrator`)**: Uses Gemini with Pydantic structured output (`MultiAgentPlan`) to parse user queries and identify whether a request has single or multiple intents.
- **Worker Agents**:
  - `task_worker`: Handles task creation, updates, completion, deletions, and calendar time-window queries.
  - `analytics_worker`: Computes completion rates, category distributions, and productivity trends.
  - `memory_worker`: Recalls stored facts, preferences, and long-term user context.
  - `chat_worker`: Handles general conversational questions and helpful chit-chat.
- **Synthesis Engine**: Merges the outputs of all dispatched worker sub-tasks into a clean, polite, and cohesive response back to the user.

```
                  ┌──────────────────────────────┐
                  │    User Natural Language     │
                  │   "Schedule OS study at 5pm  │
                  │    and check my weekly stats"│
                  └──────────────┬───────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────┐
                  │      Master Orchestrator     │
                  │  (Gemini + Structured Output)│
                  └──────────────┬───────────────┘
                                 │
                 Decomposes into sub-tasks (JSON)
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
       ┌───────────────────┐           ┌───────────────────┐
       │    task_worker    │           │ analytics_worker  │
       │ (Create Task DB)  │           │(Calculate Stats)  │
       └─────────┬─────────┘           └─────────┬─────────┘
                 │                               │
                 └───────────────┬───────────────┘
                                 ▼
                  ┌──────────────────────────────┐
                  │       Synthesizer Engine     │
                  │  (Unified Friendly Response) │
                  └──────────────────────────────┘
```

---

### 2. 🔍 Smart Hybrid Context Builder (pgvector + Scoring)
Most vector search tutorials just take cosine similarity and call it a day. In real life, that doesn't work well — an urgent task due in 2 hours might have slightly lower cosine similarity than a task from 6 months ago!

To fix this, the context builder (`rag/context_builder.py`) ranks items with a multi-factor mathematical scoring function:

$$\text{Final Score} = w_{\text{sim}} \cdot \text{Sim} + w_{\text{rec}} \cdot \text{Recency} + w_{\text{imp}} \cdot \text{Importance} + w_{\text{freq}} \cdot \text{Frequency}$$

- **Cosine Similarity ($w_{\text{sim}} = 0.50$)**: Vector distance computed via PostgreSQL `pgvector`.
- **Exponential Recency Decay ($w_{\text{rec}} = 0.20$)**: $e^{-\lambda \cdot \Delta t}$, prioritizing fresh tasks and recent conversations.
- **Priority / Importance ($w_{\text{imp}} = 0.20$)**: High-priority items get an inherent boost over casual notes.
- **Interaction Frequency ($w_{\text{freq}} = 0.10$)**: Frequently viewed or updated tasks bubble up naturally.

---

### 3. 🧠 Long-Term Memory Extraction
The assistant doesn't suffer from gold-fish memory. After conversation exchanges:
- An LLM pipeline analyzes the dialogue asynchronously.
- It detects user goals, preferences, project ideas, or habits (e.g., *"Prefers working in the evening"*, *"Building a compiler in Rust"*).
- Assigns an importance score (1 to 10) and stores it with vector embeddings so it can be seamlessly recalled in future sessions.

---

### 4. ⚡ Asynchronous Background Workers
Generating text embeddings and saving memories can take 1–2 seconds over the network. To keep API latency snappy for the user:
- Responses are returned immediately.
- Embeddings and long-term memory extraction are offloaded to FastAPI `BackgroundTasks`.

---

## 🛠️ Tech Stack

| Layer | Technology | Why Chosen |
| :--- | :--- | :--- |
| **Framework** | FastAPI (Python 3.10+) | Extremely fast, asynchronous non-blocking I/O, built-in Swagger OpenAPI docs |
| **Database** | PostgreSQL 16 + `pgvector` | Relational integrity for tasks/users + native vector similarity search |
| **ORM & Migrations** | SQLAlchemy 2.0 (Async) + Alembic | Fully async queries with `asyncpg`, strong typing, clean migrations |
| **LLM & Embeddings** | Google Gemini (`gemini-2.5-flash`, `gemini-embedding-001`) | Fast structured JSON output, generous context window, reliable embeddings |
| **Auth & Security** | JWT (Access + Refresh tokens) + Passlib/Bcrypt | Industry-standard stateless auth with token refresh mechanics |
| **Caching & Queues** | Redis | Fast token revocation and caching support |
| **Containerization** | Docker & Docker Compose | Easy one-command setup for backend, PostgreSQL, and Redis |

---

## 📁 Project Structure

```text
Ai-Assistant-FastApi/
├── agents/                  # Multi-agent orchestrator & specialized workers
│   ├── base.py              # Base worker agent interface
│   ├── master_orchestrator.py # Decomposes user queries & synthesizes answers
│   ├── task_agent.py        # Task creation, deletion, and agenda management
│   ├── analytics_agent.py   # Productivity stats & category distribution
│   ├── memory_agent.py      # Recalling long-term user facts
│   └── chat_agent.py        # General conversational fallback
├── api/                     # Additional API dependencies & helpers
├── background/              # Async background tasks (embeddings, memory extraction)
│   └── worker.py
├── core/                    # App configuration, database engine, security & exceptions
│   ├── config.py            # Pydantic Settings reading .env
│   ├── database.py          # Async engine & sessionmaker
│   └── security.py          # Password hashing & JWT token issuance
├── llm/                     # Gemini client wrapper & prompt templates
│   └── gemini.py            # Structured output handling & fallback models
├── memory/                  # Long-term memory extraction logic
│   └── long_term.py
├── models/                  # SQLAlchemy ORM models
│   ├── user.py              # User account model
│   ├── task.py              # Task model with pgvector embedding column
│   ├── category.py          # Task categories (Work, Study, Personal, etc.)
│   ├── chat.py              # Chat messages & persistent memories
│   └── auth_tokens.py       # Refresh tokens & revocation tracking
├── rag/                     # Semantic retrieval & hybrid context builder
│   ├── embeddings.py        # Gemini embedding generation
│   ├── retrieval.py         # pgvector distance queries
│   └── context_builder.py   # Hybrid scoring formula
├── repositories/            # Data access layer (Separation of Concerns)
├── routers/                 # FastAPI API route controllers
│   ├── auth.py              # /api/v1/auth (register, login, refresh, logout)
│   ├── tasks.py             # /api/v1/tasks (CRUD & status updates)
│   ├── chat.py              # /api/v1/chat (conversational assistant)
│   ├── calendar.py          # /api/v1/calendar (schedule & agenda queries)
│   ├── analytics.py         # /api/v1/analytics (productivity metrics)
│   ├── search.py            # /api/v1/search (semantic similarity search)
│   └── memory.py            # /api/v1/memory (view & manage remembered facts)
├── schemas/                 # Pydantic schemas for request/response validation
├── services/                # Business logic layer
├── tests/                   # Pytest suite
├── docker-compose.yml       # Docker services configuration
├── Dockerfile               # API container definition
├── requirements.txt         # Project dependencies
└── main.py                  # Application entry point & lifecycle setup
```

---

## 🚀 Getting Started

You can run this project either locally with Python or via Docker Compose.

### Option 1: Running Locally

#### 1. Clone the repository
```bash
git clone https://github.com/Aman-Rajput-10-09/Ai-Assistant-FastApi.git
cd Ai-Assistant-FastApi
```

#### 2. Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3. Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Configure environment variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and fill in your details:
- `GEMINI_API_KEY`: Get a free API key from [Google AI Studio](https://aistudio.google.com/).
- `DATABASE_URL`: Your PostgreSQL connection string (must have `pgvector` installed, e.g., `postgresql+asyncpg://postgres:password@localhost:5432/scheduler_db`).
- `SECRET_KEY`: A secure random string for JWT signing.

#### 5. Run the application
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Once running, head over to `http://localhost:8000/docs` to test all endpoints interactively through Swagger UI!

---

### Option 2: Running with Docker Compose (Recommended)

Docker Compose spins up the FastAPI app, PostgreSQL with `pgvector` pre-configured, and Redis all in one command:

```bash
# 1. Ensure .env is populated with your GEMINI_API_KEY
cp .env.example .env

# 2. Start all services
docker compose up --build
```

- API server will be available at: `http://localhost:8000`
- PostgreSQL at port `5432`
- Redis at port `6379`

---

## 🧪 Testing

To run the test suite:

```bash
pytest -v
```

Tests cover authentication flows, task CRUD operations, database session handling, and mock LLM orchestrator interactions.

---

## 📡 API Overview

Here is a quick tour of the primary endpoints available under `/api/v1`:

### 🔐 Authentication (`/api/v1/auth`)
- `POST /register` – Create a new user account with hashed password.
- `POST /login` – Obtain JWT access token & refresh token.
- `POST /refresh` – Rotate expired access tokens.
- `POST /logout` – Invalidate active tokens.

### 💬 AI Assistant Chat (`/api/v1/chat`)
- `POST /` – The main conversational endpoint. Accepts natural language, invokes the Master Orchestrator, executes sub-tasks across worker agents, and returns the response.
- `GET /history` – Get recent conversation history.

### 📋 Tasks & Schedule (`/api/v1/tasks` & `/api/v1/calendar`)
- `GET /tasks` – List tasks with optional status and category filters.
- `POST /tasks` – Create a task with priority, category, and due date.
- `PATCH /tasks/{id}` – Update task details or mark complete.
- `GET /calendar/agenda` – View upcoming commitments for a given date window.

### 🔍 Semantic Search & Analytics (`/api/v1/search` & `/api/v1/analytics`)
- `GET /search?q=...` – Perform vector similarity search across past tasks and notes.
- `GET /analytics/summary` – View completion rates, overdue tasks, and category breakdown.

### 🧠 Long-Term Memory (`/api/v1/memory`)
- `GET /memory` – List all extracted preferences, facts, and goals the assistant has stored about you.

---

## 📚 What I Learned Building This Project

1. **Structured Outputs are a Game Changer:**
   Using Pydantic with Gemini to enforce JSON schema responses eliminated 99% of parsing errors compared to trying to parse unstructured markdown strings.
2. **Raw Vector Similarity is Not Enough for Productivity Apps:**
   Building the hybrid scoring formula in `rag/context_builder.py` taught me how crucial recency decay and frequency weights are when dealing with time-sensitive user data.
3. **Async Database Patterns in Python:**
   Working with SQLAlchemy 2.0's async session lifecycle taught me how to properly handle connection pools, avoid memory leaks, and handle graceful rollbacks during service disruptions.
4. **Resilient LLM Design:**
   LLM APIs can experience rate limits or model version deprecations. Adding fallback model cascades (`gemini-2.5-flash` -> `gemini-2.0-flash`) ensures the application keeps running smoothly even during API hiccups.

---

## 🔮 Future Roadmap

- [ ] **Google Calendar & Outlook 2-Way Sync:** Bi-directional sync so changes made in Google Calendar reflect in the assistant and vice-versa.
- [ ] **Telegram / WhatsApp Bot Interface:** Being able to send quick voice notes or messages while on the go.
- [ ] **Voice-to-Text with Whisper:** Dictate long task lists and study schedules directly through speech.
- [ ] **Recurring Habits & Spaced Repetition:** Tracking daily student habits and reminding when revision is due based on forgetting curves.

---

## 🤝 Contributing & Feedback

If you find a bug, have an idea for an agent worker, or want to contribute:
1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/cool-idea`).
3. Commit your changes (`git commit -m 'Add cool new feature'`).
4. Push to the branch (`git push origin feature/cool-idea`).
5. Open a Pull Request.

Any feedback, suggestions, or star on GitHub is super appreciated! ⭐

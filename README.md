# Galaxy Map

Minimal task tracker for AI agents. Dead simple kanban board with a REST API that any agent can use.

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`

## API

All endpoints are under `/api`.

### Endpoints

| Method   | Path                   | Description                                  |
| -------- | ---------------------- | -------------------------------------------- |
| `GET`    | `/api/tasks`           | List tasks (`?status=` and `?specialization=`) |
| `POST`   | `/api/tasks`           | Create a task                                |
| `GET`    | `/api/tasks/{id}`      | Get a single task                            |
| `PATCH`  | `/api/tasks/{id}`      | Update a task (partial)                      |
| `DELETE` | `/api/tasks/{id}`      | Delete a task                                |
| `GET`    | `/api/statuses`        | List valid statuses                          |
| `GET`    | `/api/specializations` | List valid specializations                   |
| `GET`    | `/api/health`          | Health check                                 |

### Create a task

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Implement context caching",
    "description": "Add LRU cache for zone context to reduce tokens.",
    "specialization": "coding"
  }'
```

### Create a task with dependencies

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Write benchmarks for caching",
    "specialization": "coding",
    "blocked_by": ["abc123"]
  }'
```

A task is considered "blocked" (`is_blocked: true`) when any task in its `blocked_by` list has a status other than `done`.

### Move a task

```bash
curl -X PATCH http://localhost:8000/api/tasks/abc123 \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

### Filter by specialization

```bash
# Get all coding tasks that are queued
curl "http://localhost:8000/api/tasks?status=queued&specialization=coding"
```

This is how agents pick up work — query for their specialization + a target status.

### Agent metadata

Tasks have a `metadata` JSON field for arbitrary context:

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Refactor zone transitions",
    "specialization": "coding",
    "metadata": {
      "agent": "sr2-planner",
      "related_files": ["src/zones.py", "tests/test_zones.py"]
    }
  }'
```

### Statuses (columns)

`backlog` → `queued` → `in_progress` → `needs_review` → `done`

### Specializations

`general` · `coding` · `planning` · `research`

## Architecture

```
Your agents ──POST/PATCH──→ FastAPI (SQLite) ←──poll──── React UI
```

No websockets, no auth, no complexity. Frontend polls every 3 seconds. Database is a single SQLite file (`board.db`).

## Agent Integration Pattern

```python
import httpx

BOARD = "http://localhost:8000/api"

# Agent picks up next available task for its specialization
tasks = httpx.get(f"{BOARD}/tasks?status=queued&specialization=coding").json()
if tasks:
    task = tasks[0]
    # Claim it
    httpx.patch(f"{BOARD}/tasks/{task['id']}", json={"status": "in_progress"})
    # Do work...
    # Mark for review
    httpx.patch(f"{BOARD}/tasks/{task['id']}", json={"status": "needs_review"})
```

## Roadmap

- [ ] Clipboard sharer tab
- [ ] Markdown editor tab
- [x] MCP server wrapper
- [ ] Agent context sharing between tasks

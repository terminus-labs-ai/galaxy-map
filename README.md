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

| Method   | Path                      | Description                                           |
| -------- | ------------------------- | ----------------------------------------------------- |
| `GET`    | `/api/tasks`              | List tasks (`?status=` and `?specialization=`)       |
| `POST`   | `/api/tasks`              | Create a task                                         |
| `GET`    | `/api/tasks/{id}`         | Get a single task                                     |
| `PATCH`  | `/api/tasks/{id}`         | Update a task (partial)                               |
| `DELETE` | `/api/tasks/{id}`         | Delete a task                                         |
| `POST`   | `/api/tasks/{id}/claim`   | Claim a queued task (atomically move to in_progress) |
| `PATCH`  | `/api/tasks/{id}/metadata`| Merge metadata into task (don't replace)              |
| `GET`    | `/api/statuses`           | List all valid statuses with metadata and descriptions |
| `GET`    | `/api/statuses/{key}`     | Get single status details including allowed transitions |
| `GET`    | `/api/specializations`    | List valid specializations                            |
| `GET`    | `/api/health`             | Health check                                          |

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

A task is considered "blocked" (`is_blocked: true`) when any task in its `blocked_by` list has a status other than `done` or `needs_review`.

### Move a task

```bash
curl -X PATCH http://localhost:8000/api/tasks/abc123 \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

### Get status information

Before moving a task, check what statuses are available and their descriptions:

```bash
# Get all statuses with descriptions
curl http://localhost:8000/api/statuses

# Response:
# [
#   {
#     "key": "backlog",
#     "label": "Backlog",
#     "description": "Task is planned but not yet ready to start. Waiting for resources or dependencies.",
#     "order": 0,
#     "color": "#71717a",
#     "allowed_transitions": ["queued"],
#     "terminal": false
#   },
#   ...
# ]
```

Get details for a single status:

```bash
curl http://localhost:8000/api/statuses/in_progress

# Returns full status object with allowed transitions
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

### Merge metadata (don't replace)

Add or update specific metadata keys without replacing the entire metadata:

```bash
curl -X PATCH http://localhost:8000/api/tasks/abc123/metadata \
  -H "Content-Type: application/json" \
  -d '{"progress": "50%", "notes": "Working on caching logic"}'
```

### Statuses (columns)

Statuses are defined in `backend/config/statuses.yaml` and loaded on startup. Current statuses:

- **backlog**: Task is planned but not yet ready to start
- **queued**: Task is ready to start, waiting for an agent
- **in_progress**: Task is actively being worked on
- **needs_review**: Task is complete but awaiting approval
- **needs_human**: Task requires human intervention or decision
- **done**: Task is complete and closed

Each status includes a description, allowed transitions, and a display color.

### Specializations

`general` · `intake` · `coding` · `planning` · `research` · `claude-code`

## Architecture

```
Your agents ──POST/PATCH──→ FastAPI (SQLite) ←──poll──── React UI
                          (config from YAML)
```

No websockets, no auth, no complexity. Frontend polls every 3 seconds and fetches status definitions from the API on mount. Database is a single SQLite file (`board.db`). Status configuration is loaded from `backend/config/statuses.yaml` on startup.

## Agent Integration Pattern

```python
import httpx

BOARD = "http://localhost:8000/api"

# Get available statuses and their descriptions
statuses = httpx.get(f"{BOARD}/statuses").json()

# Agent picks up next available task for its specialization
tasks = httpx.get(f"{BOARD}/tasks?status=queued&specialization=coding").json()
if tasks:
    task = tasks[0]
    
    # Claim it (atomically move from queued to in_progress)
    httpx.post(f"{BOARD}/tasks/{task['id']}/claim", 
               params={"claimed_by": "my-agent"})
    
    # Do work...
    
    # Check what statuses we can move to
    status_info = httpx.get(f"{BOARD}/statuses/in_progress").json()
    print(status_info["allowed_transitions"])  # See allowed next statuses
    
    # Mark for review
    httpx.patch(f"{BOARD}/tasks/{task['id']}", 
                json={"status": "needs_review"})
```

## MCP Server

The MCP server wraps the REST API as MCP tools, so any MCP-compatible client (Claude Code, Claude Desktop, Cursor, etc.) can manage tasks directly.

### Available Tools

| Tool | Description |
| ---- | ----------- |
| `list_tasks` | List tasks (optional `status` and `specialization` filters) |
| `create_task` | Create a new task |
| `get_task` | Get a single task by ID |
| `update_task` | Partial update of a task |
| `claim_task` | Atomically claim a queued task |
| `merge_metadata` | Merge keys into task metadata |
| `delete_task` | Delete a task |
| `list_statuses` | List all valid statuses with metadata and descriptions |
| `get_status_details` | Get details for a single status including allowed transitions |
| `list_specializations` | List valid specializations |
| `get_task_stats` | Get task statistics by status and specialization |

### Local (stdio)

Requires the Galaxy Map backend running on `localhost:8000`.

```bash
cd mcp-server
pip install .
galaxy-map-mcp
```

To point at a different backend:

```bash
GALAXY_MAP_URL=http://some-host:8000 galaxy-map-mcp
```

### Docker (SSE)

Runs alongside the backend and frontend via docker-compose. The MCP server is exposed on port `8080` with SSE transport.

```bash
docker compose up galaxy-map-mcp
```

### Client Configuration

#### Claude Code

Add to `.mcp.json`:

```json
{
  "mcpServers": {
    "galaxy-map": {
      "command": "galaxy-map-mcp",
      "env": {
        "GALAXY_MAP_URL": "http://localhost:8000"
      }
    }
  }
}
```

#### Claude Desktop

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "galaxy-map": {
      "command": "galaxy-map-mcp",
      "env": {
        "GALAXY_MAP_URL": "http://localhost:8000"
      }
    }
  }
}
```

### Environment Variables

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `GALAXY_MAP_URL` | `http://localhost:8000` | Base URL of the Galaxy Map API |
| `MCP_TRANSPORT` | `stdio` | Transport mode (`stdio`, `sse`, or `streamable-http`) |
| `MCP_HOST` | `0.0.0.0` | Host to bind MCP server to (SSE mode) |
| `MCP_PORT` | `8080` | Port to bind MCP server to (SSE mode) |

## Configuration

### Status Configuration (backend/config/statuses.yaml)

Define custom statuses with metadata:

```yaml
statuses:
  - key: backlog
    label: Backlog
    description: Task is planned but not yet ready to start. Waiting for resources or dependencies.
    order: 0
    color: "#71717a"
    allowed_transitions: [queued]
    terminal: false
```

**Fields**:
- `key`: Unique identifier (used in API and database)
- `label`: Display name for UI
- `description`: Human-readable description for agents
- `order`: Column position (lower numbers appear first)
- `color`: Hex color for column header
- `allowed_transitions`: List of valid next statuses (informational, not enforced yet)
- `terminal`: True if no transitions allowed

Changes to this file require restarting the backend.

## Database

Single SQLite file (`board.db`) with two tables:
- `tasks`: id, title, description, status, specialization, priority, blocked_by, metadata, created_at, updated_at
- `messages`: id, user_id, text, response, status, created_at, updated_at (for Telegram integration)

No migrations system — table schema is created on first run if it doesn't exist.

## Roadmap

- [ ] Transition validation (enforce allowed_transitions)
- [ ] Database constraints on status values
- [ ] Clipboard sharer tab
- [ ] Markdown editor tab
- [x] MCP server wrapper
- [x] Status configuration via YAML
- [x] Status descriptions for agents
- [ ] Agent context sharing between tasks

# CLAUDE.md

## Project Overview

Galaxy Map — minimal task tracker / kanban board for AI agents. REST API + React UI.

## Architecture

- **Backend**: Python FastAPI + async SQLite (`backend/main.py`), database file is `board.db`
- **Frontend**: React 18 + Vite (`frontend/src/App.jsx`), polls backend every 3 seconds
- No auth, no websockets

## Quick Start

```bash
# Backend
cd backend && pip install -r requirements.txt && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend && npm install && npm run dev
```

Frontend: http://localhost:5173 | API: http://localhost:8000/api

## Key Concepts

- **Statuses (columns)**: backlog → queued → in_progress → needs_review → done
- **Specializations**: general, coding, planning, research
- **Dependencies**: tasks have `blocked_by` list; `is_blocked` is true when any blocker isn't `done`
- **Metadata**: arbitrary JSON field on tasks for agent context

## API

All endpoints under `/api`. Main ones: `GET/POST /tasks`, `GET/PATCH/DELETE /tasks/{id}`, `GET /statuses`, `GET /specializations`, `GET /health`.

## MCP Server

- **Location**: `mcp-server/server.py` — wraps the REST API as MCP tools using `FastMCP`
- **Transport**: stdio (local) or SSE (Docker)
- **Config**: `GALAXY_MAP_URL` env var (default `http://localhost:8000`), `MCP_TRANSPORT` env var (default `stdio`)
- **Tools**: `list_tasks`, `create_task`, `get_task`, `update_task`, `delete_task`, `list_statuses`, `list_specializations`
- **Install**: pip-installable package, exposes `galaxy-map-mcp` console script
- **Docker**: runs as `galaxy-map-mcp` service in docker-compose, SSE transport on port 8080

```bash
# Local
pip install ./mcp-server && galaxy-map-mcp

# Docker (included in docker-compose.yml)
docker compose up galaxy-map-mcp
```

## Dev Notes

- Backend has no tests yet
- Frontend is a single-component app (`App.jsx`)
- SQLite DB is a single file — no migrations system

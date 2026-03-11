"""
Galaxy Map — minimal task tracker for AI agents.
FastAPI + SQLite backend.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import aiosqlite
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DB_PATH = Path(os.environ.get("DATABASE_PATH", Path(__file__).parent / "board.db"))

STATUSES = ["backlog", "queued", "in_progress", "needs_review", "done", "error"]
SPECIALIZATIONS = ["general", "coding", "planning", "research", "claude-code"]


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


async def get_db() -> aiosqlite.Connection:
  db = await aiosqlite.connect(DB_PATH)
  db.row_factory = aiosqlite.Row
  await db.execute("PRAGMA journal_mode=WAL")
  await db.execute("PRAGMA foreign_keys=ON")
  return db


async def init_db():
  db = await get_db()
  await db.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id              TEXT PRIMARY KEY,
            title           TEXT NOT NULL,
            description     TEXT NOT NULL DEFAULT '',
            status          TEXT NOT NULL DEFAULT 'backlog',
            specialization  TEXT NOT NULL DEFAULT 'general',
            priority        INTEGER NOT NULL DEFAULT 0,
            blocked_by      TEXT NOT NULL DEFAULT '[]',
            metadata        TEXT NOT NULL DEFAULT '{}',
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        )
    """)
  await db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
  await db.execute(
    "CREATE INDEX IF NOT EXISTS idx_tasks_specialization ON tasks(specialization)"
  )
  await db.commit()
  await db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
  await init_db()
  yield


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
  title="Galaxy Map",
  description="Minimal task tracker for AI agents",
  version="0.2.0",
  lifespan=lifespan,
)

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class TaskCreate(BaseModel):
  id: Optional[str] = None
  title: str
  description: str = ""
  status: str = "backlog"
  specialization: str = "general"
  priority: int = 0
  blocked_by: list[str] = Field(default_factory=list)
  metadata: dict = Field(default_factory=dict)


class TaskUpdate(BaseModel):
  title: Optional[str] = None
  description: Optional[str] = None
  status: Optional[str] = None
  specialization: Optional[str] = None
  priority: Optional[int] = None
  blocked_by: Optional[list[str]] = None
  metadata: Optional[dict] = None


class TaskResponse(BaseModel):
  id: str
  title: str
  description: str
  status: str
  specialization: str
  priority: int
  blocked_by: list[str]
  is_blocked: bool
  metadata: dict
  created_at: str
  updated_at: str


_COMPLETED_STATUSES = {"done", "needs_review"}


def row_to_task(row, all_tasks: list[dict] | None = None) -> dict:
  d = dict(row)
  d["metadata"] = json.loads(d["metadata"])
  d["blocked_by"] = json.loads(d["blocked_by"])
  if all_tasks is not None:
    blocker_statuses = {t["id"]: t["status"] for t in all_tasks}
    d["is_blocked"] = any(
      blocker_statuses.get(bid, "done") not in _COMPLETED_STATUSES
      for bid in d["blocked_by"]
    )
  else:
    d["is_blocked"] = len(d["blocked_by"]) > 0
  return d


async def fetch_all_tasks_raw(db) -> list[dict]:
  cursor = await db.execute("SELECT id, status FROM tasks")
  return [dict(r) for r in await cursor.fetchall()]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_status(status: str):
  if status not in STATUSES:
    raise HTTPException(400, f"Invalid status. Must be one of: {STATUSES}")


def validate_specialization(spec: str):
  if spec not in SPECIALIZATIONS:
    raise HTTPException(
      400, f"Invalid specialization. Must be one of: {SPECIALIZATIONS}"
    )


def validate_blocked_by(blocked_by: list[str], exclude_id: str = ""):
  if not blocked_by:
    return
  for bid in blocked_by:
    if bid == exclude_id:
      raise HTTPException(400, "A task cannot block itself")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/api/tasks", response_model=list[TaskResponse])
async def list_tasks(
  status: Optional[str] = Query(None),
  specialization: Optional[str] = Query(None),
):
  """List all tasks, optionally filtered by status and/or specialization."""
  db = await get_db()

  conditions = []
  params = []
  if status:
    validate_status(status)
    conditions.append("status = ?")
    params.append(status)
  if specialization:
    validate_specialization(specialization)
    conditions.append("specialization = ?")
    params.append(specialization)

  where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
  cursor = await db.execute(
    f"SELECT * FROM tasks {where} ORDER BY priority DESC, created_at ASC",
    params,
  )
  rows = await cursor.fetchall()
  all_raw = await fetch_all_tasks_raw(db)
  await db.close()
  return [row_to_task(r, all_raw) for r in rows]


def _title_similarity(title1: str, title2: str) -> float:
  """Simple similarity check for task titles."""
  t1 = title1.lower().strip()
  t2 = title2.lower().strip()
  if t1 == t2:
    return 1.0
  # Check if one contains the other (after stripping common prefixes)
  common_prefixes = ["create ", "add ", "implement ", "fix ", "update ", "remove "]
  for prefix in common_prefixes:
    if t1.startswith(prefix):
      t1 = t1[len(prefix):].strip()
    if t2.startswith(prefix):
      t2 = t2[len(prefix):].strip()
  if t1 == t2:
    return 1.0
  # Check if titles are very similar (share most significant words)
  words1 = set(t1.split()) - {"the", "a", "an", "and", "or", "to", "of", "in", "for", "on", "with"}
  words2 = set(t2.split()) - {"the", "a", "an", "and", "or", "to", "of", "in", "for", "on", "with"}
  if not words1 or not words2:
    return 0.0
  intersection = len(words1 & words2)
  union = len(words1 | words2)
  return intersection / union if union > 0 else 0.0


@app.post("/api/tasks", response_model=TaskResponse, status_code=201)
async def create_task(task: TaskCreate):
  """Create a new task."""
  validate_status(task.status)
  validate_specialization(task.specialization)

  now = datetime.now(timezone.utc).isoformat()
  task_id = task.id if task.id is not None else uuid.uuid4().hex[:12]

  validate_blocked_by(task.blocked_by, task_id)

  db = await get_db()

  if task.id is not None:
    cursor = await db.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
    if await cursor.fetchone():
      await db.close()
      raise HTTPException(409, f"Task with id '{task_id}' already exists")

  # Check for duplicate tasks with similar titles
  cursor = await db.execute(
    "SELECT id, title, status FROM tasks WHERE status NOT IN ('done', 'error')"
  )
  existing_tasks = await cursor.fetchall()
  for row in existing_tasks:
    existing_title = row["title"]
    similarity = _title_similarity(task.title, existing_title)
    if similarity >= 0.85:  # 85% similarity threshold
      await db.close()
      raise HTTPException(
        409,
        f"Potential duplicate task found: '{existing_title}' "
        f"(similarity: {similarity:.0%}). Use update_task to modify the existing task instead.",
      )

  await db.execute(
    """INSERT INTO tasks (id, title, description, status, specialization, priority, blocked_by, metadata, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    (
      task_id,
      task.title,
      task.description,
      task.status,
      task.specialization,
      task.priority,
      json.dumps(task.blocked_by),
      json.dumps(task.metadata),
      now,
      now,
    ),
  )
  await db.commit()

  cursor = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
  row = await cursor.fetchone()
  all_raw = await fetch_all_tasks_raw(db)
  await db.close()
  return row_to_task(row, all_raw)


@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
  """Get a single task by ID."""
  db = await get_db()
  cursor = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
  row = await cursor.fetchone()
  if not row:
    await db.close()
    raise HTTPException(404, "Task not found")
  all_raw = await fetch_all_tasks_raw(db)
  await db.close()
  return row_to_task(row, all_raw)


@app.patch("/api/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, updates: TaskUpdate):
  """Update a task. Only provided fields are changed."""
  db = await get_db()
  cursor = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
  row = await cursor.fetchone()
  if not row:
    await db.close()
    raise HTTPException(404, "Task not found")

  current = dict(row)
  now = datetime.now(timezone.utc).isoformat()

  new_title = updates.title if updates.title is not None else current["title"]
  new_desc = (
    updates.description if updates.description is not None else current["description"]
  )
  new_status = updates.status if updates.status is not None else current["status"]
  new_spec = (
    updates.specialization
    if updates.specialization is not None
    else current["specialization"]
  )
  new_priority = (
    updates.priority if updates.priority is not None else current["priority"]
  )
  new_blocked = (
    json.dumps(updates.blocked_by)
    if updates.blocked_by is not None
    else current["blocked_by"]
  )
  new_metadata = (
    json.dumps(updates.metadata)
    if updates.metadata is not None
    else current["metadata"]
  )

  validate_status(new_status)
  validate_specialization(new_spec)
  if updates.blocked_by is not None:
    validate_blocked_by(updates.blocked_by, task_id)

  await db.execute(
    """UPDATE tasks
           SET title = ?, description = ?, status = ?, specialization = ?,
               priority = ?, blocked_by = ?, metadata = ?, updated_at = ?
           WHERE id = ?""",
    (
      new_title,
      new_desc,
      new_status,
      new_spec,
      new_priority,
      new_blocked,
      new_metadata,
      now,
      task_id,
    ),
  )
  await db.commit()

  cursor = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
  row = await cursor.fetchone()
  all_raw = await fetch_all_tasks_raw(db)
  await db.close()
  return row_to_task(row, all_raw)


@app.post("/api/tasks/{task_id}/claim", response_model=TaskResponse)
async def claim_task(task_id: str, claimed_by: str = Query(...)):
  """Atomically claim a queued, unblocked task.

  Sets status to in_progress and stores claimed_by in metadata.
  Returns 409 if the task is not queued, is blocked, or already claimed.
  """
  db = await get_db()
  cursor = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
  row = await cursor.fetchone()
  if not row:
    await db.close()
    raise HTTPException(404, "Task not found")

  current = dict(row)
  if current["status"] != "queued":
    await db.close()
    raise HTTPException(409, f"Task is '{current['status']}', not 'queued'")

  # Check if blocked
  blocked_by = json.loads(current["blocked_by"])
  if blocked_by:
    all_raw = await fetch_all_tasks_raw(db)
    blocker_statuses = {t["id"]: t["status"] for t in all_raw}
    is_blocked = any(blocker_statuses.get(bid, "done") not in _COMPLETED_STATUSES for bid in blocked_by)
    if is_blocked:
      await db.close()
      raise HTTPException(409, "Task is blocked by unfinished dependencies")

  now = datetime.now(timezone.utc).isoformat()
  metadata = json.loads(current["metadata"])
  metadata["claimed_by"] = claimed_by

  await db.execute(
    """UPDATE tasks SET status = 'in_progress', metadata = ?, updated_at = ? WHERE id = ?""",
    (json.dumps(metadata), now, task_id),
  )
  await db.commit()

  cursor = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
  row = await cursor.fetchone()
  all_raw = await fetch_all_tasks_raw(db)
  await db.close()
  return row_to_task(row, all_raw)


@app.patch("/api/tasks/{task_id}/metadata", response_model=TaskResponse)
async def merge_task_metadata(task_id: str, patch: dict):
  """Merge keys into a task's metadata (instead of replacing it).

  Existing keys not in the patch are preserved. Keys set to null are removed.
  """
  db = await get_db()
  cursor = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
  row = await cursor.fetchone()
  if not row:
    await db.close()
    raise HTTPException(404, "Task not found")

  current = dict(row)
  metadata = json.loads(current["metadata"])

  for key, value in patch.items():
    if value is None:
      metadata.pop(key, None)
    else:
      metadata[key] = value

  now = datetime.now(timezone.utc).isoformat()
  await db.execute(
    "UPDATE tasks SET metadata = ?, updated_at = ? WHERE id = ?",
    (json.dumps(metadata), now, task_id),
  )
  await db.commit()

  cursor = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
  row = await cursor.fetchone()
  all_raw = await fetch_all_tasks_raw(db)
  await db.close()
  return row_to_task(row, all_raw)


@app.delete("/api/tasks/{task_id}", status_code=204)
async def delete_task(task_id: str):
  """Delete a task. Also removes it from any other task's blocked_by list."""
  db = await get_db()
  cursor = await db.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
  row = await cursor.fetchone()
  if not row:
    await db.close()
    raise HTTPException(404, "Task not found")

  # Clean up references in other tasks
  cursor = await db.execute(
    "SELECT id, blocked_by FROM tasks WHERE blocked_by LIKE ?", (f"%{task_id}%",)
  )
  referencing = await cursor.fetchall()
  for ref in referencing:
    blockers = json.loads(ref["blocked_by"])
    if task_id in blockers:
      blockers.remove(task_id)
      await db.execute(
        "UPDATE tasks SET blocked_by = ?, updated_at = ? WHERE id = ?",
        (json.dumps(blockers), datetime.now(timezone.utc).isoformat(), ref["id"]),
      )

  await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
  await db.commit()
  await db.close()


@app.get("/api/statuses")
async def list_statuses():
  """Return the ordered list of valid statuses (columns)."""
  return STATUSES


@app.get("/api/specializations")
async def list_specializations():
  """Return the list of valid specializations."""
  return SPECIALIZATIONS


@app.get("/api/health")
async def health():
  return {"status": "ok", "version": "0.2.0"}

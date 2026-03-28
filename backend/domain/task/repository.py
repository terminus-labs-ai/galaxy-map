"""Task repository (data access layer)."""

import json
from datetime import datetime, timezone
import aiosqlite
from .model import Task


class TaskRepository:
  """Repository for Task persistence."""

  def __init__(self, db: aiosqlite.Connection):
    self.db = db

  async def get_by_id(self, task_id: str) -> Task | None:
    """Fetch task by ID."""
    cursor = await self.db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = await cursor.fetchone()
    return Task.from_row(row) if row else None

  async def get_all(self) -> list[Task]:
    """Fetch all tasks."""
    cursor = await self.db.execute(
      "SELECT * FROM tasks ORDER BY priority DESC, created_at ASC"
    )
    rows = await cursor.fetchall()
    return [Task.from_row(r) for r in rows]

  async def list_by_status(self, statuses: list[str]) -> list[Task]:
    """Fetch tasks by status list."""
    placeholders = ",".join(["?" for _ in statuses])
    cursor = await self.db.execute(
      f"SELECT * FROM tasks WHERE status IN ({placeholders}) ORDER BY priority DESC, created_at ASC",
      statuses,
    )
    rows = await cursor.fetchall()
    return [Task.from_row(r) for r in rows]

  async def list_by_specialization(self, specialization: str) -> list[Task]:
    """Fetch tasks by specialization."""
    cursor = await self.db.execute(
      "SELECT * FROM tasks WHERE specialization = ? ORDER BY priority DESC, created_at ASC",
      (specialization,),
    )
    rows = await cursor.fetchall()
    return [Task.from_row(r) for r in rows]

  async def list_by_status_and_specialization(
    self, statuses: list[str], specialization: str
  ) -> list[Task]:
    """Fetch tasks by both status and specialization."""
    placeholders = ",".join(["?" for _ in statuses])
    cursor = await self.db.execute(
      f"SELECT * FROM tasks WHERE status IN ({placeholders}) AND specialization = ? "
      f"ORDER BY priority DESC, created_at ASC",
      statuses + [specialization],
    )
    rows = await cursor.fetchall()
    return [Task.from_row(r) for r in rows]

  async def list_by_project(self, project_id: str) -> list[Task]:
    """Fetch tasks by project_id."""
    cursor = await self.db.execute(
      "SELECT * FROM tasks WHERE project_id = ? ORDER BY priority DESC, created_at ASC",
      (project_id,),
    )
    rows = await cursor.fetchall()
    return [Task.from_row(r) for r in rows]

  async def get_distinct_projects(self) -> list[dict]:
    """Get distinct project_ids with task counts."""
    cursor = await self.db.execute(
      "SELECT project_id, COUNT(*) as task_count FROM tasks WHERE project_id IS NOT NULL GROUP BY project_id ORDER BY project_id"
    )
    rows = await cursor.fetchall()
    return [{"project_id": row["project_id"], "task_count": row["task_count"]} for row in rows]

  async def search(self, query: str) -> list[Task]:
    """Search tasks by ID, title, description, or metadata (using SQL LIKE for efficiency)."""
    q_lower = query.lower()
    pattern = f"%{query}%"  # Case-insensitive LIKE pattern

    # Query by ID (exact match), title, description, or metadata
    cursor = await self.db.execute(
      """SELECT * FROM tasks 
               WHERE LOWER(id) = ? 
               OR LOWER(title) LIKE ? 
               OR LOWER(description) LIKE ?
               OR LOWER(metadata) LIKE ?""",
      (q_lower, pattern, pattern, pattern),
    )
    rows = await cursor.fetchall()

    results = [Task.from_row(r) for r in rows]

    # Sort by relevance score
    def relevance_score(task: Task) -> tuple:
      """Score for sorting: (type, position). Lower = better match."""
      title = task.title.lower()
      desc = task.description.lower()
      meta = json.dumps(task.metadata).lower()

      # Exact ID match is best
      if q_lower == task.id.lower():
        return (0, 0)

      # Title matches (by position)
      if title.startswith(q_lower):
        return (1, 0)  # Starts with query
      title_pos = title.find(q_lower)
      if title_pos >= 0:
        return (2, title_pos)  # Contains query

      # Description matches
      if desc.startswith(q_lower):
        return (3, 0)
      desc_pos = desc.find(q_lower)
      if desc_pos >= 0:
        return (4, desc_pos)

      # Metadata matches
      meta_pos = meta.find(q_lower)
      if meta_pos >= 0:
        return (5, meta_pos)

      return (6, 0)  # Shouldn't reach here if query was found

    results.sort(key=relevance_score)
    return results

  async def create(self, task: Task) -> Task:
    """Persist a new task."""
    try:
      await self.db.execute(
        """INSERT INTO tasks (id, title, description, status, specialization, priority, blocked_by, metadata, created_at, updated_at, project_id, parent_task_id, subagent_type, subagent_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
          task.id,
          task.title,
          task.description,
          task.status,
          task.specialization,
          task.priority,
          json.dumps(task.blocked_by),
          json.dumps(task.metadata),
          task.created_at,
          task.updated_at,
          task.project_id,
          task.parent_task_id,
          task.subagent_type,
          task.subagent_status,
        ),
      )
    except Exception as e:
      print(f"Failed to create task at db: {e}")
    await self.db.commit()
    return task

  async def update(self, task: Task) -> Task:
    """Update an existing task."""
    task.updated_at = datetime.now(timezone.utc).isoformat()
    await self.db.execute(
      """UPDATE tasks
               SET title = ?, description = ?, status = ?, specialization = ?,
                   priority = ?, blocked_by = ?, metadata = ?, updated_at = ?, project_id = ?, parent_task_id = ?, subagent_type = ?, subagent_status = ?
               WHERE id = ?""",
      (
        task.title,
        task.description,
        task.status,
        task.specialization,
        task.priority,
        json.dumps(task.blocked_by),
        json.dumps(task.metadata),
        task.updated_at,
        task.project_id,
        task.parent_task_id,
        task.subagent_type,
        task.subagent_status,
        task.id,
      ),
    )
    await self.db.commit()
    return task

  async def delete(self, task_id: str):
    """Delete a task and clean up references."""
    # Remove from other tasks' blocked_by lists
    cursor = await self.db.execute(
      "SELECT id, blocked_by FROM tasks WHERE blocked_by LIKE ?",
      (f"%{task_id}%",),
    )
    referencing = await cursor.fetchall()

    for ref in referencing:
      blockers = json.loads(ref["blocked_by"])
      if task_id in blockers:
        blockers.remove(task_id)
        await self.db.execute(
          "UPDATE tasks SET blocked_by = ?, updated_at = ? WHERE id = ?",
          (json.dumps(blockers), datetime.now(timezone.utc).isoformat(), ref["id"]),
        )

    # Delete history entries (FK constraint)
    await self.db.execute("DELETE FROM task_history WHERE task_id = ?", (task_id,))
    await self.db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    await self.db.commit()

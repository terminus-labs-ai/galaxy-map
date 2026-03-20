"""Task history repository (data access layer)."""

import uuid
from datetime import datetime, timezone
import aiosqlite
from .history_model import TaskHistory


class TaskHistoryRepository:
    """Repository for TaskHistory persistence."""

    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def create(self, history: TaskHistory) -> TaskHistory:
        """Persist a new history entry."""
        try:
            await self.db.execute(
                """INSERT INTO task_history (id, task_id, event_type, old_value, new_value, changed_by, timestamp, details)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    history.id,
                    history.task_id,
                    history.event_type,
                    history.old_value,
                    history.new_value,
                    history.changed_by,
                    history.timestamp,
                    history.details if history.details else None,
                ),
            )
            await self.db.commit()
        except Exception as e:
            print(f"Failed to create task history: {e}")
            raise
        return history

    async def get_by_task_id(
        self, task_id: str, limit: int = 100, offset: int = 0
    ) -> list[TaskHistory]:
        """Fetch history entries for a task, ordered by timestamp descending."""
        cursor = await self.db.execute(
            """SELECT * FROM task_history 
               WHERE task_id = ? 
               ORDER BY timestamp DESC 
               LIMIT ? OFFSET ?""",
            (task_id, limit, offset),
        )
        rows = await cursor.fetchall()
        return [TaskHistory.from_row(r) for r in rows]

    async def get_all(self) -> list[TaskHistory]:
        """Fetch all history entries."""
        cursor = await self.db.execute(
            "SELECT * FROM task_history ORDER BY timestamp DESC"
        )
        rows = await cursor.fetchall()
        return [TaskHistory.from_row(r) for r in rows]
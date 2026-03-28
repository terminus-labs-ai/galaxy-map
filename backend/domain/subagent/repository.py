"""Subagent repositories."""

import json
from typing import Optional, List
import aiosqlite
from .model import Subagent, SubagentTask


class SubagentRepository:
    """Repository for subagent entities."""
    
    def __init__(self, db: aiosqlite.Connection):
        self.db = db
    
    async def create_subagent(self, subagent: Subagent) -> Subagent:
        """Create a new subagent."""
        await self.db.execute(
            """INSERT INTO subagents (id, name, specialization, description, status, metadata, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                subagent.id,
                subagent.name,
                subagent.specialization,
                subagent.description,
                subagent.status,
                json.dumps(subagent.metadata),
                subagent.created_at,
                subagent.updated_at,
            ),
        )
        await self.db.commit()
        return subagent
    
    async def get_subagent(self, subagent_id: str) -> Optional[Subagent]:
        """Get a subagent by ID."""
        cursor = await self.db.execute(
            "SELECT * FROM subagents WHERE id = ?", (subagent_id,)
        )
        row = await cursor.fetchone()
        if row:
            return self._row_to_subagent(row)
        return None
    
    async def list_subagents(self, specialization: Optional[str] = None) -> List[Subagent]:
        """List subagents, optionally filtered by specialization."""
        if specialization:
            cursor = await self.db.execute(
                "SELECT * FROM subagents WHERE specialization = ? ORDER BY created_at DESC",
                (specialization,)
            )
        else:
            cursor = await self.db.execute(
                "SELECT * FROM subagents ORDER BY created_at DESC"
            )
        rows = await cursor.fetchall()
        return [self._row_to_subagent(row) for row in rows]
    
    async def update_subagent(self, subagent: Subagent) -> Subagent:
        """Update a subagent."""
        await self.db.execute(
            """UPDATE subagents SET name = ?, specialization = ?, description = ?, 
               status = ?, metadata = ?, updated_at = ? WHERE id = ?""",
            (
                subagent.name,
                subagent.specialization,
                subagent.description,
                subagent.status,
                json.dumps(subagent.metadata),
                subagent.updated_at,
                subagent.id,
            ),
        )
        await self.db.commit()
        return subagent
    
    async def delete_subagent(self, subagent_id: str) -> None:
        """Delete a subagent."""
        await self.db.execute("DELETE FROM subagents WHERE id = ?", (subagent_id,))
        await self.db.commit()
    
    async def _row_to_subagent(self, row) -> Subagent:
        """Convert a database row to a Subagent object."""
        return Subagent(
            id=row["id"],
            name=row["name"],
            specialization=row["specialization"],
            description=row["description"],
            status=row["status"],
            metadata=json.loads(row["metadata"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class SubagentTaskRepository:
    """Repository for subagent task assignments."""
    
    def __init__(self, db: aiosqlite.Connection):
        self.db = db
    
    async def create_subagent_task(self, subagent_task: SubagentTask) -> SubagentTask:
        """Create a new subagent task assignment."""
        await self.db.execute(
            """INSERT INTO subagent_tasks (id, task_id, subagent_id, status, assigned_at, 
               completed_at, result, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                subagent_task.id,
                subagent_task.task_id,
                subagent_task.subagent_id,
                subagent_task.status,
                subagent_task.assigned_at,
                subagent_task.completed_at,
                subagent_task.result,
                json.dumps(subagent_task.metadata),
            ),
        )
        await self.db.commit()
        return subagent_task
    
    async def get_subagent_task(self, subagent_task_id: str) -> Optional[SubagentTask]:
        """Get a subagent task by ID."""
        cursor = await self.db.execute(
            "SELECT * FROM subagent_tasks WHERE id = ?", (subagent_task_id,)
        )
        row = await cursor.fetchone()
        if row:
            return self._row_to_subagent_task(row)
        return None
    
    async def get_subagent_tasks_by_task_id(self, task_id: str) -> List[SubagentTask]:
        """Get all subagent tasks for a given task ID."""
        cursor = await self.db.execute(
            "SELECT * FROM subagent_tasks WHERE task_id = ? ORDER BY assigned_at DESC",
            (task_id,)
        )
        rows = await cursor.fetchall()
        return [self._row_to_subagent_task(row) for row in rows]
    
    async def get_subagent_tasks_by_subagent_id(self, subagent_id: str) -> List[SubagentTask]:
        """Get all subagent tasks for a given subagent ID."""
        cursor = await self.db.execute(
            "SELECT * FROM subagent_tasks WHERE subagent_id = ? ORDER BY assigned_at DESC",
            (subagent_id,)
        )
        rows = await cursor.fetchall()
        return [self._row_to_subagent_task(row) for row in rows]
    
    async def update_subagent_task(self, subagent_task: SubagentTask) -> SubagentTask:
        """Update a subagent task."""
        await self.db.execute(
            """UPDATE subagent_tasks SET status = ?, completed_at = ?, result = ?, 
               metadata = ? WHERE id = ?""",
            (
                subagent_task.status,
                subagent_task.completed_at,
                subagent_task.result,
                json.dumps(subagent_task.metadata),
                subagent_task.id,
            ),
        )
        await self.db.commit()
        return subagent_task
    
    async def _row_to_subagent_task(self, row) -> SubagentTask:
        """Convert a database row to a SubagentTask object."""
        return SubagentTask(
            id=row["id"],
            task_id=row["task_id"],
            subagent_id=row["subagent_id"],
            status=row["status"],
            assigned_at=row["assigned_at"],
            completed_at=row["completed_at"],
            result=row["result"],
            metadata=json.loads(row["metadata"]),
        )
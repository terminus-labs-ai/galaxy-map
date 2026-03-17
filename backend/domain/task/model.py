"""Task aggregate root."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Task:
    """Task aggregate."""

    id: str
    title: str
    description: str = ""
    status: str = "backlog"
    specialization: str = "general"
    priority: int = 0
    blocked_by: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    project_id: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @staticmethod
    def from_row(row, all_tasks: Optional[list["Task"]] = None) -> "Task":
        """Construct Task from DB row."""
        task = Task(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status=row["status"],
            specialization=row["specialization"],
            priority=row["priority"],
            blocked_by=json.loads(row["blocked_by"]),
            metadata=json.loads(row["metadata"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            project_id=row["project_id"] if "project_id" in row.keys() else None,
        )
        return task

    def is_blocked(self, all_tasks: Optional[list["Task"]] = None, completed_statuses: Optional[list[str]] = None) -> bool:
        """Check if task is blocked by unfinished dependencies."""
        if not self.blocked_by:
            return False

        if completed_statuses is None:
            from core import Config
            completed_statuses = Config.completed_statuses()

        completed = set(completed_statuses)

        if all_tasks is not None:
            status_map = {t.id: t.status for t in all_tasks}
            return any(status_map.get(bid, "done") not in completed for bid in self.blocked_by)

        return True

    def to_dict(self, is_blocked: Optional[bool] = None) -> dict:
        """Convert to response dict."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "specialization": self.specialization,
            "priority": self.priority,
            "blocked_by": self.blocked_by,
            "is_blocked": is_blocked if is_blocked is not None else self.is_blocked(),
            "metadata": self.metadata,
            "project_id": self.project_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

"""Task history/audit log model."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class TaskHistory:
    """Task history/audit log entry."""

    id: str
    task_id: str
    event_type: str  # status_change, metadata_update, assignment, comment
    old_value: str | None = None
    new_value: str | None = None
    changed_by: str = "system"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details: dict = field(default_factory=dict)

    @staticmethod
    def from_row(row) -> "TaskHistory":
        """Construct TaskHistory from DB row."""
        return TaskHistory(
            id=row["id"],
            task_id=row["task_id"],
            event_type=row["event_type"],
            old_value=row["old_value"],
            new_value=row["new_value"],
            changed_by=row["changed_by"],
            timestamp=row["timestamp"],
            details=json.loads(row["details"]) if row["details"] else {},
        )

    def to_dict(self) -> dict:
        """Convert to response dict."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "event_type": self.event_type,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "changed_by": self.changed_by,
            "timestamp": self.timestamp,
            "details": self.details,
        }
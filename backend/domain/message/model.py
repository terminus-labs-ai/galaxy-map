"""Message aggregate root."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Message:
    """Message aggregate."""

    id: str
    user_id: str
    text: str
    response: Optional[str] = None
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @staticmethod
    def from_row(row) -> "Message":
        """Construct Message from DB row."""
        return Message(
            id=row["id"],
            user_id=row["user_id"],
            text=row["text"],
            response=row["response"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def to_dict(self) -> dict:
        """Convert to response dict."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "text": self.text,
            "response": self.response,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

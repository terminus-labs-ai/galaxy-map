"""Message repository."""

from datetime import datetime, timezone
import aiosqlite
from .model import Message


class MessageRepository:
    """Repository for Message persistence."""

    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def get_by_id(self, message_id: str) -> Message | None:
        """Fetch message by ID."""
        cursor = await self.db.execute("SELECT * FROM messages WHERE id = ?", (message_id,))
        row = await cursor.fetchone()
        return Message.from_row(row) if row else None

    async def list_all(self) -> list[Message]:
        """Fetch all messages."""
        cursor = await self.db.execute("SELECT * FROM messages ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        return [Message.from_row(r) for r in rows]

    async def list_by_status(self, status: str) -> list[Message]:
        """Fetch messages by status."""
        cursor = await self.db.execute(
            "SELECT * FROM messages WHERE status = ? ORDER BY created_at DESC",
            (status,),
        )
        rows = await cursor.fetchall()
        return [Message.from_row(r) for r in rows]

    async def create(self, message: Message) -> Message:
        """Persist a new message."""
        await self.db.execute(
            """INSERT INTO messages (id, user_id, text, response, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                message.id,
                message.user_id,
                message.text,
                message.response,
                message.status,
                message.created_at,
                message.updated_at,
            ),
        )
        await self.db.commit()
        return message

    async def update(self, message: Message) -> Message:
        """Update an existing message."""
        message.updated_at = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            """UPDATE messages
               SET user_id = ?, text = ?, response = ?, status = ?, updated_at = ?
               WHERE id = ?""",
            (
                message.user_id,
                message.text,
                message.response,
                message.status,
                message.updated_at,
                message.id,
            ),
        )
        await self.db.commit()
        return message

"""Message service."""

import uuid
import aiosqlite
from core import Config, MessageNotFound
from .model import Message
from .repository import MessageRepository


class MessageService:
    """Encapsulates message business logic."""

    def __init__(self, db: aiosqlite.Connection):
        self.db = db
        self.repo = MessageRepository(db)

    async def create_message(self, user_id: str, text: str) -> Message:
        """Create a new message."""
        message = Message(
            id=uuid.uuid4().hex[:12],
            user_id=user_id,
            text=text,
            status=Config.get("messages.default_status", "pending"),
        )
        return await self.repo.create(message)

    async def get_message(self, message_id: str) -> Message:
        """Fetch a message by ID."""
        message = await self.repo.get_by_id(message_id)
        if not message:
            raise MessageNotFound(message_id)
        return message

    async def list_messages(self, status: str | None = None) -> list[Message]:
        """List messages, optionally filtered by status."""
        if status:
            return await self.repo.list_by_status(status)
        return await self.repo.list_all()

    async def update_message(
        self,
        message_id: str,
        response: str | None = None,
        status: str | None = None,
    ) -> Message:
        """Update a message."""
        message = await self.get_message(message_id)

        if response is not None:
            message.response = response
        if status is not None:
            message.status = status

        return await self.repo.update(message)

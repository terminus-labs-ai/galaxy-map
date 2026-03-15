"""Message routes."""

from fastapi import APIRouter, Query
from infrastructure import get_db
from domain import MessageService
from api.schemas import MessageCreate, MessageUpdate, MessageResponse


router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.post("", response_model=MessageResponse, status_code=201)
async def create_message(msg: MessageCreate):
    """Create a new message."""
    db = await get_db()
    service = MessageService(db)

    created = await service.create_message(msg.user_id, msg.text)
    result = created.to_dict()

    await db.close()
    return result


@router.get("", response_model=list[MessageResponse])
async def list_messages(status: str | None = Query(None)):
    """List messages, optionally filtered by status."""
    db = await get_db()
    service = MessageService(db)

    messages = await service.list_messages(status)
    result = [m.to_dict() for m in messages]

    await db.close()
    return result


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(message_id: str):
    """Get a single message by ID."""
    db = await get_db()
    service = MessageService(db)

    message = await service.get_message(message_id)
    result = message.to_dict()

    await db.close()
    return result


@router.patch("/{message_id}", response_model=MessageResponse)
async def update_message(message_id: str, updates: MessageUpdate):
    """Update a message."""
    db = await get_db()
    service = MessageService(db)

    updated = await service.update_message(
        message_id,
        response=updates.response,
        status=updates.status,
    )
    result = updated.to_dict()

    await db.close()
    return result

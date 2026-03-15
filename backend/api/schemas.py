"""API request/response schemas."""

from typing import Optional
from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    """Create task request."""
    id: Optional[str] = None
    title: str
    description: str = ""
    status: str = "backlog"
    specialization: str = "general"
    priority: int = 0
    blocked_by: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class TaskUpdate(BaseModel):
    """Update task request (partial)."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    specialization: Optional[str] = None
    priority: Optional[int] = None
    blocked_by: Optional[list[str]] = None
    metadata: Optional[dict] = None


class TaskResponse(BaseModel):
    """Task response."""
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


class StatusResponse(BaseModel):
    """Status configuration response."""
    key: str
    label: str
    description: str
    order: int
    color: str
    allowed_transitions: list[str]
    terminal: bool


class MessageCreate(BaseModel):
    """Create message request."""
    user_id: str
    text: str


class MessageUpdate(BaseModel):
    """Update message request."""
    response: Optional[str] = None
    status: Optional[str] = None


class MessageResponse(BaseModel):
    """Message response."""
    id: str
    user_id: str
    text: str
    response: Optional[str] = None
    status: str
    created_at: str
    updated_at: str

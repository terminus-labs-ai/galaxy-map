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
    project_id: Optional[str] = None


class TaskUpdate(BaseModel):
    """Update task request (partial)."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    specialization: Optional[str] = None
    priority: Optional[int] = None
    blocked_by: Optional[list[str]] = None
    metadata: Optional[dict] = None
    project_id: Optional[str] = None


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
    project_id: Optional[str] = None
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


class TaskHistoryResponse(BaseModel):
    """Task history entry response."""
    id: str
    task_id: str
    event_type: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    changed_by: str
    timestamp: str
    details: dict


# --- Project Plan schemas ---


class TaskNode(BaseModel):
    """A task node in a project plan tree."""
    title: str
    specialization: str
    description: str
    subtasks: list["TaskNode"] = Field(default_factory=list)


class ProjectPlanCreate(BaseModel):
    """Create project plan request."""
    project_id: str
    shared_metadata: dict = Field(default_factory=dict)
    tasks: list[TaskNode]


class ProjectPlanTaskResponse(BaseModel):
    """A task node in the project plan response tree."""
    id: str
    title: str
    specialization: str
    status: str
    blocked_by: list[str]
    priority: int
    subtasks: list["ProjectPlanTaskResponse"] = Field(default_factory=list)


class ProjectPlanResponse(BaseModel):
    """Project plan creation response."""
    project_id: str
    shared_metadata: dict = Field(default_factory=dict)
    tasks_created: int
    task_tree: list[ProjectPlanTaskResponse]


class SubagentTaskCreate(BaseModel):
    """Create subagent task request."""
    parent_task_id: str
    title: str
    description: str = ""
    status: str = "backlog"
    specialization: str = "general"
    priority: int = 0
    metadata: dict = Field(default_factory=dict)
    project_id: Optional[str] = None

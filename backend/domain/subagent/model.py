"""Subagent models."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import uuid


@dataclass
class Subagent:
    """A specialized subagent that can handle specific task types."""
    
    id: str
    name: str
    specialization: str
    description: str = ""
    status: str = "active"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class SubagentTask:
    """A task assigned to a subagent."""
    
    id: str
    task_id: str
    subagent_id: str
    status: str = "pending"
    assigned_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    result: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
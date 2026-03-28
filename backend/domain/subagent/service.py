"""Subagent service (business logic layer)."""

import uuid
from datetime import datetime, timezone
import aiosqlite
from .model import Subagent, SubagentTask
from .repository import SubagentRepository, SubagentTaskRepository
from core import Config, TaskNotFound


class SubagentService:
    """Encapsulates subagent business logic."""
    
    def __init__(self, db: aiosqlite.Connection):
        self.db = db
        self.repo = SubagentRepository(db)
        self.task_repo = SubagentTaskRepository(db)
    
    async def create_subagent(
        self,
        name: str,
        specialization: str,
        description: str = "",
        status: str = "active",
        metadata: dict = None
    ) -> Subagent:
        """Create a new subagent."""
        metadata = metadata or {}
        
        subagent = Subagent(
            id=uuid.uuid4().hex[:12],
            name=name,
            specialization=specialization,
            description=description,
            status=status,
            metadata=metadata,
        )
        
        return await self.repo.create_subagent(subagent)
    
    async def get_subagent(self, subagent_id: str) -> Subagent:
        """Fetch a subagent by ID."""
        subagent = await self.repo.get_subagent(subagent_id)
        if not subagent:
            raise TaskNotFound(subagent_id)
        return subagent
    
    async def list_subagents(self, specialization: str = None) -> list[Subagent]:
        """List subagents, with optional filtering by specialization."""
        return await self.repo.list_subagents(specialization)
    
    async def update_subagent(
        self,
        subagent_id: str,
        name: str = None,
        specialization: str = None,
        description: str = None,
        status: str = None,
        metadata: dict = None
    ) -> Subagent:
        """Update a subagent (partial update)."""
        subagent = await self.get_subagent(subagent_id)
        
        if name is not None:
            subagent.name = name
        if specialization is not None:
            subagent.specialization = specialization
        if description is not None:
            subagent.description = description
        if status is not None:
            subagent.status = status
        if metadata is not None:
            subagent.metadata = metadata
            
        subagent.updated_at = datetime.now(timezone.utc).isoformat()
        
        return await self.repo.update_subagent(subagent)
    
    async def delete_subagent(self, subagent_id: str) -> None:
        """Delete a subagent."""
        await self.repo.delete_subagent(subagent_id)
    
    async def assign_task_to_subagent(
        self,
        task_id: str,
        subagent_id: str,
        metadata: dict = None
    ) -> SubagentTask:
        """Assign a task to a subagent."""
        # Verify the task exists
        from domain.task.service import TaskService
        task_service = TaskService(self.db)
        task = await task_service.get_task(task_id)
        
        # Verify the subagent exists
        subagent = await self.get_subagent(subagent_id)
        
        # Create the subagent task assignment
        subagent_task = SubagentTask(
            id=uuid.uuid4().hex[:12],
            task_id=task_id,
            subagent_id=subagent_id,
            status="pending",
            metadata=metadata or {}
        )
        
        return await self.task_repo.create_subagent_task(subagent_task)
    
    async def get_subagent_task(self, subagent_task_id: str) -> SubagentTask:
        """Get a subagent task by ID."""
        subagent_task = await self.task_repo.get_subagent_task(subagent_task_id)
        if not subagent_task:
            raise TaskNotFound(subagent_task_id)
        return subagent_task
    
    async def get_subagent_tasks_by_task_id(self, task_id: str) -> list[SubagentTask]:
        """Get all subagent tasks for a given task ID."""
        return await self.task_repo.get_subagent_tasks_by_task_id(task_id)
    
    async def get_subagent_tasks_by_subagent_id(self, subagent_id: str) -> list[SubagentTask]:
        """Get all subagent tasks for a given subagent ID."""
        return await self.task_repo.get_subagent_tasks_by_subagent_id(subagent_id)
    
    async def update_subagent_task_status(
        self,
        subagent_task_id: str,
        status: str,
        result: str = None
    ) -> SubagentTask:
        """Update the status of a subagent task."""
        subagent_task = await self.get_subagent_task(subagent_task_id)
        
        subagent_task.status = status
        if status == "completed":
            subagent_task.completed_at = datetime.now(timezone.utc).isoformat()
        if result is not None:
            subagent_task.result = result
            
        return await self.task_repo.update_subagent_task(subagent_task)
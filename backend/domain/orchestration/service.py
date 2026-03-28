"""Orchestration service for coordinating main agents and subagents."""

import uuid
from datetime import datetime, timezone
import aiosqlite
from domain.subagent.service import SubagentService
from domain.task.service import TaskService
from core import Config


class OrchestrationService:
    """Service for orchestrating tasks between main agents and subagents."""
    
    def __init__(self, db: aiosqlite.Connection):
        self.db = db
        self.subagent_service = SubagentService(db)
        self.task_service = TaskService(db)
    
    async def delegate_task_to_subagent(
        self,
        task_id: str,
        specialization: str,
        metadata: dict = None
    ) -> dict:
        """Delegate a task to an appropriate subagent based on specialization."""
        # Find available subagents for this specialization
        subagents = await self.subagent_service.list_subagents(specialization)
        
        # Filter for active subagents
        active_subagents = [sa for sa in subagents if sa.status == "active"]
        
        if not active_subagents:
            raise Exception(f"No active subagents found for specialization '{specialization}'")
        
        # For simplicity, we'll assign to the first active subagent
        # In a real implementation, you might want more sophisticated selection logic
        subagent = active_subagents[0]
        
        # Assign the task to the subagent
        subagent_task = await self.subagent_service.assign_task_to_subagent(
            task_id=task_id,
            subagent_id=subagent.id,
            metadata=metadata or {}
        )
        
        # Update the task to indicate it's being handled by a subagent
        task = await self.task_service.get_task(task_id)
        task.metadata["assigned_to_subagent"] = subagent.id
        task.metadata["subagent_task_id"] = subagent_task.id
        task.metadata["subagent_specialization"] = specialization
        
        await self.task_service.update_task(
            task_id=task_id,
            metadata=task.metadata
        )
        
        return {
            "subagent_id": subagent.id,
            "subagent_task_id": subagent_task.id,
            "assigned_at": subagent_task.assigned_at
        }
    
    async def get_task_orchestration_info(self, task_id: str) -> dict:
        """Get information about task orchestration (subagent assignments, etc)."""
        task = await self.task_service.get_task(task_id)
        
        # Check if this task has been delegated to a subagent
        if "assigned_to_subagent" in task.metadata:
            subagent_id = task.metadata["assigned_to_subagent"]
            subagent_task_id = task.metadata.get("subagent_task_id")
            
            # Get subagent info
            subagent = await self.subagent_service.get_subagent(subagent_id)
            
            # Get subagent task info
            subagent_task = None
            if subagent_task_id:
                subagent_task = await self.subagent_service.get_subagent_task(subagent_task_id)
            
            return {
                "task_id": task_id,
                "is_delegated": True,
                "subagent_id": subagent_id,
                "subagent_name": subagent.name,
                "subagent_specialization": subagent.specialization,
                "subagent_task_id": subagent_task_id,
                "subagent_task_status": subagent_task.status if subagent_task else None,
                "assigned_at": task.metadata.get("assigned_at"),
                "result": task.metadata.get("subagent_result"),
            }
        
        return {
            "task_id": task_id,
            "is_delegated": False,
            "subagent_id": None,
            "subagent_name": None,
            "subagent_specialization": None,
            "subagent_task_id": None,
            "subagent_task_status": None,
            "assigned_at": None,
            "result": None,
        }
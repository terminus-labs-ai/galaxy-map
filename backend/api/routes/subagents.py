"""Subagent routes."""

from fastapi import APIRouter, HTTPException
from infrastructure import get_db
from domain.subagent.service import SubagentService
from api.schemas import SubagentCreate, SubagentUpdate, SubagentResponse, SubagentTaskResponse


router = APIRouter(prefix="/api/subagents", tags=["subagents"])


@router.post("", response_model=SubagentResponse, status_code=201)
async def create_subagent(subagent: SubagentCreate):
    """Create a new subagent."""
    db = await get_db()
    service = SubagentService(db)

    try:
        created = await service.create_subagent(
            name=subagent.name,
            specialization=subagent.specialization,
            description=subagent.description,
            status=subagent.status,
            metadata=subagent.metadata,
        )
        result = {
            "id": created.id,
            "name": created.name,
            "specialization": created.specialization,
            "description": created.description,
            "status": created.status,
            "metadata": created.metadata,
            "created_at": created.created_at,
            "updated_at": created.updated_at,
        }
        await db.close()
        return result
    except Exception as e:
        await db.close()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[SubagentResponse])
async def list_subagents(specialization: str = None):
    """List subagents, optionally filtered by specialization."""
    db = await get_db()
    service = SubagentService(db)

    try:
        subagents = await service.list_subagents(specialization)
        result = []
        for subagent in subagents:
            result.append({
                "id": subagent.id,
                "name": subagent.name,
                "specialization": subagent.specialization,
                "description": subagent.description,
                "status": subagent.status,
                "metadata": subagent.metadata,
                "created_at": subagent.created_at,
                "updated_at": subagent.updated_at,
            })
        await db.close()
        return result
    except Exception as e:
        await db.close()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{subagent_id}", response_model=SubagentResponse)
async def get_subagent(subagent_id: str):
    """Get a single subagent by ID."""
    db = await get_db()
    service = SubagentService(db)

    try:
        subagent = await service.get_subagent(subagent_id)
        result = {
            "id": subagent.id,
            "name": subagent.name,
            "specialization": subagent.specialization,
            "description": subagent.description,
            "status": subagent.status,
            "metadata": subagent.metadata,
            "created_at": subagent.created_at,
            "updated_at": subagent.updated_at,
        }
        await db.close()
        return result
    except Exception as e:
        await db.close()
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{subagent_id}", response_model=SubagentResponse)
async def update_subagent(subagent_id: str, updates: SubagentUpdate):
    """Update a subagent (partial update)."""
    db = await get_db()
    service = SubagentService(db)

    try:
        updated = await service.update_subagent(
            subagent_id=subagent_id,
            name=updates.name,
            specialization=updates.specialization,
            description=updates.description,
            status=updates.status,
            metadata=updates.metadata,
        )
        result = {
            "id": updated.id,
            "name": updated.name,
            "specialization": updated.specialization,
            "description": updated.description,
            "status": updated.status,
            "metadata": updated.metadata,
            "created_at": updated.created_at,
            "updated_at": updated.updated_at,
        }
        await db.close()
        return result
    except Exception as e:
        await db.close()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{subagent_id}", status_code=204)
async def delete_subagent(subagent_id: str):
    """Delete a subagent."""
    db = await get_db()
    service = SubagentService(db)

    try:
        await service.delete_subagent(subagent_id)
        await db.close()
    except Exception as e:
        await db.close()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{subagent_id}/tasks", response_model=SubagentTaskResponse, status_code=201)
async def assign_task_to_subagent(subagent_id: str, task_id: str, metadata: dict = None):
    """Assign a task to a subagent."""
    db = await get_db()
    service = SubagentService(db)

    try:
        subagent_task = await service.assign_task_to_subagent(
            task_id=task_id,
            subagent_id=subagent_id,
            metadata=metadata
        )
        result = {
            "id": subagent_task.id,
            "task_id": subagent_task.task_id,
            "subagent_id": subagent_task.subagent_id,
            "status": subagent_task.status,
            "assigned_at": subagent_task.assigned_at,
            "completed_at": subagent_task.completed_at,
            "result": subagent_task.result,
            "metadata": subagent_task.metadata,
        }
        await db.close()
        return result
    except Exception as e:
        await db.close()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{subagent_id}/tasks", response_model=list[SubagentTaskResponse])
async def get_subagent_tasks(subagent_id: str):
    """Get all tasks assigned to a subagent."""
    db = await get_db()
    service = SubagentService(db)

    try:
        subagent_tasks = await service.get_subagent_tasks_by_subagent_id(subagent_id)
        result = []
        for task in subagent_tasks:
            result.append({
                "id": task.id,
                "task_id": task.task_id,
                "subagent_id": task.subagent_id,
                "status": task.status,
                "assigned_at": task.assigned_at,
                "completed_at": task.completed_at,
                "result": task.result,
                "metadata": task.metadata,
            })
        await db.close()
        return result
    except Exception as e:
        await db.close()
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{subagent_task_id}/status", response_model=SubagentTaskResponse)
async def update_subagent_task_status(subagent_task_id: str, status: str, result: str = None):
    """Update the status of a subagent task."""
    db = await get_db()
    service = SubagentService(db)

    try:
        updated_task = await service.update_subagent_task_status(
            subagent_task_id=subagent_task_id,
            status=status,
            result=result
        )
        result = {
            "id": updated_task.id,
            "task_id": updated_task.task_id,
            "subagent_id": updated_task.subagent_id,
            "status": updated_task.status,
            "assigned_at": updated_task.assigned_at,
            "completed_at": updated_task.completed_at,
            "result": updated_task.result,
            "metadata": updated_task.metadata,
        }
        await db.close()
        return result
    except Exception as e:
        await db.close()
        raise HTTPException(status_code=400, detail=str(e))
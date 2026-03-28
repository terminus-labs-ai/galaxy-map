"""Orchestration routes."""

from fastapi import APIRouter, HTTPException
from infrastructure import get_db
from domain.orchestration.service import OrchestrationService


router = APIRouter(prefix="/api/orchestration", tags=["orchestration"])


@router.post("/tasks/{task_id}/delegate", status_code=200)
async def delegate_task_to_subagent(task_id: str, specialization: str, metadata: dict = None):
    """Delegate a task to an appropriate subagent based on specialization."""
    db = await get_db()
    service = OrchestrationService(db)

    try:
        result = await service.delegate_task_to_subagent(
            task_id=task_id,
            specialization=specialization,
            metadata=metadata
        )
        await db.close()
        return result
    except Exception as e:
        await db.close()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks/{task_id}/info")
async def get_task_orchestration_info(task_id: str):
    """Get information about task orchestration (subagent assignments, etc)."""
    db = await get_db()
    service = OrchestrationService(db)

    try:
        result = await service.get_task_orchestration_info(task_id)
        await db.close()
        return result
    except Exception as e:
        await db.close()
        raise HTTPException(status_code=400, detail=str(e))
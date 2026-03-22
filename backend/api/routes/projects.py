"""Project routes."""

from fastapi import APIRouter
from infrastructure import get_db
from domain import TaskService
from api.schemas import ProjectPlanCreate, ProjectPlanResponse


router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("/plan", response_model=ProjectPlanResponse, status_code=201)
async def create_project_plan(plan: ProjectPlanCreate):
    """Create an entire project plan as a tree of tasks.

    Nesting defines dependencies — subtasks are blocked by their parent.
    Siblings run in parallel. All tasks get status=queued and the
    specified project_id.
    """
    db = await get_db()
    service = TaskService(db)

    result = await service.create_project_plan(
        project_id=plan.project_id,
        tasks=[t.model_dump() for t in plan.tasks],
    )

    await db.close()
    return result

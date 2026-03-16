"""Task routes."""

from fastapi import APIRouter, Query
from infrastructure import get_db
from domain import Task, TaskService
from api.schemas import TaskCreate, TaskUpdate, TaskResponse
from core import Config


router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
  status: str | None = Query(None),
  specialization: str | None = Query(None),
):
  """List tasks, optionally filtered by status and/or specialization."""
  db = await get_db()
  service = TaskService(db)

  tasks = await service.list_tasks(status, specialization)

  # Compute is_blocked for all tasks
  all_tasks = await service.repo.get_all()
  result = [t.to_dict(is_blocked=t.is_blocked(all_tasks)) for t in tasks]

  await db.close()
  return result


@router.get("/search", response_model=list[TaskResponse])
async def search_tasks(q: str = Query(..., min_length=1)):
  """Search tasks by ID, title, description, or metadata."""
  db = await get_db()
  service = TaskService(db)

  tasks = await service.search_tasks(q)

  # Compute is_blocked for all tasks
  all_tasks = await service.repo.get_all()
  result = [t.to_dict(is_blocked=t.is_blocked(all_tasks)) for t in tasks]

  await db.close()
  return result


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(task: TaskCreate):
  """Create a new task."""
  db = await get_db()
  service = TaskService(db)

  try:
    created = await service.create_task(
      title=task.title,
      description=task.description,
      status=task.status,
      specialization=task.specialization,
      priority=task.priority,
      blocked_by=task.blocked_by,
      metadata=task.metadata,
      task_id=task.id,
    )
    print(f"Task created! {created}")
  except Exception as e:
    print(f"Error creating task: {e}")

  result = created.to_dict(is_blocked=False)
  await db.close()
  return result


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
  """Get a single task by ID."""
  db = await get_db()
  service = TaskService(db)

  task = await service.get_task(task_id)
  all_tasks = await service.repo.get_all()

  result = task.to_dict(is_blocked=task.is_blocked(all_tasks))
  await db.close()
  return result


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, updates: TaskUpdate):
  """Update a task (partial update)."""
  db = await get_db()
  service = TaskService(db)

  updated = await service.update_task(
    task_id=task_id,
    title=updates.title,
    description=updates.description,
    status=updates.status,
    specialization=updates.specialization,
    priority=updates.priority,
    blocked_by=updates.blocked_by,
    metadata=updates.metadata,
  )

  all_tasks = await service.repo.get_all()
  result = updated.to_dict(is_blocked=updated.is_blocked(all_tasks))
  await db.close()
  return result


@router.post("/{task_id}/claim", response_model=TaskResponse)
async def claim_task(task_id: str, claimed_by: str = Query(...)):
  """Atomically claim a queued, unblocked task."""
  db = await get_db()
  service = TaskService(db)

  claimed = await service.claim_task(task_id, claimed_by)
  all_tasks = await service.repo.get_all()

  result = claimed.to_dict(is_blocked=claimed.is_blocked(all_tasks))
  await db.close()
  return result


@router.patch("/{task_id}/metadata", response_model=TaskResponse)
async def merge_task_metadata(task_id: str, patch: dict):
  """Merge keys into task metadata."""
  db = await get_db()
  service = TaskService(db)

  updated = await service.merge_metadata(task_id, patch)
  all_tasks = await service.repo.get_all()

  result = updated.to_dict(is_blocked=updated.is_blocked(all_tasks))
  await db.close()
  return result


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: str):
  """Delete a task."""
  db = await get_db()
  service = TaskService(db)

  await service.delete_task(task_id)
  await db.close()

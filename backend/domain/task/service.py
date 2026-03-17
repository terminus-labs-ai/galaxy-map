"""Task service (business logic layer)."""

import uuid
from datetime import datetime, timezone
import aiosqlite
from core import Config, TaskNotFound, DuplicateTask, TaskNotQueued, TaskBlocked
from .model import Task
from .repository import TaskRepository
from .validator import TaskValidator


class TaskService:
    """Encapsulates task business logic."""

    def __init__(self, db: aiosqlite.Connection):
        self.db = db
        self.repo = TaskRepository(db)
        self.validator = TaskValidator()

    async def create_task(
        self,
        title: str,
        description: str = "",
        status: str = "backlog",
        specialization: str = "general",
        priority: int = 0,
        blocked_by: list[str] | None = None,
        metadata: dict | None = None,
        task_id: str | None = None,
        project_id: str | None = None,
    ) -> Task:
        """Create a new task with validation and duplicate detection."""
        self.validator.validate_status(status)
        self.validator.validate_specialization(specialization)

        blocked_by = blocked_by or []
        metadata = metadata or {}

        task_id = task_id or uuid.uuid4().hex[:12]
        self.validator.validate_blocked_by(blocked_by, task_id)

        # Check if task ID already exists
        if await self.repo.get_by_id(task_id):
            raise DuplicateTask(task_id, 1.0)

        # Check for duplicate titles
        await self._check_duplicate_title(title)

        task = Task(
            id=task_id,
            title=title,
            description=description,
            status=status,
            specialization=specialization,
            priority=priority,
            blocked_by=blocked_by,
            metadata=metadata,
            project_id=project_id,
        )

        return await self.repo.create(task)

    async def get_task(self, task_id: str) -> Task:
        """Fetch a task by ID."""
        task = await self.repo.get_by_id(task_id)
        if not task:
            raise TaskNotFound(task_id)
        return task

    async def list_tasks(self, status: str | None = None, specialization: str | None = None) -> list[Task]:
        """List tasks, with optional filtering."""
        # Default to queued + in_progress if not specified
        if status is None:
            status = Config.get("api_defaults.list_tasks_default_status")

        statuses = [s.strip() for s in status.split(",")]
        for s in statuses:
            self.validator.validate_status(s)

        if specialization:
            self.validator.validate_specialization(specialization)
            return await self.repo.list_by_status_and_specialization(statuses, specialization)

        return await self.repo.list_by_status(statuses)

    async def search_tasks(self, query: str) -> list[Task]:
        """Search tasks by various criteria."""
        if not query or len(query) < 1:
            return []
        return await self.repo.search(query)

    async def update_task(
        self,
        task_id: str,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
        specialization: str | None = None,
        priority: int | None = None,
        blocked_by: list[str] | None = None,
        metadata: dict | None = None,
        project_id: str | None = "___UNSET___",
    ) -> Task:
        """Update a task (partial update)."""
        task = await self.get_task(task_id)

        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if status is not None:
            self.validator.validate_status(status)
            task.status = status
        if specialization is not None:
            self.validator.validate_specialization(specialization)
            task.specialization = specialization
        if priority is not None:
            task.priority = priority
        if blocked_by is not None:
            self.validator.validate_blocked_by(blocked_by, task_id)
            task.blocked_by = blocked_by
        if metadata is not None:
            task.metadata = metadata
        if project_id != "___UNSET___":
            task.project_id = project_id

        return await self.repo.update(task)

    async def claim_task(self, task_id: str, claimed_by: str) -> Task:
        """Atomically claim a queued, unblocked task."""
        task = await self.get_task(task_id)

        if task.status != "queued":
            raise TaskNotQueued(task.status)

        # Check if blocked
        all_tasks = await self.repo.get_all()
        if task.is_blocked(all_tasks):
            raise TaskBlocked()

        task.status = "in_progress"
        task.metadata["claimed_by"] = claimed_by

        return await self.repo.update(task)

    async def merge_metadata(self, task_id: str, patch: dict) -> Task:
        """Merge keys into task metadata."""
        task = await self.get_task(task_id)

        for key, value in patch.items():
            if value is None:
                task.metadata.pop(key, None)
            else:
                task.metadata[key] = value

        return await self.repo.update(task)

    async def delete_task(self, task_id: str):
        """Delete a task."""
        task = await self.get_task(task_id)  # Ensure it exists
        await self.repo.delete(task_id)

    async def list_projects(self) -> list[dict]:
        """Get distinct project_ids with task counts."""
        return await self.repo.get_distinct_projects()

    async def _check_duplicate_title(self, title: str):
        """Check for duplicate task titles based on similarity threshold."""
        config_dup = Config.get("tasks.duplicate_detection", {})
        if not config_dup.get("enabled", True):
            return

        threshold = config_dup.get("similarity_threshold", 0.85)
        existing = [t for t in await self.repo.get_all() if t.status not in Config.completed_statuses()]

        for task in existing:
            similarity = self._title_similarity(title, task.title)
            if similarity >= threshold:
                raise DuplicateTask(task.title, similarity)

    @staticmethod
    def _title_similarity(title1: str, title2: str) -> float:
        """Simple similarity check for task titles."""
        config_dup = Config.get("tasks.duplicate_detection", {})
        prefixes = config_dup.get("ignore_prefixes", [])
        ignore_words = set(config_dup.get("ignore_words", []))

        t1 = title1.lower().strip()
        t2 = title2.lower().strip()

        if t1 == t2:
            return 1.0

        # Strip common prefixes
        for prefix in prefixes:
            if t1.startswith(prefix + " "):
                t1 = t1[len(prefix) + 1:].strip()
            if t2.startswith(prefix + " "):
                t2 = t2[len(prefix) + 1:].strip()

        if t1 == t2:
            return 1.0

        # Compute Jaccard similarity on significant words
        words1 = set(t1.split()) - ignore_words
        words2 = set(t2.split()) - ignore_words

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)
        return intersection / union if union > 0 else 0.0

"""Task service (business logic layer)."""

import uuid
import json
from datetime import datetime, timezone
import aiosqlite
from fastapi import HTTPException
from core import Config, TaskNotFound, DuplicateTask, TaskBlocked, InvalidTransition
from .model import Task
from .repository import TaskRepository
from .validator import TaskValidator
from .history_model import TaskHistory
from .history_repository import TaskHistoryRepository


class TaskService:
    """Encapsulates task business logic."""

    def __init__(self, db: aiosqlite.Connection):
        self.db = db
        self.repo = TaskRepository(db)
        self.history_repo = TaskHistoryRepository(db)
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
        changed_by: str = "system",
    ) -> Task:
        """Update a task (partial update)."""
        task = await self.get_task(task_id)
        
        # Track changes for history
        changes = {}
        
        if title is not None and title != task.title:
            changes["title"] = {"old": task.title, "new": title}
            task.title = title
        if description is not None and description != task.description:
            changes["description"] = {"old": task.description, "new": description}
            task.description = description
        if status is not None:
            self.validator.validate_status(status)
            if status != task.status:
                self._validate_transition(task.status, status)
                changes["status"] = {"old": task.status, "new": status}
            task.status = status
        if specialization is not None and specialization != task.specialization:
            self.validator.validate_specialization(specialization)
            changes["specialization"] = {"old": task.specialization, "new": specialization}
            task.specialization = specialization
        if priority is not None and priority != task.priority:
            changes["priority"] = {"old": task.priority, "new": priority}
            task.priority = priority
        if blocked_by is not None:
            self.validator.validate_blocked_by(blocked_by, task_id)
            if blocked_by != task.blocked_by:
                changes["blocked_by"] = {"old": task.blocked_by, "new": blocked_by}
            task.blocked_by = blocked_by
        if metadata is not None:
            changes["metadata"] = {"old": task.metadata, "new": metadata}
            task.metadata = metadata
        if project_id != "___UNSET___" and project_id != task.project_id:
            changes["project_id"] = {"old": task.project_id, "new": project_id}
            task.project_id = project_id

        result = await self.repo.update(task)
        
        # Create history entries for changes
        if changes:
            for field_name, change in changes.items():
                if field_name == "status":
                    event_type = "status_change"
                elif field_name == "specialization":
                    event_type = "assignment"
                else:
                    event_type = "metadata_update"
                await self._create_history_entry(
                    task_id=task_id,
                    event_type=event_type,
                    old_value=change["old"],
                    new_value=change["new"],
                    changed_by=changed_by,
                    details={"field": field_name},
                )
        
        return result

    async def claim_task(
        self, task_id: str, claimed_by: str, target_status: str = "in_progress",
    ) -> Task:
        """Atomically claim an unblocked task, transitioning to target_status."""
        task = await self.get_task(task_id)

        # Validate the transition from current status to target_status
        self._validate_transition(task.status, target_status)

        # Check if blocked
        all_tasks = await self.repo.get_all()
        if task.is_blocked(all_tasks):
            raise TaskBlocked()

        old_status = task.status
        task.status = target_status

        task.metadata["claimed_by"] = claimed_by

        result = await self.repo.update(task)

        # Create history entries
        await self._create_history_entry(
            task_id=task_id,
            event_type="status_change",
            old_value=old_status,
            new_value=target_status,
            changed_by=claimed_by,
            details={},
        )
        await self._create_history_entry(
            task_id=task_id,
            event_type="assignment",
            old_value=None,
            new_value=claimed_by,
            changed_by=claimed_by,
            details={"field": "claimed_by"},
        )

        return result

    async def merge_metadata(self, task_id: str, patch: dict, changed_by: str = "system") -> Task:
        """Merge keys into task metadata."""
        task = await self.get_task(task_id)
        old_metadata = task.metadata.copy()

        for key, value in patch.items():
            if value is None:
                task.metadata.pop(key, None)
            else:
                task.metadata[key] = value

        result = await self.repo.update(task)
        
        # Create history entry for metadata merge
        await self._create_history_entry(
            task_id=task_id,
            event_type="metadata_update",
            old_value=old_metadata,
            new_value=task.metadata,
            changed_by=changed_by,
            details={"patch": patch},
        )
        
        return result

    async def _create_history_entry(
        self,
        task_id: str,
        event_type: str,
        old_value: any = None,
        new_value: any = None,
        changed_by: str = "system",
        details: dict | None = None,
    ) -> TaskHistory:
        """Create a history entry for a task event."""
        history = TaskHistory(
            id=uuid.uuid4().hex[:12],
            task_id=task_id,
            event_type=event_type,
            old_value=json.dumps(old_value) if old_value is not None else None,
            new_value=json.dumps(new_value) if new_value is not None else None,
            changed_by=changed_by,
            details=details or {},
        )
        return await self.history_repo.create(history)

    async def delete_task(self, task_id: str):
        """Delete a task."""
        task = await self.get_task(task_id)  # Ensure it exists
        await self.repo.delete(task_id)

    async def list_projects(self) -> list[dict]:
        """Get distinct project_ids with task counts."""
        return await self.repo.get_distinct_projects()

    async def get_task_history(
        self, task_id: str, limit: int = 100, offset: int = 0
    ) -> list[dict]:
        """Get task history entries."""
        history = await self.history_repo.get_by_task_id(task_id, limit, offset)
        return [h.to_dict() for h in history]

    @staticmethod
    def _validate_transition(current_status: str, new_status: str) -> None:
        """Raise InvalidTransition if the transition is not allowed by statuses config."""
        statuses = Config.statuses()
        status_map = {s["key"]: s for s in statuses}

        status_def = status_map.get(current_status)
        if status_def is None:
            # Unknown current status — allow (don't block on misconfigured data)
            return

        allowed = status_def.get("allowed_transitions", [])
        if new_status not in allowed:
            raise InvalidTransition(current_status, new_status)

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

    async def create_project_plan(
        self,
        project_id: str,
        tasks: list[dict],
        shared_metadata: dict | None = None,
        task_id: str | None = None,
    ) -> dict:
        """Create an entire project plan from a nested task tree.

        Walks the tree depth-first, creating tasks with:
        - status: queued (always)
        - project_id: inherited from top-level param
        - blocked_by: [parent_id] (nesting defines dependency)
        - priority: 10 - depth (floor at 1)

        Atomic: rolls back all created tasks on any failure.
        """
        from core import InvalidProjectPlan, Config

        # --- Validation pass (before any DB writes) ---
        errors = []

        if not project_id or not project_id.strip():
            errors.append("project_id is required and cannot be empty")

        if not tasks:
            errors.append("tasks array is required and cannot be empty")

        valid_specializations = Config.specializations()

        def _count_and_validate(nodes, depth=0, path="tasks"):
            count = 0
            if depth > 10:
                errors.append(f"Tree depth exceeds maximum of 10 levels at {path}")
                return count
            for i, node in enumerate(nodes):
                node_path = f"{path}[{i}]"
                count += 1
                if not node.get("title") or not node["title"].strip():
                    errors.append(f"{node_path}.title is required and cannot be empty")
                if not node.get("description") or not node["description"].strip():
                    errors.append(f"{node_path}.description is required and cannot be empty")
                elif len(node["description"].strip()) < 20:
                    errors.append(f"{node_path}.description must be at least 20 characters")
                spec = node.get("specialization", "")
                if spec not in valid_specializations:
                    errors.append(
                        f"{node_path}.specialization '{spec}' is invalid. "
                        f"Must be one of: {valid_specializations}"
                    )
                if node.get("subtasks"):
                    count += _count_and_validate(node["subtasks"], depth + 1, f"{node_path}.subtasks")
            return count

        total = _count_and_validate(tasks) if tasks else 0
        if total > 50:
            errors.append(f"Plan contains {total} tasks, maximum is 50")

        if errors:
            raise InvalidProjectPlan(errors)

        # --- Idempotency: reject if project already has plan subtasks ---
        # Allow 1 existing task (the seed/parent task that EDI is planning for).
        # If there are 2+, a plan was already created.
        existing = await self.repo.list_by_project(project_id)
        if len(existing) > 1:
            raise InvalidProjectPlan(
                [f"Project '{project_id}' already has {len(existing)} tasks (plan already created). "
                 f"create_project_plan can only be called once per project_id. "
                 f"The plan was already created successfully — do not call this tool again."]
            )

        # --- Set project_id on parent task if task_id provided ---
        if task_id:
            try:
                parent_task = await self.repo.get_by_id(task_id)
                parent_task.project_id = project_id
                await self.repo.update(parent_task)
                await self.db.commit()
            except TaskNotFound:
                raise InvalidProjectPlan(
                    [f"task_id '{task_id}' not found. Pass the task ID from your assignment."]
                )

        # --- Creation pass (atomic) ---
        created_ids = []
        created_map = {}  # id -> task dict (for response assembly)

        async def _create_recursive(nodes, parent_id=None, depth=0):
            for node in nodes:
                task_id = uuid.uuid4().hex[:12]
                priority = max(1, 10 - depth)
                blocked_by = [parent_id] if parent_id else []
                now = datetime.now(timezone.utc).isoformat()

                await self.db.execute(
                    """INSERT INTO tasks (id, title, description, status, specialization,
                       priority, blocked_by, metadata, created_at, updated_at, project_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        task_id,
                        node["title"],
                        node["description"],
                        "queued",
                        node["specialization"],
                        priority,
                        json.dumps(blocked_by),
                        json.dumps(shared_metadata or {}),
                        now,
                        now,
                        project_id,
                    ),
                )
                created_ids.append(task_id)
                created_map[task_id] = {
                    "id": task_id,
                    "title": node["title"],
                    "specialization": node["specialization"],
                    "status": "queued",
                    "blocked_by": blocked_by,
                    "priority": priority,
                    "_subtask_defs": node.get("subtasks", []),
                    "_children": [],
                }

                if parent_id and parent_id in created_map:
                    created_map[parent_id]["_children"].append(task_id)

                if node.get("subtasks"):
                    await _create_recursive(node["subtasks"], parent_id=task_id, depth=depth + 1)

        try:
            await _create_recursive(tasks)
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create project plan: {e}")

        # --- Assemble response tree ---
        def _build_tree(node_ids):
            result = []
            for nid in node_ids:
                info = created_map[nid]
                result.append({
                    "id": info["id"],
                    "title": info["title"],
                    "specialization": info["specialization"],
                    "status": info["status"],
                    "blocked_by": info["blocked_by"],
                    "priority": info["priority"],
                    "subtasks": _build_tree(info["_children"]),
                })
            return result

        root_ids = [cid for cid in created_ids if not created_map[cid]["blocked_by"]]
        task_tree = _build_tree(root_ids)

        return {
            "project_id": project_id,
            "tasks_created": len(created_ids),
            "task_tree": task_tree,
        }

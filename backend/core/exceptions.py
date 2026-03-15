"""Application domain exceptions."""

from fastapi import HTTPException


class TaskNotFound(HTTPException):
    def __init__(self, task_id: str):
        super().__init__(status_code=404, detail=f"Task '{task_id}' not found")


class DuplicateTask(HTTPException):
    def __init__(self, existing_title: str, similarity: float):
        msg = (
            f"Potential duplicate task found: '{existing_title}' "
            f"(similarity: {similarity:.0%}). Use update_task to modify the existing task instead."
        )
        super().__init__(status_code=409, detail=msg)


class InvalidStatus(HTTPException):
    def __init__(self, status: str, valid: list[str]):
        super().__init__(
            status_code=400,
            detail=f"Invalid status '{status}'. Must be one of: {valid}",
        )


class InvalidSpecialization(HTTPException):
    def __init__(self, spec: str, valid: list[str]):
        super().__init__(
            status_code=400,
            detail=f"Invalid specialization '{spec}'. Must be one of: {valid}",
        )


class InvalidBlocker(HTTPException):
    def __init__(self, reason: str = ""):
        detail = f"Invalid blocked_by list: {reason}" if reason else "Invalid blocked_by list"
        super().__init__(status_code=400, detail=detail)


class TaskNotQueued(HTTPException):
    def __init__(self, current_status: str):
        super().__init__(
            status_code=409,
            detail=f"Task is '{current_status}', not 'queued'",
        )


class TaskBlocked(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=409,
            detail="Task is blocked by unfinished dependencies",
        )


class MessageNotFound(HTTPException):
    def __init__(self, message_id: str):
        super().__init__(status_code=404, detail=f"Message '{message_id}' not found")

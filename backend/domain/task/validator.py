"""Task validation logic."""

from core import (
    InvalidStatus,
    InvalidSpecialization,
    InvalidBlocker,
    Config,
)


class TaskValidator:
    """Validate task inputs and state transitions."""

    @staticmethod
    def validate_status(status: str):
        """Ensure status is valid."""
        valid_statuses = {s["key"] for s in Config.statuses()}
        if status not in valid_statuses:
            raise InvalidStatus(status, list(valid_statuses))

    @staticmethod
    def validate_specialization(spec: str):
        """Ensure specialization is valid."""
        valid = Config.specializations()
        if spec not in valid:
            raise InvalidSpecialization(spec, valid)

    @staticmethod
    def validate_blocked_by(blocked_by: list[str], task_id: str = ""):
        """Ensure blocked_by list is valid."""
        if not blocked_by:
            return
        if task_id in blocked_by:
            raise InvalidBlocker("A task cannot block itself")

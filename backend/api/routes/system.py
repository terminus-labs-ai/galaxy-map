"""System routes (statuses, specializations, health)."""

from fastapi import APIRouter
from core import Config, InvalidStatus
from api.schemas import StatusResponse


router = APIRouter(tags=["system"])


@router.get("/api/statuses", response_model=list[StatusResponse])
async def list_statuses():
    """Return all valid statuses with metadata."""
    statuses = Config.statuses()
    return [
        StatusResponse(
            key=s["key"],
            label=s["label"],
            description=s["description"],
            order=s["order"],
            color=s["color"],
            allowed_transitions=s["allowed_transitions"],
            terminal=s["terminal"],
        )
        for s in statuses
    ]


@router.get("/api/statuses/{status_key}", response_model=StatusResponse)
async def get_status_details(status_key: str):
    """Get details for a single status."""
    statuses = {s["key"]: s for s in Config.statuses()}
    if status_key not in statuses:
        raise InvalidStatus(status_key, list(statuses.keys()))

    s = statuses[status_key]
    return StatusResponse(
        key=s["key"],
        label=s["label"],
        description=s["description"],
        order=s["order"],
        color=s["color"],
        allowed_transitions=s["allowed_transitions"],
        terminal=s["terminal"],
    )


@router.get("/api/specializations")
async def list_specializations():
    """Return the list of valid specializations."""
    return Config.specializations()

"""
Galaxy Map MCP Server — exposes the Galaxy Map REST API as MCP tools.

Usage:
    python server.py

Configure via environment variable:
    GALAXY_MAP_URL  — base URL of the Galaxy Map API (default: http://localhost:8000)
"""

import os
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP

BASE_URL = os.environ.get("GALAXY_MAP_URL", "http://localhost:8000")
TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")

mcp = FastMCP("Galaxy Map", instructions="Task tracker for AI agents. Use these tools to manage tasks on the Galaxy Map kanban board.")


def _api(path: str) -> str:
    return f"{BASE_URL}/api{path}"


@mcp.tool()
async def list_tasks(status: Optional[str] = None, specialization: Optional[str] = None) -> list[dict]:
    """List tasks on the board.

    Args:
        status: Filter by status (backlog, queued, in_progress, needs_review, done).
        specialization: Filter by specialization (general, coding, planning, research).
    """
    params = {}
    if status:
        params["status"] = status
    if specialization:
        params["specialization"] = specialization
    async with httpx.AsyncClient() as client:
        resp = await client.get(_api("/tasks"), params=params)
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def create_task(
    title: str,
    description: str = "",
    status: str = "backlog",
    specialization: str = "general",
    priority: int = 0,
    blocked_by: Optional[list[str]] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """Create a new task.

    Args:
        title: Task title (required).
        description: Task description.
        status: Initial status (backlog, queued, in_progress, needs_review, done).
        specialization: Task specialization (general, coding, planning, research).
        priority: Priority (higher = more important). Default 0.
        blocked_by: List of task IDs this task depends on.
        metadata: Arbitrary JSON metadata for agent context.
    """
    body = {
        "title": title,
        "description": description,
        "status": status,
        "specialization": specialization,
        "priority": priority,
        "blocked_by": blocked_by or [],
        "metadata": metadata or {},
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(_api("/tasks"), json=body)
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def get_task(task_id: str) -> dict:
    """Get a single task by ID.

    Args:
        task_id: The task ID.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(_api(f"/tasks/{task_id}"))
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def update_task(
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    specialization: Optional[str] = None,
    priority: Optional[int] = None,
    blocked_by: Optional[list[str]] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """Update a task (partial update — only provided fields are changed).

    Args:
        task_id: The task ID to update.
        title: New title.
        description: New description.
        status: New status (backlog, queued, in_progress, needs_review, done).
        specialization: New specialization (general, coding, planning, research).
        priority: New priority.
        blocked_by: New list of blocker task IDs (replaces existing list).
        metadata: New metadata dict (replaces existing metadata).
    """
    body = {}
    if title is not None:
        body["title"] = title
    if description is not None:
        body["description"] = description
    if status is not None:
        body["status"] = status
    if specialization is not None:
        body["specialization"] = specialization
    if priority is not None:
        body["priority"] = priority
    if blocked_by is not None:
        body["blocked_by"] = blocked_by
    if metadata is not None:
        body["metadata"] = metadata
    async with httpx.AsyncClient() as client:
        resp = await client.patch(_api(f"/tasks/{task_id}"), json=body)
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def delete_task(task_id: str) -> str:
    """Delete a task. Also removes it from other tasks' blocked_by lists.

    Args:
        task_id: The task ID to delete.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.delete(_api(f"/tasks/{task_id}"))
        resp.raise_for_status()
        return f"Task {task_id} deleted."


@mcp.tool()
async def list_statuses() -> list[str]:
    """List valid task statuses (board columns), in order."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(_api("/statuses"))
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def list_specializations() -> list[str]:
    """List valid task specializations."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(_api("/specializations"))
        resp.raise_for_status()
        return resp.json()


def main():
    mcp.run(transport=TRANSPORT)


if __name__ == "__main__":
    main()

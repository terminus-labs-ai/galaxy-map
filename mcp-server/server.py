"""
Galaxy Map MCP Server — exposes the Galaxy Map REST API as MCP tools.

Usage:
    python server.py

Configure via environment variable:
    GALAXY_MAP_URL  — base URL of the Galaxy Map API (default: http://localhost:8000)
"""

import logging
import os
import sys
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("galaxy-map-mcp")

BASE_URL = os.environ.get("GALAXY_MAP_URL", "http://localhost:8000")
TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_HOST = os.environ.get("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.environ.get("MCP_PORT", "8080"))

logger.info("Starting Galaxy Map MCP server")
logger.info("GALAXY_MAP_URL=%s", BASE_URL)
logger.info("MCP_TRANSPORT=%s", TRANSPORT)

mcp = FastMCP("Galaxy Map", instructions="Task tracker for AI agents. Use these tools to manage tasks on the Galaxy Map kanban board.", host=MCP_HOST, port=MCP_PORT)


def _api(path: str) -> str:
    return f"{BASE_URL}/api{path}"


@mcp.tool()
async def list_tasks(status: Optional[str] = None, specialization: Optional[str] = None) -> list[dict]:
    """List tasks on the board.

    Args:
        status: Filter by status (backlog, queued, in_progress, needs_review, done, error).
        specialization: Filter by specialization (general, coding, planning, research).
    """
    params = {}
    if status:
        params["status"] = status
    if specialization:
        params["specialization"] = specialization
    url = _api("/tasks")
    logger.debug("list_tasks -> GET %s params=%s", url, params)
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params)
            logger.debug("list_tasks <- %s (%d bytes)", resp.status_code, len(resp.content))
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.error("list_tasks failed: %s", e)
            raise


@mcp.tool()
async def create_task(
    title: str,
    description: str = "",
    status: str = "backlog",
    specialization: str = "general",
    priority: int = 0,
    blocked_by: Optional[list[str]] = None,
    metadata: Optional[dict] = None,
    id: Optional[str] = None,
) -> dict:
    """Create a new task.

    Args:
        title: Task title (required).
        description: Task description.
        status: Initial status (backlog, queued, in_progress, needs_review, done, error).
        specialization: Task specialization (general, coding, planning, research).
        priority: Priority (higher = more important). Default 0.
        blocked_by: List of task IDs this task depends on.
        metadata: Arbitrary JSON metadata for agent context.
        id: Optional client-provided task ID. If omitted, the server generates one. Rejects duplicates (409).
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
    if id is not None:
        body["id"] = id
    url = _api("/tasks")
    logger.debug("create_task -> POST %s body=%s", url, body)
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=body)
            logger.debug("create_task <- %s (%d bytes)", resp.status_code, len(resp.content))
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.error("create_task failed: %s", e)
            raise


@mcp.tool()
async def get_task(task_id: str) -> dict:
    """Get a single task by ID.

    Args:
        task_id: The task ID.
    """
    url = _api(f"/tasks/{task_id}")
    logger.debug("get_task -> GET %s", url)
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            logger.debug("get_task <- %s (%d bytes)", resp.status_code, len(resp.content))
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.error("get_task failed: %s", e)
            raise


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
        status: New status (backlog, queued, in_progress, needs_review, done, error).
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
    url = _api(f"/tasks/{task_id}")
    logger.debug("update_task -> PATCH %s body=%s", url, body)
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.patch(url, json=body)
            logger.debug("update_task <- %s (%d bytes)", resp.status_code, len(resp.content))
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.error("update_task failed: %s", e)
            raise


@mcp.tool()
async def claim_task(task_id: str, claimed_by: str) -> dict:
    """Atomically claim a queued, unblocked task. Sets status to in_progress.

    Returns 409 if the task is not queued, is blocked, or already claimed.

    Args:
        task_id: The task ID to claim.
        claimed_by: Identifier of the agent claiming the task.
    """
    url = _api(f"/tasks/{task_id}/claim")
    logger.debug("claim_task -> POST %s claimed_by=%s", url, claimed_by)
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, params={"claimed_by": claimed_by})
            logger.debug("claim_task <- %s (%d bytes)", resp.status_code, len(resp.content))
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                return {"error": e.response.json().get("detail", "Task not claimable")}
            raise
        except httpx.HTTPError as e:
            logger.error("claim_task failed: %s", e)
            raise


@mcp.tool()
async def merge_metadata(task_id: str, metadata: dict) -> dict:
    """Merge keys into a task's metadata (instead of replacing it).

    Existing keys not in the patch are preserved. Keys set to null are removed.

    Args:
        task_id: The task ID.
        metadata: Dict of keys to merge into existing metadata.
    """
    url = _api(f"/tasks/{task_id}/metadata")
    logger.debug("merge_metadata -> PATCH %s body=%s", url, metadata)
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.patch(url, json=metadata)
            logger.debug("merge_metadata <- %s (%d bytes)", resp.status_code, len(resp.content))
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.error("merge_metadata failed: %s", e)
            raise


@mcp.tool()
async def delete_task(task_id: str) -> str:
    """Delete a task. Also removes it from other tasks' blocked_by lists.

    Args:
        task_id: The task ID to delete.
    """
    url = _api(f"/tasks/{task_id}")
    logger.debug("delete_task -> DELETE %s", url)
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.delete(url)
            logger.debug("delete_task <- %s", resp.status_code)
            resp.raise_for_status()
            return f"Task {task_id} deleted."
        except httpx.HTTPError as e:
            logger.error("delete_task failed: %s", e)
            raise


@mcp.tool()
async def list_statuses() -> list[str]:
    """List valid task statuses (board columns), in order."""
    url = _api("/statuses")
    logger.debug("list_statuses -> GET %s", url)
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            logger.debug("list_statuses <- %s", resp.status_code)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.error("list_statuses failed: %s", e)
            raise


@mcp.tool()
async def list_specializations() -> list[str]:
    """List valid task specializations."""
    url = _api("/specializations")
    logger.debug("list_specializations -> GET %s", url)
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            logger.debug("list_specializations <- %s", resp.status_code)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.error("list_specializations failed: %s", e)
            raise


def main():
    logger.info("Running with transport=%s", TRANSPORT)
    mcp.run(transport=TRANSPORT)


if __name__ == "__main__":
    main()

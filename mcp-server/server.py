"""
Galaxy Map MCP Server — exposes the Galaxy Map REST API as MCP tools.

Usage:
    python server.py

Configure via environment variable:
    GALAXY_MAP_URL  — base URL of the Galaxy Map API (default: http://localhost:8000)
"""

import json
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
async def list_tasks(status: Optional[str] = None, specialization: Optional[str] = None, project_id: Optional[str] = None) -> list[dict]:
    """List tasks on the board.

    Args:
        status: Filter by status. Use list_statuses() to see valid values.
        specialization: Filter by specialization (general, coding, planning, research).
        project_id: Filter by project slug (e.g. "galaxy-map-v2").
    """
    params = {}
    if status:
        params["status"] = status
    if specialization:
        params["specialization"] = specialization
    if project_id:
        params["project_id"] = project_id
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
async def search_tasks(q: str) -> list[dict]:
    """Search tasks by full-text query across ID, title, description, and metadata.

    Searches are case-insensitive and ranked by relevance:
    1. Exact task ID match (highest)
    2. Title starts with query
    3. Title contains query
    4. Description starts with query
    5. Description contains query
    6. Metadata contains query (lowest)

    Args:
        q: Search query (minimum 1 character).
    """
    params = {"q": q}
    url = _api("/tasks/search")
    logger.debug("search_tasks -> GET %s params=%s", url, params)
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params)
            logger.debug("search_tasks <- %s (%d bytes)", resp.status_code, len(resp.content))
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.error("search_tasks failed: %s", e)
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
    project_id: Optional[str] = None,
) -> dict:
    """Create a new task.

    Args:
        title: Task title (required).
        description: Task description.
        status: Initial status. Use list_statuses() to see valid values and descriptions.
        specialization: Task specialization (general, coding, planning, research).
        priority: Priority (higher = more important). Default 0.
        blocked_by: List of task IDs this task depends on.
        metadata: Arbitrary JSON metadata for agent context.
        id: Optional client-provided task ID. If omitted, the server generates one. Rejects duplicates (409).
        project_id: Optional project slug to group related tasks (e.g. "galaxy-map-v2").
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
    if project_id is not None:
        body["project_id"] = project_id
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
    project_id: Optional[str] = None,
) -> dict:
    """Update a task (partial update — only provided fields are changed).

    Common uses:
        update_task(task_id="abc123", project_id="my-project")  # assign to project
        update_task(task_id="abc123", status="done")             # mark complete

    Args:
        task_id: The task ID to update.
        title: New title.
        description: New description.
        status: New status. Use list_statuses() to see valid values and allowed transitions.
        specialization: New specialization (general, coding, planning, research).
        priority: New priority.
        blocked_by: New list of blocker task IDs (replaces existing list).
        metadata: New metadata dict (replaces existing metadata).
        project_id: Project slug (set to null to remove from project).
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
    if project_id is not None:
        body["project_id"] = project_id
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
async def list_projects() -> list[dict]:
    """List distinct project slugs with task counts.

    Returns a list of objects with project_id and task_count.
    Only includes tasks that have a project_id set.
    """
    url = _api("/tasks/projects")
    logger.debug("list_projects -> GET %s", url)
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            logger.debug("list_projects <- %s (%d bytes)", resp.status_code, len(resp.content))
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.error("list_projects failed: %s", e)
            raise


@mcp.tool()
async def list_statuses() -> list[dict]:
    """List all valid task statuses with metadata including descriptions.

    Returns a list of status objects, each with: key, label, description, order, color, allowed_transitions, terminal.
    Use descriptions to understand the purpose of each status and guide agents in choosing the right one.
    """
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
async def get_status_details(status_key: str) -> dict:
    """Get detailed information for a single status, including description and allowed transitions.

    Args:
        status_key: The status key to look up (e.g. 'in_progress', 'queued').

    Returns a status object with: key, label, description, order, color, allowed_transitions, terminal.
    Use the description to understand when to move a task to this status.
    """
    url = _api(f"/statuses/{status_key}")
    logger.debug("get_status_details -> GET %s", url)
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            logger.debug("get_status_details <- %s (%d bytes)", resp.status_code, len(resp.content))
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.error("get_status_details failed: %s", e)
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


@mcp.tool()
async def get_task_stats(
    status: Optional[str] = None,
    specialization: Optional[str] = None,
) -> dict:
    """Get task statistics.

    Returns total task count and breakdowns by status and specialization.
    Optional status and specialization query params can filter the statistics.

    Args:
        status: Filter by status. Use list_statuses() to see valid values.
        specialization: Filter by specialization (general, coding, planning, research).
        project_id: Filter by project slug (e.g. "galaxy-map-v2").

    Returns:
        dict with keys:
            - total: Total number of tasks
            - by_status: Dict mapping status -> count
            - by_specialization: Dict mapping specialization -> count
    """
    params = {}
    if status:
        params["status"] = status
    if specialization:
        params["specialization"] = specialization
    url = _api("/stats/tasks")
    logger.debug("get_task_stats -> GET %s params=%s", url, params)
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params)
            logger.debug("get_task_stats <- %s (%d bytes)", resp.status_code, len(resp.content))
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.error("get_task_stats failed: %s", e)
            raise


def main():
    logger.info("Running with transport=%s", TRANSPORT)
    mcp.run(transport=TRANSPORT)


if __name__ == "__main__":
    main()


@mcp.tool()
async def create_project_plan(
    project_id: str,
    tasks: list[dict],
    shared_metadata: Optional[dict] = None,
    task_id: Optional[str] = None,
) -> dict:
    """Create an entire project plan as a tree of tasks.

    IMPORTANT: Always include shared_metadata with the target repo.
    Without it, downstream agents cannot clone the repository and will fail.

    STRUCTURE:
      - The `tasks` array contains ONLY research tasks. They run in parallel.
      - Coding/testing tasks go inside a research task's `subtasks`.
      - Subtasks are blocked by their parent — they start after the parent completes.
      - This is the ONLY way to create dependencies.

    ROOT TASK fields (items in the `tasks` array):
      - title (str, REQUIRED): must start with "Research", "Analyze", "Investigate", or "Survey"
      - specialization (str, REQUIRED): MUST be "research"
      - description (str, REQUIRED): 2-3 sentences ending with "Done when: <criteria>"
      - subtasks (list, REQUIRED): coding/testing tasks that depend on this research

    SUBTASK fields (items in a task's `subtasks`):
      - title (str, REQUIRED): what to do
      - specialization (str, REQUIRED): "coding", "planning", or "claude-code"
      - description (str, REQUIRED): 2-3 sentences ending with "Done when: <criteria>"
      - subtasks (list, optional): further nested tasks

    Priority is set automatically by depth: root=10, children=9, grandchildren=8, min=1.

    Example — two parallel research tracks, each with coding and testing subtasks:

        create_project_plan(
            project_id="api-improvements",
            shared_metadata={"repo": "myorg/my-api"},
            tasks=[{
                "title": "Research rate limiting approaches",
                "specialization": "research",
                "description": "Survey rate limiting libraries for FastAPI. Done when: recommended approach documented.",
                "subtasks": [{
                    "title": "Implement rate limiting middleware",
                    "specialization": "coding",
                    "description": "Configure SlowAPI with 60 req/min per-IP limit. Done when: returns 429 on excess requests.",
                    "subtasks": [{
                        "title": "Write rate limiting tests",
                        "specialization": "coding",
                        "description": "Test 429 responses and per-IP isolation. Done when: all tests pass."
                    }]
                }]
            }, {
                "title": "Research caching strategies",
                "specialization": "research",
                "description": "Evaluate Redis vs in-memory caching for API responses. Done when: approach selected.",
                "subtasks": [{
                    "title": "Implement response caching",
                    "specialization": "coding",
                    "description": "Add Redis caching to GET endpoints with 5-min TTL. Done when: cache hits return cached data.",
                    "subtasks": [{
                        "title": "Write caching tests",
                        "specialization": "coding",
                        "description": "Test cache hit/miss and TTL expiry. Done when: all tests pass."
                    }]
                }]
            }]
        )

    WRONG — coding tasks at root level (will be rejected):
        tasks=[
            {"title": "Research X", "specialization": "research", "subtasks": [...]},
            {"title": "Research Y", "specialization": "research", "subtasks": [...]},
            {"title": "Implement X", "specialization": "coding", ...},  # REJECTED
            {"title": "Implement Y", "specialization": "coding", ...}   # REJECTED
        ]

    Args:
        project_id: Short slug identifying the project (e.g. "api-improvements").
        tasks: List of root task nodes. ALL root tasks MUST have specialization "research".
        shared_metadata: Dict merged into every task's metadata at creation.
                         MUST include "repo" key with the target repository as "org/repo-name".
                         Example: {"repo": "myorg/my-api"}
        task_id: Your task ID (from "Task ID: xxx" in the prompt). Sets project_id on your task.
    """
    # Validate: root tasks must be research-only
    for i, task in enumerate(tasks):
        spec = task.get("specialization", "")
        if spec != "research":
            return {
                "error": f"Root task #{i+1} '{task.get('title', '')}' has specialization "
                f"'{spec}' but root tasks MUST be 'research'. "
                f"Move it into a research task's subtasks array and call create_project_plan again."
            }

    body = {"project_id": project_id, "tasks": tasks}
    if task_id:
        body["task_id"] = task_id
    if shared_metadata:
        # Coerce string to dict if LLM passed JSON string instead of dict
        if isinstance(shared_metadata, str):
            try:
                shared_metadata = json.loads(shared_metadata)
            except (json.JSONDecodeError, TypeError):
                return {"error": f"shared_metadata must be a dict, got string: {shared_metadata[:200]}"}
        body["shared_metadata"] = shared_metadata
    url = _api("/projects/plan")
    logger.debug("create_project_plan -> POST %s body=%s", url, body)
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=body, timeout=30.0)
            logger.debug("create_project_plan <- %s (%d bytes)", resp.status_code, len(resp.content))
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get("detail", "Unknown error")
            logger.error("create_project_plan failed: %s", error_detail)
            return {"error": error_detail}
        except httpx.HTTPError as e:
            logger.error("create_project_plan failed: %s", e)
            raise

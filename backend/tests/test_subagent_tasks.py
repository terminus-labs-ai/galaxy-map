"""Tests for subagent task creation API."""

import pytest
from fastapi.testclient import TestClient
from main import app
from infrastructure import get_db
from domain.task.model import Task
from domain.task.service import TaskService


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
async def db():
    """Get database connection."""
    db = await get_db()
    yield db
    await db.close()


@pytest.mark.asyncio
async def test_create_subagent_task(client):
    """Test creating a subagent task linked to a parent task."""
    # First create a parent task
    parent_response = client.post("/api/tasks", json={
        "title": "Parent Task",
        "description": "This is the parent task",
        "status": "backlog",
        "specialization": "general",
        "priority": 1,
        "metadata": {"test": "parent"}
    })
    
    assert parent_response.status_code == 201
    parent_task = parent_response.json()
    parent_task_id = parent_task["id"]
    
    # Now create a subagent task
    subagent_response = client.post(f"/api/tasks/{parent_task_id}/subagent", json={
        "parent_task_id": parent_task_id,
        "title": "Subagent Task",
        "description": "This is a subagent task",
        "status": "queued",
        "specialization": "coding",
        "priority": 2,
        "metadata": {"test": "subagent"}
    })
    
    assert subagent_response.status_code == 201
    subagent_task = subagent_response.json()
    
    # Verify the subagent task was created correctly
    assert subagent_task["title"] == "Subagent Task"
    assert subagent_task["description"] == "This is a subagent task"
    assert subagent_task["status"] == "queued"
    assert subagent_task["specialization"] == "coding"
    assert subagent_task["priority"] == 2
    assert subagent_task["metadata"]["test"] == "subagent"
    assert subagent_task["blocked_by"] == [parent_task_id]
    
    # Verify the parent task exists and has the correct blocked_by relationship
    get_response = client.get(f"/api/tasks/{parent_task_id}")
    assert get_response.status_code == 200
    parent_task_data = get_response.json()
    
    # The parent task should not be blocked by the subagent task (it's the reverse)
    # But the subagent task should be blocked by the parent task
    assert parent_task_data["id"] == parent_task_id


@pytest.mark.asyncio
async def test_create_subagent_task_with_invalid_parent(client):
    """Test creating a subagent task with invalid parent task ID."""
    # Try to create a subagent task with a non-existent parent
    response = client.post("/api/tasks/invalid-id/subagent", json={
        "parent_task_id": "invalid-id",
        "title": "Subagent Task",
        "description": "This is a subagent task",
        "status": "queued",
        "specialization": "coding",
        "priority": 2,
        "metadata": {}
    })
    
    # Should fail with 404 since parent task doesn't exist
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_subagent_task_with_project_id(client):
    """Test creating a subagent task with project ID."""
    # Create a parent task
    parent_response = client.post("/api/tasks", json={
        "title": "Parent Task",
        "description": "This is the parent task",
        "status": "backlog",
        "specialization": "general",
        "priority": 1,
        "metadata": {}
    })
    
    assert parent_response.status_code == 201
    parent_task = parent_response.json()
    parent_task_id = parent_task["id"]
    
    # Create a subagent task with project ID
    subagent_response = client.post(f"/api/tasks/{parent_task_id}/subagent", json={
        "parent_task_id": parent_task_id,
        "title": "Subagent Task",
        "description": "This is a subagent task",
        "status": "queued",
        "specialization": "coding",
        "priority": 2,
        "project_id": "test-project",
        "metadata": {}
    })
    
    assert subagent_response.status_code == 201
    subagent_task = subagent_response.json()
    
    # Verify project ID is set correctly
    assert subagent_task["project_id"] == "test-project"
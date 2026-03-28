"""Tests for subagent orchestration framework."""

import pytest
import aiosqlite
from backend.domain.subagent.service import SubagentService
from backend.domain.task.service import TaskService
from backend.domain.orchestration.service import OrchestrationService


@pytest.mark.asyncio
async def test_subagent_crud_operations():
    """Test subagent creation, retrieval, and deletion."""
    # Setup in-memory database for testing
    db = await aiosqlite.connect(":memory:")
    await db.execute("CREATE TABLE subagents (id TEXT PRIMARY KEY, name TEXT, specialization TEXT, description TEXT, status TEXT, metadata TEXT, created_at TEXT, updated_at TEXT)")
    await db.execute("CREATE TABLE tasks (id TEXT PRIMARY KEY, title TEXT, description TEXT, status TEXT, specialization TEXT, priority INTEGER, blocked_by TEXT, metadata TEXT, created_at TEXT, updated_at TEXT)")
    await db.commit()
    
    service = SubagentService(db)
    
    # Create a subagent
    subagent = await service.create_subagent(
        name="Code Reviewer",
        specialization="code_review",
        description="Specialized in code review tasks",
        status="active"
    )
    
    assert subagent.id is not None
    assert subagent.name == "Code Reviewer"
    assert subagent.specialization == "code_review"
    assert subagent.status == "active"
    
    # Retrieve the subagent
    retrieved = await service.get_subagent(subagent.id)
    assert retrieved.id == subagent.id
    assert retrieved.name == "Code Reviewer"
    
    # Update the subagent
    updated = await service.update_subagent(
        subagent_id=subagent.id,
        name="Enhanced Code Reviewer",
        status="inactive"
    )
    
    assert updated.name == "Enhanced Code Reviewer"
    assert updated.status == "inactive"
    
    # List subagents
    subagents = await service.list_subagents()
    assert len(subagents) == 1
    
    # List subagents by specialization
    subagents_by_spec = await service.list_subagents("code_review")
    assert len(subagents_by_spec) == 1
    
    # Delete the subagent
    await service.delete_subagent(subagent.id)
    deleted = await service.get_subagent(subagent.id)
    assert deleted is None
    
    await db.close()


@pytest.mark.asyncio
async def test_orchestration_functionality():
    """Test orchestration functionality."""
    # Setup in-memory database for testing
    db = await aiosqlite.connect(":memory:")
    await db.execute("CREATE TABLE subagents (id TEXT PRIMARY KEY, name TEXT, specialization TEXT, description TEXT, status TEXT, metadata TEXT, created_at TEXT, updated_at TEXT)")
    await db.execute("CREATE TABLE tasks (id TEXT PRIMARY KEY, title TEXT, description TEXT, status TEXT, specialization TEXT, priority INTEGER, blocked_by TEXT, metadata TEXT, created_at TEXT, updated_at TEXT)")
    await db.execute("CREATE TABLE subagent_tasks (id TEXT PRIMARY KEY, task_id TEXT, subagent_id TEXT, status TEXT, assigned_at TEXT, completed_at TEXT, result TEXT, metadata TEXT)")
    await db.commit()
    
    # Create services
    subagent_service = SubagentService(db)
    task_service = TaskService(db)
    orchestration_service = OrchestrationService(db)
    
    # Create a task
    task = await task_service.create_task(
        title="Code Review Task",
        description="Review the new feature implementation",
        specialization="code_review"
    )
    
    # Create a subagent
    subagent = await subagent_service.create_subagent(
        name="Code Reviewer",
        specialization="code_review",
        description="Specialized in code review tasks",
        status="active"
    )
    
    # Delegate task to subagent
    result = await orchestration_service.delegate_task_to_subagent(
        task_id=task.id,
        specialization="code_review"
    )
    
    assert "subagent_id" in result
    assert "subagent_task_id" in result
    
    # Get orchestration info
    info = await orchestration_service.get_task_orchestration_info(task.id)
    assert info["is_delegated"] is True
    assert info["subagent_id"] == subagent.id
    assert info["subagent_specialization"] == "code_review"
    
    await db.close()
"""Tests for POST /api/projects/plan endpoint."""

import pytest


@pytest.mark.asyncio
async def test_basic_plan_creation(client, sample_plan):
    """3 tasks, 2 levels deep — correct status, project_id, blocked_by, priority."""
    resp = await client.post("/api/projects/plan", json=sample_plan)
    assert resp.status_code == 201
    data = resp.json()

    assert data["project_id"] == "test-project"
    assert data["tasks_created"] == 3

    root = data["task_tree"][0]
    assert root["status"] == "queued"
    assert root["blocked_by"] == []
    assert root["priority"] == 10
    assert root["specialization"] == "research"

    # Children blocked by parent
    for child in root["subtasks"]:
        assert child["status"] == "queued"
        assert child["blocked_by"] == [root["id"]]
        assert child["priority"] == 9

    # Cleanup
    for child in root["subtasks"]:
        await client.delete(f"/api/tasks/{child['id']}")
    await client.delete(f"/api/tasks/{root['id']}")


@pytest.mark.asyncio
async def test_sibling_parallelism(client):
    """Parent with 3 subtasks — siblings blocked by parent only, not each other."""
    plan = {
        "project_id": "sibling-test",
        "tasks": [{
            "title": "Parent task for sibling test",
            "specialization": "planning",
            "description": "Parent that has three parallel children. Done when: all children done.",
            "subtasks": [
                {"title": "Sibling A for parallel test", "specialization": "coding", "description": "First parallel child task. Done when: A is complete."},
                {"title": "Sibling B for parallel test", "specialization": "coding", "description": "Second parallel child task. Done when: B is complete."},
                {"title": "Sibling C for parallel test", "specialization": "research", "description": "Third parallel child task. Done when: C is complete."},
            ],
        }],
    }
    resp = await client.post("/api/projects/plan", json=plan)
    assert resp.status_code == 201
    data = resp.json()

    parent = data["task_tree"][0]
    siblings = parent["subtasks"]
    assert len(siblings) == 3

    # Each sibling blocked only by parent
    for s in siblings:
        assert s["blocked_by"] == [parent["id"]]

    # No sibling blocked by another sibling
    sibling_ids = {s["id"] for s in siblings}
    for s in siblings:
        assert not sibling_ids.intersection(s["blocked_by"])

    # Cleanup
    for s in siblings:
        await client.delete(f"/api/tasks/{s['id']}")
    await client.delete(f"/api/tasks/{parent['id']}")


@pytest.mark.asyncio
async def test_deep_nesting(client):
    """4 levels deep — blocked_by chains correctly (each blocked by direct parent only)."""
    plan = {
        "project_id": "deep-test",
        "tasks": [{
            "title": "Level 0 root task for deep nesting",
            "specialization": "planning",
            "description": "Root of 4-level chain for testing. Done when: all descendants done.",
            "subtasks": [{
                "title": "Level 1 child task for nesting",
                "specialization": "research",
                "description": "Second level in chain for testing. Done when: child done.",
                "subtasks": [{
                    "title": "Level 2 grandchild task in chain",
                    "specialization": "coding",
                    "description": "Third level in chain for testing. Done when: child done.",
                    "subtasks": [{
                        "title": "Level 3 great-grandchild leaf task",
                        "specialization": "coding",
                        "description": "Leaf task at depth 3 for testing. Done when: complete.",
                    }],
                }],
            }],
        }],
    }
    resp = await client.post("/api/projects/plan", json=plan)
    assert resp.status_code == 201
    data = resp.json()

    # Walk the chain
    level0 = data["task_tree"][0]
    level1 = level0["subtasks"][0]
    level2 = level1["subtasks"][0]
    level3 = level2["subtasks"][0]

    assert level0["blocked_by"] == []
    assert level1["blocked_by"] == [level0["id"]]
    assert level2["blocked_by"] == [level1["id"]]
    assert level3["blocked_by"] == [level2["id"]]

    # NOT blocked by grandparent
    assert level0["id"] not in level2["blocked_by"]
    assert level0["id"] not in level3["blocked_by"]

    # Cleanup
    for t in [level3, level2, level1, level0]:
        await client.delete(f"/api/tasks/{t['id']}")


@pytest.mark.asyncio
async def test_multiple_root_tasks(client):
    """2 root tasks with subtasks — roots have empty blocked_by, trees are independent."""
    plan = {
        "project_id": "multi-root-test",
        "tasks": [
            {
                "title": "Root A independent branch task",
                "specialization": "research",
                "description": "First independent root for testing. Done when: child done.",
                "subtasks": [{
                    "title": "Child of Root A branch task",
                    "specialization": "coding",
                    "description": "Subtask of root A for testing. Done when: implemented.",
                }],
            },
            {
                "title": "Root B independent branch task",
                "specialization": "planning",
                "description": "Second independent root for testing. Done when: child done.",
                "subtasks": [{
                    "title": "Child of Root B branch task",
                    "specialization": "coding",
                    "description": "Subtask of root B for testing. Done when: implemented.",
                }],
            },
        ],
    }
    resp = await client.post("/api/projects/plan", json=plan)
    assert resp.status_code == 201
    data = resp.json()

    assert data["tasks_created"] == 4

    root_a = data["task_tree"][0]
    root_b = data["task_tree"][1]

    assert root_a["blocked_by"] == []
    assert root_b["blocked_by"] == []

    # Children blocked by their own parent only
    child_a = root_a["subtasks"][0]
    child_b = root_b["subtasks"][0]
    assert child_a["blocked_by"] == [root_a["id"]]
    assert child_b["blocked_by"] == [root_b["id"]]

    # Trees are independent
    assert root_b["id"] not in child_a["blocked_by"]
    assert root_a["id"] not in child_b["blocked_by"]

    # Cleanup
    for t in [child_a, child_b, root_a, root_b]:
        await client.delete(f"/api/tasks/{t['id']}")


@pytest.mark.asyncio
async def test_priority_assignment(client):
    """Depth 0=10, depth 1=9, depth 9=1, depth 10+=1 (floor)."""
    # Build a 10-level chain (depth 0 through 9)
    def _build_chain(depth, max_depth):
        node = {
            "title": f"Priority test depth {depth} chain task",
            "specialization": "coding",
            "description": f"Task at depth {depth} for priority testing. Done when: subtask done.",
        }
        if depth < max_depth:
            node["subtasks"] = [_build_chain(depth + 1, max_depth)]
        return node

    plan = {
        "project_id": "priority-test",
        "tasks": [_build_chain(0, 9)],
    }
    resp = await client.post("/api/projects/plan", json=plan)
    assert resp.status_code == 201
    data = resp.json()

    assert data["tasks_created"] == 10

    # Walk the chain and check priorities
    node = data["task_tree"][0]
    expected_priorities = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    all_ids = []
    for expected_p in expected_priorities:
        assert node["priority"] == expected_p, f"Depth {10 - expected_p}: expected priority {expected_p}, got {node['priority']}"
        all_ids.append(node["id"])
        if node.get("subtasks"):
            node = node["subtasks"][0]

    # Cleanup (reverse order)
    for tid in reversed(all_ids):
        await client.delete(f"/api/tasks/{tid}")


@pytest.mark.asyncio
async def test_validation_missing_title(client):
    """Missing title returns 400."""
    plan = {
        "project_id": "validation-test",
        "tasks": [{
            "title": "",
            "specialization": "coding",
            "description": "Task with empty title for validation testing. Done when: validated.",
        }],
    }
    resp = await client.post("/api/projects/plan", json=plan)
    assert resp.status_code == 400
    detail = resp.json()["detail"]
    assert "title" in str(detail).lower()


@pytest.mark.asyncio
async def test_validation_invalid_specialization(client):
    """Invalid specialization returns 400 with valid options listed."""
    plan = {
        "project_id": "validation-test",
        "tasks": [{
            "title": "Task with invalid specialization value",
            "specialization": "underwater-basket-weaving",
            "description": "Testing invalid specialization validation. Done when: validated.",
        }],
    }
    resp = await client.post("/api/projects/plan", json=plan)
    assert resp.status_code == 400
    detail = str(resp.json()["detail"])
    assert "underwater-basket-weaving" in detail


@pytest.mark.asyncio
async def test_validation_empty_tasks(client):
    """Empty tasks array returns 400."""
    plan = {"project_id": "validation-test", "tasks": []}
    resp = await client.post("/api/projects/plan", json=plan)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_validation_empty_project_id(client):
    """Empty project_id returns 400."""
    plan = {
        "project_id": "",
        "tasks": [{
            "title": "Task with empty project id test",
            "specialization": "coding",
            "description": "Testing empty project_id validation. Done when: validated.",
        }],
    }
    resp = await client.post("/api/projects/plan", json=plan)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_task_count_limit(client):
    """Plan with 51 tasks is rejected."""
    tasks = []
    for i in range(51):
        tasks.append({
            "title": f"Bulk task number {i} for count limit test",
            "specialization": "coding",
            "description": f"Task {i} of 51 for testing the count limit. Done when: validated.",
        })

    plan = {"project_id": "limit-test", "tasks": tasks}
    resp = await client.post("/api/projects/plan", json=plan)
    assert resp.status_code == 400
    detail = str(resp.json()["detail"])
    assert "51" in detail or "50" in detail


@pytest.mark.asyncio
async def test_depth_limit(client):
    """Plan nested 11 levels deep is rejected."""
    # Build 11-level chain
    node = {
        "title": "Deepest leaf task at level eleven",
        "specialization": "coding",
        "description": "Leaf at depth 11 for testing depth limit. Done when: validated.",
    }
    for i in range(10, -1, -1):
        node = {
            "title": f"Depth limit test level {i} wrapping task",
            "specialization": "coding",
            "description": f"Wrapper at depth {i} for depth limit test. Done when: validated.",
            "subtasks": [node],
        }

    plan = {"project_id": "depth-limit-test", "tasks": [node]}
    resp = await client.post("/api/projects/plan", json=plan)
    assert resp.status_code == 400
    detail = str(resp.json()["detail"]).lower()
    assert "depth" in detail


@pytest.mark.asyncio
async def test_tasks_persisted_to_db(client, sample_plan):
    """Verify created tasks are actually in the DB via GET /api/tasks."""
    resp = await client.post("/api/projects/plan", json=sample_plan)
    assert resp.status_code == 201
    data = resp.json()

    root = data["task_tree"][0]

    # Fetch the root task directly
    get_resp = await client.get(f"/api/tasks/{root['id']}")
    assert get_resp.status_code == 200
    task = get_resp.json()
    assert task["title"] == root["title"]
    assert task["status"] == "queued"
    assert task["project_id"] == "test-project"

    # Cleanup
    for child in root["subtasks"]:
        await client.delete(f"/api/tasks/{child['id']}")
    await client.delete(f"/api/tasks/{root['id']}")

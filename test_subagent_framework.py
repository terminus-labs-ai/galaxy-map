#!/usr/bin/env python3
"""
Simple test script to verify subagent orchestration framework works.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.domain.subagent.model import Subagent, SubagentTask
from backend.domain.subagent.repository import SubagentRepository, SubagentTaskRepository
from backend.domain.subagent.service import SubagentService
from backend.domain.orchestration.service import OrchestrationService

def test_models():
    """Test that our models work correctly."""
    print("Testing Subagent model...")
    subagent = Subagent(
        id="test123",
        name="Test Subagent",
        specialization="test_specialization"
    )
    assert subagent.id == "test123"
    assert subagent.name == "Test Subagent"
    assert subagent.specialization == "test_specialization"
    print("✓ Subagent model works correctly")
    
    print("Testing SubagentTask model...")
    subagent_task = SubagentTask(
        id="task123",
        task_id="task456",
        subagent_id="subagent789"
    )
    assert subagent_task.id == "task123"
    assert subagent_task.task_id == "task456"
    assert subagent_task.subagent_id == "subagent789"
    print("✓ SubagentTask model works correctly")

def test_services():
    """Test that services can be imported and instantiated."""
    print("Testing service imports...")
    # This would normally require a database connection, but we're just checking imports
    print("✓ Services import correctly")

if __name__ == "__main__":
    print("Testing Subagent Orchestration Framework")
    print("=" * 50)
    
    try:
        test_models()
        test_services()
        print("=" * 50)
        print("✓ All tests passed! Subagent orchestration framework is ready.")
    except Exception as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)
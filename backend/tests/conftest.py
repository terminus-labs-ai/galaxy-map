"""Shared test fixtures."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Load config before importing app
from core import Config
Config.load()

from main import app


@pytest_asyncio.fixture
async def client():
    """Async HTTP client for testing the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def sample_plan():
    """A basic 2-level plan for testing."""
    return {
        "project_id": "test-project",
        "tasks": [
            {
                "title": "Research the problem space",
                "specialization": "research",
                "description": "Investigate approaches and summarize findings. Done when: summary written.",
                "subtasks": [
                    {
                        "title": "Implement the solution",
                        "specialization": "coding",
                        "description": "Build the feature based on research. Done when: code compiles and works.",
                    },
                    {
                        "title": "Write documentation for feature",
                        "specialization": "planning",
                        "description": "Document the new feature for users. Done when: docs published.",
                    },
                ],
            }
        ],
    }

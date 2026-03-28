"""
Galaxy Map — minimal task tracker for AI agents.
FastAPI + SQLite backend (refactored).
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core import Config
from infrastructure import init_db
from api.routes import tasks, messages, system, projects, subagents, orchestration


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App startup/shutdown."""
    Config.load()
    await init_db()
    yield


# Create app
app = FastAPI(
    title=Config.get("app.title"),
    description=Config.get("app.description"),
    version=Config.get("app.version"),
    lifespan=lifespan,
)

# CORS
cors_config = Config.get("api.cors", {})
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config.get("allow_origins", ["*"]),
    allow_credentials=cors_config.get("allow_credentials", True),
    allow_methods=cors_config.get("allow_methods", ["*"]),
    allow_headers=cors_config.get("allow_headers", ["*"]),
)

# Include routers
app.include_router(tasks.router)
app.include_router(messages.router)
app.include_router(system.router)
app.include_router(projects.router)
app.include_router(subagents.router)
app.include_router(orchestration.router)


@app.get("/api/health")
async def health():
    """Health check."""
    app_config = Config.app()
    return {
        "status": "ok",
        "version": app_config.get("version", "0.3.0"),
    }

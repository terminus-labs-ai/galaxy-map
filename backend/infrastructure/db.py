"""Database connection and initialization."""

import os
from pathlib import Path
import aiosqlite
from core import Config


async def get_db() -> aiosqlite.Connection:
    """Get a database connection."""
    db_path = _get_db_path()
    db = await aiosqlite.connect(str(db_path))
    db.row_factory = aiosqlite.Row

    db_config = Config.database()
    journal_mode = db_config.get("journal_mode", "WAL")
    foreign_keys = db_config.get("foreign_keys", True)

    await db.execute(f"PRAGMA journal_mode={journal_mode}")
    await db.execute("PRAGMA busy_timeout=5000")
    if foreign_keys:
        await db.execute("PRAGMA foreign_keys=ON")

    return db


def _get_db_path() -> Path:
    """Resolve database path from config or environment."""
    env_path = os.environ.get("DATABASE_PATH")
    if env_path:
        return Path(env_path)

    db_config = Config.database()
    db_name = db_config.get("path", "board.db")

    # If relative, it's relative to backend/
    if not Path(db_name).is_absolute():
        return Path(__file__).parent.parent / db_name

    return Path(db_name)


async def init_db():
    """Initialize database schema."""
    db = await get_db()

    await db.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id              TEXT PRIMARY KEY,
            title           TEXT NOT NULL,
            description     TEXT NOT NULL DEFAULT '',
            status          TEXT NOT NULL DEFAULT 'backlog',
            specialization  TEXT NOT NULL DEFAULT 'general',
            priority        INTEGER NOT NULL DEFAULT 0,
            blocked_by      TEXT NOT NULL DEFAULT '[]',
            metadata        TEXT NOT NULL DEFAULT '{}',
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        )
    """)

    await db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_specialization ON tasks(specialization)")

    # Migration: add project_id column (nullable, no FK)
    try:
        await db.execute("ALTER TABLE tasks ADD COLUMN project_id TEXT DEFAULT NULL")
    except Exception:
        pass  # Column already exists
    await db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id)")

    await db.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id              TEXT PRIMARY KEY,
            user_id         TEXT NOT NULL,
            text            TEXT NOT NULL,
            response        TEXT,
            status          TEXT NOT NULL DEFAULT 'pending',
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        )
    """)

    await db.execute("CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id)")

    # Task history/audit log table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS task_history (
            id              TEXT PRIMARY KEY,
            task_id         TEXT NOT NULL,
            event_type      TEXT NOT NULL,
            old_value       TEXT DEFAULT NULL,
            new_value       TEXT DEFAULT NULL,
            changed_by      TEXT NOT NULL DEFAULT 'system',
            timestamp       TEXT NOT NULL,
            details         TEXT DEFAULT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    """)
    await db.execute("CREATE INDEX IF NOT EXISTS idx_task_history_task_id ON task_history(task_id)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_task_history_timestamp ON task_history(timestamp)")

    # Subagent table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS subagents (
            id              TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            specialization  TEXT NOT NULL,
            description     TEXT NOT NULL DEFAULT '',
            status          TEXT NOT NULL DEFAULT 'active',
            metadata        TEXT NOT NULL DEFAULT '{}',
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        )
    """)
    await db.execute("CREATE INDEX IF NOT EXISTS idx_subagents_specialization ON subagents(specialization)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_subagents_status ON subagents(status)")

    # Subagent task assignments table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS subagent_tasks (
            id              TEXT PRIMARY KEY,
            task_id         TEXT NOT NULL,
            subagent_id     TEXT NOT NULL,
            status          TEXT NOT NULL DEFAULT 'pending',
            assigned_at     TEXT NOT NULL,
            completed_at    TEXT DEFAULT NULL,
            result          TEXT DEFAULT NULL,
            metadata        TEXT NOT NULL DEFAULT '{}',
            FOREIGN KEY (task_id) REFERENCES tasks(id),
            FOREIGN KEY (subagent_id) REFERENCES subagents(id)
        )
    """)
    await db.execute("CREATE INDEX IF NOT EXISTS idx_subagent_tasks_task_id ON subagent_tasks(task_id)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_subagent_tasks_subagent_id ON subagent_tasks(subagent_id)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_subagent_tasks_status ON subagent_tasks(status)")

    await db.commit()
    await db.close()

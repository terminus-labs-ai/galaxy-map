"""Configuration loader from YAML files."""

import os
from pathlib import Path
from typing import Any
import yaml


class Config:
    """Load and provide access to app configuration."""

    _instance = None
    _data = None

    @classmethod
    def load(cls):
        """Load config from YAML files. Called once on app startup."""
        config_dir = Path(__file__).parent.parent / "config"

        # Load app.yaml
        app_yaml = config_dir / "app.yaml"
        with open(app_yaml) as f:
            cls._data = yaml.safe_load(f)

        # Load statuses.yaml
        statuses_yaml = config_dir / "statuses.yaml"
        with open(statuses_yaml) as f:
            statuses_data = yaml.safe_load(f)
            cls._data["statuses"] = statuses_data.get("statuses", [])

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get a config value using dot notation. E.g., 'app.title' or 'tasks.completed_statuses'."""
        if cls._data is None:
            cls.load()

        keys = key.split(".")
        value = cls._data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value

    @classmethod
    def app(cls) -> dict:
        """Get app section."""
        if cls._data is None:
            cls.load()
        return cls._data.get("app", {})

    @classmethod
    def database(cls) -> dict:
        """Get database section."""
        if cls._data is None:
            cls.load()
        return cls._data.get("database", {})

    @classmethod
    def specializations(cls) -> list[str]:
        """Get list of valid specializations."""
        if cls._data is None:
            cls.load()
        return cls._data.get("specializations", [])

    @classmethod
    def statuses(cls) -> list[dict]:
        """Get list of status configurations."""
        if cls._data is None:
            cls.load()
        return cls._data.get("statuses", [])

    @classmethod
    def completed_statuses(cls) -> list[str]:
        """Get statuses that mark a task as complete."""
        if cls._data is None:
            cls.load()
        return cls._data.get("tasks", {}).get("completed_statuses", [])

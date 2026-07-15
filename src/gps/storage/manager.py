"""
GPS Storage Layer Manager
─────────────────────────
Manages workspace files, templates, output cache generation, and directory structures.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class StorageManager:
    """Manages workspace paths, caching, and template files."""

    def __init__(self, root_dir: Path | None = None) -> None:
        self.root = root_dir or Path.cwd()
        self.profile_dir = self.root / "profile"
        self.history_dir = self.root / "history"
        self.data_cache = self.profile_dir / "data.json"

    def ensure_directories(self) -> None:
        """Create necessary directories if they do not exist."""
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def read_cache(self) -> dict[str, Any]:
        """Read saved provider cache values."""
        if not self.data_cache.exists():
            return {}
        try:
            with self.data_cache.open("r", encoding="utf-8") as f:
                return json.load(f) or {}
        except Exception:
            return {}

    def write_cache(self, data: dict[str, Any]) -> None:
        """Write compiled outputs to data.json cache."""
        self.ensure_directories()
        with self.data_cache.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def write_readme(self, content: str, readme_path: Path) -> None:
        """Write rendered content directly to profile/README.md."""
        target = self.root / readme_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

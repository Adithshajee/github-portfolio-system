"""
GPS Plugin Loader
─────────────────
Loads and registers dynamic plugins located in the gps/plugins folder
or local repository workspace plugins.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gps.engine import GPSEngine

logger = logging.getLogger("gps")


def discover_plugins(engine: GPSEngine) -> None:
    """Discover and dynamically load GPS plugins."""
    # 1. Discover internal plugins in the gps.plugins namespace
    try:
        import gps.plugins as plugins_ns

        # Type annotation to satisfy strict mypy checks on package namespaces
        path_list: list[str] = list(plugins_ns.__path__)
        for _, name, _ in pkgutil.iter_modules(path_list):
            importlib.import_module(f"gps.plugins.{name}")
            logger.debug("Successfully loaded built-in plugin: %s", name)
    except (ImportError, AttributeError) as e:
        logger.debug("Failed to scan built-in plugins folder: %s", e)

    # 2. Discover local plugins in the user workspace (.github/gps/plugins/)
    local_path = Path(".github/gps/plugins")
    if local_path.exists():
        resolved_path = str(local_path.resolve())
        if resolved_path not in sys.path:
            sys.path.insert(0, resolved_path)
        for file in local_path.glob("*.py"):
            if file.name != "__init__.py":
                try:
                    importlib.import_module(file.stem)
                    logger.info("Loaded workspace plugin: %s", file.name)
                except Exception as e:
                    logger.warning("Failed to load local workspace plugin %s: %s", file.name, e)

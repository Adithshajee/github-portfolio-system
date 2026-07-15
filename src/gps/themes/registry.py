"""
GPS Theme Registry
──────────────────
Manages theme definitions, metadata, versions, and style configurations.
Allows extensions and dynamic theme loading.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ThemeDescriptor:
    """Contains metadata, compatible layout parameters, and dependencies for a theme."""

    def __init__(
        self,
        name: str,
        display_name: str,
        version: str,
        author: str,
        accent_color: str,
        background_color: str,
        font_family: str,
        spacing: str = "normal",
        animations: bool = False,
        compatibility: str = ">=3.0.0",
        dependencies: list[str] | None = None,
    ) -> None:
        self.name = name
        self.display_name = display_name
        self.version = version
        self.author = author
        self.accent_color = accent_color
        self.background_color = background_color
        self.font_family = font_family
        self.spacing = spacing
        self.animations = animations
        self.compatibility = compatibility
        self.dependencies = dependencies or []

    def to_dict(self) -> dict[str, Any]:
        """Convert descriptor metadata to dictionary."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "version": self.version,
            "author": self.author,
            "style": {
                "accent_color": self.accent_color,
                "background_color": self.background_color,
                "font_family": self.font_family,
                "spacing": self.spacing,
                "animations": self.animations,
            },
            "compatibility": self.compatibility,
            "dependencies": self.dependencies,
        }


class ThemeRegistry:
    """Registry managing available templates and themes."""

    def __init__(self) -> None:
        self._themes: dict[str, ThemeDescriptor] = {}
        self._load_builtins()

    def _load_builtins(self) -> None:
        """Register GPS built-in core themes."""
        builtins = [
            ThemeDescriptor(
                name="swe_general",
                display_name="Software Engineer Classic",
                version="1.0.0",
                author="GPS Core",
                accent_color="#2563EB",  # Blue
                background_color="#0F172A",  # Slate
                font_family="Inter, system-ui",
                spacing="normal",
            ),
            ThemeDescriptor(
                name="ai_ml",
                display_name="AI & ML Specialist",
                version="1.0.0",
                author="GPS Core",
                accent_color="#8B5CF6",  # Purple
                background_color="#0B0F19",  # Dark Navy
                font_family="Roboto, sans-serif",
                spacing="compact",
            ),
            ThemeDescriptor(
                name="devops",
                display_name="Cloud & DevOps Engineer",
                version="1.0.0",
                author="GPS Core",
                accent_color="#10B981",  # Green
                background_color="#1E1E2E",  # Dark Gray
                font_family="Fira Code, monospace",
                spacing="wide",
            ),
            ThemeDescriptor(
                name="apple",
                display_name="Apple Clean Design",
                version="1.0.0",
                author="GPS Design Team",
                accent_color="#000000",
                background_color="#FFFFFF",
                font_family="-apple-system, BlinkMacSystemFont, sans-serif",
                spacing="normal",
            ),
            ThemeDescriptor(
                name="cyberpunk",
                display_name="Cyberpunk Neon",
                version="1.0.0",
                author="GPS Community",
                accent_color="#FF007F",  # Neon pink
                background_color="#0D0D1A",
                font_family="Orbitron, sans-serif",
                spacing="wide",
                animations=True,
            ),
        ]
        for t in builtins:
            self.register(t)

    def register(self, descriptor: ThemeDescriptor) -> None:
        """Register a new theme in the catalog."""
        self._themes[descriptor.name] = descriptor

    def get(self, name: str) -> ThemeDescriptor | None:
        """Get theme descriptor by name."""
        return self._themes.get(name)

    def list_all(self) -> list[ThemeDescriptor]:
        """List all registered themes."""
        return list(self._themes.values())

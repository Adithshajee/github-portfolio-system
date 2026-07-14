"""
GPS Theme and Layout Engine
───────────────────────────
Manages portfolio visual themes, resolves layout templates, and renders
markdown sections using Jinja2.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger("gps.themes")


class ThemeEngine:
    """
    Manages loading and rendering templates for different themes.
    """

    def __init__(self, theme_name: str, variant: str = "dark") -> None:
        self.theme_name = theme_name
        self.variant = variant
        self._init_env()

    def _init_env(self) -> None:
        """Initialize Jinja2 environment with built-in and user search paths."""
        search_paths = []

        # 1. User custom theme overrides in repository root
        user_path = Path(f".github/gps/themes/{self.theme_name}")
        if user_path.exists():
            search_paths.append(user_path)

        # 2. Package built-in themes templates directory
        builtin_path = Path(__file__).parent / "templates" / self.theme_name
        if builtin_path.exists():
            search_paths.append(builtin_path)

        # 3. Universal base templates fallback
        base_path = Path(__file__).parent / "templates" / "base"
        if base_path.exists():
            search_paths.append(base_path)
        else:
            # Fallback to local package directory structure
            search_paths.append(Path(__file__).parent / "templates")

        self.loader = FileSystemLoader([str(p.resolve()) for p in search_paths if p.exists()])
        self.env = Environment(
            loader=self.loader,
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render_template(self, template_name: str, context: dict[str, Any]) -> str:
        """
        Render a Jinja2 template file.

        Args:
            template_name: Stem filename (e.g. 'github.md', 'hero.md').
            context: Variables to pass to the template context.
        """
        try:
            # Try to get the specific template
            template = self.env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.debug("Template %s not found in theme, using fallback: %s", template_name, e)
            # Standard hardcoded fallback representation if template doesn't exist
            return self._fallback_render(template_name.replace(".md", ""), context)

    def _fallback_render(self, section_name: str, context: dict[str, Any]) -> str:
        """Fallback markdown structures if Jinja files are missing."""
        if section_name == "github":
            data = context.get("data")
            if not data:
                return ""
            lines = ["### 📂 Pinned & Active Repositories", ""]
            for repo in getattr(data, "repositories", []):
                desc = repo.description or "No description"
                lines.append(f"- **[{repo.name}]({repo.html_url})** — {desc}")
            return "\n".join(lines)
        return ""

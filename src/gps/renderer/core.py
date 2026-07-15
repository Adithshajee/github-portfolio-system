"""
GPS Rendering Subsystem
───────────────────────
Handles output rendering for README.md, JSON caches, HTML sites, Resumes, and PDFs.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from gps.utils.validators import sanitize_markdown_string, validate_readme_markers

logger = logging.getLogger(__name__)


class MarkdownRenderer:
    """Injects rendered markdown sections into a target README file."""

    def __init__(
        self,
        readme_path: Path,
        start_marker: str = "<!-- REPOS_START -->",
        end_marker: str = "<!-- REPOS_END -->",
    ) -> None:
        self.readme_path = readme_path
        self.start_marker = start_marker
        self.end_marker = end_marker

    def render_sections(
        self,
        order: list[str],
        theme_engine: Any,  # noqa: ANN401
        context: dict[str, Any],
    ) -> str:
        """Render and assemble multiple sections into a single markdown string."""
        rendered_blocks = []
        for section in order:
            content = theme_engine.render_template(f"{section}.md", context)
            if content:
                rendered_blocks.append(content)
        return "\n\n".join(rendered_blocks)

    def _read(self) -> str:
        if not self.readme_path.exists():
            raise FileNotFoundError(f"README not found at: {self.readme_path}")
        return self.readme_path.read_text(encoding="utf-8")

    def inject(self, section_content: str, dry_run: bool = False) -> str:
        content = self._read()
        clean_content = sanitize_markdown_string(section_content)
        replacement = f"{self.start_marker}\n\n{clean_content}\n\n{self.end_marker}"
        pattern = re.compile(
            re.escape(self.start_marker) + r".*?" + re.escape(self.end_marker),
            re.DOTALL,
        )

        if not validate_readme_markers(content, self.start_marker, self.end_marker):
            updated = content.rstrip() + "\n\n" + replacement + "\n"
        else:
            updated = pattern.sub(replacement, content)

        if dry_run:
            return updated

        self.readme_path.write_text(updated, encoding="utf-8")
        return updated


class JSONRenderer:
    """Exports provider data as structured JSON."""

    def __init__(self, output_path: Path) -> None:
        self.output_path = output_path

    def render(self, data: dict[str, Any], dry_run: bool = False) -> str:
        output = json.dumps(data, indent=2, default=str, ensure_ascii=False)
        if dry_run:
            return output
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(output, encoding="utf-8")
        return output


class HTMLRenderer:
    """Converts markdown output to a minimal HTML website page."""

    def render(self, markdown_content: str, title: str = "Developer Profile") -> str:
        escaped = markdown_content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return (
            f"<!DOCTYPE html>\n<html>\n<head><title>{title}</title></head>\n"
            f"<body><pre>{escaped}</pre></body>\n</html>"
        )


class ResumeRenderer:
    """Generates standard developer resume formatted outputs."""

    def render(self, profile_data: dict[str, Any]) -> str:
        username = profile_data.get("username", "Developer")
        return f"# RESUME — {username}\n\nTarget Role: Software Engineer\n..."


class PortfolioWebsiteRenderer:
    """Compiles local portfolio developer site HTML assets."""

    def render(self, markdown_content: str) -> str:
        return f"<html><body><div id='site'>{markdown_content}</div></body></html>"


class PDFRenderer:
    """Stub PDF exporter to generate layout documents."""

    def render(self, document_content: str) -> bytes:
        return document_content.encode("utf-8")

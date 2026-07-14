"""
GPS Rendering Engine
─────────────────────
Handles injecting provider output into the profile README.

The MarkdownRenderer:
  1. Reads the target README file
  2. Finds injection markers (<!-- REPOS_START --> / <!-- REPOS_END -->)
  3. Replaces content between markers with freshly rendered markdown
  4. Writes the result back (or returns it in dry-run mode)

Supports multiple output formats: markdown, JSON, HTML (stub).
"""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

from gps.utils.validators import sanitize_markdown_string, validate_readme_markers

logger = logging.getLogger(__name__)


class MarkdownRenderer:
    """
    Injects rendered markdown sections into a target README file.

    Args:
        readme_path: Path to the target README file.
        start_marker: Opening HTML comment marker.
        end_marker: Closing HTML comment marker.
    """

    def __init__(
        self,
        readme_path: Path,
        start_marker: str = "<!-- REPOS_START -->",
        end_marker: str = "<!-- REPOS_END -->",
    ) -> None:
        self.readme_path = readme_path
        self.start_marker = start_marker
        self.end_marker = end_marker

    def _read(self) -> str:
        """Read the README file content."""
        if not self.readme_path.exists():
            raise FileNotFoundError(
                f"README not found at: {self.readme_path}\nEnsure the path in gps.yml is correct."
            )
        return self.readme_path.read_text(encoding="utf-8")

    def inject(
        self,
        section_content: str,
        dry_run: bool = False,
    ) -> str:
        """
        Inject rendered section content between markers.

        Args:
            section_content: Rendered markdown to inject.
            dry_run: If True, return the result without writing to disk.

        Returns:
            The full updated README content as a string.
        """
        content = self._read()
        clean_content = sanitize_markdown_string(section_content)

        replacement = f"{self.start_marker}\n\n{clean_content}\n\n{self.end_marker}"

        pattern = re.compile(
            re.escape(self.start_marker) + r".*?" + re.escape(self.end_marker),
            re.DOTALL,
        )

        if not validate_readme_markers(content, self.start_marker, self.end_marker):
            logger.warning(
                "Injection markers not found in %s. Appending section to end of file.",
                self.readme_path,
            )
            updated = content.rstrip() + "\n\n" + replacement + "\n"
        else:
            updated = pattern.sub(replacement, content)

        if dry_run:
            logger.info("[DRY RUN] Generated section content:")
            try:
                print(f"\n{'─' * 60}")
                print(clean_content)
                print(f"{'─' * 60}\n")
            except UnicodeEncodeError:
                # Safe fallback using stdout's native encoding with error replacement
                enc = sys.stdout.encoding or "utf-8"
                border = "-" * 60
                sys.stdout.write(f"\n{border}\n")
                sys.stdout.write(clean_content.encode(enc, errors="replace").decode(enc) + "\n")
                sys.stdout.write(f"{border}\n\n")
            return updated

        self.readme_path.write_text(updated, encoding="utf-8")
        logger.info("✓ Updated %s", self.readme_path)
        return updated


class JSONRenderer:
    """
    Exports provider data as structured JSON.

    Args:
        output_path: Path to write the JSON output.
    """

    def __init__(self, output_path: Path) -> None:
        self.output_path = output_path

    def render(self, data: dict[str, Any], dry_run: bool = False) -> str:
        """
        Serialize provider data to JSON.

        Args:
            data: Dictionary of provider name → data dict.
            dry_run: If True, print to stdout instead of writing to file.

        Returns:
            JSON string.
        """
        output = json.dumps(data, indent=2, default=str, ensure_ascii=False)

        if dry_run:
            logger.info("[DRY RUN] JSON export preview:")
            print(output)
            return output

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(output, encoding="utf-8")
        logger.info("✓ JSON exported to %s", self.output_path)
        return output


class HTMLRenderer:
    """
    Stub HTML renderer for future use.

    Converts markdown output to a minimal HTML page.
    """

    def render(self, markdown_content: str, title: str = "Developer Profile") -> str:
        """Convert markdown to basic HTML (placeholder implementation)."""
        logger.warning("HTML renderer is a stub. Full implementation coming in GPS v2.1.")
        escaped = markdown_content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return (
            f"<!DOCTYPE html>\n<html>\n<head><title>{title}</title></head>\n"
            f"<body><pre>{escaped}</pre></body>\n</html>"
        )

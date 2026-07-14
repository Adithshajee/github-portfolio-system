"""Unit tests for the MarkdownRenderer and JSONRenderer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gps.renderer import JSONRenderer, MarkdownRenderer


@pytest.mark.unit
class TestMarkdownRenderer:
    def test_injects_content_between_markers(self, readme_with_markers: Path) -> None:
        renderer = MarkdownRenderer(readme_path=readme_with_markers)
        new_content = "### New Section\n\n- Item 1\n- Item 2"
        result = renderer.inject(new_content, dry_run=True)

        assert "### New Section" in result
        assert "- Item 1" in result
        assert "<!-- REPOS_START -->" in result
        assert "<!-- REPOS_END -->" in result
        # Old content should be replaced
        assert "### Old content" not in result

    def test_appends_when_markers_missing(self, readme_without_markers: Path) -> None:
        renderer = MarkdownRenderer(readme_path=readme_without_markers)
        new_content = "### Appended Section"
        result = renderer.inject(new_content, dry_run=True)

        assert "### Appended Section" in result
        assert "<!-- REPOS_START -->" in result
        assert "<!-- REPOS_END -->" in result

    def test_dry_run_does_not_write_file(self, readme_with_markers: Path) -> None:
        original = readme_with_markers.read_text(encoding="utf-8")
        renderer = MarkdownRenderer(readme_path=readme_with_markers)
        renderer.inject("New content", dry_run=True)
        # File should be unchanged
        assert readme_with_markers.read_text(encoding="utf-8") == original

    def test_writes_file_when_not_dry_run(self, readme_with_markers: Path) -> None:
        renderer = MarkdownRenderer(readme_path=readme_with_markers)
        renderer.inject("### Updated Section\n\n- Item A", dry_run=False)
        result = readme_with_markers.read_text(encoding="utf-8")
        assert "### Updated Section" in result

    def test_raises_file_not_found(self, tmp_path: Path) -> None:
        missing = tmp_path / "nonexistent.md"
        renderer = MarkdownRenderer(readme_path=missing)
        with pytest.raises(FileNotFoundError):
            renderer.inject("content")

    def test_custom_markers(self, tmp_path: Path) -> None:
        content = "# Title\n<!-- CUSTOM_START -->\nold\n<!-- CUSTOM_END -->\nfooter"
        readme = tmp_path / "README.md"
        readme.write_text(content, encoding="utf-8")

        renderer = MarkdownRenderer(
            readme_path=readme,
            start_marker="<!-- CUSTOM_START -->",
            end_marker="<!-- CUSTOM_END -->",
        )
        result = renderer.inject("new content", dry_run=True)
        assert "new content" in result
        assert "old" not in result

    def test_preserves_content_outside_markers(self, readme_with_markers: Path) -> None:
        renderer = MarkdownRenderer(readme_path=readme_with_markers)
        result = renderer.inject("New section content", dry_run=True)
        assert "Some intro text" in result
        assert "Footer text" in result

    def test_sanitizes_null_bytes(self, readme_with_markers: Path) -> None:
        renderer = MarkdownRenderer(readme_path=readme_with_markers)
        malicious = "Repo name\x00injected"
        result = renderer.inject(malicious, dry_run=True)
        assert "\x00" not in result


@pytest.mark.unit
class TestJSONRenderer:
    def test_writes_json_file(self, tmp_path: Path) -> None:
        output_path = tmp_path / "data.json"
        renderer = JSONRenderer(output_path=output_path)
        data = {"github": "### Section", "count": 5}
        renderer.render(data, dry_run=False)

        assert output_path.exists()
        loaded = json.loads(output_path.read_text(encoding="utf-8"))
        assert loaded["github"] == "### Section"

    def test_dry_run_does_not_write(self, tmp_path: Path) -> None:
        output_path = tmp_path / "data.json"
        renderer = JSONRenderer(output_path=output_path)
        renderer.render({"test": "value"}, dry_run=True)
        assert not output_path.exists()

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        output_path = tmp_path / "deep" / "nested" / "data.json"
        renderer = JSONRenderer(output_path=output_path)
        renderer.render({}, dry_run=False)
        assert output_path.exists()

    def test_handles_datetime_serialization(self, tmp_path: Path) -> None:
        from datetime import datetime

        output_path = tmp_path / "data.json"
        renderer = JSONRenderer(output_path=output_path)
        data = {"updated": datetime(2026, 7, 14)}
        result = renderer.render(data, dry_run=True)
        assert "2026-07-14" in result

"""Unit tests for shared validation utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from gps.utils.validators import (
    safe_readme_path,
    sanitize_markdown_string,
    validate_github_username,
    validate_readme_markers,
)


@pytest.mark.unit
class TestValidateReadmeMarkers:
    def test_both_markers_present(self) -> None:
        content = "# Header\n<!-- REPOS_START -->\nold\n<!-- REPOS_END -->\nfooter"
        assert (
            validate_readme_markers(content, "<!-- REPOS_START -->", "<!-- REPOS_END -->") is True
        )

    def test_start_marker_missing(self) -> None:
        content = "# Header\n<!-- REPOS_END -->\nfooter"
        assert (
            validate_readme_markers(content, "<!-- REPOS_START -->", "<!-- REPOS_END -->") is False
        )

    def test_end_marker_missing(self) -> None:
        content = "# Header\n<!-- REPOS_START -->\nfooter"
        assert (
            validate_readme_markers(content, "<!-- REPOS_START -->", "<!-- REPOS_END -->") is False
        )

    def test_markers_in_wrong_order(self) -> None:
        content = "<!-- REPOS_END -->\n<!-- REPOS_START -->"
        assert (
            validate_readme_markers(content, "<!-- REPOS_START -->", "<!-- REPOS_END -->") is False
        )

    def test_empty_content(self) -> None:
        assert validate_readme_markers("", "<!-- START -->", "<!-- END -->") is False


@pytest.mark.unit
class TestSanitizeMarkdownString:
    def test_removes_null_bytes(self) -> None:
        result = sanitize_markdown_string("hello\x00world")
        assert "\x00" not in result
        assert "helloworld" in result

    def test_strips_whitespace(self) -> None:
        result = sanitize_markdown_string("  content  \n")
        assert result == "content"

    def test_collapses_excessive_newlines(self) -> None:
        result = sanitize_markdown_string("line1\n\n\n\nline2")
        assert "\n\n\n" not in result

    def test_empty_string_returns_empty(self) -> None:
        assert sanitize_markdown_string("") == ""

    def test_preserves_valid_markdown(self) -> None:
        content = "### Title\n\n- Item 1\n- Item 2\n"
        result = sanitize_markdown_string(content)
        assert "### Title" in result
        assert "- Item 1" in result


@pytest.mark.unit
class TestValidateGitHubUsername:
    def test_valid_usernames(self) -> None:
        valid = ["adithshajee", "user123", "my-name", "A", "ab"]
        for u in valid:
            assert validate_github_username(u) is True, f"Expected {u!r} to be valid"

    def test_invalid_usernames(self) -> None:
        invalid = ["", "-start-with-dash", "end-with-dash-", "with space", "a" * 40]
        for u in invalid:
            assert validate_github_username(u) is False, f"Expected {u!r} to be invalid"

    def test_hyphen_allowed_in_middle(self) -> None:
        assert validate_github_username("my-github-user") is True

    def test_max_length_39(self) -> None:
        assert validate_github_username("a" * 39) is True
        assert validate_github_username("a" * 40) is False


@pytest.mark.unit
class TestSafeReadmePath:
    def test_valid_relative_path(self, tmp_path: Path) -> None:
        """Valid paths within repo root should resolve correctly."""
        (tmp_path / "profile").mkdir()
        (tmp_path / "profile" / "README.md").touch()
        result = safe_readme_path(Path("profile/README.md"), repo_root=tmp_path)
        assert result.exists()

    def test_path_traversal_raises(self, tmp_path: Path) -> None:
        """Paths escaping root should raise ValueError."""
        with pytest.raises(ValueError, match="Path traversal"):
            safe_readme_path(Path("../../etc/passwd"), repo_root=tmp_path)

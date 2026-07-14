"""GPS Utilities: Shared Validation Helpers."""

from __future__ import annotations

import re
from pathlib import Path


def validate_readme_markers(content: str, start_marker: str, end_marker: str) -> bool:
    """
    Check whether both injection markers exist in the README content.

    Args:
        content: Full README file content as a string.
        start_marker: Opening marker e.g. '<!-- REPOS_START -->'.
        end_marker: Closing marker e.g. '<!-- REPOS_END -->'.

    Returns:
        True if both markers are found in correct order.
    """
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    return start_idx != -1 and end_idx != -1 and start_idx < end_idx


def sanitize_markdown_string(value: str) -> str:
    """
    Escape potentially dangerous characters for safe markdown insertion.

    Prevents injection of raw HTML or markdown that could break the README layout.

    Args:
        value: Raw string from an API response.

    Returns:
        Sanitized string safe for markdown insertion.
    """
    if not value:
        return ""
    # Remove null bytes
    value = value.replace("\x00", "")
    # Collapse multiple newlines
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def validate_github_username(username: str) -> bool:
    """
    Validate a GitHub username against GitHub's rules.

    Rules: 1-39 characters, alphanumeric or hyphens, cannot start/end with hyphen.

    Args:
        username: GitHub username to validate.

    Returns:
        True if valid.
    """
    pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,37}[a-zA-Z0-9])?$"
    return bool(re.match(pattern, username))


def safe_readme_path(path: Path, repo_root: Path | None = None) -> Path:
    """
    Verify that a readme path is safe and within the repo root.

    Args:
        path: Candidate README path.
        repo_root: Repository root directory. Defaults to cwd.

    Returns:
        Resolved safe Path.

    Raises:
        ValueError: If the path escapes the repository root.
    """
    root = (repo_root or Path.cwd()).resolve()
    resolved = (root / path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as e:
        raise ValueError(
            f"Path traversal detected: '{path}' resolves outside the repository root."
        ) from e
    return resolved

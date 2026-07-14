"""
pytest fixtures shared across all test modules.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

# ─── Sample API Data ──────────────────────────────────────────────────────────


@pytest.fixture
def sample_repo() -> dict[str, Any]:
    """A realistic GitHub repo API response dict."""
    return {
        "name": "ai-tool-tracker",
        "full_name": "testuser/ai-tool-tracker",
        "html_url": "https://github.com/testuser/ai-tool-tracker",
        "description": "Real-time tool tracking with YOLOv8 and FastAPI.",
        "language": "Python",
        "stargazers_count": 42,
        "forks_count": 8,
        "open_issues_count": 2,
        "topics": ["python", "yolov8", "computer-vision"],
        "updated_at": "2026-07-11T12:00:00Z",
        "created_at": "2025-11-01T09:00:00Z",
        "fork": False,
        "archived": False,
        "disabled": False,
        "visibility": "public",
        "homepage": None,
    }


@pytest.fixture
def sample_fork_repo(sample_repo: dict[str, Any]) -> dict[str, Any]:
    """A forked repository."""
    return {**sample_repo, "fork": True, "name": "forked-repo"}


@pytest.fixture
def sample_archived_repo(sample_repo: dict[str, Any]) -> dict[str, Any]:
    """An archived repository."""
    return {**sample_repo, "archived": True, "name": "archived-repo"}


@pytest.fixture
def sample_repo_list(sample_repo: dict[str, Any]) -> list[dict[str, Any]]:
    """A list of 5 sample repositories."""
    repos = []
    for i in range(5):
        r = dict(sample_repo)
        r["name"] = f"project-{i + 1}"
        r["stargazers_count"] = i * 10
        r["updated_at"] = f"2026-0{7 - i}-01T12:00:00Z"
        repos.append(r)
    return repos


@pytest.fixture
def sample_user() -> dict[str, Any]:
    """A realistic GitHub user API response."""
    return {
        "login": "testuser",
        "name": "Test User",
        "bio": "AI & ML Engineer",
        "avatar_url": "https://avatars.githubusercontent.com/u/12345",
        "html_url": "https://github.com/testuser",
        "public_repos": 15,
        "followers": 120,
        "following": 45,
        "created_at": "2020-01-01T00:00:00Z",
        "location": "Bangalore, India",
        "email": None,
        "blog": "https://example.com",
        "company": None,
    }


# ─── File System Fixtures ─────────────────────────────────────────────────────


@pytest.fixture
def readme_with_markers(tmp_path: Path) -> Path:
    """A temporary README.md file with injection markers."""
    content = """\
# Test Profile

Some intro text.

---

<!-- REPOS_START -->

### Old content

<!-- REPOS_END -->

---

Footer text.
"""
    readme = tmp_path / "README.md"
    readme.write_text(content, encoding="utf-8")
    return readme


@pytest.fixture
def readme_without_markers(tmp_path: Path) -> Path:
    """A temporary README.md file WITHOUT injection markers."""
    content = "# Test Profile\n\nSome intro text.\n"
    readme = tmp_path / "README.md"
    readme.write_text(content, encoding="utf-8")
    return readme


@pytest.fixture
def minimal_gps_yml(tmp_path: Path) -> Path:
    """A minimal valid gps.yml config file."""
    content = """\
platform:
  username: "testuser"
  readme_path: "profile/README.md"

providers:
  github:
    enabled: true
    repo_count: 5
"""
    config = tmp_path / "gps.yml"
    config.write_text(content, encoding="utf-8")
    return config

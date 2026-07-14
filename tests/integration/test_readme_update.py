"""
Integration test: Full README update pipeline.

Tests the complete flow from provider mock → render → README update.
Uses temporary directories — no live API calls.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from gps.config import GPSSettings
from gps.engine import GPSEngine


@pytest.mark.integration
class TestFullReadmePipeline:
    @pytest.fixture(autouse=True)
    def setup_cwd(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)

    def _make_settings(self, readme_path: Path) -> GPSSettings:
        """Create test settings pointing to a temp README."""
        settings = GPSSettings()
        settings.username = "testuser"
        settings.readme_path = Path(readme_path.name) if readme_path.is_absolute() else readme_path
        settings.providers.github.enabled = True
        settings.providers.github.repo_count = 3
        settings.providers.huggingface.enabled = False
        settings.providers.kaggle.enabled = False
        return settings

    def test_pipeline_updates_readme_with_repos(self, readme_with_markers: Path) -> None:
        settings = self._make_settings(readme_with_markers)
        engine = GPSEngine(settings)

        mock_repos: list[dict[str, Any]] = [
            {
                "name": f"repo-{i}",
                "full_name": f"testuser/repo-{i}",
                "html_url": f"https://github.com/testuser/repo-{i}",
                "description": f"Description for repo {i}",
                "language": "Python",
                "stargazers_count": i * 5,
                "forks_count": i,
                "open_issues_count": 0,
                "topics": [],
                "updated_at": f"2026-07-{10 + i:02d}T12:00:00Z",
                "created_at": "2025-01-01T00:00:00Z",
                "fork": False,
                "archived": False,
                "disabled": False,
                "visibility": "public",
                "homepage": None,
            }
            for i in range(1, 4)
        ]
        mock_user = {
            "login": "testuser",
            "name": "Test User",
            "bio": "Engineer",
            "avatar_url": "https://avatars.test/u/1",
            "html_url": "https://github.com/testuser",
            "public_repos": 10,
            "followers": 50,
            "following": 20,
            "created_at": "2020-01-01T00:00:00Z",
        }

        with (
            patch("gps.providers.github.client.GitHubClient.get_repos", return_value=mock_repos),
            patch("gps.providers.github.client.GitHubClient.get_user", return_value=mock_user),
            patch("gps.providers.github.client.GitHubClient.get_pinned_repos", return_value=[]),
        ):
            results = engine.run(dry_run=False)

        assert "github" in results
        content = readme_with_markers.read_text(encoding="utf-8")
        assert "repo-1" in content
        assert "repo-2" in content
        assert "<!-- REPOS_START -->" in content
        assert "<!-- REPOS_END -->" in content

    def test_pipeline_dry_run_does_not_modify_readme(self, readme_with_markers: Path) -> None:
        original = readme_with_markers.read_text(encoding="utf-8")
        settings = self._make_settings(readme_with_markers)
        engine = GPSEngine(settings)

        mock_repos = [
            {
                "name": "dry-run-repo",
                "full_name": "testuser/dry-run-repo",
                "html_url": "https://github.com/testuser/dry-run-repo",
                "description": "Dry run test repo",
                "language": "Python",
                "stargazers_count": 1,
                "forks_count": 0,
                "open_issues_count": 0,
                "topics": [],
                "updated_at": "2026-07-11T12:00:00Z",
                "created_at": "2025-01-01T00:00:00Z",
                "fork": False,
                "archived": False,
                "disabled": False,
                "visibility": "public",
                "homepage": None,
            }
        ]

        with (
            patch("gps.providers.github.client.GitHubClient.get_repos", return_value=mock_repos),
            patch(
                "gps.providers.github.client.GitHubClient.get_user",
                return_value={"login": "testuser"},
            ),
            patch("gps.providers.github.client.GitHubClient.get_pinned_repos", return_value=[]),
        ):
            engine.run(dry_run=True)

        assert readme_with_markers.read_text(encoding="utf-8") == original

    def test_pipeline_no_providers_enabled_returns_empty(self, readme_with_markers: Path) -> None:
        settings = self._make_settings(readme_with_markers)
        settings.providers.github.enabled = False
        engine = GPSEngine(settings)
        results = engine.run()
        assert results == {}

    def test_validate_passes_with_valid_config(self, readme_with_markers: Path) -> None:
        settings = self._make_settings(readme_with_markers)
        engine = GPSEngine(settings)
        assert engine.validate() is True

    def test_validate_fails_with_missing_username(self, readme_with_markers: Path) -> None:
        settings = self._make_settings(readme_with_markers)
        settings.username = ""
        engine = GPSEngine(settings)
        assert engine.validate() is False

    def test_validate_fails_with_missing_readme(self, tmp_path: Path) -> None:
        missing_readme = tmp_path / "missing" / "README.md"
        settings = self._make_settings(missing_readme)
        engine = GPSEngine(settings)
        assert engine.validate() is False

    def test_forks_are_excluded_by_default(self, readme_with_markers: Path) -> None:
        settings = self._make_settings(readme_with_markers)
        settings.providers.github.exclude_forks = True
        engine = GPSEngine(settings)

        repos = [
            {
                "name": "my-repo",
                "full_name": "testuser/my-repo",
                "html_url": "https://github.com/testuser/my-repo",
                "description": "Original",
                "language": "Python",
                "stargazers_count": 10,
                "forks_count": 0,
                "open_issues_count": 0,
                "topics": [],
                "updated_at": "2026-07-11T12:00:00Z",
                "created_at": "2025-01-01T00:00:00Z",
                "fork": False,
                "archived": False,
                "disabled": False,
                "visibility": "public",
                "homepage": None,
            },
            {
                "name": "forked-repo",
                "full_name": "testuser/forked-repo",
                "html_url": "https://github.com/testuser/forked-repo",
                "description": "Forked",
                "language": "Python",
                "stargazers_count": 5,
                "forks_count": 0,
                "open_issues_count": 0,
                "topics": [],
                "updated_at": "2026-07-10T12:00:00Z",
                "created_at": "2025-01-01T00:00:00Z",
                "fork": True,
                "archived": False,
                "disabled": False,
                "visibility": "public",
                "homepage": None,
            },
        ]
        mock_user = {"login": "testuser", "public_repos": 2, "followers": 0, "following": 0}

        with (
            patch("gps.providers.github.client.GitHubClient.get_repos", return_value=repos),
            patch("gps.providers.github.client.GitHubClient.get_user", return_value=mock_user),
            patch("gps.providers.github.client.GitHubClient.get_pinned_repos", return_value=[]),
        ):
            results = engine.run(dry_run=True)

        assert "forked-repo" not in results.get("github", "")
        assert "my-repo" in results.get("github", "")

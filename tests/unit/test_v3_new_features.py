"""Unit tests for the new GPS v3 features: storage, discovery, widgets, and AI agents."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from gps.verify.core import VerificationEngine

from gps.ai.agents import (
    CareerAgent,
    DocumentationAgent,
    PortfolioAgent,
    ProfileOptimizerAgent,
    ProjectRankingAgent,
    READMEAgent,
    ThemeAgent,
)
from gps.storage.manager import StorageManager
from gps.utils.discovery import DiscoveryEngine
from gps.widgets.registry import WidgetRegistry


@pytest.mark.unit
class TestStorageManager:
    def test_ensure_directories(self, tmp_path: Path) -> None:
        mgr = StorageManager(root_dir=tmp_path)
        mgr.ensure_directories()
        assert (tmp_path / "profile").exists()
        assert (tmp_path / "history").exists()

    def test_read_cache_missing_returns_empty(self, tmp_path: Path) -> None:
        mgr = StorageManager(root_dir=tmp_path)
        assert mgr.read_cache() == {}

    def test_write_and_read_cache(self, tmp_path: Path) -> None:
        mgr = StorageManager(root_dir=tmp_path)
        sample = {"test_key": "test_val"}
        mgr.write_cache(sample)
        assert mgr.read_cache() == sample

    def test_write_readme(self, tmp_path: Path) -> None:
        mgr = StorageManager(root_dir=tmp_path)
        content = "# My Profile"
        readme_rel = Path("profile/README.md")
        mgr.write_readme(content, readme_rel)
        assert (tmp_path / readme_rel).read_text(encoding="utf-8") == content


@pytest.mark.unit
class TestDiscoveryEngine:
    def test_auto_detect_calls_endpoints(self) -> None:
        mock_client = MagicMock()
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_client.get.return_value = mock_res

        discovery = DiscoveryEngine(http_client=mock_client)
        findings = discovery.auto_detect("mockuser")

        assert findings["github"]["enabled"] is True
        assert findings["huggingface"]["enabled"] is True
        assert findings["leetcode"]["enabled"] is True
        assert findings["pypi"]["enabled"] is True
        assert findings["npm"]["enabled"] is True
        assert mock_client.get.call_count == 4


@pytest.mark.unit
class TestWidgetsRegistry:
    def test_widget_catalog_and_rendering(self) -> None:
        registry = WidgetRegistry()
        widgets_list = registry.list_all()
        assert "github_stats" in widgets_list
        assert "snake" in widgets_list
        assert "blog" in widgets_list
        assert "roadmap" in widgets_list
        assert "tech_stack" in widgets_list
        assert "visitors" in widgets_list

        # Test instantiation & rendering
        stats = registry.get("github_stats", {"accent_color": "#ff0000"})
        assert stats is not None
        assert "github-readme-stats" in stats.render({"username": "testuser"})
        assert "📊" in stats.preview()

        snake = registry.get("snake")
        assert snake is not None
        assert "github-contribution-grid-snake" in snake.render({"username": "testuser"})
        assert "🐍" in snake.preview()

        blog = registry.get("blog")
        assert blog is not None
        data = {"blog": {"posts": [{"title": "Post 1", "link": "https://link", "published": "2026-07-15"}]}}
        assert "Post 1" in blog.render(data)
        assert "✍️" in blog.preview()

        roadmap = registry.get("roadmap", {"items": ["Testing"]})
        assert roadmap is not None
        assert "Testing" in roadmap.render({})
        assert "🗺️" in roadmap.preview()

        stack = registry.get("tech_stack", {"skills": ["Python"]})
        assert stack is not None
        assert "Python" in stack.render({})
        assert "🛠️" in stack.preview()

        visitors = registry.get("visitors")
        assert visitors is not None
        assert "komarev" in visitors.render({"username": "testuser"})
        assert "Visitor" in visitors.preview()


@pytest.mark.unit
class TestAIAgents:
    def test_portfolio_agent_detection(self) -> None:
        agent = PortfolioAgent()
        repos = [
            {"language": "Python", "topics": ["pytorch", "yolo"]},
            {"language": "Go", "topics": ["docker", "kubernetes"]}
        ]
        res = agent.analyze(repos)
        assert "AI" in res["role"] or "DevOps" in res["role"]
        assert "Python" in res["detected_technologies"]

    def test_readme_agent_narration(self) -> None:
        agent = READMEAgent()
        about = agent.generate_about_me("John", "DevOps Engineer", ["Docker", "AWS"])
        assert "John" in about
        assert "DevOps Engineer" in about
        assert "Docker" in about

    def test_theme_agent_recommendations(self) -> None:
        agent = ThemeAgent()
        assert agent.recommend("AI Engineer") == "ai_ml"
        assert agent.recommend("DevOps Architect") == "devops"
        assert agent.recommend("Web Developer") == "swe_general"

    def test_project_ranking_agent(self) -> None:
        agent = ProjectRankingAgent()
        repos = [
            {"name": "repo-a", "stargazers_count": 5, "forks_count": 1, "description": "Good"},
            {"name": "repo-b", "stargazers_count": 50, "forks_count": 5, "description": "Great"},
            {"name": "repo-c", "stargazers_count": 1, "forks_count": 0, "description": None, "fork": True}
        ]
        ranked = agent.rank_repos(repos)
        assert ranked[0]["name"] == "repo-b"
        assert ranked[1]["name"] == "repo-a"

    def test_career_agent_profiles(self) -> None:
        agent = CareerAgent()
        assert agent.configure_profile("devops")["theme"]["name"] == "devops"
        assert agent.configure_profile("ai_engineer")["theme"]["name"] == "ai_ml"
        assert agent.configure_profile("fullstack")["theme"]["name"] == "swe_general"

    def test_documentation_agent_advise(self) -> None:
        agent = DocumentationAgent()
        assert len(agent.advise("path")) > 0

    def test_profile_optimizer_gaps(self) -> None:
        agent = ProfileOptimizerAgent()
        gaps = agent.analyze_gaps(["Python"], ["Python", "Docker"])
        assert gaps == ["Docker"]


@pytest.mark.unit
class TestVerificationEngine:
    def test_run_doctor_missing_config(self, tmp_path: Path) -> None:
        engine = VerificationEngine(workspace_root=tmp_path)
        res = engine.run_doctor(tmp_path / "gps.yml")
        assert res["config_found"] is False
        assert len(res["errors"]) > 0

    def test_run_doctor_valid_config(self, tmp_path: Path) -> None:
        engine = VerificationEngine(workspace_root=tmp_path)
        config = tmp_path / "gps.yml"
        config.write_text(
            "platform:\n  username: 'test'\n  readme_path: 'profile/README.md'\n",
            encoding="utf-8"
        )
        readme = tmp_path / "profile/README.md"
        readme.parent.mkdir()
        readme.write_text("<!-- REPOS_START -->\n<!-- REPOS_END -->", encoding="utf-8")
        
        res = engine.run_doctor(config)
        assert res["config_found"] is True
        assert res["config_valid"] is True
        assert res["readme_found"] is True
        assert res["markers_valid"] is True

    def test_verify_all_passed(self, tmp_path: Path) -> None:
        engine = VerificationEngine(workspace_root=tmp_path)
        config = tmp_path / "gps.yml"
        config.write_text(
            "platform:\n  username: 'test'\n  readme_path: 'profile/README.md'\n",
            encoding="utf-8"
        )
        readme = tmp_path / "profile/README.md"
        readme.parent.mkdir()
        readme.write_text("<!-- REPOS_START -->\n<!-- REPOS_END -->", encoding="utf-8")
        
        res = engine.verify_all(config)
        assert res["status"] in ("PASSED", "WARNING")

    def test_verify_all_failed(self, tmp_path: Path) -> None:
        engine = VerificationEngine(workspace_root=tmp_path)
        res = engine.verify_all(tmp_path / "gps.yml")
        assert res["status"] == "FAILED"

    def test_git_and_internet_checks(self) -> None:
        engine = VerificationEngine()
        with patch("shutil.which", return_value="/usr/bin/git"):
            assert engine._check_git_available() is True
        
        with patch("shutil.which", return_value=None):
            assert engine._check_git_available() is False

        with patch("httpx.Client.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200)
            assert engine._check_internet_connectivity() is True
            
            mock_get.side_effect = Exception()
            assert engine._check_internet_connectivity() is False

    def test_run_doctor_outdated_python(self, tmp_path: Path) -> None:
        engine = VerificationEngine(workspace_root=tmp_path)
        with patch("sys.version_info", (3, 9)):
            res = engine.run_doctor()
            assert res["python_ok"] is False

    def test_run_doctor_missing_readme(self, tmp_path: Path) -> None:
        engine = VerificationEngine(workspace_root=tmp_path)
        config = tmp_path / "gps.yml"
        config.write_text(
            "platform:\n  username: 'test'\n  readme_path: 'profile/README.md'\n",
            encoding="utf-8"
        )
        res = engine.run_doctor(config)
        assert res["readme_found"] is False
        assert any("Profile README missing" in e for e in res["errors"])

    def test_run_doctor_missing_markers(self, tmp_path: Path) -> None:
        engine = VerificationEngine(workspace_root=tmp_path)
        config = tmp_path / "gps.yml"
        config.write_text(
            "platform:\n  username: 'test'\n  readme_path: 'profile/README.md'\n",
            encoding="utf-8"
        )
        readme = tmp_path / "profile/README.md"
        readme.parent.mkdir()
        readme.write_text("No markers here", encoding="utf-8")
        
        res = engine.run_doctor(config)
        assert res["markers_valid"] is False
        assert any("markers are missing" in e for e in res["errors"])


@pytest.mark.unit
class TestCLICommands:
    def test_cli_verify_passed(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            config = Path("gps.yml")
            config.write_text(
                "platform:\n  username: 'test'\n  readme_path: 'profile/README.md'\n",
                encoding="utf-8"
            )
            readme = Path("profile/README.md")
            readme.parent.mkdir()
            readme.write_text("<!-- REPOS_START -->\n<!-- REPOS_END -->", encoding="utf-8")
            
            from gps.cli import main
            result = runner.invoke(main, ["verify"])
            assert result.exit_code == 0
            assert "VERIFICATION SUCCESSFUL" in result.output

    def test_cli_verify_failed(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            from gps.cli import main
            result = runner.invoke(main, ["verify"])
            assert result.exit_code == 1
            assert "VERIFICATION FAILED" in result.output

    def test_cli_dashboard(self) -> None:
        runner = CliRunner()
        with patch("gps.dashboard.backend.server.launch_dashboard") as mock_launch:
            from gps.cli import main
            result = runner.invoke(main, ["dashboard"])
            assert result.exit_code == 0
            mock_launch.assert_called_once()

    def test_cli_plugins(self) -> None:
        runner = CliRunner()
        from gps.cli import main
        
        res = runner.invoke(main, ["plugin", "list"])
        assert res.exit_code == 0
        assert "No custom plugins" in res.output

        res = runner.invoke(main, ["plugin", "install", "myplugin"])
        assert res.exit_code == 0
        assert "myplugin" in res.output

        res = runner.invoke(main, ["plugin", "remove", "myplugin"])
        assert res.exit_code == 0
        assert "removed" in res.output

        res = runner.invoke(main, ["plugin", "update", "myplugin"])
        assert res.exit_code == 0
        assert "up to date" in res.output


@pytest.mark.unit
class TestGitHubClientExtra:
    def test_github_client_methods(self) -> None:
        from gps.providers.github.client import GitHubClient

        with patch("gps.providers.github.client.HTTPClient") as mock_http_class:
            mock_http = MagicMock()
            mock_http_class.return_value = mock_http

            # Use a token so _has_token=True for pinned repos fetch
            client = GitHubClient(token="ghp_test")  # nosec B106

            # get_user — returns raw dict from the API
            mock_http.get.return_value = {
                "login": "testuser",
                "name": "Test User",
                "bio": "Bio",
                "avatar_url": "https://avatar",
                "html_url": "https://github.com/testuser",
                "public_repos": 5,
                "followers": 10,
                "following": 3,
                "location": "Earth",
            }
            user_data = client.get_user("testuser")
            assert isinstance(user_data, dict)
            assert user_data["login"] == "testuser"

            # get_repos — returns list of raw dicts with pagination
            mock_http.get.return_value = [
                {
                    "name": "repo1",
                    "full_name": "testuser/repo1",
                    "html_url": "https://github.com/testuser/repo1",
                    "description": "A repo",
                    "stargazers_count": 1,
                    "forks_count": 0,
                    "language": "Python",
                    "topics": [],
                    "fork": False,
                    "archived": False,
                }
            ]
            repos = client.get_repos("testuser", per_page=1)
            assert len(repos) == 1
            assert repos[0]["name"] == "repo1"

            # get_pinned_repos — uses GraphQL POST and normalizes the response
            mock_http.post.return_value = {
                "data": {
                    "user": {
                        "pinnedItems": {
                            "nodes": [
                                {
                                    "name": "pinned1",
                                    "description": "Pinned",
                                    "url": "https://github.com/testuser/pinned1",
                                    "stargazerCount": 5,
                                    "forkCount": 1,
                                    "primaryLanguage": {"name": "Python"},
                                    "repositoryTopics": {"nodes": []},
                                    "updatedAt": "2024-01-01T00:00:00Z",
                                }
                            ]
                        }
                    }
                }
            }
            pinned = client.get_pinned_repos("testuser")
            assert len(pinned) == 1
            assert pinned[0]["name"] == "pinned1"
            assert pinned[0]["html_url"] == "https://github.com/testuser/pinned1"
            assert pinned[0]["language"] == "Python"


@pytest.mark.unit
class TestKaggleClientExtra:
    def test_kaggle_client_import_error(self) -> None:
        """KaggleClient must raise ImportError when the kaggle package is absent."""
        import sys
        # Temporarily hide the kaggle package from imports inside the client module
        with patch.dict(sys.modules, {"kaggle": None, "kaggle.api": None,
                                       "kaggle.api.kaggle_api_extended": None}):
            # Re-import so that the mocked sys.modules takes effect
            import importlib
            import gps.providers.kaggle.client as kc_mod
            importlib.reload(kc_mod)
            with pytest.raises(ImportError):
                kc_mod.KaggleClient()

    def test_kaggle_client_success(self) -> None:
        """KaggleClient wraps Kaggle API methods correctly."""
        mock_api_instance = MagicMock()

        mock_comp = MagicMock()
        mock_comp.ref = "comp1"
        mock_comp.title = "Competition 1"
        mock_comp.description = "Desc"
        mock_comp.url = "https://comp"
        mock_comp.category = "Cat"
        mock_comp.reward = "Prize"
        mock_comp.deadline = "2026-07-15"
        mock_comp.teamCount = 5
        mock_api_instance.competitions_list.return_value = [mock_comp]

        mock_kernel = MagicMock()
        mock_kernel.title = "Kernel 1"
        mock_kernel.ref = "user/kernel1"
        mock_kernel.totalVotes = 10
        mock_kernel.language = "python"
        mock_api_instance.kernels_list.return_value = [mock_kernel]

        mock_dataset = MagicMock()
        mock_dataset.title = "Dataset 1"
        mock_dataset.ref = "user/dataset1"
        mock_dataset.downloadCount = 100
        mock_dataset.voteCount = 20
        mock_dataset.usabilityRating = 9.5
        mock_api_instance.dataset_list.return_value = [mock_dataset]

        mock_api_class = MagicMock(return_value=mock_api_instance)
        mock_kaggle_module = MagicMock()
        mock_kaggle_module.KaggleApiExtended = mock_api_class

        import sys
        fake_module = MagicMock()
        fake_module.KaggleApiExtended = mock_api_class

        with patch.dict(sys.modules, {
            "kaggle": MagicMock(),
            "kaggle.api": MagicMock(),
            "kaggle.api.kaggle_api_extended": fake_module,
        }):
            import importlib
            import gps.providers.kaggle.client as kc_mod
            importlib.reload(kc_mod)

            client = kc_mod.KaggleClient(username="kuser", key="kkey")

            comps = client.get_competitions("kuser")
            assert len(comps) == 1
            assert comps[0]["title"] == "Competition 1"

            notebooks = client.get_notebooks("kuser")
            assert len(notebooks) == 1
            assert notebooks[0]["title"] == "Kernel 1"

            datasets = client.get_datasets("kuser")
            assert len(datasets) == 1
            assert datasets[0]["title"] == "Dataset 1"

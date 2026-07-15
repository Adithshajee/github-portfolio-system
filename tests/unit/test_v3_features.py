"""Unit tests for GPS v3.0.0 features (LeetCode, Blog, and Theme Engine)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from gps.cli import main
from gps.providers.blog import BlogData, BlogPost, BlogProvider
from gps.providers.leetcode import LeetCodeData, LeetCodeProvider
from gps.themes.engine import ThemeEngine


@pytest.mark.unit
class TestLeetCodeProvider:
    def test_provider_metadata(self) -> None:
        provider = LeetCodeProvider(username="test_user")
        assert provider.name == "leetcode"
        assert provider.display_name == "LeetCode"

    def test_transform_success(self) -> None:
        provider = LeetCodeProvider(username="test_user")
        raw = {
            "status": "success",
            "totalSolved": 120,
            "easySolved": 50,
            "mediumSolved": 50,
            "hardSolved": 20,
            "acceptanceRate": 60.5,
            "ranking": 45000,
        }
        data = provider.transform(raw)
        assert isinstance(data, LeetCodeData)
        assert data.total_solved == 120
        assert data.ranking == 45000
        assert data.easy_solved == 50

    def test_transform_failure(self) -> None:
        provider = LeetCodeProvider(username="test_user")
        raw = {"status": "error", "message": "not found"}
        data = provider.transform(raw)
        assert data.total_solved == 0

    def test_validate(self) -> None:
        provider = LeetCodeProvider(username="test_user")
        data = LeetCodeData(username="test_user", total_solved=10)
        assert provider.validate(data) is True

        empty = LeetCodeData(username="test_user", total_solved=0)
        assert provider.validate(empty) is False

    def test_render(self) -> None:
        provider = LeetCodeProvider(username="test_user")
        data = LeetCodeData(
            username="test_user",
            total_solved=100,
            easy_solved=40,
            medium_solved=40,
            hard_solved=20,
            acceptance_rate=55.0,
            ranking=12345,
        )
        rendered = provider.render(data)
        assert "LeetCode" in rendered
        assert "12,345" in rendered
        assert "100" in rendered


@pytest.mark.unit
class TestBlogProvider:
    def test_provider_metadata(self) -> None:
        provider = BlogProvider(feed_url="https://test.com/rss")
        assert provider.name == "blog"
        assert provider.display_name == "Blog Feed"

    def test_transform_success(self) -> None:
        provider = BlogProvider(feed_url="https://test.com/rss")
        raw_xml = """<rss version="2.0">
  <channel>
    <title>My Tech Blog</title>
    <link>https://test.com</link>
    <item>
      <title>Building GPS v3</title>
      <link>https://test.com/post-1</link>
      <pubDate>Mon, 14 Jul 2026 12:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>"""
        data = provider.transform(raw_xml)
        assert isinstance(data, BlogData)
        assert data.title == "My Tech Blog"
        assert len(data.posts) == 1
        assert data.posts[0].title == "Building GPS v3"
        assert data.posts[0].pub_date == "14 Jul 2026"

    def test_transform_invalid_xml(self) -> None:
        provider = BlogProvider(feed_url="https://test.com/rss")
        data = provider.transform("invalid xml content")
        assert len(data.posts) == 0

    def test_validate(self) -> None:
        provider = BlogProvider(feed_url="https://test.com/rss")
        assert provider.validate(BlogData(feed_url="https://t.co")) is False

    def test_render(self) -> None:
        provider = BlogProvider(feed_url="https://test.com/rss")
        data = BlogData(
            feed_url="https://test.com/rss",
            title="Tech Blog",
            posts=[BlogPost(title="P1", link="https://p1", pub_date="Jan 1")],
        )
        rendered = provider.render(data)
        assert "Tech Blog" in rendered
        assert "P1" in rendered


@pytest.mark.unit
class TestThemeEngine:
    def test_theme_engine_fallback(self) -> None:
        engine = ThemeEngine(theme_name="invalid_theme")
        # Try rendering github section
        rendered = engine.render_template("github.md", {})
        assert rendered == ""

    def test_theme_engine_render_built_in(self) -> None:
        engine = ThemeEngine(theme_name="swe_general")

        class MockData:
            repos = [  # noqa: RUF012
                MagicMock(
                    name="repo1",
                    html_url="https://github.com",
                    display_description="Desc",
                    stargazers_count=10,
                    forks_count=2,
                    updated_date="2026-07-14",
                )
            ]

        rendered = engine.render_template("github.md", {"data": MockData()})
        assert "Active Projects" in rendered
        assert "repo1" in rendered


@pytest.mark.unit
class TestCLIInit:
    def test_cli_init_command_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["init", "--help"])
        assert result.exit_code == 0
        assert "Initialize a new GPS configuration file" in result.output

    def test_cli_init_non_interactive_success(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                main,
                [
                    "init",
                    "--non-interactive",
                    "-u",
                    "testuser",
                    "-t",
                    "swe_general",
                    "--hf-user",
                    "hfuser",
                    "--force",
                ],
            )
            assert result.exit_code == 0
            assert "GPS configuration successfully initialized" in result.output
            assert Path("gps.yml").exists()
            assert Path("profile/README.md").exists()

    def test_cli_init_interactive(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                main,
                ["init"],
                input="testuser\ny\nhfuser\nn\ny\nleetcodeuser\nn\n",
            )
            assert result.exit_code == 0
            assert "GPS configuration successfully initialized" in result.output
            assert Path("gps.yml").exists()


@pytest.mark.unit
class TestPluginLoaderAndEngine:
    def test_discover_plugins_local(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # Create mock local plugin folder
        local_dir = tmp_path / ".github/gps/plugins"
        local_dir.mkdir(parents=True)
        plugin_file = local_dir / "my_mock_plugin.py"
        plugin_file.write_text("print('Mock plugin loaded!')", encoding="utf-8")

        # Change dir so loader sees the local folder
        monkeypatch.chdir(tmp_path)

        from gps.plugins.loader import discover_plugins

        mock_engine = MagicMock()
        discover_plugins(mock_engine)

    @patch("gps.providers.kaggle.provider.KaggleClient")
    def test_engine_build_providers_all(self, mock_kaggle: MagicMock) -> None:
        from gps.config import GPSSettings
        from gps.engine import GPSEngine

        settings = GPSSettings.model_validate(
            {
                "username": "testuser",
                "providers": {
                    "github": {"enabled": True},
                    "huggingface": {"enabled": True, "username": "hfuser"},
                    "kaggle": {"enabled": True, "username": "kaggleuser"},
                    "leetcode": {"enabled": True, "username": "lcuser"},
                    "blog": {"enabled": True, "feed_url": "https://test.com/feed"},
                },
            }
        )
        engine = GPSEngine(settings)
        providers = engine._build_providers()
        assert len(providers) == 5

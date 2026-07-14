"""Unit tests for the GPS CLI commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from gps.cli import main


@pytest.mark.unit
class TestCLIRun:
    def test_run_dry_run_succeeds(self, tmp_path: Path, readme_with_markers: Path) -> None:
        runner = CliRunner()
        with patch("gps.cli._load_engine") as mock_engine_loader:
            mock_engine = MagicMock()
            mock_engine.run.return_value = {"github": "### Section"}
            mock_engine_loader.return_value = mock_engine

            result = runner.invoke(main, ["run", "--dry-run"])
            assert result.exit_code == 0
            mock_engine.run.assert_called_once_with(dry_run=True, provider_filter=None)

    def test_run_with_provider_filter(self) -> None:
        runner = CliRunner()
        with patch("gps.cli._load_engine") as mock_engine_loader:
            mock_engine = MagicMock()
            mock_engine.run.return_value = {"github": "content"}
            mock_engine_loader.return_value = mock_engine

            result = runner.invoke(main, ["run", "--provider", "github", "--dry-run"])
            assert result.exit_code == 0
            mock_engine.run.assert_called_once_with(dry_run=True, provider_filter="github")

    def test_run_returns_exit_1_on_no_results(self) -> None:
        runner = CliRunner()
        with patch("gps.cli._load_engine") as mock_engine_loader:
            mock_engine = MagicMock()
            mock_engine.run.return_value = {}  # No results
            mock_engine_loader.return_value = mock_engine

            result = runner.invoke(main, ["run", "--dry-run"])
            assert result.exit_code == 1

    def test_run_returns_exit_1_on_file_not_found(self) -> None:
        runner = CliRunner()
        with patch("gps.cli._load_engine") as mock_engine_loader:
            mock_engine = MagicMock()
            mock_engine.run.side_effect = FileNotFoundError("README.md not found")
            mock_engine_loader.return_value = mock_engine

            result = runner.invoke(main, ["run"])
            assert result.exit_code == 1
            assert "Error" in result.output


@pytest.mark.unit
class TestCLIValidate:
    def test_validate_exits_0_on_success(self) -> None:
        runner = CliRunner()
        with patch("gps.cli._load_engine") as mock_engine_loader:
            mock_engine = MagicMock()
            mock_engine.validate.return_value = True
            mock_engine_loader.return_value = mock_engine

            result = runner.invoke(main, ["validate"])
            assert result.exit_code == 0

    def test_validate_exits_1_on_failure(self) -> None:
        runner = CliRunner()
        with patch("gps.cli._load_engine") as mock_engine_loader:
            mock_engine = MagicMock()
            mock_engine.validate.return_value = False
            mock_engine_loader.return_value = mock_engine

            result = runner.invoke(main, ["validate"])
            assert result.exit_code == 1


@pytest.mark.unit
class TestCLIVersion:
    def test_version_flag(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "3.0.0" in result.output


@pytest.mark.unit
class TestCLIStatus:
    def test_status_shows_provider_table(self) -> None:
        runner = CliRunner()
        with patch("gps.cli.load_config") as mock_load_config:
            mock_settings = MagicMock()
            mock_settings.providers.github.enabled = True
            mock_settings.providers.huggingface.enabled = False
            mock_settings.providers.kaggle.enabled = False
            mock_settings.providers.linkedin.enabled = False
            mock_settings.github_token = "ghp_test"
            mock_settings.hf_token = ""
            mock_settings.kaggle_key = ""
            mock_settings.username = "testuser"
            mock_settings.providers.github.repo_count = 5
            mock_settings.providers.huggingface.username = ""
            mock_settings.providers.kaggle.username = ""
            mock_settings.readme_path = "profile/README.md"
            mock_settings.logging.level = "INFO"
            mock_settings.logging.json_format = False
            mock_load_config.return_value = mock_settings

            result = runner.invoke(main, ["status"])
            assert result.exit_code == 0
            assert "GitHub" in result.output

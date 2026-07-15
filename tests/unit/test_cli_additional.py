"""Additional unit tests for CLI coverage including gps doctor and interactive init validation."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from gps.cli import main, print_diagnostic_error


@pytest.mark.unit
class TestCLIDoctor:
    def test_doctor_with_missing_config(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # No gps.yml exists
            result = runner.invoke(main, ["doctor"])
            assert result.exit_code == 1
            assert "Configuration file missing" in result.output

    def test_doctor_with_valid_config_and_readme(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Scaffold valid files
            Path("profile").mkdir()
            readme = Path("profile/README.md")
            readme.write_text("# Test\n<!-- REPOS_START -->\n<!-- REPOS_END -->", encoding="utf-8")

            config = Path("gps.yml")
            config.write_text(
                "platform:\n"
                "  username: 'testuser'\n"
                "  readme_path: 'profile/README.md'\n"
                "theme:\n"
                "  name: 'swe_general'\n"
                "providers:\n"
                "  github:\n"
                "    enabled: true\n",
                encoding="utf-8"
            )

            # Setup environment variable
            os.environ["GH_PAT"] = "ghp_mock_token"

            result = runner.invoke(main, ["doctor"])
            assert result.exit_code == 0
            assert "README markers: Present & valid" in result.output

            # Cleanup env variable
            del os.environ["GH_PAT"]


@pytest.mark.unit
class TestCLIInitValidation:
    def test_init_interactive_with_validation_loops(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Inputs:
            # - GitHub user: 'invalid-user-' (should fail format), then 'validuser'
            # - HF prompt: 'y', HF user: 'hf-user'
            # - Kaggle prompt: 'y', Kaggle user: 'kaggle-user'
            # - LeetCode prompt: 'y', LeetCode user: 'leetcode-user'
            # - Blog prompt: 'y', Blog feed: 'invalid-url', then 'https://myblog.com/feed'
            inputs = (
                "invalid-user-\n"
                "validuser\n"
                "y\n"
                "hf-user\n"
                "y\n"
                "kaggle-user\n"
                "y\n"
                "leetcode-user\n"
                "y\n"
                "invalid-url\n"
                "https://myblog.com/feed\n"
            )
            result = runner.invoke(
                main,
                ["init"],
                input=inputs,
            )
            assert result.exit_code == 0
            assert "Invalid GitHub username format" in result.output
            assert "Invalid Feed URL" in result.output
            assert "GPS configuration successfully initialized" in result.output
            assert Path("gps.yml").exists()
            assert Path("profile/README.md").exists()


@pytest.mark.unit
class TestCLIErrorHandling:
    def test_print_diagnostic_error_output(self) -> None:
        # Direct call to helper function to assert Rich prints it without errors
        print_diagnostic_error(
            problem="Mock problem description",
            why="Mock explanation for error",
            fix="Steps to resolve",
            next_cmd="gps doctor"
        )

    def test_run_file_not_found_handling(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Running with non-existent config should raise FileNotFoundError
            # internally and format it
            result = runner.invoke(main, ["run", "--config", "nonexistent.yml"])
            assert result.exit_code == 1
            assert "Problem: Configuration or target files not found" in result.output

    def test_validate_file_not_found_handling(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["validate", "--config", "nonexistent.yml"])
            assert result.exit_code == 1
            assert "Problem: gps.yml configuration file not found" in result.output

    def test_status_error_handling(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # status with nonexistent config should format error
            result = runner.invoke(main, ["status", "--config", "nonexistent.yml"])
            assert result.exit_code == 1
            assert "Problem: Failed to display provider status" in result.output

    def test_export_error_handling(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["export", "--config", "nonexistent.yml"])
            assert result.exit_code == 1
            assert "Problem: Data export failed" in result.output

    def test_export_html_unsupported(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            config = Path("gps.yml")
            config.write_text(
                "platform:\n  username: 'test'\n  readme_path: 'profile/README.md'\n",
                encoding="utf-8"
            )
            Path("profile").mkdir()
            Path("profile/README.md").write_text("", encoding="utf-8")
            result = runner.invoke(main, ["export", "--format", "html"])
            assert result.exit_code == 1
            assert "HTML export is not yet fully implemented" in result.output

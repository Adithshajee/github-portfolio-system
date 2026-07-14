"""Unit tests for configuration loading and validation."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from gps.config import GPSSettings, load_config


@pytest.mark.unit
class TestLoadConfig:
    def test_loads_from_yaml_file(self, tmp_path: Path) -> None:
        config_file = tmp_path / "gps.yml"
        config_file.write_text(
            "platform:\n  username: testuser\n  readme_path: profile/README.md\n",
            encoding="utf-8",
        )
        settings = load_config(config_file)
        assert settings.username == "testuser"
        assert settings.readme_path.as_posix() == "profile/README.md"

    def test_returns_defaults_when_no_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When no gps.yml is found, return Pydantic defaults."""
        monkeypatch.chdir(tmp_path)
        settings = load_config()
        assert isinstance(settings, GPSSettings)
        assert settings.username == ""

    def test_raises_file_not_found_on_explicit_missing(self, tmp_path: Path) -> None:
        missing = tmp_path / "missing.yml"
        with pytest.raises(FileNotFoundError):
            load_config(missing)

    def test_env_var_overrides_yaml(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        config_file = tmp_path / "gps.yml"
        config_file.write_text("platform:\n  username: yaml_user\n", encoding="utf-8")
        monkeypatch.setenv("GPS_USERNAME", "env_user")
        settings = load_config(config_file)
        assert settings.username == "env_user"

    def test_github_token_from_env(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GH_PAT", "ghp_test_token_abc")
        settings = load_config()
        assert settings.github_token == "ghp_test_token_abc"

    def test_github_token_not_in_yaml(self, tmp_path: Path) -> None:
        """Tokens must not be readable from YAML — only env vars."""
        config_file = tmp_path / "gps.yml"
        # Writing a token in YAML should be ignored
        config_file.write_text(
            "platform:\n  username: user\n  github_token: secret123\n",
            encoding="utf-8",
        )
        settings = load_config(config_file)
        # The field alias is GH_PAT, not github_token in YAML
        assert settings.github_token == ""

    def test_provider_settings_loaded(self, tmp_path: Path) -> None:
        config_file = tmp_path / "gps.yml"
        content = yaml.dump(
            {
                "platform": {"username": "user"},
                "providers": {
                    "github": {"enabled": True, "repo_count": 10},
                    "huggingface": {"enabled": False},
                },
            }
        )
        config_file.write_text(content, encoding="utf-8")
        settings = load_config(config_file)
        assert settings.providers.github.repo_count == 10
        assert settings.providers.huggingface.enabled is False

    def test_readme_path_cannot_be_absolute(self, tmp_path: Path) -> None:
        config_file = tmp_path / "gps.yml"
        config_file.write_text(
            "platform:\n  username: user\n  readme_path: /etc/passwd\n",
            encoding="utf-8",
        )
        with pytest.raises(ValidationError):
            load_config(config_file)


@pytest.mark.unit
class TestHTTPSettings:
    def test_http_timeout_validation(self) -> None:
        from gps.config import HTTPSettings

        s = HTTPSettings(timeout=30)
        assert s.timeout == 30

    def test_http_timeout_must_be_positive(self) -> None:
        from pydantic import ValidationError

        from gps.config import HTTPSettings

        with pytest.raises(ValidationError):
            HTTPSettings(timeout=0)


@pytest.mark.unit
class TestGitHubProviderSettings:
    def test_defaults(self) -> None:
        from gps.config import GitHubProviderSettings

        s = GitHubProviderSettings()
        assert s.enabled is True
        assert s.repo_count == 5
        assert s.exclude_forks is True

    def test_repo_count_range(self) -> None:
        from pydantic import ValidationError

        from gps.config import GitHubProviderSettings

        with pytest.raises(ValidationError):
            GitHubProviderSettings(repo_count=0)
        with pytest.raises(ValidationError):
            GitHubProviderSettings(repo_count=101)

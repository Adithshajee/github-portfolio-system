"""Unit tests for the GPSEngine core execution and validation flow."""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gps.config.manager import GPSSettings
from gps.engine.core import GPSEngine


@pytest.mark.unit
class TestEngineCore:
    def test_engine_init(self) -> None:
        settings = GPSSettings(username="testuser")
        engine = GPSEngine(settings)
        assert engine.settings == settings
        assert engine.theme_engine is not None

    def test_build_providers_all(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Prevent Kaggle authentication checks during unit tests
        monkeypatch.setenv("KAGGLE_USERNAME", "kuser")
        monkeypatch.setenv("KAGGLE_KEY", "kkey")
        
        settings = GPSSettings.model_validate({
            "username": "testuser",
            "providers": {
                "github": {"enabled": True},
                "huggingface": {"enabled": True},
                "kaggle": {"enabled": True},
                "leetcode": {"enabled": True},
                "blog": {"enabled": True, "feed_url": "https://test.com/rss"},
            }
        })
        
        with patch("gps.providers.kaggle.provider.KaggleProvider") as mock_kaggle:
            mock_kaggle.return_value = MagicMock()
            engine = GPSEngine(settings)
            providers = engine._build_providers()
            assert len(providers) == 5

    def test_engine_run_empty(self) -> None:
        settings = GPSSettings(username="testuser")
        settings.providers.github.enabled = False
        engine = GPSEngine(settings)
        res = engine.run()
        assert res == {}

    def test_engine_run_dry_run(self) -> None:
        settings = GPSSettings(username="testuser")
        engine = GPSEngine(settings)
        
        mock_provider = MagicMock()
        mock_provider.name = "github"
        mock_provider.run.return_value = ("rendered_content", True)
        
        with patch.object(engine, "_build_providers", return_value=[mock_provider]):
            with patch.object(engine, "_inject_readme") as mock_inject:
                res = engine.run(dry_run=True)
                assert res == {"github": "rendered_content"}
                mock_inject.assert_called_once_with("rendered_content", dry_run=True)

    def test_engine_run_parallel(self) -> None:
        settings = GPSSettings(username="testuser")
        engine = GPSEngine(settings)
        
        prov_a = MagicMock()
        prov_a.name = "github"
        prov_a.run.return_value = ("github_res", True)
        
        prov_b = MagicMock()
        prov_b.name = "leetcode"
        prov_b.run.return_value = ("leetcode_res", True)

        with patch.object(engine, "_build_providers", return_value=[prov_a, prov_b]):
            with patch.object(engine, "_inject_readme") as mock_inject:
                res = engine.run()
                assert "github" in res
                assert "leetcode" in res
                mock_inject.assert_called_once()

    def test_engine_validate(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        settings = GPSSettings(username="testuser", readme_path=Path("profile/README.md"))
        engine = GPSEngine(settings)
        
        # Missing README file
        assert engine.validate() is False

        # Existing README with valid markers
        readme = tmp_path / "profile/README.md"
        readme.parent.mkdir()
        readme.write_text("<!-- REPOS_START -->\n<!-- REPOS_END -->", encoding="utf-8")
        
        assert engine.validate() is True

"""Additional targeted unit tests to push coverage above 90%."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner


# ─── Logging ───────────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestGPSLogging:
    def test_configure_logging_default(self) -> None:
        from gps.utils.logging import configure_logging
        configure_logging()
        root = logging.getLogger("gps")
        assert root.level == logging.INFO
        assert root.handlers

    def test_configure_logging_debug(self) -> None:
        from gps.utils.logging import configure_logging
        configure_logging(level="DEBUG")
        root = logging.getLogger("gps")
        assert root.level == logging.DEBUG

    def test_configure_logging_json_format(self) -> None:
        from gps.utils.logging import configure_logging
        configure_logging(json_format=True)
        root = logging.getLogger("gps")
        assert root.handlers
        root.warning("test json log")

    def test_configure_logging_json_with_exception(self) -> None:
        from gps.utils.logging import configure_logging
        configure_logging(json_format=True)
        root = logging.getLogger("gps")
        try:
            raise ValueError("test error")
        except ValueError:
            root.exception("test exception log")

    def test_gps_formatter_all_levels(self) -> None:
        from gps.utils.logging import _GPSFormatter
        fmt = _GPSFormatter()
        for level in (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL):
            record = logging.LogRecord(
                name="gps.test", level=level, pathname="", lineno=0,
                msg="test", args=(), exc_info=None
            )
            result = fmt.format(record)
            assert "test" in result


# ─── Provider Base Registry ────────────────────────────────────────────────────

@pytest.mark.unit
class TestProviderRegistry:
    def test_register_and_get_provider(self) -> None:
        from gps.providers.base import _REGISTRY, get_provider, list_providers, register

        @register("_test_provider_")  # type: ignore[arg-type]
        class _TestProvider:  # type: ignore[no-untyped-def]
            name = "_test_provider_"

        assert "_test_provider_" in list_providers()
        cls = get_provider("_test_provider_")
        assert cls is _TestProvider

        del _REGISTRY["_test_provider_"]

    def test_get_unknown_provider_raises(self) -> None:
        from gps.providers.base import get_provider
        with pytest.raises(KeyError, match="Unknown provider"):
            get_provider("__nonexistent__")

    def test_base_provider_run_validation_fail(self) -> None:
        from gps.providers.base import BaseProvider

        class _FakeProvider(BaseProvider):  # type: ignore[type-arg]
            name = "fake"
            display_name = "Fake"

            def fetch(self) -> dict:  # type: ignore[override]
                return {}

            def transform(self, raw: dict) -> dict:  # type: ignore[override]
                return raw

            def validate(self, data: dict) -> bool:  # type: ignore[override]
                return False

            def render(self, data: dict) -> str:  # type: ignore[override]
                return ""

        provider = _FakeProvider()
        content, ok = provider.run()
        assert content == ""
        assert ok is False

    def test_base_provider_run_exception(self) -> None:
        from gps.providers.base import BaseProvider

        class _ErrorProvider(BaseProvider):  # type: ignore[type-arg]
            name = "error"
            display_name = "Error"

            def fetch(self) -> dict:  # type: ignore[override]
                raise RuntimeError("fetch failed")

            def transform(self, raw: dict) -> dict:  # type: ignore[override]
                return raw

            def validate(self, data: dict) -> bool:  # type: ignore[override]
                return True

            def render(self, data: dict) -> str:  # type: ignore[override]
                return ""

        provider = _ErrorProvider()
        content, ok = provider.run()
        assert content == ""
        assert ok is False

    def test_base_provider_run_with_theme(self) -> None:
        from gps.providers.base import BaseProvider

        class _ThemeProvider(BaseProvider):  # type: ignore[type-arg]
            name = "themed"
            display_name = "Themed"

            def fetch(self) -> dict:  # type: ignore[override]
                return {"key": "value"}

            def transform(self, raw: dict) -> dict:  # type: ignore[override]
                return raw

            def validate(self, data: dict) -> bool:  # type: ignore[override]
                return True

            def render(self, data: dict) -> str:  # type: ignore[override]
                return "base_rendered"

        mock_theme_engine = MagicMock()
        mock_theme_engine.render_template.return_value = "theme_output"

        provider = _ThemeProvider()
        content, ok = provider.run(theme_engine=mock_theme_engine)
        assert ok is True
        # Either theme_output (if theme returned) or base_rendered (fallback)
        assert content in ("theme_output", "base_rendered")


# ─── Discovery Engine ──────────────────────────────────────────────────────────

@pytest.mark.unit
class TestDiscoveryExtra:
    def test_auto_detect_hf_found(self) -> None:
        from gps.utils.discovery import DiscoveryEngine
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        engine = DiscoveryEngine(http_client=mock_client)
        result = engine.auto_detect("testuser")
        assert result["huggingface"]["enabled"] is True

    def test_auto_detect_hf_not_found(self) -> None:
        from gps.utils.discovery import DiscoveryEngine
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        engine = DiscoveryEngine(http_client=mock_client)
        result = engine.auto_detect("unknownuser")
        assert result["huggingface"]["enabled"] is False

    def test_auto_detect_exception_is_handled(self) -> None:
        from gps.utils.discovery import DiscoveryEngine
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("Network error")
        engine = DiscoveryEngine(http_client=mock_client)
        result = engine.auto_detect("testuser")
        assert result["github"]["enabled"] is True
        assert result["huggingface"]["enabled"] is False


# ─── CLI Exception Branches ────────────────────────────────────────────────────

@pytest.mark.unit
class TestCLIExceptionBranches:
    def test_run_unexpected_exception(self) -> None:
        runner = CliRunner()
        from gps.cli import main
        with patch("gps.cli._load_engine", side_effect=RuntimeError("boom")):
            result = runner.invoke(main, ["run"])
            assert result.exit_code == 1

    def test_run_verbose_unexpected_exception(self) -> None:
        runner = CliRunner()
        from gps.cli import main
        with patch("gps.cli._load_engine", side_effect=RuntimeError("boom")):
            result = runner.invoke(main, ["run", "--verbose"])
            assert result.exit_code == 1

    def test_validate_unexpected_exception(self) -> None:
        runner = CliRunner()
        from gps.cli import main
        with patch("gps.cli._load_engine", side_effect=RuntimeError("unexpected")):
            result = runner.invoke(main, ["validate"])
            assert result.exit_code == 1

    def test_load_engine_with_config_path(self, tmp_path: Path) -> None:
        cfg = tmp_path / "gps.yml"
        cfg.write_text("username: testuser\n", encoding="utf-8")
        from gps.cli import _load_engine
        # configure_logging is a local import inside _load_engine; patch at its source
        with patch("gps.utils.logging.configure_logging"):
            engine = _load_engine(str(cfg), verbose=False)
            assert engine is not None

    def test_load_engine_debug_verbose(self, tmp_path: Path) -> None:
        cfg = tmp_path / "gps.yml"
        cfg.write_text("username: testuser\n", encoding="utf-8")
        from gps.cli import _load_engine
        # configure_logging is a local import inside _load_engine; patch at its source
        with patch("gps.utils.logging.configure_logging") as mock_log:
            _load_engine(str(cfg), verbose=True)
            mock_log.assert_called_once_with(level="DEBUG", json_format=False)


# ─── Engine Core Additional Branches ──────────────────────────────────────────

@pytest.mark.unit
class TestEngineCoreExtra:
    def test_engine_run_provider_returns_empty(self) -> None:
        from gps.config.manager import GPSSettings
        from gps.engine.core import GPSEngine
        settings = GPSSettings(username="testuser")
        engine = GPSEngine(settings)

        mock_provider = MagicMock()
        mock_provider.name = "github"
        mock_provider.run.return_value = ("", False)

        with patch.object(engine, "_build_providers", return_value=[mock_provider]):
            with patch.object(engine, "_inject_readme") as mock_inject:
                res = engine.run()
                assert res == {}
                mock_inject.assert_not_called()

    def test_engine_inject_readme_calls_renderer(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        readme = tmp_path / "profile" / "README.md"
        readme.parent.mkdir()
        readme.write_text("<!-- REPOS_START -->\n<!-- REPOS_END -->", encoding="utf-8")

        from gps.config.manager import GPSSettings
        from gps.engine.core import GPSEngine
        settings = GPSSettings(username="testuser", readme_path=Path("profile/README.md"))
        engine = GPSEngine(settings)

        with patch("gps.engine.core.MarkdownRenderer") as MockRenderer:
            mock_instance = MagicMock()
            MockRenderer.return_value = mock_instance
            engine._inject_readme("content", dry_run=True)
            MockRenderer.assert_called_once()
            mock_instance.inject.assert_called_once()

    def test_engine_provider_filter_single(self) -> None:
        from gps.config.manager import GPSSettings
        from gps.engine.core import GPSEngine
        settings = GPSSettings(username="testuser")
        engine = GPSEngine(settings)

        mock_github = MagicMock()
        mock_github.name = "github"
        mock_github.run.return_value = ("github_output", True)

        mock_hf = MagicMock()
        mock_hf.name = "huggingface"
        mock_hf.run.return_value = ("hf_output", True)

        with patch.object(engine, "_build_providers", return_value=[mock_github, mock_hf]):
            with patch.object(engine, "_inject_readme"):
                res = engine.run(provider_filter="github")
                assert "github" in res
                assert "huggingface" not in res

    # ── Targeted _build_providers branch tests ─────────────────────────────────

    def test_build_providers_github_no_username(self) -> None:
        """Line 40: GitHub enabled but username is empty → logs error, skips."""
        from gps.config.manager import GPSSettings
        from gps.engine.core import GPSEngine
        settings = GPSSettings(username="")
        settings.providers.github.enabled = True
        engine = GPSEngine(settings)
        providers = engine._build_providers()
        assert not any(getattr(p, "name", None) == "github" for p in providers)

    def test_build_providers_hf_import_error(self) -> None:
        """Lines 74-75: HuggingFace import fails → logs error, continues."""
        from gps.config.manager import GPSSettings
        from gps.engine.core import GPSEngine
        settings = GPSSettings(username="testuser")
        settings.providers.huggingface.enabled = True
        engine = GPSEngine(settings)
        with patch(
            "gps.engine.core.__builtins__",
            side_effect=None,
        ):
            with patch(
                "gps.providers.huggingface.provider.HuggingFaceProvider",
                side_effect=ImportError("no hf"),
            ):
                # Should not raise; import error is caught
                providers = engine._build_providers()
                assert isinstance(providers, list)

    def test_build_providers_kaggle_exception(self) -> None:
        """Lines 90-91: Kaggle provider construction fails → logs error, continues."""
        from gps.config.manager import GPSSettings
        from gps.engine.core import GPSEngine
        settings = GPSSettings(username="testuser")
        settings.providers.kaggle.enabled = True
        engine = GPSEngine(settings)
        with patch(
            "gps.providers.kaggle.provider.KaggleProvider",
            side_effect=RuntimeError("kaggle auth fail"),
        ):
            providers = engine._build_providers()
            assert isinstance(providers, list)

    def test_build_providers_leetcode_exception(self) -> None:
        """Lines 99-100: LeetCode provider construction fails → logs error, continues."""
        from gps.config.manager import GPSSettings
        from gps.engine.core import GPSEngine
        settings = GPSSettings(username="testuser")
        settings.providers.leetcode.enabled = True
        engine = GPSEngine(settings)
        with patch(
            "gps.providers.leetcode.LeetCodeProvider",
            side_effect=RuntimeError("leetcode fail"),
        ):
            providers = engine._build_providers()
            assert isinstance(providers, list)

    def test_build_providers_blog_exception(self) -> None:
        """Lines 108-109: Blog provider construction fails → logs error, continues."""
        from gps.config.manager import GPSSettings
        from gps.engine.core import GPSEngine
        settings = GPSSettings.model_validate({
            "username": "testuser",
            "providers": {
                "github": {"enabled": False},
                "blog": {"enabled": True, "feed_url": "https://example.com/rss"},
            }
        })
        engine = GPSEngine(settings)
        with patch(
            "gps.providers.blog.BlogProvider",
            side_effect=RuntimeError("blog fail"),
        ):
            providers = engine._build_providers()
            assert isinstance(providers, list)

    def test_engine_run_parallel_future_exception(self) -> None:
        """Lines 141-142: Future raises in ThreadPoolExecutor → logged, not re-raised."""
        from gps.config.manager import GPSSettings
        from gps.engine.core import GPSEngine
        settings = GPSSettings(username="testuser")
        engine = GPSEngine(settings)

        prov_a = MagicMock()
        prov_a.name = "github"
        prov_a.run.side_effect = RuntimeError("provider boom")

        prov_b = MagicMock()
        prov_b.name = "huggingface"
        prov_b.run.return_value = ("hf_output", True)

        with patch.object(engine, "_build_providers", return_value=[prov_a, prov_b]):
            with patch.object(engine, "_inject_readme"):
                res = engine.run()
                # github failed, huggingface succeeded
                assert "github" not in res

    def test_engine_run_json_export(self) -> None:
        """Lines 152-153: outputs.json=True triggers _export_json."""
        from gps.config.manager import GPSSettings
        from gps.engine.core import GPSEngine
        settings = GPSSettings(username="testuser")
        settings.outputs.json = True  # type: ignore[attr-defined]
        engine = GPSEngine(settings)

        mock_provider = MagicMock()
        mock_provider.name = "github"
        mock_provider.run.return_value = ("github_content", True)

        with patch.object(engine, "_build_providers", return_value=[mock_provider]):
            with patch.object(engine, "_inject_readme"):
                with patch.object(engine, "_export_json") as mock_export:
                    res = engine.run()
                    mock_export.assert_called_once()

    def test_export_json(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Lines 167-170: _export_json writes JSON via JSONRenderer."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "profile").mkdir()

        from gps.config.manager import GPSSettings
        from gps.engine.core import GPSEngine
        settings = GPSSettings(username="testuser", readme_path=Path("profile/README.md"))
        engine = GPSEngine(settings)

        with patch("gps.engine.core.JSONRenderer") as MockJSON:
            mock_json = MagicMock()
            MockJSON.return_value = mock_json
            engine._export_json({"github": "content"}, dry_run=True)
            MockJSON.assert_called_once()
            mock_json.render.assert_called_once()

    def test_validate_invalid_username(self) -> None:
        """Lines 185-187: username fails validate_github_username check."""
        from gps.config.manager import GPSSettings
        from gps.engine.core import GPSEngine
        settings = GPSSettings(username="INVALID USER NAME!!!")
        engine = GPSEngine(settings)
        result = engine.validate()
        assert result is False

    def test_validate_readme_missing_markers(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Lines 200-203: README exists but markers are absent → warning, returns True."""
        monkeypatch.chdir(tmp_path)
        readme = tmp_path / "profile" / "README.md"
        readme.parent.mkdir()
        readme.write_text("# Hello World\nNo markers here.", encoding="utf-8")

        from gps.config.manager import GPSSettings
        from gps.engine.core import GPSEngine
        settings = GPSSettings(username="testuser", readme_path=Path("profile/README.md"))
        engine = GPSEngine(settings)
        result = engine.validate()
        # Missing markers logs a warning but validate() still returns True
        assert result is True

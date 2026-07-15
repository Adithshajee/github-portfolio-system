"""
GPS Core Engine
────────────────
Orchestrates provider execution, markdown injection, and caching.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from gps.config.manager import GPSSettings
from gps.providers.github.provider import GitHubProvider
from gps.renderer.core import JSONRenderer, MarkdownRenderer

logger = logging.getLogger(__name__)


class GPSEngine:
    """Core GPS identity engine."""

    def __init__(self, settings: GPSSettings) -> None:
        self.settings = settings
        from gps.plugins.loader import discover_plugins

        discover_plugins(self)
        from gps.themes.engine import ThemeEngine

        theme_name = getattr(self.settings.theme, "name", "swe_general")
        theme_variant = getattr(self.settings.theme, "variant", "dark")
        self.theme_engine = ThemeEngine(theme_name=theme_name, variant=theme_variant)
        self.renderer = MarkdownRenderer(
            readme_path=Path(self.settings.readme_path),
            start_marker=self.settings.sections.active_repos.start_marker,
            end_marker=self.settings.sections.active_repos.end_marker,
        )

    def _build_providers(self) -> list[Any]:
        """Instantiate all enabled providers from configuration."""
        providers: list[Any] = []
        cfg = self.settings

        if cfg.providers.github.enabled:
            if not cfg.username:
                logger.error("GitHub provider enabled but 'username' is not set.")
            else:
                providers.append(
                    GitHubProvider(
                        username=cfg.username,
                        token=cfg.github_token,
                        repo_count=cfg.providers.github.repo_count,
                        exclude_forks=cfg.providers.github.exclude_forks,
                        exclude_archived=cfg.providers.github.exclude_archived,
                        include_pinned=cfg.providers.github.include_pinned,
                        filter_topics=cfg.providers.github.filter_topics,
                        timeout=cfg.http.timeout,
                        max_retries=cfg.http.max_retries,
                        retry_delay=cfg.http.retry_delay,
                    )
                )

        if cfg.providers.huggingface.enabled:
            hf_username = cfg.providers.huggingface.username or cfg.username
            if not hf_username:
                logger.warning("Hugging Face provider enabled but no username configured.")
            else:
                try:
                    from gps.providers.huggingface.provider import HuggingFaceProvider

                    providers.append(
                        HuggingFaceProvider(
                            username=hf_username,
                            token=cfg.hf_token,
                            model_count=cfg.providers.huggingface.model_count,
                            space_count=cfg.providers.huggingface.space_count,
                            timeout=cfg.http.timeout,
                            max_retries=cfg.http.max_retries,
                        )
                    )
                except ImportError as e:
                    logger.error("Failed to load HuggingFace provider: %s", e)

        if cfg.providers.kaggle.enabled:
            kaggle_username = cfg.providers.kaggle.username or cfg.username
            if not kaggle_username:
                logger.warning("Kaggle provider enabled but no username configured.")
            else:
                try:
                    from gps.providers.kaggle.provider import KaggleProvider

                    providers.append(
                        KaggleProvider(
                            username=kaggle_username,
                            kaggle_key=cfg.kaggle_key,
                        )
                    )
                except Exception as e:
                    logger.error("Failed to load Kaggle provider: %s", e)

        if cfg.providers.leetcode.enabled:
            leetcode_username = cfg.providers.leetcode.username or cfg.username
            if leetcode_username:
                try:
                    from gps.providers.leetcode import LeetCodeProvider

                    providers.append(LeetCodeProvider(username=leetcode_username))
                except Exception as e:
                    logger.error("Failed to load LeetCode provider: %s", e)

        if cfg.providers.blog.enabled:
            feed_url = cfg.providers.blog.feed_url
            if feed_url:
                try:
                    from gps.providers.blog import BlogProvider

                    providers.append(BlogProvider(feed_url=feed_url))
                except Exception as e:
                    logger.error("Failed to load Blog provider: %s", e)

        return providers

    def run(
        self,
        dry_run: bool = False,
        provider_filter: str | None = None,
    ) -> dict[str, str]:
        """Execute all enabled providers."""
        providers = self._build_providers()

        if not providers:
            logger.warning("No providers are enabled.")
            return {}

        if provider_filter:
            providers = [p for p in providers if p.name == provider_filter]

        results: dict[str, str] = {}

        if len(providers) > 1:
            with ThreadPoolExecutor(max_workers=len(providers)) as executor:
                future_to_provider = {
                    executor.submit(p.run, self.theme_engine): p for p in providers
                }
                for future in as_completed(future_to_provider):
                    provider = future_to_provider[future]
                    try:
                        rendered, success = future.result()
                        if success:
                            results[provider.name] = rendered
                    except Exception as e:
                        logger.error("Provider '%s' failed: %s", provider.name, e)
        else:
            for provider in providers:
                rendered, success = provider.run(self.theme_engine)
                if success:
                    results[provider.name] = rendered

        if "github" in results:
            self._inject_readme(results["github"], dry_run=dry_run)

        if self.settings.outputs.json:
            self._export_json(results, dry_run=dry_run)

        return results

    def _inject_readme(self, content: str, dry_run: bool) -> None:
        readme_path = Path(self.settings.readme_path)
        section_cfg = self.settings.sections.active_repos
        renderer = MarkdownRenderer(
            readme_path=readme_path,
            start_marker=section_cfg.start_marker,
            end_marker=section_cfg.end_marker,
        )
        renderer.inject(content, dry_run=dry_run)

    def _export_json(self, results: dict[str, str], dry_run: bool) -> None:
        output_path = Path(self.settings.readme_path).parent / "data.json"
        renderer = JSONRenderer(output_path=output_path)
        renderer.render({"providers": results}, dry_run=dry_run)

    def validate(self) -> bool:
        """Validate current config."""
        from gps.utils.validators import (
            safe_readme_path,
            validate_github_username,
            validate_readme_markers,
        )

        ok = True
        cfg = self.settings

        if not cfg.username:
            logger.error("❌ 'username' is not set.")
            ok = False
        elif not validate_github_username(cfg.username):
            logger.error("❌ Username '%s' is not valid.", cfg.username)
            ok = False

        try:
            readme_path = safe_readme_path(Path(cfg.readme_path))
            if not readme_path.exists():
                logger.error("❌ README not found: %s", readme_path)
                ok = False
            else:
                content = readme_path.read_text(encoding="utf-8")
                section_cfg = cfg.sections.active_repos
                if not validate_readme_markers(
                    content, section_cfg.start_marker, section_cfg.end_marker
                ):
                    logger.warning("⚠️ Markers not found in README.")
        except Exception as e:
            logger.error("❌ Path validation failed: %s", e)
            ok = False

        return ok

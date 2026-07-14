"""
GPS GitHub Provider
────────────────────
Implements the BaseProvider interface for GitHub data.
"""

from __future__ import annotations

import logging
from typing import Any

from gps.providers.base import BaseProvider, register
from gps.providers.github.client import GitHubClient
from gps.providers.github.models import GitHubProviderData, GitHubRepo, GitHubStats, GitHubUser

logger = logging.getLogger(__name__)


@register("github")
class GitHubProvider(BaseProvider[dict[str, Any], GitHubProviderData]):
    """
    GitHub data provider.

    Fetches user profile and repositories, transforms into typed models,
    and renders the active repos section for the profile README.
    """

    name = "github"
    display_name = "GitHub"

    def __init__(
        self,
        username: str,
        token: str = "",  # nosec B107
        repo_count: int = 5,
        exclude_forks: bool = True,
        exclude_archived: bool = True,
        include_pinned: bool = True,
        filter_topics: list[str] | None = None,
        timeout: int = 15,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        self.username = username
        self.repo_count = repo_count
        self.exclude_forks = exclude_forks
        self.exclude_archived = exclude_archived
        self.include_pinned = include_pinned
        self.filter_topics = filter_topics or []
        self._client = GitHubClient(
            token=token,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )

    def fetch(self) -> dict[str, Any]:
        """Fetch user profile and repositories from GitHub API."""
        raw_user = self._client.get_user(self.username)
        raw_repos = self._client.get_repos(self.username, per_page=50)
        pinned_repos: list[dict[str, Any]] = []
        if self.include_pinned:
            pinned_repos = self._client.get_pinned_repos(self.username)
        return {
            "user": raw_user,
            "repos": raw_repos,
            "pinned_repos": pinned_repos,
        }

    def transform(self, raw: dict[str, Any]) -> GitHubProviderData:
        """Transform raw API dicts into validated Pydantic models."""
        user = GitHubUser.model_validate(raw["user"]) if raw.get("user") else None

        all_repos = [
            GitHubRepo.model_validate(r) for r in raw.get("repos", []) if isinstance(r, dict)
        ]

        pinned_repos = [
            GitHubRepo.model_validate(r) for r in raw.get("pinned_repos", []) if isinstance(r, dict)
        ]

        # Apply filters to regular repos
        filtered = [
            r
            for r in all_repos
            if not (self.exclude_forks and r.fork)
            and not (self.exclude_archived and r.archived)
            and r.name != self.username  # exclude profile repo
            and (not self.filter_topics or any(t in r.topics for t in self.filter_topics))
        ]

        # Apply filters to pinned repos
        filtered_pinned = [
            p
            for p in pinned_repos
            if not (self.exclude_forks and p.fork)
            and not (self.exclude_archived and p.archived)
            and p.name != self.username
            and (not self.filter_topics or any(t in p.topics for t in self.filter_topics))
        ]

        # Merge pinned repos at the top
        selected = list(filtered_pinned[: self.repo_count])
        included_urls = {r.html_url for r in selected}

        # Fill remaining slots with recently updated repos
        remaining_slots = self.repo_count - len(selected)
        if remaining_slots > 0:
            active_candidates = [r for r in filtered if r.html_url not in included_urls]
            sorted_candidates = sorted(
                active_candidates,
                key=lambda r: r.updated_at.timestamp() if r.updated_at else 0.0,
                reverse=True,
            )
            selected.extend(sorted_candidates[:remaining_slots])

        stats = GitHubStats(username=self.username, repos=all_repos)
        stats.compute_totals()

        return GitHubProviderData(user=user, repos=selected, stats=stats)

    def validate(self, data: GitHubProviderData) -> bool:
        """Ensure we have at least some usable data."""
        return len(data.repos) > 0 or data.user is not None

    def render(self, data: GitHubProviderData) -> str:
        """Render the active repos section as markdown."""
        if not data.repos:
            return "<!-- GPS: No repositories found -->"

        lines: list[str] = ["### 📂 Active Projects & Repositories", ""]
        for repo in data.repos:
            lines.append(f"- **[{repo.name}]({repo.html_url})** — *Updated {repo.updated_date}*")
            lines.append(f"  > {repo.display_description}")
            lines.append(f"  > 🌟 `{repo.stargazers_count}` | 🍴 `{repo.forks_count}`")
            lines.append("")

        return "\n".join(lines).strip()

    def close(self) -> None:
        self._client.close()

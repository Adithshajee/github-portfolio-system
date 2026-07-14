"""
GPS GitHub Provider: API Client
────────────────────────────────
Wraps the GitHub REST v3 and GraphQL v4 APIs.

Features:
  - PAT authentication with unauthenticated fallback
  - ETag caching via parent HTTPClient
  - Rate limit awareness
  - Pagination for repo listing
  - GraphQL for pinned repositories
"""

from __future__ import annotations

import logging
from typing import Any

from gps.utils.http import APIError, HTTPClient, RateLimitError

logger = logging.getLogger(__name__)

_REST_BASE = "https://api.github.com"
_GRAPHQL_URL = "https://api.github.com/graphql"

_PINNED_REPOS_QUERY = """
query($username: String!) {
  user(login: $username) {
    pinnedItems(first: 6, types: REPOSITORY) {
      nodes {
        ... on Repository {
          name
          description
          url
          stargazerCount
          forkCount
          primaryLanguage { name }
          repositoryTopics(first: 5) {
            nodes { topic { name } }
          }
          updatedAt
        }
      }
    }
  }
}
"""


class GitHubClient:
    """
    GitHub API client supporting REST v3 and GraphQL v4.

    Args:
        token: GitHub Personal Access Token. If empty, operates unauthenticated.
        http_settings: HTTPClient configuration (timeout, retries, etc.).
    """

    def __init__(
        self,
        token: str = "",  # nosec B107
        timeout: int = 15,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        rate_limit_threshold: int = 10,
    ) -> None:
        self._http = HTTPClient(
            token=token,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            rate_limit_threshold=rate_limit_threshold,
            user_agent=(
                "GPS/2.0 (github-portfolio-system; github.com/Adithshajee/github-portfolio-system)"
            ),
        )
        self._has_token = bool(token)

    def get_user(self, username: str) -> dict[str, Any]:
        """
        Fetch a user's public profile.

        Args:
            username: GitHub username.

        Returns:
            Raw user profile dict from GitHub API.
        """
        url = f"{_REST_BASE}/users/{username}"
        logger.debug("Fetching user profile: %s", username)
        return self._http.get(url)  # type: ignore[no-any-return]

    def get_repos(
        self,
        username: str,
        per_page: int = 30,
        sort: str = "updated",
        direction: str = "desc",
    ) -> list[dict[str, Any]]:
        """
        Fetch all public repositories for a user, with pagination.

        Args:
            username: GitHub username.
            per_page: Repos per page (max 100).
            sort: Sort field: 'updated', 'stars', 'forks', 'full_name'.
            direction: 'asc' or 'desc'.

        Returns:
            List of raw repo dicts.
        """
        url = f"{_REST_BASE}/users/{username}/repos"
        all_repos: list[dict[str, Any]] = []
        page = 1

        while True:
            params: dict[str, Any] = {
                "sort": sort,
                "direction": direction,
                "per_page": min(per_page, 100),
                "page": page,
                "type": "owner",
            }
            logger.debug("Fetching repos page %d for %s", page, username)
            batch = self._http.get(url, params=params)

            if not isinstance(batch, list) or not batch:
                break

            all_repos.extend(batch)

            # Stop if we got fewer than requested (last page)
            if len(batch) < params["per_page"]:
                break

            # Stop if we've collected enough
            if len(all_repos) >= per_page:
                break

            page += 1

        return all_repos

    def get_pinned_repos(self, username: str) -> list[dict[str, Any]]:
        """
        Fetch pinned repositories via GitHub GraphQL API.

        Requires a token with at least public_repo scope.
        Falls back gracefully if token is missing.

        Args:
            username: GitHub username.

        Returns:
            List of pinned repo dicts (normalized to match REST format).
        """
        if not self._has_token:
            logger.info(
                "Skipping pinned repos fetch: GraphQL requires a GitHub token. "
                "Set GH_PAT to enable pinned repository display."
            )
            return []

        try:
            result = self._http.post(
                _GRAPHQL_URL,
                json={"query": _PINNED_REPOS_QUERY, "variables": {"username": username}},
            )
            nodes = result.get("data", {}).get("user", {}).get("pinnedItems", {}).get("nodes", [])
            # Normalize GraphQL response to match REST schema
            normalized: list[dict[str, Any]] = []
            for node in nodes:
                if not node:
                    continue
                normalized.append(
                    {
                        "name": node.get("name", ""),
                        "html_url": node.get("url", ""),
                        "description": node.get("description"),
                        "stargazers_count": node.get("stargazerCount", 0),
                        "forks_count": node.get("forkCount", 0),
                        "language": (node.get("primaryLanguage") or {}).get("name"),
                        "topics": [
                            t["topic"]["name"]
                            for t in (node.get("repositoryTopics") or {}).get("nodes", [])
                        ],
                        "updated_at": node.get("updatedAt"),
                        "fork": False,  # Pinned repos are typically owned repos
                    }
                )
            return normalized

        except (APIError, RateLimitError, Exception) as e:
            logger.warning("Failed to fetch pinned repos via GraphQL: %s", str(e))
            return []

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._http.close()

    def __enter__(self) -> GitHubClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

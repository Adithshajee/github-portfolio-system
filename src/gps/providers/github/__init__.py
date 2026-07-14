"""GitHub provider package."""

from gps.providers.github.client import GitHubClient
from gps.providers.github.models import GitHubProviderData, GitHubRepo, GitHubStats, GitHubUser
from gps.providers.github.provider import GitHubProvider

__all__ = [
    "GitHubClient",
    "GitHubProvider",
    "GitHubProviderData",
    "GitHubRepo",
    "GitHubStats",
    "GitHubUser",
]

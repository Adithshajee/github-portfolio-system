"""
GPS GitHub Provider: Pydantic Data Models
─────────────────────────────────────────
Typed models for GitHub API responses.
All fields have sensible defaults to handle partial/missing API data.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class GitHubUser(BaseModel):
    """GitHub user profile data."""

    login: str
    name: str | None = None
    bio: str | None = None
    avatar_url: str = ""
    html_url: str = ""
    public_repos: int = 0
    followers: int = 0
    following: int = 0
    created_at: datetime | None = None
    location: str | None = None
    email: str | None = None
    blog: str | None = None
    company: str | None = None

    @field_validator("name", "bio", "location", mode="before")
    @classmethod
    def strip_strings(cls, v: object) -> str | None:
        if isinstance(v, str):
            return v.strip() or None
        return None


class GitHubRepo(BaseModel):
    """A single GitHub repository."""

    name: str
    full_name: str = ""
    html_url: str = ""
    description: str | None = None
    language: str | None = None
    stargazers_count: int = 0
    forks_count: int = 0
    open_issues_count: int = 0
    topics: list[str] = Field(default_factory=list)
    updated_at: datetime | None = None
    created_at: datetime | None = None
    fork: bool = False
    archived: bool = False
    disabled: bool = False
    visibility: str = "public"
    homepage: str | None = None

    @field_validator("description", mode="before")
    @classmethod
    def clean_description(cls, v: object) -> str | None:
        if isinstance(v, str):
            return v.strip() or None
        return None

    @property
    def updated_date(self) -> str:
        """Return formatted update date string."""
        if self.updated_at:
            return self.updated_at.strftime("%Y-%m-%d")
        return "N/A"

    @property
    def display_description(self) -> str:
        """Return description or a sensible default."""
        return self.description or "No description provided."


class GitHubStats(BaseModel):
    """Aggregated GitHub statistics for a user."""

    username: str
    repos: list[GitHubRepo] = Field(default_factory=list)
    total_stars: int = 0
    total_forks: int = 0
    languages_used: list[str] = Field(default_factory=list)

    def compute_totals(self) -> None:
        """Recompute aggregated stats from the repos list."""
        self.total_stars = sum(r.stargazers_count for r in self.repos)
        self.total_forks = sum(r.forks_count for r in self.repos)
        langs = {r.language for r in self.repos if r.language}
        self.languages_used = sorted(langs)


class GitHubProviderData(BaseModel):
    """Full dataset produced by the GitHub provider."""

    user: GitHubUser | None = None
    repos: list[GitHubRepo] = Field(default_factory=list)
    stats: GitHubStats | None = None

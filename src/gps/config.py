"""
GPS Configuration Management
─────────────────────────────
Loads and validates platform configuration from gps.yml and environment variables.

Priority (highest to lowest):
  1. Environment variables (e.g. GPS_USERNAME, GH_PAT)
  2. gps.yml in the current working directory or repo root
  3. Built-in defaults

Sensitive credentials (API tokens) must ONLY be provided via environment variables.
They are never read from gps.yml.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

# Silence Pydantic warning about json field shadowing BaseModel.json()
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message='Field name "json" in "OutputSettings" shadows an attribute in parent "BaseModel"',
)


class HTTPSettings(BaseModel):
    """HTTP client tuning parameters."""

    timeout: int = Field(default=15, ge=1, le=120, description="Request timeout in seconds")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    retry_delay: float = Field(default=1.0, ge=0.1, description="Base retry delay in seconds")
    rate_limit_threshold: int = Field(
        default=10, ge=0, description="Min remaining rate limit before pausing"
    )


class GitHubProviderSettings(BaseModel):
    """GitHub provider configuration."""

    enabled: bool = True
    repo_count: int = Field(default=5, ge=1, le=100)
    include_pinned: bool = True
    exclude_forks: bool = True
    exclude_archived: bool = True
    filter_topics: list[str] = Field(default_factory=list)


class HuggingFaceProviderSettings(BaseModel):
    """Hugging Face provider configuration."""

    enabled: bool = False
    username: str = ""
    model_count: int = Field(default=5, ge=1, le=50)
    space_count: int = Field(default=3, ge=1, le=20)


class KaggleProviderSettings(BaseModel):
    """Kaggle provider configuration."""

    enabled: bool = False
    username: str = ""


class LinkedInProviderSettings(BaseModel):
    """LinkedIn provider configuration (manual updates only)."""

    enabled: bool = False


class LeetCodeProviderSettings(BaseModel):
    """LeetCode provider configuration."""

    enabled: bool = False
    username: str = ""


class BlogProviderSettings(BaseModel):
    """Blog provider configuration."""

    enabled: bool = False
    feed_url: str = ""


class ProvidersSettings(BaseModel):
    """Aggregated provider settings."""

    github: GitHubProviderSettings = Field(default_factory=GitHubProviderSettings)
    huggingface: HuggingFaceProviderSettings = Field(default_factory=HuggingFaceProviderSettings)
    kaggle: KaggleProviderSettings = Field(default_factory=KaggleProviderSettings)
    linkedin: LinkedInProviderSettings = Field(default_factory=LinkedInProviderSettings)
    leetcode: LeetCodeProviderSettings = Field(default_factory=LeetCodeProviderSettings)
    blog: BlogProviderSettings = Field(default_factory=BlogProviderSettings)


class OutputSettings(BaseModel):
    """Output format settings."""

    markdown: bool = True
    json: bool = False  # type: ignore[assignment]
    html: bool = False


class SectionConfig(BaseModel):
    """Individual section toggle."""

    enabled: bool = True


class ActiveReposSectionConfig(SectionConfig):
    """Active repos section with marker configuration."""

    start_marker: str = "<!-- REPOS_START -->"
    end_marker: str = "<!-- REPOS_END -->"


class SectionsSettings(BaseModel):
    """README section configuration."""

    order: list[str] = Field(
        default_factory=lambda: [
            "hero",
            "professional_overview",
            "skills",
            "analytics",
            "featured_projects",
            "active_repos",
            "tech_stack",
            "engineering_map",
            "contact",
        ]
    )
    hero: SectionConfig = Field(default_factory=SectionConfig)
    professional_overview: SectionConfig = Field(default_factory=SectionConfig)
    skills: SectionConfig = Field(default_factory=SectionConfig)
    analytics: SectionConfig = Field(default_factory=SectionConfig)
    featured_projects: SectionConfig = Field(default_factory=SectionConfig)
    active_repos: ActiveReposSectionConfig = Field(default_factory=ActiveReposSectionConfig)
    tech_stack: SectionConfig = Field(default_factory=SectionConfig)
    engineering_map: SectionConfig = Field(default_factory=SectionConfig)
    contact: SectionConfig = Field(default_factory=SectionConfig)


class ThemeSettings(BaseModel):
    """Theme configuration settings."""

    name: str = "swe_general"
    variant: str = "dark"


class LoggingSettings(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    json_format: bool = False


class GPSSettings(BaseSettings):
    """
    Root platform configuration.

    Environment variable overrides use the GPS_ prefix:
        GPS_USERNAME=myuser
        GPS_README_PATH=profile/README.md
    """

    model_config = SettingsConfigDict(
        env_prefix="GPS_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return env_settings, init_settings

    # Platform identity
    username: str = Field(default="", description="Primary GitHub username")
    readme_path: Path = Field(default=Path("profile/README.md"))
    timezone: str = Field(default="UTC")

    # Sub-configurations
    providers: ProvidersSettings = Field(default_factory=ProvidersSettings)
    outputs: OutputSettings = Field(default_factory=OutputSettings)
    sections: SectionsSettings = Field(default_factory=SectionsSettings)
    http: HTTPSettings = Field(default_factory=HTTPSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    theme: ThemeSettings = Field(default_factory=ThemeSettings)

    # Secrets — ONLY from environment variables
    github_token: str = Field(
        default="", alias="GH_PAT", description="GitHub Personal Access Token"
    )
    hf_token: str = Field(default="", alias="HF_TOKEN", description="Hugging Face API token")
    kaggle_username: str = Field(default="", alias="KAGGLE_USERNAME")
    kaggle_key: str = Field(default="", alias="KAGGLE_KEY")

    @field_validator("readme_path", mode="before")
    @classmethod
    def validate_readme_path(cls, v: object) -> Path:
        """Ensure readme_path is a Path and stays within repo bounds."""
        path = Path(str(v))
        # Prevent path traversal
        if path.is_absolute() or str(path).startswith("/") or str(path).startswith("\\"):
            raise ValueError("readme_path must be a relative path within the repository")
        resolved = (Path.cwd() / path).resolve()
        try:
            resolved.relative_to(Path.cwd().resolve())
        except ValueError as e:
            raise ValueError("readme_path must be within the repository root") from e
        return path

    @model_validator(mode="after")
    def validate_enabled_providers(self) -> GPSSettings:
        """Warn if HF/Kaggle are enabled but no credentials provided."""
        if self.providers.huggingface.enabled and not self.hf_token:
            import warnings

            warnings.warn(
                "Hugging Face provider is enabled but HF_TOKEN is not set. "
                "Set the HF_TOKEN environment variable to authenticate.",
                stacklevel=2,
            )
        if self.providers.kaggle.enabled and not (self.kaggle_username and self.kaggle_key):
            import warnings

            warnings.warn(
                "Kaggle provider is enabled but KAGGLE_USERNAME/KAGGLE_KEY are not set.",
                stacklevel=2,
            )
        return self


def _find_config_file(start: Path | None = None) -> Path | None:
    """Walk up from start directory to find gps.yml."""
    search = start or Path.cwd()
    for directory in [search, *search.parents]:
        candidate = directory / "gps.yml"
        if candidate.exists():
            return candidate
        # Stop at filesystem root
        if directory == directory.parent:
            break
    return None


def load_config(config_path: Path | None = None) -> GPSSettings:
    """
    Load GPS configuration from gps.yml merged with environment variables.

    Args:
        config_path: Explicit path to gps.yml. If None, auto-discovered.

    Returns:
        Validated GPSSettings instance.

    Raises:
        FileNotFoundError: If config_path is provided but doesn't exist.
        ValueError: If configuration is invalid.
    """
    resolved_path = config_path or _find_config_file()

    yaml_data: dict[str, Any] = {}

    if resolved_path is not None:
        if config_path is not None and not resolved_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {resolved_path}")
        with resolved_path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
            if raw and isinstance(raw, dict):
                yaml_data = raw.get("platform", {})
                # Merge top-level sections into flat structure for Pydantic
                for key in ("providers", "outputs", "sections", "http", "logging", "theme"):
                    if key in raw:
                        yaml_data[key] = raw[key]

    # Environment variables take precedence — Pydantic BaseSettings handles this
    # by reading os.environ automatically
    settings = GPSSettings(**yaml_data)
    return settings

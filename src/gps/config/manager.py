"""
GPS Configuration Management
─────────────────────────────
Loads, validates, and serializes configuration settings between YAML/JSON.
Implements version migration logic and configuration state snapshot history (Undo/Redo).
"""

from __future__ import annotations

import logging
import shutil
import warnings
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

logger = logging.getLogger(__name__)

# Silence Pydantic warning about json field shadowing
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message='Field name "json" in "OutputSettings" shadows an attribute in parent "BaseModel"',
)


class HTTPSettings(BaseModel):
    """HTTP client tuning parameters."""

    timeout: int = Field(default=15, ge=1, le=120)
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay: float = Field(default=1.0, ge=0.1)
    rate_limit_threshold: int = Field(default=10, ge=0)


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
    """Root platform configuration model."""

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
    username: str = Field(default="")
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
    github_token: str = Field(default="", alias="GH_PAT")
    hf_token: str = Field(default="", alias="HF_TOKEN")
    kaggle_username: str = Field(default="", alias="KAGGLE_USERNAME")
    kaggle_key: str = Field(default="", alias="KAGGLE_KEY")

    @field_validator("readme_path", mode="before")
    @classmethod
    def validate_readme_path(cls, v: object) -> Path:
        """Ensure readme_path stays within repo bounds."""
        path = Path(str(v))
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
        # Load local secure token if github_token is not explicitly set
        if not self.github_token:
            from gps.auth.storage import get_secure_token

            self.github_token = get_secure_token() or ""

        if self.providers.huggingface.enabled and not self.hf_token:
            warnings.warn(
                "Hugging Face provider is enabled but HF_TOKEN is not set.",
                stacklevel=2,
            )
        if self.providers.kaggle.enabled and not (self.kaggle_username and self.kaggle_key):
            warnings.warn(
                "Kaggle provider is enabled but KAGGLE_USERNAME/KAGGLE_KEY are not set.",
                stacklevel=2,
            )
        return self


class ConfigurationManager:
    """Handles parsing, validation, serialization, backups, and snapshotting config."""

    def __init__(self, config_dir: Path | None = None) -> None:
        self.config_dir = config_dir or Path.cwd()
        self.history_dir = self.config_dir / "history"
        self.history_dir.mkdir(exist_ok=True)

    def load(self, path: Path | None = None) -> GPSSettings:
        """Load and validate settings from path or default gps.yml."""
        target = path or _find_config_file(self.config_dir)
        raw: dict[str, Any] = {}
        if target is not None:
            if path is not None and not target.exists():
                raise FileNotFoundError(f"Configuration file not found: {target}")
            if target.exists():
                with target.open("r", encoding="utf-8") as f:
                    raw = yaml.safe_load(f) or {}

        # Migration logic
        migrated = self.migrate(raw)

        # Build GPSSettings
        yaml_data = migrated.get("platform", {})
        for key in ("providers", "outputs", "sections", "http", "logging", "theme"):
            if key in migrated:
                yaml_data[key] = migrated[key]

        return GPSSettings(**yaml_data)

    def save(self, settings: GPSSettings, path: Path | None = None) -> None:
        """Serialize settings back to yaml config file."""
        target = path or self.config_dir / "gps.yml"
        self.create_snapshot(target)

        # Structure settings dictionary as nested yaml layout
        dump_dict = {
            "platform": {
                "username": settings.username,
                "readme_path": str(settings.readme_path),
                "timezone": settings.timezone,
            },
            "theme": settings.theme.model_dump(),
            "providers": settings.providers.model_dump(),
            "outputs": settings.model_dump()["outputs"],  # avoid shadowing
            "sections": settings.sections.model_dump(),
            "http": settings.http.model_dump(),
            "logging": settings.logging.model_dump(),
        }

        # Clean null values and empty providers
        with target.open("w", encoding="utf-8") as f:
            yaml.safe_dump(dump_dict, f, default_flow_style=False, sort_keys=False)

    def create_snapshot(self, current_file: Path) -> None:
        """Save a state snapshot inside history directory for Undo/Redo."""
        if not current_file.exists():
            return
        snapshots = sorted(self.history_dir.glob("snapshot_*.yml"))
        next_idx = len(snapshots) + 1
        shutil.copy2(current_file, self.history_dir / f"snapshot_{next_idx}.yml")

    def undo(self, current_file: Path) -> bool:
        """Revert configuration to the previous state snapshot."""
        snapshots = sorted(self.history_dir.glob("snapshot_*.yml"))
        if not snapshots:
            return False
        last_snapshot = snapshots[-1]
        shutil.copy2(last_snapshot, current_file)
        last_snapshot.unlink()
        return True

    def migrate(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Convert older keys or values to version 3 formats."""
        if not raw:
            return {}
        # Legacy checks, e.g. mapping simple string user configurations
        if "github_username" in raw:
            raw.setdefault("platform", {})
            raw["platform"]["username"] = raw.pop("github_username")
        return raw


def _find_config_file(start: Path | None = None) -> Path | None:
    """Walk up from start directory to find gps.yml."""
    search = start or Path.cwd()
    for directory in [search, *search.parents]:
        candidate = directory / "gps.yml"
        if candidate.exists():
            return candidate
        if directory == directory.parent:
            break
    return None


def load_config(config_path: Path | None = None) -> GPSSettings:
    """Helper method to quickly retrieve settings."""
    manager = ConfigurationManager()
    return manager.load(config_path)

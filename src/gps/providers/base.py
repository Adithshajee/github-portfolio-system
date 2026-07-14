"""
GPS Provider System: Abstract Base Provider
────────────────────────────────────────────
All data providers must implement this interface.

The provider pattern follows the Open-Closed Principle:
  - Open for extension (add new providers without changing engine)
  - Closed for modification (engine doesn't know about provider internals)

Each provider implements a 4-stage pipeline:
  fetch()     → Raw API data (dicts/lists from HTTP responses)
  transform() → Typed Pydantic models (validated, normalized)
  validate()  → Boolean health check on transformed data
  render()    → Markdown string ready for README injection
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Generic, TypeVar

# Generic type vars for provider input/output
RawT = TypeVar("RawT")
DataT = TypeVar("DataT")


class BaseProvider(ABC, Generic[RawT, DataT]):
    """
    Abstract base class for all GPS data providers.

    Subclasses must implement all four pipeline stages.
    """

    #: Unique provider identifier — used in CLI and config
    name: str = ""
    #: Human-readable display name
    display_name: str = ""

    @abstractmethod
    def fetch(self) -> RawT:
        """
        Fetch raw data from the provider's API.

        Returns:
            Raw response data (typically dict or list).

        Raises:
            GPSHTTPError: On any network or API error.
        """
        ...

    @abstractmethod
    def transform(self, raw: RawT) -> DataT:
        """
        Transform raw API response into validated, typed models.

        Args:
            raw: Output from fetch().

        Returns:
            Typed, validated data model(s).
        """
        ...

    @abstractmethod
    def validate(self, data: DataT) -> bool:
        """
        Perform a health check on the transformed data.

        Args:
            data: Output from transform().

        Returns:
            True if data is usable for rendering, False otherwise.
        """
        ...

    @abstractmethod
    def render(self, data: DataT) -> str:
        """
        Render provider data into a markdown string.

        Args:
            data: Output from transform().

        Returns:
            Markdown string ready for README injection.
        """
        ...

    def run(self, theme_engine: Any = None) -> tuple[str, bool]:  # noqa: ANN401
        """
        Execute the full provider pipeline.

        Returns:
            Tuple of (rendered_markdown: str, success: bool).
        """
        import logging

        log = logging.getLogger(f"gps.providers.{self.name}")

        try:
            log.info("Fetching data from %s...", self.display_name or self.name)
            raw = self.fetch()

            log.debug("Transforming %s data...", self.name)
            data = self.transform(raw)

            if not self.validate(data):
                log.warning("%s data validation failed — using empty output.", self.name)
                return "", False

            log.info("%s data fetched and validated successfully.", self.display_name or self.name)
            if theme_engine is not None:
                rendered = theme_engine.render_template(f"{self.name}.md", {"data": data})
                if rendered:
                    return rendered, True
            return self.render(data), True

        except Exception as e:
            log.error("Provider '%s' failed: %s", self.name, str(e))
            return "", False


class ProviderError(Exception):
    """Raised when a provider encounters an unrecoverable error."""

    pass


# ─── Registry ─────────────────────────────────────────────────────────────────

_REGISTRY: dict[str, type[BaseProvider[Any, Any]]] = {}


def register(
    name: str,
) -> Callable[[type[BaseProvider[Any, Any]]], type[BaseProvider[Any, Any]]]:
    """
    Decorator to register a provider class in the global registry.

    Usage:
        @register("github")
        class GitHubProvider(BaseProvider): ...
    """

    def decorator(cls: type[BaseProvider[Any, Any]]) -> type[BaseProvider[Any, Any]]:
        cls.name = name
        _REGISTRY[name] = cls
        return cls

    return decorator


def get_provider(name: str) -> type[BaseProvider[Any, Any]]:
    """
    Retrieve a registered provider class by name.

    Args:
        name: Provider identifier e.g. 'github', 'huggingface'.

    Raises:
        KeyError: If provider is not registered.
    """
    if name not in _REGISTRY:
        available = ", ".join(_REGISTRY.keys()) or "none"
        raise KeyError(f"Unknown provider: '{name}'. Available providers: {available}")
    return _REGISTRY[name]


def list_providers() -> list[str]:
    """Return a list of all registered provider names."""
    return list(_REGISTRY.keys())

"""
GPS Providers Package
──────────────────────
Import all providers to trigger their @register() decorators.
This ensures providers are registered in the global registry
simply by importing this package.
"""

from __future__ import annotations

# Import providers to trigger registration
from gps.providers import (  # noqa: F401
    blog,
    github,
    huggingface,
    kaggle,
    leetcode,
    linkedin,
)
from gps.providers.base import BaseProvider, ProviderError, get_provider, list_providers, register

__all__ = [
    "BaseProvider",
    "ProviderError",
    "get_provider",
    "list_providers",
    "register",
]

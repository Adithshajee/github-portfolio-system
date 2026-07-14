"""
GPS Hugging Face Provider: API Client
──────────────────────────────────────
Fetches user models, spaces, and datasets via Hugging Face REST APIs using HTTPClient.
"""

from __future__ import annotations

import logging
from typing import Any

from gps.utils.http import HTTPClient

logger = logging.getLogger(__name__)

_HF_API_BASE = "https://huggingface.co/api"


class HuggingFaceClient:
    """
    Hugging Face Hub API client.

    Args:
        token: HF API token (read-only token is sufficient).
        timeout: Request timeout in seconds.
        max_retries: Maximum retry attempts.
    """

    def __init__(
        self,
        token: str = "",  # nosec B107
        timeout: int = 15,
        max_retries: int = 3,
    ) -> None:
        self._http = HTTPClient(
            token=token,
            timeout=timeout,
            max_retries=max_retries,
            user_agent="GPS/2.0 (github-portfolio-system)",
        )
        self._token = token

    def get_models(
        self,
        author: str,
        limit: int = 10,
        sort: str = "likes",
    ) -> list[dict[str, Any]]:
        """
        Fetch models authored by the given user.

        Args:
            author: Hugging Face username.
            limit: Maximum number of models to return.
            sort: Sort field: 'likes', 'downloads', 'lastModified'.

        Returns:
            List of raw model dicts.
        """
        url = f"{_HF_API_BASE}/models"
        params: dict[str, Any] = {
            "author": author,
            "limit": limit,
            "sort": sort,
            "direction": -1,
        }
        result = self._http.get(url, params=params)
        return result if isinstance(result, list) else []

    def get_spaces(
        self,
        author: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Fetch Spaces authored by the given user."""
        url = f"{_HF_API_BASE}/spaces"
        params: dict[str, Any] = {"author": author, "limit": limit}
        result = self._http.get(url, params=params)
        return result if isinstance(result, list) else []

    def get_datasets(
        self,
        author: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Fetch datasets authored by the given user."""
        url = f"{_HF_API_BASE}/datasets"
        params: dict[str, Any] = {"author": author, "limit": limit}
        result = self._http.get(url, params=params)
        return result if isinstance(result, list) else []

    def close(self) -> None:
        self._http.close()

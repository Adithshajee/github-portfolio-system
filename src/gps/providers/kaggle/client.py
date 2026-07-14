"""
GPS Kaggle Provider: API Client
────────────────────────────────
Uses the official Kaggle API library.
Requires KAGGLE_USERNAME and KAGGLE_KEY environment variables.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class KaggleClient:
    """
    Kaggle API client.

    Requires the kaggle package: pip install gps[kaggle]
    And credentials: KAGGLE_USERNAME and KAGGLE_KEY env vars.
    """

    def __init__(self, username: str = "", key: str = "") -> None:
        # Kaggle library reads from env vars automatically
        if username:
            os.environ.setdefault("KAGGLE_USERNAME", username)
        if key:
            os.environ.setdefault("KAGGLE_KEY", key)

        try:
            from kaggle.api.kaggle_api_extended import KaggleApiExtended

            self._api = KaggleApiExtended()
            self._api.authenticate()
            logger.info("Kaggle client authenticated successfully.")
        except ImportError:
            raise ImportError(
                "The 'kaggle' package is required for the Kaggle provider. "
                "Install it with: pip install 'gps[kaggle]'"
            ) from None
        except Exception as e:
            raise RuntimeError(
                f"Kaggle authentication failed. Ensure KAGGLE_USERNAME and KAGGLE_KEY "
                f"are set correctly. Error: {e}"
            ) from e

    def get_competitions(self, username: str) -> list[dict[str, Any]]:
        """List competitions the user has participated in."""
        try:
            # Kaggle API doesn't have a direct "user competitions" endpoint
            # We list competitions and filter — this is a best-effort implementation
            results = self._api.competitions_list(search=username)
            return [
                {
                    "ref": c.ref,
                    "title": c.title,
                    "description": c.description,
                    "url": c.url,
                    "category": c.category,
                    "reward": c.reward,
                    "deadline": str(c.deadline) if c.deadline else None,
                    "team_count": getattr(c, "teamCount", 0),
                }
                for c in (results or [])
            ]
        except Exception as e:
            logger.warning("Failed to fetch Kaggle competitions: %s", e)
            return []

    def get_notebooks(self, username: str, page_size: int = 10) -> list[dict[str, Any]]:
        """List kernels/notebooks for the given username."""
        try:
            results = self._api.kernels_list(user=username, page_size=page_size)
            return [
                {
                    "title": k.title,
                    "url": f"https://www.kaggle.com/code/{k.ref}",
                    "votes": getattr(k, "totalVotes", 0),
                    "language": getattr(k, "language", None),
                }
                for k in (results or [])
            ]
        except Exception as e:
            logger.warning("Failed to fetch Kaggle notebooks: %s", e)
            return []

    def get_datasets(self, username: str, page_size: int = 10) -> list[dict[str, Any]]:
        """List datasets published by the given username."""
        try:
            results = self._api.dataset_list(user=username, page_size=page_size)
            return [
                {
                    "title": d.title,
                    "url": f"https://www.kaggle.com/datasets/{d.ref}",
                    "download_count": getattr(d, "downloadCount", 0),
                    "vote_count": getattr(d, "voteCount", 0),
                    "usability_rating": getattr(d, "usabilityRating", 0.0),
                }
                for d in (results or [])
            ]
        except Exception as e:
            logger.warning("Failed to fetch Kaggle datasets: %s", e)
            return []

"""
GPS Kaggle Provider
────────────────────
Fetches competition results, notebooks, and datasets from Kaggle.
Disabled by default. Enable via gps.yml:

    providers:
      kaggle:
        enabled: true
        username: "your-kaggle-username"

Requires: pip install 'gps[kaggle]'
Requires: KAGGLE_USERNAME and KAGGLE_KEY environment variables
"""

from __future__ import annotations

import logging
from typing import Any

from gps.providers.base import BaseProvider, register
from gps.providers.kaggle.client import KaggleClient
from gps.providers.kaggle.models import (
    KaggleCompetition,
    KaggleDataset,
    KaggleNotebook,
    KaggleProviderData,
)

logger = logging.getLogger(__name__)


@register("kaggle")
class KaggleProvider(BaseProvider[dict[str, Any], KaggleProviderData]):
    """
    Kaggle data provider.

    Fetches competitions, notebooks, and datasets for a Kaggle user.
    """

    name = "kaggle"
    display_name = "Kaggle"

    def __init__(
        self,
        username: str,
        kaggle_key: str = "",
    ) -> None:
        self.username = username
        self._client = KaggleClient(username=username, key=kaggle_key)

    def fetch(self) -> dict[str, Any]:
        return {
            "competitions": self._client.get_competitions(self.username),
            "notebooks": self._client.get_notebooks(self.username),
            "datasets": self._client.get_datasets(self.username),
        }

    def transform(self, raw: dict[str, Any]) -> KaggleProviderData:
        competitions = [KaggleCompetition(**c) for c in raw.get("competitions", []) if c]
        notebooks = [KaggleNotebook(**n) for n in raw.get("notebooks", []) if n]
        datasets = [KaggleDataset(**d) for d in raw.get("datasets", []) if d]
        return KaggleProviderData(
            username=self.username,
            competitions=competitions,
            notebooks=notebooks,
            datasets=datasets,
        )

    def validate(self, data: KaggleProviderData) -> bool:
        return bool(data.competitions or data.notebooks or data.datasets)

    def render(self, data: KaggleProviderData) -> str:
        """Render Kaggle section as markdown."""
        lines: list[str] = ["### 🏆 Kaggle Portfolio", ""]

        if data.tier:
            lines.append(f"**Tier:** {data.tier}")
            lines.append("")

        if data.notebooks:
            lines.append("**Notebooks:**")
            for nb in data.notebooks[:5]:
                lines.append(f"- **[{nb.title}]({nb.notebook_url})** — 🗳️ `{nb.votes}` votes")
            lines.append("")

        if data.competitions:
            lines.append("**Competitions:**")
            for comp in data.competitions[:5]:
                lines.append(f"- **[{comp.title}]({comp.competition_url})**")
            lines.append("")

        return "\n".join(lines).strip()

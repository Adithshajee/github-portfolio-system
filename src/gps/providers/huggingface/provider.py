"""
GPS Hugging Face Provider
──────────────────────────
Fetches models, spaces, and datasets from Hugging Face Hub.
Disabled by default. Enable via gps.yml:

    providers:
      huggingface:
        enabled: true
        username: "your-hf-username"

Requires HF_TOKEN environment variable for private repos and higher rate limits.
"""

from __future__ import annotations

import logging
from typing import Any

from gps.providers.base import BaseProvider, register
from gps.providers.huggingface.client import HuggingFaceClient
from gps.providers.huggingface.models import HFDataset, HFModel, HFProviderData, HFSpace

logger = logging.getLogger(__name__)


@register("huggingface")
class HuggingFaceProvider(BaseProvider[dict[str, Any], HFProviderData]):
    """
    Hugging Face Hub data provider.

    Fetches models, spaces, and datasets for a given HF username.
    Renders a summary section for the GitHub profile README.
    """

    name = "huggingface"
    display_name = "Hugging Face"

    def __init__(
        self,
        username: str,
        token: str = "",  # nosec B107
        model_count: int = 5,
        space_count: int = 3,
        timeout: int = 15,
        max_retries: int = 3,
    ) -> None:
        self.username = username
        self.model_count = model_count
        self.space_count = space_count
        self._client = HuggingFaceClient(
            token=token,
            timeout=timeout,
            max_retries=max_retries,
        )

    def fetch(self) -> dict[str, Any]:
        """Fetch models, spaces, and datasets from HF Hub."""
        return {
            "models": self._client.get_models(self.username, limit=self.model_count),
            "spaces": self._client.get_spaces(self.username, limit=self.space_count),
            "datasets": self._client.get_datasets(self.username, limit=5),
        }

    def transform(self, raw: dict[str, Any]) -> HFProviderData:
        """Transform raw HF API dicts into Pydantic models."""
        models = []
        for m in raw.get("models", []):
            try:
                models.append(
                    HFModel(
                        model_id=m.get("modelId") or m.get("id", ""),
                        author=m.get("author"),
                        last_modified=m.get("lastModified"),
                        tags=m.get("tags", []),
                        pipeline_tag=m.get("pipeline_tag"),
                        downloads=m.get("downloads", 0),
                        likes=m.get("likes", 0),
                        library_name=m.get("library_name"),
                    )
                )
            except Exception as e:
                logger.debug("Skipping malformed model: %s", e)

        spaces = []
        for s in raw.get("spaces", []):
            try:
                spaces.append(
                    HFSpace(
                        space_id=s.get("id", ""),
                        author=s.get("author"),
                        last_modified=s.get("lastModified"),
                        tags=s.get("tags", []),
                        likes=s.get("likes", 0),
                        sdk=s.get("sdk"),
                    )
                )
            except Exception as e:
                logger.debug("Skipping malformed space: %s", e)

        datasets = []
        for d in raw.get("datasets", []):
            try:
                datasets.append(
                    HFDataset(
                        dataset_id=d.get("id", ""),
                        author=d.get("author"),
                        last_modified=d.get("lastModified"),
                        downloads=d.get("downloads", 0),
                        likes=d.get("likes", 0),
                    )
                )
            except Exception as e:
                logger.debug("Skipping malformed dataset: %s", e)

        data = HFProviderData(
            username=self.username,
            models=models,
            spaces=spaces,
            datasets=datasets,
        )
        data.compute_totals()
        return data

    def validate(self, data: HFProviderData) -> bool:
        return bool(data.models or data.spaces or data.datasets)

    def render(self, data: HFProviderData) -> str:
        """Render Hugging Face section as markdown."""
        lines: list[str] = [
            "### 🤗 Hugging Face Portfolio",
            "",
            f"📊 **{data.total_downloads:,}** total downloads · "
            f"❤️ **{data.total_likes}** total likes",
            "",
        ]

        if data.models:
            lines.append("**Models:**")
            for model in data.models:
                tag = f"[`{model.pipeline_tag}`]" if model.pipeline_tag else ""
                lines.append(
                    f"- **[{model.display_name}]({model.url})** {tag} "
                    f"— 🔽 `{model.downloads:,}` | ❤️ `{model.likes}`"
                )
            lines.append("")

        if data.spaces:
            lines.append("**Spaces:**")
            for space in data.spaces:
                sdk_badge = f"`{space.sdk}`" if space.sdk else ""
                lines.append(
                    f"- **[{space.space_id.split('/')[-1]}]({space.url})** {sdk_badge}"
                    f" — ❤️ `{space.likes}`"
                )
            lines.append("")

        return "\n".join(lines).strip()

    def close(self) -> None:
        self._client.close()

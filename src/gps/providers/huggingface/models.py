"""GPS Hugging Face Provider: Pydantic Data Models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class HFModel(BaseModel):
    """A Hugging Face model card."""

    model_id: str
    author: str | None = None
    sha: str | None = None
    last_modified: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    pipeline_tag: str | None = None
    downloads: int = 0
    likes: int = 0
    library_name: str | None = None

    @property
    def url(self) -> str:
        return f"https://huggingface.co/{self.model_id}"

    @property
    def display_name(self) -> str:
        parts = self.model_id.split("/")
        return parts[-1] if len(parts) > 1 else self.model_id


class HFSpace(BaseModel):
    """A Hugging Face Space."""

    space_id: str
    author: str | None = None
    last_modified: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    likes: int = 0
    sdk: str | None = None

    @property
    def url(self) -> str:
        return f"https://huggingface.co/spaces/{self.space_id}"


class HFDataset(BaseModel):
    """A Hugging Face Dataset."""

    dataset_id: str
    author: str | None = None
    last_modified: datetime | None = None
    downloads: int = 0
    likes: int = 0

    @property
    def url(self) -> str:
        return f"https://huggingface.co/datasets/{self.dataset_id}"


class HFProviderData(BaseModel):
    """Full dataset produced by the Hugging Face provider."""

    username: str
    models: list[HFModel] = Field(default_factory=list)
    spaces: list[HFSpace] = Field(default_factory=list)
    datasets: list[HFDataset] = Field(default_factory=list)
    total_likes: int = 0
    total_downloads: int = 0

    def compute_totals(self) -> None:
        self.total_likes = (
            sum(m.likes for m in self.models)
            + sum(s.likes for s in self.spaces)
            + sum(d.likes for d in self.datasets)
        )
        self.total_downloads = sum(m.downloads for m in self.models) + sum(
            d.downloads for d in self.datasets
        )

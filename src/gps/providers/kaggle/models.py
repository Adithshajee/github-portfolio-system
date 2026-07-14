"""GPS Kaggle Provider: Pydantic Data Models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class KaggleCompetition(BaseModel):
    """A Kaggle competition entry."""

    ref: str  # competition slug
    title: str = ""
    description: str | None = None
    url: str = ""
    category: str | None = None
    reward: str | None = None
    deadline: datetime | None = None
    team_count: int = 0

    @property
    def competition_url(self) -> str:
        return self.url or f"https://www.kaggle.com/c/{self.ref}"


class KaggleNotebook(BaseModel):
    """A Kaggle notebook (kernel)."""

    title: str
    url: str = ""
    votes: int = 0
    total_votes: int = 0
    language: str | None = None

    @property
    def notebook_url(self) -> str:
        return self.url or "https://www.kaggle.com"


class KaggleDataset(BaseModel):
    """A Kaggle dataset."""

    title: str
    url: str = ""
    download_count: int = 0
    vote_count: int = 0
    usability_rating: float = 0.0


class KaggleProviderData(BaseModel):
    """Full dataset produced by the Kaggle provider."""

    username: str
    competitions: list[KaggleCompetition] = Field(default_factory=list)
    notebooks: list[KaggleNotebook] = Field(default_factory=list)
    datasets: list[KaggleDataset] = Field(default_factory=list)
    ranking: int | None = None
    tier: str | None = None  # Novice, Contributor, Expert, Master, Grandmaster

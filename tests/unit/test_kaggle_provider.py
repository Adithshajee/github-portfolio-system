"""Unit tests for the Kaggle Provider."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gps.providers.kaggle.models import KaggleProviderData
from gps.providers.kaggle.provider import KaggleProvider


@pytest.mark.unit
class TestKaggleProvider:
    @patch("gps.providers.kaggle.provider.KaggleClient")
    def test_provider_metadata(self, mock_client: MagicMock) -> None:
        provider = KaggleProvider(username="testuser")
        assert provider.name == "kaggle"
        assert provider.display_name == "Kaggle"

    @patch("gps.providers.kaggle.provider.KaggleClient")
    def test_transform_parses_valid_raw_data(self, mock_client: MagicMock) -> None:
        provider = KaggleProvider(username="testuser")
        raw_data = {
            "competitions": [
                {
                    "ref": "comp-1",
                    "title": "Predict Housing",
                    "description": "regression comp",
                    "url": "https://kaggle.com/c/comp-1",
                    "user_rank": 15,
                    "total_teams": 500,
                }
            ],
            "notebooks": [
                {
                    "ref": "testuser/my-notebook",
                    "title": "EDA Notebook",
                    "url": "https://kaggle.com/code/testuser/my-notebook",
                    "votes": 5,
                    "language": "python",
                }
            ],
            "datasets": [
                {
                    "ref": "testuser/my-dataset",
                    "title": "Housing Dataset",
                    "url": "https://kaggle.com/datasets/testuser/my-dataset",
                    "download_count": 100,
                    "vote_count": 12,
                    "usability_rating": 8.5,
                }
            ],
        }

        data = provider.transform(raw_data)
        assert isinstance(data, KaggleProviderData)
        assert len(data.competitions) == 1
        assert len(data.notebooks) == 1
        assert len(data.datasets) == 1
        assert data.username == "testuser"

    @patch("gps.providers.kaggle.provider.KaggleClient")
    def test_validate_method(self, mock_client: MagicMock) -> None:
        provider = KaggleProvider(username="testuser")

        # Valid: contains at least some notebooks
        raw_data = {
            "notebooks": [{"ref": "n1", "title": "N1", "url": "url"}],
            "competitions": [],
            "datasets": [],
        }
        data = provider.transform(raw_data)
        assert provider.validate(data) is True

        # Invalid: completely empty
        empty_data = provider.transform({"competitions": [], "notebooks": [], "datasets": []})
        assert provider.validate(empty_data) is False

    @patch("gps.providers.kaggle.provider.KaggleClient")
    def test_render_generates_correct_markdown(self, mock_client: MagicMock) -> None:
        provider = KaggleProvider(username="testuser")
        raw_data = {
            "competitions": [
                {
                    "ref": "comp-1",
                    "title": "Predict Housing",
                    "description": "regression comp",
                    "url": "https://kaggle.com/c/comp-1",
                    "user_rank": 15,
                    "total_teams": 500,
                }
            ],
            "notebooks": [
                {
                    "ref": "testuser/my-notebook",
                    "title": "EDA Notebook",
                    "url": "https://kaggle.com/code/testuser/my-notebook",
                    "votes": 5,
                    "language": "python",
                }
            ],
            "datasets": [
                {
                    "ref": "testuser/my-dataset",
                    "title": "Housing Dataset",
                    "url": "https://kaggle.com/datasets/testuser/my-dataset",
                    "download_count": 100,
                    "vote_count": 12,
                    "usability_rating": 8.5,
                }
            ],
        }
        data = provider.transform(raw_data)
        rendered = provider.render(data)

        assert "Kaggle" in rendered
        assert "Predict Housing" in rendered
        assert "EDA Notebook" in rendered

    @patch("gps.providers.kaggle.provider.KaggleClient")
    def test_fetch_invokes_client_methods(self, mock_client_class: MagicMock) -> None:
        mock_client_instance = mock_client_class.return_value
        mock_client_instance.get_competitions.return_value = []
        mock_client_instance.get_notebooks.return_value = []
        mock_client_instance.get_datasets.return_value = []

        provider = KaggleProvider(username="testuser")
        raw = provider.fetch()

        assert "competitions" in raw
        assert "notebooks" in raw
        assert "datasets" in raw
        mock_client_instance.get_competitions.assert_called_once_with("testuser")
        mock_client_instance.get_notebooks.assert_called_once_with("testuser")
        mock_client_instance.get_datasets.assert_called_once_with("testuser")

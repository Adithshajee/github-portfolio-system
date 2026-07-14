"""Unit tests for the Hugging Face Provider."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gps.providers.huggingface.models import HFProviderData
from gps.providers.huggingface.provider import HuggingFaceProvider


@pytest.mark.unit
class TestHuggingFaceProvider:
    def test_provider_metadata(self) -> None:
        provider = HuggingFaceProvider(username="testuser")
        assert provider.name == "huggingface"
        assert provider.display_name == "Hugging Face"

    def test_transform_parses_valid_raw_data(self) -> None:
        provider = HuggingFaceProvider(username="testuser")
        raw_data = {
            "models": [
                {
                    "id": "testuser/my-model",
                    "author": "testuser",
                    "downloads": 100,
                    "likes": 10,
                    "pipeline_tag": "text-generation",
                }
            ],
            "spaces": [
                {
                    "id": "testuser/my-space",
                    "author": "testuser",
                    "likes": 5,
                    "sdk": "streamlit",
                }
            ],
            "datasets": [
                {
                    "id": "testuser/my-dataset",
                    "author": "testuser",
                    "downloads": 50,
                    "likes": 2,
                }
            ],
        }

        data = provider.transform(raw_data)
        assert isinstance(data, HFProviderData)
        assert len(data.models) == 1
        assert len(data.spaces) == 1
        assert len(data.datasets) == 1
        assert data.total_likes == 17  # 10 + 5 + 2
        assert data.total_downloads == 150  # 100 + 50

    def test_validate_method(self) -> None:
        provider = HuggingFaceProvider(username="testuser")

        # Valid: contains at least some models/spaces/datasets
        raw_data = {"models": [{"id": "m1"}], "spaces": [], "datasets": []}
        data = provider.transform(raw_data)
        assert provider.validate(data) is True

        # Invalid: completely empty
        empty_data = provider.transform({"models": [], "spaces": [], "datasets": []})
        assert provider.validate(empty_data) is False

    def test_render_generates_correct_markdown(self) -> None:
        provider = HuggingFaceProvider(username="testuser")
        raw_data = {
            "models": [
                {
                    "id": "testuser/my-model",
                    "author": "testuser",
                    "downloads": 100,
                    "likes": 10,
                }
            ],
            "spaces": [
                {
                    "id": "testuser/my-space",
                    "author": "testuser",
                    "likes": 5,
                    "sdk": "gradio",
                }
            ],
            "datasets": [
                {
                    "id": "testuser/my-dataset",
                    "author": "testuser",
                    "downloads": 50,
                    "likes": 2,
                }
            ],
        }
        data = provider.transform(raw_data)
        rendered = provider.render(data)

        assert "Hugging Face" in rendered
        assert "my-model" in rendered
        assert "my-space" in rendered
        assert "17" in rendered  # total likes
        assert "150" in rendered  # total downloads

    @patch("gps.providers.huggingface.client.HTTPClient.get")
    def test_fetch_invokes_http_client(self, mock_get: MagicMock) -> None:
        provider = HuggingFaceProvider(username="testuser")
        mock_get.return_value = [{"id": "m1"}]

        raw = provider.fetch()
        assert "models" in raw
        assert "spaces" in raw
        assert "datasets" in raw
        assert mock_get.call_count == 3

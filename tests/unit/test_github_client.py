"""
Unit tests for the GitHub API client.

Tests HTTP behavior, error handling, retry logic, ETag caching,
and rate limit handling — all mocked, no live API calls.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

from gps.utils.http import (
    APIError,
    AuthenticationError,
    HTTPClient,
    NetworkError,
    NotFoundError,
    RateLimitError,
)


@pytest.mark.unit
class TestHTTPClientInit:
    def test_init_with_token_sets_auth_header(self) -> None:
        client = HTTPClient(token="ghp_test_token")
        assert "Authorization" in client._client.headers
        assert client._client.headers["Authorization"] == "Bearer ghp_test_token"
        client.close()

    def test_init_without_token_no_auth_header(self) -> None:
        client = HTTPClient()
        assert "Authorization" not in client._client.headers
        client.close()


@pytest.mark.unit
class TestHTTPClientErrorHandling:
    """Test that HTTP status codes raise the correct exceptions."""

    def _make_response(
        self, status: int, body: Any = None, headers: dict[str, str] | None = None
    ) -> MagicMock:
        """Create a mock httpx.Response."""
        mock = MagicMock(spec=httpx.Response)
        mock.status_code = status
        mock.headers = headers or {}
        mock.json.return_value = body or {}
        return mock

    def test_401_raises_authentication_error(self) -> None:
        client = HTTPClient()
        response = self._make_response(401)
        with pytest.raises(AuthenticationError):
            client._handle_response(response, "https://api.test.com/test", None)
        client.close()

    def test_403_rate_limit_raises_rate_limit_error(self) -> None:
        client = HTTPClient()
        response = self._make_response(
            403, headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "9999999999"}
        )
        with pytest.raises(RateLimitError):
            client._handle_response(response, "https://api.test.com/test", None)
        client.close()

    def test_403_forbidden_raises_authentication_error(self) -> None:
        client = HTTPClient()
        response = self._make_response(403, headers={"X-RateLimit-Remaining": "50"})
        with pytest.raises(AuthenticationError):
            client._handle_response(response, "https://api.test.com/test", None)
        client.close()

    def test_404_raises_not_found_error(self) -> None:
        client = HTTPClient()
        response = self._make_response(404)
        with pytest.raises(NotFoundError):
            client._handle_response(response, "https://api.test.com/test", None)
        client.close()

    def test_429_raises_rate_limit_error_with_retry_after(self) -> None:
        client = HTTPClient()
        response = self._make_response(429, headers={"Retry-After": "30"})
        with pytest.raises(RateLimitError) as exc_info:
            client._handle_response(response, "https://api.test.com/test", None)
        assert exc_info.value.retry_after == 30
        client.close()

    def test_500_raises_api_error(self) -> None:
        client = HTTPClient()
        response = self._make_response(500)
        with pytest.raises(APIError) as exc_info:
            client._handle_response(response, "https://api.test.com/test", None)
        assert exc_info.value.status_code == 500
        client.close()

    def test_200_returns_parsed_json(self) -> None:
        client = HTTPClient()
        data = {"login": "testuser", "public_repos": 10}
        response = self._make_response(200, body=data)
        result = client._handle_response(response, "https://api.test.com/test", None)
        assert result == data
        client.close()

    def test_304_returns_cached_data(self) -> None:
        from gps.utils.http import CachedResponse

        client = HTTPClient()
        cached = CachedResponse(etag='"abc123"', data={"cached": True})
        response = self._make_response(304)
        result = client._handle_response(response, "https://api.test.com/test", cached)
        assert result == {"cached": True}
        client.close()

    def test_etag_stored_on_200(self) -> None:
        client = HTTPClient()
        response = self._make_response(
            200,
            body={"login": "testuser"},
            headers={"ETag": '"abc123"'},
        )
        url = "https://api.test.com/users/testuser"
        client._handle_response(response, url, None)
        cached = client._cache.get(url)
        assert cached is not None
        assert cached.etag == '"abc123"'
        client.close()


@pytest.mark.unit
class TestHTTPClientRetry:
    """Test retry behavior on transient failures."""

    def test_timeout_raises_network_error_after_retries(self) -> None:
        client = HTTPClient(max_retries=2, retry_delay=0.01)
        with patch.object(client._client, "get", side_effect=httpx.TimeoutException("timeout")):
            with pytest.raises(NetworkError, match="timed out"):
                client.get("https://api.test.com/test")
        client.close()

    def test_connect_error_raises_network_error(self) -> None:
        client = HTTPClient(max_retries=1, retry_delay=0.01)
        with patch.object(
            client._client, "get", side_effect=httpx.ConnectError("connection refused")
        ):
            with pytest.raises(NetworkError, match="Connection failed"):
                client.get("https://api.test.com/test")
        client.close()

    def test_non_retriable_4xx_does_not_retry(self) -> None:
        """Client errors (4xx < 500) should not be retried."""
        client = HTTPClient(max_retries=3, retry_delay=0.01)

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 401
        mock_response.headers = {}

        call_count = 0

        def mock_get(*args: Any, **kwargs: Any) -> MagicMock:
            nonlocal call_count
            call_count += 1
            return mock_response

        with patch.object(client._client, "get", side_effect=mock_get):
            with pytest.raises(AuthenticationError):
                client.get("https://api.test.com/test")

        assert call_count == 1  # Should NOT retry on 401
        client.close()


@pytest.mark.unit
class TestETagCache:
    def test_cache_set_and_get(self) -> None:
        from gps.utils.http import ETagCache

        cache = ETagCache()
        cache.set("https://example.com", '"etag123"', {"data": 1})
        result = cache.get("https://example.com")
        assert result is not None
        assert result.etag == '"etag123"'
        assert result.data == {"data": 1}

    def test_cache_miss_returns_none(self) -> None:
        from gps.utils.http import ETagCache

        cache = ETagCache()
        assert cache.get("https://missing.com") is None

    def test_cache_clear(self) -> None:
        from gps.utils.http import ETagCache

        cache = ETagCache()
        cache.set("https://example.com", '"etag123"', {})
        cache.clear()
        assert cache.get("https://example.com") is None

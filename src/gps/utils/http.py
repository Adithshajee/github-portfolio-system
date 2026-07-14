"""
GPS Utilities: HTTP Client
──────────────────────────
Production-grade HTTP client built on httpx with:
  - Configurable timeouts
  - Exponential backoff retry
  - ETag/conditional request caching
  - Rate limit detection and handling
  - Structured exception hierarchy
  - Optional Bearer token authentication
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ─── Exception Hierarchy ──────────────────────────────────────────────────────


class GPSHTTPError(Exception):
    """Base class for all GPS HTTP errors."""

    pass


class RateLimitError(GPSHTTPError):
    """Raised when the API rate limit is exceeded."""

    def __init__(self, retry_after: int = 60, message: str = "") -> None:
        self.retry_after = retry_after
        super().__init__(message or f"Rate limit exceeded. Retry after {retry_after}s.")


class AuthenticationError(GPSHTTPError):
    """Raised when API authentication fails (401/403)."""

    pass


class NotFoundError(GPSHTTPError):
    """Raised when the requested resource does not exist (404)."""

    pass


class APIError(GPSHTTPError):
    """Raised for unexpected API errors (5xx, unexpected 4xx)."""

    def __init__(self, status_code: int, message: str = "") -> None:
        self.status_code = status_code
        super().__init__(message or f"API error: HTTP {status_code}")


class NetworkError(GPSHTTPError):
    """Raised for network-level failures (timeout, connection error)."""

    pass


# ─── ETag Cache ───────────────────────────────────────────────────────────────


@dataclass
class CachedResponse:
    """Stores a cached HTTP response with its ETag."""

    etag: str
    data: Any


@dataclass
class ETagCache:
    """In-memory ETag cache for conditional HTTP requests."""

    _store: dict[str, CachedResponse] = field(default_factory=dict)

    def get(self, url: str) -> CachedResponse | None:
        return self._store.get(url)

    def set(self, url: str, etag: str, data: Any) -> None:  # noqa: ANN401
        self._store[url] = CachedResponse(etag=etag, data=data)

    def clear(self) -> None:
        self._store.clear()


# ─── HTTP Client ──────────────────────────────────────────────────────────────


class HTTPClient:
    """
    Production-grade HTTP client with retry, caching, and rate limit handling.

    Args:
        token: Optional Bearer token for authentication.
        timeout: Request timeout in seconds.
        max_retries: Maximum number of retry attempts on transient failures.
        retry_delay: Base delay for exponential backoff (seconds).
        rate_limit_threshold: Minimum remaining rate limit before slowing down.
        user_agent: User-Agent header sent with all requests.
    """

    def __init__(
        self,
        token: str = "",  # nosec B107
        timeout: int = 15,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        rate_limit_threshold: int = 10,
        user_agent: str = "GPS/2.0 (github-portfolio-system)",
    ) -> None:
        self.token = token
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limit_threshold = rate_limit_threshold
        self._cache = ETagCache()

        headers: dict[str, str] = {"User-Agent": user_agent, "Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
            logger.debug("HTTP client initialized with token authentication.")
        else:
            logger.warning(
                "HTTP client initialized WITHOUT authentication. "
                "Rate limits will be significantly lower (60 req/hr for GitHub)."
            )

        self._client = httpx.Client(
            headers=headers,
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
        )

    def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> Any:  # noqa: ANN401
        """
        Perform a GET request with retry, ETag caching, and error handling.

        Args:
            url: Full URL to request.
            params: Query parameters dict.
            extra_headers: Additional headers to merge.

        Returns:
            Parsed JSON response body.

        Raises:
            RateLimitError: On HTTP 429 or exhausted rate limit.
            AuthenticationError: On HTTP 401/403.
            NotFoundError: On HTTP 404.
            APIError: On other 4xx/5xx errors.
            NetworkError: On connection/timeout failures.
        """
        request_headers: dict[str, str] = dict(extra_headers or {})

        # Inject ETag for conditional requests
        cached = self._cache.get(url)
        if cached:
            request_headers["If-None-Match"] = cached.etag

        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug("GET %s (attempt %d/%d)", url, attempt, self.max_retries)
                response = self._client.get(url, params=params, headers=request_headers)
                return self._handle_response(response, url, cached)

            except (RateLimitError, AuthenticationError, NotFoundError) as e:
                # Non-retriable errors
                raise e from None

            except APIError as e:
                # Only retry on 5xx server errors
                if e.status_code < 500:
                    raise e from None
                last_error = e

            except httpx.TimeoutException as e:
                logger.warning(
                    "Request timed out (attempt %d/%d): %s", attempt, self.max_retries, url
                )
                last_error = NetworkError(f"Request timed out after {self.timeout}s: {url}")
                last_error.__cause__ = e

            except httpx.ConnectError as e:
                logger.warning(
                    "Connection failed (attempt %d/%d): %s", attempt, self.max_retries, url
                )
                last_error = NetworkError(f"Connection failed: {url}")
                last_error.__cause__ = e

            except httpx.HTTPError as e:
                logger.warning("HTTP error (attempt %d/%d): %s", attempt, self.max_retries, str(e))
                last_error = NetworkError(f"HTTP error: {e}")
                last_error.__cause__ = e

            if attempt < self.max_retries:
                delay = self.retry_delay * (2 ** (attempt - 1))
                logger.info("Retrying in %.1fs...", delay)
                time.sleep(delay)

        raise last_error or NetworkError(f"Request failed after {self.max_retries} attempts: {url}")

    def _handle_response(
        self,
        response: httpx.Response,
        url: str,
        cached: CachedResponse | None,
    ) -> Any:  # noqa: ANN401
        """Process HTTP response, handling status codes and caching."""
        # 304 Not Modified — return cached data
        if response.status_code == 304 and cached:
            logger.debug("Cache hit (304): %s", url)
            return cached.data

        if response.status_code == 401:
            raise AuthenticationError(
                "Authentication failed. Check your API token (GH_PAT, HF_TOKEN, etc.)."
            )

        if response.status_code == 403:
            # Could be rate limit or forbidden
            remaining = response.headers.get("X-RateLimit-Remaining", "?")
            if remaining == "0":
                retry_after = int(response.headers.get("X-RateLimit-Reset", time.time() + 60))
                wait = max(0, retry_after - int(time.time()))
                raise RateLimitError(retry_after=wait)
            raise AuthenticationError(
                "Access forbidden. Ensure your token has the required scopes."
            )

        if response.status_code == 404:
            raise NotFoundError(f"Resource not found: {url}")

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise RateLimitError(retry_after=retry_after)

        if response.status_code >= 500:
            raise APIError(response.status_code, f"Server error from {url}")

        if response.status_code >= 400:
            raise APIError(response.status_code, f"Client error {response.status_code} from {url}")

        # Success — check rate limit proximity
        remaining = response.headers.get("X-RateLimit-Remaining")
        if remaining is not None and int(remaining) < self.rate_limit_threshold:
            logger.warning(
                "Rate limit low: %s requests remaining. Consider adding a GH_PAT token.",
                remaining,
            )

        # Parse JSON
        data = response.json()

        # Cache ETag if present
        etag = response.headers.get("ETag", "")
        if etag:
            self._cache.set(url, etag, data)
            logger.debug("Cached ETag for: %s", url)

        return data

    def post(self, url: str, json: dict[str, Any]) -> Any:  # noqa: ANN401
        """Perform a POST request (used for GraphQL)."""
        try:
            response = self._client.post(url, json=json)
            return self._handle_response(response, url, None)
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            raise NetworkError(f"Network error on POST to {url}: {e}") from e

    def __enter__(self) -> HTTPClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying httpx client."""
        self._client.close()

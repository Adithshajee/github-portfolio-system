"""
GPS GitHub Device Flow OAuth Authenticator
──────────────────────────────────────────
Implements GitHub Device Authorization Flow (RFC 8628).
"""

from __future__ import annotations

import time
from typing import Any

import httpx

# GitHub CLI Client ID is standard and public for OAuth CLI integrations.
_CLIENT_ID = "178ee8a4fd8c2cfd1e3e"
_DEVICE_CODE_URL = "https://github.com/login/device/code"
_TOKEN_URL = "https://github.com/login/oauth/access_token"  # noqa: S105

# Request scopes needed for full portfolio generation and sync
_SCOPES = "repo,read:user,workflow"


def initiate_device_flow() -> dict[str, Any]:
    """Request a device authorization code from GitHub."""
    payload = {
        "client_id": _CLIENT_ID,
        "scope": _SCOPES,
    }
    headers = {"Accept": "application/json"}

    try:
        from typing import cast

        response = httpx.post(_DEVICE_CODE_URL, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return cast(dict[str, Any], response.json())
    except Exception as e:
        raise RuntimeError(f"Failed to communicate with GitHub login services: {e}") from e


def poll_for_token(device_code: str, interval: int = 5) -> str:
    """Poll the token endpoint until user authorizes or code expires."""
    payload = {
        "client_id": _CLIENT_ID,
        "device_code": device_code,
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
    }
    headers = {"Accept": "application/json"}

    while True:
        try:
            response = httpx.post(_TOKEN_URL, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "access_token" in data:
                return str(data["access_token"])

            error_code = data.get("error")
            if error_code == "authorization_pending":
                # User has not authorized yet, wait and repeat
                time.sleep(interval)
            elif error_code == "slow_down":
                # Adjust polling interval
                interval += 5
                time.sleep(interval)
            elif error_code == "expired_token":
                raise TimeoutError(
                    "The authentication code has expired. Please try logging in again."
                )
            elif error_code == "access_denied":
                raise PermissionError("Access was denied by the user.")
            else:
                desc = data.get("error_description", error_code)
                raise RuntimeError(f"Authentication failed: {desc}")

        except httpx.HTTPError as e:
            raise RuntimeError(f"Connection lost during authentication: {e}") from e

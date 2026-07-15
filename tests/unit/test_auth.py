"""
Unit tests for the GPS secure credentials storage and OAuth device flow.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from gps.auth.device_flow import initiate_device_flow, poll_for_token
from gps.auth.storage import clear_secure_token, get_secure_token, save_secure_token
from gps.cli import main


@pytest.fixture(autouse=True)
def mock_credentials_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fixture to isolate credentials storage to a temporary path during tests."""
    creds_dir = tmp_path / ".config" / "gps"
    creds_file = creds_dir / "credentials.json"
    monkeypatch.setattr("gps.auth.storage._CREDENTIALS_DIR", creds_dir)
    monkeypatch.setattr("gps.auth.storage._CREDENTIALS_FILE", creds_file)
    return creds_file


@pytest.mark.unit
def test_storage_save_load_clear(mock_credentials_file: Path) -> None:
    # Test token is initially None if file doesn't exist
    assert get_secure_token() is None

    # Test saving secure token
    save_secure_token("test-oauth-token")
    assert mock_credentials_file.exists()
    assert get_secure_token() == "test-oauth-token"

    # Test clear secure token
    clear_secure_token()
    assert not mock_credentials_file.exists()
    assert get_secure_token() is None


@pytest.mark.unit
def test_device_flow_initiate(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        url="https://github.com/login/device/code",
        json={
            "device_code": "dev123",
            "user_code": "USER-CODE",
            "verification_uri": "https://github.com/login/device",
            "interval": 5,
        },
    )
    res = initiate_device_flow()
    assert res["device_code"] == "dev123"
    assert res["user_code"] == "USER-CODE"


@pytest.mark.unit
def test_device_flow_polling_success(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        url="https://github.com/login/oauth/access_token",
        json={"access_token": "gho_secrettoken123"},
    )
    token = poll_for_token("dev123", interval=0)
    assert token == "gho_secrettoken123"


@pytest.mark.unit
def test_device_flow_polling_pending_then_success(httpx_mock: Any) -> None:
    # Mock multiple polling attempts: first pending, second success
    httpx_mock.add_response(
        url="https://github.com/login/oauth/access_token",
        json={"error": "authorization_pending"},
    )
    httpx_mock.add_response(
        url="https://github.com/login/oauth/access_token",
        json={"access_token": "gho_polledtoken"},
    )

    with patch("time.sleep") as mock_sleep:
        token = poll_for_token("dev123", interval=0)
        assert token == "gho_polledtoken"
        mock_sleep.assert_called_once()


@pytest.mark.unit
def test_cli_auth_logout(mock_credentials_file: Path) -> None:
    save_secure_token("temp-token")
    runner = CliRunner()
    res = runner.invoke(main, ["auth", "logout"])
    assert res.exit_code == 0
    assert "logged out" in res.output
    assert get_secure_token() is None


@pytest.mark.unit
def test_cli_auth_status_not_logged_in(mock_credentials_file: Path) -> None:
    runner = CliRunner()
    res = runner.invoke(main, ["auth", "status"])
    assert res.exit_code == 0
    assert "Not logged in" in res.output


@pytest.mark.unit
def test_cli_auth_status_success(mock_credentials_file: Path, httpx_mock: Any) -> None:
    save_secure_token("valid-token")
    httpx_mock.add_response(
        url="https://api.github.com/user",
        headers={"X-OAuth-Scopes": "repo, read:user"},
        json={"login": "test-user"},
    )

    runner = CliRunner()
    res = runner.invoke(main, ["auth", "status"])
    assert res.exit_code == 0
    assert "Authenticated with GitHub" in res.output
    assert "test-user" in res.output


@pytest.mark.unit
def test_device_flow_initiate_failure(httpx_mock: Any) -> None:
    httpx_mock.add_exception(Exception("Connection failed"))
    with pytest.raises(RuntimeError) as exc:
        initiate_device_flow()
    assert "Failed to communicate" in str(exc.value)


@pytest.mark.unit
def test_device_flow_polling_slow_down(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        url="https://github.com/login/oauth/access_token",
        json={"error": "slow_down"},
    )
    httpx_mock.add_response(
        url="https://github.com/login/oauth/access_token",
        json={"access_token": "gho_slow"},
    )

    with patch("time.sleep") as mock_sleep:
        token = poll_for_token("dev123", interval=5)
        assert token == "gho_slow"
        mock_sleep.assert_called_once()


@pytest.mark.unit
def test_device_flow_polling_expired(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        url="https://github.com/login/oauth/access_token",
        json={"error": "expired_token"},
    )
    with pytest.raises(TimeoutError) as exc:
        poll_for_token("dev123", interval=0)
    assert "expired" in str(exc.value)


@pytest.mark.unit
def test_device_flow_polling_denied(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        url="https://github.com/login/oauth/access_token",
        json={"error": "access_denied"},
    )
    with pytest.raises(PermissionError) as exc:
        poll_for_token("dev123", interval=0)
    assert "denied" in str(exc.value)


@pytest.mark.unit
def test_device_flow_polling_http_error(httpx_mock: Any) -> None:
    import httpx

    httpx_mock.add_exception(httpx.ConnectError("Connection lost"))
    with pytest.raises(RuntimeError) as exc:
        poll_for_token("dev123", interval=0)
    assert "Connection lost" in str(exc.value)


@pytest.mark.unit
def test_device_flow_polling_generic_error(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        url="https://github.com/login/oauth/access_token",
        json={"error": "custom_error", "error_description": "Custom msg"},
    )
    with pytest.raises(RuntimeError) as exc:
        poll_for_token("dev123", interval=0)
    assert "Custom msg" in str(exc.value)


@pytest.mark.unit
def test_cli_auth_status_invalid_token(mock_credentials_file: Path, httpx_mock: Any) -> None:
    save_secure_token("invalid-token")
    httpx_mock.add_response(
        url="https://api.github.com/user",
        status_code=401,
    )
    runner = CliRunner()
    res = runner.invoke(main, ["auth", "status"])
    assert "invalid or expired" in res.output


@pytest.mark.unit
def test_cli_auth_status_api_failure(mock_credentials_file: Path, httpx_mock: Any) -> None:
    save_secure_token("valid-token")
    httpx_mock.add_exception(Exception("Network error"))
    runner = CliRunner()
    res = runner.invoke(main, ["auth", "status"])
    assert res.exit_code == 1
    assert "Failed to verify" in res.output


@pytest.mark.unit
def test_cli_auth_login_success(mock_credentials_file: Path) -> None:
    with (
        patch("gps.auth.device_flow.initiate_device_flow") as mock_init,
        patch("gps.auth.device_flow.poll_for_token", return_value="polled-token"),
        patch("webbrowser.open"),
    ):
        mock_init.return_value = {
            "user_code": "CODE-123",
            "verification_uri": "https://verification",
            "device_code": "dev-123",
            "interval": 1,
        }
        runner = CliRunner()
        res = runner.invoke(main, ["auth", "login"])
        assert res.exit_code == 0
        assert "Successfully authenticated" in res.output
        assert get_secure_token() == "polled-token"


@pytest.mark.unit
def test_cli_auth_login_failure(mock_credentials_file: Path) -> None:
    with patch("gps.auth.device_flow.initiate_device_flow", side_effect=Exception("API Down")):
        runner = CliRunner()
        res = runner.invoke(main, ["auth", "login"])
        assert res.exit_code == 1
        assert "Authentication failed" in res.output

"""
GPS Secure Authentication Storage
──────────────────────────────────
Handles secure local persistence of GitHub OAuth credentials.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

_CREDENTIALS_DIR = Path.home() / ".config" / "gps"
_CREDENTIALS_FILE = _CREDENTIALS_DIR / "credentials.json"


def get_secure_token() -> str | None:
    """Retrieve the stored GitHub OAuth token from secure storage."""
    if not _CREDENTIALS_FILE.exists():
        # Fall back to env variables for backward compatibility and CI environments
        return os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN")

    try:
        from typing import cast

        data = json.loads(_CREDENTIALS_FILE.read_text(encoding="utf-8"))
        return cast(str | None, data.get("github_token"))
    except Exception:
        return None


def save_secure_token(token: str) -> None:
    """Save the GitHub OAuth token to secure local storage with restricted permissions."""
    _CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)

    # Clean dict payload
    payload = {"github_token": token}
    content = json.dumps(payload, indent=2)

    # Write file with owner-only access permissions (0o600 / Owner Read-Write only)
    if _CREDENTIALS_FILE.exists():
        _CREDENTIALS_FILE.unlink()

    # On POSIX environments, open with mode 0o600
    try:
        fd = os.open(
            str(_CREDENTIALS_FILE),
            os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
            0o600,
        )
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception:
        # Fallback for platforms with limited os.open support
        _CREDENTIALS_FILE.write_text(content, encoding="utf-8")
        try:
            _CREDENTIALS_FILE.chmod(0o600)
        except AttributeError:
            pass


def clear_secure_token() -> None:
    """Clear all stored OAuth credentials from secure storage."""
    if _CREDENTIALS_FILE.exists():
        _CREDENTIALS_FILE.unlink()

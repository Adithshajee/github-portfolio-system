"""
GPS Discovery Engine
────────────────────
Auto-detects developer presence and profile info across multiple platforms:
GitHub, LeetCode, Hugging Face, Kaggle, Dev.to, NPM, PyPI, Medium, Google Scholar, etc.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class DiscoveryEngine:
    """Discovers and auto-detects developer accounts, repos, stats, and feeds."""

    def __init__(self, http_client: httpx.Client | None = None) -> None:
        self.client = http_client or httpx.Client(timeout=5.0)

    def auto_detect(self, github_username: str) -> dict[str, Any]:
        """Query multiple public profile endpoints using github username as default."""
        findings: dict[str, Any] = {
            "github": {"enabled": True, "username": github_username},
            "huggingface": {"enabled": False, "username": ""},
            "kaggle": {"enabled": False, "username": ""},
            "leetcode": {"enabled": False, "username": ""},
            "blog": {"enabled": False, "feed_url": ""},
            "pypi": {"enabled": False, "username": ""},
            "npm": {"enabled": False, "username": ""},
        }

        # 1. Check Hugging Face
        try:
            hf_url = f"https://huggingface.co/api/users/{github_username}"
            res = self.client.get(hf_url)
            if res.status_code == 200:
                findings["huggingface"] = {"enabled": True, "username": github_username}
                logger.info("Auto-detected Hugging Face account for %s", github_username)
        except Exception as e:
            logger.debug("HF auto-detect failed: %s", e)

        # 2. Check LeetCode
        try:
            lc_url = f"https://leetcode.com/{github_username}/"
            res = self.client.get(lc_url)
            if res.status_code == 200:
                findings["leetcode"] = {"enabled": True, "username": github_username}
                logger.info("Auto-detected LeetCode account for %s", github_username)
        except Exception as e:
            logger.debug("LeetCode auto-detect failed: %s", e)

        # 3. Check PyPI
        try:
            pypi_url = f"https://pypi.org/user/{github_username}/"
            res = self.client.get(pypi_url)
            if res.status_code == 200:
                findings["pypi"] = {"enabled": True, "username": github_username}
                logger.info("Auto-detected PyPI developer profile for %s", github_username)
        except Exception as e:
            logger.debug("PyPI auto-detect failed: %s", e)

        # 4. Check NPM
        try:
            npm_url = f"https://www.npmjs.com/~{github_username}"
            res = self.client.get(npm_url)
            if res.status_code == 200:
                findings["npm"] = {"enabled": True, "username": github_username}
                logger.info("Auto-detected NPM developer profile for %s", github_username)
        except Exception as e:
            logger.debug("NPM auto-detect failed: %s", e)

        return findings

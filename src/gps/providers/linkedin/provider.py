"""
GPS LinkedIn Provider (Stub)
──────────────────────────────
LinkedIn's official API has strict access restrictions that prevent
automated profile data retrieval for most use cases.

Status: MANUAL UPDATE ONLY

Reasons:
  - LinkedIn's API requires explicit approval for data access
  - The Consumer API (r_liteprofile, r_emailaddress) was deprecated in 2021
  - The Member Data Portability API is not available for automation
  - Scraping LinkedIn violates their Terms of Service

Recommended Approach:
  Maintain your LinkedIn highlights manually in profile/README.md.
  See docs/providers/linkedin.md for the recommended manual update workflow.

Future:
  If LinkedIn releases a public API suitable for this use case,
  this stub will be upgraded to a full provider.
  Watch: https://developer.linkedin.com/
"""

from __future__ import annotations

import logging
from typing import Any

from gps.providers.base import BaseProvider, register

logger = logging.getLogger(__name__)


@register("linkedin")
class LinkedInProvider(BaseProvider[dict[str, Any], dict[str, Any]]):
    """
    LinkedIn provider stub.

    Always returns empty data with a clear explanation.
    The provider is registered to ensure consistent CLI behavior
    (e.g., 'gps status' shows LinkedIn as 'manual only').
    """

    name = "linkedin"
    display_name = "LinkedIn"

    def __init__(self, **_: object) -> None:
        pass

    def fetch(self) -> dict[str, Any]:
        logger.info(
            "LinkedIn provider: Manual updates only. See docs/providers/linkedin.md for guidance."
        )
        return {}

    def transform(self, raw: dict[str, Any]) -> dict[str, Any]:
        return {}

    def validate(self, data: dict[str, Any]) -> bool:
        return False  # Always false — triggers graceful empty output

    def render(self, data: dict[str, Any]) -> str:
        return "<!-- GPS: LinkedIn data requires manual update. See docs/providers/linkedin.md -->"

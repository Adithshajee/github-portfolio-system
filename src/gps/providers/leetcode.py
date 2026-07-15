"""
GPS LeetCode Provider
─────────────────────
Fetches solved problems and ranking statistics from LeetCode.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel

from gps.providers.base import BaseProvider, register
from gps.utils.http import HTTPClient

logger = logging.getLogger(__name__)


class LeetCodeData(BaseModel):
    username: str
    total_solved: int = 0
    easy_solved: int = 0
    medium_solved: int = 0
    hard_solved: int = 0
    acceptance_rate: float = 0.0
    ranking: int = 0


@register("leetcode")
class LeetCodeProvider(BaseProvider[dict[str, Any], LeetCodeData]):
    name = "leetcode"
    display_name = "LeetCode"

    def __init__(self, username: str) -> None:
        self.username = username
        self._http = HTTPClient(user_agent="GPS/3.0")

    def fetch(self) -> dict[str, Any]:
        from typing import cast

        url = f"https://leetcode-stats-api.herokuapp.com/{self.username}"
        try:
            return cast(dict[str, Any], self._http.get(url))
        except Exception as e:
            logger.warning("Failed to fetch LeetCode statistics: %s.", e)
            return {"status": "error", "message": str(e)}

    def transform(self, raw: dict[str, Any]) -> LeetCodeData:
        if raw.get("status") != "success":
            return LeetCodeData(username=self.username)
        return LeetCodeData(
            username=self.username,
            total_solved=raw.get("totalSolved", 0),
            easy_solved=raw.get("easySolved", 0),
            medium_solved=raw.get("mediumSolved", 0),
            hard_solved=raw.get("hardSolved", 0),
            acceptance_rate=raw.get("acceptanceRate", 0.0),
            ranking=raw.get("ranking", 0),
        )

    def validate(self, data: LeetCodeData) -> bool:
        return data.total_solved > 0

    def render(self, data: LeetCodeData) -> str:
        return (
            f"### 💻 LeetCode Stats\n\n"
            f"- **User:** [{data.username}](https://leetcode.com/{data.username}/)\n"
            f"- **Rank:** `{data.ranking:,}`\n"
            f"- **Solved Problems:** `{data.total_solved}` "
            f"(🟢 `{data.easy_solved}` | 🟡 `{data.medium_solved}` | 🔴 `{data.hard_solved}`)\n"
            f"- **Acceptance Rate:** `{data.acceptance_rate}%`"
        )

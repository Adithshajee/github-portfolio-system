#!/usr/bin/env python3
# mypy: ignore-errors
"""
automation/update_readme.py — DEPRECATED COMPATIBILITY SHIM
════════════════════════════════════════════════════════════

⚠️  DEPRECATION WARNING: This file is preserved for backwards compatibility
    with existing GitHub Actions workflows and documentation references.
    It will be REMOVED in GPS v3.0.

This script now delegates to the GPS v2 engine (src/gps/).

Migration:
    OLD: python automation/update_readme.py [--dry-run]
    NEW: gps run [--dry-run]

    OLD: from automation.update_readme import fetch_latest_repos, format_repos_markdown
    NEW: from gps.providers.github.provider import GitHubProvider

Upgrade guide: https://adithshajee.github.io/github-portfolio-system/setup
"""

from __future__ import annotations

import sys
import warnings

warnings.warn(
    "\n"
    "⚠️  automation/update_readme.py is DEPRECATED as of GPS v2.0.\n"
    "    This shim will be removed in GPS v3.0.\n"
    "    \n"
    "    Migration: Replace `python automation/update_readme.py` with `gps run`\n"
    "    See: https://adithshajee.github.io/github-portfolio-system/setup\n",
    DeprecationWarning,
    stacklevel=2,
)

# ─── Backwards-compatible API (delegates to GPS v2) ───────────────────────────
# These functions are preserved so any code that imports from this module
# continues to work during the transition period.

try:
    from gps.config import load_config
    from gps.providers.github.client import GitHubClient
    from gps.providers.github.models import GitHubRepo
    from gps.providers.github.provider import GitHubProvider

    _CONFIG = load_config()
    _USERNAME = _CONFIG.username or "Adithshajee"

    def fetch_latest_repos(username: str) -> list[dict]:
        """
        DEPRECATED: Use gps.providers.github.provider.GitHubProvider instead.

        Fetch top 5 non-fork repositories for a user.
        """
        warnings.warn(
            "fetch_latest_repos() is deprecated. Use GitHubProvider instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        client = GitHubClient(token=_CONFIG.github_token)
        raw = client.get_repos(username, per_page=20)
        return [r for r in raw if not r.get("fork") and r.get("name") != username][:5]

    def format_repos_markdown(repos: list[dict]) -> str:
        """
        DEPRECATED: Use gps.providers.github.provider.GitHubProvider.render() instead.

        Format repository list as markdown.
        """
        warnings.warn(
            "format_repos_markdown() is deprecated. Use GitHubProvider.render() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        if not repos:
            return "* No recent repositories found or API rate limit exceeded."

        md = "### 📂 Active Projects & Repositories\n\n"
        for repo in repos:
            name = repo.get("name", "unknown")
            url = repo.get("html_url", "")
            desc = repo.get("description") or "No description provided."
            stars = repo.get("stargazers_count", 0)
            forks = repo.get("forks_count", 0)
            updated = (repo.get("updated_at") or "")[:10]
            md += f"- **[{name}]({url})** - *Updated {updated}*\n"
            md += f"  > {desc}\n"
            md += f"  > 🌟 `{stars}` | 🍴 `{forks}`\n\n"
        return md.strip()

except ImportError:
    # GPS v2 package not installed — provide minimal standalone implementations
    # so the script can still function as a last resort fallback.
    import json
    import re
    import urllib.request

    _USERNAME = "Adithshajee"

    def fetch_latest_repos(username: str) -> list[dict]:  # type: ignore[misc]
        """Fallback: fetch repos directly (minimal, no auth, no retry)."""
        req = urllib.request.Request(
            f"https://api.github.com/users/{username}/repos?sort=updated&per_page=20",
            headers={"User-Agent": "GPS-compat-shim/1.0"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                repos = json.loads(response.read().decode())
                return [r for r in repos if not r.get("fork") and r.get("name") != username][:5]
        except Exception as e:
            print(f"Error fetching repos: {e}", file=sys.stderr)
            return []

    def format_repos_markdown(repos: list[dict]) -> str:  # type: ignore[misc]
        """Fallback: format repos as markdown."""
        if not repos:
            return "* No recent repositories found."
        md = "### 📂 Active Projects & Repositories\n\n"
        for repo in repos:
            name = repo.get("name", "")
            url = repo.get("html_url", "")
            desc = repo.get("description") or "No description provided."
            stars = repo.get("stargazers_count", 0)
            forks = repo.get("forks_count", 0)
            updated = (repo.get("updated_at") or "")[:10]
            md += f"- **[{name}]({url})** - *Updated {updated}*\n"
            md += f"  > {desc}\n  > 🌟 `{stars}` | 🍴 `{forks}`\n\n"
        return md.strip()


def _update_readme_legacy(readme_path: str, repos_markdown: str, dry_run: bool = False) -> bool:
    """Legacy README update function — kept for backwards compatibility."""
    import re
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: {readme_path} not found.", file=sys.stderr)
        return False

    pattern = r"<!-- REPOS_START -->.*?<!-- REPOS_END -->"
    replacement = f"<!-- REPOS_START -->\n\n{repos_markdown}\n\n<!-- REPOS_END -->"

    if not re.search(pattern, content, re.DOTALL):
        new_content = content + "\n\n" + replacement
    else:
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    if dry_run:
        print("\n=== DRY RUN ===\n", repos_markdown, "\n===============\n")
        return True

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Updated {readme_path}")
    return True


# ─── Entry point (legacy) ─────────────────────────────────────────────────────

if __name__ == "__main__":
    print(
        "\n⚠️  WARNING: You are using the deprecated automation/update_readme.py\n"
        "   Please migrate to: gps run\n"
        "   See: https://adithshajee.github.io/github-portfolio-system/setup\n",
        file=sys.stderr,
    )

    # Try to delegate to the new GPS engine
    try:
        from gps.cli import main as gps_main
        sys.argv = ["gps", "run"] + (["--dry-run"] if "--dry-run" in sys.argv else [])
        gps_main(standalone_mode=True)
    except ImportError:
        # Fallback to legacy behaviour
        is_dry_run = "--dry-run" in sys.argv
        readme_path = "profile/README.md"
        repos = fetch_latest_repos(_USERNAME)
        repos_md = format_repos_markdown(repos)
        success = _update_readme_legacy(readme_path, repos_md, dry_run=is_dry_run)
        sys.exit(0 if success else 1)

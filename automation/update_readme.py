#!/usr/bin/env python3
import json
import re
import sys
import urllib.request
from datetime import datetime

# Enforce UTF-8 output encoding for consoles that do not support unicode natively
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


USER_NAME = "Adithshajee"
README_PATH = "profile/README.md"
API_URL = f"https://api.github.com/users/{USER_NAME}/repos?sort=updated&per_page=10"


def fetch_latest_repos(username):
    """Fetch the latest active, non-fork repositories from GitHub API."""
    print(f"Fetching repositories for user: {username}...")
    req = urllib.request.Request(
        f"https://api.github.com/users/{username}/repos?sort=updated&per_page=20",
        headers={"User-Agent": "GitHub-Portfolio-System-Updater"},
    )
    try:
        with urllib.request.urlopen(req) as response:
            repos = json.loads(response.read().decode())
            # Filter out forks and draft/private repos if any
            non_forks = [
                repo
                for repo in repos
                if not repo.get("fork") and repo.get("name") != username
            ]
            return non_forks[:5]  # Get top 5 repos
    except Exception as e:
        print(f"Error fetching repos: {e}")
        return []


def format_repos_markdown(repos):
    """Format the list of repositories into a clean markdown format."""
    if not repos:
        return "* No recent repositories found or API rate limit exceeded."

    md = "### 📂 Active Projects & Repositories\n\n"
    for repo in repos:
        name = repo.get("name")
        url = repo.get("html_url")
        desc = repo.get("description") or "No description provided."
        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        updated = repo.get("updated_at")[:10]

        md += f"- **[{name}]({url})** - *Updated {updated}*\n"
        md += f"  > {desc}\n"
        md += f"  > 🌟 `{stars}` | 🍴 `{forks}`\n\n"
    return md.strip()


def update_readme(readme_path, repos_markdown, dry_run=False):
    """Update the target README file with formatting blocks."""
    print(f"Reading target file: {readme_path}")
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: {readme_path} not found.")
        return False

    pattern = r"<!-- REPOS_START -->.*?<!-- REPOS_END -->"
    replacement = f"<!-- REPOS_START -->\n\n{repos_markdown}\n\n<!-- REPOS_END -->"

    if not re.search(pattern, content, re.DOTALL):
        print("Warning: Repos markers not found. Appending to end of file.")
        new_content = content + "\n\n" + replacement
    else:
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    if dry_run:
        print("\n=== DRY RUN MODE ===")
        print("Generated Markdown Content:")
        print(repos_markdown)
        print("====================\n")
        return True

    print(f"Writing updates to {readme_path}...")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Update complete!")
    return True


if __name__ == "__main__":
    is_dry_run = "--dry-run" in sys.argv
    repos = fetch_latest_repos(USER_NAME)
    repos_md = format_repos_markdown(repos)
    success = update_readme(README_PATH, repos_md, dry_run=is_dry_run)
    sys.exit(0 if success else 1)

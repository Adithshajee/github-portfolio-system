# Troubleshooting Guide

Here are common issues and error resolutions.

## 1. RateLimitError: Rate limit exceeded
**Cause:** The GitHub API limit of 60 requests per hour for unauthenticated users has been exceeded.
**Fix:** Set the `GH_PAT` environment variable with a GitHub Personal Access Token to increase the limit to 5000 requests per hour.

## 2. Invalid syntax errors during installation
**Cause:** Using an outdated Python version (GPS requires Python >= 3.10) or setuptools cache.
**Fix:** Upgrade Python to 3.10+ and install package dependencies in a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

# Setup Guide

Follow this guide to set up the GitHub Portfolio System (GPS) for your personal profile.

---

## Prerequisites

Before configuring GPS, ensure you have:
1.  A GitHub Account with a repository named `<your-username>` (if deploying as your main profile README) or `github-portfolio-system`.
2.  Python 3.10 or higher installed locally.
3.  An optional WakaTime account (if you wish to track coding stats).

---

## 1. Local Initialization

Clone this repository to your local system:

```bash
git clone https://github.com/Adithshajee/github-portfolio-system.git
cd github-portfolio-system
```

Install local development and static documentation requirements:

```bash
pip install -r requirements.txt
```

---

## 2. Configuring Secrets on GitHub

To support the automation engine (such as updating WakaTime statistics or pulling metrics graphs), configure the following repository secrets:

1.  Navigate to your repository on GitHub.
2.  Go to **Settings** > **Secrets and variables** > **Actions**.
3.  Click **New repository secret**.
4.  Add the following secrets:
    *   `WAKATIME_API_KEY`: Your private WakaTime API key (found in WakaTime account settings).
    *   `GH_PAT` *(Optional)*: A Personal Access Token with `repo` scopes if you want to pull statistics from private repositories.

---

## 3. Local Verification

To run a dry run of the automation scripts locally:

```bash
python automation/update_readme.py --dry-run
```

To run the validation test suite:

```bash
python -m unittest tests/test_validation.py
```

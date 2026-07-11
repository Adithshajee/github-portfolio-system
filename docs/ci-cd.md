# CI/CD Workflows

This document describes the automated integration and deployment workflows configured in the system.

---

## 1. Overview of Workflows

The automation in GPS is managed through YAML configuration files located in [workflows](file:///d:/github-portfolio-system/.github/workflows).

| Workflow Name | Trigger Frequency | Purpose |
| :--- | :--- | :--- |
| **Contribution Snake** | Daily (Cron) & Push | Generates a 3D/2D grid animation of contribution history. |
| **Profile Metrics** | Daily (Cron) & Push | Renders languages, achievements, and code stats. |
| **README Updater** | Hourly/Daily (Cron) | Runs the Python automation script to update WakaTime/repository logs. |
| **CodeQL Security Analysis** | Weekly & PR | Code vulnerability scanning. |
| **Release & Changelog** | Push to `main` | automates release tagging and updates `CHANGELOG.md`. |

---

## 2. CI Quality Gates

Every pull request runs standard validation checks:
1.  **Format Check**: Ensures Markdown files adhere to structural standards.
2.  **Linting**: Runs checks on GitHub Actions syntax.
3.  **Unit Tests**: Runs the `tests/test_validation.py` script.

If any check fails, merging is blocked to maintain repository health.

---

## 3. Customizing the Actions

To alter the schedule or output directories of the SVGs, edit the respective workflow file. For instance, in `.github/workflows/snake.yml`, you can customize the colors of the snake:

```yaml
- name: generate-snake-game-from-github-contribution-grid
  uses: platane/snk@v3
  with:
    github_user_name: ${{ github.repository_owner }}
    outputs: |
      dist/github-contribution-grid-snake.svg
      dist/github-contribution-grid-snake-dark.svg?palette=github-dark
```

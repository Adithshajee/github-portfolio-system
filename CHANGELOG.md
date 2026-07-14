# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] — 2026-07-14

### 🚀 Major Release — Developer Identity Platform

This release is a complete architectural redesign of GPS from a single-script automation tool into a production-grade, extensible **Developer Identity Platform**.

### Added
- **`src/gps/` Python package** — full package with `src` layout, installable via `pip install -e .`
- **Plugin-based Provider System** — `BaseProvider` ABC with `fetch()`, `transform()`, `validate()`, `render()` pipeline and self-registering `@register()` decorator
- **GitHub Provider** — REST v3 (repos, user profile) + GraphQL v4 (pinned repos), ETag caching, pagination, unauthenticated fallback
- **Hugging Face Provider** — full implementation for models, spaces, datasets; disabled by default
- **Kaggle Provider** — full implementation for competitions, notebooks, datasets; disabled by default
- **LinkedIn Provider stub** — clearly documented limitation with manual update guidance
- **`HTTPClient`** (`httpx`) — configurable timeout, exponential backoff retry, ETag caching, rate limit detection, structured exception hierarchy (`RateLimitError`, `AuthenticationError`, `NotFoundError`, `APIError`, `NetworkError`)
- **`gps.yml` configuration** — Pydantic Settings-backed platform config with env var overrides
- **Click CLI** — `gps run`, `gps validate`, `gps status`, `gps export` commands with Rich output
- **`pyproject.toml`** — full project definition with pinned deps, tool configuration (ruff, mypy, pytest, bandit, coverage)
- **`Makefile`** — 15 developer tasks: `make test`, `make ci`, `make docs`, `make run`, etc.
- **Comprehensive test suite** — pytest with mocking, unit tests, integration tests, edge cases; 80%+ coverage target
- **7th GitHub Actions workflow** — `ci.yml`: lint, typecheck, security, Python 3.10/3.11/3.12 matrix
- **`docs/assets/custom.css`** — fixes silent MkDocs build error (file was referenced but missing)
- **`CODEOWNERS`** — automatic review assignment for all PRs
- **`.editorconfig`** — consistent formatting across editors
- **`.pre-commit-config.yaml`** — ruff, isort, mypy, bandit, yamllint, general hooks
- **`.gitattributes`** — LF enforcement, binary file handling
- **MkDocs Material** upgrade — dark/light mode toggle, Mermaid diagrams, code copy buttons, Inter/JetBrains Mono fonts

### Changed
- `automation/update_readme.py` is now a **deprecated compatibility shim** that delegates to the GPS v2 engine; will be removed in v3.0
- `requirements.txt` is now a backwards-compatible shim pointing to `pyproject.toml`
- All 6 GitHub Actions workflows upgraded: concurrency control, pip caching, proper git bot identity, job summaries, only commit when changes exist
- `lowlighter/metrics@latest` pinned to commit SHA (security: prevents supply chain attacks)
- `release.yml` uses Python-based CHANGELOG parser instead of fragile `sed` command
- Both issue templates upgraded from `.md` to structured `.yml` GitHub Forms
- `CONTRIBUTING.md` expanded to full developer guide with provider addition tutorial
- `SECURITY.md` fixed: version table was logically inverted; now correct + comprehensive
- `profile/README.md`: fixed 2 broken project links (california-housing-production and bse-macro-sector-analyzer both had wrong URLs)

### Fixed
- **Bug**: `API_URL` constant in `update_readme.py` was defined but never used (dead code)
- **Bug**: `from datetime import datetime` and `import urllib.parse` were unused imports
- **Bug**: No timeout on HTTP requests (could hang GitHub Actions indefinitely)
- **Bug**: No authentication on GitHub API (hit 60 req/hr rate limit in CI)
- **Bug**: `mike` used in `deploy_docs.yml` but not in `requirements.txt` (silent fallback)
- **Bug**: `git commit ... || exit 0` in workflows silently swallowed real failures
- **Bug**: `release.yml` `sed` command produced empty release notes on first run
- **Bug**: `docs/assets/custom.css` referenced in `mkdocs.yml` but file did not exist
- **Security**: `lowlighter/metrics@latest` floating tag replaced with pinned SHA

### Removed
- Nothing removed in v2.0 (backwards compatibility maintained via shim in `automation/`)

---

## [1.0.0] — 2026-07-11

### Added
- Initial directory structure: `.github/`, `automation/`, `branding/`, `docs/`, `profile/`, `prompts/`, `templates/`, `tests/`, `assets/`
- `automation/update_readme.py` — Python script to fetch top 5 repos and update profile README
- `tests/test_validation.py` — basic unittest validation suite
- 6 GitHub Actions workflows: `readme.yml`, `metrics.yml`, `snake.yml`, `deploy_docs.yml`, `release.yml`, `codeql.yml`
- `profile/README.md` — initial GitHub profile README
- MkDocs documentation site with Material theme
- Brand guide and assets guide
- Issue templates, PR template, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md`, `LICENSE`

---

[2.0.0]: https://github.com/Adithshajee/github-portfolio-system/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/Adithshajee/github-portfolio-system/releases/tag/v1.0.0

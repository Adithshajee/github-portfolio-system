# Contributing to GitHub Portfolio System (GPS)

Thank you for contributing to GPS! This guide covers everything you need to get from zero to a merged pull request.

---

## 🧭 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Making Changes](#making-changes)
- [Code Quality](#code-quality)
- [Testing](#testing)
- [Commit Convention](#commit-convention)
- [Pull Request Process](#pull-request-process)

---

## 📋 Code of Conduct

This project follows the [Contributor Covenant v2.1](CODE_OF_CONDUCT.md). By participating, you agree to uphold these standards.

---

## 🛠️ Development Setup

### Requirements

- Python 3.10 or higher
- Git

### Steps

```bash
# 1. Fork & clone
git clone https://github.com/YOUR_USERNAME/github-portfolio-system.git
cd github-portfolio-system

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# 3. Install all dev dependencies and pre-commit hooks
make install-dev
# OR: pip install -e ".[dev]" && pre-commit install

# 4. Verify setup
make ci
```

---

## 📁 Project Structure

The GPS Python package lives at `src/gps/`. New features go there, not in `automation/` (deprecated v1 layer).

```
src/gps/
├── providers/          # Add new providers here
│   ├── base.py         # Abstract base — all providers implement this
│   ├── github/         # GitHub provider (reference implementation)
│   ├── huggingface/    # Hugging Face provider
│   └── kaggle/         # Kaggle provider
├── utils/              # Shared utilities (http, logging, validators)
├── engine.py           # Core orchestration
├── renderer.py         # Markdown/JSON rendering
├── config.py           # Pydantic configuration
└── cli.py              # Click CLI
```

---

## 🔌 Adding a New Provider

1. Create `src/gps/providers/<name>/` with `__init__.py`, `client.py`, `models.py`, `provider.py`
2. Implement `BaseProvider` — all 4 methods: `fetch()`, `transform()`, `validate()`, `render()`
3. Decorate with `@register("<name>")`
4. Add `enabled: false` settings to `gps.yml`
5. Import in `src/gps/providers/__init__.py`
6. Add tests in `tests/unit/test_<name>_client.py`
7. Add docs in `docs/providers/<name>.md`

See `src/gps/providers/github/` as the reference implementation.

---

## ✅ Code Quality

All code must pass these checks before merging:

```bash
make lint        # ruff linting
make format      # ruff format + isort
make typecheck   # mypy strict mode
make security    # bandit security scan
make test        # pytest suite
```

Or run everything at once:

```bash
make ci
```

Pre-commit hooks run automatically on `git commit`.

---

## 🧪 Testing

- All new code must have tests in `tests/unit/` or `tests/integration/`
- API calls must be mocked — no live network calls in tests
- Coverage target: ≥ 80%

```bash
make test        # Run unit + integration tests
make coverage    # Run with HTML coverage report
```

---

## 📝 Commit Convention

GPS uses [Conventional Commits](https://www.conventionalcommits.org/):

| Type | Example |
|------|---------|
| `feat` | `feat(github): add GraphQL pinned repos support` |
| `fix` | `fix(renderer): handle missing README markers correctly` |
| `docs` | `docs(setup): add Kaggle provider setup guide` |
| `test` | `test(cli): add dry-run mode unit tests` |
| `chore` | `chore(deps): bump httpx to 0.27.1` |
| `refactor` | `refactor(engine): extract provider loop into method` |
| `ci` | `ci(workflows): add Python 3.12 to test matrix` |

---

## 🔀 Pull Request Process

1. Create a branch: `git checkout -b feat/your-feature`
2. Make changes with tests and documentation
3. Run `make ci` — all checks must pass
4. Open a PR with a descriptive title (conventional commits format)
5. Fill in the PR template completely
6. Wait for review — CODEOWNERS are assigned automatically

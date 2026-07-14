# GitHub Portfolio System (GPS) v2

[![CI](https://img.shields.io/github/actions/workflow/status/Adithshajee/github-portfolio-system/ci.yml?branch=main&label=CI&style=flat-square&logo=github-actions&logoColor=white)](https://github.com/Adithshajee/github-portfolio-system/actions/workflows/ci.yml)
[![CodeQL](https://img.shields.io/github/actions/workflow/status/Adithshajee/github-portfolio-system/codeql.yml?branch=main&label=CodeQL&style=flat-square&logo=github&logoColor=white)](https://github.com/Adithshajee/github-portfolio-system/security/code-scanning)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![Docs](https://img.shields.io/badge/Docs-MkDocs%20Material-526CFE?style=flat-square&logo=materialformkdocs&logoColor=white)](https://adithshajee.github.io/github-portfolio-system/)

> A production-grade **Developer Identity Platform** for automating, standardizing, and scaling your developer presence across GitHub, Hugging Face, Kaggle, and beyond.

---

## 🚀 What is GPS?

GPS (GitHub Portfolio System) is an open-source automation platform that keeps your GitHub profile README, documentation site, and developer identity up-to-date — without manual intervention.

**Architecture:**
```
Developer Identity Platform
│
├── Core Engine (src/gps/)
│   ├── Configuration (Pydantic Settings)
│   ├── Plugin-based Provider System
│   ├── Rendering Engine (Jinja2 + Markdown)
│   └── Click CLI (gps run / validate / status)
│
├── Providers
│   ├── ✅ GitHub (REST v3 + GraphQL v4)
│   ├── ✅ Hugging Face Hub (disabled by default)
│   ├── ✅ Kaggle (disabled by default)
│   └── 📋 LinkedIn (manual only — API restricted)
│
├── Outputs
│   ├── GitHub Profile README (primary)
│   ├── JSON data export (optional)
│   └── HTML export (planned)
│
└── Automation
    ├── 6 GitHub Actions workflows
    ├── Pre-commit hooks (ruff, mypy, bandit)
    └── MkDocs documentation site
```

---

## ⚡ Quick Start

```bash
# Clone
git clone https://github.com/Adithshajee/github-portfolio-system.git
cd github-portfolio-system

# Install
pip install -e ".[dev]"

# Configure (edit gps.yml with your username)
# Set your GitHub token: export GH_PAT=ghp_your_token

# Validate setup
gps validate

# Preview output (no file writes)
gps run --dry-run

# Run for real
gps run
```

**Full setup guide:** [docs/setup.md](docs/setup.md)

---

## 🏗️ Repository Structure

```
github-portfolio-system/
├── src/gps/              # GPS Python package (v2 engine)
│   ├── providers/        # GitHub, HuggingFace, Kaggle, LinkedIn
│   ├── utils/            # HTTP client, logging, validators
│   ├── engine.py         # Core orchestration
│   ├── renderer.py       # Markdown/JSON rendering
│   ├── config.py         # Pydantic configuration
│   └── cli.py            # Click CLI
├── tests/                # pytest test suite (unit + integration)
├── docs/                 # MkDocs Material documentation
├── profile/              # Profile README source
├── automation/           # [DEPRECATED v1 compatibility layer]
├── templates/            # Reusable repo templates
├── .github/workflows/    # 7 GitHub Actions workflows
├── gps.yml               # Platform configuration
└── pyproject.toml        # Project definition + tool config
```

---

## 📋 CLI Reference

```bash
gps run [--dry-run] [--provider NAME] [--config PATH] [-v]
gps validate [--config PATH]
gps status [--config PATH]
gps export --format [json|html]
gps --version
```

---

## 🔌 Provider Status

| Provider | Status | Auth Required | Notes |
|----------|--------|---------------|-------|
| **GitHub** | ✅ Active | `GH_PAT` (optional, recommended) | REST v3 + GraphQL v4 |
| **Hugging Face** | ✅ Ready | `HF_TOKEN` | Disabled by default |
| **Kaggle** | ✅ Ready | `KAGGLE_KEY` + `KAGGLE_USERNAME` | Disabled by default |
| **LinkedIn** | 📋 Manual | N/A | API restricted by LinkedIn |

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full developer guide.

Quick checklist:
1. Install dev dependencies: `make install-dev`
2. Run tests: `make test`
3. Run quality checks: `make quality`
4. Submit a PR with Conventional Commits

---

## 📜 License

MIT — see [LICENSE](LICENSE).

---

<p align="center">
  <a href="https://adithshajee.github.io/github-portfolio-system/">📖 Documentation</a> ·
  <a href="https://github.com/Adithshajee/github-portfolio-system/issues">🐛 Issues</a> ·
  <a href="CHANGELOG.md">📋 Changelog</a>
</p>
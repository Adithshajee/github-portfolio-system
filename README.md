# GitHub Portfolio System (GPS)

[![GitHub License](https://img.shields.io/github/license/Adithshajee/github-portfolio-system?style=flat-square)](LICENSE)
[![Validation Check](https://img.shields.io/github/actions/workflow/status/Adithshajee/github-portfolio-system/codeql.yml?branch=main&label=security&style=flat-square)](https://github.com/Adithshajee/github-portfolio-system/actions)

A production-grade developer platform and engineering standard for building, automating, documenting, and maintaining professional GitHub portfolios and repositories.

---

## 🏗️ Repository Architecture

GPS is structured into modular layers to isolate developer assets from automation schedules and templates:

```
github-portfolio-system/
├── .github/                 # GitHub Workflows & Issue/PR templates
├── assets/                  # Rendered SVGs and images
├── automation/              # Python automation update scripts
├── branding/                # Personal styling & palette guides
├── docs/                    # MkDocs documentation site source
├── profile/                 # Profile README source file
├── prompts/                 # AI prompts for visual brand assets
├── templates/               # Reusable project README & architecture templates
└── tests/                   # Python quality validation tests
```

---

## 🚀 Key Modules

*   **Automation Layer**: Automated contribution snake animations (`platane/snk`) and full-scale account performance metrics (`lowlighter/metrics`).
*   **Recruiter-Grade Profile**: A structured developer summary emphasizing skills, certifications, and active repos without clutter.
*   **Standardized Governance**: Built-in Issue Templates, Pull Request Template, CodeQL, and Dependabot.
*   **Quality Assurance**: Integrated test suites to dry-run changes locally before committing.

---

## 🛠️ Getting Started

### Local Setup
1. Clone this repository:
   ```bash
   git clone https://github.com/Adithshajee/github-portfolio-system.git
   cd github-portfolio-system
   ```
2. Run validation tests:
   ```bash
   python -m unittest tests/test_validation.py
   ```

3. Deploy documentation site locally:
   ```bash
   pip install -r requirements.txt
   mkdocs serve
   ```

---

## 🤝 Contributing

We welcome additions! Please check [CONTRIBUTING.md](CONTRIBUTING.md) and review the [Code of Conduct](CODE_OF_CONDUCT.md).
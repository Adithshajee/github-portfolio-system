# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.x     | ✅ Active support  |
| 1.x     | ⚠️ Security fixes only until 2027-01-01 |
| < 1.0   | ❌ No longer supported |

---

## Reporting a Vulnerability

**Please do NOT open a public GitHub issue for security vulnerabilities.**

To report a security vulnerability:

1. **GitHub Private Advisory (preferred):** Go to the [Security Advisories](https://github.com/Adithshajee/github-portfolio-system/security/advisories/new) page and open a new private advisory.

2. **Email:** Send details to `adideva12345@gmail.com` with subject line `[GPS Security] <brief description>`.

We aim to acknowledge all security reports within **48 hours** and provide a fix or mitigation within **7 days** for critical issues.

---

## Security Design Principles

### Token Handling
- API tokens (`GH_PAT`, `HF_TOKEN`, `KAGGLE_KEY`) are **only** read from environment variables.
- Tokens must never be committed to `gps.yml`, source code, or any repository file.
- `gps.yml` is explicitly designed to not have token fields.

### Minimum Required Scopes
| Provider | Token | Required Scopes |
|----------|-------|-----------------|
| GitHub (no auth) | None | Public repos only, 60 req/hr |
| GitHub (with PAT) | `GH_PAT` | `public_repo` (read-only) |
| Hugging Face | `HF_TOKEN` | Read access (optional) |
| Kaggle | `KAGGLE_KEY` + `KAGGLE_USERNAME` | Public API |

### Supply Chain
- All GitHub Actions are pinned to tagged versions.
- `lowlighter/metrics` is pinned to a **commit SHA** (not `@latest`).
- Dependabot automatically opens PRs for action updates weekly.

### Input Validation
- All API response strings are sanitized before README insertion.
- README paths are validated against path traversal attacks.
- GitHub usernames are validated against GitHub's naming rules.
- Pydantic v2 validates all configuration at startup.

### No Subprocess
- GPS uses pure Python — no `subprocess.run(shell=True)` calls.
- All operations go through the `httpx` HTTP client.

---

## Dependency Vulnerabilities

If you discover a vulnerability in one of GPS's dependencies, please report it to the upstream project and open a GPS issue referencing the CVE. We monitor Dependabot alerts and apply patches promptly.

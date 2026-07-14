# Contributing Guide

Contributions are welcome! Please follow these steps to set up and develop the GPS platform.

## Setup

```bash
git clone https://github.com/Adithshajee/github-portfolio-system.git
cd github-portfolio-system
pip install -e ".[dev]"
```

## Running Checks

```bash
ruff check src/ tests/
mypy src/gps/
pytest tests/
```

For more info, read the root [CONTRIBUTING.md](https://github.com/Adithshajee/github-portfolio-system/blob/main/CONTRIBUTING.md) file.

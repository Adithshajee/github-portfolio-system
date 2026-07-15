.PHONY: help install install-dev test coverage lint format typecheck security docs docs-build run clean all

# ─── Colors ───────────────────────────────────────────────────────────────────
GREEN  := \033[0;32m
YELLOW := \033[1;33m
CYAN   := \033[0;36m
RESET  := \033[0m

# ─── Help ─────────────────────────────────────────────────────────────────────
help: ## Show this help message
	@echo ""
	@echo "$(CYAN)GitHub Portfolio System (GPS) v3$(RESET)"
	@echo "$(YELLOW)Developer Identity Platform — Task Runner$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-18s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# ─── Installation ─────────────────────────────────────────────────────────────
install: ## Install runtime dependencies only
	pip install -e .

install-dev: ## Install all dependencies including dev tools and pre-commit hooks
	pip install -e ".[dev]"
	pre-commit install
	@echo "$(GREEN)✓ Development environment ready$(RESET)"

# ─── Testing ──────────────────────────────────────────────────────────────────
test: ## Run the full test suite
	pytest tests/ -v -m "not network"

test-all: ## Run all tests including network tests
	pytest tests/ -v

coverage: ## Run tests with HTML coverage report
	pytest tests/ -v -m "not network" --cov=src/gps --cov-report=html:htmlcov --cov-report=term-missing
	@echo "$(GREEN)✓ Coverage report available at htmlcov/index.html$(RESET)"

# ─── Code Quality ─────────────────────────────────────────────────────────────
lint: ## Run ruff linter
	ruff check src/ tests/
	@echo "$(GREEN)✓ Lint passed$(RESET)"

format: ## Format code with ruff
	ruff format src/ tests/
	@echo "$(GREEN)✓ Code formatted$(RESET)"

format-check: ## Check formatting without modifying files
	ruff format --check src/ tests/

typecheck: ## Run mypy static type analysis
	mypy src/gps/
	@echo "$(GREEN)✓ Type check passed$(RESET)"

security: ## Run bandit security scan
	bandit -r src/gps/ -c pyproject.toml
	@echo "$(GREEN)✓ Security scan passed$(RESET)"

quality: lint typecheck security ## Run all quality checks

# ─── Documentation ────────────────────────────────────────────────────────────
docs: ## Start MkDocs local development server
	mkdocs serve

docs-build: ## Build the static documentation site
	mkdocs build --strict
	@echo "$(GREEN)✓ Documentation built in site/$(RESET)"

docs-deploy: ## Deploy documentation to GitHub Pages
	mike deploy --push --update-aliases latest

# ─── GPS CLI ──────────────────────────────────────────────────────────────────
run: ## Run the GPS engine in dry-run mode (no file writes)
	gps run --dry-run

run-full: ## Run the GPS engine and write to profile README
	gps run

validate: ## Validate configuration and README markers
	gps validate

status: ## Show rate limit and provider status
	gps status

export-json: ## Export provider data as JSON
	gps export --format json

# ─── Pre-commit ───────────────────────────────────────────────────────────────
pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

# ─── Cleanup ──────────────────────────────────────────────────────────────────
clean: ## Remove build artifacts, caches, and generated files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name site -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -name ".coverage" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned build artifacts$(RESET)"

# ─── CI (local simulation) ────────────────────────────────────────────────────
ci: format-check lint typecheck security test ## Run full CI pipeline locally
	@echo ""
	@echo "$(GREEN)✓ All CI checks passed$(RESET)"

all: install-dev ci docs-build ## Full setup + CI + docs build

# Everything a contributor runs locally. CI runs `make check`.
PY ?= python

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

.PHONY: install
install: ## Install with dev and provider extras
	$(PY) -m pip install -e ".[dev,providers]"

.PHONY: lint
lint: ## Ruff lint and format check
	ruff check src tests
	ruff format --check src tests

.PHONY: format
format: ## Apply ruff fixes and formatting
	ruff check --fix src tests
	ruff format src tests

.PHONY: typecheck
typecheck: ## mypy
	mypy

.PHONY: test
test: ## pytest with coverage
	pytest --cov --cov-report=term-missing --cov-fail-under=75

.PHONY: vendored
vendored: ## Verify vendored upstream files are unchanged
	cd vendor/llm-architects && sha256sum -c --quiet SHA256SUMS

.PHONY: validate
validate: ## Validate config, prompts, captures and score sheets
	modegrid validate

.PHONY: check
check: lint typecheck test vendored validate ## Everything CI runs

.PHONY: demo
demo: ## Synthetic end-to-end run (no API calls)
	modegrid demo

.PHONY: plan
plan: ## Regenerate the run manifest
	modegrid plan

.PHONY: analyze
analyze: ## Confirmatory analysis into results/
	modegrid analyze

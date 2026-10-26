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

PAPER_SECTIONS = paper/abstract.md paper/introduction.md paper/related-work.md paper/methods.md paper/results.md paper/discussion.md paper/broader-impact.md paper/references.md paper/appendix.md

.PHONY: paper
paper: ## Stitch the paper drafts into paper/build/manuscript.md and .html (needs pandoc for the HTML)
	mkdir -p paper/build
	cat $(PAPER_SECTIONS) > paper/build/manuscript.md
	pandoc paper/build/manuscript.md --standalone --toc --metadata title="LA-P4 manuscript draft" -o paper/build/manuscript.html
	@echo "wrote paper/build/manuscript.md and paper/build/manuscript.html"

.PHONY: jair
jair: ## LaTeX for the JAIR submission in paper/jair/ (needs pandoc; compile with latexmk + biber, or Overleaf)
	python paper/latex_build.py jair
	@if command -v latexmk >/dev/null; then cd paper/jair && latexmk -pdf -quiet main.tex; \
	else echo "latexmk not found: upload paper/jair/ and results/figure1.pdf to Overleaf"; fi

.PHONY: tmlr
tmlr: ## TMLR LaTeX in paper/tmlr/: anonymous main.pdf for review and named preprint.pdf (needs pandoc and tectonic)
	python paper/latex_build.py tmlr
	cd paper/tmlr && tectonic main.tex && tectonic preprint.tex

RATERS = human llm-a llm-b
SHEETS = $(foreach r,$(RATERS),data/scores/$(r).csv)
UNBLINDED = $(foreach r,$(RATERS),data/scores/$(r)-unblinded.csv)

.PHONY: results
results: ## After scoring: agreement, consensus, unblind, the full analysis and results/report.md (runbook Phases 3 and 4)
	modegrid agreement $(SHEETS) --out results/agreement.csv
	modegrid agreement data/scores/human.csv data/scores/llm-a.csv --out results/agreement-human-llm-a.csv
	modegrid agreement data/scores/human.csv data/scores/llm-b.csv --out results/agreement-human-llm-b.csv
	modegrid consensus $(SHEETS)
	modegrid unblind data/scores/adjudicated-blind.csv
	modegrid validate
	modegrid analyze --agreement results/agreement.csv --note "Confirmatory analysis, prereg-v1"
	for r in $(RATERS); do \
	  modegrid unblind data/scores/$$r.csv --out data/scores/$$r-unblinded.csv && \
	  modegrid analyze --scores data/scores/$$r-unblinded.csv --out results/$$r || exit 1; \
	done
	modegrid own-vendor $(UNBLINDED) --out results/own_vendor.csv --replaced-out results/own-vendor-replaced
	modegrid blinding-check $(SHEETS) --out results/blinding_check.csv
	modegrid analyze --families gpt,qwen,deepseek --out results/fast-off
	modegrid analyze --families claude,gemini,grok --out results/fast-lowest
	modegrid rank-agreement $(UNBLINDED) --out results/cell_rank_agreement.csv
	modegrid cells --figure figure1.pdf
	modegrid report
	@echo "Done. Read results/report.md. Then commit the key: git add -f data/blinding/key.csv"

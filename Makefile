.PHONY: install test smoke dataset-smoke audit burn-in metrics lint clean help

PYTHON ?= python3
VENV   ?= .venv
PY     := $(VENV)/bin/python

# Real-world projects under ~/Claude/research_<topic>/ that exist on this machine.
# `make audit` runs cross_stage --strict against any that exist.
REAL_TOPICS := eval_methodology peft calibration rlhf

help:
	@echo "Targets:"
	@echo "  install         create .venv and install package + dev deps"
	@echo "  test            run pytest against tests/"
	@echo "  smoke           run a single validator against the mini fixture"
	@echo "  dataset-smoke   run dataset_ledger validator against the dataset smoke fixture (v1.6)"
	@echo "  audit           run cross_stage --strict against all real-world projects"
	@echo "                  (mini, medium, prompt-injection real/recreated, $(REAL_TOPICS))"
	@echo "  burn-in         show unresolved high-severity BURN_IN items"
	@echo "  metrics         show dogfood_metrics.csv contents"
	@echo "  clean           remove caches and .venv"

install:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -e ".[dev]"

test:
	$(PY) -m pytest

smoke:
	$(PY) validators/bib_ledger.py tests/fixtures/mini_topic_timeseries_anomaly/bib_ledger.yml

dataset-smoke:
	@if [ -d tests/fixtures/medium_dataset_subset ]; then \
		echo "=== medium_dataset_subset (post-Phase D) ==="; \
		$(PY) validators/dataset_ledger.py tests/fixtures/medium_dataset_subset/dataset_ledger.yml; \
	else \
		echo "=== _handcrafted_dataset_smoke (Phase A handcrafted) ==="; \
		$(PY) validators/dataset_ledger.py tests/fixtures/_handcrafted_dataset_smoke/dataset_ledger.yml; \
	fi

audit:
	@echo "=== mini fixture ==="
	@$(PY) -m validators.cross_stage --strict tests/fixtures/mini_topic_timeseries_anomaly || true
	@echo "=== medium fixture ==="
	@$(PY) -m validators.cross_stage --strict tests/fixtures/medium_topic_calibration_subset || true
	@echo "=== prompt-injection real ==="
	@$(PY) -m validators.cross_stage tests/fixtures/prompt_injection_snapshot/real || true
	@echo "    (prompt-injection/real is run in default mode — has 202 intentional cross-references)"
	@echo "=== prompt-injection recreated ==="
	@$(PY) -m validators.cross_stage --strict tests/fixtures/prompt_injection_snapshot/recreated || true
	@for topic in $(REAL_TOPICS); do \
		dir=$$HOME/Claude/research_$$topic; \
		if [ -d "$$dir" ]; then \
			echo "=== $$topic ==="; \
			$(PY) -m validators.cross_stage --strict $$dir || true; \
		else \
			echo "=== $$topic === (not present locally; skipped)"; \
		fi; \
	done

burn-in:
	@$(PY) scripts/burn_in_query.py --severity high --status surfaced

metrics:
	@cat evals/dogfood_metrics.csv | column -t -s,

clean:
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache **/__pycache__ *.egg-info

.PHONY: install test smoke audit burn-in metrics lint clean help

PYTHON ?= python3
VENV   ?= .venv
PY     := $(VENV)/bin/python

# Real-world projects under ~/Claude/research_<vol>/ that exist on this machine.
# `make audit` runs cross_stage --strict against any that exist.
REAL_VOLS := vol26 vol27 vol28

help:
	@echo "Targets:"
	@echo "  install   create .venv and install package + dev deps"
	@echo "  test      run pytest against tests/"
	@echo "  smoke     run a single validator against the mini fixture"
	@echo "  audit     run cross_stage --strict against all real-world projects"
	@echo "            (mini fixture, medium fixture, vol25/real, vol25/recreated, $(REAL_VOLS))"
	@echo "  burn-in   show unresolved high-severity BURN_IN items"
	@echo "  metrics   show dogfood_metrics.csv contents"
	@echo "  clean     remove caches and .venv"

install:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -e ".[dev]"

test:
	$(PY) -m pytest

smoke:
	$(PY) validators/bib_ledger.py tests/fixtures/mini_topic_timeseries_anomaly/bib_ledger.yml

audit:
	@echo "=== mini fixture ==="
	@$(PY) -m validators.cross_stage --strict tests/fixtures/mini_topic_timeseries_anomaly || true
	@echo "=== medium fixture ==="
	@$(PY) -m validators.cross_stage --strict tests/fixtures/medium_topic_calibration_subset || true
	@echo "=== vol25 real ==="
	@$(PY) -m validators.cross_stage tests/fixtures/vol25_snapshot/real || true
	@echo "    (vol25/real is run in default mode — has 202 intentional cross-references)"
	@echo "=== vol25 recreated ==="
	@$(PY) -m validators.cross_stage --strict tests/fixtures/vol25_snapshot/recreated || true
	@for vol in $(REAL_VOLS); do \
		dir=$$HOME/Claude/research_$$vol; \
		if [ -d "$$dir" ]; then \
			echo "=== $$vol ==="; \
			$(PY) -m validators.cross_stage --strict $$dir || true; \
		else \
			echo "=== $$vol === (not present locally; skipped)"; \
		fi; \
	done

burn-in:
	@$(PY) scripts/burn_in_query.py --severity high --status surfaced

metrics:
	@cat evals/dogfood_metrics.csv | column -t -s,

clean:
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache **/__pycache__ *.egg-info

.PHONY: install test smoke lint clean help

PYTHON ?= python3
VENV   ?= .venv

help:
	@echo "Targets:"
	@echo "  install   create .venv and install package + dev deps"
	@echo "  test      run pytest against tests/"
	@echo "  smoke     run a single validator against its fixture (sanity check)"
	@echo "  clean     remove caches and .venv"

install:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -e ".[dev]"

test:
	$(VENV)/bin/python -m pytest

smoke:
	$(VENV)/bin/python validators/bib_ledger.py tests/fixtures/mini_topic_timeseries_anomaly/bib_ledger.yml

clean:
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache **/__pycache__ *.egg-info

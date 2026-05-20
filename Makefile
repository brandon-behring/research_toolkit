.PHONY: install symlinks test smoke dataset-smoke v2-smoke builders-smoke audit audit-strict burn-in metrics lint clean help

PYTHON ?= python3
VENV   ?= .venv
PY     := $(VENV)/bin/python

# Real-world projects under ~/Claude/research_<topic>/ that exist on this machine.
# `make audit` runs cross_stage --strict against any that exist.
REAL_TOPICS := eval_methodology peft calibration rlhf
SKILLS := research-plan research-gather dossier-build agent-index dossier-audit url-freshness-check dataset-gather dataset-index dataset-research freshness-audit research-kb-export

help:
	@echo "Targets:"
	@echo "  install         create .venv and install package + dev deps"
	@echo "  symlinks        symlink all skill bodies into ~/.claude/skills/"
	@echo "  test            run pytest against tests/"
	@echo "  smoke           run a single validator against the mini fixture"
	@echo "  dataset-smoke   run dataset_ledger validator against the dataset smoke fixture (v1.6)"
	@echo "  v2-smoke        run strict-live v2 validators against the v2 fixture"
	@echo "  builders-smoke  run build_claim_graph + build_dashboard against the v2 fixture (output to /tmp)"
	@echo "  audit           run cross_stage --strict against all real-world projects"
	@echo "  audit-strict    strict audit target that fails on validator failures"
	@echo "                  (mini, medium, prompt-injection real/recreated, $(REAL_TOPICS))"
	@echo "  burn-in         show unresolved high-severity BURN_IN items"
	@echo "  metrics         show dogfood_metrics.csv contents"
	@echo "  clean           remove caches and .venv"

install:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -e ".[dev]"

symlinks:
	@mkdir -p $$HOME/.claude/skills
	@for skill in $(SKILLS); do \
		ln -sf $$PWD/.claude/skills/$$skill.md $$HOME/.claude/skills/$$skill.md; \
		echo "linked $$skill"; \
	done

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

v2-smoke:
	$(PY) validators/bib_ledger.py tests/fixtures/v2_strict_live_ai_agents/bib_ledger.yml
	$(PY) validators/dataset_ledger.py tests/fixtures/v2_strict_live_ai_agents/dataset_ledger.yml
	$(PY) validators/evidence_ledger.py tests/fixtures/v2_strict_live_ai_agents/evidence_ledger.yml
	$(PY) validators/cache_manifest.py tests/fixtures/v2_strict_live_ai_agents/cache_manifest.yml
	$(PY) validators/claim_graph.py tests/fixtures/v2_strict_live_ai_agents/claim_graph.jsonl
	$(PY) validators/research_kb_export.py tests/fixtures/v2_strict_live_ai_agents/research_kb_export.jsonl
	$(PY) validators/freshness.py --strict --today 2026-05-19 tests/fixtures/v2_strict_live_ai_agents
	@echo "--- multi-entry fixture ---"
	$(PY) validators/bib_ledger.py tests/fixtures/v2_strict_live_multi_entry/bib_ledger.yml
	$(PY) validators/dataset_ledger.py tests/fixtures/v2_strict_live_multi_entry/dataset_ledger.yml
	$(PY) validators/evidence_ledger.py tests/fixtures/v2_strict_live_multi_entry/evidence_ledger.yml
	$(PY) validators/cache_manifest.py tests/fixtures/v2_strict_live_multi_entry/cache_manifest.yml
	$(PY) validators/claim_graph.py tests/fixtures/v2_strict_live_multi_entry/claim_graph.jsonl
	$(PY) validators/freshness.py --strict --today 2026-05-19 tests/fixtures/v2_strict_live_multi_entry

builders-smoke:
	$(PY) scripts/build_claim_graph.py tests/fixtures/v2_strict_live_ai_agents --output /tmp/built_claim_graph.jsonl
	$(PY) validators/claim_graph.py /tmp/built_claim_graph.jsonl
	$(PY) scripts/build_dashboard.py tests/fixtures/v2_strict_live_ai_agents --output /tmp/built_dashboard.md --today 2026-05-19
	@test -s /tmp/built_dashboard.md || (echo "FATAL: built dashboard.md is empty" >&2; exit 1)
	@grep -q "Trust State" /tmp/built_dashboard.md || (echo "FATAL: dashboard missing Trust State" >&2; exit 1)
	@echo "OK: builders-smoke"

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

audit-strict:
	$(PY) -m validators.cross_stage --strict tests/fixtures/mini_topic_timeseries_anomaly
	$(PY) -m validators.cross_stage --strict tests/fixtures/medium_topic_calibration_subset
	$(PY) -m validators.cross_stage --strict tests/fixtures/prompt_injection_snapshot/recreated
	$(PY) -m validators.freshness --strict --today 2026-05-19 tests/fixtures/v2_strict_live_ai_agents
	$(PY) -m validators.freshness --strict --today 2026-05-19 tests/fixtures/v2_strict_live_multi_entry

burn-in:
	@$(PY) scripts/burn_in_query.py --severity high --status surfaced

metrics:
	@cat evals/dogfood_metrics.csv | column -t -s,

clean:
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache **/__pycache__ *.egg-info

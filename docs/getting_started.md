# Getting started with research_toolkit

A 5-minute walkthrough. Audience: future-you or future Claude Code agents
reading the repo cold. Not external collaborators.

## Which pipeline?

| You want…                                       | Use                                    |
|---|---|
| "what literature exists for X?"                 | paper pipeline (`/research-plan`)      |
| "what public datasets exist for X?"             | dataset pipeline (`/dataset-research`) |
| "make this current + reusable KB evidence"      | strict-live v2 (`/freshness-audit`)    |
| Both (paired research)                          | run both; cross-link the agent-indexes |

The paper pipeline (v1.0+) is described first; the dataset pipeline (v1.6+) is below at "## Dataset pipeline".

## What this toolkit does

Claude Code skills that build a structured research dossier from a topic
prompt. Paper-pipeline stages:

1. `/research-plan <topic>` → produces `research_plan.md` (sub-area taxonomy + claim_family taxonomy + scope)
2. `/research-gather <plan>` → WebSearches + WebFetches primary sources; writes `bib_ledger.yml`
3. `/dossier-build <ledger>` → renders entries as topic-organized Markdown tables in `dossier/`
4. `/agent-index <dossier>` → synthesizes 5-bullet entries + lookup recipes + glossary in `<consumer>/docs/<topic>/`
5. `/dossier-audit <agent_index> [--focus <area>]` → DROP/CORRECT/FLAG/SPOT-CHECK round
6. `/url-freshness-check <agent_index>` → bulk-checks every URL; writes report

Each stage has a schema validator. Each stage's output is the next stage's input.
Strict-live v2 adds `evidence_ledger.yml`, `cache_manifest.yml`,
`claim_graph.jsonl`, trust dashboards, and `research-kb` export.

## Install

The skills live as symlinks in `~/.claude/skills/`. Install:

```bash
cd ~/Claude/research_toolkit
make install     # pip install -e ".[dev]"
make symlinks    # symlinks all skill bodies into ~/.claude/skills/
```

Verify Claude Code sees them:

```bash
ls ~/.claude/skills/research-*.md ~/.claude/skills/dossier-*.md ~/.claude/skills/agent-*.md ~/.claude/skills/url-*.md
```

### Optional: Playwright for JS-rendered sources (v2.2.1+)

`scripts/cache_source.py` uses urllib by default — fast, dependency-free,
but blind to JS-rendered SPAs / vendor dashboards. v2.2.1 adds an optional
Playwright escalation path triggered by `--escalate-on-failure`.

Install once:

```bash
pip install -e ".[dev]"            # installs playwright Python package
playwright install chromium        # downloads the Chromium browser
```

Then `cache_source.py --escalate-on-failure <url>` will retry via headless
Chromium when urllib returns 403/429 or content that looks like an
unhydrated SPA (blank text, JS-required markers).

### PDF extraction (v2.3+)

`scripts/cache_source.py` now extracts text from PDFs by default via a
two-stage cascade:

1. **pdfplumber** (pure Python, fast) — handles plain-text academic PDFs.
2. **Docling** (IBM, Apache 2.0) — preserves equations as LaTeX when math is
   detected in the pdfplumber output. ~600 MB of models downloaded lazily
   on first PDF call.

Both are hard dependencies via `pip install -e ".[dev]"`. The first PDF you
cache after install will take ~30 seconds while Docling pulls models — this
is one-time per machine (or per synced cache, see below).

`extraction_status` values surfaced in `cache_manifest.yml`:

| Status | Meaning |
|---|---|
| `ok` | pdfplumber extracted clean text, no math suspicion |
| `rich` | Docling preserved equations as LaTeX |
| `ok_text_only` | math detected but Docling failed/unavailable — pdfplumber output kept (WARN) |
| `degraded` | both extractors low-yield (likely scanned/image PDF) (WARN) |
| `partial` | encrypted PDF, partial extraction (WARN) |
| `failed` | both extractors errored (ERROR) |
| `stub` | v2.3 #10: JS-shell HTML page detected without Playwright escalation (WARN) |
| `raw_only` | non-PDF binary, or `--no-extract-pdfs` was set |

Flags:
- `--no-extract-pdfs` — skip PDF extraction (PDFs land at `raw_only`).
- `--strict-extraction` — exit non-zero on any WARN-tier status. For
  batch runs (`/research-gather --cache-pdfs`) that need clean output.
- `--extraction-log PATH` — append-only JSONL log of outcomes. Default:
  `<cache_root>/extraction_log_<hostname>.jsonl` (per-host filename
  avoids Dropbox/Drive conflicts on synced caches).

### Re-extracting legacy `raw_only` PDFs

For consumers upgrading from <=v2.2: existing `extraction_status: raw_only`
PDF entries can be re-extracted in place (no re-download) via:

```bash
python scripts/reextract_pdfs.py path/to/cache_manifest.yml
python scripts/reextract_pdfs.py path/to/cache_manifest.yml --dry-run
```

Idempotent. Revisit entries skipped. Mirrors `migrate_manifest_paths.py` UX.

### Cross-machine cache sync (Docling models + cache blobs)

The 600 MB Docling model download + the cache blobs themselves can both
live on a synced dir (Dropbox / Drive / shared NAS) so multiple machines
share one copy:

```bash
# Point cache_source.py at a synced cache_root
python scripts/cache_source.py --cache-root ~/Dropbox/research_cache <url>

# Point Docling at a synced model dir on both machines
export DOCLING_CACHE_DIR=~/Dropbox/docling_models
python scripts/precache_docling_models.py  # pre-pull from machine A
```

The per-host `extraction_log_<hostname>.jsonl` filename means concurrent
writes from two machines don't trigger Dropbox conflicted-copy files.

If `docling` install fails on macOS Python 3.12 (`'cstdint' not found`
during docling-parse build), see `docs/troubleshooting.md` for workarounds.

## A 5-minute end-to-end run

Pick a topic. From any directory:

```
/research-plan "your topic here"
```

Claude will write `~/Claude/research_<slug>/research_plan.md`. Review it; the
sub-areas + claim_family taxonomy drive everything downstream. Edit the plan
if scope is wrong.

Then:

```
/research-gather ~/Claude/research_<slug>/research_plan.md
```

This is the slow stage (~20-40 min for 50-80 entries; uses WebSearch + WebFetch
heavily). Outputs `bib_ledger.yml` with entries you can spot-check.

Then in sequence:

```
/dossier-build ~/Claude/research_<slug>/bib_ledger.yml
/agent-index ~/Claude/research_<slug>/dossier --output-dir ~/your_project/docs/<topic>/
/dossier-audit ~/your_project/docs/<topic>/ --focus "<focus area>"
/url-freshness-check ~/your_project/docs/<topic>/
```

## Dataset pipeline (v1.6+)

Use this when you need "what public datasets exist for this topic" instead of "what literature exists for this topic." Same shape as the paper pipeline; reuses `/dossier-audit` and `/url-freshness-check`.

Three skills:

1. `/dataset-gather <topic>` → searches 8 source categories (HF / Kaggle / academic / aggregators / cloud / domain / gov / classical ML); writes `dataset_ledger.yml`
2. `/dataset-index <ledger>` → renders 5-bullet entries (Source / Access / Schema / Size+License / Tasks) into `<consumer>/docs/<topic>_datasets/`
3. `/dataset-research <topic>` → one-shot wrapper for the two stages above

Trigger:

```
/dataset-research "your topic here"
```

Output:

```
~/Claude/research_<topic>_datasets/dataset_ledger.yml
~/your_project/docs/<topic>_datasets/
```

Reuse the same audit + URL-check stages with a license-focused audit:

```
/dossier-audit ~/your_project/docs/<topic>_datasets/ --focus "license risks + access stability"
/url-freshness-check ~/your_project/docs/<topic>_datasets/
```

## Strict-live v2

Use this when you want a durable research OS artifact rather than a one-time
snapshot. v2 projects cache every reachable source locally under
`~/Claude/research_cache/`, track field-level evidence in `evidence_ledger.yml`,
and export JSONL for `~/Claude/research-kb`.

Typical flow after a gather/index run:

```
/freshness-audit ~/Claude/research_<slug>/ --strict
/research-kb-export ~/Claude/research_<slug>/
```

Validate the fixture:

```bash
make v2-smoke
```

### Worked example: "time-series anomaly detection datasets"

The v1.6 dogfood — real numbers from `~/Claude/research_time_series_anomaly/`.

- Trigger: `/dataset-research "time-series anomaly detection datasets"`
- Output: `dataset_ledger.yml` with 45 entries.
- Source distribution: HF / academic / classical-ML archives (UCR, NAB) account for ~70%; the remaining ~29% is `source: other` (PhysioNet, iTrust, Yahoo Webscope, Backblaze, ELKI). The high `source: other` ratio was expected — this is a security/IoT/biomedical-heavy domain where the canonical aggregators don't dominate. See `references/dataset_sources.md` § "When `source: other` is the right answer" for why that's normal here.
- Stage 2 output: `<consumer>/docs/time_series_anomaly_datasets/` with one 5-bullet entry per dataset.
- Validation: `cross_stage --strict` catches ledger ↔ synthesis drift after Stage 2 (v1.9 extended this check to dataset projects).
- Cross-link convention: if the consumer project also has a paper-pipeline dossier, bidirectional cross-link in both READMEs (see `templates/agent_index_README.template.md` § "Paired-pipeline cross-link convention" — the v1.8 RLHF dogfood is the worked example).

## Validating an in-progress run

Each stage has its own validator; run any of them at any time:

```bash
cd ~/Claude/research_toolkit
python validators/research_plan.py ~/Claude/research_<slug>/research_plan.md
python validators/bib_ledger.py ~/Claude/research_<slug>/bib_ledger.yml
python validators/dataset_ledger.py ~/Claude/research_<slug>_datasets/dataset_ledger.yml   # dataset pipeline
python validators/dossier.py ~/Claude/research_<slug>/dossier
python validators/agent_index.py ~/your_project/docs/<topic>/
python validators/cross_stage.py ~/Claude/research_<slug>      # cross-artifact consistency
python validators/freshness.py --strict ~/Claude/research_<slug>  # v2 evidence/cache/freshness
```

Cross-stage `--strict` promotes warnings (orphan IDs, stale ledger entries) to
errors. Useful pre-publish. v1.9 extended `cross_stage` to handle dataset_ledger
↔ agent_index pairs as well.

## How the toolkit catches subagent misbehavior

Three v1.2-era guardrails:

- **arXiv canonical-form check** (`bib_ledger.py`) — `/pdf/` URLs and malformed
  IDs are rejected at validation time, not silently rendered through.
- **Cross-stage consistency** (`cross_stage.py`) — every claim_family in the
  ledger must appear in the plan's taxonomy; `--strict` also flags orphan
  arxiv IDs in the agent_index.
- **Memory-verification anti-cheat** (`bib_ledger.py`) — if ≥50 entries AND
  every entry is `status: verified`, warns. With `--strict`, errors. Catches
  the "subagent skipped per-entry WebFetch" failure mode.

If any of these fire on your run, see `docs/troubleshooting.md`.

## Where things live

- `.claude/skills/*.md` — skill bodies (read by Claude Code)
- `validators/*.py` — schema validators
- `templates/*.template.{md,yml}` — output schema templates
- `references/*.md` — protocol docs
- `~/Claude/research_cache/` — private global v2 source cache
- `~/Claude/research-kb/inbox/research_toolkit/` — v2 JSONL exports
- `tests/fixtures/` — `mini` (5 entries, smoke), `medium_topic_calibration_subset` (22 entries, v1.1+ schema reference), `prompt_injection_snapshot/{real,recreated}` (137 entries, real-world reference)
- `BURN_IN_NOTES.md` + `burn_in.yml` — friction tracking (narrative + queryable)
- `evals/dogfood_metrics.csv` — reliability metrics across runs

## What to read next

- `BURN_IN_NOTES.md` — what failure modes the toolkit has surfaced and how each was fixed
- `docs/troubleshooting.md` — common failures + their resolutions
- `references/audit_protocol.md` — how `/dossier-audit` works in detail
- The skill bodies themselves under `.claude/skills/` — they're the source of truth for what each skill does

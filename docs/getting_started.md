# Getting started with research_toolkit

A 5-minute walkthrough. Audience: future-you or future Claude Code agents
reading the repo cold. Not external collaborators.

## What this toolkit does

Six Claude Code skills that build a structured research dossier from a topic
prompt. Pipeline stages:

1. `/research-plan <topic>` → produces `research_plan.md` (sub-area taxonomy + claim_family taxonomy + scope)
2. `/research-gather <plan>` → WebSearches + WebFetches primary sources; writes `bib_ledger.yml`
3. `/dossier-build <ledger>` → renders entries as topic-organized Markdown tables in `dossier/`
4. `/agent-index <dossier>` → synthesizes 5-bullet entries + lookup recipes + glossary in `<consumer>/docs/<topic>/`
5. `/dossier-audit <agent_index> [--focus <area>]` → DROP/CORRECT/FLAG/SPOT-CHECK round
6. `/url-freshness-check <agent_index>` → bulk-checks every URL; writes report

Each stage has a schema validator. Each stage's output is the next stage's input.

## Install

The skills live as symlinks in `~/.claude/skills/`. Install:

```bash
cd ~/Claude/research_toolkit
make install     # pip install -e ".[dev]"
make symlinks    # symlinks 6 skill bodies into ~/.claude/skills/
```

Verify Claude Code sees them:

```bash
ls ~/.claude/skills/research-*.md ~/.claude/skills/dossier-*.md ~/.claude/skills/agent-*.md ~/.claude/skills/url-*.md
```

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

## Validating an in-progress run

Each stage has its own validator; run any of them at any time:

```bash
cd ~/Claude/research_toolkit
python validators/research_plan.py ~/Claude/research_<slug>/research_plan.md
python validators/bib_ledger.py ~/Claude/research_<slug>/bib_ledger.yml
python validators/dossier.py ~/Claude/research_<slug>/dossier
python validators/agent_index.py ~/your_project/docs/<topic>/
python validators/cross_stage.py ~/Claude/research_<slug>      # cross-artifact consistency
```

Cross-stage `--strict` promotes warnings (orphan IDs, stale ledger entries) to
errors. Useful pre-publish.

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
- `tests/fixtures/` — `mini` (5 entries, smoke), `medium_topic_calibration_subset` (22 entries, v1.1+ schema reference), `vol25_snapshot/{real,recreated}` (137 entries, real-world reference)
- `BURN_IN_NOTES.md` + `burn_in.yml` — friction tracking (narrative + queryable)
- `evals/dogfood_metrics.csv` — reliability metrics across runs
- `docs/roadmap_v1_2_through_v1_5.md` — version plan

## What to read next

- `BURN_IN_NOTES.md` — what failure modes the toolkit has surfaced and how each was fixed
- `docs/troubleshooting.md` — common failures + their resolutions
- `references/audit_protocol.md` — how `/dossier-audit` works in detail
- The skill bodies themselves under `.claude/skills/` — they're the source of truth for what each skill does

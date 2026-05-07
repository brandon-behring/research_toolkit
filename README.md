# research_toolkit

Claude Code skill collection for systematic research workflows: gather primary sources → build a dossier → synthesize an agent-ready indexed folder → audit it.

> **Status:** Pre-v1.0. Phase 1 (validators + fixtures) under construction. See `~/.claude/plans/i-want-to-examine-abstract-petal.md` for the implementation plan.

## What's here

Six SRP skills covering the research workflow:

| Skill | Stage | Purpose |
|---|---|---|
| `/research-plan` | 0 | Scope a topic — sub-areas, source types, in/out-of-scope, claim_family taxonomy |
| `/research-gather` | 1 | Discover primary sources, populate `bib_ledger.yml`, cache PDFs |
| `/dossier-build` | 2 | Render bib entries as topic-organized Markdown tables |
| `/agent-index` | 3 | Synthesize dossier into a dual-audience indexed folder (5-bullet entries + AGENT-INDEX README) |
| `/dossier-audit` | 4 | One round of complementary-scope audit (DROP / CORRECT / FLAG protocol) |
| `/url-freshness-check` | utility | HEAD-check URLs in any markdown collection |

Plus: schema validators (`validators/`), pytest harness (`tests/`), templates (`templates/`), reference docs (`references/`).

## Install

```bash
git clone <remote> ~/Claude/research_toolkit
cd ~/Claude/research_toolkit
make install              # creates .venv, installs validator deps
make test                 # verify validators pass on fixtures

# Make skills discoverable from any project's CWD:
mkdir -p ~/.claude/skills
for skill in research-plan research-gather dossier-build agent-index dossier-audit url-freshness-check; do
  ln -s ~/Claude/research_toolkit/.claude/skills/$skill.md ~/.claude/skills/$skill.md
done
```

## Maintenance contract

Skill bodies hard-code paths to `~/Claude/research_toolkit/templates/...` and `~/Claude/research_toolkit/references/...`. **If you move the toolkit, update those paths in every skill body.**

## TDD discipline

Each skill has a mandatory `## Validation` final step that calls `validators/<name>.py`. Validators are schema-only (fields, types, enums, counts, structural shape) — fast and deterministic. URL liveness is `/url-freshness-check`'s job; content faithfulness is `/dossier-audit`'s job.

Two fixture types under `tests/fixtures/`:
- `mini_topic_timeseries_anomaly/` — hand-curated "new use case" smoke test
- `vol25_snapshot/` — both `real/` (frozen vol25 dossier+synthesis) and `recreated/` (output of new skills run on the same domain). `test_recreation_diff.py` reports schema-equivalence + diff.

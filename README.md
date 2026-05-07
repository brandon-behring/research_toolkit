# research_toolkit

Claude Code skill collection for systematic research workflows: scope a topic → gather primary sources → build a dossier → synthesize an agent-ready indexed folder → audit it.

> **Status:** v1.5 shipped. Toolkit is in maintenance-ready state with 97 passing tests + 2 deliberate xfail baselines. See `BURN_IN_NOTES.md` for the full version history.

## What to read

| If you want to... | Read |
|---|---|
| Use the toolkit for the first time | [`docs/getting_started.md`](docs/getting_started.md) — 5-min walkthrough |
| Understand a failure / error message | [`docs/troubleshooting.md`](docs/troubleshooting.md) — 7 common failures with symptom→cause→fix |
| See what's been improved version-by-version | [`BURN_IN_NOTES.md`](BURN_IN_NOTES.md) — narrative friction log across v1.0–v1.5 |
| Query unresolved issues | `python scripts/burn_in_query.py --status surfaced` |
| See planned future work | [`docs/roadmap_v1_2_through_v1_5.md`](docs/roadmap_v1_2_through_v1_5.md) — sequenced post-v1.1 plan (now mostly applied) |
| See reliability across runs | [`evals/dogfood_metrics.csv`](evals/dogfood_metrics.csv) — per-run hard-404 + audit-correction counts |

## The 6 skills

| Skill | Stage | Input | Output | Validator |
|---|---|---|---|---|
| `/research-plan` | 0 | Topic free-text | `research_plan.md` | `validators/research_plan.py` |
| `/research-gather` | 1 | `research_plan.md` | `bib_ledger.yml` (+ optional `papers/`) | `validators/bib_ledger.py` |
| `/dossier-build` | 2 | `bib_ledger.yml` | N topic dossier files | `validators/dossier.py` |
| `/agent-index` | 3 | Dossier files | Indexed folder + AGENT-INDEX README | `validators/agent_index.py` |
| `/dossier-audit` | 4 | Indexed folder + scope focus | One round of DROP/CORRECT/FLAG fixes + audit-trail note | `validators/audit_trail.py` |
| `/url-freshness-check` | utility | Any markdown folder | URL HEAD-check report | `validators/url_check_report.py` |

Plus a v1.2 cross-artifact validator: `validators/cross_stage.py` — checks that bib_ledger / dossier / agent_index agree on what they're describing.

The handoff contract is enforced by validators — skill N's output validator IS skill N+1's input validator. If schemas drift, downstream skills fail at the validator step before they can produce broken output.

## Repository layout

```
~/Claude/research_toolkit/
├── README.md                        # this file
├── BURN_IN_NOTES.md                 # narrative friction log (v1.0-v1.5)
├── burn_in.yml                      # structured BURN_IN index (v1.5)
├── Makefile                         # `make install` / `make test` / `make audit`
├── pyproject.toml
├── .claude/skills/                  # 6 skill bodies (source of truth)
├── templates/                       # 6 schema/structure templates
├── references/                      # 6 protocol docs (audit_protocol, url_check_protocol, ...)
├── validators/                      # 7 schema validators (cross_stage added v1.2)
├── scripts/                         # backfill_ledger, build_medium_fixture, burn_in_query
├── docs/
│   ├── getting_started.md           # v1.5 onboarding
│   ├── troubleshooting.md           # v1.5 common failures
│   └── roadmap_v1_2_through_v1_5.md # forward plan (mostly applied)
├── evals/
│   └── dogfood_metrics.csv          # reliability metrics across runs
└── tests/
    ├── conftest.py
    ├── test_validators.py           # positive + negative per validator
    ├── test_skill_outputs.py        # vol25 fixture sanity
    ├── test_recreation_diff.py      # real/ vs recreated/ (2 xfailed baselines)
    ├── test_v1_1_fixes.py           # 27 cases: schema extension + arXiv canonical-form
    ├── test_v1_2_fixes.py           # 14 cases: cross_stage + anti-cheat
    ├── test_v1_3_fixtures.py        # 17 cases: backfilled ledgers + medium fixture
    ├── test_pipeline_e2e.py         # 9 cases: validator chain + idempotency
    ├── test_v1_5_artifacts.py       # 12 cases: docs + burn_in + metrics
    └── fixtures/
        ├── mini_topic_timeseries_anomaly/        # 5 entries (smoke)
        ├── medium_topic_calibration_subset/      # 22 entries (v1.3, schema reference)
        └── vol25_snapshot/{real,recreated}/      # 137 entries (real-world reference)
```

## Install

```bash
git clone <remote> ~/Claude/research_toolkit
cd ~/Claude/research_toolkit
make install              # .venv + pip install -e ".[dev]"
make test                 # 97 pass + 2 xfailed on clean checkout

# Make skills discoverable from any project's CWD:
mkdir -p ~/.claude/skills
for skill in research-plan research-gather dossier-build agent-index dossier-audit url-freshness-check; do
  ln -s ~/Claude/research_toolkit/.claude/skills/$skill.md ~/.claude/skills/$skill.md
done
```

After symlinking, the 6 skills are invokable from any project's Claude Code session without per-repo setup.

For a 5-minute end-to-end run, see [`docs/getting_started.md`](docs/getting_started.md).

## Make targets

| Command | Effect |
|---|---|
| `make install` | venv + dev deps |
| `make test` | full pytest suite |
| `make smoke` | single validator against mini fixture |
| `make audit` | run cross_stage --strict against all real-world projects (mini, vol25/real, vol25/recreated, vol26, vol27, vol28 if present) |
| `make burn-in` | show unresolved high-severity BURN_IN items |
| `make metrics` | show dogfood_metrics.csv contents |
| `make clean` | remove caches and venv |

## Maintenance contract

Skill bodies hard-code paths to `~/Claude/research_toolkit/templates/...` and `~/Claude/research_toolkit/references/...`. If you move the toolkit, update those paths in every skill body.

When updating a skill / template / reference, edit the source-of-truth file under `~/Claude/research_toolkit/`. The symlinks in `~/.claude/skills/` track changes automatically.

## TDD discipline

Each skill has a mandatory `## Validation` final step that runs `python ~/Claude/research_toolkit/validators/<name>.py <output_path>`. If validation fails, the skill reports failure with stderr — there is no path to silent partial success.

**Validator scope:** schema-only — fields, types, enums, counts, structural shape. Fast, deterministic, no network IO.

**Validator non-scope:** URL liveness (that's `/url-freshness-check`), content faithfulness (that's `/dossier-audit`), hallucination patterns.

**v1.2+ defensive layer:**
- `cross_stage.py` — claim_family taxonomy consistency between plan + ledger; orphan-arxiv warnings
- arXiv canonical-form check on `primary_url` (rejects `/pdf/` URLs and malformed IDs)
- Memory-verification anti-cheat heuristic (warns when ≥50 entries are all `verified` from memory)

## Filing new issues

Add to both `burn_in.yml` (structured, queryable) and `BURN_IN_NOTES.md` (prose). See `docs/troubleshooting.md` § "How to file a new issue" for the schema.

## License + remote

Personal toolkit on a private GitHub remote. Not designed for outside contribution at this time.

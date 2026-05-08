# research_toolkit

**Six Claude Code skills + validators that turn a research topic into an audited research dossier.**

You give it a topic. It produces a structured bibliography, a topic-organized dossier, a 5-bullet-per-entry agent-readable synthesis, and an audit trail — all gated by schema validators that fail loudly when a stage produces malformed output. Designed for cases where ad-hoc "summarize the LLM literature on X" prompts would produce plausible-but-unverified prose; this gives you a verifiable artifact instead.

Audience: anyone using Claude Code who wants research output with a paper trail. Output reads cleanly for humans and grounds reasoning for future Claude Code agents working in adjacent projects.

## Pipeline

```
topic
  │
  ▼
┌──────────────────────┐
│ /research-plan       │ ─→ research_plan.md          (sub-areas, claim_family taxonomy, scope)
└──────────────────────┘
  │
  ▼
┌──────────────────────┐
│ /research-gather     │ ─→ bib_ledger.yml            (verified primary sources;
└──────────────────────┘                               WebSearch + WebFetch)
  │
  ▼
┌──────────────────────┐
│ /dossier-build       │ ─→ dossier/0K_<topic>.md     (topic tables; one row per entry;
└──────────────────────┘                               per-file letter-prefix anchors)
  │
  ▼
┌──────────────────────┐
│ /agent-index         │ ─→ <consumer>/docs/<topic>/  (5-bullet-per-entry synthesis;
└──────────────────────┘    ├── 0K_<topic>.md          AGENT-INDEX README; lookup recipes;
                            └── README.md              glossary)
  │
  ├──────────────────────────────────────────────┐
  ▼                                              ▼
┌──────────────────────┐                ┌──────────────────────┐
│ /dossier-audit       │ (one round)    │ /url-freshness-check │
│ DROP/CORRECT/FLAG    │ + audit-trail  │ HEAD-checks all URLs │
└──────────────────────┘                └──────────────────────┘
                            │                       │
                            └─── cross_stage ───────┘
                                 (claim_family + orphan-arxiv + stale-ledger checks)
```

Every stage's output is the next stage's input. Every stage has a schema validator that fails loudly on drift. v1.2 added `cross_stage` — a cross-artifact validator that checks the bib_ledger / dossier / agent_index agree on what they're describing.

## Quickstart

```bash
git clone https://github.com/brandon-behring/research_toolkit ~/Claude/research_toolkit
cd ~/Claude/research_toolkit
make install              # .venv + pip install -e ".[dev]"
make test                 # 109 pass + 2 xfailed on a clean checkout

# Make skills discoverable from any project:
mkdir -p ~/.claude/skills
for skill in research-plan research-gather dossier-build agent-index dossier-audit url-freshness-check; do
  ln -s ~/Claude/research_toolkit/.claude/skills/$skill.md ~/.claude/skills/$skill.md
done
```

Then in any Claude Code session:

```
/research-plan "your topic"
/research-gather ~/Claude/research_<slug>/research_plan.md
/dossier-build ~/Claude/research_<slug>/bib_ledger.yml
/agent-index ~/Claude/research_<slug>/dossier --output-dir ~/your_project/docs/<topic>/
/dossier-audit ~/your_project/docs/<topic>/ --focus "<focus area>"
/url-freshness-check ~/your_project/docs/<topic>/
```

For a 5-minute walkthrough: [`docs/getting_started.md`](docs/getting_started.md). For common failures: [`docs/troubleshooting.md`](docs/troubleshooting.md).

## The 6 skills

| Skill | Stage | Input | Output | Validator |
|---|---|---|---|---|
| `/research-plan` | 0 | Topic free-text | `research_plan.md` | `validators/research_plan.py` |
| `/research-gather` | 1 | `research_plan.md` | `bib_ledger.yml` (+ optional `papers/`) | `validators/bib_ledger.py` |
| `/dossier-build` | 2 | `bib_ledger.yml` | N topic dossier files | `validators/dossier.py` |
| `/agent-index` | 3 | Dossier files | Indexed folder + AGENT-INDEX README | `validators/agent_index.py` |
| `/dossier-audit` | 4 | Indexed folder + scope focus | One round of DROP/CORRECT/FLAG fixes + audit-trail note | `validators/audit_trail.py` |
| `/url-freshness-check` | utility | Any markdown folder | URL HEAD-check report | `validators/url_check_report.py` |

## Defensive layer (v1.2+)

Three guardrails the toolkit added after dogfood runs surfaced failure modes:

- **`cross_stage` validator** — claim_family taxonomy consistency between plan and ledger; orphan-arxiv warnings; stale-ledger warnings. `--strict` promotes warnings to errors.
- **arXiv canonical-form check** on `primary_url` — rejects `/pdf/` URLs and malformed IDs at validation time.
- **Memory-verification anti-cheat heuristic** in the bib_ledger validator — warns when ≥50 entries are all `verified` (the signature of a subagent that bulk-marked entries from memory rather than per-entry WebFetch).

Empirical effect: the RLHF run (first dogfood under all v1.2+ guardrails) shipped with 0 hard 404s and 0 audit corrections; the three earlier runs (eval-methodology / PEFT / calibration) averaged ~4 / 3 respectively. See [`evals/dogfood_metrics.csv`](evals/dogfood_metrics.csv) for the trend.

## What to read

| If you want to... | Read |
|---|---|
| Use the toolkit for the first time | [`docs/getting_started.md`](docs/getting_started.md) — 5-min walkthrough |
| Understand a failure / error message | [`docs/troubleshooting.md`](docs/troubleshooting.md) — 7 common failures with symptom→cause→fix |
| See what's been improved version-by-version | [`BURN_IN_NOTES.md`](BURN_IN_NOTES.md) — narrative friction log v1.0 → v1.5.1 |
| Query unresolved issues | `python scripts/burn_in_query.py --status surfaced` |
| See planned future work | [`docs/roadmap_v1_2_through_v1_5.md`](docs/roadmap_v1_2_through_v1_5.md) — sequenced post-v1.1 plan (mostly applied) |
| See reliability across runs | [`evals/dogfood_metrics.csv`](evals/dogfood_metrics.csv) — per-run hard-404 + audit-correction counts |

## Repository layout

```
~/Claude/research_toolkit/
├── README.md                        # this file
├── LICENSE                          # MIT
├── BURN_IN_NOTES.md                 # narrative friction log (v1.0-v1.5.1)
├── burn_in.yml                      # structured BURN_IN index (v1.5)
├── Makefile                         # install / test / audit / burn-in / metrics targets
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
    ├── test_skill_outputs.py        # prompt-injection fixture sanity
    ├── test_recreation_diff.py      # real/ vs recreated/ (2 xfailed baselines)
    ├── test_v1_1_fixes.py           # 27 cases: schema extension + arXiv canonical-form
    ├── test_v1_2_fixes.py           # 14 cases: cross_stage + anti-cheat
    ├── test_v1_3_fixtures.py        # 17 cases: backfilled ledgers + medium fixture
    ├── test_pipeline_e2e.py         # 9 cases: validator chain + idempotency
    ├── test_v1_5_artifacts.py       # 12 cases: docs + burn_in + metrics
    ├── test_v1_5_1_fixes.py         # 12 cases: skill-body lints + audit_trail sequence
    └── fixtures/
        ├── mini_topic_timeseries_anomaly/        # 5 entries (smoke)
        ├── medium_topic_calibration_subset/      # 22 entries (v1.3, schema reference)
        └── prompt_injection_snapshot/{real,recreated}/      # 137 entries (real-world reference)
```

## Make targets

| Command | Effect |
|---|---|
| `make install` | venv + dev deps |
| `make test` | full pytest suite |
| `make smoke` | single validator against the mini fixture |
| `make audit` | run `cross_stage --strict` against all real-world projects |
| `make burn-in` | show unresolved high-severity BURN_IN items |
| `make metrics` | pretty-print `dogfood_metrics.csv` |
| `make clean` | remove caches and venv |

## Maintenance contract

Skill bodies hard-code paths to `~/Claude/research_toolkit/templates/...` and `~/Claude/research_toolkit/references/...`. If you move the toolkit, update those paths in every skill body.

When updating a skill / template / reference, edit the source-of-truth file under `~/Claude/research_toolkit/`. The symlinks in `~/.claude/skills/` track changes automatically.

## TDD discipline

Each skill has a mandatory `## Validation` final step that runs `python ~/Claude/research_toolkit/validators/<name>.py <output_path>`. If validation fails, the skill reports failure with stderr — there is no path to silent partial success.

**Validator scope:** schema-only — fields, types, enums, counts, structural shape. Fast, deterministic, no network IO.

**Validator non-scope:** URL liveness (that's `/url-freshness-check`), content faithfulness (that's `/dossier-audit`), hallucination patterns.

## Filing new issues

Add to both `burn_in.yml` (structured, queryable) and `BURN_IN_NOTES.md` (prose). See `docs/troubleshooting.md` § "How to file a new issue" for the schema.

## License

Personal toolkit released under [MIT](LICENSE). PRs not actively solicited but welcome — best-effort response.

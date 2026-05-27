# research_toolkit

**Claude Code skills + validators that turn a research topic into an audited dossier.**

The toolkit covers two parallel pipelines:

- **Paper synthesis** (6 skills, v1.0+): given a topic, produces a structured bibliography of primary sources + a topic-organized dossier + a 5-bullet-per-entry agent-readable synthesis + an audit trail.
- **Dataset discovery** (3 skills, v1.6+): given a topic, produces a structured ledger of public datasets + a 5-bullet-per-entry dataset dossier (Source / Access / Schema / Size+License / Tasks) — useful when you need "what data exists for this topic" with metadata, not paper bibliography.
- **Strict-live research OS** (2 skills + validators, v2.0): adds field-level evidence, local source caching, freshness blockers, claim-graph JSONL, trust dashboards, and `research-kb` export.

Both pipelines are gated by schema validators that fail loudly when a stage produces malformed output. Designed for cases where ad-hoc "summarize the LLM literature on X" or "find datasets for X" prompts would produce plausible-but-unverified prose; this gives you a verifiable artifact instead.

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

## Dataset pipeline

Same shape, different artifacts: a ledger of public datasets instead of papers, with the same audit + url-check stages reused.

```
topic
  │
  ▼
┌──────────────────────┐
│ /dataset-research    │ — one-shot wrapper for the two stages below
└──────────────────────┘
  │
  ▼
┌──────────────────────┐
│ /dataset-gather      │ ─→ dataset_ledger.yml      (8 source categories: HF /
└──────────────────────┘                             Kaggle / academic / aggregators /
                                                     cloud / domain / gov / classical ML)
  │
  ▼
┌──────────────────────┐
│ /dataset-index       │ ─→ <consumer>/docs/<topic>_datasets/
└──────────────────────┘    (5-bullet entries: Source / Access / Schema /
                             Size+License / Tasks)
  │
  └─→ /dossier-audit (focus="license risks")  +  /url-freshness-check
       (reused; cross_stage --strict catches ledger ↔ synthesis drift)
```

v1.9 extended `cross_stage` so the same orphan / stale-entry detection applies to dataset_ledger ↔ agent_index pairs. v1.9 also codified the compound-license rule (YAML + prose check) after the v1.8 Nectar dogfood surfaced an apache-2.0 declaration with non-commercial restrictions in the prose.

## Quickstart

```bash
git clone https://github.com/brandon-behring/research_toolkit ~/Claude/research_toolkit
cd ~/Claude/research_toolkit
make install              # .venv + pip install -e ".[dev]"
make test                 # full validator/regression suite

# Make skills discoverable from any project:
mkdir -p ~/.claude/skills
for skill in topic-discovery research-plan research-gather dossier-build agent-index dossier-audit url-freshness-check dataset-gather dataset-index dataset-research freshness-audit research-kb-export; do
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

## The skills

### Topic discovery (v2.5)

The front door, upstream of both pipelines: mine a knowledge corpus (e.g. an interview-prep series) into a prioritized, deduplicated backlog of research topics — both `deepen` (frontier subtopics of what the corpus already covers) and `adjacent` (uncovered white-space) — each handing off to `/research-plan`.

| Skill | Stage | Input | Output | Validator |
|---|---|---|---|---|
| `/topic-discovery` | -1 | Knowledge corpus (volumes + learning objectives) | `topic_backlog.yml` | `validators/topic_backlog.py` |

Corpus-internal (no web access). The backlog is append-only and *living*: `scripts/backlog_stamp.py` flips an entry to `status: researched` once its dossier is built, so re-runs dedup. See `references/topic_discovery_protocol.md` for the deepen/adjacent signals + scoring rubric.

### Paper-synthesis pipeline (v1.0+)

| Skill | Stage | Input | Output | Validator |
|---|---|---|---|---|
| `/research-plan` | 0 | Topic free-text | `research_plan.md` | `validators/research_plan.py` |
| `/research-gather` | 1 | `research_plan.md` | `bib_ledger.yml` (+ optional `papers/`) | `validators/bib_ledger.py` |
| `/dossier-build` | 2 | `bib_ledger.yml` | N topic dossier files | `validators/dossier.py` |
| `/agent-index` | 3 | Dossier files | Indexed folder + AGENT-INDEX README | `validators/agent_index.py` |
| `/dossier-audit` | 4 | Indexed folder + scope focus | One round of DROP/CORRECT/FLAG fixes + audit-trail note | `validators/audit_trail.py` |
| `/url-freshness-check` | utility | Any markdown folder | URL HEAD-check report | `validators/url_check_report.py` |

### Dataset-discovery pipeline (v1.6+)

| Skill | Stage | Input | Output | Validator |
|---|---|---|---|---|
| `/dataset-gather` | 1 | Topic free-text | `dataset_ledger.yml` | `validators/dataset_ledger.py` |
| `/dataset-index` | 2 | `dataset_ledger.yml` | Indexed folder with 5-bullet dataset entries (Source/Access/Schema/Size+License/Tasks) | `validators/agent_index.py` |
| `/dataset-research` | wrapper | Topic free-text | Both above in sequence | both validators |

Reuses paper-pipeline's `/dossier-audit` (focus area: "license risks + access stability") and `/url-freshness-check`. Searches 8 source categories — see `references/dataset_sources.md` for the per-source discovery strategy + gotchas.

### Strict-live v2 research OS

| Skill | Stage | Input | Output | Validator |
|---|---|---|---|---|
| `/freshness-audit` | utility | v2 project dir | refreshed ledgers + `dashboard.md` | `validators/freshness.py` |
| `/research-kb-export` | utility | v2 project dir | JSONL inbox file for `~/Claude/research-kb` | `validators/research_kb_export.py` |

v2 projects add `evidence_ledger.yml`, `cache_manifest.yml`, `claim_graph.jsonl`, and `research_kb_export.jsonl`. Full source snapshots are cached locally under `~/Claude/research_cache/` for private research use and later ingestion.

Three helper scripts mechanize the artifacts the skills used to populate by hand:

- `scripts/build_claim_graph.py <project_dir>` — emits `claim_graph.jsonl` from the project's ledgers + evidence_ledger + cache_manifest. Called from `/research-gather` Phase 4.
- `scripts/build_dashboard.py <project_dir> --today <YYYY-MM-DD>` — emits `dashboard.md` with Trust State metrics + per-tier Action Queue (and FACT-framework Claim Health metrics for v3 projects). Called from `/freshness-audit` Phase 5.
- `scripts/verify_citations.py <project_dir>` — mechanical FACT-framework citation auditor for v3 projects. For every `verbatim_match` evidence link, slices the cached `text_path` at the declared byte offset, hashes the slice, and asserts the excerpt matches. Emits `citation_audit_report.md` with per-method breakdown + per-claim grounding strength.

All three validate output before writing and accept `--no-overwrite` to refuse if the target file already exists.

### v2.1 — anti-hallucination upgrade (schema_version 3)

v2.1 adds `schema_version: 3` to evidence_ledger.yml: every `supports[]` link must declare `extraction_method` (verbatim_match / paraphrase / llm_inferred / propagated_from_child / user_asserted / manual_override) + `link_confidence` (0..1, capped per method). For `verbatim_match`, an `excerpt_anchor: {cache_id, text_path_offset, sha256_of_span}` block is required, and the validator mechanically verifies the substring + hash against the cached text — closing the gap between "source is real" and "the link between source and claim is real." Existing v2 fixtures are grandfathered. See `references/strict_live_v2.md` for the full v3 protocol.

The new `/citation-audit` skill runs this verification as a pre-flight before `/research-kb-export`. The `/dossier-audit` skill's Phase 3 now uses CoVE-factored verification (Dhuliawala et al. arXiv 2309.11495) — verification questions answered in fully decoupled sub-agent contexts to prevent post-rationalization.

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
| See what's been improved version-by-version | [`BURN_IN_NOTES.md`](BURN_IN_NOTES.md) — narrative friction log v1.0 → v1.9 |
| Query unresolved issues | `python scripts/burn_in_query.py --status surfaced` |
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
├── .claude/skills/                  # 14 skill bodies (source of truth)
├── templates/                       # 18 schema/structure templates
├── references/                      # 12 protocol docs (audit_protocol, url_check_protocol, ...)
├── validators/                      # 17 schema validators (cross_stage added v1.2)
├── scripts/                         # backfill_ledger, build_medium_fixture, burn_in_query
├── docs/
│   ├── getting_started.md           # onboarding (paper + dataset pipelines)
│   └── troubleshooting.md           # common failures v1.0 → v1.9
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
| `make symlinks` | symlink all skill bodies into `~/.claude/skills/` |
| `make test` | full pytest suite |
| `make smoke` | single validator against the mini fixture |
| `make v2-smoke` | strict-live v2 validator chain against the v2 fixtures (`ai_agents` + `multi_entry`) |
| `make builders-smoke` | run `scripts/build_claim_graph.py` + `scripts/build_dashboard.py` against the v2 fixture (outputs to `/tmp`, validates) |
| `make audit` | run `cross_stage --strict` against all real-world projects |
| `make audit-strict` | CI-style strict audit target that fails on validator failures |
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

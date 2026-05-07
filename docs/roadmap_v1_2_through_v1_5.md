# research_toolkit roadmap — v1.2 through v1.5

Forward plan to address the 10 post-v1.1 improvement items identified in the
2026-05-07 cross-vol audit. Each version is a coherent ship goal with its own
acceptance criteria; ship them in order, but a later version can be reordered
or dropped without invalidating earlier ones.

## Decisions captured 2026-05-07

Four scope choices made before this roadmap was committed:

1. **Roadmap is aspirational, not a ship commitment.** This document exists so
   future-you (or future Claude Code agents reading the repo cold) can find the
   sequenced plan; executing any of v1.2-v1.5 is a separate decision per
   version, gated by its own clarifying-question round.
2. **v1.3 backfill scope: all 3 vols.** vol26 + vol27 + vol28 = ~227 entries
   gain `authors` / `venue` / `code_url`. Even though vol26 is shipped
   methodology, the backfill makes future re-runs deterministic for any vol.
3. **Audience: future-you + future Claude Code agents.** v1.5 docs (B7) are
   *tight* — ~80 lines getting_started, ~60 lines troubleshooting. Not full
   onboarding for external collaborators; not a screencast. The audience reads
   the repo cold and needs to be productive in <10 minutes.
4. **vol29+ is planned.** v1.5 reliability metrics CSV (C9) is high-value
   *because* there will be more dogfood runs to track. Every future vol logs
   to `evals/dogfood_metrics.csv`; trend visible after 2-3 runs.

These choices are baked into the v1.3 and v1.5 sections below.

| Version | Theme | Items | Effort | Risk |
|---|---|---|---|---|
| v1.2 | Defensive hardening | A2, A3, A4, B6 | 1-2 sessions | Low — pure tooling |
| v1.3 | Data + fixture grounding | A1, C10 | 2-3 sessions | Medium — touches real ledgers |
| v1.4 | Pipeline test surface | B5 | 1 session | Low — adds to existing harness |
| v1.5 | Operations & ergonomics | B7, C8, C9 | 1-2 sessions | Low — write-once polish |

Total: ~5-8 sessions of work. Each version is independently shippable.

---

## v1.2 — Defensive hardening

**Goal:** make the toolkit *resistant to subagents misbehaving* rather than just
*requesting that subagents behave*. Subagent prompt adherence will always be
probabilistic; validator-level checks are deterministic.

### Items

**A2. Cross-stage consistency validator** — `validators/cross_stage.py`
- Takes a project directory containing `bib_ledger.yml`, `dossier/`, `agent_index/`.
- Asserts: set of bibkeys in `bib_ledger.yml` ⊇ set of `**Source:**` URLs / bibkey
  references in `dossier/*.md` and `agent_index/0*.md` (entries can be in the
  ledger but not yet rendered; cannot be rendered without a ledger entry).
- Asserts: per-claim_family entry count in bib_ledger matches the per-file row
  count in `dossier/`.
- Asserts: total `**Source:**` lines in `agent_index/0*.md` matches total entries
  in `bib_ledger.yml` (excluding 00_overview.md and README.md).

**A3. Memory-verified anti-cheat heuristic** — extend `validators/bib_ledger.py`
- New optional warning category (NOT a hard error): if `>=50` entries AND
  `verified` ratio == 1.0 AND no audit-trail entry yet, emit a warning. The
  warning is informational; it doesn't fail validation, but `make test`
  surfaces it.
- Add a `--strict` flag that promotes warnings to errors for CI gating.

**A4. Resolve or xfail the 2 baseline test fails**
- Re-run vol25 recreation under v1.1 skills (which now have per-file letter-prefix
  codified + dash-default URLs + count-assertion). Expect: section_anchors_match
  passes; entry_counts_within_tolerance may still fail if the bibliography drift
  is real.
- For whatever doesn't pass: `@pytest.mark.xfail(strict=True, reason="<vol25
  drift, see BURN_IN_NOTES.md §...>")`. The `strict=True` matters — it surfaces
  if the test starts passing again.

**B6. CI inventory + gate audit**
- Read `.github/workflows/test.yml` and confirm: runs `make test` on push/PR,
  matrix covers Python 3.11+ at minimum, runs validators against vol25 fixtures
  not just mini.
- If gaps: file a follow-up PR adding the missing gates.

### Deliverables

- `validators/cross_stage.py` (new, ~80-120 lines)
- Modified `validators/bib_ledger.py` (memory-verified heuristic, ~30 lines)
- Modified `tests/test_recreation_diff.py` (xfail markers)
- Possibly modified `.github/workflows/test.yml`

### Tests

- `tests/test_v1_2_fixes.py` (new, ~15-20 cases):
  - Cross-stage: positive (consistent fixture passes); negative (orphan bibkey
    in dossier fails); negative (count drift fails).
  - Memory-verified heuristic: positive (small ledger or with audit notes
    passes); negative (large all-verified ledger emits warning).
  - `--strict` flag promotes warning to error.

### Acceptance criteria

- `make test` reports green (0 fail, 0 unexpectedly-passing xfail).
- Cross-stage validator catches a deliberately-orphan bibkey in vol25/recreated
  test variant.
- CI workflow gates merges to main on v1.2 test suite.

---

## v1.3 — Data + fixture grounding

**Goal:** make the v1.1 schema extension *useful* by populating the optional
fields in existing ledgers, and stress-test the dossier-build logic at the size
where it actually breaks.

### Items

**A1. Backfill `authors`/`venue`/`code_url` in vol26/27/28 ledgers (all 3 vols, ~227 entries)**
- Programmatic backfill of `authors` via bibkey-heuristic (with manual review
  for surnames known to be tricky — Ben-Zaken, Rücklé, etc.).
- Manual `venue` backfill: ~72 entries in vol26 + ~67 in vol27 + ~88 in vol28
  = ~227 lookups. Spread across ~3 sessions. Use vol25/real's existing venue
  claims as reference where overlap exists. vol26 is included even though
  shipped — backfilling makes future re-runs deterministic.
- `code_url` backfill: opt-in, only for entries where the canonical repo is
  *known* (not guessed). Use the v1.1 BURN_IN finding as the rule:
  `pilancilab/spectral_adapter`-style lab repos and `EricLBuehler/xlora`-style
  unrelated handles — populate when WebFetch-confirmed, otherwise omit.

**C10. Medium fixture** — `tests/fixtures/medium_topic_calibration_subset/`
- ~30 entries from the vol28 calibration ledger (subset across 4 claim_families).
- Exercises sub-section logic (file 02 with B1-B6 anchors at scale) that the
  mini fixture (5 entries) can't reach.
- Includes a populated `authors`/`venue`/`code_url` set on every entry —
  serves as the reference example for v1.1+ ledger format.

### Deliverables

- 3 backfilled ledger files (`research_vol26/`, `research_vol27/`,
  `research_vol28/bib_ledger.yml`).
- New `tests/fixtures/medium_topic_calibration_subset/` directory with all 4
  artifacts (research_plan, bib_ledger, dossier, agent_index).
- Documentation update: `templates/bib_ledger.template.yml` shows the medium
  fixture as the reference example.

### Tests

- `tests/test_v1_3_fixtures.py`:
  - Each backfilled ledger validates cleanly.
  - Cross-stage validator (from v1.2) passes on all backfilled vols.
  - Medium fixture passes all 6 validators.
  - Medium fixture's optional-field coverage is ≥80% (every entry has at
    least one of authors/venue/code_url populated).

### Acceptance criteria

- vol26/27/28 ledgers have ≥80% coverage on `authors` and `venue` fields,
  ≥40% coverage on `code_url`.
- Medium fixture is referenced by `dossier-build.md` skill body as the
  worked example.
- No regression on v1.1 + v1.2 test suites.

---

## v1.4 — Pipeline test surface

**Goal:** catch contract drift between stages with a real end-to-end test,
rather than relying on manual dogfood runs to surface mismatches.

### Items

**B5. End-to-end pipeline smoke test** — `tests/test_pipeline_e2e.py`
- Drives all 6 stages against the medium fixture (from v1.3).
- Mocks WebSearch/WebFetch via a fixture-baked URL→response cache (no network
  dependence in CI).
- Asserts each stage's output validates AND each stage's output is a valid
  input to the next stage (the cross-stage validator from v1.2 doubles as
  the inter-stage contract check).
- Final assertion: round-trip stability — re-running stages 3-6 against the
  unchanged bib_ledger produces byte-identical output (modulo timestamps).

### Deliverables

- `tests/test_pipeline_e2e.py` (~150 lines).
- `tests/fixtures/medium_topic_calibration_subset/web_cache.json` — baked
  WebFetch responses for the ~30 entries (one-time effort, regenerable
  via a helper script).
- `tests/helpers/web_cache.py` — mock WebFetch backend reading from
  `web_cache.json`.

### Tests

The new test file IS the test. Internally it has ~10-15 assertions across the
6 pipeline stages.

### Acceptance criteria

- E2E smoke test runs in <30 seconds against the medium fixture.
- Test catches a deliberate Stage 3 schema regression (mutate the dossier
  template; E2E should fail with a clear stage-boundary error).
- CI gates merges on the E2E test passing.

---

## v1.5 — Operations & ergonomics

**Goal:** lower the onboarding cliff for anyone who isn't already deep in
the toolkit, and make the BURN_IN log queryable for trend analysis.

### Items

**B7. Getting-started + troubleshooting docs (audience: future-self + future agents)**
- `docs/getting_started.md` (~80 lines): tight 5-minute walkthrough — install,
  run /research-plan on a tiny topic, see the 6-stage output. Audience is
  future-you OR a future Claude Code agent reading the repo cold; not external
  collaborators. No screencast, no example walkthrough beyond the bare
  end-to-end run, no skill-by-skill quickref.
- `docs/troubleshooting.md` (~60 lines): BURN_IN-distilled common failures
  with symptom→cause→fix structure. Top candidates: macOS URL regex returns 0,
  validator ModuleNotFoundError, GitHub URL 404 cluster, Stage 2 memory-verified
  inflation, count-mismatch warnings.

**C8. Structured BURN_IN log** — `burn_in.yml` (companion to BURN_IN_NOTES.md)
- One YAML entry per finding: `{id, phase, stage, finding, status, fix_commit,
  fix_version, severity}`.
- BURN_IN_NOTES.md prose remains; YAML is the queryable index.
- Helper script `scripts/burn_in_query.py` for filtering ("show all unresolved
  high-severity findings").

**C9. Reliability metrics tracking** — `evals/dogfood_metrics.csv` (high-value: vol29+ planned)
- One row per dogfood run: `{date, vol, total_entries, total_urls,
  hard_404_count, attribution_corrections_in_audit, version_skill_used}`.
- Initial seeding: 5 rows for vol25/recreated + vol26 + vol27 + vol28 + (the
  v1.3-medium-fixture run if it counts as dogfood).
- Future runs append to this file as part of the BURN_IN-write step.
- **Real signal expected after 2-3 future vols.** vol29+ is planned per the
  decisions captured at the top of this document; the trend visible in this
  CSV is the only quantitative answer to "did v1.1+ actually reduce failure
  rates" beyond the n=2 vol27/vol28 baseline.

### Deliverables

- `docs/getting_started.md` (~80-120 lines).
- `docs/troubleshooting.md` (~60-100 lines).
- `burn_in.yml` (initial seed: ~50 entries from existing BURN_IN_NOTES.md).
- `scripts/burn_in_query.py` (~40 lines).
- `evals/dogfood_metrics.csv` with header + 4-5 backfilled rows.

### Tests

- `tests/test_v1_5_artifacts.py`:
  - `burn_in.yml` validates against a small JSON Schema.
  - `dogfood_metrics.csv` parses without error and has ≥4 rows.
  - `getting_started.md` example commands are syntactically valid (don't
    actually run the network calls; just bash-syntax check).

### Acceptance criteria

- A first-time user following `getting_started.md` produces a valid
  agent_index in <10 minutes.
- `burn_in_query.py --severity high --status open` returns a list (catches
  unresolved high-priority items).
- Dogfood metrics file is appended automatically by the next run (not
  manually maintained).

---

## Out of all-versions scope

These were considered and explicitly deferred:

- **Pydantic / config framework / packaging changes** — out of scope per
  CLAUDE.md "no thin dependency wrappers."
- **Auto-iterating audit during /dossier-audit** — single-round per design;
  user controls iteration. Unchanged.
- **New skills (`/dossier-export`, `/dossier-merge`, etc.)** — surface as a
  separate plan if a need emerges. v1.x is hardening the existing 6 skills,
  not adding new ones.
- **Re-architecting validators to non-schema content checks beyond what v1.2
  adds** — content correctness is the audit stage's job, not the validator's.

---

## Decision points along the way

After each version, ask:

- Did the items reduce the BURN_IN findings rate in the next dogfood run?
  (Track via v1.5 metrics CSV once that ships.)
- Did any acceptance-criterion test stay flaky? Investigate before moving on.
- Did anyone but the original author run the toolkit end-to-end? (v1.5
  getting-started doc is the gate for this.)

If 2+ versions ship and dogfood reliability hasn't measurably improved, the
roadmap was wrong — pause and re-audit before continuing.

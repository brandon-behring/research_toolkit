# Roadmap — v2.6: trustworthy, autonomous, committed pipeline

Living tracking doc for the v2.6 milestone. Phases are executed in
reviewed, per-phase-approval increments (each = branch + PR + green
pytest/validators). Structured friction items live in
[`../burn_in.yml`](../burn_in.yml) under phase label `v2.6 Planning`
(ids `v26-*`); narrative companion in
[`../BURN_IN_NOTES.md`](../BURN_IN_NOTES.md). Approved plan source:
`~/.claude/plans/make-sure-we-are-shiny-moon.md`.

## Milestone goal

Make the dossier-building pipeline **trustworthy**, **autonomous**, and
**committed**. The #1 goal is **machine-checkable trust**: the dossiers feed
`research-kb` and are read downstream by an AI consumer via the exported claim
graph, so trust guarantees must be enforced by committed validators, not just
documented. The product is a one-command `/research <topic>` that returns a
finished, validated dossier — or halts on a resumable checkpoint, never
auto-shipping a broken one.

## Why now

The 4-topic strict-live batch surfaced that the spine of the pipeline is not in
the repo:

- The real artifact **assembler** and **renderer** live as ~13 uncommitted
  `~/Claude/_*.py` scratch files — including `_render_topicN.py` re-authored at
  ~200 hand-edited lines **per topic**. Zero version control, zero tests.
- There is **no CLI** entry point: every stage is `python scripts/foo.py`,
  chained by hand per topic.
- Long gather sub-agents hold sources **in memory** and lose everything on a
  socket drop (topic-4 lost ~3.6h; recoverable only because the cache is
  content-addressed).
- Several trust guarantees are **documented-but-unenforced** — most notably the
  display≠evidence rule (rendered Mechanism sentence must be a verbatim cache
  substring), which is applied only by the uncommitted local renderers.

So the ordering is: commit the pipeline (the deterministic spine) first, then
the #1 trust work, then resumability, then the autonomous payoff.

## Design decisions

- **Failure mode:** on a validator failure the autonomous `/research` does
  **bounded auto-retry, then halt + checkpoint**. It never auto-ships or stamps
  a broken dossier.
- **Export-contract redesign is DEFERRED** to a separate follow-up milestone.
  v2.6 hardens the *trust of what is produced*, not the export schema. The new
  trust fields ride in the existing export payload verbatim so a later milestone
  can promote them to first-class queryable fields.

## Phases

### Phase 0 — record the roadmap (no code)

- **Goal:** track the milestone in the repo so the work is visible + queryable.
- **Deliverables:** this `docs/ROADMAP_v2_6.md`; v2.6 friction items filed into
  `burn_in.yml` (+ a dated `BURN_IN_NOTES.md` session line).
- **Acceptance:** one commit `docs(roadmap): v2.6 milestone + friction backlog`;
  `burn_in.yml` still parses.

### Phase 1 — kill the scratch-helper debt (the spine)

- **Goal:** commit the assembler/renderer/merge so the rest of the milestone has
  deterministic, testable code to build on.
- **Deliverables:**
  - `scripts/assemble_artifacts.py` (from `~/Claude/_assemble.py`):
    sources-JSON + cache → bib/evidence/cache_manifest/gather_trace, emitting
    `published_online`. Reuses committed `build_excerpt_anchor` +
    `v2_common.verify_excerpt_anchor` for anchoring (drop the hand-rolled
    `anchor()`).
  - `scripts/render_agent_index.py` (parameterizes the `_render_topicN.py`
    family): one driver + a **sidecar config**
    (`templates/render_config.schema.yml` + per-topic `render_config.yml`:
    RESULT lines, FAMILIES, glossary, recipes, README scope). Bakes in the
    `verify_display` guard.
  - `scripts/compose_cross_project_kg.py` (commits + env-parameterizes
    `_merge_projects.py` / `_merge_tracks.py`; strips wave/date hardcodes).
  - Retire scratch twins (`_anchor_tmp.py`, `_build_excerpt_anchor.py`); dedup
    `ARXIV_ID_RE` / `ARXIV_OLD_ID_RE` / `DOI_RE` into `validators/_common.py`.
- **Acceptance:** **parity test** — re-run a finished topic
  (incrementality-geo-lift) through the new committed scripts; output reproduces
  the shipped dossier and passes citation-audit 100%. Unit tests per script.

### Phase 2 — trust enforcement (the #1 goal)

- **Goal:** make trust machine-checkable, since an AI consumes the claim graph.
- **Deliverables:**
  - `validators/agent_index_display.py`: every rendered Mechanism display
    sentence must be a raw-byte cache substring; wired into
    cross_stage / citation-audit. (Enforceable now that the renderer is
    committed.)
  - `published_online` → staleness: extend `v2_common.stale_error_for_entry`
    with a content-age **WARNING** (not hard-fail) relative to tier — finishes
    the deferred half of PR #30.
  - `link_confidence` tiers in `validators/evidence_ledger.py`:
    verbatim_match / user_asserted ≥ 0.85; paraphrase / manual_override ≤ 0.80;
    llm_inferred ≤ 0.70.
  - Claim-excerpt **relevance** WARNING in `verify_citations.py`: keyword-overlap
    flag for likely quote-mining (excerpt verbatim but off-topic) — warning-only,
    documented as a known limitation.
- **Acceptance:** intentional-violation fixtures caught for each check (display
  drift, mis-tiered confidence, stale content-age, quote-mine flag). Commits per
  check.

### Phase 3 — reliability & resumability

- **Goal:** autonomy can't be fragile — a dropped agent must not lose work.
- **Deliverables:**
  - `scripts/resume_gather_from_cache.py`: scan
    `research_cache/metadata/sha256/*.json` for `topic==<slug>`, rebuild a
    sources-JSON skeleton from clean blobs (the topic-4 manual recovery, made one
    command).
  - **Incremental-write discipline** in `.claude/skills/research-gather.md`
    (write each source as confirmed, not in-memory-then-dump) + a documented
    resume path; update `references/agent_discipline.md`.
- **Acceptance:** resume script rebuilds a sources set from a fixture cache.

### Phase 4 — autonomous orchestration + ergonomics (the payoff)

- **Goal:** one command per topic; zero-touch on the happy path.
- **Deliverables:**
  - `/research` skill: chains plan → gather → assemble → index → citation-audit
    → freshness → export → stamp. On a validator failure, **bounded auto-retry
    first** (re-fetch / re-anchor / re-pick excerpt, capped attempts), then
    **halt + checkpoint** if recovery fails — never auto-ship/stamp broken.
    Resume support.
  - Unified CLI: `[project.scripts]` → `research-toolkit <subcommand>`.
  - Stale-doc fixes: drop `--cache-pdfs` from the runbook (not a real flag);
    `<TODAY>` auto-fill / make-target; reconcile skill `verification_method`
    examples with the validator enum; pin allowed enums in the gather brief.
- **Acceptance:** `/research` halts + checkpoints on an injected validator
  failure; CLI subcommands run. Commits per sub-item.

### Phase 5 — great tests + clear docs + release

- **Goal:** lock the milestone in with coverage, an architecture doc, and a tag.
- **Deliverables:**
  - Audit + extend `tests/test_pipeline_e2e.py` to a full fixture build
    (plan → assemble → render → claim-graph → citation-audit → freshness →
    export) asserting schema + integrity + 100% citation pass + the new export
    trust fields. Add `make e2e`.
  - `docs/architecture.md`: producer / verifier / agent-authored map;
    display≠evidence; the trust model's guarantees **and honest holes**
    (substring ✓, relevance ✗→warning, content-age ✓→warning); the export
    contract for AI consumers.
  - References hygiene (JS-render note in `citation_rules.md`, cache-identity in
    `url_check_protocol.md`, YAML leading-quote in `code-style.md`); update
    `README.md` + `CLAUDE.md` index.
  - Release v2.6 per the release process (bump pyproject + cache UA, BURN_IN
    summary, annotated `v2.6.0` tag).
- **Acceptance:** `make e2e` builds a fixture dossier end-to-end green; v2.6
  tagged.

## Sequencing prerequisite

PR #30 (`published_online` + arXiv preference) is open; Phase 2's staleness item
builds on it. Recommended: merge #30 first, branch v2.6 phases off `main`.

## Deferred / out of scope

- **Export-contract redesign for AI consumers** — making grounding-strength /
  `link_confidence` / content-age / audit-status first-class queryable export
  fields + an export-schema validator. Its own follow-up milestone; v2.6's trust
  fields ride in the existing payload so it can promote them later.
- **Cross-project KG merge at scale** beyond committing the script.
- **HTML / interactive dashboard.**
- **Schema-migration framework.**

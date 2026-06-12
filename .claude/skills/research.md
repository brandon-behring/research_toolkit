---
name: research
description: Use when the user wants one command to take a topic from scratch to a finished, validated strict-live dossier. Chains research-plan -> research-gather -> assemble -> render-index -> build-claim-graph -> citation-audit -> freshness -> export -> backlog-stamp, running each stage's validator as a gate; on failure it bounded-auto-retries then halts on a resumable checkpoint, never auto-shipping a broken dossier.
allowed-tools: Read, Write, Edit, Bash, WebSearch, WebFetch
---

# /research — End-to-end strict-live dossier orchestrator

## Usage

```
/research "<topic>" [--output-dir <project_dir>] [--today YYYY-MM-DD]
```

**Examples:**
```
/research "Adaptive jailbreak attacks 2024-2025"
/research "Incrementality and geo-lift measurement" --output-dir ~/Claude/research-dossiers/research_incrementality_geo_lift/ --today 2026-06-01
```

**Default project dir**: `~/Claude/research-dossiers/research_<slug>/` where `<slug>` is the topic
snake_cased. **Default `--today`**: the run date (YYYY-MM-DD) — fill it in once
and reuse it for every stage so freshness math is consistent.

## When to use

- The user wants a **one-command, zero-touch happy path**: topic in, finished +
  validated strict-live dossier out (or a clean halt on a checkpoint).
- The topic has **no existing dossier** (greenfield) OR a partially-built one to
  resume (gather dropped, an artifact needs a fix).
- NOT for a quick scoping pass alone (use `/research-plan`) or a single stage in
  isolation (run that stage's skill directly).
- NOT for datasets — use `/dataset-research` for the dataset pipeline.

This is an orchestrator. Each numbered stage below IS the corresponding skill /
script; read that skill for its full semantics + HARD RULES. The orchestrator's
job is sequencing, per-stage validator gating, and the failure policy.

## Workflow

Run the stages **in order**. **Each stage ends by running its validator; the
next stage starts only on a green (exit-0) validator.** Never carry a non-zero
validator forward. Dogfood the **committed** Phase-1 scripts
(`scripts/assemble_artifacts.py`, `scripts/render_agent_index.py`,
`scripts/build_claim_graph.py`) and the resume tool
(`scripts/resume_gather_from_cache.py`) — NOT the retired `~/Claude/_*.py`
scratch helpers.

Set `<proj>` = the project dir and `<TODAY>` = the run date once, up front.

### Stage 1 — plan (`/research-plan`)

```bash
/research-plan "<topic>" --output <proj>/research_plan.md
python ~/Claude/research_toolkit/validators/research_plan.py <proj>/research_plan.md
```
Gate: validator exit 0 (H1, 4–8 sub-areas, non-empty out-of-scope, ≥3
claim_family entries). Skip Stage 1 only when resuming a topic that already has
a validated plan.

### Stage 2 — gather (`/research-gather`)

```bash
/research-gather <proj>/research_plan.md
python ~/Claude/research_toolkit/validators/bib_ledger.py <proj>/bib_ledger.yml
python ~/Claude/research_toolkit/validators/gather_trace.py <proj>/gather_trace.yml
```
Apply the **incremental-write discipline** (Phase 3): append each source to the
on-disk artifacts the moment it is confirmed + cached + anchored — never hold
sources in memory to dump at the end. If gather drops, **resume from the
content-addressed cache** rather than restarting:
```bash
python ~/Claude/research_toolkit/scripts/resume_gather_from_cache.py <slug> \
  --out <proj>/<slug>_sources.recovered.json
```
Gate: `bib_ledger.py` exit 0 AND `gather_trace.py` exit 0.

### Stage 3 — assemble (`scripts/assemble_artifacts.py`)

Build the v2 artifacts from the gather sources JSON + the content cache:
```bash
python ~/Claude/research_toolkit/scripts/assemble_artifacts.py \
  <proj>/<slug>_sources.json <proj>
python ~/Claude/research_toolkit/validators/evidence_ledger.py <proj>/evidence_ledger.yml
python ~/Claude/research_toolkit/validators/cache_manifest.py <proj>/cache_manifest.yml
```
Gate: both validators exit 0. (Assemble emits bib/evidence/cache_manifest/
gather_trace, including `published_online`, reusing `build_excerpt_anchor` +
`v2_common.verify_excerpt_anchor` for anchoring.)

### Stage 4 — render-index (`scripts/render_agent_index.py` + `render_config.yml`)

Write a `<proj>/render_config.yml` first (RESULT lines, families, glossary,
recipes, README scope) — copy `templates/render_config.example.yml` and fill it;
the script REQUIRES it and errors if absent. Then render + validate:
```bash
python ~/Claude/research_toolkit/scripts/render_agent_index.py \
  <proj>/<slug>_sources.json <proj> --config <proj>/render_config.yml --today <TODAY>
python ~/Claude/research_toolkit/validators/agent_index.py <proj>/agent_index
python ~/Claude/research_toolkit/validators/agent_index_display.py <proj>
python ~/Claude/research_toolkit/validators/cross_stage.py <proj> --strict
```
Gate: all three validators exit 0. `agent_index_display.py` enforces the
**display≠evidence** rule (every rendered Mechanism sentence is a raw-byte cache
substring); `cross_stage.py --strict` catches claim_family drift + orphan arXiv
IDs.

### Stage 5 — build-claim-graph (`scripts/build_claim_graph.py`)

```bash
python ~/Claude/research_toolkit/scripts/build_claim_graph.py <proj>
python ~/Claude/research_toolkit/validators/claim_graph.py <proj>/claim_graph.jsonl
```
Gate: builder exit 0 (it self-validates before writing) AND `claim_graph.py`
exit 0.

### Stage 6 — citation-audit (`scripts/verify_citations.py`)

```bash
python ~/Claude/research_toolkit/scripts/verify_citations.py <proj>
echo "Exit code: $?"  # 0 = all substrings pass; 1 = substring failures
```
Gate: exit 0 — **MUST report clean before export**. A substring failure here is
a trust violation; do not export.

### Stage 7 — freshness (`validators/freshness.py` + `scripts/build_dashboard.py`)

```bash
python ~/Claude/research_toolkit/validators/freshness.py --strict <proj>
python ~/Claude/research_toolkit/scripts/build_dashboard.py <proj> --today <TODAY>
python ~/Claude/research_toolkit/validators/freshness.py --strict <proj>
```
Refresh any stale primary sources (re-cache + re-anchor), rebuild the dashboard,
then re-run `--strict`. Gate: the final `freshness.py --strict` exits 0 (no
stale blockers, evidence/cache referential integrity holds, anchors verify).

### Stage 8 — export (`scripts/research_kb_export.py`)

```bash
python ~/Claude/research_toolkit/scripts/research_kb_export.py <proj>
python ~/Claude/research_toolkit/validators/research_kb_export.py \
  <project_dir>/synthesis_export.jsonl
```
Gate: exporter exit 0 AND export validator exit 0. **Never reach this stage with
a non-clean citation-audit or a failing freshness `--strict`.**

### Stage 9 — backlog-stamp (`scripts/backlog_stamp.py`)

```bash
python ~/Claude/research_toolkit/scripts/backlog_stamp.py \
  ~/Claude/topic_backlog.yml <topic_id> \
  --status researched --dossier <proj>/agent_index --today <TODAY>
```
Stamp ONLY after a clean export, so re-runs of `/topic-discovery` dedup the
finished topic. (Skip silently if the topic has no backlog entry.)

### Failure handling (bounded auto-retry -> halt + checkpoint; never auto-ship)

This is the user's explicit policy. On a stage/validator failure:

1. **Bounded auto-retry first** — attempt the failed stage again, capped at
   **3 attempts total per stage**, applying the narrowest fix that addresses the
   reported error:
   - **gather**: a dead/403/429/JS-stub source -> re-fetch with
     `--escalate-on-failure`; a missing sub-area -> re-run only that sub-area.
   - **assemble / display drift**: a Mechanism sentence that is not a verbatim
     cache substring -> re-pick a genuinely-anchoring excerpt (or re-extract the
     cached blob), then re-assemble / re-render.
   - **citation-audit substring failure**: fix the offending excerpt/anchor at
     the source artifact, then re-run the stage.
   - **freshness stale/ref error**: refresh the stale source (re-cache +
     re-anchor) or fix the dangling evidence_id/cache_id, then re-run `--strict`.
   - transient network/tooling errors -> simple retry.
2. **Halt + checkpoint** — if the capped retries still fail, **STOP**. Do NOT
   proceed to the next stage, do NOT export, do NOT stamp. Leave a resumable
   checkpoint and tell the user exactly where to resume:
   - gather not yet complete -> point at
     `scripts/resume_gather_from_cache.py <slug>` (the cache is the checkpoint).
   - a built artifact is wrong -> name the specific file to fix
     (`evidence_ledger.yml` entry, `render_config.yml` RESULT line, the failing
     `claim_id`) + the exact validator command that is red.
   Report: which stage failed, the validator's stderr, the attempts made, and
   the one resume command / file to fix.

**HARD RULE:** never auto-advance past a red validator, and never export or
backlog-stamp a dossier whose citation-audit is non-clean or whose freshness
`--strict` is failing. A halt on a checkpoint is the success-shaped outcome of a
failure — a shipped broken dossier is not.

## Templates

- [`render_config.example.yml`](~/Claude/research_toolkit/templates/render_config.example.yml) — fill per topic for Stage 4.
- [`render_config.schema.yml`](~/Claude/research_toolkit/templates/render_config.schema.yml) — render config field reference.
- [`research_plan.template.md`](~/Claude/research_toolkit/templates/research_plan.template.md) — Stage 1 structure.
- [`bib_ledger.template.yml`](~/Claude/research_toolkit/templates/bib_ledger.template.yml) — Stage 2 schema.
- [`evidence_ledger.template.yml`](~/Claude/research_toolkit/templates/evidence_ledger.template.yml) + [`cache_manifest.template.yml`](~/Claude/research_toolkit/templates/cache_manifest.template.yml) — Stage 3 artifacts.

## References

- [`citation_rules.md`](~/Claude/research_toolkit/references/citation_rules.md) — URL forms, bibkey convention, no-LLM-specifics rule.
- [`agent_discipline.md`](~/Claude/research_toolkit/references/agent_discipline.md) — tool-call budget, mid-phase validator checkpoints, incremental-write + cache-as-checkpoint resume.
- [`strict_live_v2.md`](~/Claude/research_toolkit/references/strict_live_v2.md) — evidence/cache/freshness artifact schema + path portability.
- Per-stage skills for full semantics: `/research-plan`, `/research-gather`, `/agent-index`, `/citation-audit`, `/freshness-audit`, `/synthesis-export`.

## Validation

The orchestrator has no validator of its own — **its correctness IS the
per-stage validator gates above**. Every stage must end on a green validator
before the next begins, and the run is "complete" only when Stage 8's export
validator passes (Stage 9 is bookkeeping). If any gate is red after bounded
retry, the run HALTS on a checkpoint (see Failure handling) and reports failure
— it never reports a partial run as success.

```bash
# At the end of a successful run, these should all exit 0:
python ~/Claude/research_toolkit/scripts/verify_citations.py <proj>          # citation audit clean
python ~/Claude/research_toolkit/validators/freshness.py --strict <proj>     # no stale blockers
python ~/Claude/research_toolkit/validators/research_kb_export.py \
  <project_dir>/synthesis_export.jsonl                    # export well-formed
```

## Output / handoff

**Produces (in `<proj>`):**
- `research_plan.md`, `bib_ledger.yml`, `gather_trace.yml`
- `evidence_ledger.yml`, `cache_manifest.yml`, `claim_graph.jsonl`
- `render_config.yml`, `agent_index/` (README + 5-bullet entry files), `dashboard.md`
- `citation_audit_report.md`
- `~/Claude/research_cache/` blobs (gitignored, content-addressed)
- `<project_dir>/synthesis_export.jsonl` (export envelope)
- a stamped `~/Claude/topic_backlog.yml` entry

**Consumed by:** `~/Claude/research-kb` ingestion (downstream AI consumer reads
the exported claim graph). Re-audit any time with `/citation-audit`,
`/freshness-audit`, or `/dossier-audit`.

**On halt:** the partial artifacts + the content cache are intact and resumable;
the report names the single resume command / file to fix.

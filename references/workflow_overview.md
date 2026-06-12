# Workflow overview

The research_toolkit codifies a staged research workflow plus utility skills.
Each stage produces a typed artifact that the next stage consumes. v2 adds a
strict-live research OS layer for evidence, cache, freshness, dashboards, and
`research-kb` export.

## Stage diagram

```
┌────────────────┐    ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ /research-plan │───▶│ /research-gather │───▶│  /dossier-build  │───▶│   /agent-index   │───▶│  /dossier-audit │
│                │    │                  │    │                  │    │                  │    │                 │
│ research_plan. │    │  bib_ledger.yml  │    │  N topic files   │    │ indexed folder + │    │ DROP/CORRECT/   │
│      md        │    │  + papers/       │    │ (Markdown tables)│    │ AGENT-INDEX      │    │ FLAG round +    │
│                │    │  + cache/        │    │                  │    │ README           │    │ audit-trail note│
└────────────────┘    └──────────────────┘    └──────────────────┘    └──────────────────┘    └─────────────────┘
        │                                                                                              │
        │                                                                                              │ (re-invoke
        │                                                                                              │  per round)
        ▼                                                                                              ▼
   validators/                                                                                  validators/
   research_plan.py                                                                              audit_trail.py

       ┌──────────────────────┐
       │ /url-freshness-check │   (utility — invokable on any markdown collection)
       └──────────────────────┘

       ┌──────────────────────┐      ┌──────────────────────┐
       │   /freshness-audit   │─────▶│ /synthesis-export  │
       │ v2 trust/dashboard   │      │ JSONL ingestion feed │
       └──────────────────────┘      └──────────────────────┘
```

## Stage handoffs

| Stage | Skill | Reads | Writes | Validator |
|---|---|---|---|---|
| 0 | `/research-plan` | Topic free-text | `research_plan.md` | `validators/research_plan.py` |
| 1 | `/research-gather` | `research_plan.md` | `bib_ledger.yml`, `papers/`, `cache/` | `validators/bib_ledger.py` |
| 2 | `/dossier-build` | `bib_ledger.yml` | N topic dossier files | `validators/dossier.py` |
| 3 | `/agent-index` | Dossier files | Indexed folder (5-bullet + AGENT-INDEX) | `validators/agent_index.py` |
| 4 | `/dossier-audit` | Indexed folder + scope focus | Inline edits + audit-trail note | `validators/audit_trail.py` |
| utility | `/url-freshness-check` | Any markdown folder | URL check report | `validators/url_check_report.py` |
| utility | `/freshness-audit` | v2 project dir | refreshed ledgers + `dashboard.md` | `validators/freshness.py` |
| utility | `/synthesis-export` | v2 project dir | in-dossier `synthesis_export.jsonl` | `validators/research_kb_export.py` |

## When each skill applies

- **`/research-plan`**: starting a new research effort on a topic you don't yet have a dossier for. Run once per topic; output is referenced throughout the rest of the pipeline.
- **`/research-gather`**: after the plan; for each sub-area in the plan, discovers primary sources via WebSearch / WebFetch and adds them to `bib_ledger.yml`. May be re-run when adding sources later.
- **`/dossier-build`**: once `bib_ledger.yml` is reasonably stable. Renders entries into editable Markdown table files organized by claim_family.
- **`/agent-index`**: after the dossier is content-complete. Synthesizes the dossier into a dual-audience indexed folder optimized for downstream agent + human consumption. Run once; re-run only after material dossier edits.
- **`/dossier-audit`**: after `/agent-index` produces the synthesis. Each invocation is one round of complementary-scope verification. Stop iterating when a round returns "clean."
- **`/url-freshness-check`**: any time. Useful before publishing the synthesis externally or after long gaps where blog posts may have drifted to 404.
- **`/freshness-audit`**: v2 strict-live trust pass. Refreshes stale entries, checks evidence/cache IDs, validates cache hashes, and updates the trust dashboard. Phase 5 of this skill invokes `scripts/build_dashboard.py` to mechanically generate `dashboard.md`.
- **`/synthesis-export`**: after strict freshness passes. Emits the in-dossier `synthesis_export.jsonl` envelope for synthesis-kb.

## Mechanized v2 artifacts

Two helper scripts produce v2 artifacts deterministically rather than relying on LLM hand-construction:

- `scripts/build_claim_graph.py` — invoked from `/research-gather` Phase 4 after `evidence_ledger.yml` + `cache_manifest.yml` are written. Reads all ledgers, emits a complete `claim_graph.jsonl` with entity / source / claim / evidence / cache_blob records. Claim text comes from the highest-quality supporting evidence's `excerpt` field.
- `scripts/build_dashboard.py` — invoked from `/freshness-audit` Phase 5. Reads all v2 artifacts, emits `dashboard.md` with 5 Trust State metrics + per-tier Action Queue.

Both validate output before writing. `--no-overwrite` refuses if the target exists (safety for hand-curated fixtures).

## Pipeline correctness

The handoff contract is enforced by validators: skill N's output validator IS skill N+1's input validator. If the schema drifts, downstream skills fail at the validator step before they can emit broken output. Each skill body ends with a mandatory `## Validation` step that calls the validator and aborts on non-zero exit.

This is the strongest correctness discipline available for prompt-defined skills — schema invariants are deterministically checked even though the skills themselves are LLM-driven.

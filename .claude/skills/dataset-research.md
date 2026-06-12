---
name: dataset-research
description: One-shot wrapper that runs /dataset-gather then /dataset-index in sequence. Convenience for "give me a dataset dossier on this topic" without invoking the two stages separately. The mini-pipeline (gather + index as separate skills) is still available for users who want intermediate review.
allowed-tools: Read, Write, Edit, Bash, WebSearch, WebFetch
---

# /dataset-research — One-shot dataset dossier generator

## Usage

```
/dataset-research "<topic>" [--output-dir <consumer-project-docs-dir>]
```

**Examples:**
```
/dataset-research "time-series anomaly detection"
/dataset-research "tabular ML benchmarks" --output-dir ~/my_project/docs/research/tabular_datasets/
```

## When to use

- When you want one command to produce a dataset dossier on a topic.
- When you don't need intermediate review between discovery and rendering.

For granular control (review the ledger before rendering), use
`/dataset-gather` and `/dataset-index` separately.

## Workflow

This is a thin orchestrator. It invokes:

1. **`/dataset-gather "<topic>"`** — produces
   `~/Claude/research-dossiers/research_<slug>/dataset_ledger.yml`. See `dataset-gather.md`
   for full discovery semantics + the HARD REQUIREMENTS (read
   `references/dataset_sources.md`, strict `unverified` default, count
   assertion in final report, anti-cheat heuristic at ≥30 entries).

2. **`/dataset-index <ledger_path> --output-dir <consumer-project>/docs/research/<slug>_datasets/`** —
   renders the ledger as 5-bullet-entry AGENT-INDEX folder. See
   `dataset-index.md` for full rendering semantics + HARD RULES (display
   `name` verbatim, no fabricated metadata, run `cross_stage` after own
   validator).

After both stages succeed, the wrapper:
- Reports the total datasets gathered + per-source-category breakdown.
- Reports validator status of both ledger + agent_index.
- Suggests next steps:
  - Run `/dossier-audit <output_dir> --focus "license risks + access stability"` for a Round 1 audit.
  - Run `/url-freshness-check <output_dir>` to confirm URL liveness.

## Failure handling

If `/dataset-gather` fails (validator non-zero, count-assertion mismatch,
anti-cheat warning that needs explicit `--strict` consideration), the
wrapper STOPS and surfaces the failure. Do not auto-promote past gather.

If `/dataset-index` fails after gather succeeded, the wrapper reports the
gather output is intact and the user can fix-and-rerun `/dataset-index`
without re-discovering.

## Output / handoff

**Produces:**
- `~/Claude/research-dossiers/research_<slug>/dataset_ledger.yml` (gather output)
- `<consumer-project>/docs/research/<slug>_datasets/` (index output: README + 00_overview + 0K_<source>.md)

**Consumed by:**
- `/dossier-audit` (use focus="license risks + access stability")
- `/url-freshness-check`

## Why a wrapper exists

The 2-skill pipeline (`/dataset-gather` + `/dataset-index`) maps to 2 distinct
artifacts (ledger, agent-index) with separate validators between. The wrapper
exists because for the common case ("give me a dataset dossier on X") the
intermediate review point isn't load-bearing — most users want the final
artifact and audit it once at the end via `/dossier-audit`.

If your workflow benefits from reviewing the ledger before rendering, use
the 2 skills separately.

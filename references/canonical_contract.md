# Canonical dossier contract

The clean-break v1 layout is:

```text
dossier.yaml
sources.jsonl
evidence.jsonl
claims.jsonl
reviews.jsonl
watch.jsonl
runs/<run-id>/manifest.json
runs/<run-id>/search-decisions.jsonl
runs/<run-id>/refresh-events.jsonl
derived/claim-graph.jsonl
derived/agent-index.md
derived/citation-report.json
derived/consumer-bindings.jsonl
derived/synthesis-export.jsonl
release.json
```

Schemas live under `${CLAUDE_PLUGIN_ROOT}/schemas/v1/`. Stable identifiers are
never reused. Removal uses `status`, `supersedes`, and `superseded_by`; consumers
must process tombstones instead of retaining deleted claims.

The relationship is many sources → many evidence records → many claims → many
consumer bindings. A byte anchor proves that text exists in a snapshot; it does
not prove entailment. Only a dated `ClaimReviewRecord` can approve entailment,
currency, methodology, and risk of bias.

Generated files under `derived/` have one deterministic producer and must not
be edited by hand. Correct canonical records or adjudicated reviews, then
rebuild. A release is valid only when `research-toolkit release check` verifies
all declared artifact hashes.

Use the one-time importer for legacy v2/v3 dossiers:

```bash
python -m research_toolkit.legacy_import <legacy-dir> <new-dir>
```

The importer is idempotent and intentionally marks claims `unresolved`; it does
not convert structural provenance into a semantic approval.

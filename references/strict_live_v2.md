# Strict-Live v2 Protocol

research_toolkit v2 is a trust-first research OS. It treats current evidence,
local cache, and durable IDs as first-class artifacts.

## Default Posture

- **Primary-first:** secondary sources may discover leads, but final claims cite
  primary or official sources.
- **Strict freshness:** stale or unevidenced required claims fail strict
  validation.
- **Max local cache:** cache every reachable source artifact for personal
  research and future `research-kb` ingestion.
- **Human + agent output:** Markdown stays readable, while ledgers and JSONL
  records carry machine-checkable evidence.

## Required Artifacts

Every v2 project should contain:

- `bib_ledger.yml` and/or `dataset_ledger.yml`
- `evidence_ledger.yml`
- `cache_manifest.yml`
- `claim_graph.jsonl`
- `dashboard.md`
- `research_kb_export.jsonl` when ready to ingest

All YAML ledgers use:

```yaml
schema_version: 2
topic: <topic>
generated_at: <YYYY-MM-DD>
current_as_of: <YYYY-MM-DD>
freshness_policy: strict_live
```

## Freshness Tiers

Default maximum stale windows:

| Tier | Days | Use for |
|---|---:|---|
| `volatile` | 30 | vendor pages, repos, leaderboards, mutable model/dataset cards, shipping status |
| `active` | 90 | recent papers, active benchmarks, drafts, fast-changing methods |
| `stable` | 365 | published papers, stable datasets, finalized standards |
| `historical` | 1825 | classics whose bibliographic facts rarely change |

Do not increase `stale_after_days` above the tier default. Use a less volatile
tier only when the source truly deserves it.

## Evidence Model

Every substantive claim should map to one or more evidence IDs. Use typed claim
records for:

- fact
- comparison
- trend
- risk
- recommendation
- contradiction
- open question
- user judgment

Preserve conflicts. If two primary sources disagree, keep both claims/evidence
records with dates and confidence factors instead of flattening the conflict.

## Cache Policy

Default cache root: `~/Claude/research_cache/`.

Store:

- raw blob
- extracted text/Markdown derivative
- metadata JSON
- SHA-256 hash
- byte count
- source URL
- rights/restriction flags

The cache is private by default: gitignored, local, and not intended for
publication as a source archive. Export manifests and hashes, not raw cached
content.

For GitHub/code sources, cache an archive snapshot at a resolved commit/tag
where possible, plus README/license/release metadata.

For restricted/authenticated sources, cache when your access and terms allow it.
Mark `restricted: true` and record access/rights notes in metadata.

## Research-KB Export

`research_toolkit` exports append-only JSONL records. `research-kb` owns the
durable graph and ingestion/indexing.

**Lossless wrap contract.** Each line in `research_kb_export.jsonl` wraps a
complete `claim_graph.jsonl` record in this envelope:

```json
{
  "export_schema_version": 2,
  "record_type": "<entity|source|claim|evidence|cache_blob>",
  "id": "export_<original_record_id>",
  "source_project": "<project name>",
  "exported_at": "<YYYY-MM-DD>",
  "payload": { ... full claim_graph record verbatim ... }
}
```

The `payload` field preserves every claim_graph attribute — `record_type`,
`id`, `topic`, plus per-record-type fields (claim `confidence`/`status`/
`entity_ids`, source `cache_ids`, entity `aliases`, etc.). Ingestion code
on the research-kb side parses `payload.*` directly; nothing is dropped on
the export side so future ingestion always has full information.

See `templates/research_kb_export.template.jsonl` for the per-record-type
payload schemas and `scripts/research_kb_export.py` for the implementation
(it does verbatim copy: `"payload": record`).

**Ingestion is out of scope for `research_toolkit`.** Building the
parse-inbox / DB-schema / index pipeline lives in the `research-kb` repo.
The toolkit's responsibility ends at producing a validated export jsonl in
`~/Claude/research-kb/inbox/research_toolkit/<slug>.jsonl`.

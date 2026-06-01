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

**Examples for calibration** (agents default to the middle category when uncertain — concrete examples shift the distribution toward correct):

- **`volatile` (30 days)**: release candidates and beta features, GitHub repo READMEs that ship per-release, leaderboard pages, model cards on Hugging Face that update with each checkpoint, security-advisory feeds, the MCP RC pages during the May–July 2026 RC window.
- **`active` (90 days)**: vendor blog posts on shipping features, docs pages that ship per release (e.g., `code.claude.com/docs/en/agent-sdk/overview`), SDK release notes, dated case studies, Anthropic engineering posts on a still-evolving system.
- **`stable` (365 days)**: spec sections of ratified protocol versions (e.g., MCP `2025-11-25` spec sections), core architecture posts (e.g., agent-loop semantics, hub-and-spoke patterns), established mechanisms documented years ago, published peer-reviewed papers.
- **`historical` (1825 days)**: foundational papers (Brier 1950, Vaswani 2017, Sutton & Barto), classical algorithms, mathematical proofs, completed RFCs that have not been amended.

If you find yourself defaulting many entries to `active`, recalibrate: `active` is for things that ship updates regularly. Anything documented once and rarely touched is `stable`; anything mid-flight is `volatile`.

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

### v2.3+ extraction cascade (#11)

For `application/pdf` sources, `scripts/cache_source.py` runs a two-stage
cascade:

1. **pdfplumber** (Stage 1, always tried first) — pure-Python, fast text
   extraction.
2. **Docling** (Stage 2, lazy-imported when math is detected) — preserves
   equations as LaTeX. ~600 MB models downloaded on first use.

`extraction_status` enum (v2.3 extends v2.0's {ok, partial, raw_only, failed}):

| Status | Meaning | Downstream behavior |
|---|---|---|
| `ok` | pdfplumber clean text | Phase 2a span-anchoring fully supported |
| `rich` | Docling extracted equations | Phase 2a fully supported, equations in LaTeX |
| `ok_text_only` | math detected, Docling failed | Phase 2a runs but math spans may be lossy |
| `degraded` | image-PDF / near-empty | **Phase 2a SKIPS** this entry |
| `partial` | encrypted PDF | **Phase 2a SKIPS** this entry |
| `failed` | both extractors errored | **Phase 2a SKIPS** this entry |
| `raw_only` | non-PDF binary OR `--no-extract-pdfs` | **Phase 2a SKIPS** this entry |
| `stub` (#10) | JS-shell HTML detected without Playwright | **Phase 2a SKIPS** this entry |

Authors should treat `degraded`/`partial`/`failed`/`stub` entries as
sources that need re-fetching (find a non-paywalled / non-encrypted /
non-image alternative), not as silently lossy supports. `cache_source.py`
emits a stderr WARN for any non-ideal status; the optional PDF-caching
step of `/research-gather` reads `<cache_root>/extraction_log_<hostname>.jsonl`
and prints an aggregated end-of-run summary.

### Path portability (v2.3 / #13)

`raw_path` / `text_path` / `metadata_path` MUST be relative to
`cache_root`. Absolute / ~-prefixed paths are rejected by the validator.
Migrate legacy manifests via `scripts/migrate_manifest_paths.py`.

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

## v2.2 additive extensions (within `schema_version: 3`)

v2.2 layers three additive artifacts onto the v2.1 anti-hallucination
regime. The schema version stays at 3 — new fields are required when
present but pre-v2.2 projects (no manifest files) remain valid.

### `gather_trace.yml` (Item 5: Self-RAG adaptive retrieval)

Written by `/research-gather` Phase 2. Every WebSearch+WebFetch emits a
structured reflection record with `is_relevant` / `is_supported` /
`is_useful` and a `decision` (`accept` / `reject` / `escalate_to_manual`).
Backed by Self-RAG (Asai 2023 ICLR) + FAIR-RAG (Asl 2025 — confirming
2023-2025 convergence on adaptive iterative refinement).

The trace makes the discovery step auditable after the fact: every
search that *didn't* yield a source stays in the trace as evidence the
search was performed deliberately. `/freshness-audit` Phase 4 reads it
for discovery-rigor metrics; `build_dashboard.py` surfaces fetches-
reviewed / accept-rate / escalations as a "Discovery Rigor" section.

Schema template: `templates/gather_trace.template.yml`.
Validator: `validators/gather_trace.py`.

### `pre_selection_manifest.yml` (Item 3: Attribute-First refactor)

Written by `/agent-index` Phase 2b. Commits to evidence spans BEFORE any
bullet prose is generated. Validator rejects any evidence_id whose
anchor isn't in the manifest — post-hoc rationalization becomes
mechanically impossible.

Phase 2 sub-phases:
- **2a — span-select**: open `cache_manifest` text_paths and pick spans
  per atomic claim. Record byte offsets + sha256 + excerpt.
- **2b — plan**: emit `pre_selection_manifest.yml` with one selection
  per (bullet, atom) pair.
- **2c — generate**: write bullets conditioned ONLY on selected spans.

Backed by Attribute-First (Slobodkin 2024 ACL) + C²-Cite (Yu 2026
WSDM) + Gen-vs-Posthoc (Saxena 2025; G-Cite > P-Cite empirical
justification).

Schema template: `templates/pre_selection_manifest.template.yml`.
Validator: `validators/pre_selection_manifest.py` (reuses v3
`verify_excerpt_anchor` for substring + sha256 + bytes-equality).

### Atomic claim IDs (Item 1: atomic decomposition)

`/agent-index` Phase 2 emits 2–5 atomic claim_ids per 5-bullet block
(naming: `claim_<topic>_b<N>_a<M>_<descriptor>`) instead of one
bullet-level claim_id. Each atom binds to ONE pre-selected span.
`build_claim_graph.py` needs no schema change — the existing
many-to-many evidence→claim mapping already supports atom granularity.

Backed by FActScore (Min 2023 EMNLP) + RAGTruth (Niu 2024) + VISTA
(Lewis 2025) + AtomEval (Cen 2026) + VeriFact (Liu 2025).

v2.2 ships **free-text atoms** (string per atom). SROM 4-tuple
(subject-relation-object-modifier) atomic structure deferred to v2.3
once free-text usage surfaces friction.

**Migration vs fresh generation (v2.3 clarification).** Retroactive
migration from v2.1 (one atom per bullet) does NOT trigger multi-atom
decomposition — the existing excerpt only anchors a single atomic
claim_id, since both retroactive ID assignment and gather-time excerpt
capture naturally produce one claim per evidence. True 2-5 atoms per
bullet emerges only when `/agent-index` Phase 2c generates fresh prose
conditioned on a `pre_selection_manifest` with multi-atom selections.
This pattern held across all 4 v2.2 dogfood phases (every project
stayed at 1 atom per source even after migration); it's expected
behavior, not a defect of the migration path.

### Dashboard additions (v3 evidence ledgers)

`build_dashboard.py` surfaces two new Claim Health rows when
`schema_version: 3`:

- **corroborated (≥2 independent sources)**: % of claims supported by
  evidence from ≥2 distinct `source_url`s. Implements Item 2's scoring
  half (aggregation half was already in v2.1's builder).
- **atoms fully supported**: % of claims where all supporting evidence
  has `evidence_role_strength: full`.

Both gate on v3 schema; v2 fixtures emit only the v2.1 rows.

### Cross-cutting note

v2.2 settles into "use" posture after shipping. v2.3 candidates from
the saturated backlog include SROM atom upgrade, multi-agent debate
harness, and semantic-entropy citation audit — not planned until
specific friction surfaces.

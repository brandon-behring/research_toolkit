---
name: synthesis-export
description: Use when the user has a complete strict-live project with passing /freshness-audit and asks to export it for synthesis-kb ingestion. Wraps each claim_graph record verbatim in an envelope (export_schema_version 2), writes IN-DOSSIER to <project_dir>/synthesis_export.jsonl. Lossless — preserves every payload field. Should not run while /citation-audit reports substring failures (v3 projects). Renamed from /research-kb-export at RS1 (2026-06-12); there is no inbox.
allowed-tools: Read, Write, Bash
---

# /synthesis-export — emit the in-dossier synthesis-kb envelope

## Usage

```
/synthesis-export <project_dir> [--output <path>]
```

**Default output:** `<project_dir>/synthesis_export.jsonl` (in-dossier — the R1a contract;
the old `~/Claude/research-kb/inbox/` is deleted).

## When to use

- After `/freshness-audit <project_dir> --strict` passes.
- When the project's claim graph should become durable long-term memory in `synthesis-kb`.

## Workflow

### Phase 1: validate strict-live project

Run:

```bash
python ~/Claude/research_toolkit/validators/freshness.py --strict <project_dir>
python ~/Claude/research_toolkit/validators/claim_graph.py <project_dir>/claim_graph.jsonl
```

### Phase 2: export JSONL

Use the bundled exporter:

```bash
python ~/Claude/research_toolkit/scripts/synthesis_export.py <project_dir>
```

The exporter wraps claim-graph records as append-only ingestion records with:
- `export_schema_version: 2`
- `record_type`
- `id`
- `source_project`
- `exported_at`
- `payload`

### Phase 3: validate export

Run:

```bash
python ~/Claude/research_toolkit/validators/research_kb_export.py <project_dir>/synthesis_export.jsonl
```

(The validator module keeps its historical name — the envelope schema is unchanged.)
Do not report success until the export validates.

## Contract

- `research_toolkit` owns collection, cache, evidence, and synthesis quality.
- `synthesis-kb` owns the durable claim/concept layer and downstream graph indexing.
- The envelope lives ONLY in its dossier folder (R1a, decisions register 2026-06-11) — no
  staging directory, no copy steps.
- Export records must preserve strong IDs for entities, sources, claims, evidence, and cache blobs.
- Full cache blobs stay local/private; export records point to paths and hashes rather than
  embedding raw copyrighted content.

## Consumer

`synthesis-kb/scripts/ingest_dossiers.py` reads `<dossier_dir>/synthesis_export.jsonl` for every
slug in its `DOMAIN_SLUGS` (default root `~/Claude/research-dossiers/<slug>/`, with external
producers like prompt-injection-portfolio mapped via `SLUG_DIRS`). Live since 2026-05-29
(four promoted domains: agents, ml_security, llm_alignment_scaling, ml_methodology); the old
"no consumer exists" status note (2026-05-21) is obsolete. Downstream: claims → Sonnet concept
extraction → SKOS concept scheme + computed bridges (see synthesis-kb CLAUDE.md).

## Output / handoff

**Produces:** `<project_dir>/synthesis_export.jsonl` unless `--output` overrides it.

**Consumed by:** `synthesis-kb/scripts/ingest_dossiers.py` (see Consumer above). For a new
dossier, ingestion also requires adding its slug to the relevant `DOMAIN_SLUGS` list (a
deliberate curation step, not automation).

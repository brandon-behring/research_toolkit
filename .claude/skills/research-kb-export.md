---
name: research-kb-export
description: Use when the user has a complete v2 strict-live project with passing /freshness-audit and asks to export it for ~/Claude/research-kb ingestion. Wraps each claim_graph record verbatim in an envelope (export_schema_version 2), writes to ~/Claude/research-kb/inbox/research_toolkit/. Lossless — preserves every payload field. Should not run while /citation-audit reports substring failures (v3 projects).
allowed-tools: Read, Write, Bash
---

# /research-kb-export — emit research-kb ingestion JSONL

## Usage

```
/research-kb-export <project_dir> [--output <path>]
```

**Default output:** `~/Claude/research-kb/inbox/research_toolkit/<project_slug>.jsonl`

## When to use

- After `/freshness-audit <project_dir> --strict` passes.
- When the project’s claim graph should become durable long-term memory in `research-kb`.

## Workflow

### Phase 1: validate strict-live project

Run:

```bash
python ~/Claude/research_toolkit/validators/freshness.py --strict <project_dir>
python ~/Claude/research_toolkit/validators/claim_graph.py <project_dir>/claim_graph.jsonl
python ~/Claude/research_toolkit/validators/research_kb_export.py <project_dir>/research_kb_export.jsonl
```

If a project-local `research_kb_export.jsonl` does not exist yet, skip the third command and generate it in Phase 2.

### Phase 2: export JSONL

Use the bundled exporter:

```bash
python ~/Claude/research_toolkit/scripts/research_kb_export.py <project_dir>
```

The exporter wraps claim-graph records as append-only research-kb ingestion records with:
- `export_schema_version: 2`
- `record_type`
- `id`
- `source_project`
- `exported_at`
- `payload`

### Phase 3: validate export

Run:

```bash
python ~/Claude/research_toolkit/validators/research_kb_export.py <output_path>
```

Do not report success until the export validates.

## Contract

- `research_toolkit` owns collection, cache, evidence, and synthesis quality.
- `research-kb` owns durable memory and downstream graph indexing.
- Export records must preserve strong IDs for entities, sources, claims, evidence, and cache blobs.
- Full cache blobs stay local/private; export records point to paths and hashes rather than embedding raw copyrighted content.

## Status

**As of 2026-05-21**, the kb-side consumer does **not yet exist**. Verification: `grep -rln 'research_toolkit\|inbox/research_toolkit\|export_schema_version' ~/Claude/research-kb/` returns zero matches. research-kb runs its own corpus pipeline (Semantic Scholar weekly cron → GROBID/Docling/MinerU PDF extraction → BGE-large embeddings into PostgreSQL+pgvector+KuzuDB) and does not poll the toolkit's inbox.

Exports produced by this skill are **currently archival** — they sit in `~/Claude/research-kb/inbox/research_toolkit/` and are not auto-ingested. They remain valid (envelope-wrapped, schema-stable) and will be ingestible once a consumer is built.

**Root cause of the gap**: ontology mismatch. The toolkit's records (entity / claim / atom / evidence / span) don't map 1:1 to the kb's records (source / chunk / citation / concept / method / assumption). Bridging requires either a kb-side adapter or a separate toolkit-dossier corpus inside the kb. Tracked at [research_toolkit#5](https://github.com/brandon-behring/research_toolkit/issues/5); see `references/v2_2_skill_audit.md` § "research-kb-export" and § "Integration sketch" (2026-05-21).

**When to still run this skill anyway**:
- The export is a clean, append-only durable snapshot of the dossier's claim graph — useful as a long-term archive even without active ingestion.
- Future kb-consumer builds will retroactively ingest whatever sits in inbox/.
- Other tooling (e.g., a fresh Claude session) can read the JSONL directly.

## Output / handoff

**Produces:** a JSONL file in `~/Claude/research-kb/inbox/research_toolkit/` unless `--output` overrides it.

**Consumed by:** No consumer currently exists in `research-kb` (see `## Status` above). Output is archival pending consumer implementation.

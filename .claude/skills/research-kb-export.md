---
name: research-kb-export
description: Export a strict-live v2 research_toolkit project into normalized JSONL records for ~/Claude/research-kb ingestion. Requires freshness/evidence/cache validation before emitting records.
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

## Output / handoff

**Produces:** a JSONL file in `~/Claude/research-kb/inbox/research_toolkit/` unless `--output` overrides it.

**Consumed by:** `research-kb` ingestion workflows.

# 0001 — Producer contract: dossiers repo, in-dossier envelope, /synthesis-export

- **Status**: Accepted
- **Date**: 2026-06-11
- **Deciders**: Brandon (research-side design review 2026-06-10/11)
- **Canonical register**: `~/Claude/lever_of_archimedes/docs/plans/active/2026-06-research-side-design-review/decisions.yaml` (rows R1a, R2, R4, R12)

## Context

research_toolkit's dossier outputs (67 folders) sat at `~/Claude` root with no VCS — yet they are the
CANONICAL files (both KBs are derived). The `/research-kb-export` skill wrote envelopes to
`research-kb/inbox/`, which research-kb never consumes (the 2026-05-21 design's M0 was never built);
synthesis-kb reads the envelopes — from the wrong repo's tree.

## Decision

1. **Output home**: new dossier projects are created inside the **private `~/Claude/research-dossiers/`
   git repo** (slice RS1 creates it and moves existing dossiers verbatim, with transition symlinks at
   `~/Claude` root for one cycle — review row R12).
2. **Export skill**: `/research-kb-export` → **`/synthesis-export`**, writing the envelope **only into the
   dossier folder** (no inbox copy). `research-kb/inbox/` is deleted. The envelope schema is unchanged;
   synthesis-kb's `ingest_dossiers.py` reads in-dossier.
3. **Index files**: `research_INDEX.md`, `research_BACKLOG.md`, `research_TOPIC_BACKLOG.md`,
   `research_graph.json` move into the dossiers repo.
4. **Wanted-primaries** (R2): the toolkit does NOT bulk-export caches to research-kb (M0 dropped).
   Acquisition is demand-driven from synthesis-kb's unresolved reports; non-arXiv islands (research-kb #23)
   are per-domain ingestion decisions.
5. `research_cache` (shared content-addressed store) stays at `~/Claude/research_cache`, outside git,
   with an off-disk backup (review row R11).

## Consequences

- One path change in toolkit config (project base path) + the skill rename; slugs stay verbatim so
  envelopes/INDEX/DB references don't churn.
- Dossiers gain history, diffs, and Mac access via `git clone`.
- The misleading research-kb inbox address disappears; the producer→organizer contract reads true.

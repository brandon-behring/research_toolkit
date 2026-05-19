---
name: freshness-audit
description: Strict-live v2 refresh and trust-state audit for a research_toolkit project. Validates stale blockers, evidence IDs, cache hashes, URL liveness, and missing source snapshots; refreshes or downgrades entries before downstream synthesis/export.
allowed-tools: Read, Write, Edit, Bash, WebSearch, WebFetch
---

# /freshness-audit — strict-live v2 trust audit

## Usage

```
/freshness-audit <project_dir> [--strict] [--today YYYY-MM-DD]
```

## When to use

- Before treating a v2 project as current.
- Before `/research-kb-export`.
- Any time `validators/freshness.py --strict` fails, or a dashboard shows stale blockers.

**Not the same as `/url-freshness-check`.** This skill is the v2 strict-live trust audit: it reads `evidence_ledger.yml`, `cache_manifest.yml`, `claim_graph.jsonl`, validates referential integrity, re-fetches stale primary sources, and updates the dashboard. `/url-freshness-check` is a generic HTTP-HEAD utility on any markdown folder (2xx/3xx/4xx categorization, no v2 awareness). For a v2 project both can be useful: run `/url-freshness-check` on the rendered agent-index markdown to catch dead URLs, and run this skill on the project root to refresh stale evidence and rebuild trust state.

## Workflow

### Phase 1: load strict-live artifacts

Read:
- `<project_dir>/bib_ledger.yml` and/or `<project_dir>/dataset_ledger.yml`
- `<project_dir>/evidence_ledger.yml`
- `<project_dir>/cache_manifest.yml`
- `<project_dir>/claim_graph.jsonl`
- `<project_dir>/dashboard.md` if present

Read `~/Claude/research_toolkit/references/strict_live_v2.md` before editing.

### Phase 2: validate current trust state

Run:

```bash
python ~/Claude/research_toolkit/validators/freshness.py --strict <project_dir>
python ~/Claude/research_toolkit/validators/evidence_ledger.py <project_dir>/evidence_ledger.yml
python ~/Claude/research_toolkit/validators/cache_manifest.py <project_dir>/cache_manifest.yml
python ~/Claude/research_toolkit/validators/claim_graph.py <project_dir>/claim_graph.jsonl
```

Treat every strict failure as a blocker. Stale entries are not “mostly fine” in v2.

### Phase 3: refresh stale or weak sources

For each stale / missing / weak entry:
- Re-fetch the primary or official source with WebFetch or API access.
- Cache everything reachable locally using the strict-live cache policy.
- Prefer `scripts/cache_source.py` for simple public URLs:

```bash
python ~/Claude/research_toolkit/scripts/cache_source.py <url> --topic <topic>
```

- Update `cache_manifest.yml` with the new blob paths, hashes, extracted text paths, and metadata paths.
- Update `evidence_ledger.yml` with field-level evidence.
- Update ledger entry `retrieved_at`, `verified_at`, `verified_fields`, `evidence_ids`, and `cache_ids`.
- Preserve conflicting evidence as separate claim/evidence records instead of deleting it.

### Phase 4: rerun discovery for volatile areas

For AI/ML topics, strict-live refresh includes a current scan of:
- arXiv / OpenReview / Semantic Scholar
- Hugging Face models/datasets/papers
- GitHub repos/releases
- benchmark/leaderboard pages
- vendor blogs and official product/security pages
- NIST / ISO / EU / US policy and standards sources when relevant

Use current-date-aware search windows, not fixed years. Secondary sources are discovery aids only; final claims cite primary or official sources.

### Phase 5: write trust dashboard

Generate the dashboard mechanically:

```bash
python ~/Claude/research_toolkit/scripts/build_dashboard.py <project_dir> --today <YYYY-MM-DD>
```

The builder reads all v2 artifacts and emits `dashboard.md` with Trust State
metrics (stale blockers, evidence coverage, cache completeness, conflicts,
weak claims) and an Action Queue with one line per freshness tier needing
refresh.

You may edit the dashboard afterward to add narrative observations (e.g.,
specific next-actions, friction notes), but the mechanical metrics will be
overwritten on the next builder run (default is overwrite). Pass
`--no-overwrite` to preserve hand-edits at the cost of stale metrics.

### Phase 6: final validation

Run all relevant validators again:

```bash
python ~/Claude/research_toolkit/validators/freshness.py --strict <project_dir>
python ~/Claude/research_toolkit/validators/claim_graph.py <project_dir>/claim_graph.jsonl
```

Do not report success until strict validation passes.

## Output / handoff

**Produces:** refreshed v2 ledgers, cache manifest, evidence ledger, claim graph, and trust dashboard.

**Consumed by:** `/research-kb-export <project_dir>` and future research sessions.

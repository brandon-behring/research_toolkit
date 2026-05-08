# prompt-injection snapshot fixture

**What this is**: a real 137-entry research synthesis on **direct + indirect prompt injection, jailbreaks, defenses, training-time threats, datasets, vendors, and standards** — checked into the toolkit's tests as the canonical real-world integration-test fixture. The citations are public (arXiv preprints, conference papers, vendor blogs, standards documents); the synthesis itself is the toolkit author's own work, originally produced separately and frozen here as a stress-shaped reference example for the validators and skills. Used to prove the toolkit handles heterogeneous real-world content (paper tables + leaderboard lists + vendor profiles + standards profiles), not just the small `mini_topic_timeseries_anomaly/` smoke fixture.

Frozen copy (taken 2026-05-06) of the prompt-injection prompt-injection research dossier and the agent-index synthesis built from it. Used as the "old use case" regression for the research_toolkit validators and skills.

## Layout

```
prompt_injection_snapshot/
├── real/                         # frozen at toolkit-creation time
│   ├── bib_ledger.yml            # 137 entries, 5 fields each
│   ├── cache/                    # bib_primary_source_cache.yml — PDF metadata
│   ├── dossier/                  # 7 topic table files + _dossier_readme.md
│   └── agent_index/              # 9 indexed files (00..07 + README.md)
└── recreated/                    # populated in Phase 3.5 by the new skills
    └── ...                       # mirrors real/ when the skills can rebuild the same content
```

`real/` was copied from:
- `~/interview_prep_series/docs/research/prompt_injection_research/` (dossier, bib_ledger, cache)
- `~/prompt-injection-detector/docs/prompt_injection_research/` (agent_index synthesis)

The `papers/` directory (35 cached PDFs, ~115 MB) was deliberately excluded — fixtures are for schema validation, not for re-running the cited papers.

## Schema notes (v1.1+ status)

- **`bib_ledger.yml`**: validates cleanly under v1.1+. (Historical note: under
  v1.0, `entries[63]` had an empty `primary_url`; the v1.1 cleanup populated it
  with the canonical Nature MI URL. The corresponding test was renamed
  `test_prompt_injection_bib_ledger_passes_cleanly`.)
- **`dossier/_dossier_readme.md`**: not a topic file; renamed from `README.md`
  to avoid name collision with the agent_index `README.md`. Validators skip it
  (no `| Title |` table → accepted).
- **No `research_plan.md`**: prompt-injection predates the `/research-plan` stage 0 skill.
  Stage-0 validation is therefore not exercised by this fixture.

All five validators (research_plan, bib_ledger, dossier, agent_index,
audit_trail) plus v1.2's `cross_stage` validator **pass cleanly** on the
snapshot in default mode. Under `cross_stage --strict`, prompt-injection/real fails on
soft warnings: ~202 cross-reference arxiv IDs in agent_index `**Source:**`
lines aren't in prompt-injection's own bib_ledger (foundational pre-LLM papers cited as
context — a deliberate prompt-injection design choice, not a defect).

The heterogeneous content types in prompt-injection (paper tables, leaderboard lists,
vendor profiles, standards profiles) are accommodated by the validators'
content-type detection (paper-table vs non-paper-table; presence of Result
bullet to distinguish paper-synthesis entries from vendor profiles).

## Schema-equivalence rubric (`real/` vs `recreated/`)

`test_recreation_diff.py` (populated in Phase 1d) compares `real/` to
`recreated/` after `/agent-index` (and optionally `/research-gather` +
`/dossier-build`) have been run on the prompt-injection domain. The comparison
is **schema-equivalence**, not byte-identity:

- Same number of files in each artifact-type directory (±0).
- Each `agent_index/<file>.md` has the same number of `**Source:**` entries
  within ±20% of the real version.
- README has AGENT-INDEX comment, scope-boundary callout, lookup recipes section,
  and glossary in both.
- Same set of top-level section anchors (`## A1.`, `## B2.`, etc.) when the
  recreation produces a paper-synthesis schema.

Discrepancies above the tolerance (missing entries, mis-attributed authors,
reordered sections) are surfaced in the diff report but do not fail the gate —
they get logged in `BURN_IN_NOTES.md` for review during Phase 5 dogfood.

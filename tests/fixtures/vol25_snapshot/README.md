# vol25 snapshot fixture

Frozen copy (taken 2026-05-06) of the vol25 prompt-injection research dossier and the agent-index synthesis built from it. Used as the "old use case" regression for the research_toolkit validators and skills.

## Layout

```
vol25_snapshot/
├── real/                         # frozen at toolkit-creation time
│   ├── bib_ledger.yml            # 137 entries, 5 fields each
│   ├── cache/                    # bib_primary_source_cache.yml — PDF metadata
│   ├── dossier/                  # 7 topic table files + _dossier_readme.md
│   └── agent_index/              # 9 indexed files (00..07 + README.md)
└── recreated/                    # populated in Phase 3.5 by the new skills
    └── ...                       # mirrors real/ when the skills can rebuild the same content
```

`real/` was copied from:
- `~/interview_prep_series/docs/research/vol25_prompt_injection/` (dossier, bib_ledger, cache)
- `~/prompt-injection-detector/docs/vol25_research/` (agent_index synthesis)

The `papers/` directory (35 cached PDFs, ~115 MB) was deliberately excluded — fixtures are for schema validation, not for re-running the cited papers.

## Known violations vs the validators

The vol25 corpus predates several research_toolkit conventions, so some entries
deliberately violate the toolkit's canonical schema. These are *expected* — they
demonstrate that real-world research artifacts have legitimate sub-schemas.

- **`bib_ledger.yml`**: `entries[63]` (`kim2024selfreminder`) has an empty
  `primary_url`. Source data was incomplete at vol25 creation time. Validator
  correctly flags this. Test asserts exactly 1 error, in this entry.
- **`dossier/_dossier_readme.md`**: not a topic file; renamed from `README.md`
  to avoid name collision with the agent_index `README.md`. Validators skip it
  (no `| Title |` table → accepted).
- **No `research_plan.md`**: vol25 predates the `/research-plan` stage 0 skill.
  Stage-0 validation is therefore not exercised by this fixture.

The dossier and agent_index validators **pass cleanly** on the snapshot — the
heterogeneous content types in vol25 (paper tables, leaderboard lists, vendor
profiles, standards profiles) are accommodated by the validators' content-type
detection (paper-table vs non-paper-table; presence of Result bullet to
distinguish paper-synthesis entries from vendor profiles).

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

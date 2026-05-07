---
name: dossier-build
description: Render a populated bib_ledger.yml into N topic-organized Markdown table files (the dossier). Groups entries by claim_family, picks topic file boundaries, renders 7-column tables, updates entry status to verified. Output consumed by /agent-index.
allowed-tools: Read, Write, Edit, Bash
---

# /dossier-build — Render bib entries as topic dossier files

## Usage

```
/dossier-build <bib_ledger_path> [--output-dir <dir>]
```

**Examples:**
```
/dossier-build ~/Claude/research_timeseries/bib_ledger.yml
/dossier-build ~/Claude/research_jailbreak/bib_ledger.yml --output-dir ~/Claude/research_jailbreak/dossier/
```

**Default output dir**: `<bib_ledger_dir>/dossier/`.

## When to use

- After `/research-gather` produces a content-stable `bib_ledger.yml`.
- Re-run after material `bib_ledger.yml` edits (adding sources, changing claim_family, etc.).
- The dossier is the editable "raw research notes" form — humans may continue to edit the dossier files directly; the skill should not overwrite manual edits without warning.

**Upstream:** `/research-gather` produces `bib_ledger.yml`.
**Downstream:** `/agent-index` reads the dossier files to produce the agent-ready synthesis.

## Workflow

### Phase 1: load + analyze

Read the input `bib_ledger.yml`. Compute the claim_family distribution:
- How many entries per claim_family?
- Are there single-entry claim_families (consider merging)?
- Are there 50+ entry claim_families (consider splitting)?

Read the corresponding `research_plan.md` (typically `<bib_ledger_dir>/research_plan.md`) if it exists, to align topic-file boundaries with the plan's sub-areas.

### Phase 2: propose topic-file split

Propose 5–7 topic files. Each maps to one or more claim_family values. Common patterns:

| Pattern | Topic files |
|---|---|
| Attack/Defense | `01_attacks.md`, `02_defenses.md`, ... |
| Stage of pipeline | `01_attacks_direct.md`, `02_attacks_indirect.md`, `03_defenses.md`, `04_training_time.md`, ... |
| Methodology | `01_papers.md`, `02_datasets.md`, `03_tools.md`, `04_surveys.md` |

For the time-series mini fixture, the simple split is:
- `01_benchmarks_and_datasets.md` (claim_family: benchmark + dataset)
- `02_toolkits_and_surveys.md` (claim_family: toolkit + survey)

Surface the proposed split for user approval before writing files. Don't proceed silently — topic-file boundaries are an editorial choice.

### Phase 3: render entries as table rows

Read `~/Claude/research_toolkit/templates/dossier_table.template.md` for the canonical 7-column schema:

`Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution`

For non-paper content (vendor profiles, standards documents), use a different table schema with column 2 ≠ "Authors (year)" — see `templates/dossier_table.template.md` § "Non-paper variants".

Inside each topic file, group entries into sub-sections:
- `## A1. <sub-area>` for the first sub-section
- `## A2. <sub-area>` for the second
- etc., matching the research_plan's sub-area numbering when applicable

Render verbatim title (no title-casing); apply citation rules from `references/citation_rules.md` for URL canonical forms.

### Phase 4: update bib_ledger status

For each entry now cited in a dossier file, update its status from `unverified` to `verified` in `bib_ledger.yml`. (If a verified entry's title or authors don't match what you found while writing the dossier, set status to `mismatched` and surface the conflict.)

### Phase 5: write dossier README

Write `<output_dir>/_dossier_readme.md` (NOT `README.md` — that name is reserved for the agent-index README). Include:
- Compiled date
- Total entry count
- Entries per claim_family
- Pointer to the source `bib_ledger.yml`

### Phase 6: verify

Run the dossier validator on the output directory before exit.

## Templates

- `Read ~/Claude/research_toolkit/templates/dossier_table.template.md` — 7-column paper schema + non-paper variants.

## References

- `Read ~/Claude/research_toolkit/references/citation_rules.md` — URL canonical forms, author rendering, status flags.

## Validation

```bash
python ~/Claude/research_toolkit/validators/dossier.py <output_dir>
```

Validator checks: paper-table headers (`Title | Authors (year) | Venue | arXiv/DOI | <Code/GitHub variant>`), data row Title/Authors non-empty, at least one of arXiv/DOI or GitHub per row. Non-paper tables (col 2 ≠ "Authors (year)") get a looser check (Title non-empty + URL recommended).

## Output / handoff

**Produces:**
- `<output_dir>/0K_<topic>.md` — N topic-organized Markdown files (typically 5–7)
- `<output_dir>/_dossier_readme.md` — stats + cross-reference to bib_ledger
- Updates to `<bib_ledger_path>` (status field transitions: `unverified` → `verified` for cited entries)

**Consumed by:** `/agent-index <dossier_dir>` — synthesizes the dossier into a dual-audience indexed folder.

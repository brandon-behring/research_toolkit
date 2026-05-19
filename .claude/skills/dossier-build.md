---
name: dossier-build
description: Render a populated bib_ledger.yml into N topic-organized Markdown table files (the dossier). Groups entries by claim_family, picks topic file boundaries, renders 7-column tables, and reads evidence_ledger.yml when present to render strict-live verification status flags (read-only — does not write v2 artifacts). Output consumed by /agent-index.
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

Inside each topic file, group entries into sub-sections using the **per-file letter-prefix anchor convention**:
- File 01 uses `## A1.`, `## A2.`, ...
- File 02 uses `## B1.`, `## B2.`, ...
- File 03 uses `## C1.`, ...
- etc., matching the research_plan's sub-area numbering when applicable.

This convention is enforced by `tests/test_recreation_diff.py` and surfaced as cross-references in the agent-index. It propagates as a hard rule from the templates; do not invent new schemes.

**Worked example:** see `~/Claude/research_toolkit/tests/fixtures/medium_topic_calibration_subset/dossier/01_calibration_methods_metrics.md` — a 22-entry rendered dossier file that demonstrates the canonical 7-column schema with v1.1+ optional fields (authors, venue, code_url) populated. Mirror its row format exactly.

Render verbatim title (no title-casing); apply citation rules from `references/citation_rules.md` for URL canonical forms.

#### Cell rendering rules (HARD RULES — reproduced 2x as 404s in PEFT/calibration dogfood)

For each row, prefer the bib_ledger's optional `authors`, `venue`, `code_url` fields when populated:

- **Title**: copy `bib_ledger.title` verbatim. Do NOT abbreviate to a practitioner nickname (e.g., write "Language Models (Mostly) Know What They Know", not "LMs Mostly Know"). Display title = arXiv title verbatim.
- **Authors (year)**: use `bib_ledger.authors` if present. Otherwise derive from bibkey using the heuristic ("Hu et al. (2021)" / "Brier (1950)") and flag `(uncertain authors)` in the row's status text.
- **Venue**: use `bib_ledger.venue` if present. Otherwise default to "arXiv preprint" — DO NOT guess venues from memory; honest "arXiv preprint" beats wrong "ICML 2024".
- **arXiv/DOI**: derive from `bib_ledger.primary_url`. For arxiv URLs the validator requires the canonical `arxiv.org/abs/<id>` form.
- **GitHub**: use `bib_ledger.code_url` if present. Otherwise write `—`. **Do NOT guess `<firstauthor>/<paper-slug>` patterns.** The PEFT dogfood found 7/117 such guesses 404'd; calibration found 3/137 more. Real code lives at lab repos (`pilancilab/spectral_adapter`), author handles that don't match the bibkey (`EricLBuehler/xlora`), or doesn't exist at all. Empty cell `—` is correct when uncertain; the URL-freshness-check stage will surface real repos via inline correction if found.
- **One-line description**, **Key contribution**: factual, neutral, no hype.

If you find yourself writing a GitHub URL based on the pattern `github.com/<paper-firstauthor>/<paper-name>`, STOP. That's the failing pattern. Use `—`.

### Phase 4: preserve / update evidence-backed status

Rendering an entry into a dossier does NOT make it verified. For v2
strict-live projects, `verified` only means the relevant fields have supporting
evidence IDs and cache IDs in `evidence_ledger.yml` / `cache_manifest.yml`.

For v1 legacy ledgers, keep the existing status unless you actually re-fetch
the primary source while rendering. If a verified entry's title or authors do
not match the evidence you find, set status to `mismatched` and surface the
conflict.

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
- Updates to `<bib_ledger_path>` only when evidence-backed status or mismatch information changed

**Consumed by:** `/agent-index <dossier_dir>` — synthesizes the dossier into a dual-audience indexed folder.

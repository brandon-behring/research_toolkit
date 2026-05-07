---
name: research-gather
description: Discover primary sources for a research topic and populate bib_ledger.yml. Reads a research_plan.md, uses WebSearch + WebFetch to find papers / vendor blogs / datasets per sub-area, assigns bibkeys, optionally caches PDFs. Output consumed by /dossier-build.
allowed-tools: Read, Write, Edit, Bash, WebSearch, WebFetch
---

# /research-gather — Discover primary sources

## Usage

```
/research-gather <plan_path> [--cache-pdfs] [--output-dir <dir>]
```

**Examples:**
```
/research-gather ~/Claude/research_timeseries/research_plan.md
/research-gather ~/Claude/research_jailbreak/research_plan.md --cache-pdfs
```

**Default output dir**: same directory as `<plan_path>` (e.g., `~/Claude/research_<slug>/`).

## When to use

- After `/research-plan` produces a `research_plan.md`.
- May be re-run later when adding new sources to an existing dossier — pass the same plan path; the skill appends new entries (no duplicates per bibkey).
- `--cache-pdfs` is opt-in; expensive (per-paper download) and only needed when offline access is required.

**Upstream:** `/research-plan` produces the plan this skill consumes.
**Downstream:** `/dossier-build` reads `bib_ledger.yml` to render topic-organized table files.

## Workflow

### Phase 1: load plan + reference

Read the input `research_plan.md`. Extract:
- Sub-areas list (`## Sub-areas`)
- Source types per sub-area
- Out-of-scope list (skip queries adjacent to these)
- Claim family taxonomy (used to classify each entry)
- Known landmark papers (pre-populate without re-discovery)

Read `~/Claude/research_toolkit/references/citation_rules.md` for URL canonical forms and bibkey convention.

### Phase 2: per-sub-area search

For each sub-area, plan 2–4 web search queries based on its source-type list. Examples:
- `arXiv preprint` → `"<topic> arxiv 2024" OR "<topic> arxiv 2025"`
- `conference proceedings` → `"<topic> NeurIPS|ICML|ICLR|KDD|VLDB"`
- `vendor blog` → `"<topic> site:vendor.com|microsoft.com|anthropic.com"`
- `dataset card` → `"<topic> dataset huggingface.co/datasets"`
- `leaderboard` → `"<topic> leaderboard"`

Use `WebSearch` for each query. For results that look promising, use `WebFetch` to read the abstract / first page. Decide:
- Does this match the sub-area scope? (Skip if it's in the out-of-scope list)
- Is the URL canonical? (arXiv `/abs/` not `/pdf/`; GitHub repo root not subdir)
- Can you assign a bibkey from the authors + year + a 1-3 word slug?

Skip items already listed in `Known landmark papers` — note them as pre-populated, don't re-search.

### Phase 3: assign bibkey + claim_family

For each accepted source:
- Bibkey: `{firstauthor_lowercase}{year}{slug}` (per `citation_rules.md`)
- Resolve title verbatim from the primary source
- Classify under the plan's claim_family taxonomy
- Initial status: `unverified`

If no claim_family from the plan fits, flag this to the user — either the plan's taxonomy is missing a category, or the source is genuinely off-scope.

### Phase 4: write bib_ledger.yml

Read `~/Claude/research_toolkit/templates/bib_ledger.template.yml` for the canonical schema.

Write entries to `<output_dir>/bib_ledger.yml`. If the file already exists, append new entries (deduplicate by bibkey — fail with a clear error on duplicate).

### Phase 5 (optional): cache PDFs

If `--cache-pdfs` was passed:
- Create `<output_dir>/papers/`
- For each arXiv entry, download the PDF (`https://arxiv.org/pdf/<id>.pdf`) and save as `<slug>_<firstauthor>_<year>.pdf`
- Create `<output_dir>/cache/bib_primary_source_cache.yml` with metadata (authors list, source, title, url, year). Read `templates/bib_primary_source_cache.template.yml` for schema.

PDFs are gitignored at the toolkit level (`papers/` typically isn't committed).

### Phase 6: verify

Before exit:
- Every entry in `bib_ledger.yml` has all 5 required fields.
- All bibkeys are unique.
- All `claim_family` values appear in the plan's taxonomy.
- All `primary_url` values are valid http(s) URLs.

If any check fails, do NOT report success — fix the issue or surface it for user resolution.

## Templates

- `Read ~/Claude/research_toolkit/templates/bib_ledger.template.yml` — bib_ledger schema.
- `Read ~/Claude/research_toolkit/templates/bib_primary_source_cache.template.yml` — PDF cache schema (only if `--cache-pdfs`).

## References

- `Read ~/Claude/research_toolkit/references/citation_rules.md` — URL forms, bibkey convention.

## Validation

```bash
python ~/Claude/research_toolkit/validators/bib_ledger.py <output_dir>/bib_ledger.yml
```

Validator checks: required fields present, types valid, bibkeys unique, status enum valid (`unverified | verified | mismatched`), primary_url is well-formed.

## Output / handoff

**Produces:**
- `<output_dir>/bib_ledger.yml` — populated bibliography ledger
- `<output_dir>/papers/` — cached PDFs (only with `--cache-pdfs`)
- `<output_dir>/cache/bib_primary_source_cache.yml` — PDF metadata (only with `--cache-pdfs`)

**Consumed by:** `/dossier-build <bib_ledger_path>` — renders the entries into topic-organized Markdown tables.

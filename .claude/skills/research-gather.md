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

For strict-live v2 projects, also read
`~/Claude/research_toolkit/references/strict_live_v2.md`. The v2 contract is
primary-first, current-date-aware, and evidence-backed: every substantive claim
needs an evidence ID, every reachable source gets cached locally, and stale
entries block strict validation.

### Phase 2: per-sub-area search

For each sub-area, plan 2–4 web search queries based on its source-type list.
Use the current calendar year and the prior year for fast-moving fields; do
NOT hard-code stale year pairs. Examples:
- `arXiv preprint` → `"<topic> arxiv <current year>" OR "<topic> arxiv <prior year>"`
- `conference proceedings` → `"<topic> NeurIPS|ICML|ICLR|KDD|VLDB"`
- `vendor blog` → `"<topic> site:vendor.com|microsoft.com|anthropic.com"`
- `dataset card` → `"<topic> dataset huggingface.co/datasets"`
- `leaderboard` → `"<topic> leaderboard"`

Use `WebSearch` for each query. For results that look promising, use `WebFetch` to read the abstract / first page. Decide:
- Does this match the sub-area scope? (Skip if it's in the out-of-scope list)
- Is the URL canonical? (arXiv `/abs/` not `/pdf/`; GitHub repo root not subdir)
- Can you assign a bibkey from the authors + year + a 1-3 word slug?

Known landmark papers still require live verification in strict-live v2. Do not
trust memory or a plan annotation for title, first author, year, venue, code, or
current status.

### Phase 3: assign bibkey + claim_family + (optional) populate downstream fields

For each accepted source:
- Bibkey: `{firstauthor_lowercase}{year}{slug}` (per `citation_rules.md`)
- Resolve title verbatim from the primary source — DO NOT abbreviate or substitute practitioner nicknames. The arXiv `<title>` field is the source of truth.
- Classify under the plan's claim_family taxonomy
- Initial status: `unverified` (default; promote only via Phase 4 verification)

When you have already WebFetched the source page during this phase, populate the bib_ledger's optional fields too:
- `authors`: e.g., "Hu et al. (2021)" / "Brier (1950)" — directly from the abstract page's author list
- `venue`: e.g., "ICLR 2022", "NeurIPS 2024 Spotlight", or "arXiv preprint" — based on the abstract page's published-in field. **If you do not know the venue, write "arXiv preprint" — do not guess from memory.**
- `code_url`: ONLY if the abstract page or the project page links to a code repository. Common locations: arXiv "Code" tab, abstract page footer, paper PDF first-page footnote. **Do NOT guess `<firstauthor>/<paper-slug>` GitHub patterns** — PEFT/calibration dogfood produced ~3% hard-404 rate from this pattern. Omit the field entirely when uncertain; downstream stages render `—`.

Populating these three optional fields here means `/dossier-build` and `/agent-index` render from data instead of guessing — the highest-leverage v1.1 improvement.

**Worked example:** see `~/Claude/research_toolkit/tests/fixtures/medium_topic_calibration_subset/bib_ledger.yml` — a 22-entry calibration-subset fixture that demonstrates the v1.1+ format, including which entries have `code_url` populated (entries with a known canonical repo) and which omit it (pre-2010 classics with no canonical code release).

If no claim_family from the plan fits, flag this to the user — either the plan's taxonomy is missing a category, or the source is genuinely off-scope.

### Phase 4: write bib_ledger.yml (+ v2 artifacts for strict-live projects)

Read `~/Claude/research_toolkit/templates/bib_ledger.template.yml` for the canonical schema.

Write entries to `<output_dir>/bib_ledger.yml`. If the file already exists, append new entries (deduplicate by bibkey — fail with a clear error on duplicate).

#### v2 strict-live writes (when project uses `schema_version: 2`)

Populate v2 strict-live fields on every bib_ledger entry: `retrieved_at`, `verified_at`,
`verification_method`, `verified_fields`, `freshness_tier`,
`stale_after_days`, `evidence_ids`, and `cache_ids`.

For strict-live projects you MUST also write these companion artifacts as part of this skill's output. Downstream skills (`/agent-index`, `/freshness-audit`, `/dossier-audit`) assume they exist:

1. **`<output_dir>/cache_manifest.yml`** — read `templates/cache_manifest.template.yml`.
   For each reachable source, run:
   ```bash
   python ~/Claude/research_toolkit/scripts/cache_source.py <url> --topic <topic_slug>
   ```
   The script prints a manifest entry; append it to `cache_manifest.yml`. The script writes the raw blob + extracted text + metadata JSON into `~/Claude/research_cache/` (gitignored). Record the returned `cache_id` on the bib_ledger entry's `cache_ids` list.

2. **`<output_dir>/evidence_ledger.yml`** — read `templates/evidence_ledger.template.yml`.
   For each substantive claim that will appear in downstream synthesis (typically: the paper's headline result, key methodological choice, and any benchmark/scale numbers), create one evidence entry with `evidence_id`, `source_url`, `source_type`, `source_quality` (`primary` / `official` / `secondary` / `user_note`), `verification_method`, and `supports` (claim IDs + field paths). Record the `evidence_id` on the bib_ledger entry's `evidence_ids` list.

3. **`<output_dir>/claim_graph.jsonl`** — read `templates/claim_graph.template.jsonl`.
   For each bib_ledger entry, write JSONL records:
   - one `entity` record (entity_type = paper/dataset/benchmark/repo/etc.)
   - one `source` record (with cache_ids)
   - one `claim` record per evidence entry (claim_type = `fact` for headline result; populate `confidence.score` and `confidence.factors` based on source quality + verification status)
   - one `evidence` record per evidence_ledger entry (linking claim_ids and cache_ids)
   - one `cache_blob` record per cache_manifest entry

   **Note**: in Phase 2 of the v2.0 work this manual claim_graph creation will be replaced by `scripts/build_claim_graph.py`. Until that script exists, populate claim_graph.jsonl by following the template — one record per line, fields per `templates/claim_graph.template.jsonl`.

Validate each artifact before exit (see Phase 6).

### Phase 5 (optional): cache PDFs

If `--cache-pdfs` was passed:
- Create `<output_dir>/papers/`
- For each arXiv entry, download the PDF (`https://arxiv.org/pdf/<id>.pdf`) and save as `<slug>_<firstauthor>_<year>.pdf`
- Create `<output_dir>/cache/bib_primary_source_cache.yml` with metadata (authors list, source, title, url, year). Read `templates/bib_primary_source_cache.template.yml` for schema.

PDFs are gitignored at the toolkit level (`papers/` typically isn't committed).

### Phase 6: verify (HARD REQUIREMENTS — failures here block downstream stages)

Before exit:

**Schema checks (the validator enforces these; you should pre-check):**
- Every entry has all 5 required fields (`bibkey`, `primary_url`, `title`, `status`, `claim_family`).
- All bibkeys are unique.
- All `claim_family` values appear in the plan's taxonomy.
- All `primary_url` values are valid http(s) URLs.
- arxiv.org URLs use the canonical `arxiv.org/abs/<id>` form (no `/pdf/`, no version suffix unless intentional).

**Verification protocol (governs the `status` field):**

`status` semantics are strict:
- `unverified` (default): bibkey + URL are syntactically valid, but title/first-author/year have NOT been WebFetch-confirmed.
- `verified`: WebFetch on `primary_url` returned a page whose title matches `title` AND first author surname matches the bibkey's `{firstauthor}` AND year matches the bibkey's `{year}`. Promote to `verified` only with this evidence.
- `mismatched`: WebFetch returned different attribution than the entry claims. Surface as a CORRECT candidate; do not silently fix.

When time-pressed, default ALL entries to `unverified`. The downstream `/dossier-audit` stage runs the WebFetch confirmation and promotes entries based on evidence. **Avoid the v1.0 anti-pattern of marking all entries `verified` from memory** — calibration produced 1 misattribution-out-of-88 this way that only Stage 5 caught.

**Count-assertion (HARD REQUIREMENT for the final report):**

Your final report's "total entries" count MUST match the actual file count. Compute programmatically before reporting:

```bash
grep -c "^- bibkey:" <output_dir>/bib_ledger.yml
```

The narrative count in your final report must equal that number. calibration Stage 2 reported "73 entries" but the file had 88 — silently inconsistent self-reporting. If your count and the file's grep-count differ, recount before reporting.

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
- `<output_dir>/evidence_ledger.yml` (v2 strict-live only) — field-level evidence entries linking claims to primary/official sources
- `<output_dir>/cache_manifest.yml` (v2 strict-live only) — SHA-256-keyed manifest of cached source artifacts
- `<output_dir>/claim_graph.jsonl` (v2 strict-live only) — JSONL records (entity / source / claim / evidence / cache_blob) consumed by `/research-kb-export`
- `~/Claude/research_cache/` (v2 strict-live only) — raw + text + metadata blobs written by `scripts/cache_source.py` (gitignored)
- `<output_dir>/papers/` — cached PDFs (only with `--cache-pdfs`)
- `<output_dir>/cache/bib_primary_source_cache.yml` — PDF metadata (only with `--cache-pdfs`)

**Consumed by:** `/dossier-build <bib_ledger_path>` — renders the entries into topic-organized Markdown tables. For v2 strict-live projects, `/freshness-audit` and `/agent-index` also read the v2 companion artifacts.

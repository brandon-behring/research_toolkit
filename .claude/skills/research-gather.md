---
name: research-gather
description: Use when the user has a research_plan.md ready and asks to discover sources, build a bib_ledger, gather primary references, or populate a v2 strict-live project. Reads the plan, uses WebSearch + WebFetch to find papers / vendor blogs / datasets per sub-area, assigns bibkeys, optionally caches PDFs. For strict-live projects, also writes evidence_ledger.yml + cache_manifest.yml + claim_graph.jsonl. Output consumed by /dossier-build.
allowed-tools: Read, Write, Edit, Bash, WebSearch, WebFetch
---

# /research-gather — Discover primary sources

## Usage

```
/research-gather <plan_path> [--output-dir <dir>]
```

**Examples:**
```
/research-gather ~/Claude/research-dossiers/research_timeseries/research_plan.md
/research-gather ~/Claude/research-dossiers/research_jailbreak/research_plan.md
```

**Default output dir**: same directory as `<plan_path>` (e.g., `~/Claude/research-dossiers/research_<slug>/`).

## When to use

- After `/research-plan` produces a `research_plan.md`.
- May be re-run later when adding new sources to an existing dossier — pass the same plan path; the skill appends new entries (no duplicates per bibkey).
- The optional PDF-caching step (Phase 5 below) is opt-in; expensive (per-paper download) and only needed when offline access is required. There is **no `--cache-pdfs` flag** — `cache_source.py` extracts PDF text by default (opt out with `--no-extract-pdfs`). Control PDF caching by running or skipping Phase 5.

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

**Tool-call discipline**: see `~/Claude/research_toolkit/references/agent_discipline.md` for full guidance. Summary:
- Cap each dispatched agent at ~25-30 tool calls. ~3-4 calls per source (WebSearch + WebFetch + cache + Write) means a 10-source sub-area already runs at the cap; split high-volume sub-areas across two narrower agents rather than one wide one (e.g., "track A: 5 sources" + "track B: 5 sources" + "synthesis" instead of one agent covering 10).
- After every 5-6 sources written, run `python ~/Claude/research_toolkit/validators/bib_ledger.py <output_dir>/bib_ledger.yml` on the partial file. Failing fast catches systematic drift (broken bibkey, wrong status enum, paraphrased claim_family) before it propagates to remaining sources.

Use `WebSearch` for each query. For results that look promising, use `WebFetch` to read the abstract / first page. Decide:
- Does this match the sub-area scope? (Skip if it's in the out-of-scope list)
- Is the URL canonical? (arXiv `/abs/` not `/pdf/`; GitHub repo root not subdir)
- Can you assign a bibkey from the authors + year + a 1-3 word slug?

**Prefer open-access canonical sources (v2.6).** When a paper is on arXiv,
cite and cache the `arxiv.org/abs/<id>` page rather than a paywalled-journal
HTML page or a JS-rendered stub. `cache_source.py` reinforces this: on a
suspect/stub fetch of an arXiv URL it auto-fetches the plain-HTML abs page
(no Playwright needed) and records `escalation_reason: arxiv_abs_fallback`.
Only fall back to a paywalled / HTML snapshot when no open version exists
(then set `rights_status: restricted` per `references/citation_rules.md`).
Source-tier rules (T1 `arxiv.org/abs/*`; third-party-citing-T1 ≠ T1) live in
`references/citation_rules.md`; the primary-first posture is in
`references/strict_live_v2.md`.

Known landmark papers still require live verification in strict-live v2. Do not
trust memory or a plan annotation for title, first author, year, venue, code, or
current status.

#### Self-RAG reflection (v2.2; strict-live projects only)

For strict-live projects, every WebSearch + WebFetch becomes a row in
`<output_dir>/gather_trace.yml`. After each fetch, emit a structured
reflection record with `is_relevant` / `is_supported` / `is_useful` and a
decision (`accept` / `reject` / `escalate_to_manual`). This makes the
discovery step auditable after the fact instead of relying on author memory.

See `templates/gather_trace.template.yml` for the canonical schema.

Reflection rules:
- `is_relevant`: true if the fetched source matches the sub-area scope.
- `is_supported`: `full` if the source covers all the sub-area's claims; `partial` if some; `none` if it's orthogonal or unrelated.
- `is_useful`: integer 1–5 (1 = vendor marketing / no methodology; 5 = primary peer-reviewed paper with quantitative results).
- `decision`: `accept` (assign bibkey + write evidence entry below); `reject` (don't add to bib_ledger; record the reason); `escalate_to_manual` (sub-area partially covered and user judgment is needed).
- `accept` requires `assigned_bibkey`; `reject` / `escalate_to_manual` must omit it.

The trace is one row per (search, fetch) pair, not one row per accepted source. Rejected and escalated fetches stay in the trace as audit evidence that the search was performed and the decision was deliberate.

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
- `published_online` (v2.6): the original online publication date (`YYYY-MM-DD`) when determinable. `cache_source.py` captures it automatically (arXiv API / Crossref / HTML `<meta>` tags) into the cache metadata + the manifest entry it prints — carry that value onto the bib_ledger entry. **Why:** it lets `/freshness-audit` judge *content* age, not just cache age (a paper cached today may be five years old). Omit when the cache step didn't resolve one — never the server `Last-Modified` (that's file mod time, not pub date).

Populating these three optional fields here means `/dossier-build` and `/agent-index` render from data instead of guessing — the highest-leverage v1.1 improvement.

**Worked example:** see `~/Claude/research_toolkit/tests/fixtures/medium_topic_calibration_subset/bib_ledger.yml` — a 22-entry calibration-subset fixture that demonstrates the v1.1+ format, including which entries have `code_url` populated (entries with a known canonical repo) and which omit it (pre-2010 classics with no canonical code release).

If no claim_family from the plan fits, flag this to the user — either the plan's taxonomy is missing a category, or the source is genuinely off-scope.

### Phase 4: write bib_ledger.yml (+ v2 artifacts for strict-live projects)

Read `~/Claude/research_toolkit/templates/bib_ledger.template.yml` for the canonical schema.

Write entries to `<output_dir>/bib_ledger.yml`. If the file already exists, append new entries (deduplicate by bibkey — fail with a clear error on duplicate).

**HARD RULE — write each source incrementally.** Append every source to the on-disk artifacts (bib_ledger.yml + the v2 companions + gather_trace.yml) the moment it is confirmed, cached, and anchored — do NOT accumulate sources in memory to dump once at the end. A gather sub-agent that holds its sources in memory and drops on a socket close after hours of work loses every record: the content-addressed cache survives (each blob is on disk under `~/Claude/research_cache/`), but the sources list it was feeding does not. Writing per-source means a mid-run crash costs at most the one in-flight source, and the rest are recoverable. If a crash happens anyway, see "Resuming a crashed gather" below.

#### v2 strict-live writes (when project uses `schema_version: 2`)

Populate v2 strict-live fields on every bib_ledger entry: `retrieved_at`, `verified_at`,
`verification_method`, `verified_fields`, `freshness_tier`,
`stale_after_days`, `evidence_ids`, and `cache_ids`.

For strict-live projects you MUST also write these companion artifacts as part of this skill's output. Downstream skills (`/agent-index`, `/freshness-audit`, `/dossier-audit`) assume they exist:

1. **`<output_dir>/cache_manifest.yml`** — read `templates/cache_manifest.template.yml`.
   For each reachable source, run:
   ```bash
   python ~/Claude/research_toolkit/scripts/cache_source.py <url> --topic <topic_slug> --escalate-on-failure
   ```
   The script prints a manifest entry; append it to `cache_manifest.yml`. The script writes the raw blob + extracted text + metadata JSON into `~/Claude/research_cache/` (gitignored). Record the returned `cache_id` on the bib_ledger entry's `cache_ids` list.

   **Escalation is default-on**: pass `--escalate-on-failure` on every `cache_source.py` invocation (including the PDF path in Phase 5). It retries via headless Chromium (Playwright) when urllib hits HTTP 403/429 or returns a suspect JS-shell stub — so paywalled / SPA-rendered sources are captured rather than stubbed. Requires `pip install -e ".[dev]" && playwright install chromium`; if Playwright is absent the flag degrades gracefully (403/429 re-raises the HTTP error; suspect content falls back to a `stub` record) with a stderr WARN, so it is safe to pass unconditionally.

2. **`<output_dir>/evidence_ledger.yml`** — read `templates/evidence_ledger.template.yml`.
   For each substantive claim that will appear in downstream synthesis (typically: the paper's headline result, key methodological choice, and any benchmark/scale numbers), create one evidence entry with `evidence_id`, `source_url`, `source_type`, `source_quality` (`primary` / `official` / `secondary` / `user_note`), `verification_method`, and `supports` (claim IDs + field paths). Record the `evidence_id` on the bib_ledger entry's `evidence_ids` list.

   **Controlled enums (validator source of truth — do not invent values).** The
   evidence-ledger validators reject any value outside these sets. Copy the exact
   tokens; they are case-sensitive. (Sources: `validators/v2_common.py`
   `ALLOWED_*` + `validators/evidence_ledger.py`.)

   | Field | Allowed values |
   |---|---|
   | `source_type` | `api`, `benchmark`, `blog`, `dataset`, `leaderboard`, `other`, `paper`, `policy`, `repo`, `standard`, `vendor` |
   | `source_quality` | `official`, `primary`, `secondary`, `user_note` |
   | `verification_method` | `api`, `inaccessible`, `manual`, `pdf`, `webfetch`, `websearch_snippet` |
   | `extraction_method` | `llm_inferred`, `manual_override`, `paraphrase`, `propagated_from_child`, `user_asserted`, `verbatim_match` |
   | `evidence_role` (`supports[*].role`) | `contradicts`, `dates`, `defines`, `identifies`, `mentions`, `qualifies`, `supports` |

   `verification_method` records **how** a field was checked, not **when** — put
   the date in `verified_at`. Never write `webfetch_<date>` or a custom token like
   `cross_reference`; those fail the validator.

3. **`<output_dir>/claim_graph.jsonl`** — generated mechanically from the artifacts written in steps 1 + 2. Run:

   ```bash
   python ~/Claude/research_toolkit/scripts/build_claim_graph.py <output_dir>
   ```

   The builder reads bib_ledger / dataset_ledger / evidence_ledger / cache_manifest and emits:
   - one `entity` record per bib/dataset entry (entity_type derived from `claim_family` for bib or `source` field for dataset)
   - one `source` record per unique primary URL (cache_ids unioned across ledger entries pointing at that URL)
   - one `claim` record per distinct claim_id referenced in `evidence_ledger.supports[*].claim_id`, with text from the highest-quality supporting evidence's `excerpt` field; ties broken by longest excerpt. Confidence score: `primary → 0.95, official → 0.85, secondary → 0.60, user_note → 0.50`
   - one `evidence` record per evidence_ledger entry
   - one `cache_blob` record per cache_manifest entry

   The builder validates output before writing; non-zero exit means the project state is inconsistent (typically: a claim's evidence isn't referenced by any bib/dataset entry, so entity_ids can't be derived).

   `--no-overwrite` will refuse if `claim_graph.jsonl` already exists; default is overwrite-from-scratch (the bib/dataset/evidence ledgers are the source of truth).

Validate each artifact before exit (see Phase 6).

### Phase 5 (optional): cache PDFs

If you are running this optional PDF-caching step:

**Step 5.0 (v2.4+ pre-cache scan).** BEFORE fetching new URLs, scan the
existing `<output_dir>/cache_manifest.yml` for entries where
`content_type == "application/pdf"` AND `extraction_status == "raw_only"`.
If any exist, run:

```bash
python ~/Claude/research_toolkit/scripts/reextract_pdfs.py \
  <output_dir>/cache_manifest.yml
```

This upgrades v2.2-era cached PDFs to v2.3+ extraction in place (no
re-download — reads from the existing cached blob). Idempotent: no-op
when zero raw_only PDFs exist (the script's first action prints
`OK: ... has 0 raw_only PDF entries to re-extract` and exits 0 in that
case, so skipping the script when the manifest has no raw_only PDFs is
fine but not required).

WARNs from this step append to the same per-host
`<cache_root>/extraction_log_<hostname>.jsonl` that fresh-cache runs use,
so the end-of-run extraction summary (below) covers both.

**Step 5.1 — fresh cache:**
- Create `<output_dir>/papers/`
- For each arXiv entry, download the PDF (`https://arxiv.org/pdf/<id>.pdf`) and save as `<slug>_<firstauthor>_<year>.pdf`
- Create `<output_dir>/cache/bib_primary_source_cache.yml` with metadata (authors list, source, title, url, year). Read `templates/bib_primary_source_cache.template.yml` for schema.

PDFs are gitignored at the toolkit level (`papers/` typically isn't committed).

#### v2.3+ extraction summary (end-of-run)

When this optional PDF-caching step runs AND `cache_source.py` is invoked
against PDF URLs, each call appends one JSONL record to
`<cache_root>/extraction_log_<hostname>.jsonl` (per-host filename avoids
sync conflicts on Dropbox/Drive-hosted cache_root).

At the end of the run, read that log filtered by the run's start
timestamp (or just `tail -N` matching the count of fetches) and print an
aggregated summary like:

```
Extraction summary: 22 of 25 PDFs ok, 2 ok_text_only, 1 degraded
  ok_text_only: arxiv.org/abs/2401.XXXXX (Docling errored: ...)
  ok_text_only: arxiv.org/abs/2402.YYYYY
  degraded:     kohavi2012... (likely scanned/image PDF)
```

This catches consumer-visible extraction problems before the user notices
them downstream in `/agent-index` Phase 2a span-anchoring (now mechanized by
`scripts/build_excerpt_anchor.py`, which turns a verbatim excerpt + cache_id into a
self-verified `text_path_offset` + `sha256_of_span`). For batch debug
runs add `--strict-extraction` to `cache_source.py` so any non-ideal
status surfaces as exit-1 immediately.

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

### Resuming a crashed gather

When a gather drops before finishing, do NOT restart from zero. Every source confirmed before the crash is already in the content-addressed cache, so rebuild the sources skeleton from the cache and continue:

```bash
python ~/Claude/research_toolkit/scripts/resume_gather_from_cache.py <topic_slug> \
  [--existing <partial_sources.json>] --out <topic_slug>_sources.recovered.json
```

It selects this topic's cache blobs, fills the fields the cache knows (`sha`, `primary_url`, `published_online`), marks judgment fields (`bibkey`/`claim_family`/`sub_area` as `TODO`; `title`/`authors`/`venue`/`excerpt` as empty), and flags tiny/stub blobs `_low_quality` so you re-fetch them rather than trust them. Then:

1. Fill the placeholder fields for each recovered source from its cached text (path in `_cached_text_path`).
2. Continue gathering only the sub-areas still missing.
3. Re-running the tool is idempotent — it dedups by `sha` and `primary_url` and never overwrites a completed record — so pass the partial file back via `--existing`.

See `references/agent_discipline.md` for the full cache-as-checkpoint recovery procedure.

## Templates

- `Read ~/Claude/research_toolkit/templates/bib_ledger.template.yml` — bib_ledger schema.
- `Read ~/Claude/research_toolkit/templates/bib_primary_source_cache.template.yml` — PDF cache schema (only if running the optional Phase 5 PDF-caching step).

## References

- `Read ~/Claude/research_toolkit/references/citation_rules.md` — URL forms, bibkey convention.
- `Read ~/Claude/research_toolkit/references/agent_discipline.md` — tool-call budget, incremental-write rule, and the cache-as-checkpoint resume procedure.
- `scripts/resume_gather_from_cache.py` — rebuilds the sources skeleton from the content-addressed cache after a crash.

## Validation

```bash
python ~/Claude/research_toolkit/validators/bib_ledger.py <output_dir>/bib_ledger.yml
```

Validator checks: required fields present, types valid, bibkeys unique, status enum valid (`unverified | verified | mismatched`), primary_url is well-formed.

For strict-live v2.2+ projects, also run:

```bash
python ~/Claude/research_toolkit/validators/gather_trace.py <output_dir>/gather_trace.yml
```

Validator checks: schema_version present, fetches list non-empty, every fetch has IsRel/IsSup/IsUse + decision + reason, IsSup ∈ {full, partial, none}, IsUse integer 1–5, decision ∈ {accept, reject, escalate_to_manual}, assigned_bibkey present iff decision==accept, assigned_bibkey cross-resolves into bib_ledger when both files are present.

## Output / handoff

**Produces:**
- `<output_dir>/bib_ledger.yml` — populated bibliography ledger
- `<output_dir>/evidence_ledger.yml` (v2 strict-live only) — field-level evidence entries linking claims to primary/official sources
- `<output_dir>/cache_manifest.yml` (v2 strict-live only) — SHA-256-keyed manifest of cached source artifacts
- `<output_dir>/claim_graph.jsonl` (v2 strict-live only) — JSONL records (entity / source / claim / evidence / cache_blob) consumed by `/synthesis-export`
- `<output_dir>/gather_trace.yml` (v2.2+ strict-live only) — per-fetch Self-RAG reflection records (IsRel/IsSup/IsUse + decision); audit trail for discovery rigor
- `~/Claude/research_cache/` (v2 strict-live only) — raw + text + metadata blobs written by `scripts/cache_source.py` (gitignored)
- `<output_dir>/papers/` — cached PDFs (only when the optional Phase 5 PDF-caching step is run)
- `<output_dir>/cache/bib_primary_source_cache.yml` — PDF metadata (only when the optional Phase 5 PDF-caching step is run)

**Consumed by:** `/dossier-build <bib_ledger_path>` — renders the entries into topic-organized Markdown tables. For v2 strict-live projects, `/freshness-audit` and `/agent-index` also read the v2 companion artifacts.

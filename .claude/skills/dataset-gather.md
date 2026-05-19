---
name: dataset-gather
description: Discover public datasets for a research topic and populate dataset_ledger.yml. Searches across HuggingFace, Kaggle, academic repos (Zenodo/OSF/Figshare/ICPSR), aggregators (Google Dataset Search/OpenML), cloud-vendor open data, domain-specific portals (PhysioNet/iTrust/etc.), government open data, and classical ML repos. Output consumed by /dataset-index.
allowed-tools: Read, Write, Edit, Bash, WebSearch, WebFetch
---

# /dataset-gather — Discover public datasets for a topic

## Usage

```
/dataset-gather "<topic>" [--sources <comma-separated>] [--output-dir <dir>]
```

**Examples:**
```
/dataset-gather "time-series anomaly detection"
/dataset-gather "tabular benchmarks" --sources huggingface,uci,openml
/dataset-gather "biomedical text classification" --output-dir ~/Claude/research_<slug>/
```

**Default `--output-dir`**: `~/Claude/research_<slug>/` where `<slug>` is the
topic with spaces → underscores, lowercase.

**Default `--sources`**: all 8 categories (see `references/dataset_sources.md`).

## When to use

- When you need to know "what datasets exist for this topic?" with metadata
  (size, license, access method) — not just paper bibliography.
- Pairs with `/research-gather` for paper-side coverage. The two outputs are
  separate ledgers; both can exist for the same topic in sibling dirs.

**Upstream:** topic free-text. No `research_plan.md` required (datasets have
a fixed `task_family` enum; no per-topic taxonomy step needed).

**Downstream:** `/dataset-index <ledger>` renders the ledger as a consumer
artifact (5-bullet entries + AGENT-INDEX README).

## Workflow

### Phase 1: load reference (HARD REQUIREMENT)

Read `~/Claude/research_toolkit/references/dataset_sources.md` BEFORE any
search. It catalogs the 8 source categories with per-source discovery
methods + metadata-extraction strategies + gotchas. The skill body assumes
you're working from this catalog.

Read `~/Claude/research_toolkit/templates/dataset_ledger.template.yml` for
the schema.

For strict-live v2 projects, also read
`~/Claude/research_toolkit/references/strict_live_v2.md` plus:
- `templates/evidence_ledger.template.yml`
- `templates/cache_manifest.template.yml`
- `templates/claim_graph.template.jsonl`

The v2 contract is primary-first, current-date-aware, evidence-backed, and
max-local-cache by default. Every substantive claim gets an evidence ID; every
reachable source page/API payload/artifact gets cached locally for personal use
and later `research-kb` ingestion.

Read `~/Claude/research_toolkit/validators/dataset_ledger.py` to understand
the validator's enforcement (especially `task_family` fixed enum + memory-
verification anti-cheat heuristic at ≥30 entries).

**Worked example:** see
`~/Claude/research_toolkit/tests/fixtures/medium_dataset_subset/dataset_ledger.yml`
(populated after the v1.6 dogfood). It demonstrates the v1.6 schema with
full optional-field coverage, including which entries omit `code_url`-style
guesses (none — datasets don't have a code_url field analog; they have
`schema_url` for the dataset-card page).

### Phase 2: source-category sweep

For each `--sources` category (default: all 8), run discovery per
`dataset_sources.md`:

- **HuggingFace**: WebFetch `https://huggingface.co/api/datasets?search=<topic>&limit=100` for a JSON listing. Extract name + dataset card URL.
- **Kaggle**: WebSearch `<topic> site:kaggle.com/datasets`. WebFetch each candidate.
- **Zenodo / OSF / Figshare / ICPSR**: WebSearch `<topic> site:zenodo.org` (etc.) + each platform's own search.
- **Aggregators**: WebSearch `<topic> site:datasetsearch.research.google.com` (Google Dataset Search). Note: paperswithcode.com/datasets was an aggregator in v1.6 but is dead as of 2026 (redirects to HF papers/trending) — removed in v1.7.
- **Cloud open data**: WebSearch `<topic> site:registry.opendata.aws` (etc.).
- **Domain-specific**: skip if topic clearly off-domain. Otherwise: search NIH/NCBI for biomedical, FRED for economics, NASA for earth/climate, Common Crawl for web-scale.
- **Government**: WebSearch `<topic> site:data.gov` etc.
- **UCI / OpenML / awesome-* lists**: WebSearch `<topic> site:archive.ics.uci.edu` and `<topic> site:openml.org`. WebFetch awesome-public-datasets-style lists.

Use current-date-aware queries for fast-moving dataset/model-card ecosystems;
do not rely on fixed year examples. Secondary sources are discovery aids only;
final metadata and claims must cite primary or official dataset pages.

Dedupe across sources by primary URL (some datasets are mirrored on multiple
platforms; prefer the canonical source — usually HF for ML datasets, the
academic repo for academic datasets).

### Phase 3: per-candidate metadata fetch (HARD REQUIREMENT — verification)

For every candidate, WebFetch the source page and extract:

- `name` — dataset's official name (verbatim from the source page; do NOT abbreviate)
- `primary_url` — canonical landing page
- `license` — from the source page's license field; use `unknown` honestly when not disclosed
- `size` — human-readable (e.g., "1.2GB", "5M tokens", "365K rows")
- `rows` / `columns` — when known
- `schema_url` — link to the schema/card page if the source has one
- `access_method` — `hf datasets` / `direct` / `API` / `signup wall` / `credentialed`
- `auth_required` — true if download requires login / API key / signed agreement
- `citation` — recommended citation form

For v2, also populate per-entry strict-live fields: `retrieved_at`,
`verified_at`, `verification_method`, `verified_fields`, `freshness_tier`,
`stale_after_days`, `evidence_ids`, and `cache_ids`.

Cache every reachable dataset card, API JSON, README, schema page, license page,
repo archive, and downloadable artifact by default. If a very large dataset is
reachable and your access/terms allow it, cache it; record size, hash, access
conditions, and `restricted` status in `cache_manifest.yml`.

Assign `task_family` from the **fixed enum** (one of: classification,
regression, sequence_labeling, generation, retrieval, ranking, multimodal,
graph, time_series, tabular, recommendation, structured_prediction, other).
Use `other` honestly when the dataset doesn't fit; do NOT force-fit.

#### License capture — compound-license HARD RULE (v1.9)

**License capture must check both YAML AND prose.** When a source page
(HF dataset card, GitHub README, Zenodo metadata) declares a `license:`
field in its YAML/structured frontmatter, ALSO read the prose section
for restrictive caveats that contradict or restrict the declared license.

If the prose adds restrictions beyond the YAML license, render the
`license` field as `<base license> + custom restrictions: <one-line
summary>` and document the restrictions verbatim in the entry's
`citation` field or as a free-form note.

**Worked failure example (v1.8 dogfood)**: `berkeley-nest/Nectar`
declares `license: apache-2.0` in YAML but the prose says "non-commercial
research preview, not for use competing with OpenAI, subject to LLaMA +
OpenAI ToU + ShareGPT terms." A naive YAML-only read produces
"Apache-2.0" — materially wrong for downstream users who would treat
that as commercially-redistributable. The compound-license rendering is:

```yaml
license: 'apache-2.0 + custom restrictions: non-commercial research preview;
  not for competing with OpenAI; subject to LLaMA + OpenAI ToU + ShareGPT terms'
```

**When to use this rule**: every entry where the source page has BOTH a
structured license field AND a prose section discussing terms. If the
prose only restates the structured license (no new restrictions), no
compound-rendering needed.

### Phase 4: assign bibkey

`bibkey` convention: `{dataset_slug}{year}{source_short}`, e.g.:
- `nab2017kpi` (NAB benchmark, 2017, KPI flavor)
- `ucr2018archive` (UCR archive, 2018)
- `librispeech2015openslr` (LibriSpeech, 2015, OpenSLR)
- `imagenet2012ilsvrc` (ImageNet, 2012, ILSVRC challenge year)

All bibkeys must be unique within the ledger.

### Phase 5: status assignment (v1.5.1 STRICT VERIFICATION PROTOCOL)

`status` semantics:
- `unverified` (DEFAULT): bibkey + URL syntactically valid, but the source
  page hasn't been WebFetch-confirmed.
- `verified`: WebFetch confirmed the page exists AND name matches the
  ledger's `name` field AND license matches what's recorded.
- `mismatched`: WebFetch returned different attribution (different name,
  different license, redirected to unrelated page).

**HARD RULE: do NOT bulk-mark `verified` from memory.** The validator's
anti-cheat heuristic warns at ≥30 entries with 100% verified. A run with
~95% verified + a few honest `unverified` entries is the right shape.

When time-pressed, default to `unverified` and let `/dossier-audit` promote
based on evidence.

### Phase 6: write dataset_ledger.yml

Write to `<output_dir>/dataset_ledger.yml`. If the file already exists, append
new entries (deduplicate by `bibkey` — fail with a clear error on duplicate).

### Phase 7: verify

Before exit, run:

```bash
python ~/Claude/research_toolkit/validators/dataset_ledger.py <output_dir>/dataset_ledger.yml
```

The validator enforces:
- All required fields present (bibkey, primary_url, name, source, status, task_family)
- `task_family` ∈ fixed 13-value enum
- `auth_required` is bool when present
- bibkeys unique
- URLs well-formed
- Anti-cheat heuristic doesn't fire (or, if you have ≥30 entries, that you
  haven't bulk-marked everything `verified` from memory)

If validation fails, do NOT report success — fix the issue or surface it for
user resolution.

### Count-assertion (HARD REQUIREMENT for the final report)

Your final report's "total datasets" count MUST match the actual file count.
Compute programmatically before reporting:

```bash
grep -c "^- bibkey:" <output_dir>/dataset_ledger.yml
```

The narrative count in your final report must equal that number. If they
differ, recount before reporting. (vol28 §2.2 was the failure mode — applies
identically here.)

## Templates

- `Read ~/Claude/research_toolkit/templates/dataset_ledger.template.yml` — schema spec.

## References

- `Read ~/Claude/research_toolkit/references/dataset_sources.md` — HARD REQUIREMENT — load before searching.

## Validation

```bash
python ~/Claude/research_toolkit/validators/dataset_ledger.py <output_dir>/dataset_ledger.yml
```

After per-stage validator passes, also run `cross_stage` for cross-artifact
consistency (when there's a parallel paper-pipeline `<topic>_synthesis/` in
the same parent project; otherwise this is a no-op).

## Output / handoff

**Produces:** `<output_dir>/dataset_ledger.yml` — populated dataset ledger.

**Consumed by:** `/dataset-index <output_dir>/dataset_ledger.yml` — renders
the ledger into a 5-bullet-entry agent-index folder.

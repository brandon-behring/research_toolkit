# Dataset sources catalog (v1.7)

Reference doc for `/dataset-gather`. Catalogs the source categories the skill
searches, with per-source discovery method + metadata-extraction strategy +
known gotchas.

Read this BEFORE invoking `/dataset-gather` if you want to understand what
coverage to expect; the skill body assumes this doc exists and references it.

## Discovery priority order

When `/dataset-gather` runs against a topic, it searches sources in this order
(roughly by metadata richness + ease of programmatic access):

1. HuggingFace datasets (rich API; mostly NLP + vision)
2. Classical ML repos (UCI / OpenML; tabular benchmarks)
3. Academic repos (Zenodo, OSF, Figshare, ICPSR; DOI-stable)
4. Aggregators (Google Dataset Search; cross-vendor) — **note**: paperswithcode.com/datasets was on this list in v1.6 but is dead in 2026 (redirects to HF papers/trending). Removed.
5. Domain-specific portals (NIH, FRED, NASA, Common Crawl, **PhysioNet**, **Kaggle community**)
6. Cloud vendor open data (AWS, GCP, Azure; large + structured)
7. Government open data (data.gov, EU, UK)
8. Kaggle (skip if not auth'd; otherwise rich)
9. **Domain-specialized portals** (v1.7): security/ICS — SUTD iTrust, Morris-UAH, ELKI, KDD/NSL-KDD/CICIDS/UNSW; biomedical — PhysioNet (separately listed); IoT/storage — Backblaze; legacy time-series — Yahoo Webscope (deprecated/dead).

Skip categories that are clearly off-topic (e.g., NIH for a non-bio topic).

## When `source: other` is the right answer

The v1.6 dogfood on time-series anomaly detection produced 29% of entries with `source: other` — too many to be ignorable. Patterns where this is **expected**:

- **Critical-infrastructure / ICS topics**: SUTD iTrust (SWaT, WADI), Morris-UAH ICS, KDD/NSL-KDD/CICIDS, UNSW-NB15. These have established institutional hosts but don't fit the conventional aggregator/repo categories.
- **Biomedical signal data**: PhysioNet hosts most ECG / EEG / sleep-staging benchmarks with its own access policy (PhysioNet Credentialed Health Data License). Treat as its own category if doing biomedical work.
- **Legacy webscope**: Yahoo Webscope (S5, R6) is unmaintained as of 2025 but still cited heavily. Treat as `other` with `Status: Unverified` (signup wall + dead infrastructure).
- **Storage/IoT operational logs**: Backblaze drive stats (canonical disk-failure dataset), large telemetry archives.
- **Open-source benchmark suites that ship multiple datasets**: ELKI, TSB-AD, TSB-UAD — these are aggregators of canonical anomaly benchmarks but they're code repos, not "aggregator sites."

If your topic touches these areas, **expect 20-40% of entries to be `source: other`** and don't try to force-fit them into HF/Kaggle/Zenodo. Document the actual hosts in the `Tasks` bullet of each entry.

---

## 1. HuggingFace datasets

- **URL pattern**: `https://huggingface.co/datasets/<org>/<dataset>`
- **Discovery**: HF datasets search API — `https://huggingface.co/api/datasets?search=<topic>` returns JSON. Or WebSearch for `<topic> site:huggingface.co/datasets`.
- **Metadata extraction**: dataset card (`/datasets/<org>/<dataset>` page) has license, task tags, citation, size in MB/GB. The `dataset_info` API returns rows + features.
- **License capture**: HF cards have a `license:` field in YAML frontmatter when filled. Often `unknown` for older entries.
- **Schema**: dataset card lists features (column names + types). Rich.
- **Gotchas**:
  - Dataset cards can be sparse/missing (check `last_modified`).
  - Some datasets are gated (HF requires login). Mark `auth_required: true`.
  - Large datasets stream-only (e.g., LAION) — note this in `access_method`.

## 2. Kaggle datasets

- **URL pattern**: `https://www.kaggle.com/datasets/<owner>/<slug>`
- **Discovery**: WebSearch `<topic> site:kaggle.com/datasets`. The Kaggle API requires auth — listing IS public via WebSearch.
- **Metadata extraction**: Kaggle dataset pages list license, size, columns (for tabular), upvotes (popularity proxy). Schema is in the "Data" tab; column names + types visible.
- **Gotchas**:
  - Downloading requires Kaggle API key — mark `auth_required: true` even though listing is public.
  - Many datasets are user-uploaded and have unclear original-source citation. Flag with `citation: '(community upload)'`.
  - Competition datasets often have restrictive licenses.

## 3. Academic repositories

### Zenodo
- **URL pattern**: `https://zenodo.org/records/<id>` or `https://doi.org/10.5281/zenodo.<id>`
- **Discovery**: WebSearch `<topic> zenodo`. Zenodo has its own search at `https://zenodo.org/search?q=<topic>`.
- **Metadata extraction**: Zenodo records have license (typically CC-BY-4.0 or CC0), DOI, citation, files list. Rich.
- **Gotchas**: Zenodo records are versioned (multiple versions of same dataset). Use the latest unless the version-pinned one is canonical.

### OSF (Open Science Framework)
- **URL pattern**: `https://osf.io/<id>/`
- **Discovery**: WebSearch `<topic> site:osf.io`. OSF has search but it's noisy.
- **Metadata extraction**: License + DOI + files visible on the project page.
- **Gotchas**: OSF projects can be works-in-progress; check `status: <published/in-progress>`.

### Figshare
- **URL pattern**: `https://figshare.com/articles/<type>/<title>/<id>`
- **Discovery**: WebSearch `<topic> site:figshare.com`.
- **Gotchas**: Mostly individual-file uploads; less curated than Zenodo.

### ICPSR (Inter-University Consortium for Political and Social Research)
- **URL pattern**: `https://www.icpsr.umich.edu/web/ICPSR/studies/<id>`
- **Discovery**: WebSearch `<topic> site:icpsr.umich.edu`.
- **Gotchas**: Most ICPSR datasets require institutional login. Mark `auth_required: true` and `access_method: signup wall`.

## 4. Aggregators

### ~~Papers with Code datasets~~ (DEAD as of 2026 — removed in v1.7)

- **Status (2026)**: `paperswithcode.com/datasets` redirects to `huggingface.co/papers/trending`. Confirmed during v1.6 dogfood. Do NOT search this URL.
- **What replaced it**: HF datasets directly + Google Dataset Search.
- **Historical note**: PWC was useful from ~2018-2024 as a cross-vendor aggregator that linked datasets to the papers that used them. The link-graph is now lost; rebuilding via HF is the supported path.

### Google Dataset Search
- **URL pattern**: `https://datasetsearch.research.google.com/search?query=<topic>`
- **Discovery**: Returns metadata aggregated from schema.org/Dataset markup across the web.
- **Gotchas**: Quality varies wildly. Use as a "did I miss anything?" check, not a primary source.

### OpenML
- **URL pattern**: `https://www.openml.org/d/<id>`
- **Discovery**: OpenML has a real API + search. Mostly tabular benchmarks.
- **Metadata extraction**: Rich metadata (number of features, classes, missing values, citation). Best for classical ML benchmarks.
- **Gotchas**: License often unspecified; default to `unknown`.

## 5. Domain-specific portals

### NIH / NCBI (biomedical)
- **URL patterns**: `ncbi.nlm.nih.gov/<resource>/<id>` (e.g., GEO, SRA, dbSNP, ClinVar). PubMed for paper-linked.
- **Discovery**: NCBI search API.
- **Gotchas**: Some require approval (dbGaP). Mark accordingly.

### FRED (Federal Reserve Economic Data)
- **URL pattern**: `fred.stlouisfed.org/series/<id>`
- **Discovery**: FRED API or web search.
- **Gotchas**: Free + public domain.

### NASA Earthdata
- **URL pattern**: `earthdata.nasa.gov` and DAAC subdomains.
- **Discovery**: CMR API + Earthdata search.
- **Gotchas**: Many datasets require Earthdata Login (free but registration). Mark `auth_required: true`.

### Common Crawl
- **URL pattern**: `commoncrawl.org` and `data.commoncrawl.org`
- **Discovery**: Crawl-by-crawl listing on the site.
- **Gotchas**: Petabyte-scale; usable only via S3 or specific extraction tools. Mark `size: ~PB` and `access_method: API` (S3).

## 6. Cloud vendor open data

### AWS Open Data Registry
- **URL pattern**: `registry.opendata.aws/`
- **Discovery**: Browse the registry directly. Each entry links to AWS resources (S3 buckets, etc.).
- **Metadata extraction**: License, size, update frequency on each registry page.
- **Gotchas**: "Free" usually means free download from S3 in the right region; egress to other regions may incur cost.

### GCP Public Datasets
- **URL pattern**: `cloud.google.com/datasets`
- **Discovery**: GCP marketplace.
- **Gotchas**: Some require GCP project + billing setup even if data is "free". Note in `auth_required`.

### Azure Open Datasets
- **URL pattern**: `azure.microsoft.com/en-us/products/open-datasets/catalog/`
- **Gotchas**: Smaller catalog than AWS or GCP. Mostly Microsoft-curated subsets.

## 7. Government open data

### data.gov (US)
- **URL pattern**: `catalog.data.gov/dataset/<slug>`
- **Discovery**: data.gov search.
- **Gotchas**: License varies by agency; many are public domain (US gov work) but some cite "Creative Commons" without explicit version.

### data.europa.eu (EU)
- **URL pattern**: `data.europa.eu/data/datasets/<slug>`
- **Discovery**: EU data portal search.
- **Gotchas**: Often multilingual; check if you need the English version specifically.

### data.gov.uk
- **URL pattern**: `data.gov.uk/dataset/<slug>`
- **Gotchas**: UK Open Government Licence (OGL) — permissive but cite it as such.

## 8. Classical ML repos

### UCI Machine Learning Repository
- **URL pattern**: `archive.ics.uci.edu/dataset/<id>/<slug>`
- **Discovery**: UCI search. Modern UI; old datasets have been migrated.
- **Metadata extraction**: License, citation, attribute info. Some entries are XML-shaped (older); the modern UI fixes this.
- **Gotchas**: Many UCI datasets have non-redistributable licenses despite being "free." Read the dataset's individual page for license details.

### awesome-public-datasets (curated lists on GitHub)
- **URL pattern**: `github.com/awesomedata/awesome-public-datasets` (the canonical list) and topic-specific lists like `awesome-time-series-dataset`, `awesome-nlp-datasets`, `awesome-medical-data`, etc.
- **Discovery**: WebSearch `awesome <topic> datasets github`.
- **Metadata extraction**: These are link aggregators; click through to the actual source for canonical metadata.
- **Gotchas**: Stale links common. Always WebFetch the linked URL to confirm it's still live.

---

## Discovery strategy summary

For a new topic, run sources in priority order. For each source:
1. Search.
2. Triage results (filter by topic relevance — drop obvious off-topic hits).
3. WebFetch each candidate's metadata page.
4. Extract: name, license, size, schema (if available), access method.
5. Set `status: verified` only if WebFetch confirmed the page exists and matches.

Time budget: 30-50 datasets in ~30-45 minutes if running across HF + UCI +
academic + 1-2 aggregators. Adding cloud + government + domain-specific
portals adds depth but also adds time per-source.

## Honest signals

A run that hits ALL 8 source categories with ~5+ datasets per category is
suspiciously over-comprehensive — most topics are concentrated in 2-4 sources.
A discovery skill that consistently produces "5 from each category" is likely
making things up.

A run that produces 30 datasets but only from HF is honest but narrow —
flag in BURN_IN as "did not exhaustively search non-HF sources."

Trust the per-source-category gotchas above. The dossier-audit stage will
catch obvious mistakes (license = "MIT" on a dataset with a custom EULA, etc.).

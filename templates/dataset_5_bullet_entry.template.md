# Dataset 5-bullet entry template (v1.6)

The canonical shape of a single dataset entry in the agent_index synthesis.
Mirrors `5_bullet_entry.template.md` (paper-pipeline) but with dataset-specific bullets.

## Schema (5 bullets)

```markdown
- **<Dataset name>** — <Source / org> (<year>).
  - **Source:** <primary URL — HF page / Zenodo DOI / Kaggle / direct host>
  - **Access:** <method (hf datasets / direct / API / signup wall); auth_required: Y/N>
  - **Schema:** <N cols, key column types; schema_url if available>
  - **Size+License:** <rows / GB / tokens>; <license shorthand: CC-BY-4.0, MIT, custom, unknown>
  - **Tasks:** <what the dataset is used for; benchmarks built on it>
  - **Status:** <Verified | Unverified | (uncertain license) Verified>
```

## Worked example (filled in)

```markdown
- **Numenta Anomaly Benchmark (NAB)** — Numenta (2017).
  - **Source:** https://github.com/numenta/NAB
  - **Access:** direct download from GitHub repo; auth_required: N
  - **Schema:** 58 streams, each one-column timeseries (timestamp, value);
    schema_url: https://github.com/numenta/NAB/blob/master/labels/combined_labels.json
  - **Size+License:** ~365K rows across all streams; ~50MB; AGPL-3.0
  - **Tasks:** time-series anomaly detection benchmark; widely used in
    streaming-anomaly methodology papers
  - **Status:** Verified.
```

## Worked example (unknown license — `unknown` is honest, not "guessed")

```markdown
- **Yahoo S5 Webscope Benchmark** — Yahoo (2015).
  - **Source:** https://webscope.sandbox.yahoo.com/catalog.php?datatype=s
  - **Access:** signup wall; auth_required: Y (researcher agreement required)
  - **Schema:** 367 timeseries with hourly granularity; tabular: 4 cols
    (timestamp, value, anomaly, change_point)
  - **Size+License:** ~370K rows; small; **license: unknown** (Yahoo Webscope ToU
    requires per-researcher agreement; not redistributable)
  - **Tasks:** time-series anomaly detection; reference benchmark in many
    streaming-anomaly papers (e.g., Twitter Anomaly Detection)
  - **Status:** (uncertain license — non-redistributable) Verified.
```

## Hard rules (carried up from /dataset-build skill body)

- **Name**: copy `dataset_ledger.name` verbatim. Do NOT abbreviate to a slug.
- **Source URL**: from `dataset_ledger.primary_url` directly.
- **Access**: combine `access_method` + `auth_required` from ledger. Default
  `direct` + `auth_required: N` if both unknown — flag with `(uncertain access)`.
- **Schema**: short summary; link to schema_url if ledger has it. Do NOT
  invent column counts.
- **Size+License**: from `size` + `license` ledger fields. If license is
  `unknown` in the ledger, render it verbatim ("license: unknown") — do NOT
  guess by inference from source category.
- **Tasks**: short prose about what tasks the dataset is used for. Cite
  benchmark papers if known, but don't fabricate citations.
- **Status**: same as paper-pipeline. Append `(uncertain X)` when a field
  is honest-unknown, never when it's "I didn't bother checking."

## Why these 5 bullets (vs paper-pipeline's Source/Code/Mechanism/Result/Status)

Datasets aren't claims; they're artifacts. The 5 bullets answer:
1. **Source** — where does it live?
2. **Access** — can I get it? auth required?
3. **Schema** — what's in it structurally?
4. **Size+License** — how big? can I use it for my purpose?
5. **Tasks** — what's it for?

These 5 are the minimum metadata for a practitioner to decide "is this the
right dataset for my problem?" without downloading.

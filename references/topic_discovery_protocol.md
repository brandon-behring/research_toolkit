# Topic discovery protocol (v1)

Reference doc for `/topic-discovery`. Defines the method for mining a knowledge
corpus into a prioritized, deduplicated `topic_backlog.yml` of **deepen** and
**adjacent** research topics.

Read this BEFORE invoking `/topic-discovery`; the skill body assumes this doc
exists and references it. The default corpus is the interview-prep LaTeX series
at `~/interview_prep_series`; the method generalizes to any corpus exposing
volumes + learning objectives + reading lists.

## Corpus shape (interview_prep_series)

- `volumes.yml` — registry of `volumes:` (numbered, tracks 1-7) + `satellites:`
  (company/cert). Loadable via `scripts/lib/volume_scope.py::get_all_volumes()`
  → `VolumeInfo(dir_name, slug, los_prefix, track, track_name, num, is_satellite)`.
- Per-volume LOS embedded in LaTeX at `<dir_name>/chapters/<NN>_*.tex` as
  `\los{ID}{bloom_level}{statement}`. Extract via
  `scripts/lib/los_utils.py::extract_volume_los(repo_root, vol_dir)` →
  dicts `{id, level, statement, file, line, chapter_num}`.
- Per-volume `reading_list.yml` (SPARSE — present for ~1 of 39 volumes). Where
  present, the strongest deepen signal: curated frontier papers + a `to_acquire`
  / `research_kb: null  # NEED TO ACQUIRE` section the author already flagged.

`bloom_level` is an open ~60-verb vocabulary, NOT a 6-value enum. Treat these as
the **high-Bloom whitelist** (frontier-signalling):

    analyze, evaluate, design, synthesize, formulate, architect, create,
    develop, diagnose, construct

## Step 0 — load the corpus (reuse-first)

Primary: run the prep repo's loaders via Bash from the corpus root, e.g.

```bash
python3 -c "import sys; sys.path.insert(0, '$HOME/interview_prep_series'); \
from scripts.lib.volume_scope import get_all_volumes; \
from scripts.lib.los_utils import extract_volume_los; \
... print as JSON ..."
```

Fallback if `scripts/lib` is absent: `yaml.safe_load` `volumes.yml` (keys
`volumes:` + `satellites:`); glob `<dir>/chapters/*.tex`; regex
`\\los\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}` for LOS and
`\\(chapter|section|part)\{([^}]+)\}` for titles.

**HARD RULE: emit only `topic_id` / `source_volume` / `source_los` values the
loader actually returned. Never invent corpus identifiers.**

## Step 1 — DEEPEN candidates (priority order)

A deepen topic goes *deeper than interview-prep depth* on something a volume
already covers. Cite `source_volume`; one topic per chapter cluster.

1. **`to_acquire` / `NEED TO ACQUIRE` markers** in any `reading_list.yml`
   (strongest — author-flagged gaps). `seed_sources` = the paper's DOI/arXiv;
   `claim_family_seeds` from its `topics:`.
2. **High-Bloom LOS clusters** — group whitelist-level LOS by `chapter_num`
   inside Advanced/ML/Practice `\part`s. One deepen topic per cluster;
   `source_los` = those IDs.
3. **`\section{}` titles** in those parts (e.g. "Double Machine Learning /
   Causal Forests / TMLE" → one DML-frontier topic).

**Gotcha:** one topic per chapter cluster, NEVER one per LOS — 2,623 LOS would
explode the backlog. **HARD RULE: deepen entries must cite `source_volume`.**

## Step 2 — ADJACENT candidates

An adjacent topic is related white-space the corpus does NOT cover. Omit
`source_volume`; set `track: cross`.

1. **Scaffold / placeholder volumes** — dirs whose `chapters/` hold few real LOS
   (e.g. `vol10_nlp`, `vol16_data_engineering`, `vol21_behavioral`). These are
   explicit reserved white-space; one topic each.
2. **Cross-track intersections** — domains that co-occur in
   `shared/company-tags.yml` `domains:` lists with no single bridging volume
   (e.g. causal inference × LLM evaluation).
3. **Prose asides** — `\section{Future…}` / "Limitations" / "Open problems"
   (lower yield; default P2).

**Gotcha:** adjacent topics have no parent volume — do not back-fill a spurious
`source_volume` to satisfy a deepen-shaped instinct.

## Step 3 — DEDUP against prior research (the re-run contract)

Build a normalized "already-covered" set, then drop matches with a logged reason:

1. This backlog's own entries with `status ∈ {researched, planned, dropped}`
   (and dedup `proposed` by `topic_id` in append mode).
2. `~/Claude/research_*/` directory slugs (strip `research_` prefix + trailing
   `_datasets`) AND each `bib_ledger.yml`'s top-level `topic:` field.
3. `~/Claude/research-kb/inbox/research_toolkit/*.jsonl` filename stems.

Match with token-overlap on normalized strings (reuse the
`validators._common.matches_canonical_fuzzy` spirit — min-length guarded to
avoid trivial collisions).

**HARD RULE: `/topic-discovery` is append-only.** Never rewrite or reorder
existing entries; never re-emit a `status: researched` topic.

## Step 4 — SCORE → priority + rationale (deterministic rubric)

Additive 0-6:

| Signal | Points |
|---|---|
| Strong signal: `to_acquire`-backed deepen OR scaffold-volume adjacent | +2 |
| Frontier density: ≥3 high-Bloom LOS in the cluster OR multi-track domain overlap | +1 |
| **Documented interest bias**: title/seeds touch AI-safety or causal terms (below) | +2 |
| Transferability: spans ≥2 tracks / multiple companies' domains | +1 |

Tier map: **≥5 → P0**, **3-4 → P1**, **≤2 → P2**.

Interest-bias term sets (the user's stated research interests):
- AI safety: `alignment, jailbreak, oversight, eval, red-team, interpretability,
  RLHF, reward model, deception`
- Causal: `causal, treatment effect, identification, DML, instrumental, DiD,
  synthetic control, uplift, counterfactual`

`rationale` names the top contributing signal(s) in one line.

## Honest signals

- An all-`deepen` (or all-`adjacent`) backlog at ≥8 entries is the signature of
  a skipped axis — the validator's `--strict` both-kinds check catches it.
- All-P0, or all-identical-priority, means scoring never ran — also caught.
- A backlog that re-lists a topic with an existing `~/Claude/research_<slug>/`
  dir means dedup (Step 3) was skipped.

The downstream `/research-plan` → `/research-gather` chain catches over-broad
topics (un-scopable taxonomy) and missing landmark papers; this protocol's job
is only to surface the *right candidates*, not to research them.

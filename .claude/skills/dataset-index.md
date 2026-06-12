---
name: dataset-index
description: Render a populated dataset_ledger.yml into a 5-bullet-per-entry agent-index folder. 5 bullets per dataset (Source / Access / Schema / Size+License / Tasks). Produces an AGENT-INDEX README with lookup recipes + glossary. Mirrors /agent-index but for datasets instead of papers.
allowed-tools: Read, Write, Edit, Bash
---

# /dataset-index — Synthesize dataset ledger as agent-ready indexed folder

## Usage

```
/dataset-index <ledger_path> [--output-dir <dir>] [--topic <slug>]
```

**Examples:**
```
/dataset-index ~/Claude/research-dossiers/research_<slug>/dataset_ledger.yml
/dataset-index ~/Claude/research-dossiers/research_anomaly/dataset_ledger.yml --output-dir ~/some_project/docs/research/anomaly_datasets/
```

**Default `--output-dir`**: `~/<consumer-project>/docs/research/<topic>_datasets/`
when invoked from a project root, else prompts.

## When to use

- After `/dataset-gather` produces a content-stable `dataset_ledger.yml`.
- Run **once** per ledger; re-run after material edits.
- Output is the consumer artifact — what a future agent reads when grounding
  reasoning in "what datasets exist for this topic."

**Upstream:** `/dataset-gather` produces `dataset_ledger.yml`.

**Downstream:**
- `/dossier-audit` verifies the synthesis (use focus areas like "license risks" or "access stability").
- `/url-freshness-check` validates URL liveness on the output.

## Workflow

### Phase 1: load reference (HARD REQUIREMENT)

Read `~/Claude/research_toolkit/references/dual_audience_design.md` BEFORE
generating any output. The 9 design principles for the AGENT-INDEX format
are mandatory.

Read `~/Claude/research_toolkit/references/citation_rules.md` for URL
canonical forms + status flags.

Read `~/Claude/research_toolkit/templates/dataset_5_bullet_entry.template.md`
for the canonical 5-bullet shape.

For strict-live v2 projects, read
`~/Claude/research_toolkit/references/strict_live_v2.md`. Preserve compact
evidence IDs per dataset block so every access/license/size/schema/task claim
can be traced to `evidence_ledger.yml`.

**Worked example:** see
`~/Claude/research_toolkit/tests/fixtures/medium_dataset_subset/agent_index/`
(populated after v1.6 dogfood). Mirror its file structure + per-file
letter-prefix anchor convention.

### Phase 2: read ledger

Read `<ledger_path>` (a `dataset_ledger.yml`). Extract entries — each entry
becomes one 5-bullet block.

### Phase 3: pick topic-file split

Datasets organize naturally by `source` category (huggingface, uci, etc.) OR
by `task_family` (time_series, classification, etc.). Pick the split that
produces 3-7 files, each with 3+ entries.

Recommended default: split by `source` category, with a fallback "other"
file for orphan source values. Each file uses per-file letter-prefix
anchors (`## A1.`, `## A2.` for file 01; `## B1.` for file 02; etc.).

Surface the proposed split for user approval before writing files.

### Phase 4: render 5-bullet entries

For each ledger entry, render as:

```markdown
- **<name>** — <source / org> (<year>).
  - **Source:** <primary_url>
  - **Access:** <access_method>; auth_required: <Y/N>
  - **Schema:** <N cols, key types; schema_url if present>
  - **Size+License:** <size>; <license shorthand>
  - **Tasks:** <prose about what this dataset is used for + benchmarks built on it>
  - **Status:** <Verified | Unverified | (uncertain X) Verified>
  - **Evidence:** <evidence IDs from dataset_ledger.evidence_ids>
```

**HARD RULES (carry up from skill body conventions):**

- **Name**: copy `dataset_ledger.name` verbatim. Do NOT abbreviate to a slug.
- **Source URL — NO domain substitution from memory** (v1.7 BURN_IN finding from v1.6 dogfood). Copy `dataset_ledger.primary_url` byte-for-byte. The ledger is the source of truth. The Stage 4 rendering subagent in v1.6 substituted `cs.cornell.edu` for `cs.ucr.edu` (Eamonn Keogh is at UC Riverside, not Cornell) because of memorized "researcher domain" associations. **Do NOT auto-correct domain/host names — even if your prior knowledge of the author's affiliation suggests a different domain.** Trust the ledger.
- **Access**: combine `access_method` + `auth_required`. Default `direct` +
  `auth_required: N` if both unknown — flag with `(uncertain access)`.
- **Schema**: short summary; link to `schema_url` if ledger has it. Do NOT
  invent column counts.
- **Size+License**: from `size` + `license` ledger fields. If license is
  `unknown` in the ledger, render verbatim ("license: unknown") — do NOT
  guess by inference from source category (e.g., "HF datasets are usually
  CC-BY-4.0" — that's a guess).
- **Tasks**: short prose. Cite known benchmark papers where the dataset is
  used; don't fabricate.
- **Status**: append `(uncertain X)` when a field is honest-unknown.
- **Evidence**: v2 outputs include evidence IDs from the ledger. If a dataset
  block contains claims from multiple sources, include all relevant IDs.

### Phase 5: write README + 00_overview

`README.md` (the AGENT-INDEX hub) must include:

- Top: `<!-- AGENT-INDEX: ... -->` HTML comment
- Front-loaded metadata (Purpose, Scope, Coverage, Last updated)
- Scope-boundary callout cross-referencing the parallel `<topic>_synthesis/`
  paper dossier IF it exists. Format:

  > For paper-synthesis on this topic, see
  > [`../<topic>_synthesis/`](../<topic>_synthesis/). The dataset dossier
  > here covers metadata + access methods; the synthesis covers methodology.

- File table (which file has which source category / task family)
- Lookup recipes (~15-25 dataset-shaped questions: "What's the canonical
  benchmark for X?", "Which dataset has CC-BY-4.0 + the most rows?")
- Glossary (dataset-specific terms: "datasheet", "license shorthand",
  "task_family enum values")
- Verification & limits (audit-trail placeholder)
- Attribution

`00_overview.md` (optional but recommended): topic intro + table-of-contents
+ source-category coverage stats.

### Phase 6: validate

Run all 3 validators:

```bash
python ~/Claude/research_toolkit/validators/agent_index.py <output_dir>
python ~/Claude/research_toolkit/validators/cross_stage.py <project_dir>
```

(`<project_dir>` is the parent containing `dataset_ledger.yml` + this
`agent_index/` output. cross_stage checks that all dataset entries in the
ledger are referenced in the agent_index, and vice versa.)

## Templates

- `Read ~/Claude/research_toolkit/templates/dataset_5_bullet_entry.template.md` — entry shape.
- `Read ~/Claude/research_toolkit/templates/agent_index_README.template.md` — README structure.

## References

- `Read ~/Claude/research_toolkit/references/dual_audience_design.md` — HARD REQUIREMENT.
- `Read ~/Claude/research_toolkit/references/citation_rules.md` — URL forms + status flags.

## Validation

```bash
python ~/Claude/research_toolkit/validators/agent_index.py <output_dir>
python ~/Claude/research_toolkit/validators/cross_stage.py <project_dir>
```

Both must exit 0.

## Output / handoff

**Produces:**
- `<output_dir>/README.md` — agent-index hub
- `<output_dir>/00_overview.md` — optional overview
- `<output_dir>/0K_<source-category>.md` — synthesis files (one per source category, typically)

**Consumed by:**
- `/dossier-audit <output_dir> --focus "license risks + access stability"` — Stage 5 audit
- `/url-freshness-check <output_dir>` — URL liveness check
- Future LLM agents grounding reasoning in this dataset dossier
- Human readers as a reference document

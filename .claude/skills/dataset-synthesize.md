---
name: dataset-synthesize
description: Generate synthetic datasets via Anthropic Claude with multi-template prompt caching and a cost-bounded escape hatch. Use when constructing training corpora, eval sets, or red-team carrier sets across multiple template patterns.
allowed-tools: Read, Write, Edit, Bash
---

# dataset-synthesize

## Usage

```bash
python3 ~/Claude/research_toolkit/scripts/dataset_synthesize.py \
    --recipe <path-to-recipe.yaml> \
    --output <output-dir>/ \
    --bail-at-cost 80.00
```

`--validate-only` parses + validates the recipe without calling the
API. Errors written to stderr; exit code 1 on any validation error.

## When to use

- Building a synthetic training corpus across 5-20 template families.
- Generating evaluation sets where each template covers a distinct
  pattern + per-template count control is required.
- Red-team carrier construction (per ADR-041-style ETHICS norm: only
  documented attack vectors; the recipe author is responsible for
  content discipline).
- NOT for: single-template free-form generation (use the Anthropic
  API directly); cross-provider work (prompt caching is
  Anthropic-specific); real-time / streaming use cases (this skill
  is batch-oriented).

## Workflow

### Phase 1 — Validate the recipe

Read `~/Claude/research_toolkit/templates/dataset_synthesis_recipe.template.yml`
for the schema. Construct or edit a recipe YAML; run
`--validate-only` first to confirm schema before incurring API spend:

```bash
python3 ~/Claude/research_toolkit/scripts/dataset_synthesize.py \
    --recipe my_recipe.yaml --output /tmp/_validate --validate-only
```

### Phase 2 — Set up API access

`ANTHROPIC_API_KEY` env var must be set. The skill requires the
`anthropic` Python SDK (optional dep: `pip install
'research_toolkit[synthesis]'`); `--validate-only` works without it.

### Phase 3 — Run synthesis with cost cap

```bash
python3 ~/Claude/research_toolkit/scripts/dataset_synthesize.py \
    --recipe my_recipe.yaml \
    --output data/synthetic/run-1/ \
    --bail-at-cost 80.00
```

`--bail-at-cost` is REACTIVE (post-call): the first sample always
runs; subsequent samples halt once total cost crosses the threshold.
To cap pre-call, tighten `max_tokens` or pick a cheaper model in the
recipe.

### Phase 4 — Resume after interrupt or API failure

`samples.jsonl` is append-only. On re-run, the skill reads existing
rows + per-template counts + generates only the remaining shortfall.
Safe to interrupt + resume.

If exit code 3 (API error): inspect `manifest.json`'s `api_error`
field, address the upstream issue (rate limit, auth, etc.), re-run
to continue from the JSONL state.

## Templates

- [`dataset_synthesis_recipe.template.yml`](~/Claude/research_toolkit/templates/dataset_synthesis_recipe.template.yml)
  — recipe schema + field documentation.

## References

- Anthropic prompt caching docs:
  https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
- [`scripts/dataset_synthesize.py`](~/Claude/research_toolkit/scripts/dataset_synthesize.py)
  — implementation reference.
- [`docs/conventions/skill-spec.md`](~/Claude/research_toolkit/docs/conventions/skill-spec.md)
  — skill format conventions this file follows.

## Validation

`--validate-only` exits 0 on a valid recipe + 1 on errors.
For a smoke test against the canonical template:

```bash
python3 ~/Claude/research_toolkit/scripts/dataset_synthesize.py \
    --recipe ~/Claude/research_toolkit/templates/dataset_synthesis_recipe.template.yml \
    --output /tmp/_smoke --validate-only
```

Exit codes:

- `0` — all templates reached `target_count`
- `1` — recipe validation error or missing recipe / API key
- `2` — bail-at-cost tripped; partial manifest written
- `3` — API call raised an exception; partial manifest written with
  `api_error` field set; samples up to the failing call are
  preserved in JSONL (re-run resumes from there)

## Output / handoff

- Writes: `<output>/samples.jsonl` (one row per sample;
  `{id, template_id, content, model, metadata, usage, cost_usd, timestamp}`)
- Writes: `<output>/manifest.json` (aggregate counts + total cost +
  cache hit rate + per-template breakdown + `orphan_template_ids` +
  `api_error` if applicable)
- Consumed by: downstream tooling that ingests JSONL (training data
  loaders, eval harnesses, dataset publishers). The manifest's
  sha256 fields anchor reproducibility.

Closes brandon-behring/research_toolkit#1.

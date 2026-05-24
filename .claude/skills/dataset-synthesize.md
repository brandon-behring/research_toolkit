---
name: dataset-synthesize
description: Generate synthetic samples via Anthropic Claude with prompt caching. Takes a recipe YAML (multi-template, each with cached system + few-shot + per-call user prompt + target count) and writes JSONL output + a manifest with per-template counts + cost + cache-hit metrics. Cost-bounded via --bail-at-cost (writes partial manifest + exits 2 on threshold trip). Idempotent re-runs resume from existing JSONL.
allowed-tools: Read, Write, Edit, Bash
---

# dataset-synthesize

Generates synthetic datasets via Anthropic Claude with prompt caching as
the load-bearing primitive. Use when you need to construct a synthetic
training corpus, evaluation set, or red-team carrier set across multiple
templated patterns where each template's system prompt + few-shot
examples should be cached once and reused across many generations.

## When to use

- Building a synthetic training corpus across 5-20 template families.
- Generating evaluation sets where each template covers a distinct
  pattern + you want per-template count control.
- Red-team carrier construction (per ADR-041-style ETHICS norm: only
  use documented attack vectors; this skill is a tool, not a policy
  layer — the recipe author is responsible for content discipline).

## When NOT to use

- Single-template free-form generation — use the Anthropic API directly.
- Cross-provider work (OpenAI/Gemini) — prompt caching is
  Anthropic-specific; cross-provider abstraction defeats the point.
- Real-time / streaming use cases — this skill is batch-oriented.

## Inputs

- **Recipe YAML** at `--recipe <path>`. See
  `templates/dataset_synthesis_recipe.template.yml` for the schema.
- **Output directory** at `--output <dir>` — created if absent.
- **Bail-at-cost threshold** at `--bail-at-cost <usd>` (default 80.00).
  REACTIVE (post-call): the first sample always runs; subsequent
  samples halt once the running total crosses the threshold. For
  pre-call caps, tighten max_tokens / pick a cheaper model in the
  recipe.

## Outputs

`<output>/samples.jsonl` — one row per sample::

    {"id": "sample_<uuid12>", "template_id": "...", "content": "...",
     "model": "...", "metadata": {...}, "usage": {...},
     "cost_usd": 0.00X, "timestamp": "..."}

`<output>/manifest.json` — aggregate counts + cost + cache hit metrics
+ per-template breakdown.

## Cost bounding

`--bail-at-cost` is a REACTIVE (post-call) $-cap, NOT proactive. The
first sample always runs to completion regardless of expected cost.
After each call, the running total is checked; if it crosses the
threshold, the loop halts, the partial manifest is written (with
`bail_fired: true`), and the skill exits with code 2. The next re-run
resumes from the existing JSONL — samples already produced are not
regenerated.

**Implication**: with an expensive model + large max_tokens, the
first call alone can exceed `--bail-at-cost`. To cap before the
first call, reduce `max_tokens` or pick a cheaper model in the
recipe. Pre-call cost estimation is a future enhancement.

## Exit codes

- `0` — all templates reached `target_count`
- `1` — recipe validation error or missing recipe / API key
- `2` — bail-at-cost tripped; partial manifest written
- `3` — API call raised an exception; partial manifest written with
  `api_error` field set; samples up to the failing call are preserved
  in JSONL (re-run resumes from there)

## Recipe schema

```yaml
model: claude-sonnet-4-7        # required; one of PRICING_PER_MTOK keys
defaults:                       # optional
  temperature: 0.9
  max_tokens: 800
  batch_size: 1                 # reserved for future multi-sample-per-call
templates:                      # required, non-empty
  - id: email-imperative        # unique within recipe
    system: |                   # cacheable system prompt
                                # (Anthropic caches by content hash;
                                # no user-supplied cache key)
      You are generating ...
    few_shot:                   # optional; alternating user/assistant
      - role: user
        content: "Example input"
      - role: assistant
        content: "Example output"
    user_prompt: |              # per-call prompt (NOT cached)
      Generate one sample.
    target_count: 100           # required; positive integer
    metadata:                   # optional; carried into each output row
      carrier: email
      style: imperative
```

## Validation

`--validate-only` parses + validates the recipe without calling the
API. Errors written to stderr; exit code 1 on any validation error.

## Idempotency

`samples.jsonl` is append-only. On re-run, the skill reads existing
rows + per-template counts + only generates the remaining shortfall
toward each template's `target_count`. Safe to interrupt + resume.

## Anthropic SDK requirement

This skill requires the `anthropic` Python SDK (optional dep:
`pip install 'research_toolkit[synthesis]'`) plus the
`ANTHROPIC_API_KEY` env var. `--validate-only` works without the SDK
installed.

## Closes

brandon-behring/research_toolkit#1.

## Cross-references

- Anthropic prompt caching docs:
  https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
- `templates/dataset_synthesis_recipe.template.yml` — full schema +
  field documentation
- `scripts/dataset_synthesize.py` — implementation
- `tests/test_dataset_synthesize.py` — unit tests (no live API calls)

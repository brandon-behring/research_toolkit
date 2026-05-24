#!/usr/bin/env python3
"""Prompt-cached synthetic dataset generation via Anthropic Claude.

Generates synthetic samples across multiple templates with Anthropic
prompt caching so the system prompt + few-shot examples are billed once
per template per cache TTL window. Outputs JSONL (one row per sample)
plus a manifest with per-template counts + cost + cache-hit metrics.

Cost-bounded via ``--bail-at-cost`` — on threshold trip, writes a partial
manifest with ``bail_fired: true`` and exits 2. Idempotent re-runs resume
from existing JSONL rows.

Closes brandon-behring/research_toolkit#1.

Usage:

    python3 scripts/dataset_synthesize.py \\
        --recipe configs/synthesis/indirect-injection-v2.yaml \\
        --output data/synthetic/indirect-v2/ \\
        --bail-at-cost 80.00

Output layout::

    data/synthetic/indirect-v2/
      samples.jsonl        # one synthetic sample per line
      manifest.json        # counts + cost + sha256s + per-template metrics

Recipe schema (see ``templates/dataset_synthesis_recipe.template.yml``)::

    model: claude-sonnet-4-7
    defaults:
      temperature: 0.9
      max_tokens: 800
      batch_size: 1
    templates:
      - id: email-imperative
        cache_key: email-imperative-v1
        system: |
          You are generating realistic indirect prompt injection samples...
        few_shot:
          - role: user
            content: "Sample input"
          - role: assistant
            content: "Sample output"
        user_prompt: |
          Generate one sample.
        target_count: 100
        metadata:
          carrier: email
          style: imperative

The skill is intentionally provider-specific (Anthropic-only) because
prompt caching is the load-bearing primitive — cross-provider abstraction
would defeat the point. To run, set ``ANTHROPIC_API_KEY`` env var.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# Anthropic SDK is an optional dependency under [synthesis] extra. Lazy-import
# so callers running --dry-run or --validate-recipe without the SDK installed
# don't fail.
_ANTHROPIC_SDK_AVAILABLE = False
_ANTHROPIC_IMPORT_ERROR: str | None = None
try:  # pragma: no cover - environment-dependent
    import anthropic  # type: ignore[import-not-found]

    _ANTHROPIC_SDK_AVAILABLE = True
except ImportError as exc:  # pragma: no cover
    _ANTHROPIC_IMPORT_ERROR = str(exc)


# Per-1M-token costs in USD for Claude models supported by this skill.
# Caching reads are 10% of input price; cache writes are 125% of input price
# (per Anthropic pricing as of 2026-05).
PRICING_PER_MTOK: dict[str, dict[str, float]] = {
    "claude-sonnet-4-7": {"input": 3.0, "output": 15.0},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
    "claude-opus-4-7": {"input": 15.0, "output": 75.0},
    "claude-opus-4-6": {"input": 15.0, "output": 75.0},
    "claude-haiku-4-5": {"input": 1.0, "output": 5.0},
}
CACHE_READ_DISCOUNT = 0.10
CACHE_WRITE_PREMIUM = 1.25


@dataclass
class Template:
    id: str
    system: str
    user_prompt: str
    target_count: int
    few_shot: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Recipe:
    model: str
    templates: list[Template]
    temperature: float = 0.9
    max_tokens: int = 800
    batch_size: int = 1
    sha256: str = ""


def validate_recipe(data: dict[str, Any]) -> tuple[Recipe | None, list[str]]:
    """Parse + validate a recipe YAML mapping. Returns (recipe, errors)."""
    errors: list[str] = []
    if not isinstance(data, dict):
        return None, ["top-level recipe must be a mapping"]

    model = data.get("model")
    if not isinstance(model, str) or not model.strip():
        errors.append("'model' must be a non-empty string")

    if isinstance(model, str) and model not in PRICING_PER_MTOK:
        errors.append(
            f"'model' = {model!r} not in pricing table. Known: "
            f"{sorted(PRICING_PER_MTOK)}"
        )

    defaults = data.get("defaults", {}) or {}
    if not isinstance(defaults, dict):
        errors.append("'defaults' must be a mapping if present")
        defaults = {}

    temperature = defaults.get("temperature", 0.9)
    if not isinstance(temperature, (int, float)) or not 0 <= float(temperature) <= 2:
        errors.append("'defaults.temperature' must be a number in [0, 2]")
    max_tokens = defaults.get("max_tokens", 800)
    if not isinstance(max_tokens, int) or max_tokens <= 0:
        errors.append("'defaults.max_tokens' must be a positive integer")
    batch_size = defaults.get("batch_size", 1)
    if not isinstance(batch_size, int) or batch_size <= 0:
        errors.append("'defaults.batch_size' must be a positive integer")

    templates_raw = data.get("templates")
    if not isinstance(templates_raw, list) or not templates_raw:
        errors.append("'templates' must be a non-empty list")
        templates_raw = []

    templates: list[Template] = []
    seen_ids: set[str] = set()
    for idx, t in enumerate(templates_raw):
        loc = f"templates[{idx}]"
        if not isinstance(t, dict):
            errors.append(f"{loc}: must be a mapping")
            continue
        tid = t.get("id")
        if not isinstance(tid, str) or not tid.strip():
            errors.append(f"{loc}.id: must be a non-empty string")
            tid = f"unknown_{idx}"
        if tid in seen_ids:
            errors.append(f"{loc}.id: duplicate id {tid!r}")
        seen_ids.add(tid)

        system = t.get("system")
        if not isinstance(system, str) or not system.strip():
            errors.append(f"{loc}.system: must be a non-empty string")
            system = ""

        user_prompt = t.get("user_prompt")
        if not isinstance(user_prompt, str) or not user_prompt.strip():
            errors.append(f"{loc}.user_prompt: must be a non-empty string")
            user_prompt = ""

        target_count = t.get("target_count")
        if not isinstance(target_count, int) or target_count <= 0:
            errors.append(f"{loc}.target_count: must be a positive integer")
            target_count = 0

        few_shot_raw = t.get("few_shot", []) or []
        if not isinstance(few_shot_raw, list):
            errors.append(f"{loc}.few_shot: must be a list if present")
            few_shot_raw = []
        few_shot: list[dict[str, str]] = []
        for j, fs in enumerate(few_shot_raw):
            if not isinstance(fs, dict):
                errors.append(f"{loc}.few_shot[{j}]: must be a mapping")
                continue
            role = fs.get("role")
            content = fs.get("content")
            if role not in ("user", "assistant"):
                errors.append(
                    f"{loc}.few_shot[{j}].role: must be 'user' or 'assistant'"
                )
            if not isinstance(content, str) or not content.strip():
                errors.append(f"{loc}.few_shot[{j}].content: must be a non-empty string")
            few_shot.append({"role": role or "user", "content": content or ""})

        metadata = t.get("metadata", {}) or {}
        if not isinstance(metadata, dict):
            errors.append(f"{loc}.metadata: must be a mapping if present")
            metadata = {}

        templates.append(
            Template(
                id=tid,
                system=system,
                user_prompt=user_prompt,
                target_count=target_count,
                few_shot=few_shot,
                metadata=metadata,
            )
        )

    if errors:
        return None, errors

    recipe = Recipe(
        model=str(model),
        templates=templates,
        temperature=float(temperature),
        max_tokens=int(max_tokens),
        batch_size=int(batch_size),
    )
    return recipe, []


def recipe_sha256(recipe_path: Path) -> str:
    return hashlib.sha256(recipe_path.read_bytes()).hexdigest()


def compute_call_cost(
    model: str,
    *,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int = 0,
    cache_creation_tokens: int = 0,
) -> float:
    """Compute USD cost for a single API call. Per-token math against the
    PRICING_PER_MTOK table; cache reads at 10%, cache writes at 125%."""
    pricing = PRICING_PER_MTOK.get(model)
    if pricing is None:
        return 0.0
    input_rate = pricing["input"] / 1_000_000
    output_rate = pricing["output"] / 1_000_000
    cost = (
        input_tokens * input_rate
        + output_tokens * output_rate
        + cache_read_tokens * input_rate * CACHE_READ_DISCOUNT
        + cache_creation_tokens * input_rate * CACHE_WRITE_PREMIUM
    )
    return round(cost, 6)


def build_messages(template: Template) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build (system_blocks, messages) with cache_control set on system + few_shot."""
    # System prompt as a cacheable block (Anthropic SDK accepts list[block] for
    # system). The cache_control marker tells Anthropic to cache up to + including
    # this block.
    system_blocks = [
        {
            "type": "text",
            "text": template.system,
            "cache_control": {"type": "ephemeral"},
        }
    ]
    messages: list[dict[str, Any]] = []
    # Few-shot pairs as alternating user/assistant. The LAST few-shot message gets
    # a cache_control marker so all few-shot examples are included in the cache.
    for idx, fs in enumerate(template.few_shot):
        is_last_few_shot = idx == len(template.few_shot) - 1
        content_block: dict[str, Any] = {"type": "text", "text": fs["content"]}
        if is_last_few_shot:
            content_block["cache_control"] = {"type": "ephemeral"}
        messages.append({"role": fs["role"], "content": [content_block]})
    # Final user message with the actual generation prompt — NOT cached.
    messages.append(
        {"role": "user", "content": [{"type": "text", "text": template.user_prompt}]}
    )
    return system_blocks, messages


def _extract_usage(response: Any) -> dict[str, int]:
    """Extract token-usage stats from an Anthropic Message response.

    Defensive: response.usage may have different shapes depending on SDK
    version. We pull input_tokens, output_tokens, cache_read_input_tokens,
    cache_creation_input_tokens with safe fallbacks to 0.
    """
    usage = getattr(response, "usage", None)
    if usage is None:
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_read_tokens": 0,
            "cache_creation_tokens": 0,
        }

    def _g(name: str) -> int:
        return int(getattr(usage, name, 0) or 0)

    return {
        "input_tokens": _g("input_tokens"),
        "output_tokens": _g("output_tokens"),
        "cache_read_tokens": _g("cache_read_input_tokens"),
        "cache_creation_tokens": _g("cache_creation_input_tokens"),
    }


def _extract_text(response: Any) -> str:
    """Extract concatenated text from an Anthropic Message response.content."""
    parts: list[str] = []
    for block in getattr(response, "content", []) or []:
        if getattr(block, "type", None) == "text":
            parts.append(getattr(block, "text", "") or "")
    return "".join(parts)


def load_existing_samples(jsonl_path: Path) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Resume support: read prior samples + per-template counts.

    Returns (rows, counts_by_template_id). Skips malformed lines.
    """
    rows: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    if not jsonl_path.exists():
        return rows, counts
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        rows.append(row)
        tid = row.get("template_id")
        if isinstance(tid, str):
            counts[tid] = counts.get(tid, 0) + 1
    return rows, counts


def synthesize(
    *,
    recipe: Recipe,
    output_dir: Path,
    bail_at_cost: float,
    seed: int | None = None,
    client: Any | None = None,
) -> tuple[int, dict[str, Any]]:
    """Run the synthesis loop. Returns (exit_code, manifest).

    Exit codes:
      0 — all templates reached target_count
      2 — bail-at-cost tripped; partial manifest written
      3 — API call raised an exception; partial manifest written with
          ``api_error`` field; samples up to the failing call are
          preserved in JSONL (re-run resumes from there)

    ``client`` is the Anthropic SDK client (or a test double with the same
    interface). If None, instantiated via ``anthropic.Anthropic()``.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = output_dir / "samples.jsonl"
    manifest_path = output_dir / "manifest.json"

    existing_rows, prior_counts = load_existing_samples(jsonl_path)
    per_template_actual = dict(prior_counts)
    per_template_cost = {t.id: 0.0 for t in recipe.templates}
    per_template_input = {t.id: 0 for t in recipe.templates}
    per_template_output = {t.id: 0 for t in recipe.templates}
    per_template_cache_read = {t.id: 0 for t in recipe.templates}
    per_template_cache_write = {t.id: 0 for t in recipe.templates}

    total_cost = 0.0
    bail_fired = False
    api_error: str | None = None
    started_at = datetime.now(timezone.utc).isoformat()

    # Lazy-init Anthropic client only if we need to call the API.
    work_remaining = any(
        per_template_actual.get(t.id, 0) < t.target_count for t in recipe.templates
    )
    if work_remaining and client is None:
        if not _ANTHROPIC_SDK_AVAILABLE:
            raise RuntimeError(
                f"anthropic SDK not installed: {_ANTHROPIC_IMPORT_ERROR}. "
                f"Install with: pip install 'research_toolkit[synthesis]'"
            )
        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY env var

    with jsonl_path.open("a", encoding="utf-8") as jsonl_f:
        for template in recipe.templates:
            already = per_template_actual.get(template.id, 0)
            to_generate = template.target_count - already
            if to_generate <= 0:
                continue
            system_blocks, messages = build_messages(template)
            for _ in range(to_generate):
                if total_cost >= bail_at_cost:
                    bail_fired = True
                    break
                # API failures (network, rate limits, auth errors, etc.) are
                # caught + persisted in the manifest as `api_error` so the
                # partial state is recoverable. Re-runs resume from existing
                # JSONL rows.
                try:
                    response = client.messages.create(
                        model=recipe.model,
                        system=system_blocks,
                        messages=messages,
                        max_tokens=recipe.max_tokens,
                        temperature=recipe.temperature,
                    )
                except Exception as exc:
                    api_error = f"{type(exc).__name__}: {exc}"
                    print(
                        f"dataset-synthesize: API error during template "
                        f"{template.id!r}: {api_error}",
                        file=sys.stderr,
                    )
                    break
                text = _extract_text(response)
                usage = _extract_usage(response)
                cost = compute_call_cost(recipe.model, **usage)
                row = {
                    "id": f"sample_{uuid.uuid4().hex[:12]}",
                    "template_id": template.id,
                    "content": text,
                    "model": recipe.model,
                    "metadata": template.metadata,
                    "usage": usage,
                    "cost_usd": cost,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                jsonl_f.write(json.dumps(row, ensure_ascii=False) + "\n")
                jsonl_f.flush()
                per_template_actual[template.id] = per_template_actual.get(template.id, 0) + 1
                per_template_cost[template.id] += cost
                per_template_input[template.id] += usage["input_tokens"]
                per_template_output[template.id] += usage["output_tokens"]
                per_template_cache_read[template.id] += usage["cache_read_tokens"]
                per_template_cache_write[template.id] += usage["cache_creation_tokens"]
                total_cost += cost
            if bail_fired or api_error is not None:
                break

    ended_at = datetime.now(timezone.utc).isoformat()

    # Compute cache hit rate (across all templates).
    total_cache_read = sum(per_template_cache_read.values())
    total_cache_write = sum(per_template_cache_write.values())
    total_input_excl_cache = sum(per_template_input.values())
    denom = total_cache_read + total_cache_write + total_input_excl_cache
    cache_hit_rate = (total_cache_read / denom) if denom > 0 else 0.0

    jsonl_sha = (
        hashlib.sha256(jsonl_path.read_bytes()).hexdigest()
        if jsonl_path.exists()
        else None
    )

    manifest = {
        "version": "1",
        "model": recipe.model,
        "recipe_sha256": recipe.sha256,
        "templates": {
            t.id: {
                "target": t.target_count,
                "actual": per_template_actual.get(t.id, 0),
                "cost_usd": round(per_template_cost[t.id], 4),
                "input_tokens": per_template_input[t.id],
                "output_tokens": per_template_output[t.id],
                "cache_read_tokens": per_template_cache_read[t.id],
                "cache_creation_tokens": per_template_cache_write[t.id],
            }
            for t in recipe.templates
        },
        "total_samples": sum(per_template_actual.values()),
        "total_cost_usd": round(total_cost, 4),
        "cache_hit_rate": round(cache_hit_rate, 4),
        "bail_at_cost": bail_at_cost,
        "bail_fired": bail_fired,
        "api_error": api_error,
        "seed": seed,
        "started_at": started_at,
        "ended_at": ended_at,
        "output_jsonl_sha256": jsonl_sha,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    if api_error is not None:
        exit_code = 3
    elif bail_fired:
        exit_code = 2
    else:
        exit_code = 0
    return exit_code, manifest


def _cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="dataset-synthesize",
        description=(
            "Generate synthetic samples via Anthropic with prompt caching. "
            "See `--help` for recipe schema. Closes brandon-behring/"
            "research_toolkit#1."
        ),
    )
    parser.add_argument(
        "--recipe", required=True, type=Path, help="Path to recipe YAML."
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output directory for samples.jsonl + manifest.json.",
    )
    parser.add_argument(
        "--bail-at-cost",
        type=float,
        default=80.0,
        help="Hard $-cap; on threshold trip, write partial manifest + exit 2. "
        "Default: 80.00.",
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="Optional seed (recorded in manifest)."
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Parse + validate the recipe; do not call the API. Exits 0 on "
        "valid recipe, 1 on errors.",
    )
    args = parser.parse_args(argv)

    if not args.recipe.exists():
        print(f"error: recipe file not found: {args.recipe}", file=sys.stderr)
        return 1
    raw = yaml.safe_load(args.recipe.read_text(encoding="utf-8"))
    recipe, errors = validate_recipe(raw)
    if errors:
        for err in errors:
            print(f"recipe error: {err}", file=sys.stderr)
        return 1
    assert recipe is not None
    recipe.sha256 = recipe_sha256(args.recipe)

    print(
        f"recipe: {args.recipe.name} (sha256: {recipe.sha256[:12]}...)\n"
        f"model: {recipe.model}\n"
        f"templates: {len(recipe.templates)} "
        f"(targets: {[t.target_count for t in recipe.templates]})",
        file=sys.stderr,
    )

    if args.validate_only:
        print("validate-only: recipe OK", file=sys.stderr)
        return 0

    if not os.environ.get("ANTHROPIC_API_KEY") and _ANTHROPIC_SDK_AVAILABLE:
        print(
            "error: ANTHROPIC_API_KEY env var not set",
            file=sys.stderr,
        )
        return 1

    exit_code, manifest = synthesize(
        recipe=recipe,
        output_dir=args.output,
        bail_at_cost=args.bail_at_cost,
        seed=args.seed,
    )

    print(
        f"manifest: {args.output / 'manifest.json'}\n"
        f"total samples: {manifest['total_samples']}\n"
        f"total cost: ${manifest['total_cost_usd']:.4f}\n"
        f"cache hit rate: {manifest['cache_hit_rate']:.2%}\n"
        f"bail fired: {manifest['bail_fired']}",
        file=sys.stderr,
    )
    return exit_code


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))

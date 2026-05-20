#!/usr/bin/env python3
"""Build a strict-live v2 dashboard.md for a project.

Reads bib_ledger.yml + dataset_ledger.yml + evidence_ledger.yml +
cache_manifest.yml + claim_graph.jsonl and emits a mechanical trust dashboard:
stale blockers, evidence coverage, cache completeness, conflicts, weak claims,
and a per-tier action queue.

Overwrites the target by default; --no-overwrite refuses if the target exists.
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path
import sys
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators.jsonl_common import load_jsonl
from validators.v2_common import (
    is_v3_mapping,
    load_yaml_mapping,
    parse_iso_date,
    stale_error_for_entry,
)


TIER_ORDER = ("volatile", "active", "stable", "historical")

# Words that should render in upper case rather than title case. Add new
# acronyms here as they appear in research topics.
ACRONYMS = {
    "ai", "ml", "dl", "nn", "llm", "lm", "nlp", "cv", "rl", "rlhf", "rlaif",
    "api", "sdk", "sql", "html", "json", "yaml", "csv", "pdf",
    "ui", "ux", "cli", "gui", "cpu", "gpu", "tpu",
    "us", "eu", "uk", "uae", "iso", "ieee", "acm",
    "nist", "owasp", "mitre", "fda", "epa",
    "gpt", "bert", "clip", "vit",
    "pi",  # prompt injection — surfaced by v2.0 Phase 4 dogfood
}


def _title_case(slug: str) -> str:
    parts = slug.replace("_", " ").replace("-", " ").split()
    rendered: list[str] = []
    for part in parts:
        if part.lower() in ACRONYMS:
            rendered.append(part.upper())
        else:
            rendered.append(part.capitalize())
    return " ".join(rendered)


def _pluralize_entity_type(entity_type: str) -> str:
    """Render an entity_type into the noun phrase used in Action Queue lines."""
    overrides = {
        "paper": "papers",
        "dataset": "datasets",
        "benchmark": "benchmark pages",
        "model": "models",
        "repo": "repositories",
        "vendor": "vendor pages",
        "standard": "standards",
        "policy": "policy documents",
        "author": "author pages",
        "org": "organizations",
        "concept": "concept pages",
    }
    return overrides.get(entity_type, "entries")


def _load_optional(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data, errors = load_yaml_mapping(path)
    if errors:
        raise SystemExit(f"{path.name}: {'; '.join(errors)}")
    return data or {}


def _stale_on(entry: dict[str, Any]) -> date | None:
    stale_after = entry.get("stale_after_days")
    if not isinstance(stale_after, int) or stale_after <= 0:
        return None
    anchor_value = entry.get("verified_at") or entry.get("retrieved_at")
    anchor, _ = parse_iso_date(anchor_value, "stale_on")
    if anchor is None:
        return None
    return anchor + timedelta(days=stale_after)


def build(project_dir: Path, today: date) -> str:
    evidence_data = _load_optional(project_dir / "evidence_ledger.yml")
    if not evidence_data:
        raise SystemExit(f"evidence_ledger.yml missing in {project_dir}")

    topic = evidence_data.get("topic", "research")
    bib_entries = _load_optional(project_dir / "bib_ledger.yml").get("entries") or []
    dataset_entries = _load_optional(project_dir / "dataset_ledger.yml").get("entries") or []
    cache_entries = _load_optional(project_dir / "cache_manifest.yml").get("entries") or []
    evidence_entries = evidence_data.get("entries") or []

    claim_records: list[dict[str, Any]] = []
    cg_path = project_dir / "claim_graph.jsonl"
    if cg_path.exists():
        records, _ = load_jsonl(cg_path)
        claim_records = [
            r for r in records if isinstance(r, dict) and r.get("record_type") == "claim"
        ]

    stale_blockers = 0
    # Per-tier list of (stale_on_date, entity_type) tuples so the Action Queue
    # can specialize the noun phrase when all entries in a tier share an
    # entity_type.
    by_tier_stale: dict[str, list[tuple[date, str]]] = {}
    for idx, entry in enumerate(list(bib_entries) + list(dataset_entries)):
        if not isinstance(entry, dict):
            continue
        loc = f"entries[{idx}]"
        if stale_error_for_entry(entry, loc=loc, today=today) is not None:
            stale_blockers += 1
        tier = entry.get("freshness_tier")
        stale_on = _stale_on(entry)
        if isinstance(tier, str) and stale_on is not None:
            entity_type = entry.get("claim_family") or entry.get("source") or ""
            by_tier_stale.setdefault(tier, []).append((stale_on, str(entity_type)))

    evidence_id_set = {
        e.get("evidence_id") for e in evidence_entries
        if isinstance(e, dict) and isinstance(e.get("evidence_id"), str)
    }
    total_claims = len(claim_records)
    covered_claims = 0
    for cr in claim_records:
        ev_ids = cr.get("evidence_ids")
        if (
            isinstance(ev_ids, list)
            and ev_ids
            and all(e in evidence_id_set for e in ev_ids)
        ):
            covered_claims += 1

    referenced_cache_ids: set[str] = set()
    for e in evidence_entries:
        if not isinstance(e, dict):
            continue
        for c in e.get("cache_ids") or []:
            if isinstance(c, str):
                referenced_cache_ids.add(c)
    manifest_cache_ids = {
        c.get("cache_id") for c in cache_entries
        if isinstance(c, dict) and isinstance(c.get("cache_id"), str)
    }
    cached = len(referenced_cache_ids & manifest_cache_ids)
    total_referenced = len(referenced_cache_ids)

    conflicts = sum(
        1 for cr in claim_records if cr.get("claim_type") == "contradiction"
    )
    weak_claims = 0
    for cr in claim_records:
        conf = cr.get("confidence")
        if isinstance(conf, dict):
            score = conf.get("score")
            if isinstance(score, (int, float)) and score < 0.8:
                weak_claims += 1

    action_lines: list[str] = []
    for tier in TIER_ORDER:
        stale_items = sorted(by_tier_stale.get(tier, []), key=lambda x: x[0])
        if not stale_items:
            continue
        earliest_date = stale_items[0][0]
        entity_types = {et for _, et in stale_items if et}
        if len(entity_types) == 1:
            noun = _pluralize_entity_type(next(iter(entity_types)))
        else:
            noun = "entries"
        action_lines.append(f"- Refresh {tier} {noun} by {earliest_date.isoformat()}.")
    if not action_lines:
        action_lines.append("- (no action needed)")

    # v3-only: Claim Health (FACT framework) metrics
    claim_health_lines: list[str] = []
    if is_v3_mapping(evidence_data):
        total_links = 0
        verbatim_match_count = 0
        strong_count = 0
        partial_count = 0
        weak_count = 0
        strong_methods = {"verbatim_match", "user_asserted"}
        partial_methods = {"paraphrase", "manual_override"}
        weak_methods = {"llm_inferred", "propagated_from_child"}
        # v2.2: per-claim corroboration + role-strength tracking
        claim_source_urls: dict[str, set[str]] = {}
        claim_strengths: dict[str, set[str]] = {}
        for entry in evidence_entries:
            if not isinstance(entry, dict):
                continue
            entry_url = entry.get("source_url")
            for support in (entry.get("supports") or []):
                if not isinstance(support, dict):
                    continue
                total_links += 1
                method = support.get("extraction_method")
                if method == "verbatim_match":
                    verbatim_match_count += 1
                if method in strong_methods:
                    strong_count += 1
                elif method in partial_methods:
                    partial_count += 1
                elif method in weak_methods:
                    weak_count += 1
                claim_id = support.get("claim_id")
                if isinstance(claim_id, str):
                    if isinstance(entry_url, str):
                        claim_source_urls.setdefault(claim_id, set()).add(entry_url)
                    strength = support.get("evidence_role_strength")
                    if isinstance(strength, str):
                        claim_strengths.setdefault(claim_id, set()).add(strength)
        if total_links:
            vm_pct = round(100 * verbatim_match_count / total_links)
            strong_pct = round(100 * strong_count / total_links)
            claim_health_lines = [
                "",
                "## Claim Health (FACT framework)",
                "",
                f"- total support links: {total_links}",
                f"- verbatim-anchored: {verbatim_match_count}/{total_links} ({vm_pct}%)",
                f"- strongly grounded: {strong_count}/{total_links} ({strong_pct}%)",
                f"- partially grounded: {partial_count}/{total_links}",
                f"- weakly grounded (inferred/propagated): {weak_count}/{total_links}",
            ]
            # v2.2: corroboration + atom support strength metrics. Only surface
            # when there's at least one claim with binding data; otherwise the
            # ratios are misleading.
            if claim_source_urls:
                corroborated = sum(
                    1 for urls in claim_source_urls.values() if len(urls) >= 2
                )
                total_claims_for_corr = len(claim_source_urls)
                corr_pct = round(100 * corroborated / total_claims_for_corr)
                claim_health_lines.append(
                    f"- corroborated (≥2 independent sources): "
                    f"{corroborated}/{total_claims_for_corr} ({corr_pct}%)"
                )
            if claim_strengths:
                full_only = sum(
                    1 for s in claim_strengths.values() if s == {"full"}
                )
                total_claims_for_strength = len(claim_strengths)
                full_pct = round(100 * full_only / total_claims_for_strength)
                claim_health_lines.append(
                    f"- atoms fully supported: {full_only}/{total_claims_for_strength} ({full_pct}%)"
                )

    # v2.2: Discovery Rigor metrics (reads gather_trace.yml if present)
    discovery_rigor_lines: list[str] = []
    gt_data = _load_optional(project_dir / "gather_trace.yml")
    gt_fetches = gt_data.get("fetches") if isinstance(gt_data, dict) else None
    if isinstance(gt_fetches, list) and gt_fetches:
        total_fetches = len(gt_fetches)
        accepts = 0
        rejects = 0
        escalations = 0
        by_subarea_decisions: dict[str, set[str]] = {}
        for fetch in gt_fetches:
            if not isinstance(fetch, dict):
                continue
            decision = fetch.get("decision")
            if decision == "accept":
                accepts += 1
            elif decision == "reject":
                rejects += 1
            elif decision == "escalate_to_manual":
                escalations += 1
            sub_area = fetch.get("sub_area")
            if isinstance(sub_area, str):
                by_subarea_decisions.setdefault(sub_area, set()).add(
                    str(decision) if decision is not None else "unknown"
                )
        accept_pct = round(100 * accepts / total_fetches) if total_fetches else 0
        coverage_gaps = sorted(
            sub_area for sub_area, decisions in by_subarea_decisions.items()
            if "accept" not in decisions
        )
        discovery_rigor_lines = [
            "",
            "## Discovery Rigor",
            "",
            f"- fetches reviewed: {total_fetches}",
            f"- accept rate: {accepts}/{total_fetches} ({accept_pct}%)",
            f"- rejected: {rejects}",
            f"- escalations needing manual review: {escalations}",
        ]
        if coverage_gaps:
            discovery_rigor_lines.append(
                f"- sub-areas with no accepted source: {', '.join(coverage_gaps)}"
            )

    title = _title_case(topic) if isinstance(topic, str) else "Research"
    lines = [
        f"# {title} — Trust Dashboard",
        "",
        f"Generated: {today.isoformat()}",
        f"Current as of: {today.isoformat()}",
        "",
        "## Trust State",
        "",
        f"- stale blockers: {stale_blockers}",
        f"- evidence coverage: {covered_claims}/{total_claims} claims",
        f"- cache completeness: {cached}/{total_referenced} sources",
        f"- conflicts: {conflicts}",
        f"- weak claims: {weak_claims}",
        "",
        "## Action Queue",
        "",
        *action_lines,
        *claim_health_lines,
        *discovery_rigor_lines,
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("project_dir")
    parser.add_argument(
        "--output",
        help="Output path (default: <project_dir>/dashboard.md)",
    )
    parser.add_argument(
        "--today",
        default=date.today().isoformat(),
        help="Anchor date for staleness (YYYY-MM-DD)",
    )
    parser.add_argument("--no-overwrite", action="store_true")
    args = parser.parse_args(argv[1:])

    project = Path(args.project_dir).expanduser().resolve()
    if not project.is_dir():
        print(f"error: not a directory: {project}", file=sys.stderr)
        return 2

    today_obj, err = parse_iso_date(args.today, "--today")
    if err is not None or today_obj is None:
        print(f"error: {err or 'invalid --today'}", file=sys.stderr)
        return 2

    output = (
        Path(args.output).expanduser().resolve()
        if args.output
        else project / "dashboard.md"
    )
    if args.no_overwrite and output.exists():
        print(f"error: refusing to overwrite existing {output}", file=sys.stderr)
        return 2

    content = build(project, today_obj)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

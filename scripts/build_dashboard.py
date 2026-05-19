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
    load_yaml_mapping,
    parse_iso_date,
    stale_error_for_entry,
)


TIER_ORDER = ("volatile", "active", "stable", "historical")


def _title_case(slug: str) -> str:
    return " ".join(part.capitalize() for part in slug.replace("_", " ").split())


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
    by_tier_stale: dict[str, list[date]] = {}
    for idx, entry in enumerate(list(bib_entries) + list(dataset_entries)):
        if not isinstance(entry, dict):
            continue
        loc = f"entries[{idx}]"
        if stale_error_for_entry(entry, loc=loc, today=today) is not None:
            stale_blockers += 1
        tier = entry.get("freshness_tier")
        stale_on = _stale_on(entry)
        if isinstance(tier, str) and stale_on is not None:
            by_tier_stale.setdefault(tier, []).append(stale_on)

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
        dates = sorted(by_tier_stale.get(tier, []))
        if not dates:
            continue
        action_lines.append(f"- Refresh {tier} entries by {dates[0].isoformat()}.")
    if not action_lines:
        action_lines.append("- (no action needed)")

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

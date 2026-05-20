#!/usr/bin/env python3
"""Mechanical FACT-framework-style citation audit for v3 strict-live projects.

Reads evidence_ledger.yml + cache_manifest.yml; for every supports[] link
runs the substring/hash check that validators/evidence_ledger.py runs.
Emits a citation_audit_report.md with per-method breakdowns + per-claim
grounding strength, plus a machine-readable summary block consumed by
scripts/build_dashboard.py.

No LLM required — the check is purely substring + hash.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date
import json
from pathlib import Path
import sys
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators.v2_common import (
    is_v3_mapping,
    load_yaml_mapping,
    verify_excerpt_anchor,
)


METHOD_BUCKETS = {
    "verbatim_match": "strong",
    "user_asserted": "strong",
    "paraphrase": "partial",
    "llm_inferred": "weak",
    "propagated_from_child": "weak",
    "manual_override": "partial",
}


def audit(project_dir: Path) -> dict[str, Any]:
    evidence_path = project_dir / "evidence_ledger.yml"
    manifest_path = project_dir / "cache_manifest.yml"

    edata, errors = load_yaml_mapping(evidence_path)
    if edata is None:
        raise SystemExit(f"evidence_ledger.yml: {'; '.join(errors) or 'missing'}")

    mdata, _ = load_yaml_mapping(manifest_path)
    cache_entries_by_id: dict[str, Any] = {}
    if mdata is not None:
        for e in (mdata.get("entries") or []):
            if isinstance(e, dict) and isinstance(e.get("cache_id"), str):
                cache_entries_by_id[e["cache_id"]] = e

    is_v3 = is_v3_mapping(edata)

    total_links = 0
    method_counts: dict[str, int] = defaultdict(int)
    method_sum_conf: dict[str, float] = defaultdict(float)
    substring_pass = 0
    substring_attempt = 0
    substring_failures: list[str] = []
    per_claim_methods: dict[str, list[str]] = defaultdict(list)
    per_claim_confs: dict[str, list[float]] = defaultdict(list)

    for entry in (edata.get("entries") or []):
        if not isinstance(entry, dict):
            continue
        excerpt = entry.get("excerpt") if isinstance(entry.get("excerpt"), str) else ""
        for support in (entry.get("supports") or []):
            if not isinstance(support, dict):
                continue
            total_links += 1
            method = support.get("extraction_method")
            link_conf = support.get("link_confidence")
            claim_id = support.get("claim_id")

            if isinstance(method, str):
                method_counts[method] += 1
            if isinstance(link_conf, (int, float)):
                method_counts.setdefault(method or "unknown", 0)
                method_sum_conf[method or "unknown"] += float(link_conf)
                if isinstance(claim_id, str):
                    per_claim_confs[claim_id].append(float(link_conf))
            if isinstance(claim_id, str) and isinstance(method, str):
                per_claim_methods[claim_id].append(method)

            anchor = support.get("excerpt_anchor")
            if method == "verbatim_match" and isinstance(anchor, dict) and is_v3:
                substring_attempt += 1
                anchor_errs = verify_excerpt_anchor(
                    excerpt=excerpt,
                    cache_id=anchor.get("cache_id", ""),
                    text_path_offset=anchor.get("text_path_offset", [0, 0]),
                    sha256_of_span=anchor.get("sha256_of_span", ""),
                    cache_entries_by_id=cache_entries_by_id,
                    manifest_path=manifest_path,
                    loc=f"{entry.get('evidence_id', '?')}.supports[?]",
                )
                if not anchor_errs:
                    substring_pass += 1
                else:
                    substring_failures.extend(anchor_errs)

    method_avg_conf = {
        m: round(method_sum_conf[m] / method_counts[m], 3) if method_counts[m] else 0.0
        for m in method_counts
    }

    grounded_strong = sum(method_counts.get(m, 0) for m, b in METHOD_BUCKETS.items() if b == "strong")
    grounded_partial = sum(method_counts.get(m, 0) for m, b in METHOD_BUCKETS.items() if b == "partial")
    grounded_weak = sum(method_counts.get(m, 0) for m, b in METHOD_BUCKETS.items() if b == "weak")

    # Per-claim grounding strength = strongest method seen for that claim
    rank = {"strong": 3, "partial": 2, "weak": 1, "unknown": 0}
    per_claim_health = {}
    for claim_id, methods in per_claim_methods.items():
        buckets = [METHOD_BUCKETS.get(m, "unknown") for m in methods]
        best = max(buckets, key=lambda b: rank[b])
        per_claim_health[claim_id] = best

    return {
        "is_v3": is_v3,
        "total_links": total_links,
        "method_counts": dict(method_counts),
        "method_avg_link_confidence": method_avg_conf,
        "grounded_strong": grounded_strong,
        "grounded_partial": grounded_partial,
        "grounded_weak": grounded_weak,
        "substring_attempt": substring_attempt,
        "substring_pass": substring_pass,
        "substring_failures": substring_failures,
        "per_claim_health": per_claim_health,
    }


def render_report(audit_data: dict[str, Any], project_name: str, today: date) -> str:
    total = audit_data["total_links"]
    strong = audit_data["grounded_strong"]
    partial = audit_data["grounded_partial"]
    weak = audit_data["grounded_weak"]

    pct = lambda n: f"{round(100 * n / total)}%" if total else "n/a"

    lines = [
        f"# Citation Audit Report — {project_name}",
        "",
        f"Generated: {today.isoformat()}",
        "",
        "## Summary",
        "",
        f"- Total support links: {total}",
        f"- Strongly grounded (verbatim_match + user_asserted): {strong}/{total} ({pct(strong)})",
        f"- Partially grounded (paraphrase + manual_override): {partial}/{total} ({pct(partial)})",
        f"- Weakly grounded (llm_inferred + propagated_from_child): {weak}/{total} ({pct(weak)})",
    ]
    if audit_data["substring_attempt"]:
        s_pass = audit_data["substring_pass"]
        s_total = audit_data["substring_attempt"]
        lines.append(
            f"- Substring check pass rate: {s_pass}/{s_total} ({round(100 * s_pass / s_total)}%)"
        )
    else:
        lines.append("- Substring check: not applicable (no verbatim_match anchors)")

    lines.extend([
        "",
        "## Per-method breakdown",
        "",
        "| extraction_method | count | avg link_confidence |",
        "|---|---|---|",
    ])
    for method in sorted(audit_data["method_counts"]):
        count = audit_data["method_counts"][method]
        avg_conf = audit_data["method_avg_link_confidence"].get(method, 0.0)
        lines.append(f"| {method} | {count} | {avg_conf} |")

    lines.extend([
        "",
        "## Per-claim grounding strength",
        "",
        "| claim_id | strongest_method_bucket |",
        "|---|---|",
    ])
    for claim_id in sorted(audit_data["per_claim_health"]):
        bucket = audit_data["per_claim_health"][claim_id]
        lines.append(f"| {claim_id} | {bucket} |")

    if audit_data["substring_failures"]:
        lines.extend([
            "",
            "## Substring check failures",
            "",
        ])
        for f in audit_data["substring_failures"]:
            lines.append(f"- {f}")

    lines.append("")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("project_dir")
    parser.add_argument("--output", help="Report path (default: <project_dir>/citation_audit_report.md)")
    parser.add_argument("--today", default=date.today().isoformat())
    parser.add_argument("--json", action="store_true", help="Also print metrics JSON to stdout")
    args = parser.parse_args(argv[1:])

    project = Path(args.project_dir).expanduser().resolve()
    if not project.is_dir():
        print(f"error: not a directory: {project}", file=sys.stderr)
        return 2

    audit_data = audit(project)
    today = date.fromisoformat(args.today)
    report = render_report(audit_data, project.name, today)

    output = (
        Path(args.output).expanduser().resolve()
        if args.output
        else project / "citation_audit_report.md"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(output)

    if args.json:
        # Strip non-serializable items
        serializable = {k: v for k, v in audit_data.items() if k != "substring_failures"}
        serializable["substring_failure_count"] = len(audit_data["substring_failures"])
        print(json.dumps(serializable, sort_keys=True))

    # Exit code: 0 if no substring failures (or no v3), 1 if failures
    return 1 if audit_data["substring_failures"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

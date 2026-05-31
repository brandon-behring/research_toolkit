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
import re
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

# --- Claim-excerpt relevance heuristic (WARNING-only) -----------------------
# The substring/hash check proves an excerpt EXISTS byte-exact in the cache; it
# does NOT prove the excerpt is ON-TOPIC for the claim it supports, so a real
# but tangential span ("quote-mining") passes the audit. This heuristic flags
# POSSIBLE quote-mining for HUMAN REVIEW by measuring keyword overlap between
# the claim text and the excerpt. It is explicitly NOT a correctness verdict and
# NEVER changes the audit's pass/fail (exit code) — relevance is heuristic.
#
# Metric: fraction of the claim's salient (stopworded, len>=3) tokens that also
# appear in the excerpt (recall of claim terms). Below RELEVANCE_MIN_OVERLAP ->
# warning. The heuristic ONLY runs when a real natural-language claim_text is
# available for the claim (from the sibling claim_graph.jsonl); without it the
# only claim-side descriptors are identifier-shaped (field_path + claim_id), too
# thin to judge, so the link is skipped rather than flagged. Claims whose
# claim_text has fewer than RELEVANCE_MIN_CLAIM_TOKENS salient tokens are also
# skipped (too short to judge). FALSE-POSITIVE EXPECTATION: short/technical
# excerpts, heavy acronym use, or claims phrased with different vocabulary than
# the source may flag despite being on-topic; that is why this is review-only,
# not a gate. Threshold 0.20 chosen so that on the shipped dossiers (whose
# claim_graphs do not yet populate claim_text) zero links are flagged — i.e. the
# check is silent until a project supplies real claim text to judge against.
RELEVANCE_MIN_OVERLAP = 0.2
RELEVANCE_MIN_CLAIM_TOKENS = 4

_RELEVANCE_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for", "with",
    "as", "by", "at", "from", "is", "are", "was", "were", "be", "been", "being",
    "that", "this", "these", "those", "it", "its", "which", "who", "whom", "whose",
    "can", "may", "must", "should", "would", "could", "will", "shall", "not", "no",
    "into", "over", "under", "than", "then", "such", "via", "per", "also", "where",
    "when", "while", "they", "them", "their", "there", "here", "between", "each",
    "any", "all", "some", "more", "most", "other", "using", "use", "used", "based",
    "how", "what", "if", "so", "do", "does", "has", "have", "had", "we", "you",
})
_RELEVANCE_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _salient_tokens(text: str | None) -> set[str]:
    """Lowercase alnum tokens of length >= 3 with stopwords removed."""
    return {
        w
        for w in _RELEVANCE_TOKEN_RE.findall((text or "").lower())
        if len(w) >= 3 and w not in _RELEVANCE_STOPWORDS
    }


def _load_claim_texts(project_dir: Path) -> dict[str, str]:
    """Best-effort map of claim_id -> claim text from a sibling claim_graph.jsonl.

    The canonical claim_graph claim record (record_type == "claim") carries the
    claim id under ``id`` and the natural-language statement under ``text`` — and
    a support link's ``claim_id`` references that ``id``. We key on ``id``/``text``
    and also accept the alternate ``claim_id``/``claim_text`` spelling for
    robustness. Returns {} if the file is absent or unreadable; malformed lines
    are skipped so a partial file still yields what it can.
    """
    path = project_dir / "claim_graph.jsonl"
    out: dict[str, str] = {}
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return out
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(rec, dict):
            continue
        # Only claim records carry claim text; skip entity/source/evidence/etc.
        if rec.get("record_type") not in (None, "claim"):
            continue
        cid = rec.get("id") if isinstance(rec.get("id"), str) else rec.get("claim_id")
        ct = rec.get("text") if isinstance(rec.get("text"), str) else rec.get("claim_text")
        if isinstance(cid, str) and isinstance(ct, str) and ct.strip():
            out[cid] = ct
    return out


def _relevance_warning(
    *,
    claim_id: str | None,
    field_path: str | None,
    excerpt: str,
    claim_texts: dict[str, str],
    loc: str,
) -> str | None:
    """Return a relevance WARNING if claim/excerpt keyword overlap is low, else None.

    The heuristic only runs when a real natural-language ``claim_text`` is
    available for ``claim_id`` from the sibling claim_graph.jsonl. If it is not
    (no claim_graph, or that claim carries no claim_text), this returns None:
    the only claim-side descriptors otherwise on the support link are
    ``field_path`` + ``claim_id``, which are identifier-shaped (e.g.
    ``results.jailbreak_rate`` / ``claim_v3_demo_accuracy``) and too thin to
    judge topical overlap without producing noise. Staying silent beats flagging
    spuriously: this is a review aid, and a false alarm on every link would make
    it useless. (``field_path`` is accepted for signature stability but is not
    used as a claim-text substitute.)
    """
    if not (isinstance(claim_id, str) and claim_id in claim_texts):
        return None
    claim_side = claim_texts[claim_id]

    claim_tokens = _salient_tokens(claim_side)
    if len(claim_tokens) < RELEVANCE_MIN_CLAIM_TOKENS:
        return None
    excerpt_tokens = _salient_tokens(excerpt)
    if not excerpt_tokens:
        # An excerpt with no salient tokens cannot substantiate a multi-term
        # claim; flag for review.
        overlap = 0.0
    else:
        overlap = len(claim_tokens & excerpt_tokens) / len(claim_tokens)
    if overlap >= RELEVANCE_MIN_OVERLAP:
        return None
    shared = sorted(claim_tokens & excerpt_tokens)
    return (
        f"{loc}: low claim-excerpt overlap {overlap:.2f} "
        f"(< {RELEVANCE_MIN_OVERLAP}); shared salient terms: {shared or 'none'} "
        f"(claim_id={claim_id!r}) — possible off-topic excerpt, review manually"
    )


def audit(project_dir: Path) -> dict[str, Any]:
    evidence_path = project_dir / "evidence_ledger.yml"
    manifest_path = project_dir / "cache_manifest.yml"

    edata, errors = load_yaml_mapping(evidence_path)
    if edata is None:
        raise SystemExit(f"evidence_ledger.yml: {'; '.join(errors) or 'missing'}")

    mdata, _ = load_yaml_mapping(manifest_path)
    cache_entries_by_id: dict[str, Any] = {}
    cache_root_value: str | None = None
    if mdata is not None:
        for e in (mdata.get("entries") or []):
            if isinstance(e, dict) and isinstance(e.get("cache_id"), str):
                cache_entries_by_id[e["cache_id"]] = e
        # v2.3+: honor cache_root for portable manifests + mixed-cache-location
        # dossiers (per ADR-049 body-quote anchoring discipline). Same pattern
        # as validators/evidence_ledger.py.
        if isinstance(mdata.get("cache_root"), str):
            cache_root_value = mdata["cache_root"]

    is_v3 = is_v3_mapping(edata)

    # Best-effort claim text for the relevance heuristic (sibling claim_graph).
    claim_texts = _load_claim_texts(project_dir)

    total_links = 0
    method_counts: dict[str, int] = defaultdict(int)
    method_sum_conf: dict[str, float] = defaultdict(float)
    substring_pass = 0
    substring_attempt = 0
    substring_failures: list[str] = []
    relevance_warnings: list[str] = []
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

            # Heuristic claim-excerpt relevance (WARNING-only; never affects exit).
            field_path = support.get("field_path")
            rel = _relevance_warning(
                claim_id=claim_id if isinstance(claim_id, str) else None,
                field_path=field_path if isinstance(field_path, str) else None,
                excerpt=excerpt,
                claim_texts=claim_texts,
                loc=f"{entry.get('evidence_id', '?')}.supports[claim={claim_id}]",
            )
            if rel:
                relevance_warnings.append(rel)

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
                    cache_root=cache_root_value,
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
        "relevance_warnings": relevance_warnings,
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

    relevance = audit_data.get("relevance_warnings") or []
    lines.extend([
        "",
        "## Relevance warnings (heuristic — review manually)",
        "",
        "These flag support links where the excerpt shares few salient keywords "
        "with the claim it supports — a possible sign of an off-topic excerpt "
        "(\"quote-mining\"). This is a HEURISTIC for human review, NOT a "
        "correctness verdict, and does NOT affect the audit's pass/fail. Short, "
        "technical, or differently-phrased excerpts may flag while still being "
        "on-topic.",
        "",
        f"- Links flagged: {len(relevance)} "
        f"(overlap threshold {RELEVANCE_MIN_OVERLAP})",
    ])
    for w in relevance:
        lines.append(f"- {w}")

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
        # Replace verbose string lists with counts for a compact metrics block.
        serializable = {
            k: v
            for k, v in audit_data.items()
            if k not in ("substring_failures", "relevance_warnings")
        }
        serializable["substring_failure_count"] = len(audit_data["substring_failures"])
        serializable["relevance_warning_count"] = len(
            audit_data.get("relevance_warnings") or []
        )
        print(json.dumps(serializable, sort_keys=True))

    # Exit code: 0 if no substring failures (or no v3), 1 if failures
    return 1 if audit_data["substring_failures"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

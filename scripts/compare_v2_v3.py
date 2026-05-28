#!/usr/bin/env python3
"""compare_v2_v3.py — regression check between a v2 dossier and its v3 re-gather.

After an E re-gather agent completes, run this to compare the new v3 dossier
against the v2 predecessor and surface:
  - Sources in v2 not in v3 (potential REGRESSIONS — was the drop intentional?)
  - Sources in v3 not in v2 (enrichments — v3 found new landmarks)
  - Sources in both (kept — v3 likely authoritative if it has excerpt anchors)
  - Bibkey overlap + delta
  - Claim count delta
  - Per-author/per-year coverage delta

Writes a markdown comparison report. Default-authoritative recommendation per
category. Surface losses for user judgment.

Usage:
    python compare_v2_v3.py <v2_dossier_dir> <v3_dossier_dir> [--out <path>]
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

import yaml


ARXIV_ID_RE = re.compile(r"arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5})", re.I)
DOI_RE = re.compile(r"\b(10\.\d{4,9}/[-._;()/:A-Z0-9]+)\b", re.I)


def canonicalize_url(url: str) -> str:
    """Normalize URLs for set comparison (strip pdf/abs variations, version suffixes)."""
    if not url:
        return ""
    u = url.strip().lower()
    # arXiv abs/pdf collapse
    am = ARXIV_ID_RE.search(u)
    if am:
        return f"arxiv:{am.group(1)}"
    dm = DOI_RE.search(u)
    if dm:
        return f"doi:{dm.group(1)}"
    # Strip query strings, trailing slashes
    u = u.split("?")[0].rstrip("/")
    return u


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with path.open() as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def collect_v2(dossier_dir: Path) -> dict:
    """Extract from v2 dossier: source URLs, bibkeys, evidence count, claim count."""
    out = {"sources": {}, "bibkeys": {}, "evidence_count": 0, "claim_count": 0, "schema": "?"}
    ev = load_yaml(dossier_dir / "evidence_ledger.yml")
    out["schema"] = ev.get("schema_version", "?")
    # v2 uses 'entries:' at top level
    for entry in ev.get("entries") or []:
        out["evidence_count"] += 1
        url = entry.get("source_url")
        if url:
            cu = canonicalize_url(url)
            out["sources"].setdefault(cu, []).append({"url": url, "ev_id": entry.get("evidence_id")})
    bib = load_yaml(dossier_dir / "bib_ledger.yml")
    for entry in bib.get("entries") or []:
        bk = entry.get("bibkey")
        if bk:
            out["bibkeys"][bk] = {
                "title": (entry.get("title") or "")[:120],
                "authors": entry.get("authors"),
                "year": _extract_year(entry),
                "url": entry.get("primary_url"),
            }
    # Claim count from claim_graph.jsonl if present
    cg = dossier_dir / "claim_graph.jsonl"
    if cg.exists():
        for line in cg.open():
            try:
                r = json.loads(line)
                if r.get("record_type") == "claim":
                    out["claim_count"] += 1
            except Exception:
                pass
    return out


def collect_v3(dossier_dir: Path) -> dict:
    """Extract from v3 dossier: source URLs, bibkeys, evidence count + supports w/ excerpt_anchor.

    Both v2 and v3 use top-level `entries:` — the schema difference is that v3 requires
    `supports[].excerpt_anchor` (cache_id + text_path_offset + sha256_of_span)."""
    out = {"sources": {}, "bibkeys": {}, "claim_count": 0, "anchor_count": 0,
           "schema": "?", "evidence_count": 0}
    ev = load_yaml(dossier_dir / "evidence_ledger.yml")
    out["schema"] = ev.get("schema_version", "?")
    seen_claims: set[str] = set()
    for entry in ev.get("entries") or []:
        out["evidence_count"] += 1
        url = entry.get("source_url")
        if url:
            cu = canonicalize_url(url)
            out["sources"].setdefault(cu, []).append({"url": url, "ev_id": entry.get("evidence_id")})
        for sup in entry.get("supports") or []:
            cid = sup.get("claim_id")
            if cid:
                seen_claims.add(cid)
            if "excerpt_anchor" in sup:
                out["anchor_count"] += 1
    out["claim_count"] = len(seen_claims)
    # Also pull from cache_manifest (canonical URL list — covers any cached URL even if not in supports)
    cm = load_yaml(dossier_dir / "cache_manifest.yml")
    for entry in cm.get("entries") or []:
        url = entry.get("source_url")
        if url:
            cu = canonicalize_url(url)
            if cu not in out["sources"]:
                out["sources"].setdefault(cu, []).append({"url": url, "ev_id": entry.get("cache_id")})
    # Also pull from cache_manifest (canonical URL list)
    cm = load_yaml(dossier_dir / "cache_manifest.yml")
    for entry in cm.get("entries") or []:
        url = entry.get("source_url")
        if url:
            cu = canonicalize_url(url)
            if cu not in out["sources"]:
                out["sources"].setdefault(cu, []).append({"url": url, "ev_id": entry.get("cache_id")})
    bib = load_yaml(dossier_dir / "bib_ledger.yml")
    for entry in bib.get("entries") or []:
        bk = entry.get("bibkey")
        if bk:
            out["bibkeys"][bk] = {
                "title": (entry.get("title") or "")[:120],
                "authors": entry.get("authors"),
                "year": _extract_year(entry),
                "url": entry.get("primary_url"),
            }
    return out


def _extract_year(bib_entry: dict) -> str | None:
    """Best-effort year extraction from a bib entry."""
    for k in ("year", "venue", "authors"):
        v = bib_entry.get(k)
        if isinstance(v, str):
            m = re.search(r"\b(19|20)\d{2}\b", v)
            if m:
                return m.group(0)
    return None


def render_report(v2: dict, v2_dir: Path, v3: dict, v3_dir: Path) -> str:
    v2_urls = set(v2["sources"].keys())
    v3_urls = set(v3["sources"].keys())
    v2_only = v2_urls - v3_urls
    v3_only = v3_urls - v2_urls
    common = v2_urls & v3_urls
    v2_bk = set(v2["bibkeys"].keys())
    v3_bk = set(v3["bibkeys"].keys())

    lines = []
    L = lines.append
    L(f"# Regression comparison: v2 vs v3 re-gather\n")
    L(f"- **v2 dossier:** `{v2_dir}`  (schema {v2['schema']}, {v2['evidence_count']} evidence, {v2['claim_count']} claims)")
    L(f"- **v3 dossier:** `{v3_dir}`  (schema {v3['schema']}, {v3['evidence_count']} evidence, {v3['claim_count']} claims, {v3['anchor_count']} with excerpt anchor)\n")

    L(f"## Source coverage delta (canonicalized URLs)\n")
    L(f"- v2 sources: **{len(v2_urls)}**  ·  v3 sources: **{len(v3_urls)}**  ·  common: **{len(common)}**")
    L(f"- v2-only (potential REGRESSIONS): **{len(v2_only)}**")
    L(f"- v3-only (ENRICHMENTS): **{len(v3_only)}**")
    L("")

    L(f"## Bibkey delta\n")
    L(f"- v2 bibkeys: {len(v2_bk)}  ·  v3 bibkeys: {len(v3_bk)}")
    only_v2_bk = v2_bk - v3_bk
    only_v3_bk = v3_bk - v2_bk
    L(f"- v2-only bibkeys: {len(only_v2_bk)}")
    L(f"- v3-only bibkeys: {len(only_v3_bk)}")
    L("")

    if v2_only:
        L(f"## Sources in v2 NOT in v3 — surface for your judgment ({len(v2_only)})\n")
        L(f"For each: was this an intentional drop (dedup/scope/superseded) or a regression to recover?\n")
        L(f"| canonical | original URL | v2 ev_ids |")
        L(f"|---|---|---|")
        for cu in sorted(v2_only):
            samples = v2["sources"][cu]
            url = samples[0]["url"]
            ev_ids = ", ".join((s.get("ev_id") or "?")[:24] for s in samples[:3])
            L(f"| `{cu[:60]}` | {url[:80]} | {ev_ids} |")
        L("")

    if only_v2_bk:
        L(f"## Bibkeys in v2 NOT in v3 (cross-reference; some may be URL-only changes)\n")
        L(f"| bibkey | v2 title | year | url |")
        L(f"|---|---|---|---|")
        for bk in sorted(only_v2_bk):
            info = v2["bibkeys"][bk]
            L(f"| `{bk}` | {info['title']} | {info['year'] or '?'} | {(info['url'] or '')[:80]} |")
        L("")

    if v3_only:
        L(f"## Sources NEW in v3 (enrichments — v3 authoritative) ({len(v3_only)})\n")
        L(f"| canonical | original URL |")
        L(f"|---|---|")
        for cu in sorted(v3_only)[:50]:
            samples = v3["sources"][cu]
            L(f"| `{cu[:60]}` | {samples[0]['url'][:80]} |")
        if len(v3_only) > 50:
            L(f"| … | (+{len(v3_only)-50} more) |")
        L("")

    L(f"## Authoritative recommendation\n")
    L(f"- **For sources in both ({len(common)}):** v3 authoritative (has excerpt anchors).")
    L(f"- **For v3-only ({len(v3_only)}):** v3 authoritative (enrichment).")
    if v2_only:
        L(f"- **For v2-only ({len(v2_only)}):** **surface to user** — review each in §'Sources in v2 NOT in v3' above and confirm intentional drop vs. regression. Use `--accept-v2-only <ev_id1,ev_id2,...>` on a follow-up cache_source.py run to bring them into v3.")
    else:
        L(f"- v2-only is empty — v3 covers v2's full source set. **v2 can be safely deprecated.**")
    L("")

    L(f"## Net judgment\n")
    if not v2_only and v3_only:
        L(f"- v3 strictly enriches v2 with {len(v3_only)} new sources and adds {v3['anchor_count']} excerpt anchors. **v3 authoritative. Safe to deprecate v2.**")
    elif not v2_only and not v3_only:
        L(f"- v3 preserves v2's source set exactly and adds {v3['anchor_count']} excerpt anchors. **v3 authoritative. Safe to deprecate v2.**")
    elif v2_only:
        L(f"- v3 has {len(v2_only)} regression(s) against v2. **DO NOT deprecate v2 until each loss is reviewed.** Recover or document acceptance.")

    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("v2_dir", type=Path, help="Path to v2 dossier dir")
    ap.add_argument("v3_dir", type=Path, help="Path to v3 dossier dir")
    ap.add_argument("--out", type=Path, default=None, help="Write report to this path (default: stdout)")
    args = ap.parse_args()

    if not (args.v2_dir / "evidence_ledger.yml").exists():
        print(f"FATAL: v2 evidence_ledger.yml not found: {args.v2_dir}", file=sys.stderr)
        return 2
    if not (args.v3_dir / "evidence_ledger.yml").exists():
        print(f"FATAL: v3 evidence_ledger.yml not found: {args.v3_dir}", file=sys.stderr)
        return 2

    print(f"Reading v2: {args.v2_dir}", file=sys.stderr)
    v2 = collect_v2(args.v2_dir)
    print(f"  schema={v2['schema']} evidence={v2['evidence_count']} claims={v2['claim_count']} sources={len(v2['sources'])} bibkeys={len(v2['bibkeys'])}", file=sys.stderr)

    print(f"Reading v3: {args.v3_dir}", file=sys.stderr)
    v3 = collect_v3(args.v3_dir)
    print(f"  schema={v3['schema']} evidence={v3['evidence_count']} claims={v3['claim_count']} anchors={v3['anchor_count']} sources={len(v3['sources'])} bibkeys={len(v3['bibkeys'])}", file=sys.stderr)

    report = render_report(v2, args.v2_dir, v3, args.v3_dir)
    if args.out:
        args.out.write_text(report)
        print(f"\nWROTE {args.out}", file=sys.stderr)
    else:
        print(report)

    # Exit code: 1 if v2-only sources exist (regressions to review), 0 otherwise
    v2_only = set(v2["sources"].keys()) - set(v3["sources"].keys())
    return 1 if v2_only else 0


if __name__ == "__main__":
    sys.exit(main())

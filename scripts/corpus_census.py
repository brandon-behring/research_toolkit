#!/usr/bin/env python3
"""Machine census of the research-dossiers corpus — the authoritative counts.

`research_INDEX.md` is hand-curated prose (per-domain sections, narrative, per-dossier
tables) and that curation is its value. What goes stale is its *summary statistics*: on
2026-08-26 the header claimed 85 folders / 36 v3 against a real 174 / 154.

This does not regenerate the INDEX. It emits the ground truth the INDEX's summary should
cite, so the numbers can be corrected without destroying the prose. `research_INDEX.md:1`
referred to `scripts/corpus_index.py --write-index`, which does not exist in the repo (it
was deliberately not imported); this fills that role read-only.

Usage:
    python3 corpus_census.py [ROOT] [--json]

Never fails silently: an unreadable ledger is reported, not skipped.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import yaml

DEFAULT_ROOT = Path.home() / "Claude" / "research-dossiers"


def tier(d: Path) -> str:
    """v3 = schema_version 3 · v2 = strict-live without anchors · dataset · v1 = bib-only."""
    ev = d / "evidence_ledger.yml"
    if ev.exists():
        try:
            sv = (yaml.safe_load(ev.read_text()) or {}).get("schema_version")
        except yaml.YAMLError as exc:
            raise ValueError(f"{d.name}: unreadable evidence_ledger.yml: {exc}") from exc
        return f"v{sv}" if sv else "v?"
    if (d / "dataset_ledger.yml").exists():
        return "dataset"
    if (d / "bib_ledger.yml").exists():
        return "v1"
    return "none"


def census(root: Path) -> dict:
    dossiers, problems = [], []
    for d in sorted(root.glob("research_*")):
        if not d.is_dir():
            continue
        try:
            t = tier(d)
        except ValueError as exc:
            problems.append(str(exc))
            t = "error"
        dash = d / "dashboard.md"
        stale = None
        if dash.exists():
            for line in dash.read_text().splitlines():
                if "stale blockers:" in line:
                    stale = int(line.split(":")[1].strip())
                    break
        cg = d / "claim_graph.jsonl"
        dossiers.append({
            "slug": d.name,
            "tier": t,
            "claims": sum(1 for _ in cg.open()) if cg.exists() else 0,
            "dashboard": dash.exists(),
            "stale_blockers": stale,
            "exported": (d / "synthesis_export.jsonl").exists(),
        })
    return {
        "root": str(root),
        "dossier_dirs": len(dossiers),
        "tiers": dict(Counter(x["tier"] for x in dossiers)),
        "with_dashboard": sum(1 for x in dossiers if x["dashboard"]),
        "with_claim_graph": sum(1 for x in dossiers if x["claims"]),
        "exported": sum(1 for x in dossiers if x["exported"]),
        "total_claims": sum(x["claims"] for x in dossiers),
        "stale": {x["slug"]: x["stale_blockers"] for x in dossiers if x["stale_blockers"]},
        "problems": problems,
        "dossiers": dossiers,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", nargs="?", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if not args.root.is_dir():
        print(f"ERROR: not a directory: {args.root}", file=sys.stderr)
        return 2

    c = census(args.root)
    if args.json:
        print(json.dumps(c, indent=2))
        return 1 if c["problems"] else 0

    print(f"corpus census — {c['root']}\n")
    print(f"  dossier folders   {c['dossier_dirs']}")
    print(f"  tiers             " + " · ".join(f"{k} {v}" for k, v in sorted(c["tiers"].items())))
    print(f"  with dashboard    {c['with_dashboard']}")
    print(f"  with claim graph  {c['with_claim_graph']}")
    print(f"  exported          {c['exported']}")
    print(f"  total claims      {c['total_claims']:,}")
    if c["stale"]:
        print(f"\n  STALE ({len(c['stale'])}):")
        for slug, n in sorted(c["stale"].items(), key=lambda kv: -kv[1]):
            print(f"    {slug:52} {n}")
    for p in c["problems"]:
        print(f"  PROBLEM: {p}", file=sys.stderr)
    return 1 if c["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""verify_anchors.py — prove every evidence anchor still points at the bytes it claims.

Read-only. For each dossier, resolves the cache_root its OWN manifest declares, then for
every `excerpt_anchor` in its evidence_ledger.yml checks two things:

  1. PRESENCE  — the cited cache_id resolves to a text blob on disk.
  2. INTEGRITY — re-hashing the bytes at `text_path_offset` reproduces `sha256_of_span`.

Presence alone is not enough, and a restore or re-cache is exactly when that gap bites: a
re-fetched source keeps its excerpt but moves its offsets, so a presence-only check passes an
atom that points at the wrong bytes. That is why (2) exists and why both are failures, not
warnings.

BYTES, NOT CHARACTERS. `text_path_offset` indexes raw bytes, so the span is sliced from
`read_bytes()`. Decoding first and slicing characters agrees on pure ASCII and diverges on
anything multi-byte — a checker that silently agrees is worse than one that fails, so
`tests/test_verify_anchors.py` pins this with a multi-byte fixture.

CACHE_ROOT IS THREE-STATE, not two:

    resolves                -> verify
    absent, `~`-relative    -> SKIP; a clean checkout legitimately has a cold cache
    absent, absolute        -> MANIFEST DEFECT; an absolute root from another machine is a
                               portability bug, and reporting it as "cold cache" is how a
                               dossier gets a green tick over spans nobody can read

UNANCHORED SUPPORTS ARE SPLIT, NOT TOTALLED. A support whose `extraction_method` is
`paraphrase` cannot carry a verbatim span — no anchor there is *correct*, not missing. Reporting
one combined count invites the next reader to see a gap where there is none, so the two are
reported separately and only the `other` bucket is a question. Neither is a failure.

Usage:
    python verify_anchors.py [--root DIR] [--dossier NAME ...] [--report OUT.md] [--json]

Exit 0 only when nothing failed. Exit 1 on any missing blob, hash mismatch, or manifest defect.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

DEFAULT_ROOT = Path("~/Claude/research-dossiers").expanduser()


def load(path: Path):
    try:
        return yaml.safe_load(path.read_text()) or {}
    except Exception:
        return {}


def manifest_index(dossier: Path) -> tuple[dict, str, Path | None, str]:
    """Return (cache_id -> entry, declared_root_str, resolved_root_or_None, root_state)."""
    man = load(dossier / "cache_manifest.yml")
    declared = str(man.get("cache_root") or "~/Claude/research_cache")
    p = Path(declared).expanduser()
    if p.is_dir():
        state = "ok"
        root = p
    elif declared.startswith("~"):
        state = "cold"          # legitimate on a clean checkout
        root = None
    else:
        state = "defect"        # absolute path from another machine
        root = None
    return ({e["cache_id"]: e for e in (man.get("entries") or []) if e.get("cache_id")},
            declared, root, state)


def verify_dossier(dossier: Path) -> dict:
    idx, declared, root, root_state = manifest_index(dossier)
    r = {"dossier": dossier.name, "cache_root": declared, "root_state": root_state,
         "atoms": 0, "verified": 0, "missing_blob": 0, "mismatch": 0,
         "no_anchor_paraphrase": 0, "no_anchor_other": 0,
         "unknown_cache_id": 0, "failures": []}

    ev = load(dossier / "evidence_ledger.yml")
    cache: dict[Path, bytes] = {}

    for atom in (ev.get("entries") or []):
        eid = atom.get("evidence_id")
        for sup in (atom.get("supports") or []):
            anchor = sup.get("excerpt_anchor") or {}
            cid, off, want = (anchor.get("cache_id"), anchor.get("text_path_offset"),
                              anchor.get("sha256_of_span"))
            if not (cid and off and want):
                # A paraphrase CANNOT carry a verbatim span — no anchor is correct there, not
                # missing. Split so the total is never read as a gap: only `other` is a question.
                key = ("no_anchor_paraphrase" if sup.get("extraction_method") == "paraphrase"
                       else "no_anchor_other")
                r[key] += 1
                continue
            r["atoms"] += 1
            if root_state != "ok":
                continue                      # counted at the dossier level, not per atom
            entry = idx.get(cid)
            if entry is None:
                r["unknown_cache_id"] += 1
                r["failures"].append(f"{eid}: cache_id {cid} not in cache_manifest")
                continue
            tp = root / str(entry.get("text_path", ""))
            if not tp.is_file():
                r["missing_blob"] += 1
                r["failures"].append(f"{eid}: blob absent — {entry.get('source_url')}")
                continue
            if tp not in cache:
                cache[tp] = tp.read_bytes()       # BYTES. see module docstring.
            got = hashlib.sha256(cache[tp][off[0]:off[1]]).hexdigest()
            if got == want:
                r["verified"] += 1
            else:
                r["mismatch"] += 1
                r["failures"].append(f"{eid}: span hash mismatch at {off} in {cid}")
    return r


def run(root: Path, only: list[str] | None) -> tuple[int, dict]:
    dossiers = sorted(d for d in root.glob("research_*")
                      if (d / "evidence_ledger.yml").is_file()
                      and (not only or d.name in only))
    rows = [verify_dossier(d) for d in dossiers]
    agg = {k: sum(r[k] for r in rows)
           for k in ("atoms", "verified", "missing_blob", "mismatch",
                     "no_anchor_paraphrase", "no_anchor_other", "unknown_cache_id")}
    agg["dossiers"] = len(rows)
    agg["root_defect"] = sum(r["root_state"] == "defect" for r in rows)
    agg["root_cold"] = sum(r["root_state"] == "cold" for r in rows)
    failed = agg["missing_blob"] + agg["mismatch"] + agg["unknown_cache_id"] + agg["root_defect"]
    return (1 if failed else 0), {"summary": agg, "dossiers": rows}


def render(res: dict) -> str:
    s = res["summary"]
    ok = not (s["missing_blob"] + s["mismatch"] + s["unknown_cache_id"] + s["root_defect"])
    out = ["# Anchor verification", "", f"**{'PASS' if ok else 'FAIL'}** — "
           f"{s['dossiers']} dossiers, {s['atoms']} anchored atoms", "",
           "| Measure | Count |", "|---|--:|",
           f"| verified (span re-hashes equal) | {s['verified']} |",
           f"| missing blob | {s['missing_blob']} |",
           f"| span hash mismatch | {s['mismatch']} |",
           f"| cache_id not in manifest | {s['unknown_cache_id']} |",
           f"| cache_root MANIFEST DEFECT (absolute, unresolvable) | {s['root_defect']} |",
           f"| cache_root cold (`~`-relative, absent — skipped) | {s['root_cold']} |",
           f"| no anchor — `extraction_method: paraphrase` (correct, not a gap) | {s['no_anchor_paraphrase']} |",
           f"| no anchor — other extraction_method (worth a look) | {s['no_anchor_other']} |", ""]
    bad = [d for d in res["dossiers"] if d["failures"] or d["root_state"] == "defect"]
    if bad:
        out += ["## Problems", ""]
        for d in bad:
            if d["root_state"] == "defect":
                out.append(f"- **{d['dossier']}** — cache_root defect: `{d['cache_root']}`")
            for f in d["failures"][:20]:
                out.append(f"- `{d['dossier']}` {f}")
            if len(d["failures"]) > 20:
                out.append(f"- `{d['dossier']}` … {len(d['failures']) - 20} more")
        out.append("")
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Verify evidence anchors against cached bytes.")
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--dossier", action="append")
    ap.add_argument("--report", type=Path)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    code, res = run(a.root, a.dossier)
    print(json.dumps(res["summary"], indent=2) if a.json else render(res))
    if a.report:
        a.report.write_text(render(res))
    return code


if __name__ == "__main__":
    sys.exit(main())

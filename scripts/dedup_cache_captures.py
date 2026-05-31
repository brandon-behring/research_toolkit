#!/usr/bin/env python3
"""dedup_cache_captures.py — consolidate same-paper-different-sha256 cache captures.

Fix D from Phase 1. When the same paper was captured under multiple sha256s
(usually because of `arxiv.org/abs/...` vs `arxiv.org/pdf/...`, different URL
versions, or mirror sites), this script picks a canonical sha256 per identifier
(arXiv ID or DOI), rewrites all cache_manifest references in non-canonical
dossiers to point at the canonical, and (optionally) removes the now-orphaned
duplicate blobs.

Canonical selection rule (deterministic):
  1. Most-referenced sha256 wins (most dossier manifests).
  2. Tie-breaker 1: HTML over PDF (HTML/abs pages tend to have cleaner
     full-metadata text + smaller bytes).
  3. Tie-breaker 2: smallest cache_id (lexicographic — stable).

Idempotent and dry-run by default; pass --execute to apply.
"""
from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path

import yaml

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators._common import ARXIV_ID_RE, DOI_RE

HOME = Path.home()
SHARED_CACHE = HOME / "Claude" / "research_cache"

ROOTS = [
    HOME / "Claude", HOME / "post_transformers", HOME / "guides",
    HOME / "guides-experimentation", HOME / "eval-toolkit",
    HOME / "rl_and_control", HOME / "double_ml_time_series", HOME / "prompt-injection-v4",
]


def find_dossier_dirs() -> list[Path]:
    seen: set[Path] = set()
    for root in ROOTS:
        if not root.exists():
            continue
        for cg in root.rglob("claim_graph.jsonl"):
            if any(p in {".venv", "tests", "fixtures", "composed", "node_modules"} for p in cg.parts):
                continue
            seen.add(cg.parent)
    return sorted(seen)


def collect_id_to_shas(dossier_dirs: list[Path]) -> tuple[dict, dict, dict]:
    """Return (arxiv_id_to_shas, doi_to_shas, sha_meta) where sha_meta tracks per-sha:
       {refs: set[dossier_slug], content_type, source_url, cache_id}.
    """
    arxiv: dict[str, set[str]] = collections.defaultdict(set)
    doi: dict[str, set[str]] = collections.defaultdict(set)
    sha_meta: dict[str, dict] = {}
    for d in dossier_dirs:
        cm = d / "cache_manifest.yml"
        if not cm.exists():
            continue
        try:
            with cm.open() as f:
                data = yaml.safe_load(f) or {}
        except Exception:
            continue
        for entry in data.get("entries") or []:
            sha = entry.get("sha256")
            if not sha:
                continue
            url = entry.get("source_url") or ""
            meta = sha_meta.setdefault(sha, {"refs": set(), "content_type": entry.get("content_type"),
                                             "source_url": url, "cache_id": entry.get("cache_id"),
                                             "raw_path": entry.get("raw_path")})
            meta["refs"].add(d.name)
            am = ARXIV_ID_RE.search(url)
            if am:
                arxiv[am.group(1)].add(sha)
            dm = DOI_RE.search(url)
            if dm:
                doi[dm.group(1)].add(sha)
    return arxiv, doi, sha_meta


def pick_canonical(shas: list[str], sha_meta: dict) -> str:
    def key(sha):
        m = sha_meta.get(sha, {})
        refs = -len(m.get("refs", []))  # more refs = better (more negative)
        ct = (m.get("content_type") or "").lower()
        html_first = 0 if "html" in ct or "text" in ct else 1  # HTML wins
        cache_id = m.get("cache_id", "")
        return (refs, html_first, cache_id)
    return sorted(shas, key=key)[0]


def rewrite_manifest(dossier_dir: Path, sha_remap: dict[str, str], execute: bool) -> int:
    """Replace any sha256 that appears as a key in sha_remap with its canonical value.
    Returns number of entries rewritten."""
    cm = dossier_dir / "cache_manifest.yml"
    if not cm.exists():
        return 0
    with cm.open() as f:
        data = yaml.safe_load(f) or {}
    entries = data.get("entries") or []
    n = 0
    for entry in entries:
        sha = entry.get("sha256")
        if sha and sha in sha_remap:
            canonical = sha_remap[sha]
            if execute:
                entry["sha256"] = canonical
                entry["raw_path"] = f"blobs/sha256/{canonical}"
                entry["text_path"] = f"text/sha256/{canonical}.txt"
                entry["metadata_path"] = f"metadata/sha256/{canonical}.json"
                # Note in source_url metadata? Leave URL alone — it's the original.
            n += 1
    if execute and n:
        with cm.open("w") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--execute", action="store_true", help="Actually rewrite manifests (default: dry-run)")
    ap.add_argument("--remove-orphan-blobs", action="store_true",
                    help="After consolidation, rm the non-canonical blobs from shared cache (requires --execute)")
    args = ap.parse_args()

    dossier_dirs = find_dossier_dirs()
    print(f"Scanning {len(dossier_dirs)} dossier dirs", file=sys.stderr)
    arxiv, doi, sha_meta = collect_id_to_shas(dossier_dirs)
    arxiv_dupes = {k: sorted(v) for k, v in arxiv.items() if len(v) > 1}
    doi_dupes = {k: sorted(v) for k, v in doi.items() if len(v) > 1}
    print(f"\narXiv dupes: {len(arxiv_dupes)}  |  DOI dupes: {len(doi_dupes)}", file=sys.stderr)

    sha_remap: dict[str, str] = {}  # non-canonical -> canonical
    for id_kind, dupes in [("arXiv", arxiv_dupes), ("DOI", doi_dupes)]:
        for ident, shas in dupes.items():
            canonical = pick_canonical(shas, sha_meta)
            print(f"\n  {id_kind} {ident}:", file=sys.stderr)
            for s in shas:
                refs = len(sha_meta.get(s, {}).get("refs", []))
                ct = sha_meta.get(s, {}).get("content_type", "?")
                marker = "  CANONICAL" if s == canonical else "  remap ->"
                print(f"   {marker} {s[:16]}…  refs={refs}  ct={ct}", file=sys.stderr)
            for s in shas:
                if s != canonical:
                    # Don't overwrite if this sha was already chosen as canonical for a different ID
                    if s not in sha_remap:
                        sha_remap[s] = canonical

    print(f"\n{len(sha_remap)} sha256s to remap to canonicals", file=sys.stderr)
    if not sha_remap:
        return 0

    print(f"\nMode: {'EXECUTE' if args.execute else 'DRY-RUN'}", file=sys.stderr)
    total_rewrites = 0
    for d in dossier_dirs:
        n = rewrite_manifest(d, sha_remap, args.execute)
        if n:
            print(f"  - {d.name}: {n} entry/entries rewritten", file=sys.stderr)
            total_rewrites += n
    print(f"\nTotal entries rewritten: {total_rewrites}", file=sys.stderr)

    if args.execute and args.remove_orphan_blobs:
        print(f"\nRemoving {len(sha_remap)} orphan blobs from shared cache…", file=sys.stderr)
        for orphan_sha in sha_remap:
            for kind, suffix in [("blobs", ""), ("text", ".txt"), ("metadata", ".json")]:
                p = SHARED_CACHE / kind / "sha256" / f"{orphan_sha}{suffix}"
                if p.exists():
                    p.unlink()
                    print(f"  - rm {kind}/{orphan_sha[:12]}…{suffix}", file=sys.stderr)
    elif args.execute:
        print(f"\nOrphan blobs remain in shared cache ({len(sha_remap)} blobs). "
              f"Re-run with --remove-orphan-blobs to GC.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

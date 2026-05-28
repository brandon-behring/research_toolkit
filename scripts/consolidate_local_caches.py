#!/usr/bin/env python3
"""consolidate_local_caches.py — move per-dossier local caches into the shared cache.

Fix A from Phase 1 of the locked plan. For each dossier whose `cache_manifest.yml`
points at a local `./cache/` (or any cache_root != the shared root), this script:

1. For each entry, verifies the local blob's sha256 == filename (content-addressed
   integrity check), then copies blob + text + metadata into the shared cache
   (skipping any target that already exists, which dedups for free across dossiers).
2. Rewrites the manifest: `cache_root` → shared, paths → relative to shared
   (`blobs/sha256/<sha>` / `text/sha256/<sha>.txt` / `metadata/sha256/<sha>.json`).
3. Optionally removes the local `cache/` dir after verification (--delete-local).

Idempotent — safe to re-run. Dry-run by default; pass --execute to apply.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

import yaml

HOME = Path.home()
SHARED_CACHE = HOME / "Claude" / "research_cache"
SHARED_DISPLAY = "~/Claude/research_cache"

# Dossier roots to scan (same as cache_health.py).
ROOTS = [
    HOME / "Claude",
    HOME / "post_transformers",
    HOME / "guides",
    HOME / "guides-experimentation",
    HOME / "eval-toolkit",
    HOME / "rl_and_control",
    HOME / "double_ml_time_series",
    HOME / "prompt-injection-v4",
]


def find_local_cache_dossiers() -> list[Path]:
    """Find dirs that have BOTH claim_graph.jsonl AND a non-empty local cache/."""
    seen: set[Path] = set()
    for root in ROOTS:
        if not root.exists():
            continue
        for cg in root.rglob("claim_graph.jsonl"):
            parts = cg.parts
            if any(p in {".venv", "tests", "fixtures", "composed", "node_modules"} for p in parts):
                continue
            d = cg.parent
            local = d / "cache"
            if local.is_dir() and any(local.rglob("*")):
                seen.add(d)
    return sorted(seen)


def relative_blob_path(sha: str) -> str:
    return f"blobs/sha256/{sha}"


def relative_text_path(sha: str) -> str:
    return f"text/sha256/{sha}.txt"


def relative_meta_path(sha: str) -> str:
    return f"metadata/sha256/{sha}.json"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def consolidate_dossier(dossier_dir: Path, execute: bool, delete_local: bool) -> dict:
    cm_path = dossier_dir / "cache_manifest.yml"
    if not cm_path.exists():
        return {"slug": dossier_dir.name, "skipped": "no cache_manifest"}
    with cm_path.open() as f:
        data = yaml.safe_load(f) or {}
    local_root = dossier_dir / "cache"
    if data.get("cache_root", "").startswith(SHARED_DISPLAY) or data.get("cache_root", "").startswith(str(SHARED_CACHE)):
        return {"slug": dossier_dir.name, "skipped": "already shared"}
    entries = data.get("entries") or []
    stats = {
        "slug": dossier_dir.name,
        "entries": len(entries),
        "copied_blob": 0, "copied_text": 0, "copied_meta": 0,
        "already_shared": 0, "integrity_failures": [], "missing_local": [],
    }
    for entry in entries:
        sha = entry.get("sha256")
        if not sha:
            continue
        # Local file locations
        for kind, suffix, key in [
            ("blob", "", "raw_path"),
            ("text", ".txt", "text_path"),
            ("meta", ".json", "metadata_path"),
        ]:
            local_dir = local_root / ({"blob": "blobs", "text": "text", "meta": "metadata"}[kind]) / "sha256"
            local_file = local_dir / f"{sha}{suffix}"
            shared_dir = SHARED_CACHE / ({"blob": "blobs", "text": "text", "meta": "metadata"}[kind]) / "sha256"
            shared_file = shared_dir / f"{sha}{suffix}"

            if not local_file.exists():
                if kind == "blob":
                    stats["missing_local"].append(sha)
                continue
            # Verify integrity for blobs (sha256 of content == filename)
            if kind == "blob":
                got = sha256_of(local_file)
                if got != sha:
                    stats["integrity_failures"].append({"sha": sha, "actual": got})
                    continue  # skip copying corrupt entry
            if shared_file.exists():
                stats["already_shared"] += 1 if kind == "blob" else 0
                continue
            if execute:
                shared_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(local_file, shared_file)
            if kind == "blob":
                stats["copied_blob"] += 1
            elif kind == "text":
                stats["copied_text"] += 1
            else:
                stats["copied_meta"] += 1
        # Repoint the entry to shared layout
        if execute:
            entry["raw_path"] = relative_blob_path(sha)
            entry["text_path"] = relative_text_path(sha)
            entry["metadata_path"] = relative_meta_path(sha)

    # Rewrite manifest
    if execute:
        data["cache_root"] = SHARED_DISPLAY
        with cm_path.open("w") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
        # Optionally delete local cache
        if delete_local and not stats["integrity_failures"] and not stats["missing_local"]:
            shutil.rmtree(local_root)
            stats["deleted_local"] = True
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--execute", action="store_true", help="Actually copy/rewrite (default: dry-run)")
    ap.add_argument("--delete-local", action="store_true", help="rm -rf local cache/ after successful consolidation")
    ap.add_argument("--only", action="append", default=[], help="Only consolidate dossiers whose name contains this substring (repeatable)")
    args = ap.parse_args()

    dossiers = find_local_cache_dossiers()
    if args.only:
        dossiers = [d for d in dossiers if any(s in d.name for s in args.only)]
    print(f"Found {len(dossiers)} local-cache dossiers to consolidate", file=sys.stderr)
    print(f"Mode: {'EXECUTE' if args.execute else 'DRY-RUN'}{' + delete-local' if args.delete_local and args.execute else ''}", file=sys.stderr)
    print("", file=sys.stderr)

    totals = {"entries": 0, "copied_blob": 0, "copied_text": 0, "copied_meta": 0, "already_shared": 0,
              "integrity_failures": 0, "missing_local": 0, "deleted_local": 0}
    results = []
    for d in dossiers:
        r = consolidate_dossier(d, execute=args.execute, delete_local=args.delete_local)
        results.append(r)
        if "skipped" in r:
            print(f"  - {r['slug']}: SKIPPED ({r['skipped']})", file=sys.stderr)
            continue
        totals["entries"] += r["entries"]
        totals["copied_blob"] += r["copied_blob"]
        totals["copied_text"] += r["copied_text"]
        totals["copied_meta"] += r["copied_meta"]
        totals["already_shared"] += r["already_shared"]
        totals["integrity_failures"] += len(r["integrity_failures"])
        totals["missing_local"] += len(r["missing_local"])
        if r.get("deleted_local"):
            totals["deleted_local"] += 1
        flags = []
        if r["integrity_failures"]:
            flags.append(f"!! {len(r['integrity_failures'])} integrity failures")
        if r["missing_local"]:
            flags.append(f"!! {len(r['missing_local'])} missing local blobs")
        flag_str = " | ".join(flags) if flags else "ok"
        print(f"  - {r['slug']}: entries={r['entries']} copy_blob={r['copied_blob']} already_shared={r['already_shared']}{' '+flag_str if flags else ''}", file=sys.stderr)

    print("", file=sys.stderr)
    print("=== TOTALS ===", file=sys.stderr)
    for k, v in totals.items():
        print(f"  {k}: {v}", file=sys.stderr)
    if totals["integrity_failures"]:
        print(f"\nINTEGRITY FAILURES — investigate before --execute or --delete-local:", file=sys.stderr)
        for r in results:
            for f in r.get("integrity_failures", []):
                print(f"  - {r['slug']}: sha={f['sha'][:12]}… got={f['actual'][:12]}…", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

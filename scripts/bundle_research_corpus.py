#!/usr/bin/env python3
"""bundle_research_corpus.py — package the personal research corpus for transport.

Phase 2 of the locked plan. Produces a portable tarball + sha256 sidecar + manifest
for shipping the corpus from laptop to desktop (where research-kb's queryable
ingestion code lives). Reusable for the recurring laptop→desktop sync per
locked design §8 Q14 (files-canonical).

Scope B (locked): ~/Claude strict-live dossiers + shared cache + inbox + catalogue
+ home-wide research project dirs (minus cruft).

Behavior:
1. Freshness pre-flight — re-run `research_kb_export.py` for any dossier whose
   claim_graph.jsonl is newer than its inbox JSONL (so the inbox is current).
2. Enumerate the scope-B payload (write paths to a temp file for `tar -T`).
3. Build a MANIFEST.txt with: schema, ISO timestamp, scope, toolkit git rev,
   per-dossier records + claim_graph sha256, cache summary, inbox summary,
   embedded cache_health.md snapshot.
4. tar czf the payload with the exclusion list.
5. Sha256 the tarball; write `.sha256` sidecar; append to MANIFEST.
6. Print desktop verification commands.

Idempotent. Re-run any time to produce a fresh tarball of current state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

HOME = Path.home()
CLAUDE = HOME / "Claude"
TK = CLAUDE / "research_toolkit"
SHARED_CACHE = CLAUDE / "research_cache"
INBOX = CLAUDE / "research-kb" / "inbox"
CATALOGUE = [
    CLAUDE / "research_INDEX.md",
    CLAUDE / "research_BACKLOG.md",
    CLAUDE / "research_TOPIC_BACKLOG.md",
    CLAUDE / "research_graph.json",
    CLAUDE / "research_graph.html",
    CLAUDE / "cache_health.md",
    CLAUDE / "retry_escalations_report.md",
]

HOMEWIDE_PROJECTS = [
    HOME / "post_transformers",
    HOME / "guides",
    HOME / "guides-experimentation",
    HOME / "eval-toolkit",
    HOME / "rl_and_control",
    HOME / "double_ml_time_series",
    HOME / "prompt-injection-v4",
]

EXCLUDES = [
    ".venv", ".git", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache",
    ".DS_Store", "*.pyc",
]


def sha256_of_file(path: Path, chunk: int = 65536) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for c in iter(lambda: f.read(chunk), b""):
            h.update(c)
    return h.hexdigest()


def get_toolkit_git_rev() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=TK, capture_output=True, text=True, timeout=5
        )
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def find_strict_live_dossiers() -> list[Path]:
    """All dirs containing claim_graph.jsonl across the scope-B roots."""
    seen: set[Path] = set()
    roots = [CLAUDE] + HOMEWIDE_PROJECTS
    for root in roots:
        if not root.exists():
            continue
        for cg in root.rglob("claim_graph.jsonl"):
            if any(p in {".venv", "tests", "fixtures", "composed", "node_modules"} for p in cg.parts):
                continue
            seen.add(cg.parent)
    return sorted(seen)


def freshness_preflight(dossiers: list[Path]) -> dict[str, str]:
    """Re-run research_kb_export.py for any dossier whose claim_graph.jsonl is newer than its inbox JSONL.

    Returns {slug: status_message}.
    """
    py = TK / ".venv" / "bin" / "python"
    export_script = TK / "scripts" / "research_kb_export.py"
    inbox_dir = INBOX / "research_toolkit"
    results: dict[str, str] = {}
    for d in dossiers:
        cg = d / "claim_graph.jsonl"
        if not cg.exists():
            continue
        slug = d.name
        # The export slug logic in research_kb_export.py uses the dir basename
        inbox_file = inbox_dir / f"{slug}.jsonl"
        # Determine if re-export is needed
        if not inbox_file.exists():
            need = True
            reason = "no inbox file"
        elif cg.stat().st_mtime > inbox_file.stat().st_mtime:
            need = True
            reason = "claim_graph newer"
        else:
            need = False
            reason = "current"
        if need:
            print(f"  re-exporting {slug} ({reason})", file=sys.stderr)
            try:
                out = subprocess.run(
                    [str(py), str(export_script), str(d)],
                    capture_output=True, text=True, timeout=60,
                )
                if out.returncode == 0:
                    results[slug] = "re-exported"
                else:
                    results[slug] = f"export-failed ({out.stderr[:80]})"
            except Exception as e:
                results[slug] = f"export-error ({type(e).__name__})"
        else:
            results[slug] = "current"
    return results


def build_manifest(dossiers: list[Path], cache_health_excerpt: str | None = None) -> dict:
    """Build the MANIFEST.txt content (returned as dict; rendered separately)."""
    manifest: dict = {
        "schema_version": 1,
        "tool": "bundle_research_corpus.py",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "B",
        "toolkit_git_rev": get_toolkit_git_rev(),
        "dossiers": [],
        "shared_cache": {},
        "inbox": {},
        "catalogue": [],
        "homewide_projects": [],
    }
    # Dossiers
    for d in dossiers:
        cg = d / "claim_graph.jsonl"
        cg_sha = sha256_of_file(cg) if cg.exists() else None
        cg_records = sum(1 for _ in cg.open()) if cg.exists() else 0
        manifest["dossiers"].append({
            "slug": d.name,
            "path": str(d.relative_to(HOME)),
            "claim_graph_records": cg_records,
            "claim_graph_sha256": cg_sha,
        })

    # Shared cache summary
    if SHARED_CACHE.exists():
        blobs = list((SHARED_CACHE / "blobs" / "sha256").iterdir()) if (SHARED_CACHE / "blobs" / "sha256").exists() else []
        total_bytes = sum(p.stat().st_size for p in blobs)
        manifest["shared_cache"] = {
            "path": str(SHARED_CACHE.relative_to(HOME)),
            "blob_count": len(blobs),
            "total_bytes": total_bytes,
        }

    # Inbox summary
    inbox_files = list((INBOX / "research_toolkit").glob("*.jsonl")) if (INBOX / "research_toolkit").exists() else []
    manifest["inbox"] = {
        "path": str(INBOX.relative_to(HOME)),
        "file_count": len(inbox_files),
        "file_sizes": {f.name: f.stat().st_size for f in inbox_files},
        "total_records": sum(sum(1 for _ in f.open()) for f in inbox_files),
    }

    # Catalogue
    for c in CATALOGUE:
        if c.exists():
            manifest["catalogue"].append({"path": str(c.relative_to(HOME)), "bytes": c.stat().st_size})

    # Home-wide projects
    for p in HOMEWIDE_PROJECTS:
        if p.exists():
            manifest["homewide_projects"].append({"path": str(p.relative_to(HOME))})

    if cache_health_excerpt:
        manifest["cache_health_excerpt"] = cache_health_excerpt[:5000]  # bounded

    return manifest


def render_manifest(manifest: dict) -> str:
    lines = ["# Research Corpus Manifest\n"]
    lines.append(f"- generated_at: {manifest['generated_at']}")
    lines.append(f"- scope: {manifest['scope']}")
    lines.append(f"- toolkit_git_rev: `{manifest['toolkit_git_rev']}`\n")
    lines.append(f"## Dossiers ({len(manifest['dossiers'])} strict-live)\n")
    for d in manifest["dossiers"]:
        lines.append(f"- `{d['path']}` — {d['claim_graph_records']} claim_graph records — sha256 `{(d['claim_graph_sha256'] or '?')[:16]}`")
    lines.append("")
    sc = manifest["shared_cache"]
    if sc:
        lines.append(f"## Shared cache\n- path: `{sc['path']}`")
        lines.append(f"- blob_count: {sc['blob_count']}")
        lines.append(f"- total_bytes: {sc['total_bytes']:,} ({sc['total_bytes']/1024/1024:.1f} MiB)\n")
    ib = manifest["inbox"]
    if ib:
        lines.append(f"## Inbox\n- path: `{ib['path']}`")
        lines.append(f"- file_count: {ib['file_count']}")
        lines.append(f"- total_records: {ib['total_records']:,}\n")
    if manifest["catalogue"]:
        lines.append(f"## Catalogue\n")
        for c in manifest["catalogue"]:
            lines.append(f"- `{c['path']}` ({c['bytes']} bytes)")
    if manifest["homewide_projects"]:
        lines.append(f"\n## Home-wide projects\n")
        for p in manifest["homewide_projects"]:
            lines.append(f"- `{p['path']}`")
    return "\n".join(lines) + "\n"


def write_payload_paths_file(dossiers: list[Path], extra_files: list[Path], tmp_dir: Path) -> Path:
    """Write the path list for `tar -T`. Paths are relative to HOME so tar produces clean names."""
    paths_file = tmp_dir / "payload_paths.txt"
    with paths_file.open("w") as f:
        # Shared cache, inbox dirs (full)
        if SHARED_CACHE.exists():
            f.write(str(SHARED_CACHE.relative_to(HOME)) + "\n")
        if INBOX.exists():
            f.write(str(INBOX.relative_to(HOME)) + "\n")
        # Dossier dirs (full each)
        for d in dossiers:
            f.write(str(d.relative_to(HOME)) + "\n")
        # Home-wide project dirs (full each, exclusions filter cruft)
        for p in HOMEWIDE_PROJECTS:
            if p.exists():
                f.write(str(p.relative_to(HOME)) + "\n")
        # Catalogue
        for c in extra_files:
            if c.exists():
                f.write(str(c.relative_to(HOME)) + "\n")
    return paths_file


def build_tar(payload_paths: Path, manifest_path: Path, cache_health_path: Path | None,
              out_tarball: Path, dry_run: bool) -> None:
    cmd = ["tar", "czf", str(out_tarball), "-C", str(HOME), "-T", str(payload_paths)]
    for excl in EXCLUDES:
        cmd.extend(["--exclude", excl])
    # Add manifest + cache_health as top-level entries (relative to HOME they don't exist; copy first)
    work_dir = HOME / ".bundle_research_corpus_tmp"
    work_dir.mkdir(exist_ok=True)
    try:
        shutil.copy2(manifest_path, work_dir / "MANIFEST.txt")
        if cache_health_path and cache_health_path.exists():
            shutil.copy2(cache_health_path, work_dir / "cache_health.md")
        # Append the temp dir entries
        cmd.extend([str((work_dir / "MANIFEST.txt").relative_to(HOME))])
        if cache_health_path and cache_health_path.exists():
            cmd.extend([str((work_dir / "cache_health.md").relative_to(HOME))])
        print(f"\nRunning: {' '.join(cmd[:6])} … (with {len(EXCLUDES)} exclusions)", file=sys.stderr)
        if dry_run:
            print(f"DRY-RUN: not executing tar; payload_paths file is at {payload_paths}", file=sys.stderr)
            return
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
        if result.returncode != 0:
            print(f"TAR FAILED: {result.stderr}", file=sys.stderr)
            raise RuntimeError("tar failed")
    finally:
        if work_dir.exists():
            shutil.rmtree(work_dir, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scope", choices=["B"], default="B")  # only B locked
    ap.add_argument("--out", type=Path, default=CLAUDE)
    ap.add_argument("--dry-run", action="store_true", help="Build manifest + path list but don't tar")
    ap.add_argument("--skip-freshness", action="store_true", help="Don't re-run inbox exports")
    args = ap.parse_args()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_tarball = args.out / f"research_corpus_{today}.tar.gz"
    out_sha256 = args.out / f"research_corpus_{today}.tar.gz.sha256"
    out_manifest = args.out / f"research_corpus_{today}.manifest.txt"

    print("[1/5] Finding strict-live dossiers…", file=sys.stderr)
    dossiers = find_strict_live_dossiers()
    print(f"      found {len(dossiers)}", file=sys.stderr)

    if not args.skip_freshness:
        print("[2/5] Freshness pre-flight (re-export stale inbox entries)…", file=sys.stderr)
        results = freshness_preflight(dossiers)
        stale = sum(1 for v in results.values() if v == "re-exported")
        failed = sum(1 for v in results.values() if "fail" in v or "error" in v)
        print(f"      re-exported {stale}, failed {failed}", file=sys.stderr)
    else:
        print("[2/5] SKIPPED freshness pre-flight", file=sys.stderr)

    print("[3/5] Reading cache_health.md (if present) for embed…", file=sys.stderr)
    ch_path = CLAUDE / "cache_health.md"
    ch_text = ch_path.read_text() if ch_path.exists() else None
    print(f"      cache_health.md: {'present' if ch_text else 'absent'}", file=sys.stderr)

    print("[4/5] Building manifest…", file=sys.stderr)
    manifest = build_manifest(dossiers, cache_health_excerpt=ch_text)
    out_manifest.write_text(render_manifest(manifest))
    print(f"      WROTE {out_manifest}", file=sys.stderr)

    print("[5/5] Building tar…", file=sys.stderr)
    with tempfile.TemporaryDirectory() as tmp:
        payload_paths = write_payload_paths_file(dossiers, CATALOGUE, Path(tmp))
        build_tar(payload_paths, out_manifest, ch_path, out_tarball, dry_run=args.dry_run)
    if args.dry_run:
        print(f"\nDRY-RUN done. Manifest at {out_manifest}. No tarball.", file=sys.stderr)
        return 0

    # Sha256 the tarball
    print("\n[+] Computing tarball sha256…", file=sys.stderr)
    sha = sha256_of_file(out_tarball)
    out_sha256.write_text(f"{sha}  {out_tarball.name}\n")
    print(f"\n=== SUMMARY ===", file=sys.stderr)
    print(f"Tarball: {out_tarball}  ({out_tarball.stat().st_size:,} bytes = {out_tarball.stat().st_size/1024/1024:.1f} MiB)", file=sys.stderr)
    print(f"Sha256:  {sha}", file=sys.stderr)
    print(f"Sidecar: {out_sha256}", file=sys.stderr)
    print(f"Manifest: {out_manifest}", file=sys.stderr)
    print(f"\nDesktop verification:", file=sys.stderr)
    print(f"  shasum -a 256 -c {out_sha256.name}", file=sys.stderr)
    print(f"  tar tzf {out_tarball.name} | wc -l   # file count", file=sys.stderr)
    print(f"  tar tzf {out_tarball.name} | grep -c claim_graph.jsonl   # should match dossier count", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

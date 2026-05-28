#!/usr/bin/env python3
"""retry_escalations.py — Wayback Machine recovery pass for escalate_to_manual fetches.

Fix B from Phase 1. For each gather_trace fetch with `decision: escalate_to_manual`
(typically paywalled landmarks the original gather agent couldn't access), this script:

1. Queries the Wayback Machine availability API for the original source URL.
2. If a snapshot exists, downloads it and caches to the shared cache (sha256-content-addressed).
3. Reports successes + failures.

By default does NOT modify gather_trace.yml / cache_manifest.yml / bib_ledger.yml —
prints a recovery report you can review. Pass `--update-manifests` to apply changes
(adds new cache_manifest entries pointing to recovered Wayback captures + flips the
gather_trace decision to `accept_via_wayback`).

This is a MVP — tries Wayback only. Future variants can add arxiv-vanity, author
homepages, mirror domains.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any

import yaml

HOME = Path.home()
SHARED_CACHE = HOME / "Claude" / "research_cache"
WAYBACK_AVAIL = "https://archive.org/wayback/available?url={url}"
HTTP_TIMEOUT = 30  # seconds
USER_AGENT = "research-toolkit/retry_escalations (research dossier recovery)"

ROOTS = [HOME / "Claude", HOME / "post_transformers", HOME / "guides",
         HOME / "guides-experimentation", HOME / "eval-toolkit",
         HOME / "rl_and_control", HOME / "double_ml_time_series", HOME / "prompt-injection-v4"]


def find_dossier_dirs() -> list[Path]:
    seen = set()
    for root in ROOTS:
        if not root.exists():
            continue
        for cg in root.rglob("claim_graph.jsonl"):
            if any(p in {".venv", "tests", "fixtures", "composed", "node_modules"} for p in cg.parts):
                continue
            seen.add(cg.parent)
    return sorted(seen)


def collect_escalations(dossier_dirs: list[Path]) -> list[dict[str, Any]]:
    out = []
    for d in dossier_dirs:
        gt = d / "gather_trace.yml"
        if not gt.exists():
            continue
        try:
            with gt.open() as f:
                data = yaml.safe_load(f) or {}
        except Exception:
            continue
        for idx, fetch in enumerate(data.get("fetches") or []):
            if fetch.get("decision") == "escalate_to_manual":
                out.append({
                    "dossier_dir": d,
                    "dossier_name": d.name,
                    "fetch_index": idx,
                    "fetch_id": fetch.get("fetch_id"),
                    "url": fetch.get("source_url"),
                    "reason": (fetch.get("reason") or "")[:200],
                    "bibkey": fetch.get("assigned_bibkey"),
                    "sub_area": (fetch.get("sub_area") or "")[:80],
                })
    return out


def fetch_url(url: str, *, timeout: int = HTTP_TIMEOUT) -> tuple[int, bytes, str]:
    """Return (status, body, content_type). Raises on network failure."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read(), resp.headers.get("Content-Type", "application/octet-stream")


def wayback_check(url: str) -> str | None:
    """Return a Wayback snapshot URL if available, else None."""
    api = WAYBACK_AVAIL.format(url=urllib.parse.quote(url, safe=":/?&="))
    try:
        status, body, _ = fetch_url(api, timeout=15)
        if status != 200:
            return None
        data = json.loads(body.decode("utf-8", errors="replace"))
    except Exception:
        return None
    snap = (data.get("archived_snapshots") or {}).get("closest")
    if not snap or snap.get("available") is not True:
        return None
    return snap.get("url")


def extract_text(raw: bytes, content_type: str) -> str:
    """Best-effort text extraction (HTML via BS4, PDF via cache_source cascade if available)."""
    ct = content_type.lower()
    if "pdf" in ct:
        try:
            sys.path.insert(0, str(HOME / "Claude" / "research_toolkit"))
            from scripts import cache_source
            text, _, _ = cache_source._extract_pdf_text(raw)
            return text or ""
        except Exception:
            return ""
    if "html" in ct or "xml" in ct or ct.startswith("text/"):
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(raw, "html.parser")
            for el in soup(["script", "style", "noscript"]):
                el.decompose()
            text = soup.get_text(separator=" ", strip=False)
            text = re.sub(r"\s+", " ", text)
            return text.strip()
        except Exception:
            return raw.decode("utf-8", errors="replace")
    return ""


def cache_blob(raw: bytes, text: str, source_url: str, content_type: str) -> str:
    """Save to shared cache (sha256-addressed). Returns sha256."""
    sha = hashlib.sha256(raw).hexdigest()
    blob_dir = SHARED_CACHE / "blobs" / "sha256"
    text_dir = SHARED_CACHE / "text" / "sha256"
    meta_dir = SHARED_CACHE / "metadata" / "sha256"
    blob_dir.mkdir(parents=True, exist_ok=True)
    text_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)
    blob_path = blob_dir / sha
    text_path = text_dir / f"{sha}.txt"
    meta_path = meta_dir / f"{sha}.json"
    if not blob_path.exists():
        blob_path.write_bytes(raw)
    if not text_path.exists() and text:
        text_path.write_text(text, encoding="utf-8")
    if not meta_path.exists():
        meta_path.write_text(json.dumps({
            "source_url": source_url,
            "content_type": content_type,
            "bytes": len(raw),
            "sha256": sha,
            "fetched_at": date.today().isoformat(),
            "fetch_method": "wayback_recovery",
        }, indent=2), encoding="utf-8")
    return sha


def update_dossier_metadata(esc: dict, sha: str, wayback_url: str, content_type: str, raw_bytes: int) -> None:
    """Append a new cache_manifest entry + flip gather_trace decision (with --update-manifests)."""
    dossier_dir: Path = esc["dossier_dir"]

    # 1) Append cache_manifest entry
    cm_path = dossier_dir / "cache_manifest.yml"
    if cm_path.exists():
        with cm_path.open() as f:
            cm = yaml.safe_load(f) or {}
        entries = cm.setdefault("entries", [])
        # Check if a manifest entry already exists for this sha (idempotent)
        if not any(e.get("sha256") == sha for e in entries):
            entries.append({
                "cache_id": f"cache_wayback_{sha[:16]}",
                "source_url": wayback_url,
                "fetched_at": date.today().isoformat(),
                "content_type": content_type,
                "bytes": raw_bytes,
                "sha256": sha,
                "raw_path": f"blobs/sha256/{sha}",
                "text_path": f"text/sha256/{sha}.txt",
                "metadata_path": f"metadata/sha256/{sha}.json",
                "restricted": False,
                "rights_status": "private_use",
                "extraction_status": "ok",
                "recovery_note": "Recovered from Wayback Machine after original source escalate_to_manual",
            })
            with cm_path.open("w") as f:
                yaml.safe_dump(cm, f, sort_keys=False, allow_unicode=True)

    # 2) Flip gather_trace decision
    gt_path = dossier_dir / "gather_trace.yml"
    if gt_path.exists():
        with gt_path.open() as f:
            gt = yaml.safe_load(f) or {}
        fetches = gt.get("fetches") or []
        idx = esc["fetch_index"]
        if 0 <= idx < len(fetches):
            fetches[idx]["decision"] = "accept_via_wayback"
            fetches[idx]["recovered_via_url"] = wayback_url
            fetches[idx]["recovered_at"] = date.today().isoformat()
            with gt_path.open("w") as f:
                yaml.safe_dump(gt, f, sort_keys=False, allow_unicode=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--update-manifests", action="store_true",
                    help="Apply changes to gather_trace + cache_manifest (default: report only)")
    ap.add_argument("--max", type=int, default=66, help="Max escalations to try (for sampling)")
    ap.add_argument("--out", type=Path, default=HOME / "Claude" / "retry_escalations_report.md")
    args = ap.parse_args()

    dossier_dirs = find_dossier_dirs()
    print(f"Scanning {len(dossier_dirs)} dossier dirs", file=sys.stderr)
    escalations = collect_escalations(dossier_dirs)
    print(f"Found {len(escalations)} escalate_to_manual entries", file=sys.stderr)
    escalations = escalations[: args.max]

    results = {"recovered": [], "no_wayback_snapshot": [], "fetch_failed": [], "extract_failed": []}
    for i, esc in enumerate(escalations):
        url = esc["url"]
        if not url:
            continue
        print(f"\n[{i+1}/{len(escalations)}] {esc['dossier_name']}: {url[:80]}", file=sys.stderr)
        wb = wayback_check(url)
        if not wb:
            results["no_wayback_snapshot"].append(esc)
            print(f"  no Wayback snapshot", file=sys.stderr)
            continue
        print(f"  Wayback: {wb[:80]}", file=sys.stderr)
        try:
            status, raw, ct = fetch_url(wb)
            if status != 200 or len(raw) < 200:
                results["fetch_failed"].append({**esc, "wayback_url": wb, "http_status": status, "size": len(raw)})
                print(f"  fetch failed: status={status} size={len(raw)}", file=sys.stderr)
                continue
        except Exception as e:
            results["fetch_failed"].append({**esc, "wayback_url": wb, "error": str(e)[:200]})
            print(f"  fetch error: {type(e).__name__}: {str(e)[:120]}", file=sys.stderr)
            continue
        text = extract_text(raw, ct)
        if not text:
            results["extract_failed"].append({**esc, "wayback_url": wb, "size": len(raw), "ct": ct})
            print(f"  extracted text empty (ct={ct})", file=sys.stderr)
            continue
        sha = cache_blob(raw, text, wb, ct)
        results["recovered"].append({**esc, "wayback_url": wb, "sha256": sha, "size": len(raw), "ct": ct, "text_len": len(text)})
        print(f"  cached sha={sha[:12]}… text={len(text)} bytes", file=sys.stderr)
        if args.update_manifests:
            try:
                update_dossier_metadata(esc, sha, wb, ct, len(raw))
                print(f"  manifest updated for {esc['dossier_name']}", file=sys.stderr)
            except Exception as e:
                print(f"  manifest update failed: {e}", file=sys.stderr)

    # Render report
    lines = [f"# Wayback Retry Report — {date.today().isoformat()}\n"]
    lines.append(f"Total escalations attempted: **{len(escalations)}**\n")
    lines.append(f"- recovered: **{len(results['recovered'])}**")
    lines.append(f"- no Wayback snapshot: **{len(results['no_wayback_snapshot'])}**")
    lines.append(f"- fetch failed: **{len(results['fetch_failed'])}**")
    lines.append(f"- extract failed: **{len(results['extract_failed'])}**")
    if args.update_manifests:
        lines.append(f"\n**Manifest updates: APPLIED** (gather_trace decisions flipped to accept_via_wayback; new cache_manifest entries added).\n")
    else:
        lines.append(f"\n**Manifest updates: DRY-RUN** (no changes). Re-run with --update-manifests to apply.\n")

    if results["recovered"]:
        lines.append(f"\n## Recovered ({len(results['recovered'])})\n")
        lines.append("| dossier | bibkey | original URL | wayback | sha |")
        lines.append("|---|---|---|---|---|")
        for r in results["recovered"]:
            lines.append(f"| {r['dossier_name']} | {r.get('bibkey') or '?'} | {(r['url'] or '')[:50]} | {r['wayback_url'][:50]} | `{r['sha256'][:12]}` |")
    if results["no_wayback_snapshot"]:
        lines.append(f"\n## No Wayback snapshot ({len(results['no_wayback_snapshot'])})\n")
        lines.append("| dossier | original URL | reason |")
        lines.append("|---|---|---|")
        for r in results["no_wayback_snapshot"][:30]:
            lines.append(f"| {r['dossier_name']} | {(r['url'] or '')[:60]} | {r['reason'][:80]} |")
    if results["fetch_failed"]:
        lines.append(f"\n## Wayback fetch failed ({len(results['fetch_failed'])})\n")
        for r in results["fetch_failed"][:15]:
            lines.append(f"- {r['dossier_name']}: {(r.get('wayback_url') or '')[:80]}  ({r.get('error') or 'http_status=' + str(r.get('http_status'))})")
    if results["extract_failed"]:
        lines.append(f"\n## Extract failed (cached blob but no text) ({len(results['extract_failed'])})\n")
        for r in results["extract_failed"]:
            lines.append(f"- {r['dossier_name']}: {(r.get('wayback_url') or '')[:80]}  (ct={r.get('ct')} size={r.get('size')})")

    args.out.write_text("\n".join(lines) + "\n")
    print(f"\nWROTE {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

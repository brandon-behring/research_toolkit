#!/usr/bin/env python3
"""reextract_low_quality.py — re-extract text from blobs flagged by cache_health.py.

Fix C from Phase 1. Targets blobs with:
  - tiny text (text <200 bytes when blob is >50 KB) — usually PDFs whose initial
    extraction returned a stub; re-run the v2.3 PDF cascade (pdfplumber + Docling).
  - collapsed-space text (long runs without whitespace) — usually HTML pages whose
    extractor stripped whitespace via BeautifulSoup's default `.get_text()` collapse.
    Re-run with BeautifulSoup's `.get_text(separator=' ', strip=True)` which preserves
    inter-element whitespace.

Reads the shared cache, finds flagged blobs, re-extracts in place (writing to the
existing text/sha256/<sha>.txt), and records before/after stats. Idempotent.
Dry-run by default.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

HOME = Path.home()
SHARED_CACHE = HOME / "Claude" / "research_cache"
TK = HOME / "Claude" / "research_toolkit"

# Reuse cache_source's PDF cascade
sys.path.insert(0, str(TK))
try:
    from scripts import cache_source
    _PDF_EXTRACT = cache_source._extract_pdf_text
except Exception as e:
    print(f"WARN: cache_source PDF cascade unavailable ({e}); PDF re-extraction disabled", file=sys.stderr)
    _PDF_EXTRACT = None

try:
    from bs4 import BeautifulSoup
    _BS4_OK = True
except Exception:
    _BS4_OK = False
    print("WARN: BeautifulSoup not installed; HTML re-extraction disabled", file=sys.stderr)


def html_extract(raw: bytes) -> str:
    """Re-extract HTML preserving inter-element whitespace."""
    soup = BeautifulSoup(raw, "html.parser")
    # Drop scripts/styles
    for el in soup(["script", "style", "noscript"]):
        el.decompose()
    # separator=' ' between elements, then collapse runs of whitespace
    text = soup.get_text(separator=" ", strip=False)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r" \n ", "\n", text)
    return text.strip()


def json_extract(raw: bytes) -> str:
    """For JSON blobs: pretty-print + extract string values for searchability."""
    import json as _json
    try:
        data = _json.loads(raw.decode("utf-8", errors="replace"))
        # Concatenate every string value reachable in the tree (basic but works for searchability)
        out = []
        def walk(x):
            if isinstance(x, str):
                out.append(x)
            elif isinstance(x, dict):
                for k, v in x.items():
                    out.append(str(k))
                    walk(v)
            elif isinstance(x, list):
                for v in x: walk(v)
            elif x is not None:
                out.append(str(x))
        walk(data)
        return "\n".join(out)
    except Exception:
        return raw.decode("utf-8", errors="replace")


def collect_sha_meta() -> dict[str, dict]:
    """Map sha256 -> {content_type, source_url, manifest_paths}."""
    meta: dict[str, dict] = {}
    for cm in HOME.rglob("cache_manifest.yml"):
        if any(p in {".venv", "tests", "fixtures", "composed", "node_modules"} for p in cm.parts):
            continue
        try:
            with cm.open() as f:
                data = yaml.safe_load(f) or {}
        except Exception:
            continue
        for entry in data.get("entries") or []:
            sha = entry.get("sha256")
            if sha and sha not in meta:
                meta[sha] = {
                    "content_type": (entry.get("content_type") or "").lower(),
                    "source_url": entry.get("source_url") or "",
                }
    return meta


def find_flagged() -> dict[str, list[str]]:
    """Re-derive flagged shas from the shared cache."""
    out = {"empty": [], "tiny_pdf": [], "tiny_other": [], "collapsed_html": [], "collapsed_json": [], "collapsed_other": []}
    text_dir = SHARED_CACHE / "text" / "sha256"
    blob_dir = SHARED_CACHE / "blobs" / "sha256"
    sha_meta = collect_sha_meta()
    for tf in text_dir.glob("*.txt"):
        sha = tf.stem
        size = tf.stat().st_size
        blob = blob_dir / sha
        blob_size = blob.stat().st_size if blob.exists() else 0
        ct = sha_meta.get(sha, {}).get("content_type", "")
        is_pdf = "pdf" in ct
        is_html = "html" in ct or "text/" in ct and "json" not in ct
        is_json = "json" in ct
        if size == 0:
            out["empty"].append(sha)
            continue
        if size < 200 and blob_size > 50_000:
            (out["tiny_pdf"] if is_pdf else out["tiny_other"]).append(sha)
            continue
        # collapsed: check first 50KB
        try:
            chunk = tf.read_bytes()[:50_000]
            text = chunk.decode("utf-8", errors="replace")
            if re.search(r"\S{2000,}", text):
                if is_html:
                    out["collapsed_html"].append(sha)
                elif is_json:
                    out["collapsed_json"].append(sha)
                else:
                    out["collapsed_other"].append(sha)
        except Exception:
            pass
    return out


def reextract_one(sha: str, kind: str) -> tuple[bool, str, int, int]:
    """Re-extract a single sha. Returns (ok, status, before_bytes, after_bytes)."""
    blob = SHARED_CACHE / "blobs" / "sha256" / sha
    tf = SHARED_CACHE / "text" / "sha256" / f"{sha}.txt"
    if not blob.exists():
        return False, "blob_missing", 0, 0
    raw = blob.read_bytes()
    before = tf.stat().st_size if tf.exists() else 0

    if kind in ("tiny_pdf",):
        if not _PDF_EXTRACT:
            return False, "no_pdf_cascade", before, 0
        text, status, warnings = _PDF_EXTRACT(raw)
        if status == "raw_only" or not text or len(text) < 200:
            return False, f"cascade_returned_{status}", before, len(text or "")
        return True, status, before, len(text)

    if kind in ("collapsed_html",):
        if not _BS4_OK:
            return False, "no_bs4", before, 0
        try:
            text = html_extract(raw)
        except Exception as e:
            return False, f"bs4_error_{type(e).__name__}", before, 0
        if len(text) < 100:
            return False, "html_extract_too_short", before, len(text)
        return True, "html_re_extracted", before, len(text)

    if kind in ("collapsed_json",):
        try:
            text = json_extract(raw)
        except Exception as e:
            return False, f"json_error_{type(e).__name__}", before, 0
        return True, "json_re_extracted", before, len(text)

    return False, f"unsupported_kind_{kind}", before, 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--execute", action="store_true", help="Actually rewrite text/<sha>.txt (default: dry-run)")
    ap.add_argument("--only", choices=["tiny_pdf", "collapsed_html", "collapsed_json"],
                    action="append", default=[], help="Only re-extract these kinds (repeatable)")
    args = ap.parse_args()

    flagged = find_flagged()
    print("\n=== flagged blobs ===", file=sys.stderr)
    for k, v in flagged.items():
        print(f"  {k}: {len(v)}", file=sys.stderr)

    if not args.only:
        kinds = ["tiny_pdf", "collapsed_html", "collapsed_json"]
    else:
        kinds = args.only

    print(f"\nMode: {'EXECUTE' if args.execute else 'DRY-RUN'}  kinds: {kinds}", file=sys.stderr)
    stats = {k: {"attempted": 0, "ok": 0, "fail": 0, "sample_failures": []} for k in kinds}

    for kind in kinds:
        for sha in flagged.get(kind, []):
            stats[kind]["attempted"] += 1
            ok, status, before, after = reextract_one(sha, kind)
            if not ok:
                stats[kind]["fail"] += 1
                if len(stats[kind]["sample_failures"]) < 5:
                    stats[kind]["sample_failures"].append(f"{sha[:12]}…: {status}")
                continue
            if args.execute:
                # Write the new text
                tf = SHARED_CACHE / "text" / "sha256" / f"{sha}.txt"
                tf.write_text((html_extract(SHARED_CACHE.joinpath("blobs/sha256", sha).read_bytes())
                               if kind == "collapsed_html"
                               else json_extract(SHARED_CACHE.joinpath("blobs/sha256", sha).read_bytes())
                               if kind == "collapsed_json"
                               else _PDF_EXTRACT(SHARED_CACHE.joinpath("blobs/sha256", sha).read_bytes())[0]),
                              encoding="utf-8")
            stats[kind]["ok"] += 1

    print("\n=== results ===", file=sys.stderr)
    for kind, s in stats.items():
        print(f"  {kind}: attempted={s['attempted']} ok={s['ok']} fail={s['fail']}", file=sys.stderr)
        for f in s["sample_failures"]:
            print(f"    - {f}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

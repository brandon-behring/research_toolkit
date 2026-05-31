#!/usr/bin/env python3
"""retry_escalations_v2.py — multi-strategy recovery beyond Wayback.

Stage-2 of fix B. After `retry_escalations.py` exhausted Wayback Machine, this
pass tries additional strategies on the still-unrecovered escalate_to_manual
entries. Strategies are chained: the first one that gets usable text wins.

Strategies (in order):
  1. Playwright direct fetch — handles JS-rendered + Cloudflare/Incapsula
     bot-protected sites. Re-uses `cache_source._fetch_via_playwright`.
  2. Crossref API — for any URL containing a DOI, fetch
     `api.crossref.org/works/{doi}` → JSON with title/abstract/authors.
  3. arXiv abs substitution — if the URL is `arxiv.org/pdf/X` (or similar
     PDF variant), try the HTML abs page at `arxiv.org/abs/X`.
  4. arxiv-vanity HTML rendering — `arxiv-vanity.com/papers/{id}/` for
     arXiv URLs (often more extractable than the raw PDF).
  5. HTTPS variant — if original was HTTP, try HTTPS.

Same semantics as v1: dry-run by default, `--update-manifests` to apply.
Idempotent — re-running skips already-recovered URLs (those now marked
`accept_via_wayback` or `accept_via_playwright` etc. in gather_trace).
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
HTTP_TIMEOUT = 30
USER_AGENT = "research-toolkit/retry_v2 (multi-strategy dossier recovery)"
ROOTS = [HOME / "Claude", HOME / "post_transformers", HOME / "guides",
         HOME / "guides-experimentation", HOME / "eval-toolkit",
         HOME / "rl_and_control", HOME / "double_ml_time_series",
         HOME / "prompt-injection-v4"]

# Recovered-via decisions from stage 1 or v2 — skip these on re-run
ALREADY_RECOVERED = {"accept", "accept_via_wayback", "accept_via_playwright",
                     "accept_via_crossref", "accept_via_arxiv_abs",
                     "accept_via_arxiv_vanity", "accept_via_https"}

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators._common import ARXIV_ID_RE, ARXIV_OLD_ID_RE, DOI_RE


# Reuse cache_source
sys.path.insert(0, str(HOME / "Claude" / "research_toolkit"))
try:
    from scripts import cache_source
    _PDF_EXTRACT = cache_source._extract_pdf_text
    _PLAYWRIGHT = cache_source._fetch_via_playwright
except Exception as e:
    print(f"WARN: cache_source unavailable: {e}", file=sys.stderr)
    _PDF_EXTRACT = None
    _PLAYWRIGHT = None


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


def collect_unrecovered(dossier_dirs: list[Path]) -> list[dict[str, Any]]:
    """Get escalate_to_manual entries that are NOT already recovered."""
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
            dec = fetch.get("decision")
            if dec in ALREADY_RECOVERED:
                continue
            if dec != "escalate_to_manual":
                continue
            out.append({
                "dossier_dir": d, "dossier_name": d.name, "fetch_index": idx,
                "fetch_id": fetch.get("fetch_id"), "url": fetch.get("source_url"),
                "reason": (fetch.get("reason") or "")[:200],
                "bibkey": fetch.get("assigned_bibkey"),
            })
    return out


def fetch_urllib(url: str, timeout: int = HTTP_TIMEOUT) -> tuple[int, bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read(), resp.headers.get("Content-Type", "application/octet-stream")


def extract_text(raw: bytes, content_type: str) -> str:
    """HTML via BS4, PDF via cascade, JSON literal, else best-effort decode."""
    ct = content_type.lower()
    if "pdf" in ct:
        if _PDF_EXTRACT:
            try:
                text, _, _ = _PDF_EXTRACT(raw)
                return text or ""
            except Exception:
                pass
        return ""
    if "html" in ct or "xml" in ct or ct.startswith("text/"):
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(raw, "html.parser")
            for el in soup(["script", "style", "noscript"]):
                el.decompose()
            text = soup.get_text(separator=" ", strip=False)
            return re.sub(r"\s+", " ", text).strip()
        except Exception:
            return raw.decode("utf-8", errors="replace")
    if "json" in ct:
        try:
            data = json.loads(raw.decode("utf-8", errors="replace"))
            return json.dumps(data, indent=2)
        except Exception:
            return raw.decode("utf-8", errors="replace")
    return ""


def cache_blob(raw: bytes, text: str, source_url: str, content_type: str, method: str) -> str:
    sha = hashlib.sha256(raw).hexdigest()
    for kind, suffix in [("blobs", ""), ("text", ".txt"), ("metadata", ".json")]:
        (SHARED_CACHE / kind / "sha256").mkdir(parents=True, exist_ok=True)
    blob_path = SHARED_CACHE / "blobs" / "sha256" / sha
    text_path = SHARED_CACHE / "text" / "sha256" / f"{sha}.txt"
    meta_path = SHARED_CACHE / "metadata" / "sha256" / f"{sha}.json"
    if not blob_path.exists():
        blob_path.write_bytes(raw)
    if not text_path.exists() and text:
        text_path.write_text(text, encoding="utf-8")
    if not meta_path.exists():
        meta_path.write_text(json.dumps({
            "source_url": source_url, "content_type": content_type, "bytes": len(raw),
            "sha256": sha, "fetched_at": date.today().isoformat(), "fetch_method": method,
        }, indent=2), encoding="utf-8")
    return sha


# ──────── strategies ────────

def strategy_playwright(url: str) -> tuple[str, bytes, str] | None:
    """Headless Chromium fetch — handles JS-rendered + many bot-protected sites."""
    if not _PLAYWRIGHT:
        return None
    try:
        status, raw, ct, _etag, _last_mod = _PLAYWRIGHT(url)
        if status == 200 and len(raw) > 200:
            return ("playwright", raw, ct)
    except Exception:
        return None
    return None


def strategy_crossref(url: str) -> tuple[str, bytes, str] | None:
    """For any URL containing a DOI, fetch Crossref API JSON for title/abstract."""
    m = DOI_RE.search(url)
    if not m:
        return None
    doi = m.group(1).rstrip("/.,;")
    crossref_url = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='/')}"
    try:
        status, raw, _ct = fetch_urllib(crossref_url, timeout=20)
        if status == 200 and len(raw) > 200:
            return ("crossref", raw, "application/json")
    except Exception:
        return None
    return None


def strategy_arxiv_abs(url: str) -> tuple[str, bytes, str] | None:
    """If URL is arxiv PDF or anything-not-abs, try the abs HTML page."""
    if "arxiv.org" not in url.lower():
        return None
    m = ARXIV_ID_RE.search(url) or ARXIV_OLD_ID_RE.search(url)
    if not m:
        return None
    arxiv_id = re.sub(r"v\d+$", "", m.group(1))
    abs_url = f"https://arxiv.org/abs/{arxiv_id}"
    if url == abs_url:
        return None  # same URL — already tried
    try:
        status, raw, ct = fetch_urllib(abs_url, timeout=20)
        if status == 200 and len(raw) > 500:
            return ("arxiv_abs", raw, ct)
    except Exception:
        return None
    return None


def strategy_arxiv_vanity(url: str) -> tuple[str, bytes, str] | None:
    """arxiv-vanity renders arXiv papers as clean HTML."""
    if "arxiv.org" not in url.lower():
        return None
    m = ARXIV_ID_RE.search(url) or ARXIV_OLD_ID_RE.search(url)
    if not m:
        return None
    arxiv_id = re.sub(r"v\d+$", "", m.group(1))
    vanity_url = f"https://www.arxiv-vanity.com/papers/{arxiv_id}/"
    try:
        status, raw, ct = fetch_urllib(vanity_url, timeout=20)
        if status == 200 and len(raw) > 1000:
            return ("arxiv_vanity", raw, ct)
    except Exception:
        return None
    return None


def strategy_https_swap(url: str) -> tuple[str, bytes, str] | None:
    if not url.lower().startswith("http://"):
        return None
    https_url = "https://" + url[7:]
    try:
        status, raw, ct = fetch_urllib(https_url, timeout=20)
        if status == 200 and len(raw) > 200:
            return ("https_swap", raw, ct)
    except Exception:
        return None
    return None


STRATEGIES = [
    ("playwright", strategy_playwright),
    ("crossref", strategy_crossref),
    ("arxiv_abs", strategy_arxiv_abs),
    ("arxiv_vanity", strategy_arxiv_vanity),
    ("https_swap", strategy_https_swap),
]


def update_dossier_metadata(esc: dict, sha: str, source_url: str, content_type: str,
                            raw_bytes: int, method: str) -> None:
    dossier_dir: Path = esc["dossier_dir"]
    cm_path = dossier_dir / "cache_manifest.yml"
    if cm_path.exists():
        with cm_path.open() as f:
            cm = yaml.safe_load(f) or {}
        entries = cm.setdefault("entries", [])
        if not any(e.get("sha256") == sha for e in entries):
            entries.append({
                "cache_id": f"cache_{method}_{sha[:16]}",
                "source_url": source_url,
                "fetched_at": date.today().isoformat(),
                "content_type": content_type, "bytes": raw_bytes, "sha256": sha,
                "raw_path": f"blobs/sha256/{sha}",
                "text_path": f"text/sha256/{sha}.txt",
                "metadata_path": f"metadata/sha256/{sha}.json",
                "restricted": False, "rights_status": "private_use",
                "extraction_status": "ok",
                "recovery_note": f"Recovered via {method} after original source escalate_to_manual",
            })
            with cm_path.open("w") as f:
                yaml.safe_dump(cm, f, sort_keys=False, allow_unicode=True)
    gt_path = dossier_dir / "gather_trace.yml"
    if gt_path.exists():
        with gt_path.open() as f:
            gt = yaml.safe_load(f) or {}
        fetches = gt.get("fetches") or []
        idx = esc["fetch_index"]
        if 0 <= idx < len(fetches):
            fetches[idx]["decision"] = f"accept_via_{method}"
            fetches[idx]["recovered_via_url"] = source_url
            fetches[idx]["recovered_at"] = date.today().isoformat()
            with gt_path.open("w") as f:
                yaml.safe_dump(gt, f, sort_keys=False, allow_unicode=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--update-manifests", action="store_true",
                    help="Apply changes (default: report-only)")
    ap.add_argument("--max", type=int, default=999)
    ap.add_argument("--skip", default="", help="Comma-separated strategy names to skip")
    ap.add_argument("--out", type=Path, default=HOME / "Claude" / "retry_escalations_v2_report.md")
    args = ap.parse_args()
    skip_set = {s.strip() for s in args.skip.split(",") if s.strip()}

    dossier_dirs = find_dossier_dirs()
    print(f"Scanning {len(dossier_dirs)} dossier dirs", file=sys.stderr)
    unrecovered = collect_unrecovered(dossier_dirs)
    print(f"Unrecovered escalate_to_manual after stage 1: {len(unrecovered)}", file=sys.stderr)
    unrecovered = unrecovered[: args.max]

    results = {"recovered": [], "all_strategies_failed": []}
    per_strategy = collections.Counter()
    for i, esc in enumerate(unrecovered):
        url = esc["url"]
        if not url:
            continue
        print(f"\n[{i+1}/{len(unrecovered)}] {esc['dossier_name']}: {url[:80]}", file=sys.stderr)
        recovered = False
        for strat_name, strat_fn in STRATEGIES:
            if strat_name in skip_set:
                continue
            print(f"  trying {strat_name}…", file=sys.stderr)
            try:
                res = strat_fn(url)
            except Exception as e:
                print(f"    {strat_name} error: {type(e).__name__}: {str(e)[:80]}", file=sys.stderr)
                continue
            if not res:
                continue
            method, raw, ct = res
            text = extract_text(raw, ct)
            if not text or len(text) < 100:
                print(f"    {strat_name} got raw={len(raw)} but text too small ({len(text)})", file=sys.stderr)
                continue
            sha = cache_blob(raw, text, url, ct, method)
            per_strategy[method] += 1
            results["recovered"].append({**esc, "method": method, "sha256": sha,
                                          "raw_bytes": len(raw), "text_bytes": len(text), "ct": ct})
            print(f"    ✓ recovered via {strat_name}: sha={sha[:12]}… text={len(text)} bytes", file=sys.stderr)
            if args.update_manifests:
                try:
                    update_dossier_metadata(esc, sha, url, ct, len(raw), method)
                except Exception as e:
                    print(f"    manifest update failed: {e}", file=sys.stderr)
            recovered = True
            break
        if not recovered:
            results["all_strategies_failed"].append(esc)

    # Report
    lines = [f"# Multi-strategy Retry Report — {date.today().isoformat()}\n"]
    lines.append(f"Unrecovered after stage 1 (Wayback): **{len(unrecovered)}**\n")
    lines.append(f"- recovered by v2: **{len(results['recovered'])}**")
    lines.append(f"- all strategies failed: **{len(results['all_strategies_failed'])}**")
    lines.append(f"\n## Per-strategy success counts\n")
    for s, n in per_strategy.most_common():
        lines.append(f"- {s}: {n}")
    if results["recovered"]:
        lines.append(f"\n## Recovered\n| dossier | bibkey | strategy | original URL | sha |")
        lines.append("|---|---|---|---|---|")
        for r in results["recovered"]:
            lines.append(f"| {r['dossier_name']} | {r.get('bibkey') or '?'} | {r['method']} | {(r['url'] or '')[:50]} | `{r['sha256'][:12]}` |")
    if results["all_strategies_failed"]:
        lines.append(f"\n## All strategies failed ({len(results['all_strategies_failed'])})\n")
        lines.append("| dossier | URL | reason |")
        lines.append("|---|---|---|")
        for r in results["all_strategies_failed"]:
            lines.append(f"| {r['dossier_name']} | {(r['url'] or '')[:60]} | {(r.get('reason') or '')[:80]} |")

    args.out.write_text("\n".join(lines) + "\n")
    print(f"\nWROTE {args.out}", file=sys.stderr)
    print(f"v2 stage recovered: {len(results['recovered'])}/{len(unrecovered)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

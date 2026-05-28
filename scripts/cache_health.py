#!/usr/bin/env python3
"""cache_health.py — read-only audit of the shared research cache + per-dossier metadata.

Sweeps the shared cache (~/Claude/research_cache) + every dossier's cache_manifest.yml /
bib_ledger.yml / evidence_ledger.yml / gather_trace.yml across ~/Claude/research_* and
the home-wide research project roots; writes a markdown health report.

Per the locked plan (Phase 1a) the report covers 9 sections:
  1. Cache contents (blob/text/metadata counts + missing counterparts)
  2. Orphans (blobs not referenced by any cache_manifest)
  3. Dangling refs (bib_ledger entries whose URL/sha256 are not cached)
  4. Integrity (sha256(content) == filename on a sample)
  5. Extraction red flags (empty / tiny / non-printable / collapsed-space / garbled-unicode)
  6. Per-dossier coverage (% of bib entries with a cached primary)
  7. Escalation tally (gather_trace decisions other than accept)
  8. Local-vs-shared (dossier dirs with their own ./cache/ instead of using shared)
  9. Duplicate suspects (arXiv ID / DOI appearing under multiple sha256)

Usage:
  python cache_health.py [--cache-root ~/Claude/research_cache]
                         [--out ~/Claude/cache_health.md]
                         [--integrity-sample 50]

Pure stdlib + pyyaml (already in the toolkit venv). Read-only — never modifies anything.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import random
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("FATAL: pyyaml not installed. Use the toolkit venv:", file=sys.stderr)
    print("  ~/Claude/research_toolkit/.venv/bin/python", file=sys.stderr)
    sys.exit(2)

HOME = Path.home()
DEFAULT_CACHE_ROOT = HOME / "Claude" / "research_cache"
DEFAULT_OUT = HOME / "Claude" / "cache_health.md"

# Dossier roots to sweep — plan scope B.
DOSSIER_ROOT_GLOBS = [
    HOME / "Claude",  # the ~/Claude/research_* dirs
    HOME / "post_transformers",
    HOME / "guides",
    HOME / "guides-experimentation",
    HOME / "eval-toolkit",
    HOME / "rl_and_control",
    HOME / "double_ml_time_series",
    HOME / "prompt-injection-v4",
]

# Extraction statuses considered "good" — anything else flagged.
HEALTHY_EXTRACTION = {"ok", "ok_text_only", "rich"}
# Decisions considered "successful" in gather_trace — anything else flagged.
HEALTHY_DECISIONS = {"accept"}

ARXIV_ID_RE = re.compile(r"arxiv\.org/abs/([0-9]{4}\.[0-9]{4,5}(?:v\d+)?)", re.I)
DOI_RE = re.compile(r"\b(10\.\d{4,9}/[-._;()/:A-Z0-9]+)\b", re.I)


def find_dossier_dirs() -> list[Path]:
    """Find every directory containing a claim_graph.jsonl across the scope-B roots."""
    seen: set[Path] = set()
    for root in DOSSIER_ROOT_GLOBS:
        if not root.exists():
            continue
        for cg in root.rglob("claim_graph.jsonl"):
            # Skip toolkit fixtures / composed projects / .venv / tests
            parts = cg.parts
            if any(p in {".venv", "tests", "fixtures", "composed", "node_modules"} for p in parts):
                continue
            seen.add(cg.parent)
    return sorted(seen)


def load_yaml(path: Path) -> Any:
    try:
        with path.open() as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        return {"_load_error": str(e)}


def section_1_cache_contents(cache_root: Path) -> dict[str, Any]:
    blobs = list((cache_root / "blobs" / "sha256").iterdir()) if (cache_root / "blobs" / "sha256").exists() else []
    texts = list((cache_root / "text" / "sha256").iterdir()) if (cache_root / "text" / "sha256").exists() else []
    metas = list((cache_root / "metadata" / "sha256").iterdir()) if (cache_root / "metadata" / "sha256").exists() else []
    blob_shas = {p.name for p in blobs}
    # text files have .txt suffix
    text_shas = {p.stem for p in texts if p.suffix == ".txt"}
    # metadata files have .json suffix
    meta_shas = {p.stem for p in metas if p.suffix == ".json"}
    total_blob_bytes = sum(p.stat().st_size for p in blobs)
    missing_text = blob_shas - text_shas
    missing_meta = blob_shas - meta_shas
    return {
        "blob_count": len(blobs),
        "text_count": len(text_shas),
        "metadata_count": len(meta_shas),
        "total_blob_bytes": total_blob_bytes,
        "blob_shas": blob_shas,
        "text_shas": text_shas,
        "meta_shas": meta_shas,
        "missing_text_count": len(missing_text),
        "missing_meta_count": len(missing_meta),
        "missing_text_sample": sorted(missing_text)[:5],
        "missing_meta_sample": sorted(missing_meta)[:5],
    }


def collect_manifest_refs(dossier_dirs: list[Path]) -> dict[str, set[str]]:
    """Return {sha256: {dossier_slug,...}} for every sha referenced by any cache_manifest."""
    refs: dict[str, set[str]] = collections.defaultdict(set)
    for d in dossier_dirs:
        cm = d / "cache_manifest.yml"
        if not cm.exists():
            continue
        data = load_yaml(cm)
        if "_load_error" in data:
            continue
        for entry in data.get("entries") or []:
            sha = entry.get("sha256")
            if sha:
                refs[sha].add(d.name)
    return refs


def section_2_orphans(blob_shas: set[str], refs: dict[str, set[str]], cache_root: Path) -> dict[str, Any]:
    orphans = blob_shas - set(refs.keys())
    orphan_bytes = sum(
        (cache_root / "blobs" / "sha256" / sha).stat().st_size
        for sha in orphans
        if (cache_root / "blobs" / "sha256" / sha).exists()
    )
    return {
        "count": len(orphans),
        "total_bytes": orphan_bytes,
        "sample": sorted(orphans)[:5],
    }


def section_3_dangling_refs(dossier_dirs: list[Path], blob_shas: set[str]) -> dict[str, Any]:
    """bib_ledger entries with primary_url/sha256 that are NOT in the cache."""
    by_dossier: dict[str, dict[str, Any]] = {}
    # Build URL->sha map from cache_manifests so we can resolve bib_ledger primary_url -> sha
    url_to_sha: dict[str, str] = {}
    for d in dossier_dirs:
        cm = d / "cache_manifest.yml"
        if not cm.exists():
            continue
        data = load_yaml(cm)
        for entry in data.get("entries") or []:
            sha = entry.get("sha256")
            url = entry.get("source_url")
            if sha and url:
                url_to_sha[url] = sha
    grand_total_entries = 0
    grand_total_dangling = 0
    for d in dossier_dirs:
        bib = d / "bib_ledger.yml"
        if not bib.exists():
            continue
        data = load_yaml(bib)
        entries = data.get("entries") or []
        dangling = []
        for entry in entries:
            url = entry.get("primary_url")
            if not url:
                continue
            sha = url_to_sha.get(url)
            if sha is None or sha not in blob_shas:
                dangling.append({"bibkey": entry.get("bibkey"), "url": url, "title": (entry.get("title") or "")[:80]})
        by_dossier[d.name] = {"entries": len(entries), "dangling": len(dangling), "sample": dangling[:5]}
        grand_total_entries += len(entries)
        grand_total_dangling += len(dangling)
    return {
        "grand_total_entries": grand_total_entries,
        "grand_total_dangling": grand_total_dangling,
        "by_dossier": by_dossier,
    }


def section_4_integrity(cache_root: Path, blob_shas: set[str], sample_size: int) -> dict[str, Any]:
    if not blob_shas:
        return {"sampled": 0, "failures": [], "ok": 0}
    sample = random.sample(sorted(blob_shas), min(sample_size, len(blob_shas)))
    failures = []
    for sha in sample:
        p = cache_root / "blobs" / "sha256" / sha
        if not p.exists():
            failures.append({"sha": sha, "reason": "blob path missing"})
            continue
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        if h != sha:
            failures.append({"sha": sha, "actual": h, "reason": "sha256 mismatch"})
    return {"sampled": len(sample), "ok": len(sample) - len(failures), "failures": failures}


def section_5_extraction_flags(cache_root: Path, blob_shas: set[str]) -> dict[str, Any]:
    text_dir = cache_root / "text" / "sha256"
    empty: list[str] = []
    tiny: list[str] = []  # text very small relative to blob
    high_nonprintable: list[str] = []
    collapsed_space: list[str] = []  # long runs without whitespace
    garbled_unicode: list[str] = []
    for sha in sorted(blob_shas):
        tf = text_dir / f"{sha}.txt"
        if not tf.exists():
            continue
        size = tf.stat().st_size
        if size == 0:
            empty.append(sha)
            continue
        blob_size = (cache_root / "blobs" / "sha256" / sha).stat().st_size if (cache_root / "blobs" / "sha256" / sha).exists() else 0
        if size < 200 and blob_size > 50_000:
            tiny.append(sha)
        # sample first 50KB for the printable / collapsed / garbled checks (cheap)
        try:
            chunk = tf.read_bytes()[:50_000]
        except Exception:
            continue
        if not chunk:
            continue
        nonprintable = sum(1 for b in chunk if b < 9 or (13 < b < 32))
        if nonprintable / len(chunk) > 0.05:
            high_nonprintable.append(sha)
        # collapsed-space: any run >2000 chars without whitespace
        try:
            text = chunk.decode("utf-8", errors="replace")
        except Exception:
            continue
        if re.search(r"\S{2000,}", text):
            collapsed_space.append(sha)
        # garbled unicode: high density of replacement chars
        replacement_chars = text.count("�")
        if replacement_chars > 50 and replacement_chars / max(len(text), 1) > 0.005:
            garbled_unicode.append(sha)
    return {
        "empty": {"count": len(empty), "sample": empty[:5]},
        "tiny_vs_blob": {"count": len(tiny), "sample": tiny[:5]},
        "high_nonprintable": {"count": len(high_nonprintable), "sample": high_nonprintable[:5]},
        "collapsed_space": {"count": len(collapsed_space), "sample": collapsed_space[:5]},
        "garbled_unicode": {"count": len(garbled_unicode), "sample": garbled_unicode[:5]},
    }


def section_6_per_dossier_coverage(dangling: dict[str, Any]) -> dict[str, Any]:
    rows = []
    low_coverage = []
    for slug, info in sorted(dangling["by_dossier"].items()):
        total = info["entries"] or 1
        cached = total - info["dangling"]
        pct = 100.0 * cached / total
        rows.append({"slug": slug, "total": info["entries"], "cached": cached, "pct": pct})
        if info["entries"] >= 5 and pct < 80:
            low_coverage.append({"slug": slug, "pct": pct, "total": info["entries"]})
    return {"rows": rows, "low_coverage_count": len(low_coverage), "low_coverage": low_coverage}


def section_7_escalations(dossier_dirs: list[Path]) -> dict[str, Any]:
    by_decision: collections.Counter[str] = collections.Counter()
    candidates: list[dict[str, Any]] = []
    by_dossier_count: collections.Counter[str] = collections.Counter()
    for d in dossier_dirs:
        gt = d / "gather_trace.yml"
        if not gt.exists():
            continue
        data = load_yaml(gt)
        for fetch in data.get("fetches") or []:
            decision = fetch.get("decision") or "unknown"
            by_decision[decision] += 1
            if decision not in HEALTHY_DECISIONS:
                by_dossier_count[d.name] += 1
                candidates.append({
                    "dossier": d.name,
                    "decision": decision,
                    "url": fetch.get("source_url"),
                    "reason": (fetch.get("reason") or "")[:120],
                    "sub_area": (fetch.get("sub_area") or "")[:80],
                })
        # Also count any cache_manifest entries with non-healthy extraction
    return {
        "by_decision": dict(by_decision),
        "candidate_count": len(candidates),
        "by_dossier": dict(by_dossier_count.most_common()),
        "top10_candidates": candidates[:10],
    }


def section_8_local_vs_shared(dossier_dirs: list[Path]) -> dict[str, Any]:
    local_dossiers = []
    for d in dossier_dirs:
        local_cache = d / "cache"
        if local_cache.is_dir():
            # Count anything inside it
            try:
                docs = sum(1 for _ in local_cache.rglob("*") if _.is_file())
                size = sum(p.stat().st_size for p in local_cache.rglob("*") if p.is_file())
            except Exception:
                docs, size = 0, 0
            if docs > 0:
                local_dossiers.append({"slug": d.name, "docs": docs, "bytes": size, "path": str(d.relative_to(HOME))})
    return {
        "count": len(local_dossiers),
        "dossiers": local_dossiers,
        "total_local_bytes": sum(x["bytes"] for x in local_dossiers),
    }


def section_9_duplicate_suspects(dossier_dirs: list[Path]) -> dict[str, Any]:
    """arXiv ID / DOI appearing under multiple sha256 in any cache_manifest."""
    arxiv_to_shas: dict[str, set[str]] = collections.defaultdict(set)
    doi_to_shas: dict[str, set[str]] = collections.defaultdict(set)
    for d in dossier_dirs:
        cm = d / "cache_manifest.yml"
        if not cm.exists():
            continue
        data = load_yaml(cm)
        for entry in data.get("entries") or []:
            sha = entry.get("sha256")
            url = entry.get("source_url") or ""
            if not sha:
                continue
            am = ARXIV_ID_RE.search(url)
            if am:
                # Normalize: strip trailing v\d+
                arxiv_id = re.sub(r"v\d+$", "", am.group(1))
                arxiv_to_shas[arxiv_id].add(sha)
            dm = DOI_RE.search(url)
            if dm:
                doi_to_shas[dm.group(1)].add(sha)
    arxiv_dupes = {k: sorted(v) for k, v in arxiv_to_shas.items() if len(v) > 1}
    doi_dupes = {k: sorted(v) for k, v in doi_to_shas.items() if len(v) > 1}
    return {
        "arxiv_dupes_count": len(arxiv_dupes),
        "doi_dupes_count": len(doi_dupes),
        "arxiv_dupes_sample": dict(list(arxiv_dupes.items())[:10]),
        "doi_dupes_sample": dict(list(doi_dupes.items())[:10]),
    }


def fmt_bytes(n: int) -> str:
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} TB"


def render_markdown(report: dict[str, Any], today: str) -> str:
    lines = []
    L = lines.append
    L(f"# Cache Health Report — {today}\n")
    L(f"> Generated by `cache_health.py` (read-only audit).")
    L(f"> Cache root: `{report['cache_root']}`")
    L(f"> Dossier dirs scanned: **{report['dossier_count']}**\n")

    # 1
    c = report["cache_contents"]
    L("## 1. Cache contents\n")
    L(f"- **Blobs:** {c['blob_count']:,} ({fmt_bytes(c['total_blob_bytes'])})")
    L(f"- **Text extractions (.txt):** {c['text_count']:,}")
    L(f"- **Metadata (.json):** {c['metadata_count']:,}")
    L(f"- **Blobs missing text extraction:** {c['missing_text_count']:,}" +
      (f" — sample sha: {', '.join(s[:12] for s in c['missing_text_sample'])}" if c['missing_text_sample'] else ""))
    L(f"- **Blobs missing metadata:** {c['missing_meta_count']:,}" +
      (f" — sample sha: {', '.join(s[:12] for s in c['missing_meta_sample'])}" if c['missing_meta_sample'] else ""))
    L("")

    # 2
    o = report["orphans"]
    L("## 2. Orphans (blobs not referenced by any cache_manifest)\n")
    L(f"- **Count:** {o['count']:,}  ({fmt_bytes(o['total_bytes'])})")
    if o["sample"]:
        L("- Sample sha256:")
        for s in o["sample"]:
            L(f"  - `{s}`")
    L("")

    # 3
    dr = report["dangling_refs"]
    L("## 3. Dangling refs (bib entries whose primary_url is NOT cached)\n")
    L(f"- **Total bib entries:** {dr['grand_total_entries']:,}")
    L(f"- **Dangling:** {dr['grand_total_dangling']:,}")
    if dr["by_dossier"]:
        L("\n### Top 10 dossiers by dangling count\n")
        L("| dossier | bib entries | dangling | coverage % |")
        L("|---|--:|--:|--:|")
        top = sorted(dr["by_dossier"].items(), key=lambda kv: -kv[1]["dangling"])[:10]
        for slug, info in top:
            total = info["entries"] or 1
            pct = 100.0 * (total - info["dangling"]) / total
            L(f"| {slug} | {info['entries']} | {info['dangling']} | {pct:.0f}% |")
    L("")

    # 4
    integ = report["integrity"]
    L("## 4. Integrity (sha256 sample)\n")
    L(f"- **Sampled:** {integ['sampled']}  /  **OK:** {integ['ok']}  /  **Failures:** {len(integ['failures'])}")
    for f in integ["failures"][:5]:
        L(f"  - `{f.get('sha', '?')[:12]}…` — {f.get('reason')}")
    L("")

    # 5
    e = report["extraction_flags"]
    L("## 5. Extraction red flags\n")
    L("| flag | count | sample sha |")
    L("|---|--:|---|")
    for key, label in [
        ("empty", "empty text file"),
        ("tiny_vs_blob", "tiny text vs large blob"),
        ("high_nonprintable", "high non-printable ratio"),
        ("collapsed_space", "collapsed-space (Hudgens-Halloran pattern)"),
        ("garbled_unicode", "garbled unicode (replacement-char density)"),
    ]:
        info = e[key]
        sample = ", ".join(s[:12] for s in info["sample"][:3])
        L(f"| {label} | {info['count']} | {sample} |")
    L("")

    # 6
    cov = report["coverage"]
    L("## 6. Per-dossier cache coverage\n")
    L(f"- **Dossiers with <80% coverage (≥5 bib entries):** {cov['low_coverage_count']}")
    if cov["low_coverage"]:
        L("\n| dossier | coverage % | bib entries |")
        L("|---|--:|--:|")
        for r in sorted(cov["low_coverage"], key=lambda x: x["pct"]):
            L(f"| {r['slug']} | {r['pct']:.0f}% | {r['total']} |")
    L("")

    # 7
    esc = report["escalations"]
    L("## 7. Gather-trace escalations / non-accept decisions\n")
    L(f"- **Decisions tally:** {esc['by_decision']}")
    L(f"- **Total non-accept fetches:** {esc['candidate_count']}")
    if esc["by_dossier"]:
        L("\n### Top dossiers by non-accept count\n")
        L("| dossier | non-accept |")
        L("|---|--:|")
        for slug, n in list(esc["by_dossier"].items())[:10]:
            L(f"| {slug} | {n} |")
    if esc["top10_candidates"]:
        L("\n### Top 10 retry candidates\n")
        L("| dossier | decision | URL | reason |")
        L("|---|---|---|---|")
        for c in esc["top10_candidates"]:
            url = (c.get("url") or "")[:60]
            reason = (c.get("reason") or "").replace("|", "/")[:80]
            L(f"| {c['dossier']} | {c['decision']} | {url} | {reason} |")
    L("")

    # 8
    lvs = report["local_vs_shared"]
    L("## 8. Local-vs-shared cache\n")
    L(f"- **Dossiers still using local `cache/`:** {lvs['count']}  (total {fmt_bytes(lvs['total_local_bytes'])})")
    if lvs["dossiers"]:
        L("\n| dossier | local docs | size |")
        L("|---|--:|--:|")
        for d in sorted(lvs["dossiers"], key=lambda x: -x["bytes"]):
            L(f"| {d['slug']} | {d['docs']} | {fmt_bytes(d['bytes'])} |")
    L("")

    # 9
    dup = report["dupes"]
    L("## 9. Duplicate suspects (same paper, multiple sha256)\n")
    L(f"- **arXiv-ID dupes:** {dup['arxiv_dupes_count']}")
    L(f"- **DOI dupes:** {dup['doi_dupes_count']}")
    if dup["arxiv_dupes_sample"]:
        L("\n### Sample arXiv dupes (top 10)\n")
        for arxiv_id, shas in dup["arxiv_dupes_sample"].items():
            L(f"- `arXiv:{arxiv_id}` → {len(shas)} sha256s: {', '.join(s[:12] for s in shas)}")
    L("")

    L("---\n")
    L("## Top-3 recommended fixes (auto-derived)\n")
    fixes = []
    if dr["grand_total_dangling"] > 0:
        fixes.append(f"**Dangling refs** — {dr['grand_total_dangling']:,} bib entries with no cached primary. Run **fix B (escalation retry)** to recover.")
    if e["empty"]["count"] + e["tiny_vs_blob"]["count"] + e["collapsed_space"]["count"] + e["garbled_unicode"]["count"] > 0:
        bad = e["empty"]["count"] + e["tiny_vs_blob"]["count"] + e["collapsed_space"]["count"] + e["garbled_unicode"]["count"]
        fixes.append(f"**Extraction issues** — {bad} blobs flagged across empty/tiny/collapsed/garbled. Run **fix C (re-extract)**.")
    if lvs["count"] > 0:
        fixes.append(f"**Local caches still present** — {lvs['count']} dossiers. Run **fix A (consolidate to shared)**.")
    if dup["arxiv_dupes_count"] + dup["doi_dupes_count"] > 0:
        fixes.append(f"**Duplicate captures** — {dup['arxiv_dupes_count']} arXiv + {dup['doi_dupes_count']} DOI dupes. Run **fix D (dedup)**.")
    if not fixes:
        fixes.append("**Cache looks healthy** — minimal fix work needed pre-tarball.")
    for f in fixes[:3]:
        L(f"- {f}")

    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE_ROOT)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--integrity-sample", type=int, default=50)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    random.seed(args.seed)

    if not args.cache_root.exists():
        print(f"FATAL: cache root not found: {args.cache_root}", file=sys.stderr)
        return 2

    from datetime import date
    today = date.today().isoformat()

    print(f"[1/9] Cache contents @ {args.cache_root}…", file=sys.stderr)
    cc = section_1_cache_contents(args.cache_root)
    print(f"      blobs={cc['blob_count']:,} text={cc['text_count']:,} metadata={cc['metadata_count']:,}", file=sys.stderr)

    print("[…] Finding dossier dirs…", file=sys.stderr)
    dossier_dirs = find_dossier_dirs()
    print(f"      found {len(dossier_dirs)} dossier dirs", file=sys.stderr)

    print("[…] Collecting cache_manifest refs…", file=sys.stderr)
    refs = collect_manifest_refs(dossier_dirs)

    print(f"[2/9] Orphans (blob_shas={len(cc['blob_shas']):,} vs refs={len(refs):,})…", file=sys.stderr)
    orph = section_2_orphans(cc["blob_shas"], refs, args.cache_root)
    print(f"      orphans={orph['count']:,} ({fmt_bytes(orph['total_bytes'])})", file=sys.stderr)

    print("[3/9] Dangling refs (bib entries with no cached primary)…", file=sys.stderr)
    dr = section_3_dangling_refs(dossier_dirs, cc["blob_shas"])
    print(f"      dangling={dr['grand_total_dangling']}/{dr['grand_total_entries']}", file=sys.stderr)

    print(f"[4/9] Integrity sample of {args.integrity_sample}…", file=sys.stderr)
    integ = section_4_integrity(args.cache_root, cc["blob_shas"], args.integrity_sample)
    print(f"      sampled={integ['sampled']} failures={len(integ['failures'])}", file=sys.stderr)

    print("[5/9] Extraction red flags…", file=sys.stderr)
    ext = section_5_extraction_flags(args.cache_root, cc["blob_shas"])
    print(f"      empty={ext['empty']['count']} tiny={ext['tiny_vs_blob']['count']} nonprintable={ext['high_nonprintable']['count']} collapsed={ext['collapsed_space']['count']} garbled={ext['garbled_unicode']['count']}", file=sys.stderr)

    print("[6/9] Per-dossier coverage…", file=sys.stderr)
    cov = section_6_per_dossier_coverage(dr)
    print(f"      low-coverage dossiers={cov['low_coverage_count']}", file=sys.stderr)

    print("[7/9] Escalation tally…", file=sys.stderr)
    esc = section_7_escalations(dossier_dirs)
    print(f"      non-accept fetches={esc['candidate_count']}", file=sys.stderr)

    print("[8/9] Local-vs-shared cache…", file=sys.stderr)
    lvs = section_8_local_vs_shared(dossier_dirs)
    print(f"      dossiers w/ local cache={lvs['count']}", file=sys.stderr)

    print("[9/9] Duplicate suspects…", file=sys.stderr)
    dup = section_9_duplicate_suspects(dossier_dirs)
    print(f"      arxiv-dupes={dup['arxiv_dupes_count']} doi-dupes={dup['doi_dupes_count']}", file=sys.stderr)

    report = {
        "cache_root": str(args.cache_root),
        "dossier_count": len(dossier_dirs),
        "cache_contents": cc,
        "orphans": orph,
        "dangling_refs": dr,
        "integrity": integ,
        "extraction_flags": ext,
        "coverage": cov,
        "escalations": esc,
        "local_vs_shared": lvs,
        "dupes": dup,
    }
    md = render_markdown(report, today)
    args.out.write_text(md)
    print(f"\nWROTE {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

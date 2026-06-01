#!/usr/bin/env python3
"""Reconstruct a gather sources-JSON skeleton from the cache for a topic.

When a gather run drops mid-flight, the sources-JSON it was building in
memory is lost — but every confirmed source has already been written to
the content-addressed cache (`scripts/cache_source.py`), and each blob's
metadata sidecar records the `topic` it belongs to. This tool scans the
cache for a topic and rebuilds a partial sources-JSON so the gather can
resume from where it left off instead of restarting.

The output is a valid INPUT to `scripts/assemble_artifacts.py`: the
top-level shape is `{topic, today, cache_root, sources, rejects}` and
each source carries the keys assemble_artifacts requires. Fields the
cache knows (`sha`, `primary_url`, `published_online`) are filled in;
fields that need human/LLM judgment are left as placeholders so the
resumer can see exactly what still has to be completed:

    bibkey / claim_family / sub_area  -> "TODO"
    title / authors / venue / excerpt -> ""

Triage helpers (prefixed `_` so they are ignorable extras, not schema
fields): `_content_type`, `_extraction_status`, `_cached_text_path`, and
on degraded blobs `_low_quality` + `_low_quality_reason`.

A blob is flagged low-quality (re-fetch rather than trust) when its
extracted text is below LOW_QUALITY_TEXT_BYTES (2000 bytes) or its
extraction_status is one of LOW_QUALITY_STATUSES (stub / failed). It is
flagged in place in `sources` rather than dropped, so the resumer still
sees the URL and can decide to re-fetch.

Read-only over the cache: never fetches the network, never writes to the
cache. The only write is the output JSON.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

CACHE_ROOT_DEFAULT = "~/Claude/research_cache"
LOW_QUALITY_TEXT_BYTES = 2000
LOW_QUALITY_STATUSES = ("stub", "failed")

PLACEHOLDER_TODO = "TODO"
PLACEHOLDER_EMPTY = ""


def iter_metadata(cache_root: Path) -> "list[dict[str, Any]]":
    """Yield parsed metadata sidecars from the cache, skipping bad ones."""
    out: "list[dict[str, Any]]" = []
    meta_dir = cache_root / "metadata" / "sha256"
    if not meta_dir.is_dir():
        return out
    for path in sorted(meta_dir.glob("*.json")):
        try:
            out.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return out


def _cached_text_path(cache_root: Path, sha: str) -> str:
    """Return the cache text path for a SHA as a string."""
    return str(cache_root / "text" / "sha256" / f"{sha}.txt")


def _low_quality_reason(meta: "dict[str, Any]") -> str | None:
    """Return a reason string if the blob is too weak to trust, else None."""
    status = meta.get("extraction_status")
    if status in LOW_QUALITY_STATUSES:
        return f"extraction_status={status}"
    text_bytes = meta.get("text_bytes")
    if isinstance(text_bytes, int) and text_bytes < LOW_QUALITY_TEXT_BYTES:
        return f"text_bytes={text_bytes} < {LOW_QUALITY_TEXT_BYTES}"
    return None


def build_source_record(
    meta: "dict[str, Any]", cache_root: Path, n: int
) -> "dict[str, Any]":
    """Build a partial source record from one cache metadata sidecar."""
    sha = meta.get("sha256", "")
    record: "dict[str, Any]" = {
        "n": n,
        "bibkey": PLACEHOLDER_TODO,
        "primary_url": meta.get("source_url", ""),
        "title": PLACEHOLDER_EMPTY,
        "authors": PLACEHOLDER_EMPTY,
        "venue": PLACEHOLDER_EMPTY,
        "claim_family": PLACEHOLDER_TODO,
        "sha": sha,
        "sub_area": PLACEHOLDER_TODO,
        "excerpt": PLACEHOLDER_EMPTY,
        "_content_type": meta.get("content_type"),
        "_extraction_status": meta.get("extraction_status"),
        "_cached_text_path": _cached_text_path(cache_root, sha),
    }
    published = meta.get("published_online")
    if published:
        record["published_online"] = published
    reason = _low_quality_reason(meta)
    if reason is not None:
        record["_low_quality"] = True
        record["_low_quality_reason"] = reason
    return record


def _existing_keys(existing: "dict[str, Any]") -> "tuple[set[str], set[str]]":
    """Return the (sha, primary_url) sets already covered by an existing JSON."""
    shas: set[str] = set()
    urls: set[str] = set()
    for src in existing.get("sources", []):
        if src.get("sha"):
            shas.add(src["sha"])
        if src.get("primary_url"):
            urls.add(src["primary_url"])
    return shas, urls


def recover_sources(
    records: "list[dict[str, Any]]",
    topic: str,
    cache_root: Path,
    existing: "dict[str, Any] | None" = None,
) -> "dict[str, Any]":
    """Build a sources-JSON skeleton for a topic, merging an existing one.

    Existing source records are kept verbatim; cache blobs already
    covered (by sha or primary_url) are skipped so a human-completed
    record is never overwritten. Returns the merged skeleton dict.
    """
    existing = existing or {}
    sources: "list[dict[str, Any]]" = list(existing.get("sources", []))
    seen_shas, seen_urls = _existing_keys(existing)
    recovered = 0
    low_quality = 0
    n = len(sources)
    for meta in records:
        if meta.get("topic") != topic:
            continue
        sha = meta.get("sha256", "")
        url = meta.get("source_url", "")
        if (sha and sha in seen_shas) or (url and url in seen_urls):
            continue
        n += 1
        record = build_source_record(meta, cache_root, n)
        sources.append(record)
        if sha:
            seen_shas.add(sha)
        if url:
            seen_urls.add(url)
        recovered += 1
        if record.get("_low_quality"):
            low_quality += 1
    today = existing.get("today") or _dt.date.today().isoformat()
    skeleton: "dict[str, Any]" = {
        "topic": topic,
        "today": today,
        "cache_root": str(cache_root),
        "sources": sources,
        "rejects": list(existing.get("rejects", [])),
    }
    skeleton["_recovery_summary"] = {
        "recovered": recovered,
        "low_quality": low_quality,
        "already_present": len(existing.get("sources", [])),
    }
    return skeleton


def _load_existing(path: Path) -> "dict[str, Any]":
    """Load a partial sources-JSON to merge into; raise on bad JSON."""
    return json.loads(path.read_text(encoding="utf-8"))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("topic_slug", help="topic slug to recover from the cache")
    parser.add_argument("--cache-root", default=CACHE_ROOT_DEFAULT)
    parser.add_argument("--out", default=None, help="output path for the recovered sources-JSON")
    parser.add_argument("--existing", default=None, help="partial sources-JSON to merge into")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    cache_root = Path(args.cache_root).expanduser()
    out_path = Path(args.out).expanduser() if args.out else Path(
        f"{args.topic_slug}_sources.recovered.json"
    )
    existing: "dict[str, Any] | None" = None
    if args.existing:
        existing_path = Path(args.existing).expanduser()
        if not existing_path.is_file():
            print(f"resume_gather: --existing not found: {existing_path}", file=sys.stderr)
            return 1
        try:
            existing = _load_existing(existing_path)
        except json.JSONDecodeError as exc:
            print(f"resume_gather: --existing is not valid JSON: {exc}", file=sys.stderr)
            return 1
    records = iter_metadata(cache_root)
    skeleton = recover_sources(records, args.topic_slug, cache_root, existing)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(skeleton, indent=2, sort_keys=True), encoding="utf-8")
    summary = skeleton["_recovery_summary"]
    print(
        "resume_gather: "
        f"{summary['recovered']} recovered, "
        f"{summary['low_quality']} low-quality, "
        f"{summary['already_present']} already-present -> {out_path}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

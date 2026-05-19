#!/usr/bin/env python3
"""Cache public source artifacts into the strict-live global content cache.

This helper is intentionally dependency-free. It stores raw bytes, a best-effort
text derivative, and metadata JSON under a content-addressed cache root. It does
not update a project manifest automatically; it prints manifest-ready YAML
entries so a gather/freshness skill can append them deliberately.
"""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import sys
from urllib.error import URLError
from urllib.request import Request, urlopen


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_text(data: bytes, content_type: str) -> tuple[str, str]:
    if content_type.startswith("text/") or "json" in content_type or "html" in content_type:
        return data.decode("utf-8", errors="replace"), "ok"
    return (
        f"[raw binary cached; no dependency-free extractor available for {content_type}]\n",
        "raw_only",
    )


def _fetch(source_url: str) -> tuple[bytes, str]:
    req = Request(source_url, headers={"User-Agent": "research_toolkit/2.0 strict-live cache"})
    with urlopen(req, timeout=30) as response:  # noqa: S310 - user-requested research cache helper
        content_type = response.headers.get_content_type() or "application/octet-stream"
        return response.read(), content_type


def _private_write(path: Path, data: bytes | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        path.write_text(data, encoding="utf-8")
    else:
        path.write_bytes(data)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def cache_one(source_url: str, *, cache_root: Path, fetched_at: str, topic: str) -> dict:
    raw, content_type = _fetch(source_url)
    digest = _sha256(raw)
    blob_dir = cache_root / "blobs" / "sha256"
    text_dir = cache_root / "text" / "sha256"
    meta_dir = cache_root / "metadata" / "sha256"

    raw_path = blob_dir / digest
    text_path = text_dir / f"{digest}.txt"
    metadata_path = meta_dir / f"{digest}.json"

    text, extraction_status = _safe_text(raw, content_type)
    metadata = {
        "schema_version": 2,
        "topic": topic,
        "source_url": source_url,
        "fetched_at": fetched_at,
        "content_type": content_type,
        "bytes": len(raw),
        "sha256": digest,
        "cache_policy": "max_local_private",
        "restricted": False,
        "rights_status": "private_use",
        "extraction_status": extraction_status,
    }

    cache_root.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(cache_root, 0o700)
    except OSError:
        pass
    _private_write(raw_path, raw)
    _private_write(text_path, text)
    _private_write(metadata_path, json.dumps(metadata, indent=2, sort_keys=True) + "\n")

    return {
        "cache_id": f"cache_{digest[:16]}",
        "source_url": source_url,
        "fetched_at": fetched_at,
        "content_type": content_type or mimetypes.guess_type(source_url)[0] or "application/octet-stream",
        "bytes": len(raw),
        "sha256": digest,
        "raw_path": str(raw_path),
        "text_path": str(text_path),
        "metadata_path": str(metadata_path),
        "restricted": False,
        "rights_status": "private_use",
        "extraction_status": extraction_status,
    }


def _print_yaml_entry(entry: dict) -> None:
    print("- cache_id: " + entry["cache_id"])
    for key in (
        "source_url",
        "fetched_at",
        "content_type",
        "bytes",
        "sha256",
        "raw_path",
        "text_path",
        "metadata_path",
        "restricted",
        "rights_status",
        "extraction_status",
    ):
        value = entry[key]
        if isinstance(value, bool):
            value = str(value).lower()
        print(f"  {key}: {value}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_url", nargs="+")
    parser.add_argument("--cache-root", default="~/Claude/research_cache")
    parser.add_argument("--topic", default="unspecified")
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args(argv[1:])

    root = Path(args.cache_root).expanduser().resolve()
    failures = 0
    for source_url in args.source_url:
        try:
            entry = cache_one(source_url, cache_root=root, fetched_at=args.date, topic=args.topic)
        except (URLError, TimeoutError, OSError) as exc:
            failures += 1
            print(f"ERROR caching {source_url}: {exc}", file=sys.stderr)
            continue
        _print_yaml_entry(entry)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

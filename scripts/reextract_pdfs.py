#!/usr/bin/env python3
"""Re-extract text from existing raw_only PDF cache entries (v2.3 / #11).

When the toolkit upgrades from <=v2.2 to v2.3+, existing manifests have PDFs
cached with ``extraction_status: raw_only`` because the old ``_safe_text()``
bailed on application/pdf. v2.3 adds the pdfplumber + Docling cascade in
``cache_source.py``, but only for FRESH captures.

This script walks an existing manifest, finds raw_only PDF entries, reads the
cached blob (no network), runs the v2.3 cascade against it, and updates:
- ``text_path`` file (overwrites the placeholder text)
- ``metadata.json`` (sets ``extraction_status`` + ``extraction_warnings``)
- The manifest entry itself (status + warnings)

Idempotent: re-running has no effect on entries already at non-raw_only.

Usage:
    python scripts/reextract_pdfs.py path/to/cache_manifest.yml
    python scripts/reextract_pdfs.py path/to/cache_manifest.yml --dry-run
    python scripts/reextract_pdfs.py path/to/cache_manifest.yml --strict-extraction
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

import yaml

# Reuse the cascade + extraction_log helpers from cache_source.py
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import cache_source  # noqa: E402


def _resolve_cache_path(manifest_path: Path, cache_root: str | None, value: str) -> Path:
    """Mirror validators/cache_manifest.py:_resolve() — cache_root-aware."""
    p = Path(value).expanduser()
    if p.is_absolute():
        return p
    if cache_root:
        root = Path(cache_root).expanduser()
        if not root.is_absolute():
            root = (manifest_path.parent / root).resolve()
        return (root / p).resolve()
    return (manifest_path.parent / p).resolve()


def reextract(
    manifest_path: Path,
    *,
    dry_run: bool = False,
    strict_extraction: bool = False,
    docling_cache_dir: str | None = None,
) -> int:
    """Return exit code (0 OK, 1 if would-change in dry-run or strict failures, 2 on error)."""
    raw_text = manifest_path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw_text)
    if not isinstance(data, dict):
        print(f"error: {manifest_path} is not a YAML mapping", file=sys.stderr)
        return 2

    cache_root = data.get("cache_root") if isinstance(data.get("cache_root"), str) else None
    entries = data.get("entries")
    if not isinstance(entries, list):
        print(f"error: {manifest_path} has no 'entries' list", file=sys.stderr)
        return 2

    log_path: Path | None = None
    if cache_root:
        cache_root_resolved = Path(cache_root).expanduser()
        if not cache_root_resolved.is_absolute():
            cache_root_resolved = (manifest_path.parent / cache_root_resolved).resolve()
        log_path = cache_source._default_extraction_log_path(cache_root_resolved)
    run_id = uuid.uuid4().hex[:12]

    candidates = []
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        if entry.get("record_type") == "revisit":
            continue
        ct = entry.get("content_type", "")
        if not (ct == "application/pdf" or (isinstance(ct, str) and ct.endswith("/pdf"))):
            continue
        if entry.get("extraction_status") != "raw_only":
            continue
        candidates.append((idx, entry))

    if not candidates:
        print(f"OK: {manifest_path} has 0 raw_only PDF entries to re-extract", file=sys.stderr)
        return 0

    if dry_run:
        print(
            f"DRY-RUN: would re-extract {len(candidates)} raw_only PDF(s) in "
            f"{manifest_path}",
            file=sys.stderr,
        )
        for idx, entry in candidates:
            print(f"  entries[{idx}] {entry.get('source_url')}", file=sys.stderr)
        return 1

    changed = 0
    strict_violations = 0
    for idx, entry in candidates:
        raw_path = _resolve_cache_path(manifest_path, cache_root, entry["raw_path"])
        if not raw_path.exists():
            print(
                f"WARN: entries[{idx}] raw_path missing on disk: {raw_path} "
                f"— skipping",
                file=sys.stderr,
            )
            continue
        raw_bytes = raw_path.read_bytes()
        text, status, warnings = cache_source._extract_pdf_text(
            raw_bytes, docling_cache_dir=docling_cache_dir
        )
        if status == "raw_only":
            # Cascade itself bailed (e.g., pdfplumber missing). Don't overwrite.
            print(
                f"WARN: entries[{idx}] cascade returned raw_only: {warnings} "
                f"— skipping",
                file=sys.stderr,
            )
            continue

        # Update text_path on disk
        text_path = _resolve_cache_path(manifest_path, cache_root, entry["text_path"])
        text_path.parent.mkdir(parents=True, exist_ok=True)
        text_path.write_text(text, encoding="utf-8")

        # Update metadata.json
        metadata_path = _resolve_cache_path(manifest_path, cache_root, entry["metadata_path"])
        if metadata_path.exists():
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                metadata = {}
            metadata["extraction_status"] = status
            if warnings:
                metadata["extraction_warnings"] = list(warnings)
            elif "extraction_warnings" in metadata:
                del metadata["extraction_warnings"]
            metadata_path.write_text(
                json.dumps(metadata, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

        # Update manifest entry
        entry["extraction_status"] = status
        if warnings:
            entry["extraction_warnings"] = list(warnings)
        elif "extraction_warnings" in entry:
            del entry["extraction_warnings"]

        # Log it
        if log_path is not None:
            try:
                cache_source._append_extraction_log(
                    log_path,
                    cache_id=entry.get("cache_id", ""),
                    source_url=entry.get("source_url", ""),
                    status=status,
                    warnings=list(warnings),
                    run_id=run_id,
                )
            except OSError as exc:
                print(f"WARN: failed to append extraction_log: {exc}", file=sys.stderr)

        # WARN for non-ideal status (matches cache_source.py behavior)
        if status in cache_source.LOUD_EXTRACTION_STATUSES:
            warn_msg = f"WARN: {entry.get('source_url')} re-extracted as {status}"
            if warnings:
                warn_msg += f" — {warnings[0]}"
            print(warn_msg, file=sys.stderr)

        if strict_extraction and status in cache_source.STRICT_FAIL_STATUSES:
            strict_violations += 1

        changed += 1

    # Write the updated manifest back
    new_text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    manifest_path.write_text(new_text, encoding="utf-8")
    print(
        f"OK: re-extracted {changed} PDF(s) in {manifest_path}",
        file=sys.stderr,
    )
    return 1 if strict_violations else 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Re-extract text from existing raw_only PDF cache entries using the "
            "v2.3 pdfplumber + Docling cascade. Idempotent. Closes #11 for "
            "consumers upgrading from <=v2.2."
        )
    )
    parser.add_argument("manifest", help="path to cache_manifest.yml")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report which entries would be re-extracted without writing",
    )
    parser.add_argument(
        "--strict-extraction",
        action="store_true",
        help="exit non-zero when any entry lands at a non-ideal status",
    )
    parser.add_argument(
        "--docling-cache-dir",
        default=None,
        help="passed through to the cascade (honors $DOCLING_CACHE_DIR)",
    )
    args = parser.parse_args(argv[1:])

    target = Path(args.manifest).expanduser().resolve()
    if not target.exists():
        print(f"error: path does not exist: {target}", file=sys.stderr)
        return 2
    return reextract(
        target,
        dry_run=args.dry_run,
        strict_extraction=args.strict_extraction,
        docling_cache_dir=args.docling_cache_dir,
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv))

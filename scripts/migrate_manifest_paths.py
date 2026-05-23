#!/usr/bin/env python3
"""Rewrite a v2.0-v2.2 cache_manifest.yml to use v2.3+ portable relative paths.

v2.3 closes #2 / #13: the writer used to serialize absolute / ~-prefixed paths
into raw_path / text_path / metadata_path, making manifests non-portable across
machines. This script does the one-pass remediation.

For each capture entry, the script:
- Reads cache_root from the top of the manifest.
- For raw_path / text_path / metadata_path, strips the cache_root prefix
  (after ~ expansion) and writes the remainder as a relative path.
- Leaves entries already using relative paths untouched (idempotent).
- Skips revisit entries (they reference capture entries by ID, no paths to fix).

Usage:
    python scripts/migrate_manifest_paths.py path/to/cache_manifest.yml
    python scripts/migrate_manifest_paths.py path/to/cache_manifest.yml --dry-run
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml


PATH_FIELDS = ("raw_path", "text_path", "metadata_path")


def _relativize(value: str, cache_root: Path) -> tuple[str, bool]:
    """Return (new_value, changed).

    If `value` is absolute (or ~-prefixed) AND lives under cache_root, return
    the path relative to cache_root. Otherwise return (value, False).
    """
    p = Path(value).expanduser()
    if not p.is_absolute():
        return value, False
    try:
        rel = p.relative_to(cache_root)
    except ValueError:
        # Path doesn't live under cache_root — leave alone, but caller will
        # surface this as a warning since validator will reject it.
        return value, False
    return str(rel), True


def migrate(manifest_path: Path, *, dry_run: bool = False) -> int:
    """Return exit code (0 OK, 1 if would-change in dry-run, 2 on error)."""
    raw_text = manifest_path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw_text)
    if not isinstance(data, dict):
        print(f"error: {manifest_path} is not a YAML mapping", file=sys.stderr)
        return 2

    cache_root_str = data.get("cache_root")
    if not isinstance(cache_root_str, str) or not cache_root_str.strip():
        print(
            f"error: {manifest_path} has no top-level cache_root; cannot "
            "compute relative paths. Add `cache_root: ~/Claude/research_cache` "
            "(or your cache location) and re-run.",
            file=sys.stderr,
        )
        return 2

    cache_root = Path(cache_root_str).expanduser().resolve()

    entries = data.get("entries")
    if not isinstance(entries, list):
        print(f"error: {manifest_path} has no 'entries' list", file=sys.stderr)
        return 2

    total_changed = 0
    out_of_root: list[str] = []
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        if entry.get("record_type") == "revisit":
            continue
        for field in PATH_FIELDS:
            value = entry.get(field)
            if not isinstance(value, str) or not value.strip():
                continue
            new_value, changed = _relativize(value, cache_root)
            if changed:
                entry[field] = new_value
                total_changed += 1
            elif value.startswith("/") or value.startswith("~"):
                out_of_root.append(
                    f"  entries[{idx}].{field}: {value!r} is not under cache_root {cache_root}"
                )

    if out_of_root:
        print(
            f"warning: {len(out_of_root)} path(s) are absolute but do not live "
            f"under cache_root; left unchanged:",
            file=sys.stderr,
        )
        for line in out_of_root:
            print(line, file=sys.stderr)

    if total_changed == 0:
        print(f"OK: {manifest_path} already portable (0 paths rewritten)", file=sys.stderr)
        return 0

    if dry_run:
        print(
            f"DRY-RUN: would rewrite {total_changed} path(s) in {manifest_path}",
            file=sys.stderr,
        )
        return 1

    # Preserve top-level comment header by emitting a fresh dump. We can't
    # easily round-trip comments without ruamel.yaml, so the migration
    # explicitly does not promise comment preservation. Document this in
    # docs/troubleshooting.md.
    new_text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    manifest_path.write_text(new_text, encoding="utf-8")
    print(
        f"OK: rewrote {total_changed} path(s) in {manifest_path}",
        file=sys.stderr,
    )
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Rewrite v2.0-v2.2 cache_manifest.yml absolute paths to v2.3+ "
            "portable relative paths. Idempotent. Closes #2 / #13."
        )
    )
    parser.add_argument("manifest", help="path to cache_manifest.yml")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would change but don't write",
    )
    args = parser.parse_args(argv[1:])

    target = Path(args.manifest).expanduser().resolve()
    if not target.exists():
        print(f"error: path does not exist: {target}", file=sys.stderr)
        return 2
    return migrate(target, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main(sys.argv))

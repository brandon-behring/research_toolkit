"""Validate strict-live v2 cache_manifest.yml."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators._common import URL_RE
from validators.v2_common import (
    ALLOWED_RIGHTS_STATUS,
    load_yaml_mapping,
    parse_iso_date,
    validate_nonempty_string,
    validate_strict_live_top,
)

import re

URL_PATTERN = re.compile(rf"^{URL_RE}$")
ALLOWED_EXTRACTION_STATUS = {"ok", "partial", "raw_only", "failed"}
REQUIRED_ENTRY_FIELDS = (
    "cache_id",
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
)


def _resolve(path: Path, value: str) -> Path:
    p = Path(value).expanduser()
    if p.is_absolute():
        return p
    return (path.parent / p).resolve()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _validate_entry(entry: dict[str, Any], *, loc: str, manifest_path: Path) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_ENTRY_FIELDS:
        if field not in entry:
            errors.append(f"{loc}: missing required field '{field}'")

    for field in ("cache_id", "source_url", "content_type", "sha256", "raw_path", "text_path", "metadata_path"):
        if field in entry:
            err = validate_nonempty_string(entry[field], f"{loc}.{field}")
            if err:
                errors.append(err)

    if isinstance(entry.get("source_url"), str) and not URL_PATTERN.match(entry["source_url"]):
        errors.append(f"{loc}.source_url: not a valid http(s) URL: {entry['source_url']!r}")

    if "fetched_at" in entry:
        _, err = parse_iso_date(entry["fetched_at"], f"{loc}.fetched_at")
        if err:
            errors.append(err)

    if "bytes" in entry:
        if not isinstance(entry["bytes"], int) or entry["bytes"] < 0:
            errors.append(f"{loc}.bytes: must be a non-negative integer")

    if isinstance(entry.get("sha256"), str) and not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]):
        errors.append(f"{loc}.sha256: must be 64 lowercase hex characters")

    if "restricted" in entry and not isinstance(entry["restricted"], bool):
        errors.append(f"{loc}.restricted: must be boolean")

    rights = entry.get("rights_status")
    if rights is not None and rights not in ALLOWED_RIGHTS_STATUS:
        errors.append(f"{loc}.rights_status: {rights!r} not in {sorted(ALLOWED_RIGHTS_STATUS)}")

    extraction = entry.get("extraction_status")
    if extraction is not None and extraction not in ALLOWED_EXTRACTION_STATUS:
        errors.append(
            f"{loc}.extraction_status: {extraction!r} not in {sorted(ALLOWED_EXTRACTION_STATUS)}"
        )

    raw_value = entry.get("raw_path")
    if isinstance(raw_value, str) and raw_value.strip():
        raw_path = _resolve(manifest_path, raw_value)
        if not raw_path.exists():
            errors.append(f"{loc}.raw_path: file does not exist: {raw_value}")
        elif raw_path.is_file():
            actual_hash = _sha256(raw_path)
            if isinstance(entry.get("sha256"), str) and actual_hash != entry["sha256"]:
                errors.append(
                    f"{loc}.sha256: expected {entry['sha256']}, actual {actual_hash}"
                )
            if isinstance(entry.get("bytes"), int) and raw_path.stat().st_size != entry["bytes"]:
                errors.append(
                    f"{loc}.bytes: expected {entry['bytes']}, actual {raw_path.stat().st_size}"
                )

    for field in ("text_path", "metadata_path"):
        value = entry.get(field)
        if isinstance(value, str) and value.strip():
            resolved = _resolve(manifest_path, value)
            if not resolved.exists():
                errors.append(f"{loc}.{field}: file does not exist: {value}")
            elif field == "metadata_path":
                try:
                    json.loads(resolved.read_text(encoding="utf-8"))
                except json.JSONDecodeError as exc:
                    errors.append(f"{loc}.metadata_path: JSON parse error: {exc}")

    return errors


def validate(path: Path) -> list[str]:
    data, errors = load_yaml_mapping(path)
    if errors:
        return errors
    assert data is not None

    errors.extend(validate_strict_live_top(data))
    if "cache_root" in data:
        err = validate_nonempty_string(data["cache_root"], "top-level.cache_root")
        if err:
            errors.append(err)

    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        errors.append("'entries' must be a non-empty list")
        return errors

    seen: set[str] = set()
    for idx, entry in enumerate(entries):
        loc = f"entries[{idx}]"
        if not isinstance(entry, dict):
            errors.append(f"{loc}: must be a mapping")
            continue
        cache_id = entry.get("cache_id")
        if isinstance(cache_id, str):
            if cache_id in seen:
                errors.append(f"{loc}: duplicate cache_id {cache_id!r}")
            seen.add(cache_id)
        errors.extend(_validate_entry(entry, loc=loc, manifest_path=path))
    return errors


def _cli(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} <cache_manifest.yml>", file=sys.stderr)
        return 2
    target = Path(argv[1]).expanduser().resolve()
    if not target.exists():
        print(f"error: path does not exist: {target}", file=sys.stderr)
        return 2
    errors = validate(target)
    if errors:
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        print(f"VALIDATION FAILED: {len(errors)} error(s) in {target}", file=sys.stderr)
        return 1
    print(f"OK: {target}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv))

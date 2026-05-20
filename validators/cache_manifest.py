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
ALLOWED_RECORD_TYPES = {"capture", "revisit", "metadata", "conversion"}
ALLOWED_REVISIT_PROFILES = {"server-not-modified", "identical-payload-digest"}
# v2.2.1: fetch_method records HOW the cache was acquired. urllib is the
# default (omitted on disk for backward compat); playwright_rendered is
# only set when Playwright escalation was used.
ALLOWED_FETCH_METHODS = {"urllib", "playwright_rendered"}
# v2.1: WARC-inspired revisit records save storage on re-fetch when the
# remote content hasn't changed. A revisit record stores only the pointer
# back to the original capture (refers_to_cache_id) plus the http response
# metadata that justifies the revisit decision.
REQUIRED_ENTRY_FIELDS_CAPTURE = (
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
REQUIRED_ENTRY_FIELDS_REVISIT = (
    "cache_id",
    "source_url",
    "fetched_at",
    "record_type",
    "refers_to_cache_id",
    "revisit_profile",
)
# Kept for backward compat — defaults to capture record fields
REQUIRED_ENTRY_FIELDS = REQUIRED_ENTRY_FIELDS_CAPTURE


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


def _validate_entry(
    entry: dict[str, Any],
    *,
    loc: str,
    manifest_path: Path,
    capture_ids: set[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    record_type = entry.get("record_type", "capture")
    if record_type not in ALLOWED_RECORD_TYPES:
        errors.append(
            f"{loc}.record_type: {record_type!r} not in {sorted(ALLOWED_RECORD_TYPES)}"
        )

    is_revisit = record_type == "revisit"

    required_fields = REQUIRED_ENTRY_FIELDS_REVISIT if is_revisit else REQUIRED_ENTRY_FIELDS_CAPTURE
    for field in required_fields:
        if field not in entry:
            errors.append(f"{loc}: missing required field '{field}'")

    if is_revisit:
        profile = entry.get("revisit_profile")
        if profile is not None and profile not in ALLOWED_REVISIT_PROFILES:
            errors.append(
                f"{loc}.revisit_profile: {profile!r} not in {sorted(ALLOWED_REVISIT_PROFILES)}"
            )
        refers_to = entry.get("refers_to_cache_id")
        if isinstance(refers_to, str) and capture_ids is not None:
            if refers_to not in capture_ids:
                import difflib
                close = difflib.get_close_matches(refers_to, capture_ids, n=2, cutoff=0.6)
                hint = f" (closest match: {close})" if close else ""
                errors.append(
                    f"{loc}.refers_to_cache_id: {refers_to!r} not found among "
                    f"capture entries in this manifest{hint}"
                )
        # Revisit records skip the SHA-256/file existence checks below
        return errors

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

    fetch_method = entry.get("fetch_method")
    if fetch_method is not None and fetch_method not in ALLOWED_FETCH_METHODS:
        errors.append(
            f"{loc}.fetch_method: {fetch_method!r} not in {sorted(ALLOWED_FETCH_METHODS)}"
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

    # First pass: collect capture cache_ids for revisit cross-reference
    capture_ids: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("record_type", "capture") == "capture":
            cid = entry.get("cache_id")
            if isinstance(cid, str):
                capture_ids.add(cid)

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
        errors.extend(
            _validate_entry(entry, loc=loc, manifest_path=path, capture_ids=capture_ids)
        )
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

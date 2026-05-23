"""Shared strict-live v2/v3 validation helpers."""
from __future__ import annotations

from datetime import date, datetime, timedelta
import hashlib
from pathlib import Path
from typing import Any

import yaml

ALLOWED_SCHEMA_VERSIONS = (2, 3)
# v2 = legacy strictness (no per-link verification required)
# v3 = v2.1 anti-hallucination regime: span-anchored extraction_method,
#      link_confidence caps, substring validation for verbatim_match

STRICT_LIVE_TOP_FIELDS = (
    "schema_version",
    "topic",
    "generated_at",
    "current_as_of",
    "freshness_policy",
)

STRICT_LIVE_ENTRY_FIELDS = (
    "retrieved_at",
    "verified_at",
    "verification_method",
    "verified_fields",
    "freshness_tier",
    "stale_after_days",
    "evidence_ids",
    "cache_ids",
)

ALLOWED_VERIFICATION_METHODS = {
    "webfetch",
    "api",
    "pdf",
    "websearch_snippet",
    "manual",
    "inaccessible",
}

ALLOWED_FRESHNESS_TIERS = {"volatile", "active", "stable", "historical"}

DEFAULT_STALE_AFTER_DAYS = {
    "volatile": 30,
    "active": 90,
    "stable": 365,
    "historical": 1825,
}

ALLOWED_RIGHTS_STATUS = {
    "public",
    "private_use",
    "restricted",
    "unknown",
    "cache_only",
}


def load_yaml_mapping(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    """Read a YAML file and require a top-level mapping."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return None, [f"YAML parse error: {exc}"]
    if not isinstance(data, dict):
        return None, ["top-level must be a mapping"]
    return data, []


def is_v2_mapping(data: dict[str, Any]) -> bool:
    """True for any strict-live mapping (schema_version 2 or 3)."""
    return data.get("schema_version") in ALLOWED_SCHEMA_VERSIONS


def is_v3_mapping(data: dict[str, Any]) -> bool:
    """True only for v3-strict mappings (per-link verification required)."""
    return data.get("schema_version") == 3


def resolve_cache_path(
    value: str,
    *,
    manifest_path: Path,
    cache_root: str | None = None,
) -> Path:
    """Resolve a relative path from a cache_manifest entry to an absolute Path.

    Resolution order (when ``cache_root`` is set and value is relative):
    1. Try ``cache_root / value`` (v2.3+ portable convention; primary cache).
    2. If that doesn't exist, fall back to ``manifest_path.parent / value``
       (v2.2-vintage convention; derived dossier-local artifacts per
       ADR-049-style body-quote anchoring).
    3. Return the cache_root candidate (so error messages remain consistent
       with the v2.3 convention) if neither exists.

    Absolute / ~-prefixed values always pass through ``expanduser()``.
    When ``cache_root`` is None, falls back to the v2.0-v2.2 behavior of
    resolving against ``manifest_path.parent`` directly.

    Closes #14 — supports mixed-cache-location dossiers where primary cache
    entries (sha256-keyed PDFs/HTML) live in a shared cache_root while
    derived per-bibkey artifacts (pdftotext body_text, body_meta) live
    dossier-local. Both are legitimate per ADR-049 body-quote anchoring
    discipline.
    """
    p = Path(value).expanduser()
    if p.is_absolute():
        return p
    if cache_root:
        root = Path(cache_root).expanduser()
        if not root.is_absolute():
            root = (manifest_path.parent / root).resolve()
        cache_root_candidate = (root / p).resolve()
        if cache_root_candidate.exists():
            return cache_root_candidate
        # Fallback for dossier-local derived artifacts (v2.2-vintage compat).
        dossier_local_candidate = (manifest_path.parent / p).resolve()
        if dossier_local_candidate.exists():
            return dossier_local_candidate
        # Neither exists; return cache_root candidate for consistent error
        # messages with v2.3 portability convention.
        return cache_root_candidate
    return (manifest_path.parent / p).resolve()


def verify_excerpt_anchor(
    *,
    excerpt: str,
    cache_id: str,
    text_path_offset: list[int],
    sha256_of_span: str,
    cache_entries_by_id: dict[str, dict[str, Any]],
    manifest_path: Path,
    loc: str,
    cache_root: str | None = None,
) -> list[str]:
    """Verify a v3 excerpt_anchor against the cached text_path.

    Substring + hash + slice-bytes-equality. Closes the hallucination gap:
    "source is real" (cache_manifest) vs "the link between source and claim
    is real" (this check). Returns list of error strings (empty = OK).

    v2.3+: ``cache_root`` (from the manifest's top-level field) is used as the
    base for relative text_path resolution, matching the cache_manifest
    validator's _resolve(). Closes #13.

    v2.3.x: when ``cache_root`` is set, falls back to ``manifest_path.parent``
    if the file doesn't exist in cache_root — supports mixed-cache-location
    dossiers where derived artifacts live dossier-local (per ADR-049 body-
    quote anchoring discipline). Closes #14. See ``resolve_cache_path()``.
    """
    errors: list[str] = []

    cache_entry = cache_entries_by_id.get(cache_id)
    if cache_entry is None:
        return [
            f"{loc}.excerpt_anchor.cache_id: {cache_id!r} not found in cache_manifest. "
            f"Known cache_ids: {sorted(cache_entries_by_id)[:5]}{'...' if len(cache_entries_by_id) > 5 else ''}"
        ]

    text_path_value = cache_entry.get("text_path")
    if not isinstance(text_path_value, str):
        return [f"{loc}.excerpt_anchor: cache_manifest entry has no text_path"]

    text_path = resolve_cache_path(
        text_path_value,
        manifest_path=manifest_path,
        cache_root=cache_root,
    )

    if not text_path.exists():
        return [f"{loc}.excerpt_anchor: text_path file does not exist: {text_path}"]

    if not isinstance(text_path_offset, list) or len(text_path_offset) != 2:
        return [
            f"{loc}.excerpt_anchor.text_path_offset: must be [start, end] integers"
        ]
    start, end = text_path_offset
    if not isinstance(start, int) or not isinstance(end, int):
        return [f"{loc}.excerpt_anchor.text_path_offset: must be [int, int]"]
    if start < 0 or end <= start:
        return [
            f"{loc}.excerpt_anchor.text_path_offset: must be [0 <= start < end], got [{start}, {end}]"
        ]

    text_bytes = text_path.read_bytes()
    if end > len(text_bytes):
        return [
            f"{loc}.excerpt_anchor.text_path_offset: end {end} exceeds text length {len(text_bytes)}"
        ]

    span_bytes = text_bytes[start:end]
    actual_hash = hashlib.sha256(span_bytes).hexdigest()
    if actual_hash != sha256_of_span:
        errors.append(
            f"{loc}.excerpt_anchor.sha256_of_span: expected {sha256_of_span}, "
            f"actual {actual_hash} for bytes [{start}:{end}] of {text_path.name}"
        )

    # Excerpt-equality check (whitespace-normalized)
    span_text = span_bytes.decode("utf-8", errors="replace")
    if _normalize_ws(span_text) != _normalize_ws(excerpt):
        errors.append(
            f"{loc}.excerpt_anchor: excerpt does not match span at offset [{start}:{end}]. "
            f"Span starts: {span_text[:80]!r}..."
        )

    return errors


def _normalize_ws(s: str) -> str:
    """Collapse runs of whitespace to a single space; strip ends."""
    return " ".join(s.split())


def parse_iso_date(value: Any, loc: str) -> tuple[date | None, str | None]:
    if value is None:
        return None, None
    if isinstance(value, datetime):
        return value.date(), None
    if isinstance(value, date):
        return value, None
    if not isinstance(value, str):
        return None, f"{loc}: must be YYYY-MM-DD string or null"
    try:
        return datetime.strptime(value, "%Y-%m-%d").date(), None
    except ValueError:
        return None, f"{loc}: {value!r} is not YYYY-MM-DD"


def validate_nonempty_string(value: Any, loc: str) -> str | None:
    if not isinstance(value, str):
        return f"{loc}: must be a string"
    if not value.strip():
        return f"{loc}: must be non-empty"
    return None


def validate_string_list(value: Any, loc: str, *, allow_empty: bool = False) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, list):
        return [f"{loc}: must be a list"]
    if not value and not allow_empty:
        errors.append(f"{loc}: must be non-empty")
    for idx, item in enumerate(value):
        err = validate_nonempty_string(item, f"{loc}[{idx}]")
        if err:
            errors.append(err)
    return errors


def validate_strict_live_top(data: dict[str, Any], *, loc: str = "top-level") -> list[str]:
    errors: list[str] = []
    for field in STRICT_LIVE_TOP_FIELDS:
        if field not in data:
            errors.append(f"{loc}: missing required v2 field '{field}'")

    if data.get("schema_version") not in ALLOWED_SCHEMA_VERSIONS:
        errors.append(
            f"{loc}.schema_version: must be one of {list(ALLOWED_SCHEMA_VERSIONS)} for strict-live artifacts"
        )

    for field in ("topic", "freshness_policy"):
        if field in data:
            err = validate_nonempty_string(data[field], f"{loc}.{field}")
            if err:
                errors.append(err)

    if data.get("freshness_policy") != "strict_live":
        errors.append(f"{loc}.freshness_policy: must be 'strict_live'")

    for field in ("generated_at", "current_as_of"):
        if field in data:
            _, err = parse_iso_date(data[field], f"{loc}.{field}")
            if err:
                errors.append(err)

    return errors


def validate_strict_live_entry(entry: dict[str, Any], *, loc: str) -> list[str]:
    errors: list[str] = []
    for field in STRICT_LIVE_ENTRY_FIELDS:
        if field not in entry:
            errors.append(f"{loc}: missing required v2 field '{field}'")

    if "retrieved_at" in entry:
        _, err = parse_iso_date(entry["retrieved_at"], f"{loc}.retrieved_at")
        if err:
            errors.append(err)

    if "verified_at" in entry:
        verified_at, err = parse_iso_date(entry["verified_at"], f"{loc}.verified_at")
        if err:
            errors.append(err)
        if entry.get("status") == "verified" and verified_at is None:
            errors.append(f"{loc}.verified_at: verified entries require a date")

    method = entry.get("verification_method")
    if method is not None:
        if not isinstance(method, str) or method not in ALLOWED_VERIFICATION_METHODS:
            errors.append(
                f"{loc}.verification_method: {method!r} not in "
                f"{sorted(ALLOWED_VERIFICATION_METHODS)}"
            )

    if "verified_fields" in entry:
        errors.extend(validate_string_list(entry["verified_fields"], f"{loc}.verified_fields"))

    tier = entry.get("freshness_tier")
    if tier is not None:
        if not isinstance(tier, str) or tier not in ALLOWED_FRESHNESS_TIERS:
            errors.append(
                f"{loc}.freshness_tier: {tier!r} not in {sorted(ALLOWED_FRESHNESS_TIERS)}"
            )

    stale_after = entry.get("stale_after_days")
    if stale_after is not None:
        if not isinstance(stale_after, int) or stale_after <= 0:
            errors.append(f"{loc}.stale_after_days: must be a positive integer")
        elif isinstance(tier, str) and tier in DEFAULT_STALE_AFTER_DAYS:
            default = DEFAULT_STALE_AFTER_DAYS[tier]
            if stale_after > default:
                errors.append(
                    f"{loc}.stale_after_days: {stale_after} exceeds strict-live "
                    f"default {default} for tier {tier!r}"
                )

    for field in ("evidence_ids", "cache_ids"):
        if field in entry:
            errors.extend(validate_string_list(entry[field], f"{loc}.{field}"))

    return errors


def stale_error_for_entry(
    entry: dict[str, Any], *, loc: str, today: date
) -> str | None:
    """Return a stale-entry error if the entry is past its verified/retrieved window."""
    stale_after = entry.get("stale_after_days")
    if not isinstance(stale_after, int) or stale_after <= 0:
        return None

    anchor_value = entry.get("verified_at") or entry.get("retrieved_at")
    anchor, err = parse_iso_date(anchor_value, f"{loc}.verified_at")
    if err or anchor is None:
        return None

    stale_on = anchor + timedelta(days=stale_after)
    if stale_on < today:
        return (
            f"{loc}: stale as of {today.isoformat()} "
            f"(last verified/retrieved {anchor.isoformat()}, stale_after_days={stale_after})"
        )
    return None


def collect_entry_ids(entries: list[dict[str, Any]], field: str) -> set[str]:
    values: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        for value in entry.get(field, []) or []:
            if isinstance(value, str) and value.strip():
                values.add(value.strip())
    return values

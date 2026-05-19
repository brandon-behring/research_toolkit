"""Shared strict-live v2 validation helpers."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

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
    return data.get("schema_version") == 2


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

    if data.get("schema_version") != 2:
        errors.append(f"{loc}.schema_version: must be 2 for strict-live artifacts")

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

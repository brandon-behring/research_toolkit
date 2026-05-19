"""Validate strict-live v2 evidence_ledger.yml."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators._common import URL_RE
from validators.v2_common import (
    ALLOWED_RIGHTS_STATUS,
    ALLOWED_VERIFICATION_METHODS,
    load_yaml_mapping,
    parse_iso_date,
    validate_nonempty_string,
    validate_strict_live_top,
    validate_string_list,
)

URL_PATTERN = re.compile(rf"^{URL_RE}$")
ALLOWED_SOURCE_TYPES = {
    "paper",
    "dataset",
    "repo",
    "vendor",
    "standard",
    "policy",
    "benchmark",
    "leaderboard",
    "blog",
    "api",
    "other",
}
ALLOWED_SOURCE_QUALITY = {"primary", "official", "secondary", "user_note"}
ALLOWED_EVIDENCE_ROLES = {
    "supports",
    "contradicts",
    "qualifies",
    "defines",
    "dates",
    "identifies",
}
REQUIRED_ENTRY_FIELDS = (
    "evidence_id",
    "source_url",
    "source_type",
    "source_quality",
    "retrieved_at",
    "verification_method",
    "cache_ids",
    "supports",
    "excerpt",
    "rights_status",
)


def _validate_support(support: Any, *, loc: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(support, dict):
        return [f"{loc}: must be a mapping"]
    for field in ("claim_id", "field_path", "evidence_role"):
        if field not in support:
            errors.append(f"{loc}: missing required field '{field}'")
        else:
            err = validate_nonempty_string(support[field], f"{loc}.{field}")
            if err:
                errors.append(err)
    role = support.get("evidence_role")
    if isinstance(role, str) and role not in ALLOWED_EVIDENCE_ROLES:
        errors.append(f"{loc}.evidence_role: {role!r} not in {sorted(ALLOWED_EVIDENCE_ROLES)}")
    return errors


def _validate_entry(entry: dict[str, Any], *, loc: str) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_ENTRY_FIELDS:
        if field not in entry:
            errors.append(f"{loc}: missing required field '{field}'")

    for field in ("evidence_id", "source_url", "source_type", "source_quality", "verification_method", "excerpt", "rights_status"):
        if field in entry:
            err = validate_nonempty_string(entry[field], f"{loc}.{field}")
            if err:
                errors.append(err)

    if isinstance(entry.get("source_url"), str) and not URL_PATTERN.match(entry["source_url"]):
        errors.append(f"{loc}.source_url: not a valid http(s) URL: {entry['source_url']!r}")

    if "retrieved_at" in entry:
        _, err = parse_iso_date(entry["retrieved_at"], f"{loc}.retrieved_at")
        if err:
            errors.append(err)

    source_type = entry.get("source_type")
    if isinstance(source_type, str) and source_type not in ALLOWED_SOURCE_TYPES:
        errors.append(f"{loc}.source_type: {source_type!r} not in {sorted(ALLOWED_SOURCE_TYPES)}")

    source_quality = entry.get("source_quality")
    if isinstance(source_quality, str) and source_quality not in ALLOWED_SOURCE_QUALITY:
        errors.append(
            f"{loc}.source_quality: {source_quality!r} not in {sorted(ALLOWED_SOURCE_QUALITY)}"
        )

    method = entry.get("verification_method")
    if isinstance(method, str) and method not in ALLOWED_VERIFICATION_METHODS:
        errors.append(
            f"{loc}.verification_method: {method!r} not in {sorted(ALLOWED_VERIFICATION_METHODS)}"
        )

    rights = entry.get("rights_status")
    if isinstance(rights, str) and rights not in ALLOWED_RIGHTS_STATUS:
        errors.append(f"{loc}.rights_status: {rights!r} not in {sorted(ALLOWED_RIGHTS_STATUS)}")

    if "cache_ids" in entry:
        errors.extend(validate_string_list(entry["cache_ids"], f"{loc}.cache_ids"))

    supports = entry.get("supports")
    if not isinstance(supports, list) or not supports:
        errors.append(f"{loc}.supports: must be a non-empty list")
    elif isinstance(supports, list):
        for idx, support in enumerate(supports):
            errors.extend(_validate_support(support, loc=f"{loc}.supports[{idx}]"))

    if "confidence" in entry:
        confidence = entry["confidence"]
        if not isinstance(confidence, dict):
            errors.append(f"{loc}.confidence: must be a mapping when present")
        else:
            score = confidence.get("score")
            if score is not None and not (
                isinstance(score, (int, float)) and 0 <= float(score) <= 1
            ):
                errors.append(f"{loc}.confidence.score: must be a number from 0 to 1")

    return errors


def validate(path: Path) -> list[str]:
    data, errors = load_yaml_mapping(path)
    if errors:
        return errors
    assert data is not None

    errors.extend(validate_strict_live_top(data))
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
        evidence_id = entry.get("evidence_id")
        if isinstance(evidence_id, str):
            if evidence_id in seen:
                errors.append(f"{loc}: duplicate evidence_id {evidence_id!r}")
            seen.add(evidence_id)
        errors.extend(_validate_entry(entry, loc=loc))
    return errors


def _cli(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} <evidence_ledger.yml>", file=sys.stderr)
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

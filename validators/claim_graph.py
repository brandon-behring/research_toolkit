"""Validate strict-live v2 claim_graph.jsonl records."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators.jsonl_common import load_jsonl, require_string, require_string_list
from research_toolkit.retrieval_security import durable_value_errors

ALLOWED_RECORD_TYPES = {
    "entity",
    "source",
    "claim",
    "evidence",
    "cache_blob",
}
ALLOWED_CLAIM_TYPES = {
    "fact",
    "comparison",
    "trend",
    "risk",
    "recommendation",
    "contradiction",
    "open_question",
    "user_judgment",
}
ALLOWED_ENTITY_TYPES = {
    "paper",
    "author",
    "org",
    "model",
    "dataset",
    "benchmark",
    "standard",
    "repo",
    "vendor",
    "policy",
    "concept",
}
ALLOWED_STATUSES = {"active", "superseded", "conflicted", "stale", "draft"}
PROVENANCE_FIELDS = {"composed_on", "source_projects"}
ALLOWED_RECORD_FIELDS = {
    "entity": {
        "record_type",
        "id",
        "topic",
        "entity_type",
        "canonical_name",
        "aliases",
    },
    "source": {
        "record_type",
        "id",
        "topic",
        "source_url",
        "primary_url",
        "cache_ids",
    },
    "claim": {
        "record_type",
        "id",
        "topic",
        "claim_type",
        "text",
        "status",
        "evidence_ids",
        "entity_ids",
        "confidence",
        "corroboration_count",
        "synthesis_entry_id",
    },
    "evidence": {
        "record_type",
        "id",
        "topic",
        "evidence_id",
        "claim_ids",
        "cache_ids",
    },
    "cache_blob": {
        "record_type",
        "id",
        "topic",
        "cache_id",
        "sha256",
        "content_type",
        "bytes",
        "source_url",
        "fetched_at",
        "published_online",
        "extraction_status",
    },
}
for _fields in ALLOWED_RECORD_FIELDS.values():
    _fields.update(PROVENANCE_FIELDS)


def _validate_confidence(value: Any, *, loc: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return [f"{loc}.confidence: must be a mapping"]
    score = value.get("score")
    if not isinstance(score, (int, float)) or not 0 <= float(score) <= 1:
        errors.append(f"{loc}.confidence.score: must be a number from 0 to 1")
    factors = value.get("factors")
    if (
        not isinstance(factors, list)
        or not factors
        or any(not isinstance(item, str) or not item.strip() for item in factors)
    ):
        errors.append(f"{loc}.confidence.factors: must be a non-empty list")
    unexpected = sorted(set(value) - {"score", "factors"})
    if unexpected:
        errors.append(
            f"{loc}.confidence: unsupported fields {unexpected}; "
            "claim confidence is metadata-only"
        )
    return errors


def _validate_record(record: dict[str, Any], *, loc: str) -> list[str]:
    errors: list[str] = []
    errors.extend(durable_value_errors(record, loc))
    for field in ("record_type", "id", "topic"):
        errors.extend(require_string(record, field, loc))

    record_type = record.get("record_type")
    if isinstance(record_type, str) and record_type not in ALLOWED_RECORD_TYPES:
        errors.append(f"{loc}.record_type: {record_type!r} not in {sorted(ALLOWED_RECORD_TYPES)}")
    if isinstance(record_type, str) and record_type in ALLOWED_RECORD_FIELDS:
        unexpected = sorted(set(record) - ALLOWED_RECORD_FIELDS[record_type])
        if unexpected:
            errors.append(
                f"{loc}: unsupported fields for {record_type!r}: {unexpected}"
            )

    if record_type == "claim":
        for field in ("claim_type", "text", "status"):
            errors.extend(require_string(record, field, loc))
        if isinstance(record.get("claim_type"), str) and record["claim_type"] not in ALLOWED_CLAIM_TYPES:
            errors.append(
                f"{loc}.claim_type: {record['claim_type']!r} not in {sorted(ALLOWED_CLAIM_TYPES)}"
            )
        if isinstance(record.get("status"), str) and record["status"] not in ALLOWED_STATUSES:
            errors.append(f"{loc}.status: {record['status']!r} not in {sorted(ALLOWED_STATUSES)}")
        errors.extend(require_string_list(record, "evidence_ids", loc))
        errors.extend(require_string_list(record, "entity_ids", loc))
        if "confidence" not in record:
            errors.append(f"{loc}: missing required field 'confidence'")
        else:
            errors.extend(_validate_confidence(record["confidence"], loc=loc))

    elif record_type == "entity":
        errors.extend(require_string(record, "entity_type", loc))
        errors.extend(require_string(record, "canonical_name", loc))
        if isinstance(record.get("entity_type"), str) and record["entity_type"] not in ALLOWED_ENTITY_TYPES:
            errors.append(
                f"{loc}.entity_type: {record['entity_type']!r} not in {sorted(ALLOWED_ENTITY_TYPES)}"
            )
        aliases = record.get("aliases")
        if aliases is not None and (
            not isinstance(aliases, list)
            or any(not isinstance(alias, str) or not alias.strip() for alias in aliases)
        ):
            errors.append(f"{loc}.aliases: must be a list of non-empty strings when present")

    elif record_type == "source":
        errors.extend(require_string(record, "source_url", loc))
        errors.extend(require_string_list(record, "cache_ids", loc))

    elif record_type == "evidence":
        errors.extend(require_string(record, "evidence_id", loc))
        errors.extend(require_string_list(record, "claim_ids", loc))
        errors.extend(require_string_list(record, "cache_ids", loc))

    elif record_type == "cache_blob":
        errors.extend(require_string(record, "cache_id", loc))
        errors.extend(require_string(record, "sha256", loc))

    return errors


def validate_record(record: dict[str, Any], *, loc: str) -> list[str]:
    """Validate one in-memory graph record for producers and export gates."""
    return _validate_record(record, loc=loc)


def validate(path: Path) -> list[str]:
    records, errors = load_jsonl(path)
    seen: set[str] = set()
    for idx, record in enumerate(records):
        loc = f"line {idx + 1}"
        record_id = record.get("id")
        if isinstance(record_id, str):
            if record_id in seen:
                errors.append(f"{loc}: duplicate id {record_id!r}")
            seen.add(record_id)
        errors.extend(_validate_record(record, loc=loc))
    return errors


def _cli(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} <claim_graph.jsonl>", file=sys.stderr)
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

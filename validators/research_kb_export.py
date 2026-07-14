"""Validate strict-live v2 research_kb_export.jsonl records."""
from __future__ import annotations

import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators.jsonl_common import load_jsonl, require_string
from validators.v2_common import ALLOWED_RIGHTS_STATUS, parse_iso_date
from validators import claim_graph
from research_toolkit.retrieval_security import durable_value_errors

ALLOWED_RECORD_TYPES = set(claim_graph.ALLOWED_RECORD_TYPES)
ALLOWED_POLICY_VISIBILITY = {"public", "authenticated", "private", "unknown"}
ENVELOPE_FIELDS = {
    "export_schema_version",
    "record_type",
    "id",
    "source_project",
    "exported_at",
    "payload",
}
METADATA_FIELDS = {
    record_type: set(fields)
    for record_type, fields in claim_graph.ALLOWED_RECORD_FIELDS.items()
}
BODY_FIELD_NAMES = {
    "blob",
    "body",
    "body_text",
    "bytes_base64",
    "content",
    "document",
    "excerpt",
    "html",
    "markdown",
    "quote",
    "raw",
    "raw_body",
    "raw_bytes",
    "raw_content",
    "raw_path",
    "text_path",
}


def find_body_fields(value: object, *, path: str = "payload") -> list[str]:
    """Return paths whose names identify cached body material."""
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            text = str(key)
            text = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", text)
            text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)
            normalized = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").lower()
            if (
                normalized in BODY_FIELD_NAMES
                or normalized.endswith("_body")
                or normalized.endswith("_base64")
            ):
                found.append(child_path)
            else:
                found.extend(find_body_fields(child, path=child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(find_body_fields(child, path=f"{path}[{index}]"))
    return found


def referenced_cache_ids(payload: dict) -> set[str]:
    """Return every syntactically valid cache ID referenced by a payload."""
    result: set[str] = set()
    cache_id = payload.get("cache_id")
    if isinstance(cache_id, str):
        result.add(cache_id)
    cache_ids = payload.get("cache_ids")
    if isinstance(cache_ids, list):
        result.update(value for value in cache_ids if isinstance(value, str))
    return result


def validate_metadata_only_payload(
    payload: dict,
    *,
    loc: str,
    allow_rights_policy: bool,
) -> list[str]:
    """Fail closed on every field in an exported metadata payload."""
    record_type = payload.get("record_type")
    allowed = METADATA_FIELDS.get(record_type)
    if allowed is None:
        return [
            f"{loc}: is not metadata-only; record_type {record_type!r} may not "
            "cross the synthesis export boundary"
        ]
    allowed_fields = set(allowed)
    if allow_rights_policy and record_type == "cache_blob":
        allowed_fields.add("rights_policy")
    unexpected = sorted(set(payload) - allowed_fields)
    errors: list[str] = []
    if "cache_id" in payload and (
        not isinstance(payload["cache_id"], str) or not payload["cache_id"].strip()
    ):
        errors.append(f"{loc}.cache_id: must be a non-empty string")
    if "cache_ids" in payload:
        cache_ids = payload["cache_ids"]
        if (
            not isinstance(cache_ids, list)
            or not cache_ids
            or any(not isinstance(value, str) or not value.strip() for value in cache_ids)
        ):
            errors.append(f"{loc}.cache_ids: must be a non-empty list of strings")
    if unexpected:
        errors.append(
            f"{loc}: is not metadata-only; unsupported cache-linked fields "
            f"{unexpected}"
        )
    body_fields = find_body_fields(payload, path=loc)
    if body_fields:
        errors.append(
            f"{loc}: metadata-only export contains cached body fields {body_fields}"
        )
    return errors


def _validate_cache_rights_policy(payload: dict, *, loc: str) -> list[str]:
    errors: list[str] = []
    policy = payload.get("rights_policy")
    policy_loc = f"{loc}.payload.rights_policy"
    if not isinstance(policy, dict):
        return [f"{policy_loc}: must be a mapping for cache_blob records"]
    unexpected = sorted(
        set(policy)
        - {
            "vocabulary",
            "rights_status",
            "visibility",
            "restricted",
            "body_exported",
        }
    )
    if unexpected:
        errors.append(
            f"{policy_loc}: unsupported fields in rights policy {unexpected}"
        )
    if policy.get("vocabulary") != "strict-live-cache-v2":
        errors.append(f"{policy_loc}.vocabulary: must be 'strict-live-cache-v2'")
    rights = policy.get("rights_status")
    if rights not in ALLOWED_RIGHTS_STATUS:
        errors.append(
            f"{policy_loc}.rights_status: {rights!r} not in "
            f"{sorted(ALLOWED_RIGHTS_STATUS)}"
        )
    visibility = policy.get("visibility")
    if visibility not in ALLOWED_POLICY_VISIBILITY:
        errors.append(
            f"{policy_loc}.visibility: {visibility!r} not in "
            f"{sorted(ALLOWED_POLICY_VISIBILITY)}"
        )
    restricted = policy.get("restricted")
    if not isinstance(restricted, bool):
        errors.append(f"{policy_loc}.restricted: must be boolean")
    elif restricted is False and (rights != "public" or visibility != "public"):
        errors.append(
            f"{policy_loc}.restricted: false requires public rights and visibility"
        )
    if policy.get("body_exported") is not False:
        errors.append(f"{policy_loc}.body_exported: must be false")
    return errors


def validate(path: Path) -> list[str]:
    records, errors = load_jsonl(path)
    seen: set[str] = set()
    referenced: set[str] = set()
    cache_blob_ids: set[str] = set()
    for idx, record in enumerate(records):
        loc = f"line {idx + 1}"
        errors.extend(durable_value_errors(record, loc))
        unexpected_envelope = sorted(set(record) - ENVELOPE_FIELDS)
        if unexpected_envelope:
            errors.append(
                f"{loc}: unsupported export envelope fields {unexpected_envelope}"
            )
        if record.get("export_schema_version") != 2:
            errors.append(f"{loc}.export_schema_version: must be 2")
        for field in ("record_type", "id", "source_project", "exported_at"):
            errors.extend(require_string(record, field, loc))
        record_type = record.get("record_type")
        if isinstance(record_type, str) and record_type not in ALLOWED_RECORD_TYPES:
            errors.append(f"{loc}.record_type: {record_type!r} not in {sorted(ALLOWED_RECORD_TYPES)}")
        if "exported_at" in record:
            _, err = parse_iso_date(record["exported_at"], f"{loc}.exported_at")
            if err:
                errors.append(err)
        payload = record.get("payload")
        if not isinstance(payload, dict) or not payload:
            errors.append(f"{loc}.payload: must be a non-empty object")
        else:
            payload_type = payload.get("record_type")
            if payload_type != record_type:
                errors.append(
                    f"{loc}.payload.record_type: {payload_type!r} does not match "
                    f"envelope record_type {record_type!r}"
                )
            payload_cache_ids = referenced_cache_ids(payload)
            referenced.update(payload_cache_ids)
            errors.extend(
                validate_metadata_only_payload(
                    payload,
                    loc=f"{loc}.payload",
                    allow_rights_policy=True,
                )
            )
            graph_payload = dict(payload)
            graph_payload.pop("rights_policy", None)
            errors.extend(
                claim_graph.validate_record(
                    graph_payload,
                    loc=f"{loc}.payload",
                )
            )
            if payload_type == "cache_blob":
                cache_blob_ids.update(payload_cache_ids)
                errors.extend(_validate_cache_rights_policy(payload, loc=loc))
        record_id = record.get("id")
        if isinstance(record_id, str):
            if record_id in seen:
                errors.append(f"{loc}: duplicate id {record_id!r}")
            seen.add(record_id)
    missing_policy_records = sorted(referenced - cache_blob_ids)
    if missing_policy_records:
        errors.append(
            "export cache references lack cache_blob policy records: "
            f"{missing_policy_records}"
        )
    return errors


def _cli(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} <research_kb_export.jsonl>", file=sys.stderr)
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

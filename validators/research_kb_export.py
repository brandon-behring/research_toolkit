"""Validate strict-live v2 research_kb_export.jsonl records."""
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators.jsonl_common import load_jsonl, require_string
from validators.v2_common import parse_iso_date

ALLOWED_RECORD_TYPES = {
    "entity",
    "source",
    "claim",
    "evidence",
    "topic_membership",
    "cache_blob",
    "project_dashboard",
}


def validate(path: Path) -> list[str]:
    records, errors = load_jsonl(path)
    seen: set[str] = set()
    for idx, record in enumerate(records):
        loc = f"line {idx + 1}"
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
        record_id = record.get("id")
        if isinstance(record_id, str):
            if record_id in seen:
                errors.append(f"{loc}: duplicate id {record_id!r}")
            seen.add(record_id)
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

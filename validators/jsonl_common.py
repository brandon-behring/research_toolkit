"""Shared JSONL validator helpers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_no}: JSON parse error: {exc}")
            continue
        if not isinstance(record, dict):
            errors.append(f"line {line_no}: record must be a JSON object")
            continue
        records.append(record)
    if not records and not errors:
        errors.append("JSONL file must contain at least one record")
    return records, errors


def require_string(record: dict[str, Any], field: str, loc: str) -> list[str]:
    value = record.get(field)
    if not isinstance(value, str):
        return [f"{loc}.{field}: must be a string"]
    if not value.strip():
        return [f"{loc}.{field}: must be non-empty"]
    return []


def require_string_list(record: dict[str, Any], field: str, loc: str) -> list[str]:
    value = record.get(field)
    if not isinstance(value, list) or not value:
        return [f"{loc}.{field}: must be a non-empty list"]
    errors: list[str] = []
    for idx, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{loc}.{field}[{idx}]: must be a non-empty string")
    return errors

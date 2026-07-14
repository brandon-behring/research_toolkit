"""Load and validate versioned research record JSON Schemas.

The validator intentionally implements the small JSON Schema subset used by
this repository. Keeping it dependency-free lets the same contract checks run
inside Claude Code, CI, and a plain Python installation.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SCHEMA_VERSION = "1.0.0"
SCHEMA_ROOT = Path(__file__).resolve().parent.parent / "schemas" / "v1"

CORE_SCHEMAS = {
    "claim-record",
    "claim-review-record",
    "consumer-binding",
    "dossier-manifest",
    "evidence-record",
    "refresh-event",
    "research-lock",
    "research-release-manifest",
    "research-run-manifest",
    "source-record",
    "source-watch-record",
}


def load_schema(name: str) -> dict[str, Any]:
    """Return a bundled v1 schema by its stem."""
    if name not in CORE_SCHEMAS:
        raise ValueError(f"unknown schema: {name}")
    path = SCHEMA_ROOT / f"{name}.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def _format_valid(value: str, format_name: str) -> bool:
    try:
        if format_name == "date":
            date.fromisoformat(value)
            return True
        if format_name == "date-time":
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            return "T" in value
        if format_name == "uri":
            parsed = urlparse(value)
            return bool(parsed.scheme and (parsed.netloc or parsed.scheme == "urn"))
    except ValueError:
        return False
    return True


def _validate(value: Any, schema: dict[str, Any], loc: str) -> list[str]:
    errors: list[str] = []

    expected = schema.get("type")
    if expected is not None:
        choices = expected if isinstance(expected, list) else [expected]
        if not any(_matches_type(value, item) for item in choices):
            return [f"{loc}: expected {' or '.join(choices)}, got {type(value).__name__}"]

    if "const" in schema and value != schema["const"]:
        errors.append(f"{loc}: expected constant {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{loc}: {value!r} is not one of {schema['enum']!r}")

    if isinstance(value, str):
        minimum = schema.get("minLength")
        if isinstance(minimum, int) and len(value) < minimum:
            errors.append(f"{loc}: string is shorter than {minimum}")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.fullmatch(pattern, value) is None:
            errors.append(f"{loc}: {value!r} does not match {pattern!r}")
        format_name = schema.get("format")
        if isinstance(format_name, str) and not _format_valid(value, format_name):
            errors.append(f"{loc}: {value!r} is not a valid {format_name}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{loc}: {value} is below minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{loc}: {value} is above maximum {schema['maximum']}")

    if isinstance(value, list):
        minimum = schema.get("minItems")
        if isinstance(minimum, int) and len(value) < minimum:
            errors.append(f"{loc}: array has fewer than {minimum} items")
        if schema.get("uniqueItems"):
            encoded = [json.dumps(item, sort_keys=True) for item in value]
            if len(encoded) != len(set(encoded)):
                errors.append(f"{loc}: array items must be unique")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(_validate(item, item_schema, f"{loc}[{index}]"))

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{loc}.{key}: required field is missing")
        properties = schema.get("properties", {})
        for key, item in value.items():
            if key in properties:
                errors.extend(_validate(item, properties[key], f"{loc}.{key}"))
            elif schema.get("additionalProperties") is False:
                errors.append(f"{loc}.{key}: unexpected field")

    return errors


def validate_record(record: dict[str, Any], schema_name: str) -> list[str]:
    """Validate one record and return location-prefixed errors."""
    schema = load_schema(schema_name)
    return _validate(record, schema, schema_name)


def validate_schema_bundle() -> list[str]:
    """Check that all declared schemas are readable and internally versioned."""
    errors: list[str] = []
    for name in sorted(CORE_SCHEMAS):
        try:
            schema = load_schema(name)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{name}: cannot load schema: {exc}")
            continue
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            errors.append(f"{name}: unsupported or missing $schema declaration")
        version = schema.get("properties", {}).get("schema_version", {}).get("const")
        if version != SCHEMA_VERSION:
            errors.append(f"{name}: schema_version const must be {SCHEMA_VERSION!r}")
    return errors


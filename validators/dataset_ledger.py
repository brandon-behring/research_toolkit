"""Validate dataset_ledger.yml schema (v1.6).

The dataset pipeline parallels the paper pipeline but with different artifact
shapes. A dataset entry captures discovery metadata (where it lives, how to
access, what schema, what tasks it's used for) — not bibliography.

Required fields per entry:
    bibkey | primary_url | name | source | status | task_family

Optional fields (the "rich metadata" tier — populated when /dataset-gather
WebFetched the source page):
    license          (str) — e.g., "CC-BY-4.0", "MIT", "custom", "unknown".
    size             (str) — human-readable, e.g., "1.2GB", "5M tokens".
    rows             (int|str) — when known.
    columns          (int|str) — when known (or "tabular: <N>").
    schema_url       (str) — link to the dataset card / schema page if the
                              source has one.
    access_method    (str) — "hf datasets", "direct", "API", "signup wall".
    auth_required    (bool) — true if downloading requires login / API key.
    citation         (str) — recommended citation form (BibTeX-friendly).

`task_family` is a fixed enum (v1.6):
    classification | regression | sequence_labeling | generation | retrieval |
    ranking | multimodal | graph | time_series | tabular | recommendation |
    structured_prediction | other

`source` is a free-string but conventionally one of:
    huggingface | kaggle | zenodo | osf | figshare | icpsr | aws_open_data |
    gcp_public | azure_open | nih | ncbi | fred | nasa | common_crawl |
    data_gov | uci | openml | paperswithcode | github | other

Asserts bibkey uniqueness across the ledger; URL well-formed; task_family in
enum; auth_required is bool when present.

Memory-verification anti-cheat heuristic (parallels bib_ledger v1.2 but with
a lower threshold for datasets, since per-topic dataset counts are typically
smaller than per-topic paper counts):

    If a ledger has ≥30 entries AND every single entry has `status: verified`,
    that's the signature of a discovery skill that bulk-marked entries from
    memory rather than per-source WebFetch. Default behavior: emit a warning
    to stderr; --strict promotes to error.

    Usage:
        python -m validators.dataset_ledger ledger.yml             # warns
        python -m validators.dataset_ledger ledger.yml --strict    # errors
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators._common import URL_RE, cli_main
from validators.v2_common import (
    is_strict_live,
    is_v2_mapping,
    validate_strict_live_entry,
    validate_strict_live_top,
)

ALLOWED_STATUS = {"unverified", "verified", "mismatched"}
ALLOWED_TASK_FAMILY = {
    "classification",
    "regression",
    "sequence_labeling",
    "generation",
    "retrieval",
    "ranking",
    "multimodal",
    "graph",
    "time_series",
    "tabular",
    "recommendation",
    "structured_prediction",
    "other",
}
REQUIRED_FIELDS = (
    "bibkey",
    "primary_url",
    "name",
    "source",
    "status",
    "task_family",
)
OPTIONAL_STRING_FIELDS = (
    "license",
    "size",
    "schema_url",
    "access_method",
    "citation",
)
OPTIONAL_INT_OR_STRING_FIELDS = ("rows", "columns")
URL_PATTERN = re.compile(rf"^{URL_RE}$")

MEMORY_VERIFIED_THRESHOLD = 30  # ≥ this many entries triggers the anti-cheat check


def _memory_verified_warning(entries: list[dict]) -> str | None:
    """Detect bulk-mark-from-memory anti-pattern.

    Lower threshold than bib_ledger's 50 because dataset ledgers are typically
    smaller per topic (30-50 datasets vs 50-90 papers).
    """
    if len(entries) < MEMORY_VERIFIED_THRESHOLD:
        return None
    statuses = [e.get("status") for e in entries if isinstance(e, dict)]
    if not statuses:
        return None
    if all(s == "verified" for s in statuses):
        return (
            f"WARN memory-verification suspected: {len(statuses)} dataset entries, "
            f"all marked 'verified' (no 'unverified' or 'mismatched'). Per-source "
            f"WebFetch verification typically produces ≥2 mismatched/unverified "
            f"entries on a run this size. --strict promotes to error"
        )
    return None


def validate(path: Path, *, strict: bool = False) -> list[str]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [f"YAML parse error: {exc}"]

    if not isinstance(data, dict) or "entries" not in data:
        return ["top-level must be a mapping with key 'entries:'"]

    # Out-of-scope v2/v3 variant: declares a schema_version but isn't strict-live → n/a. v1
    # ledgers and genuine strict-live ledgers both fall through to validation.
    if is_v2_mapping(data) and not is_strict_live(data):
        return []

    v2 = is_v2_mapping(data)
    if v2:
        errors.extend(validate_strict_live_top(data))

    entries = data["entries"]
    if not isinstance(entries, list) or not entries:
        return ["'entries' must be a non-empty list"]

    seen_bibkeys: set[str] = set()
    for idx, entry in enumerate(entries):
        loc = f"entries[{idx}]"
        if not isinstance(entry, dict):
            errors.append(f"{loc}: must be a mapping")
            continue

        for field in REQUIRED_FIELDS:
            if field not in entry:
                errors.append(f"{loc}: missing required field '{field}'")
            elif not isinstance(entry[field], str):
                errors.append(f"{loc}.{field}: must be a string")
            elif not entry[field].strip():
                errors.append(f"{loc}.{field}: must be non-empty")

        for field in OPTIONAL_STRING_FIELDS:
            if field in entry:
                value = entry[field]
                if not isinstance(value, str):
                    errors.append(f"{loc}.{field}: must be a string when present")
                elif not value.strip():
                    errors.append(
                        f"{loc}.{field}: when present, must be non-empty "
                        f"(omit the field rather than use empty string)"
                    )

        for field in OPTIONAL_INT_OR_STRING_FIELDS:
            if field in entry:
                value = entry[field]
                if not isinstance(value, (int, str)):
                    errors.append(
                        f"{loc}.{field}: must be int or string when present "
                        f"(got {type(value).__name__})"
                    )
                elif isinstance(value, str) and not value.strip():
                    errors.append(f"{loc}.{field}: empty string; omit the field instead")

        if "auth_required" in entry:
            value = entry["auth_required"]
            if not isinstance(value, bool):
                errors.append(
                    f"{loc}.auth_required: must be a boolean (true/false), "
                    f"got {type(value).__name__}"
                )

        bibkey = entry.get("bibkey")
        if isinstance(bibkey, str):
            if bibkey in seen_bibkeys:
                errors.append(f"{loc}: duplicate bibkey '{bibkey}'")
            seen_bibkeys.add(bibkey)

        url = entry.get("primary_url")
        if isinstance(url, str) and url.strip():
            if not URL_PATTERN.match(url.strip()):
                errors.append(f"{loc}.primary_url: not a valid http(s) URL: {url!r}")

        schema_url = entry.get("schema_url")
        if isinstance(schema_url, str) and schema_url.strip():
            if not URL_PATTERN.match(schema_url.strip()):
                errors.append(
                    f"{loc}.schema_url: not a valid http(s) URL: {schema_url!r}"
                )

        status = entry.get("status")
        if isinstance(status, str) and status not in ALLOWED_STATUS:
            errors.append(
                f"{loc}.status: {status!r} not in {sorted(ALLOWED_STATUS)}"
            )

        task_family = entry.get("task_family")
        if isinstance(task_family, str) and task_family not in ALLOWED_TASK_FAMILY:
            errors.append(
                f"{loc}.task_family: {task_family!r} not in fixed enum "
                f"{sorted(ALLOWED_TASK_FAMILY)}"
            )

        if v2:
            errors.extend(validate_strict_live_entry(entry, loc=loc))

    only_dicts = [e for e in entries if isinstance(e, dict)]
    warning = _memory_verified_warning(only_dicts)
    if warning:
        if strict:
            errors.append(warning)
        else:
            warnings.append(warning)

    if warnings and not strict:
        for w in warnings:
            print(f"  - {w}", file=sys.stderr)

    return errors


def _cli_with_strict(argv: list[str]) -> int:
    strict = False
    args = argv[1:]
    if "--strict" in args:
        strict = True
        args = [a for a in args if a != "--strict"]
    if len(args) != 1:
        print(f"usage: {Path(argv[0]).name} [--strict] <path>", file=sys.stderr)
        return 2
    target = Path(args[0]).expanduser().resolve()
    if not target.exists():
        print(f"error: path does not exist: {target}", file=sys.stderr)
        return 2
    errors = validate(target, strict=strict)
    if errors:
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        print(
            f"VALIDATION FAILED: {len(errors)} error(s) in {target}",
            file=sys.stderr,
        )
        return 1
    print(f"OK: {target}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(_cli_with_strict(sys.argv))

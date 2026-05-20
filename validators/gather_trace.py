"""Validate strict-live v2.2 gather_trace.yml (Self-RAG-style adaptive retrieval trace).

A gather_trace records the per-fetch reflection (IsRel/IsSup/IsUse) that
/research-gather Phase 2 emits for each WebSearch+WebFetch. /freshness-audit
Phase 4 reads it for discovery-rigor metrics.

Sibling artifact pattern to cache_manifest.yml. Cross-references bib_ledger.yml
when assigned_bibkey is present (decision == accept implies assignment).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators._common import URL_RE
from validators.v2_common import (
    load_yaml_mapping,
    parse_iso_date,
    validate_nonempty_string,
    validate_strict_live_top,
)

import re

URL_PATTERN = re.compile(rf"^{URL_RE}$")
ALLOWED_IS_SUPPORTED = {"full", "partial", "none"}
ALLOWED_DECISION = {"accept", "reject", "escalate_to_manual"}

REQUIRED_FETCH_FIELDS = (
    "fetch_id",
    "sub_area",
    "query",
    "source_url",
    "fetched_at",
    "reflection",
    "decision",
    "reason",
)

REQUIRED_REFLECTION_FIELDS = (
    "is_relevant",
    "is_supported",
    "is_useful",
)


def _validate_reflection(reflection: Any, loc: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(reflection, dict):
        errors.append(f"{loc}: must be a mapping")
        return errors

    for field in REQUIRED_REFLECTION_FIELDS:
        if field not in reflection:
            errors.append(f"{loc}: missing required field {field!r}")

    if "is_relevant" in reflection and not isinstance(reflection["is_relevant"], bool):
        errors.append(f"{loc}.is_relevant: must be boolean")

    is_supported = reflection.get("is_supported")
    if is_supported is not None and is_supported not in ALLOWED_IS_SUPPORTED:
        errors.append(
            f"{loc}.is_supported: {is_supported!r} not in {sorted(ALLOWED_IS_SUPPORTED)}"
        )

    is_useful = reflection.get("is_useful")
    if is_useful is not None:
        if not isinstance(is_useful, int) or not (1 <= is_useful <= 5):
            errors.append(f"{loc}.is_useful: must be integer in [1, 5]")

    return errors


def _validate_fetch(
    fetch: dict[str, Any],
    *,
    loc: str,
    known_bibkeys: set[str] | None,
) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_FETCH_FIELDS:
        if field not in fetch:
            errors.append(f"{loc}: missing required field {field!r}")

    for field in ("fetch_id", "sub_area", "query", "reason"):
        if field in fetch:
            err = validate_nonempty_string(fetch[field], f"{loc}.{field}")
            if err:
                errors.append(err)

    source_url = fetch.get("source_url")
    if isinstance(source_url, str) and not URL_PATTERN.match(source_url):
        errors.append(f"{loc}.source_url: not a valid http(s) URL: {source_url!r}")

    if "fetched_at" in fetch:
        _, err = parse_iso_date(fetch["fetched_at"], f"{loc}.fetched_at")
        if err:
            errors.append(err)

    if "reflection" in fetch:
        errors.extend(_validate_reflection(fetch["reflection"], f"{loc}.reflection"))

    decision = fetch.get("decision")
    if decision is not None and decision not in ALLOWED_DECISION:
        errors.append(f"{loc}.decision: {decision!r} not in {sorted(ALLOWED_DECISION)}")

    assigned_bibkey = fetch.get("assigned_bibkey")
    if assigned_bibkey is not None:
        if not isinstance(assigned_bibkey, str) or not assigned_bibkey.strip():
            errors.append(f"{loc}.assigned_bibkey: must be a non-empty string when present")
        elif known_bibkeys is not None and assigned_bibkey not in known_bibkeys:
            import difflib
            close = difflib.get_close_matches(assigned_bibkey, known_bibkeys, n=2, cutoff=0.6)
            hint = f" (closest match: {close})" if close else ""
            errors.append(
                f"{loc}.assigned_bibkey: {assigned_bibkey!r} not found in bib_ledger{hint}"
            )

    # accept requires assigned_bibkey; reject/escalate must NOT have one
    if decision == "accept" and assigned_bibkey is None:
        errors.append(
            f"{loc}: decision 'accept' requires an assigned_bibkey"
        )
    if decision in ("reject", "escalate_to_manual") and assigned_bibkey is not None:
        errors.append(
            f"{loc}: decision {decision!r} must not have an assigned_bibkey"
        )

    return errors


def _collect_bibkeys(trace_path: Path) -> set[str] | None:
    """If a sibling bib_ledger.yml exists, return its bibkeys for cross-ref.
    Otherwise return None (skip cross-ref check)."""
    candidate = trace_path.parent / "bib_ledger.yml"
    if not candidate.exists():
        return None
    data, errors = load_yaml_mapping(candidate)
    if errors or data is None:
        return None
    entries = data.get("entries")
    if not isinstance(entries, list):
        return None
    bibkeys = set()
    for entry in entries:
        if isinstance(entry, dict):
            key = entry.get("bibkey")
            if isinstance(key, str) and key.strip():
                bibkeys.add(key)
    return bibkeys


def validate(path: Path) -> list[str]:
    data, errors = load_yaml_mapping(path)
    if errors:
        return errors
    assert data is not None

    errors.extend(validate_strict_live_top(data))

    fetches = data.get("fetches")
    if not isinstance(fetches, list) or not fetches:
        errors.append("'fetches' must be a non-empty list")
        return errors

    known_bibkeys = _collect_bibkeys(path)

    seen_ids: set[str] = set()
    for idx, fetch in enumerate(fetches):
        loc = f"fetches[{idx}]"
        if not isinstance(fetch, dict):
            errors.append(f"{loc}: must be a mapping")
            continue
        fetch_id = fetch.get("fetch_id")
        if isinstance(fetch_id, str):
            if fetch_id in seen_ids:
                errors.append(f"{loc}: duplicate fetch_id {fetch_id!r}")
            seen_ids.add(fetch_id)
        errors.extend(_validate_fetch(fetch, loc=loc, known_bibkeys=known_bibkeys))

    return errors


def _cli(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} <gather_trace.yml>", file=sys.stderr)
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

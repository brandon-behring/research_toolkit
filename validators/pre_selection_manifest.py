"""Validate strict-live v2.2 pre_selection_manifest.yml.

Written by /agent-index Phase 2b (Attribute-First planning step). Encodes the
structural anti-hallucination commitment: before any bullet is generated, the
spans that will become its evidence must be selected and recorded here.

Validators cross-reference with claim_graph.jsonl (atom_ids exist as claim
records) and cache_manifest.yml (cache_ids resolve). Excerpts are verified
via the v3 substring + sha256 + bytes-equality check from v2_common, same as
evidence_ledger.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators.jsonl_common import load_jsonl
from validators.v2_common import (
    load_yaml_mapping,
    validate_nonempty_string,
    validate_strict_live_top,
    verify_excerpt_anchor,
)

REQUIRED_SELECTION_FIELDS = (
    "selection_id",
    "bullet_id",
    "atom_id",
    "cache_id",
    "span",
)

REQUIRED_SPAN_FIELDS = (
    "text_path_offset",
    "sha256_of_span",
    "excerpt",
)


def _load_cache_entries(
    manifest_path: Path,
) -> tuple[dict[str, dict[str, Any]], Path | None, str | None]:
    """Sibling cache_manifest.yml lookup.

    Returns ``(cache_entries_by_id, cache_manifest_path, cache_root)``.
    All three are None / empty when the sibling manifest is missing.
    ``cache_root`` is the top-level field from the manifest (v2.3+ relative
    path resolution base).
    """
    candidate = manifest_path.parent / "cache_manifest.yml"
    if not candidate.exists():
        return {}, None, None
    data, _errs = load_yaml_mapping(candidate)
    if not isinstance(data, dict):
        return {}, candidate, None
    entries = data.get("entries")
    if not isinstance(entries, list):
        return {}, candidate, None
    by_id: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if isinstance(entry, dict):
            cid = entry.get("cache_id")
            if isinstance(cid, str):
                by_id[cid] = entry
    cache_root = data.get("cache_root") if isinstance(data.get("cache_root"), str) else None
    return by_id, candidate, cache_root


def _load_atom_ids(manifest_path: Path) -> set[str] | None:
    """Sibling claim_graph.jsonl lookup. Returns set of claim IDs or None if absent."""
    candidate = manifest_path.parent / "claim_graph.jsonl"
    if not candidate.exists():
        return None
    records, _errs = load_jsonl(candidate)
    ids: set[str] = set()
    for record in records:
        if isinstance(record, dict) and record.get("record_type") == "claim":
            rid = record.get("id")
            if isinstance(rid, str):
                ids.add(rid)
    return ids


def _validate_selection(
    selection: dict[str, Any],
    *,
    loc: str,
    cache_entries_by_id: dict[str, dict[str, Any]],
    cache_manifest_path: Path | None,
    cache_root: str | None,
    known_atom_ids: set[str] | None,
) -> list[str]:
    errors: list[str] = []

    for field in REQUIRED_SELECTION_FIELDS:
        if field not in selection:
            errors.append(f"{loc}: missing required field {field!r}")

    for field in ("selection_id", "bullet_id", "atom_id", "cache_id"):
        if field in selection:
            err = validate_nonempty_string(selection[field], f"{loc}.{field}")
            if err:
                errors.append(err)

    atom_id = selection.get("atom_id")
    if isinstance(atom_id, str) and known_atom_ids is not None:
        if atom_id not in known_atom_ids:
            errors.append(
                f"{loc}.atom_id: {atom_id!r} not found among claim records in sibling "
                f"claim_graph.jsonl. Pre-selection must commit to atoms that exist."
            )

    # v2.3 C2: optional synthesis_entry_ref. Validated for shape only —
    # build_claim_graph.py does the cross-file resolution (synthesis_id lookup +
    # source_urls corroboration warning).
    synthesis_ref = selection.get("synthesis_entry_ref")
    if synthesis_ref is not None:
        if not isinstance(synthesis_ref, str) or not synthesis_ref.startswith("syn_"):
            errors.append(
                f"{loc}.synthesis_entry_ref: must be a string of the form "
                f"'syn_<topic>_<slug>' (got {synthesis_ref!r})"
            )

    span = selection.get("span")
    if not isinstance(span, dict):
        errors.append(f"{loc}.span: must be a mapping")
        return errors

    for field in REQUIRED_SPAN_FIELDS:
        if field not in span:
            errors.append(f"{loc}.span: missing required field {field!r}")

    excerpt = span.get("excerpt")
    cache_id = selection.get("cache_id")
    offset = span.get("text_path_offset")
    sha256_of_span = span.get("sha256_of_span")
    if (
        isinstance(excerpt, str)
        and isinstance(cache_id, str)
        and isinstance(offset, list)
        and isinstance(sha256_of_span, str)
        and cache_manifest_path is not None
    ):
        errors.extend(
            verify_excerpt_anchor(
                excerpt=excerpt,
                cache_id=cache_id,
                text_path_offset=offset,
                sha256_of_span=sha256_of_span,
                cache_entries_by_id=cache_entries_by_id,
                manifest_path=cache_manifest_path,
                cache_root=cache_root,
                loc=f"{loc}.span",
            )
        )

    return errors


def validate(path: Path) -> list[str]:
    data, errors = load_yaml_mapping(path)
    if errors:
        return errors
    assert data is not None

    errors.extend(validate_strict_live_top(data))

    selections = data.get("selections")
    if not isinstance(selections, list) or not selections:
        errors.append("'selections' must be a non-empty list")
        return errors

    cache_entries_by_id, cache_manifest_path, cache_root = _load_cache_entries(path)
    known_atom_ids = _load_atom_ids(path)

    seen_ids: set[str] = set()
    for idx, selection in enumerate(selections):
        loc = f"selections[{idx}]"
        if not isinstance(selection, dict):
            errors.append(f"{loc}: must be a mapping")
            continue
        sid = selection.get("selection_id")
        if isinstance(sid, str):
            if sid in seen_ids:
                errors.append(f"{loc}: duplicate selection_id {sid!r}")
            seen_ids.add(sid)
        errors.extend(
            _validate_selection(
                selection,
                loc=loc,
                cache_entries_by_id=cache_entries_by_id,
                cache_manifest_path=cache_manifest_path,
                cache_root=cache_root,
                known_atom_ids=known_atom_ids,
            )
        )

    return errors


def _cli(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} <pre_selection_manifest.yml>", file=sys.stderr)
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

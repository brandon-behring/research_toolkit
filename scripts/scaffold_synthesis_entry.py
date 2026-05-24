#!/usr/bin/env python3
"""Draft synthesis_entry.yml entries from a project's claim_graph (v2.4+).

Closes the v2.4 producer gap for synthesis_entry.yml. Reads:
- ``claim_graph.jsonl`` → find ``claim_synthesis_*`` atoms with
  ``corroboration_count >= 3`` (the synthesis_entry validator's bar).
- ``evidence_ledger.yml`` → resolve each atom's supporting evidence to
  the union of source_urls + the dominant freshness_tier.
- ``bib_ledger.yml`` → resolve each atom's entity_ids to the dominant
  claim_family.

For each qualifying atom, emit a draft ``synthesis_entry`` block with:
- ``synthesis_id`` — derived from atom_id (``claim_synthesis_<topic>_<slug>``
  → ``syn_<topic>_<slug>``).
- ``source_urls`` — union of source_urls across supporting evidence,
  sorted for determinism.
- ``title`` — copied from the claim_graph claim text (author rewrites
  during /agent-index Phase 4c).
- ``claim_family`` — dominant value across supporting bib_ledger entries.
- ``volatility`` — derived from the most-volatile freshness_tier across
  supporters (synthesis inherits least-stable per the template comment).
- ``tier_summary`` — computed via ``scripts/source_tiers.tier_summary``.
- ``status`` — ``unverified`` (author flips to verified after writing
  attribution_map and confirming sources are still live).
- ``attribution_map`` — left as a placeholder comment; author fills it
  in during /agent-index Phase 4c.

Usage:
    python scripts/scaffold_synthesis_entry.py <project_dir>
    python scripts/scaffold_synthesis_entry.py <project_dir> --output PATH
    python scripts/scaffold_synthesis_entry.py <project_dir> --merge

Default output: ``<project_dir>/synthesis_entry.yml``. Refuses to overwrite
an existing file unless ``--merge`` is set; with --merge, hand-authored
entries are preserved and only new synthesis_ids are appended.

Validates output via ``validators/synthesis_entry.py`` before writing —
matches the byte-stable pattern used by ``scripts/build_claim_graph.py:write()``.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(REPO_ROOT))

from scripts.source_tiers import tier_summary  # noqa: E402
from validators import synthesis_entry as synth_validator  # noqa: E402
from validators.v2_common import load_yaml_mapping  # noqa: E402


# Map freshness_tier (bib_ledger) → volatility (synthesis_entry).
# Synthesis "inherits the least-stable source's volatility" per the
# template comment, so picking the MOST-volatile across supporters
# is correct.
_FRESHNESS_TO_VOLATILITY = {
    "volatile": "fast-moving",
    "active": "evolving",
    "stable": "stable",
    "historical": "stable",
}
_VOLATILITY_ORDER = ["fast-moving", "evolving", "stable"]


def _atom_to_synthesis_id(atom_id: str) -> str:
    """``claim_synthesis_<topic>_<slug>`` → ``syn_<topic>_<slug>``.

    Handles the v2.2 atomic-decomposition pattern (``claim_<topic>_b<N>_a<M>_<descriptor>``)
    by detecting the ``claim_synthesis_`` prefix specifically — synthesis
    atoms don't carry the bullet/atom subscript pattern.
    """
    if not atom_id.startswith("claim_synthesis_"):
        raise ValueError(f"not a synthesis atom_id: {atom_id!r}")
    return "syn_" + atom_id[len("claim_synthesis_"):]


def _pick_dominant(values: list[str]) -> str | None:
    """Return the most common value in ``values``; ties broken by sort order."""
    if not values:
        return None
    counts = Counter(values).most_common()
    top_count = counts[0][1]
    tied = sorted(v for v, c in counts if c == top_count)
    return tied[0]


def _pick_most_volatile(freshness_tiers: list[str]) -> str:
    """Map freshness_tier values to volatility, pick the most-volatile."""
    volatilities = [
        _FRESHNESS_TO_VOLATILITY[ft]
        for ft in freshness_tiers
        if ft in _FRESHNESS_TO_VOLATILITY
    ]
    if not volatilities:
        return "evolving"  # safe default — author can refine
    for candidate in _VOLATILITY_ORDER:
        if candidate in volatilities:
            return candidate
    return "evolving"


def _load_claim_graph(project_dir: Path) -> list[dict[str, Any]]:
    path = project_dir / "claim_graph.jsonl"
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def _build_supporter_index(
    evidence_data: dict[str, Any], bib_data: dict[str, Any]
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """Index evidence by evidence_id + bib entries by ent_<bibkey>."""
    ev_index: dict[str, dict[str, Any]] = {}
    for entry in evidence_data.get("entries") or []:
        if not isinstance(entry, dict):
            continue
        eid = entry.get("evidence_id")
        if isinstance(eid, str):
            ev_index[eid] = entry
    bib_index: dict[str, dict[str, Any]] = {}
    for entry in bib_data.get("entries") or []:
        if not isinstance(entry, dict):
            continue
        bibkey = entry.get("bibkey")
        if isinstance(bibkey, str):
            bib_index[f"ent_{bibkey}"] = entry
    return ev_index, bib_index


def _draft_entry(
    claim_record: dict[str, Any],
    ev_index: dict[str, dict[str, Any]],
    bib_index: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], list[str]]:
    """Build one synthesis_entry block + return any warnings.

    Caller is responsible for skipping atoms with corroboration_count < 3.
    """
    warnings: list[str] = []
    atom_id = claim_record["id"]
    try:
        synthesis_id = _atom_to_synthesis_id(atom_id)
    except ValueError as exc:
        warnings.append(str(exc))
        return {}, warnings

    # source_urls union from supporting evidence
    source_urls: set[str] = set()
    freshness_tiers: list[str] = []
    for ev_id in claim_record.get("evidence_ids") or []:
        ev = ev_index.get(ev_id)
        if not ev:
            continue
        url = ev.get("source_url")
        if isinstance(url, str):
            source_urls.add(url)
        # freshness_tier lives on bib_ledger entries; evidence entries
        # don't carry it directly. Fall through to the bib lookup below.

    # claim_family from dominant entity (ent_<bibkey>)
    claim_families: list[str] = []
    for ent_id in claim_record.get("entity_ids") or []:
        bib_entry = bib_index.get(ent_id)
        if not bib_entry:
            continue
        cf = bib_entry.get("claim_family")
        if isinstance(cf, str):
            claim_families.append(cf)
        ft = bib_entry.get("freshness_tier")
        if isinstance(ft, str):
            freshness_tiers.append(ft)
    dominant_cf = _pick_dominant(claim_families)
    if dominant_cf is None:
        warnings.append(
            f"{atom_id}: no claim_family resolvable from entity_ids; "
            f"defaulting to 'synthesis' — author should set explicitly"
        )
        dominant_cf = "synthesis"

    urls_sorted = sorted(source_urls)
    entry = {
        "synthesis_id": synthesis_id,
        "source_urls": urls_sorted,
        "title": claim_record.get("text", synthesis_id),
        "claim_family": dominant_cf,
        "volatility": _pick_most_volatile(freshness_tiers),
        "tier_summary": tier_summary(urls_sorted),
        "status": "unverified",
        # attribution_map left absent; the skill body's /agent-index Phase 4c
        # instructs the author to add it. The validator allows omission.
    }
    return entry, warnings


def _scaffold(
    project_dir: Path, *, merge: bool, output: Path | None
) -> tuple[list[dict[str, Any]], list[str]]:
    """Compute new entries to add. Returns (entries_to_write, warnings)."""
    warnings: list[str] = []

    cg_records = _load_claim_graph(project_dir)
    if not cg_records:
        raise SystemExit(
            f"{project_dir / 'claim_graph.jsonl'} missing or empty. "
            f"Run build_claim_graph.py first."
        )

    evidence_data, _ = load_yaml_mapping(project_dir / "evidence_ledger.yml")
    if not isinstance(evidence_data, dict):
        raise SystemExit(f"evidence_ledger.yml missing or malformed in {project_dir}")
    bib_data, _ = load_yaml_mapping(project_dir / "bib_ledger.yml")
    if not isinstance(bib_data, dict):
        bib_data = {}

    ev_index, bib_index = _build_supporter_index(evidence_data, bib_data)

    # Existing synthesis_id set (for --merge)
    existing_ids: set[str] = set()
    if merge and output is not None and output.exists():
        existing_data, _ = load_yaml_mapping(output)
        if isinstance(existing_data, dict):
            for entry in existing_data.get("entries") or []:
                if isinstance(entry, dict) and isinstance(entry.get("synthesis_id"), str):
                    existing_ids.add(entry["synthesis_id"])

    drafts: list[dict[str, Any]] = []
    seen_synthesis_ids: set[str] = set(existing_ids)
    for record in cg_records:
        if not isinstance(record, dict) or record.get("record_type") != "claim":
            continue
        atom_id = record.get("id", "")
        if not isinstance(atom_id, str) or not atom_id.startswith("claim_synthesis_"):
            continue
        corr = record.get("corroboration_count", 0)
        if not isinstance(corr, int) or corr < 3:
            warnings.append(
                f"{atom_id}: corroboration_count={corr} < 3; skipping "
                f"(synthesis_entry requires >=3 source_urls)"
            )
            continue
        entry, entry_warnings = _draft_entry(record, ev_index, bib_index)
        warnings.extend(entry_warnings)
        if not entry:
            continue
        sid = entry["synthesis_id"]
        if sid in seen_synthesis_ids:
            if sid in existing_ids:
                # --merge case: silently skip; hand-authored takes precedence
                continue
            warnings.append(
                f"{atom_id}: synthesis_id {sid!r} collides with another draft; "
                f"second occurrence skipped"
            )
            continue
        seen_synthesis_ids.add(sid)
        drafts.append(entry)
    return drafts, warnings


def write(
    drafts: list[dict[str, Any]],
    output: Path,
    *,
    merge: bool,
    project_topic: str,
) -> None:
    """Write entries to output, validating before commit."""
    existing_entries: list[dict[str, Any]] = []
    payload: dict[str, Any]
    if merge and output.exists():
        existing_data, _ = load_yaml_mapping(output)
        if isinstance(existing_data, dict):
            payload = existing_data
            existing_entries = list(payload.get("entries") or [])
        else:
            payload = _empty_envelope(project_topic)
    else:
        payload = _empty_envelope(project_topic)
        if output.exists() and not merge:
            raise SystemExit(
                f"refusing to overwrite existing {output}; "
                f"pass --merge to append new synthesis_ids only"
            )

    payload["entries"] = existing_entries + drafts

    tmp = output.with_suffix(output.suffix + ".tmp")
    tmp.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    errors = synth_validator.validate(tmp)
    if errors:
        tmp.unlink(missing_ok=True)
        raise SystemExit(
            "generated synthesis_entry.yml failed validation:\n" + "\n".join(errors)
        )
    tmp.replace(output)


def _empty_envelope(topic: str) -> dict[str, Any]:
    from datetime import date as _date
    today = _date.today().isoformat()
    return {
        "schema_version": 2,
        "topic": topic,
        "generated_at": today,
        "current_as_of": today,
        "freshness_policy": "strict_live",
        "entries": [],
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Draft synthesis_entry.yml entries from a project's claim_graph "
            "(v2.4+). Used by /agent-index Phase 4c."
        )
    )
    parser.add_argument("project_dir", help="path to project dir containing claim_graph.jsonl + ledgers")
    parser.add_argument(
        "--output",
        default=None,
        help="output path (default: <project_dir>/synthesis_entry.yml)",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="preserve existing entries; append only new synthesis_ids. "
        "Without --merge, refuses to overwrite an existing file.",
    )
    args = parser.parse_args(argv[1:])

    project_dir = Path(args.project_dir).expanduser().resolve()
    if not project_dir.is_dir():
        print(f"error: not a directory: {project_dir}", file=sys.stderr)
        return 2

    output = Path(args.output).expanduser().resolve() if args.output else project_dir / "synthesis_entry.yml"

    evidence_data, _ = load_yaml_mapping(project_dir / "evidence_ledger.yml")
    if not isinstance(evidence_data, dict):
        print(f"error: evidence_ledger.yml missing in {project_dir}", file=sys.stderr)
        return 2
    topic = evidence_data.get("topic")
    if not isinstance(topic, str) or not topic.strip():
        print("error: evidence_ledger.yml missing 'topic'", file=sys.stderr)
        return 2

    drafts, warnings = _scaffold(project_dir, merge=args.merge, output=output)
    for w in warnings:
        print(f"WARN: {w}", file=sys.stderr)
    if not drafts:
        print(
            f"OK: no new synthesis entries to draft "
            f"(0 atoms with corroboration_count>=3 not already in {output.name})",
            file=sys.stderr,
        )
        return 0

    try:
        write(drafts, output, merge=args.merge, project_topic=topic)
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(
        f"OK: drafted {len(drafts)} synthesis entr{'y' if len(drafts) == 1 else 'ies'} → {output}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

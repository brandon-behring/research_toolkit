#!/usr/bin/env python3
"""Compose multiple per-project claim-graphs into one cross-project KG.

Committed, parameterized successor to the unversioned scratch helper
``~/Claude/_merge_projects.py`` (and its within-project sibling
``~/Claude/_merge_tracks.py``). The scratch script hardcoded a wave label and
date (via ``WAVE`` / ``MERGE_DATE`` env vars defaulting to ``wave3`` /
``2026-05-27``) and an inline ``SAME_AS`` alias map, and it was driven by a
fixed list of project dirs baked into the calling shell. This version takes the
output path, the project dirs, and the date as ordinary CLI arguments so any set
of strict-live projects can be folded into one knowledge graph for downstream
import — nothing wave/date/project specific is baked in.

Given N project directories, each containing a ``claim_graph.jsonl``, the
composer unions records the same way the scratch helper did:

  - Resolvable records (``entity``, ``source``, ``cache_blob``) legitimately
    recur across projects and are DEDUPED. The toolkit derives their ids
    deterministically from the underlying identity (``src_<url-slug>`` from a
    source's ``primary_url``, ``graph_cache_<cache_id>`` from a blob's sha256),
    so a source cited by several projects carries the SAME ``id`` everywhere and
    id-recurrence IS the primary_url+sha256 dedup. As an explicit safety net the
    composer also treats a shared ``source_url`` (or ``primary_url``) as a dedup
    key, folding same-source-different-id captures together and remapping the
    losing id via an alias map. The union records each contributing project in
    ``source_projects``.
  - Claim / evidence / other records are disjoint by per-dossier id prefix, so a
    recurring claim/evidence id is an ID-collision bug and is reported as an
    error (mirroring the scratch helper's assertion). Their ``entity_ids`` /
    subject / object references are remapped through the alias map so
    cross-project references resolve to the surviving id.

Output is a single ``claim_graph.jsonl`` (resolvable records first, then the
rest) that ``validators/claim_graph.py`` accepts. Each emitted record is stamped
with ``composed_on`` for provenance.

Usage:
    python scripts/compose_cross_project_kg.py <output.jsonl> <project_dir> [<project_dir> ...]
    python scripts/compose_cross_project_kg.py out.jsonl projA projB --date 2026-05-31

Exit codes: 0 success, 1 data error (collision / malformed input), 2 usage error.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from datetime import date
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators.jsonl_common import load_jsonl

# Record types that legitimately recur across projects (deduped by identity).
RESOLVABLE_TYPES = {"entity", "source", "cache_blob"}
# Fields on claim/other records whose values are entity/source ids to remap.
REFERENCE_LIST_FIELDS = ("entity_ids", "claim_ids", "evidence_ids", "cache_ids")
REFERENCE_SCALAR_FIELDS = ("subject", "subject_id", "object", "object_id")


def _project_slug(project: Path) -> str:
    """Short provenance label for a project dir (drops a ``research_`` prefix)."""
    name = project.name
    for prefix in ("research_agent_", "research_"):
        if name.startswith(prefix):
            return name[len(prefix) :]
    return name


def _add_project(record: dict[str, Any], slug: str) -> None:
    """Record ``slug`` in the record's ``source_projects`` list (no dupes)."""
    projects = record.setdefault("source_projects", [])
    if slug not in projects:
        projects.append(slug)


def _source_url(record: dict[str, Any]) -> str | None:
    """Return a source record's dedup URL (``source_url`` or ``primary_url``)."""
    url = record.get("source_url") or record.get("primary_url")
    if isinstance(url, str) and url.strip():
        return url.strip().lower()
    return None


def compose(
    project_dirs: list[Path], compose_date: str
) -> tuple[list[dict[str, Any]], list[str]]:
    """Merge each project's claim_graph.jsonl into one ordered record list.

    Returns ``(records, errors)``. ``records`` is the deduped resolvable records
    (entities/sources/cache_blobs) followed by the disjoint claim/other records,
    with all id references remapped through the alias map. ``errors`` collects
    read problems (missing file, malformed JSONL) and cross-project claim-id
    collisions; an empty list means a clean compose.
    """
    resolvable: OrderedDict[str, dict[str, Any]] = OrderedDict()  # id -> record
    url_to_id: dict[str, str] = {}  # source_url -> surviving id
    others: list[dict[str, Any]] = []
    alias_map: dict[str, str] = {}  # losing id -> surviving id
    claim_owner: dict[str, str] = {}  # claim/other id -> project (collision guard)
    errors: list[str] = []

    for project in project_dirs:
        cg = project / "claim_graph.jsonl"
        if not cg.exists():
            errors.append(f"{project}: no claim_graph.jsonl")
            continue
        records, read_errors = load_jsonl(cg)
        for err in read_errors:
            errors.append(f"{cg}: {err}")
        slug = _project_slug(project)
        for rec in records:
            rec_id = rec.get("id")
            rec_type = rec.get("record_type")

            if rec_type in RESOLVABLE_TYPES:
                # Dedup key: a shared source_url collapses same-source captures
                # even if their ids differ; otherwise the (deterministic) id is
                # the key.
                url = _source_url(rec) if rec_type == "source" else None
                survivor_id = None
                if url is not None and url in url_to_id:
                    survivor_id = url_to_id[url]
                elif isinstance(rec_id, str) and rec_id in resolvable:
                    survivor_id = rec_id

                if survivor_id is not None:
                    survivor = resolvable[survivor_id]
                    _add_project(survivor, slug)
                    if isinstance(rec_id, str) and rec_id != survivor_id:
                        alias_map[rec_id] = survivor_id
                    continue

                _add_project(rec, slug)
                if isinstance(rec_id, str):
                    resolvable[rec_id] = rec
                    if url is not None:
                        url_to_id[url] = rec_id
                else:
                    # No usable id — keep it so the validator can flag it.
                    others.append(rec)
            else:
                # claim / evidence / unknown: must be globally unique.
                if isinstance(rec_id, str):
                    if rec_id in claim_owner:
                        errors.append(
                            f"{cg}: cross-project id collision on "
                            f"{rec_type!r} id={rec_id!r} "
                            f"(also in {claim_owner[rec_id]})"
                        )
                        continue
                    claim_owner[rec_id] = slug
                _add_project(rec, slug)
                others.append(rec)

    # Remap id references on the disjoint records through the alias map.
    for rec in others:
        for field in REFERENCE_SCALAR_FIELDS:
            value = rec.get(field)
            if isinstance(value, str) and value in alias_map:
                rec[field] = alias_map[value]
        for field in REFERENCE_LIST_FIELDS:
            value = rec.get(field)
            if isinstance(value, list):
                rec[field] = [alias_map.get(v, v) for v in value]

    ordered = list(resolvable.values()) + others
    for rec in ordered:
        rec.setdefault("composed_on", compose_date)
    return ordered, errors


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="compose_cross_project_kg.py",
        description="Compose multiple per-project claim-graphs into one KG.",
    )
    parser.add_argument("output", type=Path, help="output claim_graph.jsonl path")
    parser.add_argument(
        "project_dirs",
        type=Path,
        nargs="+",
        help="one or more project dirs (each with a claim_graph.jsonl)",
    )
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="compose date stamped on records (default: today, ISO 8601)",
    )
    args = parser.parse_args(argv)

    project_dirs = [p.expanduser().resolve() for p in args.project_dirs]
    for project in project_dirs:
        if not project.is_dir():
            print(f"error: not a directory: {project}", file=sys.stderr)
            return 2

    records, errors = compose(project_dirs, args.date)
    for err in errors:
        print(f"error: {err}", file=sys.stderr)
    if errors:
        print(
            f"error: compose aborted with {len(errors)} problem(s)",
            file=sys.stderr,
        )
        return 1

    out_path = args.output.expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for rec in records:
            handle.write(json.dumps(rec, ensure_ascii=False) + "\n")

    counts: dict[str, int] = {}
    for rec in records:
        counts[rec.get("record_type") or "?"] = counts.get(rec.get("record_type") or "?", 0) + 1
    summary = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
    print(f"wrote {len(records)} records ({summary}) -> {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

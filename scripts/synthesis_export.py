#!/usr/bin/env python3
"""Export strict-live project records as the in-dossier synthesis-kb envelope.

Writes <project_dir>/synthesis_export.jsonl (RS1 contract, 2026-06-12): the envelope
lives only in its dossier folder — there is no inbox. Consumed by
synthesis-kb/scripts/ingest_dossiers.py. Schema unchanged (export_schema_version 2;
validated by validators/research_kb_export.py, which keeps its historical name).
"""
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators import cache_manifest, research_kb_export


def _read_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _prepare_metadata_records(project_dir: Path) -> list[dict]:
    """Load and rights-gate claim-graph metadata for export.

    Restricted, private-use, and unknown cache entries remain eligible because
    this envelope contains no cached bodies.  Their explicit policy travels on
    the corresponding ``cache_blob`` record so downstream consumers cannot
    mistake identifier reachability for redistribution permission.
    """
    manifest_path = project_dir / "cache_manifest.yml"
    if not manifest_path.is_file():
        raise SystemExit(f"cache_manifest.yml missing in {project_dir}")
    policies, policy_errors = cache_manifest.load_access_policies(manifest_path)
    if policy_errors:
        raise SystemExit(
            "cache_manifest.yml access policy failed validation:\n"
            + "\n".join(policy_errors)
        )

    records = _read_jsonl(project_dir / "claim_graph.jsonl")
    if not records:
        raise SystemExit(f"no claim_graph.jsonl records found in {project_dir}")

    referenced: set[str] = set()
    cache_blob_ids: set[str] = set()
    prepared: list[dict] = []
    for index, original in enumerate(records):
        record = dict(original)
        record_type = record.get("record_type", "claim")
        record_cache_ids = research_kb_export.referenced_cache_ids(record)
        referenced.update(record_cache_ids)

        metadata_errors = research_kb_export.validate_metadata_only_payload(
            record,
            loc=f"claim_graph.jsonl record {index + 1}",
            allow_rights_policy=False,
        )
        if metadata_errors:
            raise SystemExit(
                "claim_graph.jsonl metadata-only export policy failed:\n"
                + "\n".join(metadata_errors)
            )

        if record_type == "cache_blob":
            cache_id = record.get("cache_id")
            if not isinstance(cache_id, str) or cache_id not in policies:
                raise SystemExit(
                    f"claim_graph.jsonl cache_blob record {index + 1} references "
                    f"unknown cache_id {cache_id!r}"
                )
            cache_blob_ids.add(cache_id)
            record["rights_policy"] = policies[cache_id]
        prepared.append(record)

    unknown = sorted(referenced - set(policies))
    if unknown:
        raise SystemExit(
            "claim_graph.jsonl references cache_ids absent from cache_manifest.yml: "
            f"{unknown}"
        )
    missing_policy_records = sorted(referenced - cache_blob_ids)
    if missing_policy_records:
        raise SystemExit(
            "claim_graph.jsonl cache references lack cache_blob policy records: "
            f"{missing_policy_records}"
        )
    return prepared


def export_project(project_dir: Path, *, output: Path, exported_at: str) -> None:
    source_project = project_dir.name
    records: list[dict] = []

    for record in _prepare_metadata_records(project_dir):
        record_type = record.get("record_type", "claim")
        record_id = record.get("id", f"{record_type}_{len(records)}")
        records.append(
            {
                "export_schema_version": 2,
                "record_type": record_type,
                "id": f"export_{record_id}",
                "source_project": source_project,
                "exported_at": exported_at,
                "payload": record,
            }
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "\n".join(json.dumps(r, sort_keys=True, separators=(",", ":")) for r in records) + "\n",
        encoding="utf-8",
    )

    errors = research_kb_export.validate(output)
    if errors:
        output.unlink(missing_ok=True)
        raise SystemExit("generated export failed validation:\n" + "\n".join(errors))


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("--output")
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args(argv[1:])

    project = Path(args.project_dir).expanduser().resolve()
    if args.output:
        output = Path(args.output).expanduser().resolve()
    else:
        output = project / "synthesis_export.jsonl"
    export_project(project, output=output, exported_at=args.date)
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

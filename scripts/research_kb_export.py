#!/usr/bin/env python3
"""Export strict-live v2 project records for research-kb ingestion."""
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators import research_kb_export


def _slug(path: Path) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", path.name.lower()).strip("_") or "project"


def _read_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def export_project(project_dir: Path, *, output: Path, exported_at: str) -> None:
    source_project = project_dir.name
    records: list[dict] = []

    for record in _read_jsonl(project_dir / "claim_graph.jsonl"):
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

    if not records:
        raise SystemExit(f"no claim_graph.jsonl records found in {project_dir}")

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
        output = (
            Path("~/Claude/research-kb/inbox/research_toolkit").expanduser()
            / f"{_slug(project)}.jsonl"
        )
    export_project(project, output=output, exported_at=args.date)
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

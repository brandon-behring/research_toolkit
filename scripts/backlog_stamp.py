#!/usr/bin/env python3
"""Stamp a topic_backlog.yml entry's lifecycle fields after research completes.

/topic-discovery produces an append-only backlog; once a topic has been run
through the research pipeline, this helper flips its `status` (default
`researched`) and sets `dossier_path` + `researched_at` so the next
/topic-discovery run dedups it out (see references/topic_discovery_protocol.md
Step 3).

The stamped data is validated with validators/topic_backlog.py and written via
an atomic temp-file replace — a result that would fail validation is never left
on disk. Like scripts/migrate_manifest_paths.py, this does not preserve the
backlog's top comment block (yaml.safe_dump round-trips data, not comments).

Usage:
    python scripts/backlog_stamp.py <backlog.yml> <topic_id> \\
        --status researched --dossier ~/Claude/research_<slug>/agent_index/
    python scripts/backlog_stamp.py <backlog.yml> <topic_id> --status dropped

Exit codes: 0 OK; 1 schema/data error (result would be invalid); 2 usage error
(bad args, file missing, malformed backlog, topic_id not found).
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

import yaml

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators import topic_backlog

ALLOWED_STATUS = ("proposed", "planned", "researched", "dropped")


def stamp(
    backlog_path: Path,
    topic_id: str,
    *,
    status: str = "researched",
    dossier: str | None = None,
    today: str | None = None,
) -> int:
    """Set lifecycle fields on one entry and rewrite the backlog. Return exit code."""
    try:
        data = yaml.safe_load(backlog_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        print(f"error: cannot parse {backlog_path}: {exc}", file=sys.stderr)
        return 2
    if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
        print(
            f"error: {backlog_path} is not a topic_backlog (no 'entries' list)",
            file=sys.stderr,
        )
        return 2

    matches = [
        e
        for e in data["entries"]
        if isinstance(e, dict) and e.get("topic_id") == topic_id
    ]
    if not matches:
        print(f"error: topic_id {topic_id!r} not found in {backlog_path}", file=sys.stderr)
        return 2

    # validate() rejects duplicate topic_id, so there is exactly one match.
    entry = matches[0]
    entry["status"] = status
    if dossier is not None:
        entry["dossier_path"] = dossier
    if status == "researched":
        entry["researched_at"] = today or date.today().isoformat()

    new_text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    tmp = backlog_path.with_suffix(backlog_path.suffix + ".tmp")
    tmp.write_text(new_text, encoding="utf-8")
    errors = topic_backlog.validate(tmp)
    if errors:
        tmp.unlink(missing_ok=True)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        print("error: stamped backlog would be invalid; not written", file=sys.stderr)
        return 1
    os.replace(tmp, backlog_path)
    print(f"OK: stamped {topic_id!r} status={status} in {backlog_path}", file=sys.stderr)
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="backlog-stamp",
        description=(
            "Stamp a topic_backlog.yml entry's lifecycle fields (status, "
            "dossier_path, researched_at) after a topic has been researched."
        ),
    )
    parser.add_argument("backlog", help="path to topic_backlog.yml")
    parser.add_argument("topic_id", help="topic_id of the entry to stamp")
    parser.add_argument(
        "--status",
        default="researched",
        choices=ALLOWED_STATUS,
        help="new status (default: researched)",
    )
    parser.add_argument(
        "--dossier", default=None, help="dossier_path to record (e.g. the agent_index dir)"
    )
    parser.add_argument(
        "--today",
        default=None,
        help="YYYY-MM-DD for researched_at (default: today)",
    )
    args = parser.parse_args(argv[1:])

    target = Path(args.backlog).expanduser().resolve()
    if not target.exists():
        print(f"error: path does not exist: {target}", file=sys.stderr)
        return 2
    return stamp(
        target,
        args.topic_id,
        status=args.status,
        dossier=args.dossier,
        today=args.today,
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv))

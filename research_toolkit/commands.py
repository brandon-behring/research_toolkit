"""Deterministic workflow commands used by the Claude plugin and CI."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from research_toolkit.canonical import (
    due_watch_records,
    find_dossiers,
    impact_graph,
    initialize_dossier,
    validate_dossier,
)


def _print_errors(errors: list[str], *, json_output: bool) -> None:
    if json_output:
        print(json.dumps({"ok": not errors, "errors": errors}, sort_keys=True))
    else:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)


def audit_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="research-toolkit audit")
    parser.add_argument("dossier", type=Path)
    parser.add_argument("--release", action="store_true", help="require release artifacts")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args(argv)
    errors = validate_dossier(args.dossier, require_release=args.release)
    _print_errors(errors, json_output=args.json_output)
    if not errors and not args.json_output:
        print(f"OK: canonical dossier validates: {args.dossier}")
    return 1 if errors else 0


def _run_main(argv: list[str], *, kind: str) -> int:
    prog = "research-toolkit dataset run" if kind == "dataset" else "research-toolkit research run"
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Initialize or preflight the deterministic boundary for an agent-authored run.",
    )
    parser.add_argument("dossier", type=Path)
    parser.add_argument("--initialize", action="store_true")
    parser.add_argument("--dossier-id")
    parser.add_argument("--topic")
    parser.add_argument("--run-id")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args(argv)
    if args.initialize:
        missing = [name for name in ("dossier_id", "topic", "run_id") if not getattr(args, name)]
        if missing:
            parser.error("--initialize requires --dossier-id, --topic, and --run-id")
        try:
            run_date = date.fromisoformat(args.date)
            initialize_dossier(
                args.dossier,
                dossier_id=args.dossier_id,
                topic=args.topic,
                run_id=args.run_id,
                run_date=run_date,
                kind=kind,
            )
        except (FileExistsError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    errors = validate_dossier(args.dossier)
    _print_errors(errors, json_output=args.json_output)
    if not errors and not args.json_output:
        print(f"READY: {kind} run boundary validates: {args.dossier}")
        print("Agent-authored discovery and semantic review remain required before release.")
    return 1 if errors else 0


def research_run_main(argv: list[str]) -> int:
    return _run_main(argv, kind="research")


def dataset_run_main(argv: list[str]) -> int:
    return _run_main(argv, kind="dataset")


def freshness_poll_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="research-toolkit freshness poll",
        description="Read-only selection of source watch records due for review.",
    )
    parser.add_argument("dossier", type=Path)
    parser.add_argument("--today", default=date.today().isoformat())
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args(argv)
    try:
        today = date.fromisoformat(args.today)
    except ValueError:
        parser.error("--today must be YYYY-MM-DD")
    due, errors = due_watch_records(args.dossier, today)
    if errors:
        _print_errors(errors, json_output=args.json_output)
        return 1
    payload = {"ok": True, "today": today.isoformat(), "due_count": len(due), "records": due}
    if args.json_output:
        print(json.dumps(payload, sort_keys=True))
    else:
        print(f"due sources: {len(due)}")
        for item in due:
            print(f"- {item['source_id']} ({item['next_check_at']})")
    return 0


def impact_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="research-toolkit impact")
    parser.add_argument("dossier", type=Path)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--source-id")
    choice.add_argument("--claim-id")
    args = parser.parse_args(argv)
    errors = validate_dossier(args.dossier)
    if errors:
        _print_errors(errors, json_output=True)
        return 1
    payload = impact_graph(args.dossier, source_id=args.source_id, claim_id=args.claim_id)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def release_check_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="research-toolkit release check")
    parser.add_argument("dossier", type=Path)
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args(argv)
    errors = validate_dossier(args.dossier, require_release=True)
    _print_errors(errors, json_output=args.json_output)
    if not errors and not args.json_output:
        print(f"OK: release is internally consistent: {args.dossier}")
    return 1 if errors else 0


def corpus_check_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="research-toolkit corpus check")
    parser.add_argument("root", type=Path)
    parser.add_argument("--release", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args(argv)
    dossiers = find_dossiers(args.root)
    results = []
    failed = 0
    for dossier in dossiers:
        errors = validate_dossier(dossier, require_release=args.release)
        failed += bool(errors)
        results.append({"dossier": str(dossier), "ok": not errors, "errors": errors})
    if args.json_output:
        print(json.dumps({"count": len(dossiers), "failed": failed, "results": results}, sort_keys=True))
    else:
        for result in results:
            print(f"{'OK' if result['ok'] else 'FAIL'}: {result['dossier']}")
            for error in result["errors"]:
                print(f"  {error}")
        print(f"checked {len(dossiers)} dossiers; {failed} failed")
    return 1 if failed else 0


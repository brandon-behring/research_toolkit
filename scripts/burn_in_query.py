"""Query the structured BURN_IN log (`burn_in.yml`).

Filter friction-tracking entries by status, severity, phase, or stage. Useful
for "what's left unresolved at high severity?" or "which v1.x version fixed
this kind of issue?". The narrative version lives in `BURN_IN_NOTES.md`; this
script answers structured questions without grep-and-pray.

Examples:
    python scripts/burn_in_query.py --status surfaced
    python scripts/burn_in_query.py --severity high --status applied
    python scripts/burn_in_query.py --phase phase-5c
    python scripts/burn_in_query.py --stage research-gather
    python scripts/burn_in_query.py --fix-version v1.1
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
BURN_IN_PATH = REPO_ROOT / "burn_in.yml"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", choices=("surfaced", "applied", "deferred", "wontfix"))
    parser.add_argument("--severity", choices=("high", "medium", "low"))
    parser.add_argument("--phase")
    parser.add_argument("--stage")
    parser.add_argument("--fix-version")
    parser.add_argument(
        "--format",
        choices=("table", "yaml", "ids"),
        default="table",
        help="output format (default: table)",
    )
    args = parser.parse_args()

    if not BURN_IN_PATH.exists():
        print(f"FATAL: {BURN_IN_PATH} not found", file=sys.stderr)
        return 2
    data = yaml.safe_load(BURN_IN_PATH.read_text(encoding="utf-8"))
    entries = data.get("entries") or []

    def matches(entry: dict) -> bool:
        if args.status and entry.get("status") != args.status:
            return False
        if args.severity and entry.get("severity") != args.severity:
            return False
        if args.phase and entry.get("phase") != args.phase:
            return False
        if args.stage and entry.get("stage") != args.stage:
            return False
        if args.fix_version and entry.get("fix_version") != args.fix_version:
            return False
        return True

    matched = [e for e in entries if matches(e)]

    if not matched:
        print("(no matches)", file=sys.stderr)
        return 0

    if args.format == "ids":
        for e in matched:
            print(e["id"])
    elif args.format == "yaml":
        print(yaml.safe_dump({"entries": matched}, sort_keys=False, allow_unicode=True))
    else:  # table
        print(f"{'ID':<10} {'SEV':<6} {'STATUS':<10} {'FIX':<10} FINDING")
        print(f"{'-' * 10} {'-' * 6} {'-' * 10} {'-' * 10} {'-' * 60}")
        for e in matched:
            id_ = e.get("id", "?")[:10]
            sev = e.get("severity", "?")[:6]
            status = e.get("status", "?")[:10]
            fix = (e.get("fix_version") or "-")[:10]
            finding = e.get("finding", "")
            if len(finding) > 80:
                finding = finding[:77] + "..."
            print(f"{id_:<10} {sev:<6} {status:<10} {fix:<10} {finding}")
        print(f"\n{len(matched)} entries", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())

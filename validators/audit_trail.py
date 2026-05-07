"""Validate audit-trail notes inside an agent-index README.

The audit trail is a series of inline 'Independent audit, round N (date): ...' notes
under a Verification & limits or Independent audit subsection in the indexed folder's
README.md. Multiple rounds are allowed; each must:
- Begin with the literal '**Independent audit, round N' (N >= 1)
- Include a YYYY-MM-DD date in parentheses on the same line
- Be a non-empty paragraph

This validator accepts a README.md and returns errors only if at least one audit-trail
note is malformed. Zero audit notes is allowed (a fresh agent-index hasn't been audited
yet) — the validator only fails on malformed notes, not absence.

Importable: agent_index.py imports validate_audit_trail to fold this check into its
own pass.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from validators._common import cli_main

AUDIT_NOTE_RE = re.compile(
    r"\*\*Independent audit, round (?P<round>\d+)\s*\((?P<date>[^)]*)\):\*\*",
)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_audit_trail(text: str) -> list[str]:
    errors: list[str] = []
    matches = list(AUDIT_NOTE_RE.finditer(text))
    seen_rounds: set[int] = set()
    for m in matches:
        round_num = int(m.group("round"))
        date = m.group("date").strip()
        if round_num < 1:
            errors.append(f"audit-trail: round number must be >= 1, got {round_num}")
        if round_num in seen_rounds:
            errors.append(f"audit-trail: duplicate round number {round_num}")
        seen_rounds.add(round_num)
        if not DATE_RE.match(date):
            errors.append(
                f"audit-trail: round {round_num} date {date!r} not in YYYY-MM-DD form"
            )
    return errors


def validate(path: Path) -> list[str]:
    if path.is_dir():
        readme = path / "README.md"
        if not readme.exists():
            return [f"no README.md in {path}"]
        text = readme.read_text(encoding="utf-8")
    else:
        text = path.read_text(encoding="utf-8")
    return validate_audit_trail(text)


if __name__ == "__main__":
    sys.exit(cli_main(sys.argv, validate))

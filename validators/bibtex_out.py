"""Validate an emitted BibTeX ``.bib`` (the output of ``scripts/emit_bibtex.py``).

Schema-only, per the toolkit contract: braces balance, every ``@type{key,``
parses with balanced braces, keys are unique, ``author``/``title`` are present as
top-level fields, and NO field value contains an escaped brace ``\\{`` / ``\\}``
(which would destroy BibTeX brace-protection -- the bug this feature exists to
avoid). Runnable as ``python -m validators.bibtex_out <path>``; exits 0 clean,
1 on violation, 2 on usage/missing path.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators._common import cli_main

_AT_ENTRY_RE = re.compile(r"@(\w+)\s*\{")
# A required field must appear at the START of a line (col 0 after indent), so a
# field NAME occurring inside another field's value ("note = {words author =}")
# is not mistaken for the field itself.
_NON_ENTRY_TYPES = {"string", "comment", "preamble"}


def parse_entries(text: str) -> list[tuple[str, str, str]]:
    """Return ``(type, key, fields)`` for each ``@type{key, ...}`` with BALANCED
    braces. Skips ``@string``/``@comment``/``@preamble`` (not reference entries).
    An entry whose braces never close is dropped (``validate_text`` catches the
    imbalance separately)."""
    out: list[tuple[str, str, str]] = []
    i, n = 0, len(text)
    while i < n:
        at = text.find("@", i)
        if at < 0:
            break
        m = _AT_ENTRY_RE.match(text, at)
        if not m:
            i = at + 1
            continue
        typ = m.group(1).lower()
        depth, j, start = 1, m.end(), m.end()
        while j < n and depth:
            depth += (text[j] == "{") - (text[j] == "}")
            j += 1
        if depth != 0:  # unterminated -- stop; imbalance reported by validate_text
            break
        body = text[start:j - 1]
        i = j
        if typ in _NON_ENTRY_TYPES:
            continue
        key, _, fields = body.partition(",")
        out.append((typ, key.strip(), fields))
    return out


def validate_text(text: str) -> list[str]:
    """Return a list of schema violations for the BibTeX ``text`` (empty = valid)."""
    errors: list[str] = []
    if text.count("{") != text.count("}"):
        errors.append("unbalanced braces in the .bib (a field value has a stray { or })")

    entries = parse_entries(text)
    if not entries:
        errors.append("no BibTeX entries found (expected at least one @type{key, ...})")
        return errors

    seen: set[str] = set()
    for _type, key, _fields in entries:
        if not key:
            errors.append("an entry has an empty citation key")
        elif key in seen:
            errors.append(f"duplicate entry key: {key}")
        seen.add(key)

    for _type, key, fields in entries:
        if r"\{" in fields or r"\}" in fields:
            errors.append(f"{key}: escaped brace (\\{{ or \\}}) corrupts brace-protection")
        for required in ("author", "title"):
            if not re.search(rf"(?mi)^\s*{required}\s*=", fields):
                errors.append(f"{key}: missing required field '{required}'")
    return errors


def validate(path: Path) -> list[str]:
    """Validate the ``.bib`` file at ``path``."""
    if path.is_dir():
        return [f"expected a .bib file, got directory: {path}"]
    return validate_text(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    sys.exit(cli_main(sys.argv, validate))

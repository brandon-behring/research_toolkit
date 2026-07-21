"""Validate an emitted BibTeX ``.bib`` (the output of ``scripts/emit_bibtex.py``).

Schema-only, per the toolkit contract: every ``@type{key,`` parses, keys are
unique, ``author``/``title`` are present, and NO field value contains an escaped
brace ``\\{`` / ``\\}`` (which would destroy BibTeX brace-protection -- the bug
this feature exists to avoid). Runnable as ``python -m validators.bibtex_out
<path>``; exits 0 clean, 1 on violation, 2 on usage/missing path.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators._common import cli_main

_ENTRY_RE = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,(.*?)\n\}", re.S)
_FIELD_RE = re.compile(r"\b(\w+)\s*=", re.I)


def validate_text(text: str) -> list[str]:
    """Return a list of schema violations for the BibTeX ``text`` (empty = valid)."""
    errors: list[str] = []
    entries = _ENTRY_RE.findall(text)
    if not entries:
        errors.append("no BibTeX entries found (expected at least one @type{key, ...})")
        return errors

    keys = [key for _type, key, _body in entries]
    seen: set[str] = set()
    for key in keys:
        if key in seen:
            errors.append(f"duplicate entry key: {key}")
        seen.add(key)

    for _type, key, body in entries:
        if r"\{" in body or r"\}" in body:
            errors.append(f"{key}: escaped brace (\\{{ or \\}}) corrupts brace-protection")
        fields = {m.group(1).lower() for m in _FIELD_RE.finditer(body)}
        for required in ("author", "title"):
            if required not in fields:
                errors.append(f"{key}: missing required field '{required}'")
    return errors


def validate(path: Path) -> list[str]:
    """Validate the ``.bib`` file at ``path``."""
    if path.is_dir():
        return [f"expected a .bib file, got directory: {path}"]
    return validate_text(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    sys.exit(cli_main(sys.argv, validate))

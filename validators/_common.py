"""Shared helpers for validator scripts."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Callable


def _norm(s: str) -> str:
    """Normalize a string for fuzzy taxonomy/heading matching.

    Strips backticks, quotes, and `--` punctuation; collapses whitespace; lowercases.
    Used by claim_family and similar taxonomy-string fuzzy matchers.
    """
    s = s.replace("`", "").replace('"', "").replace("'", "").replace("--", "")
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def matches_canonical_fuzzy(
    value: str, canonical_set: set[str], min_len: int = 10
) -> bool:
    """Check whether ``value`` matches any canonical phrasing (fuzzy substring).

    Returns True if:
    - The normalized ``value`` exactly equals some normalized entry in
      ``canonical_set``, OR
    - The normalized ``value`` is a substring of some canonical entry (or vice
      versa), AND the normalized length is ≥ ``min_len`` (avoids trivial
      1-2-word collisions).

    Designed for taxonomy-string membership checks (e.g., `claim_family` against
    research_plan.md's enumerated families) where agents naturally write
    near-canonical forms ("Session state" vs "Session state (--resume,
    fork_session, scratchpads)"). Strict equality alone produces ~20-30% false
    positives on real research-gather output. See BURN_IN_NOTES.md external
    dogfood item #5.
    """
    v = _norm(value)
    norm_set = {_norm(c) for c in canonical_set}
    if v in norm_set:
        return True
    if len(v) < min_len:
        return False
    return any(v in c or c in v for c in norm_set)


def cli_main(argv: list[str], validate_fn: Callable[[Path], list[str]]) -> int:
    """Standard CLI entrypoint shared across validators.

    Usage: python -m validators.<name> <path>
    Exits 0 if valid, 1 on schema violation, 2 on usage error.
    """
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} <path>", file=sys.stderr)
        return 2
    path = Path(argv[1]).expanduser().resolve()
    if not path.exists():
        print(f"error: path does not exist: {path}", file=sys.stderr)
        return 2
    errors = validate_fn(path)
    if errors:
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        print(
            f"VALIDATION FAILED: {len(errors)} error(s) in {path}",
            file=sys.stderr,
        )
        return 1
    print(f"OK: {path}", file=sys.stderr)
    return 0


URL_RE = r"https?://[^\s\)\]]+"

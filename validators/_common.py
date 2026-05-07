"""Shared helpers for validator scripts."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable


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

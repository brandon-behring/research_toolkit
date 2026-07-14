#!/usr/bin/env python3
"""Retired legacy recovery entry point.

This module intentionally contains no retrieval, cache, or dossier-mutation
implementation. Historical Wayback retry results remain audit artifacts only;
new retrieval must use the bundled ``research-toolkit cache-source`` boundary.
"""
from __future__ import annotations

import sys


RETIRED_MESSAGE = (
    "error: retry_escalations.py is retired and cannot fetch or mutate dossiers; "
    "use the bundled research-toolkit cache-source command for a reviewed URL"
)


def main(argv: list[str] | None = None) -> int:
    """Fail closed for every invocation, including historical arguments."""
    del argv
    print(RETIRED_MESSAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

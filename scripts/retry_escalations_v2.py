#!/usr/bin/env python3
"""Retired multi-strategy legacy recovery entry point.

The former implementation could fetch external resources and rewrite legacy
manifests. It is deliberately replaced by a fail-closed compatibility stub so
old automation cannot revive an unreviewed network or mutation path.
"""
from __future__ import annotations

import sys


RETIRED_MESSAGE = (
    "error: retry_escalations_v2.py is retired and cannot fetch or mutate "
    "dossiers; use the bundled research-toolkit cache-source command for a "
    "reviewed URL"
)


def main(argv: list[str] | None = None) -> int:
    """Fail closed for every invocation, including historical arguments."""
    del argv
    print(RETIRED_MESSAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

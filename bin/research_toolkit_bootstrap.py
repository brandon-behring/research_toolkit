"""Start the bundled research-toolkit CLI from an isolated interpreter."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    """Load the trusted plugin package without admitting the caller's cwd."""
    if not sys.flags.isolated:
        print(
            "error: research-toolkit bootstrap requires Python isolated mode (-I)",
            file=sys.stderr,
        )
        return 2

    plugin_root = str(Path(__file__).resolve().parent.parent)
    sys.path.insert(0, plugin_root)

    from scripts.cli import main as cli_main

    return cli_main()


if __name__ == "__main__":
    sys.exit(main())

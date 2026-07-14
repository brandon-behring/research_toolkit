"""Run the research-toolkit console entry point as a module."""
from __future__ import annotations

import sys

from scripts.cli import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))


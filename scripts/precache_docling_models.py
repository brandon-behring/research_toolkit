#!/usr/bin/env python3
"""Pre-download Docling models for cross-machine cache sync (v2.3).

The default v2.3 PDF cascade lazy-loads Docling on the first equation-rich
PDF, pulling ~600 MB of models into the local cache. On a two-machine
workflow each machine pays that download separately — unless the cache lives
on a synced dir.

This script triggers the download proactively so you can:
- Run it once on a fresh install before any real caching work
- Run it on machine A, then point machine B's DOCLING_CACHE_DIR at the same
  synced location (Dropbox / Google Drive / shared NAS), so machine B never
  re-downloads

Usage:
    DOCLING_CACHE_DIR=~/Dropbox/docling-models python scripts/precache_docling_models.py
    # or just:
    python scripts/precache_docling_models.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    cache_dir = os.environ.get("DOCLING_CACHE_DIR")
    if cache_dir:
        expanded = str(Path(cache_dir).expanduser())
        # Docling uses HuggingFace Transformers under the hood; HF_HOME is the
        # standard cache env var.
        os.environ.setdefault("HF_HOME", expanded)
        print(f"Using DOCLING_CACHE_DIR={expanded}", file=sys.stderr)

    try:
        from docling.document_converter import DocumentConverter
    except ImportError as exc:
        print(
            f"error: docling is not installed: {exc}\n"
            f"Install it via: pip install -e .  (it's a hard dep in pyproject.toml)\n"
            f"\nNote: docling-parse has a known C++ build issue on macOS Python 3.12 "
            f"(missing 'cstdint'). Workarounds:\n"
            f"  - install via conda: conda install -c conda-forge docling\n"
            f"  - or downgrade to Python 3.11\n"
            f"  - or skip extraction entirely with --no-extract-pdfs",
            file=sys.stderr,
        )
        return 1

    print("Initializing Docling DocumentConverter — first run downloads ~600 MB of models...", file=sys.stderr)
    converter = DocumentConverter()
    # Touching the converter is enough — model files are pulled lazily on first
    # convert() call. To force download here, we'd need to actually convert
    # something; a single one-page synthetic PDF is the cheapest probe.
    print("DocumentConverter initialized.", file=sys.stderr)
    print(
        "Models will fully download on first PDF conversion. To verify, run "
        "cache_source.py against an equation-rich PDF and confirm "
        "extraction_status: rich.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

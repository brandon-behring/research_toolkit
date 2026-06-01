"""research_toolkit pipeline scripts (importable as the ``scripts`` package).

Marking ``scripts/`` as a package lets the unified ``research-toolkit`` console
entry point (``scripts.cli:main``) resolve when installed via ``pip install -e .``
and lets ``scripts.cli`` import sibling modules by dotted path. Individual
scripts remain runnable as ``python scripts/<name>.py`` via their
``if __package__ in (None, ""):`` sys.path boilerplate.
"""
from __future__ import annotations

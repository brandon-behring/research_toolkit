"""Unified ``research-toolkit`` command — one entry point for the pipeline.

Dispatches to the existing ``scripts/*.py`` (and ``validators/freshness.py``)
``main`` functions without reimplementing their logic. Each subcommand imports
its target module lazily and forwards the remaining argv, so unrelated heavy
dependencies (e.g. docling, pulled in by ``cache-source``) are not imported for
other verbs.

Usage::

    research-toolkit --help              # list subcommands
    research-toolkit <subcommand> --help # delegate to the script's own parser
    research-toolkit assemble sources.json proj/

Exit codes mirror the dispatched script (0 success; 1 data/schema; 2 usage;
3 upstream/network). ``2`` is also returned for an unknown/missing subcommand.
"""
from __future__ import annotations

import importlib
import sys
from collections.abc import Callable
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Argv-shape contract differs across the target scripts: some call
# ``parser.parse_args(argv)`` (already-sliced — pass the remaining args as-is),
# others call ``parser.parse_args(argv[1:])`` (expect the full argv with the
# program name at index 0 — prepend a synthetic prog token before forwarding).
SHAPE_SLICED = "sliced"  # main(remaining_args)
SHAPE_FULL = "full"  # main([prog, *remaining_args])

# subcommand -> (module path, attribute name of the callable, argv shape).
# Module paths are dotted from the repo root (scripts.* / validators.*); they
# resolve both in-tree (repo root on sys.path) and when installed as packages.
_REGISTRY: dict[str, tuple[str, str, str]] = {
    "cache-source": ("scripts.cache_source", "main", SHAPE_FULL),
    "assemble": ("scripts.assemble_artifacts", "main", SHAPE_SLICED),
    "render-index": ("scripts.render_agent_index", "main", SHAPE_SLICED),
    "build-claim-graph": ("scripts.build_claim_graph", "main", SHAPE_FULL),
    "verify-citations": ("scripts.verify_citations", "main", SHAPE_FULL),
    "build-dashboard": ("scripts.build_dashboard", "main", SHAPE_FULL),
    "freshness": ("validators.freshness", "_cli", SHAPE_FULL),
    "export": ("scripts.research_kb_export", "main", SHAPE_FULL),
    "backlog-stamp": ("scripts.backlog_stamp", "main", SHAPE_FULL),
    "resume-gather": ("scripts.resume_gather_from_cache", "main", SHAPE_SLICED),
    "compose-kg": ("scripts.compose_cross_project_kg", "main", SHAPE_SLICED),
}

# One-line help shown by ``research-toolkit --help`` (no module import needed).
_SUMMARIES: dict[str, str] = {
    "cache-source": "Cache a public source URL into the strict-live content cache.",
    "assemble": "Build bib/evidence/cache_manifest/gather_trace from a sources JSON + cache.",
    "render-index": "Render an evidence ledger into an agent-index folder (5-bullet blocks).",
    "build-claim-graph": "Emit claim_graph.jsonl from the project's ledgers.",
    "verify-citations": "Run the mechanical FACT-framework citation audit (substring check).",
    "build-dashboard": "Rebuild dashboard.md (trust/freshness summary) for a project.",
    "freshness": "Validate freshness + evidence/cache referential integrity (--strict).",
    "export": "Wrap claim_graph records into the research-kb export envelope.",
    "backlog-stamp": "Stamp a topic_backlog.yml entry as handed off / done.",
    "resume-gather": "Rebuild a sources-JSON skeleton from the content-addressed cache.",
    "compose-kg": "Merge per-project claim graphs into a cross-project KG snapshot.",
}


def _resolve(name: str) -> Callable[[list[str]], int]:
    """Import the target module and return its dispatch callable."""
    module_path, attr, _ = _REGISTRY[name]
    module = importlib.import_module(module_path)
    return getattr(module, attr)


# Subcommands whose target does NOT use argparse (no built-in ``--help``).
# For these we print a usage line ourselves on a help request so that
# ``research-toolkit <sub> --help`` is consistent across every verb.
_HELP_FALLBACK: dict[str, str] = {
    "freshness": "usage: research-toolkit freshness [--strict] [--today YYYY-MM-DD] <project_dir>",
}


def _dispatch(name: str, rest: list[str]) -> int:
    """Forward ``rest`` to the subcommand, adapting to its argv shape.

    argparse's ``--help`` (and arg errors) raise ``SystemExit``; translate that
    into the integer exit code so the unified CLI never aborts the interpreter
    out from under a caller that invoked ``main`` directly (e.g. tests).
    """
    if name in _HELP_FALLBACK and any(a in ("-h", "--help") for a in rest):
        print(_HELP_FALLBACK[name], file=sys.stdout)
        print(f"\n{_SUMMARIES.get(name, '')}", file=sys.stdout)
        return 0

    shape = _REGISTRY[name][2]
    func = _resolve(name)
    forwarded = rest if shape == SHAPE_SLICED else [name, *rest]
    try:
        return func(forwarded)
    except SystemExit as exc:  # argparse --help / usage error
        code = exc.code
        if code is None:
            return 0
        return code if isinstance(code, int) else 1


def _print_top_help(stream: object) -> None:
    print("usage: research-toolkit <subcommand> [args...]", file=stream)
    print("", file=stream)
    print("Unified entry point for the research_toolkit pipeline.", file=stream)
    print("", file=stream)
    print("subcommands:", file=stream)
    width = max(len(name) for name in _REGISTRY)
    for name in _REGISTRY:
        print(f"  {name:<{width}}  {_SUMMARIES.get(name, '')}", file=stream)
    print("", file=stream)
    print(
        "Run 'research-toolkit <subcommand> --help' for a subcommand's options.",
        file=stream,
    )


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help", "help"):
        # ``help`` with no topic, or no args at all -> top-level help on stdout.
        if len(argv) >= 2 and argv[0] == "help" and argv[1] in _REGISTRY:
            return _dispatch(argv[1], ["--help"])
        _print_top_help(sys.stdout)
        return 0

    sub = argv[0]
    if sub not in _REGISTRY:
        print(f"error: unknown subcommand: {sub!r}", file=sys.stderr)
        _print_top_help(sys.stderr)
        return 2

    return _dispatch(sub, argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

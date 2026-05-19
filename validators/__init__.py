"""Schema validators for research_toolkit artifacts.

One validator per artifact type. Each module exposes a `validate(path: Path) -> list[str]`
function returning a list of human-readable error strings (empty list = valid). Each module
is also runnable as `python -m validators.<name> <path>` and exits non-zero on validation
failure with errors printed to stderr.

The v1 validators are schema-oriented: they check fields, types, enums, counts,
and structural shape. v2 strict-live validators add evidence/cache/freshness
contracts for research OS artifacts (`evidence_ledger.yml`,
`cache_manifest.yml`, `claim_graph.jsonl`, and `research_kb_export.jsonl`).

URL liveness is still handled by /url-freshness-check and /freshness-audit;
content faithfulness is represented through v2 evidence IDs and cache hashes.
"""

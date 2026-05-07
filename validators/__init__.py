"""Schema validators for research_toolkit artifacts.

One validator per artifact type. Each module exposes a `validate(path: Path) -> list[str]`
function returning a list of human-readable error strings (empty list = valid). Each module
is also runnable as `python -m validators.<name> <path>` and exits non-zero on validation
failure with errors printed to stderr.

Validators are schema-only: they check fields, types, enums, counts, and structural shape.
URL liveness, content faithfulness, and hallucination-pattern detection are intentionally
out of scope (handled by /url-freshness-check and /dossier-audit respectively).
"""

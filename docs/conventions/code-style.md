# Python code style — research_toolkit conventions

Applies to all `.py` files under `scripts/`, `validators/`, and the
repository root. Tests have additional conventions in
[`test-style.md`](test-style.md).

## File header

Every `.py` file begins with:

1. Module-level docstring (triple-quoted): first-line summary +
   optional fuller description / usage examples.
2. `from __future__ import annotations` (always — see
   [Type annotations](#type-annotations)).
3. Stdlib imports (alphabetized).
4. Blank line.
5. Third-party imports.
6. Blank line.
7. Local imports (with `if __package__ in (None, ""):` boilerplate
   when running as a script — see [Local imports](#local-imports)).

Example (`validators/cache_manifest.py`):

```python
"""Validate strict-live v2 cache_manifest.yml."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators._common import URL_RE
from validators.v2_common import (
    ALLOWED_RIGHTS_STATUS,
    load_yaml_mapping,
    ...
)
```

## Module-level docstring

Triple-quoted; first line is a complete summary; optional further
paragraphs describe purpose, key behaviors, usage examples.

Good:

```python
"""Cache public source artifacts into the strict-live global content cache.

Default path is dependency-free (urllib). v2.2.1 adds optional Playwright
escalation for JS-rendered sites...
"""
```

Bad: missing summary line; PEP 257 violations; one-word docstrings.

## Type annotations

Python ≥3.11 required. PEP 604 unions only:

- ✅ `str | None`, `int | float`, `list[Path] | None`
- ❌ `Optional[str]`, `Union[int, float]`, `List[Path]`

Use lowercase generic types (PEP 585):

- ✅ `dict[str, Any]`, `list[int]`, `tuple[int, str]`
- ❌ `Dict[str, Any]`, `List[int]`, `Tuple[int, str]`

**`from __future__ import annotations` is required even on Python 3.13+.**
PEP 563 (lazy annotation evaluation) was NOT made default; PEP 649
(deferred eval) is still draft as of 2026. The import gives you:
- Lazy annotation evaluation (forward references work without quotes)
- Avoids circular-import issues
- Lower import cost
- Forward-compatibility with future Python versions

## Function-level docstrings

Plain prose with inline args/returns. No strict Google/NumPy style
required — pick whatever describes the function clearly in 1-3 sentences.
Longer functions warrant longer docstrings.

Examples (all acceptable):

```python
def _resolve(path: Path, value: str, cache_root: str | None = None) -> Path:
    """Resolve a path value from a manifest entry.

    v2.3+: when ``cache_root`` is set on the manifest, relative path values are
    resolved against the EXPANDED cache_root (supports portable manifests where
    the cache lives in a shared location...).
    """
```

```python
def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
```

Private helpers (prefix `_`) can skip docstrings if the name + signature
are self-explanatory.

## Imports

### Grouping

Three groups separated by blank lines:

1. Standard library
2. Third-party packages
3. Local imports (from `validators.*`, etc.)

Within each group: alphabetize where possible; `import X` lines before
`from X import Y` lines.

### Local imports

Scripts that need to import from `validators/` (or other local packages)
must include this boilerplate AFTER stdlib + third-party imports and
BEFORE local imports:

```python
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators._common import URL_RE
from validators.v2_common import (
    load_yaml_mapping,
    ...
)
```

This allows the script to run as `python3 scripts/foo.py` AND as part
of the installed `validators` package. It must appear ONCE per file.

## CLI entrypoint pattern

Scripts with a CLI use this pattern:

```python
def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="<command-name>", description="...")
    parser.add_argument(...)
    args = parser.parse_args(argv)
    # ... work ...
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

Conventions:
- Function name is `main` (not `_cli` / `cli` / `run`).
- Signature: `main(argv: list[str]) -> int`.
- Returns exit code; never `sys.exit()` from inside `main()`.
- Argparse `prog=` set explicitly to the command name (helps `--help` output).

## Exit codes

| Code | Meaning |
|---:|---|
| `0` | Success |
| `1` | Schema / data error (validation failed, parse error, missing required field, etc.) |
| `2` | Usage / argument error (missing required arg, file not found, malformed CLI invocation) |
| `3` | Upstream / network / API error (external dependency failed; partial state may be persisted with error info in output) |

Document the script's exit codes in its `main()` docstring or near the
top of the file. If a script needs a new exit code value beyond 3,
document it explicitly + add a brief justification.

## Error messages

To stderr; lowercase prefix; f-strings:

```python
print(f"error: path does not exist: {path}", file=sys.stderr)
return 1
```

Validators return error strings to a caller (not stderr); use a `loc:`
prefix to indicate location context:

```python
errors.append(f"entries[{idx}].cache_id: {cache_id!r} not found in cache_manifest")
```

## stderr / logging

Use `print(..., file=sys.stderr)` for diagnostics. **Do not use the
`logging` module** — no script in the project uses it; introducing it
for one script creates inconsistency in log format + output target.

If you need leveled output, use simple prefixes:

```python
print(f"warning: ...", file=sys.stderr)
print(f"error: ...", file=sys.stderr)
```

## Path handling

Use `pathlib.Path` everywhere. Idiom for user-supplied paths:

```python
path = Path(arg).expanduser().resolve()
```

- `.expanduser()` expands `~` to home dir.
- `.resolve()` makes the path absolute + collapses `..` segments.
- Combined: any user input becomes a canonical absolute Path.

For checking existence + reading in one breath, prefer:

```python
try:
    content = path.read_text(encoding="utf-8")
except FileNotFoundError:
    ...
```

over:

```python
if path.exists():
    content = path.read_text(...)  # TOCTOU race
```

— unless the existence check is itself the logic (e.g., fallback
resolution choosing between two candidate paths).

## Naming

- Public functions / classes: `snake_case` / `PascalCase`.
- Private helpers: `_snake_case` prefix.
- Constants: `UPPER_SNAKE_CASE` at module scope.
- Type aliases: `PascalCase` (e.g., `type Result = dict[str, Any]`).

## Cross-references

- [`test-style.md`](test-style.md) — Pytest conventions (extends this file's
  rules for tests).
- [`../../README.md`](../../README.md) — TDD discipline + validator scope.
- [`../../references/agent_discipline.md`](../../references/agent_discipline.md)
  — agent dispatch limits (applies when calling sub-agents).

# Pytest conventions — research_toolkit

Extends [`code-style.md`](code-style.md) with test-specific rules.
Applies to all `tests/test_*.py` files.

## Test function naming

`test_<feature>_<scenario>` with action-verb scenarios:

| Pattern | Example |
|---|---|
| `_accepts_` | `test_validate_recipe_accepts_minimal_valid_entry` |
| `_rejects_` | `test_validate_recipe_rejects_duplicate_cache_key` |
| `_extracts_` | `test_safe_text_html_extracts_text` |
| `_writes_` | `test_cache_one_writes_blob_text_metadata` |
| `_falls_back_` | `test_cache_manifest_falls_back_to_manifest_local_for_derived_artifacts` |
| `_matches_` | `test_sha256_helper_matches_hashlib` |
| `_catches_` | `test_synthesize_catches_api_exception_writes_partial_manifest` |
| `_detects_` | `test_synthesize_detects_orphan_rows_in_manifest` |

The verb describes what's being tested + the expected behavior.

## Fixture usage

Use `tmp_path` (function-scoped, auto-cleanup) for any test that
needs to write files. Use `tmp_path_factory` only when sharing
across multiple tests in the same module (rare).

Shared fixtures live in `tests/conftest.py`:

- `mini_dir` — minimal fixture project tree for validator smoke tests
- PDF bytes fixtures: `plain_text_pdf_bytes`, `equation_rich_pdf_bytes`,
  `image_only_pdf_bytes`, `encrypted_pdf_bytes`
- `test_cache_root` — temporary cache root for cache-writing tests

Custom test-local fixtures: define in the test file, not in `conftest.py`,
unless ≥2 test files share them.

## Assertions

Bare `assert` statements; multiple per test OK. No assertion libraries.

```python
def test_synthesize_happy_path_3_samples(tmp_path):
    ...
    exit_code, manifest = ds.synthesize(...)
    assert exit_code == 0
    assert manifest["total_samples"] == 3
    assert manifest["bail_fired"] is False
    rows = [json.loads(line) for line in ...]
    assert len(rows) == 3
    assert all(row["template_id"] == "t1" for row in rows)
```

For substring checks in error lists:

```python
errors = validator.validate(path)
assert any("substring expected" in e for e in errors), errors
```

The trailing `, errors` argument prints the actual list on failure —
critical for debugging.

For exception testing:

```python
import pytest

def test_X_raises_on_Y():
    with pytest.raises(ValueError, match="expected pattern"):
        do_something()
```

## Mock + fake patterns

**Do not use `unittest.mock`** (no test file in the project does).

Instead, use either:

1. **Hand-rolled dataclass-like doubles** (preferred for SDK clients,
   responses with structured fields):

```python
@dataclass
class _FakeUsage:
    input_tokens: int = 200
    output_tokens: int = 400
    cache_read_input_tokens: int = 0

@dataclass
class _FakeMessage:
    content: list[_FakeBlock] = field(default_factory=list)
    usage: _FakeUsage = field(default_factory=_FakeUsage)

class _FakeClient:
    def __init__(self, scenarios):
        self.messages = _FakeMessages(scenarios)
```

Place these AT THE TOP of the test file (after imports) so they're
visible without scrolling.

2. **`monkeypatch.setattr`** (preferred for module-level function
   replacement, e.g., `urlopen`, `requests.get`):

```python
def test_cache_one_handles_failure(tmp_path, monkeypatch):
    def _fake_fetch(url, headers=None, timeout=None):
        raise URLError("simulated failure")
    monkeypatch.setattr("scripts.cache_source._urlopen", _fake_fetch)
    ...
```

## Test data setup

Three patterns by use case:

1. **Inline dict literals** for small fixtures (≤10 lines):

```python
def test_X():
    data = {
        "schema_version": 2,
        "topic": "test",
        ...
    }
```

2. **Helper functions** that build YAML or JSON payloads (when used
   in multiple tests in the same file):

```python
def _write_manifest(path, entries):
    payload = {"schema_version": 2, "entries": entries, ...}
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
```

3. **Conftest fixtures** for generated binary blobs (PDFs, etc.).

Prefer `yaml.safe_dump(data, sort_keys=False)` (preserves field
order, matches what writer scripts emit) over `yaml.dump`.

## File structure

Top of file:

```python
"""Tests for <module>.

<Optional brief description of what's tested + what's mocked.>
"""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import dataset_synthesize as ds  # type: ignore[import-not-found]

# Test doubles
# ...

# Test cases grouped by topic
# ...
```

For tests that import scripts/* (not packaged): use the `sys.path.insert`
+ module-level import pattern. Add `# type: ignore[import-not-found]`
to suppress mypy/pyright warnings.

## Test organization

Group tests by topic with comment headers:

```python
# ---------- Recipe validation ----------

def test_validate_recipe_accepts_minimal_valid_entry():
    ...

def test_validate_recipe_rejects_duplicate_id():
    ...

# ---------- Cost computation ----------

def test_compute_call_cost_input_only():
    ...
```

Each comment header announces the topic; tests under it cover that
topic's positive + negative cases.

## Coverage expectations

Every validator MUST have:
- ≥1 positive case (accepts a known-good fixture)
- ≥1 negative case (rejects a corrupted variant)

Validators that share helpers (e.g., `verify_excerpt_anchor`) get
unit tests for the helper directly + integration tests through the
caller (see PR #15's `test_evidence_ledger_validates_dossier_local_body_anchor_with_cache_root`).

## Cross-references

- [`code-style.md`](code-style.md) — Python style (applies to tests too).
- [`../../tests/conftest.py`](../../tests/conftest.py) — shared fixtures.
- [`../../pyproject.toml`](../../pyproject.toml) — pytest config
  (`testpaths`, `addopts="-v --tb=short"`).

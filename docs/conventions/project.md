# Project conventions index

Read the convention matching the task before editing:

| Topic | File |
|---|---|
| Python code | `docs/conventions/code-style.md` |
| Tests | `docs/conventions/test-style.md` |
| Claude plugin skills | `docs/conventions/skill-spec.md` |
| Templates | `docs/conventions/templates.md` |
| Producer and verifier ownership | `docs/architecture.md` |

Hard rules:

1. Begin Python files with a module docstring and
   `from __future__ import annotations`.
2. Use PEP 604 unions, lowercase generic types, `pathlib.Path`, and explicit
   integer CLI exit codes.
3. Print diagnostics to stderr; do not introduce the logging module.
4. Do not use `unittest.mock`; use hand-built doubles and `monkeypatch`.
5. Every validator has a positive and negative test.
6. Keep exactly six public plugin skills unless deliberately changing the
   interface and its contract tests.
7. Use `${CLAUDE_PLUGIN_ROOT}` in plugin skills, never checkout-specific paths.
8. End every skill with a deterministic validation gate and never silently
   advance past failure.

Use conventional commits in the form `<type>(<scope>): <summary>`. Preserve
historical plans and burn-in records as dated evidence; update active README,
architecture, getting-started, and troubleshooting guidance when behavior
changes.

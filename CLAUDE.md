# CLAUDE.md — research_toolkit conventions index

Entry point for Claude Code sessions (and any agentic workflow). The
project's load-bearing rules live across multiple files; this index
maps them so agents can find the right one for a given question.

## Auto-loaded context

Claude Code loads this file at session start. Read the file matching
your task before generating code.

## Convention files

| Topic | File | When to read |
|---|---|---|
| Python code style | [`docs/conventions/code-style.md`](docs/conventions/code-style.md) | Writing or editing any `.py` file in `scripts/`, `validators/`, or top-level. Covers imports, type annotations, docstrings, CLI pattern, error messages, exit codes, path handling. |
| Pytest conventions | [`docs/conventions/test-style.md`](docs/conventions/test-style.md) | Writing or editing any `tests/test_*.py` file. Covers naming, fixtures, assertions, mock patterns (hand-rolled doubles via monkeypatch — NOT `unittest.mock`), data setup. |
| Skill spec format | [`docs/conventions/skill-spec.md`](docs/conventions/skill-spec.md) | Writing or editing any `.claude/skills/*.md` file. Covers frontmatter, section order, voice, length, cross-references. |
| Template format | [`docs/conventions/templates.md`](docs/conventions/templates.md) | Writing or editing any `templates/*.yml` or `*.template.{yml,md}` file. Covers field ordering, comment blocks, optional-field handling. |

## Existing rules (not redundantly re-codified here)

The following rules are documented elsewhere — read these too:

- [`README.md`](README.md) — TDD discipline: every skill ends with a
  mandatory `## Validation` step running its validator; no silent
  partial success. Validator scope: schema-only, not URL liveness or
  content faithfulness.
- [`references/citation_rules.md`](references/citation_rules.md) — URL
  canonical forms, YAML quoting, bibkey naming (`{firstauthor_lc}{year}{slug}`),
  "no LLM-generated specifics" rule, source tiers T1/T2/T3.
- [`references/agent_discipline.md`](references/agent_discipline.md)
  — agent tool-call budget (~25-30 per dispatch), mid-phase validator
  checkpoint cadence, recovery patterns.
- [`references/strict_live_v2.md`](references/strict_live_v2.md) —
  evidence/cache/freshness artifact schema, v2.3 manifest path
  portability.
- [`BURN_IN_NOTES.md`](BURN_IN_NOTES.md) + [`burn_in.yml`](burn_in.yml)
  — friction tracking: file new issues with status surfaced/applied/
  deferred/wontfix. See `docs/troubleshooting.md` for the schema.

## Commit + branch conventions

- **Commits**: conventional-commits format `<type>(<scope>): <summary> [— <body>] [(closes #N)]`.
  Types in use: `feat`, `fix`, `docs`, `chore`, `release`, `style`.
  Scopes are file/module-oriented (e.g., `validators`, `skills`,
  `cache`, `synthesis`).
- **Branches**: `<type>/<N>-<slug>` where `N` is the issue number
  (e.g., `feat/1-dataset-synthesize-skill`, `fix/14-fallback-resolution`).
- **PRs**: open against `main`; one logical change per PR; review
  comments addressed as additional commits (not amends/squashes).

## Quick reference: hard rules

These are the rules most likely to be violated by a fresh session:

1. **Validator discipline**: every skill ends with `## Validation` running
   its validator. No silent partial success.
2. **Conventional commits**: subject under 72 chars; type + scope
   mandatory.
3. **`from __future__ import annotations`** at the top of every `.py` file.
4. **PEP 604 unions** (`str | None`, not `Optional[str]`); `dict[str, Any]`
   lowercase.
5. **No `unittest.mock`** in tests; use hand-rolled doubles + `monkeypatch.setattr`.
6. **No `logging` module**; use `print(..., file=sys.stderr)`.
7. **Skill spec section order**: `## Usage` → `## When to use` →
   `## Workflow` → `## Templates` → `## References` → `## Validation`
   → `## Output / handoff`.
8. **Tool-call budget per agent**: ~25-30; split for 10+ sources;
   mid-phase validator checkpoint every 5-6 sources.

If your work touches any of these, read the relevant file in
`docs/conventions/` for the full pattern + examples.

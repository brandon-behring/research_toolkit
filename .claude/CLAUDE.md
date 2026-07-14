# CLAUDE.md — research_toolkit conventions index

Entry point for Claude Code sessions (and any agentic workflow). The
project's load-bearing rules live across multiple files; this index
maps them so agents can find the right one for a given question.

## Auto-loaded context

Claude Code loads this file when working in the source repository. Installed
plugin copies do not load root `CLAUDE.md`; runtime guidance lives in the six
plugin skills instead.

## Convention files

| Topic | File | When to read |
|---|---|---|
| Python code style | [`docs/conventions/code-style.md`](docs/conventions/code-style.md) | Writing or editing any `.py` file in `scripts/`, `validators/`, or top-level. Covers imports, type annotations, docstrings, CLI pattern, error messages, exit codes, path handling. |
| Pytest conventions | [`docs/conventions/test-style.md`](docs/conventions/test-style.md) | Writing or editing any `tests/test_*.py` file. Covers naming, fixtures, assertions, mock patterns (hand-rolled doubles via monkeypatch — NOT `unittest.mock`), data setup. |
| Skill spec format | [`docs/conventions/skill-spec.md`](docs/conventions/skill-spec.md) | Writing or editing any `skills/*/SKILL.md` file. Covers frontmatter, section order, voice, length, cross-references. |
| Template format | [`docs/conventions/templates.md`](docs/conventions/templates.md) | Writing or editing any `templates/*.yml` or `*.template.{yml,md}` file. Covers field ordering, comment blocks, optional-field handling. |

## Existing rules (not redundantly re-codified here)

The following rules are documented elsewhere — read these too:

- [`README.md`](README.md) — TDD discipline: every skill ends with a
  mandatory `## Validation` step running its validator; no silent
  partial success. Validator scope: schema-only, not URL liveness or
  content faithfulness.
- [`docs/architecture.md`](docs/architecture.md) — producer / verifier /
  agent-authored map for the committed pipeline (which script PRODUCES each
  artifact vs which validator VERIFIES it), the display-vs-evidence contract
  (`validators/agent_index_display.py`), and the trust model's guarantees +
  honest holes. Read before editing any `scripts/*` producer, the CLI, or the
  `/research-toolkit:research` orchestrator.
- [`references/citation_rules.md`](references/citation_rules.md) — URL
  canonical forms, YAML quoting, bibkey naming (`{firstauthor_lc}{year}{slug}`),
  "no LLM-generated specifics" rule, source tiers T1/T2/T3.
- [`references/agent_discipline.md`](references/agent_discipline.md)
  — agent tool-call budget (~25-30 per dispatch), mid-phase validator
  checkpoint cadence, recovery patterns.
- [`references/strict_live_v2.md`](references/strict_live_v2.md) — historical
  evidence/cache/freshness artifact schema and v2.3 migration context.
- [`BURN_IN_NOTES.md`](BURN_IN_NOTES.md) + [`burn_in.yml`](burn_in.yml)
  — friction tracking: file new issues with status surfaced/applied/
  deferred/wontfix. See `docs/troubleshooting.md` for the schema.

## Commit + branch conventions

- **Commits**: conventional-commits format `<type>(<scope>): <summary> [— <body>] [(closes #N)]`.
  Types in use: `feat`, `fix`, `docs`, `chore`, `release`, `style`.
- **Branches**: `<type>/<N>-<slug>` when an issue number exists; use a
  descriptive conventional prefix for audit/remediation branches.
- **PRs**: open against `main`; one logical change per PR; review comments
  addressed as additional commits unless the repository policy says otherwise.

## Quick reference: hard rules

1. **Validator discipline**: every skill ends with `## Validation` running
   its validator. No silent partial success.
2. **Conventional commits**: subject under 72 chars; type + scope mandatory.
3. **`from __future__ import annotations`** at the top of every `.py` file.
4. **PEP 604 unions** (`str | None`, not `Optional[str]`); `dict[str, Any]`
   lowercase.
5. **No `unittest.mock`** in tests; use hand-rolled doubles + `monkeypatch.setattr`.
6. **No `logging` module**; use `print(..., file=sys.stderr)`.
7. **Exactly six public plugin skills** unless deliberately changing the
   interface and its contract tests.
8. **Portable paths**: plugin skills use `${CLAUDE_PLUGIN_ROOT}` and never a
   checkout-specific absolute path.
9. **Tool-call budget per agent**: ~25-30; split for 10+ sources; mid-phase
   validator checkpoint every 5-6 sources.

If your work touches any of these, read the relevant file in
`docs/conventions/` for the full pattern and examples.

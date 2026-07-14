# Claude plugin skill format

## Location and discovery

Place a workflow at `skills/<skill-name>/SKILL.md`. The plugin manifest lives at
`.claude-plugin/plugin.json`; Claude exposes each workflow as
`/research-toolkit:<skill-name>`.

Do not add flat `.claude/skills/*.md` files or global symlink instructions.

## Frontmatter

Use:

```yaml
---
name: skill-name
description: State what the workflow does and the requests that should trigger it.
allowed-tools: Read, Write, Edit, Bash, WebSearch, WebFetch
---
```

Keep tools to the minimum the workflow uses. Omit file-path trigger filters on
workflow skills because they make discovery context-dependent.

## Body

- Use imperative instructions and a concise workflow.
- Reference plugin resources with `${CLAUDE_PLUGIN_ROOT}`.
- Link detailed schemas and variants from `references/`; do not duplicate them.
- Put repeatable or fragile mechanics behind the `research-toolkit` CLI.
- End with a deterministic `## Validation` gate.
- State the produced records and downstream handoff.
- Use a HARD RULE only for silent corruption, unsafe behavior, or false success.

The six public skills are `research`, `audit`, `freshness`, `topic-discovery`,
`dataset-research`, and `release`. Adding another public skill is an interface
change and requires updating plugin-contract tests and release notes.

## Decision protocol

Research, dataset, and topic-discovery skills must read
`${CLAUDE_PLUGIN_ROOT}/references/decision_protocol.md`. That protocol is
self-contained and records question, viable options, recommendation, selection,
and impact in the run manifest.

## Validation

Run:

```bash
claude plugin validate --strict .
pytest tests/test_plugin_contract.py
```

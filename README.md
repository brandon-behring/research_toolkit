# research_toolkit

`research_toolkit` is an auditable research-dossier system with two layers:

- A Claude Code plugin for planning, discovery, semantic review, freshness,
  dataset research, and release decisions.
- A platform-neutral Python CLI for schemas, referential integrity, provenance,
  impact analysis, corpus checks, and release hashes.

Version 3 is a clean break in the agent interface. The 15 loose flat skills are
replaced by six plugin-namespaced workflows:

- `/research-toolkit:research`
- `/research-toolkit:audit`
- `/research-toolkit:freshness`
- `/research-toolkit:topic-discovery`
- `/research-toolkit:dataset-research`
- `/research-toolkit:release`

The existing deterministic v2.6 producers and validators remain available
through the CLI while dossiers migrate to the versioned v1 canonical contract.
They are implementation tools, not legacy slash-command aliases.

## Install for development

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
claude plugin validate --strict .
.venv/bin/pytest
```

Install the plugin from an approved local/team marketplace or use the path as a
development plugin according to Claude Code's plugin workflow. Do not create
global `~/.claude/skills/*.md` symlinks.

## Canonical workflow

```text
discover → intake → capture → normalize → evidence/claims
→ independent audit → synthesis/render → release → watch/refresh
```

The canonical dossier is record-first:

```text
dossier.yaml
sources.jsonl
evidence.jsonl
claims.jsonl
reviews.jsonl
watch.jsonl
runs/<run-id>/...
derived/...
release.json
```

Schemas are under `schemas/v1/`. A source snapshot and matching excerpt prove
provenance, not meaning. `reviews.jsonl` records the separate judgments about
entailment, currentness, methods, and risk of bias.

## CLI

Canonical workflow commands:

```bash
research-toolkit research run --help
research-toolkit audit <dossier>
research-toolkit freshness poll <dossier> --today YYYY-MM-DD
research-toolkit impact <dossier> --claim-id <id>
research-toolkit release check <dossier>
research-toolkit corpus check <root>
research-toolkit dataset run --help
```

The CLI's `research run` and `dataset run` commands create or validate the
deterministic run boundary. Claude performs the generative discovery and
semantic-review steps through the plugin skill; the CLI never pretends those
judgments are mechanical.

Existing v2.6 deterministic commands such as `assemble`, `render-index`,
`build-claim-graph`, `verify-citations`, `build-dashboard`, `freshness`, and
`export` remain callable during migration.

## Legacy import

Use the one-time importer to create a separate canonical dossier:

```bash
python -m research_toolkit.legacy_import <legacy-dossier> <canonical-dossier>
```

The importer is idempotent, refuses to overwrite differing outputs, preserves
legacy graph/export bytes when present, and marks imported claims unresolved.
It never turns a structural cache check into semantic approval.

## Validation and safety

```bash
research-toolkit audit <dossier>
research-toolkit release check <dossier>
research-toolkit corpus check <corpus-root>
```

Retrieval treats fetched content as untrusted, keeps restricted source bodies
local, and separates access from redistribution rights. Freshness polling is
read-only; human review is required before claims or consumers change.

For architecture and trust boundaries, read `docs/architecture.md`. For a
walkthrough, read `docs/getting_started.md`. Historical v1/v2 plans and burn-in
records remain in the repository as dated evidence, not current instructions.

## Tests

The suite retains the v1/v2 validator and producer regressions and adds plugin,
schema, canonical-dossier, referential-integrity, CLI, and importer tests.

```bash
make test
make plugin-check
make e2e
```

## License

MIT

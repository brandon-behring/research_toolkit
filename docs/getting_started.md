# Getting started

## Choose a workflow

| Need | Skill |
|---|---|
| Research or refresh a topic | `/research-toolkit:research` |
| Independently verify a dossier | `/research-toolkit:audit` |
| Check source currency | `/research-toolkit:freshness` |
| Mine a corpus for research gaps | `/research-toolkit:topic-discovery` |
| Research datasets and recipes | `/research-toolkit:dataset-research` |
| Gate a coordinated release | `/research-toolkit:release` |

All skills are plugin-namespaced. There are no `/research-plan`,
`/research-gather`, `/dossier-build`, `/agent-index`, `/dossier-audit`, or
`/url-freshness-check` aliases in the clean-break interface.

## Install the development environment

```bash
cd /path/to/research_toolkit
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
claude plugin validate --strict .
.venv/bin/pytest
```

Use a Claude Code marketplace or development-plugin path to install the plugin.
Do not symlink individual Markdown files into `~/.claude/skills`.

## Start a research dossier

Invoke:

```text
/research-toolkit:research "Your topic"
```

The skill first inspects the repository, then resolves consequential choices
one at a time. Each question includes viable options, a recommendation, and
the downstream impact. The decisions are stored in the run manifest; retrieval
does not begin until the specification is complete.

For a direct CLI scaffold:

```bash
research-toolkit research run ./research_example \
  --initialize \
  --dossier-id dossier_example \
  --topic "Example topic" \
  --run-id run_20260714 \
  --date 2026-07-14
```

This creates the canonical record boundary and a planned run manifest. It does
not claim to have done web discovery or semantic review.

## Understand the records

- `sources.jsonl` identifies requested, canonical, and final sources plus
  authority scope, independence, rights, visibility, and snapshot hashes.
- `evidence.jsonl` stores excerpts and many-to-many support links.
- `claims.jsonl` stores atomic propositions, status, confidence, and
  supersession.
- `reviews.jsonl` stores entailment, currency, methodology, risk of bias, and
  independent-review decisions.
- `watch.jsonl` stores source owners, volatility, cadence, events, and the next
  due semantic review.
- `runs/` stores decisions, searches, attempts, environment, and artifact
  hashes.
- `derived/` contains only deterministic outputs.
- `release.json` binds validators, reviewers, repositories, waivers, and exact
  artifact hashes.

Run the structural and referential gate at any point:

```bash
research-toolkit audit ./research_example
```

## Audit meaning, not only structure

Invoke:

```text
/research-toolkit:audit ./research_example
```

The deterministic CLI catches schema, ID, path, and hash failures. The skill
adds the necessary semantic work: read full source context, test entailment,
evaluate methods and bias, inspect counterevidence, and check current sources.
A matching excerpt proves presence, not support.

Trace an affected claim or source:

```bash
research-toolkit impact ./research_example --claim-id claim_example
research-toolkit impact ./research_example --source-id src_example
```

## Check freshness

Invoke `/research-toolkit:freshness`, or select due records mechanically:

```bash
research-toolkit freshness poll ./research_example --today 2026-07-14 --json
```

Polling is read-only. HTTP success, a recent retrieval, or an unchanged hash
does not prove semantic freshness. Material changes require impact analysis and
human adjudication.

## Research a dataset

Invoke:

```text
/research-toolkit:dataset-research "Dataset topic"
```

Dataset runs use the same evidence and review contracts plus license, privacy,
PII, leakage, duplicate, contamination, recipe-hash, seed, resume, cost, and
version controls.

## Import a legacy dossier

Import into a separate directory:

```bash
python -m research_toolkit.legacy_import ./legacy ./canonical
```

Rerunning the same import is a no-op. A differing target fails rather than
overwriting it. Imported claims are `unresolved` until semantic review.

## Gate a release

After review and deterministic rebuild, invoke `/research-toolkit:release` and
run:

```bash
research-toolkit audit ./research_example --release
research-toolkit release check ./research_example
```

Use release IDs `rr-YYYYMMDD.N`. A valid release pins repository commits,
freshness cutoff, validator versions, reviewer acceptance, waivers, consumer
bindings, and hashes. Publishing, pushing, merging, or external ingestion still
requires explicit authorization.

## Legacy deterministic producers

Existing v2.6 commands remain available while dossiers migrate:

```bash
research-toolkit assemble --help
research-toolkit render-index --help
research-toolkit build-claim-graph --help
research-toolkit verify-citations --help
research-toolkit build-dashboard --help
research-toolkit export --help
```

They are implementation compatibility commands, not discoverable legacy
skills. New agent workflows write the canonical contract.

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

The core and development installs do not activate document parsers. The
supported default is bounded raw-byte caching with `--no-extract-pdfs`.
Installing either PDF extra is an explicit opt-in to processing untrusted PDF
bytes in-process and requires a source-specific risk decision:

```bash
pip install -e ".[pdf]"       # pdfplumber text extraction
pip install -e ".[rich-pdf]"  # PDF extraction + optional Docling math/OCR
```

Browser execution is disabled in the supported workflow. Do not pass
`--escalate-on-failure` or install a browser runtime for this plugin until a
separate browser worker has a verified process sandbox and default-deny network
boundary. Prefer a static/official source, cache raw bytes, or leave a JS-only
source unresolved.

Each skill calls `${CLAUDE_PLUGIN_ROOT}/bin/research-toolkit`. The wrapper runs
the copied plugin directly when Python and PyYAML are available, otherwise it
can materialize the small core package through `uvx` without writing into the
installed-plugin directory. It fails with an actionable preflight message when
neither path exists; it never silently skips validation.

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
"${CLAUDE_PLUGIN_ROOT}/bin/research-toolkit" import-legacy \
  <legacy-dossier> <canonical-dossier>
```

The importer builds and validates a staging tree before any target artifact is
written, redacts durable URL query values, refuses URL-derived identifiers and
differing outputs, and marks imported claims unresolved. Legacy derived files
are not copied across this trust boundary; rebuild them from canonical records.
The importer never turns a structural cache check into semantic approval.

## Validation and safety

```bash
research-toolkit audit <dossier>
research-toolkit release check <dossier>
research-toolkit corpus check <corpus-root>
```

Retrieval treats fetched content as untrusted. The supported path is public,
read-only HTTP(S) raw caching with public-address validation and connection
pinning, redirect revalidation, standard ports, five redirects, a 25 MiB wire
limit, identity encoding, an absolute DNS/header/body deadline, and no ambient
proxy. Generic query strings are rejected before DNS; only a small
host-and-key allowlist of public resource identifiers is accepted. Use a clean
canonical URL and never a signed/authenticated URL. Durable redaction removes
userinfo and fragments, then replaces every non-allowlisted query with the
single fixed marker `?redacted=REDACTED`; no attacker-controlled query key or
value is retained. Canonical records and derived exports are scanned
recursively for embedded URLs and URL/request fingerprint aliases.
Redirects are revalidated and a sanitized `final_url` is recorded whenever the
effective request URL changes. OS calls without portable cancellation are
watchdog-bounded and concurrency-capped; split-horizon routing of nominally
global addresses remains an environmental residual. Browser execution is
disabled. Cache rights default to `unknown`; access, license, redistribution
rights, and source authority remain separate. See
`references/security_and_rights.md` for the exact boundary and residual risks.

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

# Architecture and trust boundaries

## Two layers

The toolkit deliberately separates judgment from mechanics:

- Six Claude plugin skills plan, discover, interpret, review, and adjudicate.
- The Python CLI validates contracts, IDs, references, dates, paths, hashes,
  due watches, impact paths, and release consistency.

The CLI does not claim to decide relevance or entailment. The skills do not
hand-edit deterministic `derived/` outputs.

## Canonical flow

```text
discover → intake → capture → normalize → evidence/claims
→ independent audit → synthesis/render → release → watch/refresh
```

Every stage writes or consumes a versioned record. The run manifest captures
the exact inputs, environment, decisions, queries, attempts, and output hashes.
A red deterministic or required semantic gate halts the chain.

## Record graph

```text
SourceRecord ──< EvidenceRecord >── ClaimRecord
     │                                  │
SourceWatchRecord                 ClaimReviewRecord
     │                                  │
RefreshEvent                     ConsumerBinding
             \                    /
              ResearchReleaseManifest
                       │
                  ResearchLock
```

Relationships are many-to-many. Identifiers are stable. Removal is explicit
through status, supersession, and downstream tombstones.

## What mechanics prove

The deterministic layer can prove:

- JSON/JSONL/YAML records satisfy the bundled versioned contracts.
- IDs are unique and evidence, claims, reviews, watches, and consumer bindings
  resolve.
- Declared files stay beneath the dossier root.
- Declared artifact bytes match their SHA-256 digests.
- Watch records are due according to recorded dates.
- A source or claim reaches the reported evidence and consumers.
- Re-running the legacy importer on identical inputs does not change output.

## What mechanics do not prove

The deterministic layer does not prove:

- An excerpt entails a proposition.
- Search was comprehensive or unbiased.
- A study design supports the intended generalization.
- A source is still semantically current because it is reachable or unchanged.
- A public page can legally be redistributed.
- An interpretive synthesis follows from individually valid claim IDs.

Those decisions require dated `ClaimReviewRecord` or `RefreshEvent` judgments,
with independent review according to risk.

## Plugin boundary

The plugin is rooted at `.claude-plugin/plugin.json`. Claude discovers exactly
these skill folders under `skills/`:

- `research`
- `audit`
- `freshness`
- `topic-discovery`
- `dataset-research`
- `release`

Claude namespaces them as `/research-toolkit:<skill>`. Skills locate scripts,
schemas, templates, and references through `${CLAUDE_PLUGIN_ROOT}` and never
depend on a specific `~/Claude` checkout. The decision protocol adapts the
useful interaction pattern from `/exploring-options` without requiring that
personal skill.

## Existing deterministic spine

The v2.6 producers and validators remain under `scripts/` and `validators/`.
Flat CLI commands continue to dispatch to them so existing dossiers can be
rebuilt while they migrate. They are not exposed as Claude skill aliases.

The one-way importer reads legacy `bib_ledger.yml`, `evidence_ledger.yml`, and
`claim_graph.jsonl`, then emits the canonical boundary through the isolated
bundled launcher. It redacts durable URL query values, assigns source IDs
without URL hashes, validates a complete staging tree before target writes, and
does not copy legacy derived bytes across the trust boundary. Imported claims
remain unresolved because old structural validation is not semantic approval.

## Freshness boundary

`freshness poll` only selects due watches. A scheduler may retrieve and classify
sources but must not edit a dossier or publish. Humans accept material changes,
then the normal research, impact, audit, rebuild, and release gates run.

## Security and rights

Fetched material is untrusted data. The supported capture path uses
`research_toolkit.retrieval_security`: GET/HEAD HTTP(S), public-only DNS
answers, direct connections pinned to a validated address, TLS hostname
verification, redirect revalidation, standard ports, five redirects, and a
25 MiB response bound. Ambient proxies are disabled. One absolute deadline
covers DNS, connection, response headers, and incremental body reads. Because
portable cancellation is unavailable for some OS resolver/header calls, their
watchdog workers are concurrency-capped; a wedged worker can deny later reads
until it returns, but cannot create an unbounded thread population.
Split-horizon networks that route nominally global space internally remain
outside what IP classification alone can prove.

Browser execution is disabled pending a verified process sandbox and
default-deny network boundary. Supported skills cache raw bytes and pass
`--no-extract-pdfs`; PDF parsing is a separate explicit opt-in. Treat every URL
query value as potentially sensitive, reject credentials and signed URLs, and
record only sanitized provenance. Generic query strings fail before DNS; a
small domain-specific allowlist covers public resource IDs. Any other durable
query is represented only by the exact marker `?redacted=REDACTED`; recursive
validation also rejects embedded unsafe URLs and URL/request fingerprints.
Cache records keep
sanitized requested provenance and include sanitized `final_url` whenever a
redirect or approved fallback changes the effective URL. Visibility, license,
access, source authority, and redistribution rights are separate fields;
rights default to `unknown`. The full boundary is in
`references/security_and_rights.md`.

Canonical assembly and legacy import create owner-only directories (`0700`)
and files (`0600`) atomically; the four strict-live ledgers commit as one
rollback-protected set. Strict exports use explicit record-type and
field allowlists, so removing a cache identifier cannot make a body field
exportable.

## Release boundary

Release IDs use `rr-YYYYMMDD.N`. The release manifest pins repositories,
validators, freshness cutoff, artifact hashes, reviewer acceptance, unresolved
findings, and waivers. Consumer repositories use `ResearchLock` files to verify
the release without depending on a sibling checkout.

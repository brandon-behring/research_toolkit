# Architecture — producer / verifier / agent-authored map

How the strict-live pipeline is wired, now that the whole spine is committed
code (v2.6). Audience: future-you or a Claude Code agent that needs to know
*which* code produces each artifact, *which* code verifies it, and what the
trust model actually guarantees — versus what it only flags.

For the narrative onboarding read [`getting_started.md`](getting_started.md);
for the v3 evidence/anchor schema read
[`../references/strict_live_v2.md`](../references/strict_live_v2.md); for the
v2.6 milestone rationale read [`ROADMAP_v2_6.md`](ROADMAP_v2_6.md).

## The split that matters

Every artifact in a strict-live project is one of three kinds:

- **Producer** — a committed, deterministic Python script writes it. Same
  inputs → byte-stable output. No LLM in the loop.
- **Verifier** — a committed validator (`validators/*.py`) checks it against a
  schema + cross-artifact integrity. Returns a list of error strings; empty
  list = pass. Fast, deterministic, no network.
- **Agent-authored** — a Claude Code *skill* (a Markdown prompt under
  `.claude/skills/`) produces it by reasoning over sources. This is the only
  place an LLM writes content, and it is always followed by a verifier.

The v2.6 work moved the dossier **assembler** and **renderer** out of
uncommitted `~/Claude/_*.py` scratch files and into committed producers, so the
two stages that used to be hand-authored-per-topic are now deterministic code
with their own validators. What remains agent-authored is the genuinely
generative work: scoping a topic, discovering sources, and selecting excerpts.

## Stage flow

The pipeline is a linear chain; each stage's output is the next stage's input.
The autonomous `/research` skill ([`.claude/skills/research.md`]) drives the
whole chain, gating each stage on its validator and halting on a resumable
checkpoint if a stage cannot be made to pass.

| # | Stage | Produced by | Kind | Primary artifact(s) | Verified by |
|---|---|---|---|---|---|
| 0 | plan | `/research-plan` | agent | `research_plan.md` | `validators/research_plan.py` |
| 1 | gather | `/research-gather` (+ `scripts/cache_source.py`) | agent + producer | sources (in cache) + `gather_trace.yml` | `validators/gather_trace.py` |
| 2 | assemble | `scripts/assemble_artifacts.py` | producer | `bib_ledger.yml`, `evidence_ledger.yml`, `cache_manifest.yml`, `gather_trace.yml` | `validators/{bib_ledger,evidence_ledger,cache_manifest,gather_trace}.py` |
| 3 | claim-graph | `scripts/build_claim_graph.py` | producer | `claim_graph.jsonl` | `validators/claim_graph.py` |
| 4 | render | `scripts/render_agent_index.py` (+ `render_config.yml`) | producer | `pre_selection_manifest.yml`, `agent_index/` | `validators/{pre_selection_manifest,agent_index,agent_index_display}.py` |
| 5 | audit | `scripts/verify_citations.py` | producer | `citation_audit_report.md` | (self-checking: exit 1 on substring failure) |
| 6 | freshness | `scripts/build_dashboard.py` | producer | `dashboard.md` | `validators/freshness.py` |
| 7 | export | `scripts/synthesis_export.py` | producer | `synthesis_export.jsonl` (in-dossier) | `validators/research_kb_export.py` |
| 8 | stamp | `scripts/backlog_stamp.py` | producer | updated `topic_backlog.yml` | `validators/topic_backlog.py` |

Cross-cutting: `validators/cross_stage.py` validates the *whole project* —
claim_family-taxonomy agreement between plan and ledger, orphan/stale arxiv-id
detection, wiki-link resolution, and (v2.6) it calls
`validators/agent_index_display.py` so a normal `cross_stage` run includes the
display-vs-evidence audit. The committed end-to-end test
[`../tests/test_e2e_build.py`](../tests/test_e2e_build.py) drives stages 2–7 on
a tiny from-scratch fixture and asserts the whole chain is green (`make e2e`).

A unified `research-toolkit` CLI (`scripts/cli.py`,
`[project.scripts]` in `pyproject.toml`) exposes the producers as subcommands
(`assemble`, `render-index`, `build-claim-graph`, `verify-citations`,
`build-dashboard`, `freshness`, `export`, `resume-gather`, `compose-kg`, …) so
the chain can be run by hand without `python scripts/<x>.py` per stage.

## What is agent-authored vs deterministic

| Decision | Who makes it | Why |
|---|---|---|
| Topic scope + claim_family taxonomy | agent (`/research-plan`) | generative; needs judgment |
| Which sources exist + are primary | agent (`/research-gather`) | web discovery + relevance judgment |
| Which span of a source to quote | agent (excerpt selection) | judgment about what substantiates a claim |
| Byte offsets + span hash of that excerpt | producer (`build_excerpt_anchor.build_anchor`) | mechanical; no judgment |
| The four ledgers' structure | producer (`assemble_artifacts`) | mechanical from the sources JSON |
| The claim graph | producer (`build_claim_graph`) | mechanical from the ledgers |
| The agent-index 5-bullet blocks | producer (`render_agent_index`) + `render_config.yml` data | mechanical; per-topic *data* is config, not code |
| A cleaner display sentence for a Mechanism bullet | agent (config `mechanism_display`) | optional; **must still be a verbatim cache substring** (see below) |

The single anchor producer (`scripts/build_excerpt_anchor.py::build_anchor`,
called with `occurrence=1`) is reused by both `assemble_artifacts` and
`render_agent_index` so the offsets + span hash an excerpt gets are
byte-identical no matter which stage anchored it.

## The display-vs-evidence contract

The load-bearing anti-hallucination guarantee: **every Mechanism sentence shown
to a reader (or to an AI consuming the claim graph) is a verbatim raw-byte
substring of the cached source snapshot.** A nicer-reading "display" sentence
never drifts from what the source actually says.

This is enforced twice — at write time and at audit time:

- **Write-time guard** (`scripts/render_agent_index.py::verify_display`): when
  `render_config.yml` supplies a `mechanism_display[bibkey]` override, the
  renderer asserts it is a raw-byte substring of that source's cached text and
  **aborts (non-zero exit)** otherwise. When no override is given, the Mechanism
  bullet shows the anchored excerpt itself, which is a substring by
  construction. The anchored excerpt in `pre_selection_manifest.yml` is never
  changed by a display override — `display != evidence`.
- **Audit-time check** (`validators/agent_index_display.py`): re-checks, for
  every rendered `- **Mechanism:** …` bullet, that its display text is still a
  whitespace-normalized substring of the cached text it is grounded in (resolved
  via the block's inline `- **Evidence:**` bullet → evidence record → cache_id →
  `cache_manifest` `text_path`). A bullet with no resolvable cache linkage is a
  hard error, never silently passed. This catches a family file edited by hand,
  or rendered by an older path that lacked the guard. It is wired into
  `cross_stage` as a hard error independent of `--strict`.

Two enforcement points because the write-time guard only protects what the
committed renderer writes; the audit-time validator protects the artifact at
rest, which a human or an old tool could have mutated.

## Trust model — guarantees and honest holes

The #1 goal of the strict-live pipeline is **machine-checkable trust**, because
the exported claim graph is read downstream by an AI consumer. Being honest
about the boundary between *guaranteed* and *flagged* is part of the contract.

### What strict-live GUARANTEES (mechanically enforced)

- **Byte-exact substring anchoring.** Every `verbatim_match` evidence link
  carries an `excerpt_anchor: {cache_id, text_path_offset, sha256_of_span}`.
  `validators/evidence_ledger.py` (and `scripts/verify_citations.py`) slice the
  cached `text_path` at the declared offset, hash the slice, and assert it
  equals both the recorded `sha256_of_span` and the excerpt bytes. The excerpt
  provably *exists, byte-for-byte,* in the cached source.
- **Content-addressed cache integrity.** `cache_manifest.yml` records each
  blob's `sha256` and `bytes`; `validators/cache_manifest.py` re-hashes the
  on-disk `raw_path` and checks both. The cache is keyed by content hash, so a
  silently-mutated snapshot fails validation.
- **Display == evidence.** Every shown Mechanism sentence is a cache substring
  (the contract above), enforced at write time and audit time.
- **Referential integrity.** `cross_stage` + `freshness` check that every
  `evidence_id` / `cache_id` a ledger references actually resolves, and that the
  claim graph's `evidence_ids` are all present.
- **link_confidence tiering.** `validators/evidence_ledger.py` bounds
  `link_confidence` per `extraction_method` (verbatim_match / user_asserted ≥
  0.85; paraphrase / manual_override ≤ 0.80; llm_inferred ≤ 0.70), so a weak
  extraction cannot claim strong confidence.

### KNOWN HOLES (flagged, NOT guaranteed)

These are real limitations, surfaced as **warnings** for human review. They do
**not** change a stage's pass/fail. Naming them is deliberate — a downstream AI
should not over-trust them.

- **Claim-excerpt relevance is a heuristic WARNING, not a guarantee.** The
  substring check proves an excerpt *exists* in the cache; it does **not** prove
  the excerpt is *on-topic* for the claim it supports. A real but tangential
  span ("quote-mining") passes the audit. `scripts/verify_citations.py` adds a
  keyword-overlap heuristic that flags *possible* off-topic excerpts for review
  (it only runs when a real natural-language claim_text is available, and
  false-positives are expected on short/technical/differently-phrased excerpts).
  It is review-only and never affects the exit code. Semantic relevance is not
  mechanically decidable here.
- **Content-age is a WARNING, not a hard-fail.** `published_online` drives a
  tier-relative content-age warning in `validators/freshness.py` (and a Content
  Age section in the dashboard), distinct from the cache/verify-age that drives
  staleness. Old content is surfaced, not blocked — a foundational 2017 paper is
  legitimately old.
- **The export contract is deferred.** v2.6 hardens the *trust of what is
  produced*, not the *export schema*. The export envelope
  (`synthesis_export.jsonl`, `export_schema_version 2`) wraps each claim_graph
  record verbatim and losslessly, so the trust fields above ride in the payload
  — but promoting grounding-strength / link_confidence / content-age /
  audit-status to first-class *queryable* export fields (with an export-schema
  validator) is its own follow-up milestone (`v26-export-contract-redesign`,
  deferred). Until then a consumer must read those fields out of the wrapped
  payload, not the envelope.

## The export contract for AI consumers

`scripts/synthesis_export.py` reads `claim_graph.jsonl` and wraps each record
in an envelope: `{export_schema_version: 2, record_type, id: "export_<id>",
source_project, exported_at, payload: <verbatim claim_graph record>}`. It
validates with `validators/research_kb_export.py` before writing and refuses to
emit an empty export. The wrap is **lossless** — every payload field (including
the v2.6 trust fields) is preserved, which is what lets the deferred
export-contract milestone promote them later without a re-export. A consumer
ingesting the JSONL gets the full claim graph plus provenance, and should treat
the "known holes" above as review signals, not guarantees.

## Cross-references

- [`getting_started.md`](getting_started.md) — onboarding walkthrough.
- [`troubleshooting.md`](troubleshooting.md) — symptom → cause → fix for common failures.
- [`../references/strict_live_v2.md`](../references/strict_live_v2.md) — the v2/v3 evidence + cache + export schema.
- [`../references/citation_rules.md`](../references/citation_rules.md) — URL canonical forms, bibkey naming, the "no LLM-generated specifics" rule.
- [`ROADMAP_v2_6.md`](ROADMAP_v2_6.md) — the v2.6 milestone (committed pipeline, trust enforcement, autonomy) and what is deferred.

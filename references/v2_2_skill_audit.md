# v2.2 Skill Audit + research-kb Integration Investigation

**Audited:** 2026-05-21 (Linux box, post-reconciliation)
**Toolkit version:** v2.2.1 at commit `1b4f56c`
**Auditor scope:** Mixed strict/pragmatic per `/exploring-options` Q1=C, bodies + dogfood-product cross-check per Q2=B, Medium kb depth + value chain per Q3=B and Big-picture Q1=C
**Revisit when:** v2.3 design cycle is scheduled, or if a new dogfood arc surfaces friction in any pragmatic-tier skill, or if research-kb integration is undertaken.

---

## Executive summary

The 12 toolkit skills are mostly well-designed, with one significant **description-implementation drift** (in `agent-index`) and one **contract drift between two skills** (`dossier-build` is effectively superseded in the v2.2 strict-live pipeline but still described as the upstream-of-agent-index). The `research-kb-export` skill is internally clean (good validate-before-act + envelope-wrapping pattern) but its output is **completely orphaned** — research-kb has no consumer for the inbox jsonl, and the two systems use incompatible ontologies (entities/claims/atoms vs sources/chunks/citations).

The value chain reveals a more important fact than expected: **the toolkit and research-kb are de facto parallel research arcs**, not a producer→storage pipeline. The toolkit feeds prompt-injection paper drafts (v3/v4/v5); research-kb feeds research-agent via MCP. They overlap on subject matter (both touch causal inference, PI literature) but not on data.

---

## Triage table

| Skill | Tier | Color | One-line note |
|---|---|---|---|
| `research-plan` | pragmatic | 🟢 | Clean; run-once; explicit retrofitting edge case |
| `research-gather` | pragmatic | 🟢 | Idempotent (per-bibkey dedup); v2-aware; opt-in PDF cache |
| `agent-index` | **strict** | 🟡 | Description omits v2.2 atomic decomp / Attribute-First / pre_selection_manifest — major drift |
| `dossier-build` | **strict** | 🟡 | Skipped in v2.2 strict-live pipeline; skill body still describes it as agent-index's upstream |
| `dossier-audit` | pragmatic | 🟢 | Single-round semantics; v1.6 dataset extension; "Clean — stop here" termination |
| `citation-audit` | pragmatic | 🟢 | Mechanical; v3-scoped; "not for v2 projects" guard; reuses validators |
| `url-freshness-check` | pragmatic | 🟢 | Explicit disambig vs freshness-audit; generic markdown utility |
| `freshness-audit` | pragmatic | 🟢 | Explicit disambig vs url-freshness-check; v2 strict-live trust audit |
| `dataset-gather` | pragmatic | 🟢 | 8 source categories; parallel to research-gather for datasets |
| `dataset-index` | pragmatic | 🟢 | "Mirrors /agent-index for datasets"; parallel-pipeline pattern |
| `dataset-research` | pragmatic | 🟢 | Composite wrapper; granular alternatives still available (good UX) |
| `research-kb-export` | **strict** | 🟢/🔴 | Producer side clean; consumer side completely orphaned (see Integration sketch) |

**Net:** 10 GREEN, 2 YELLOW, 0 RED on producer side. The RED is an *integration gap*, not a skill defect.

---

## Strict-tier deep dives

### `agent-index` — 🟡 description-implementation drift

**Skill body description** (current frontmatter):
> Synthesize a dossier into a dual-audience indexed folder. Renders entries as 5-bullet blocks (Source/Code/Mechanism/Result/Status), writes an AGENT-INDEX README with scope-boundary callout, lookup recipes, and glossary. Designed for both human readers and future LLM agents grounding reasoning in the literature.

**What it actually produces** (verified across 4 v2.2-dogfood dossiers):
- `agent_index/README.md` + `agent_index/0K_<topic>.md` files — ✅ matches description
- `pre_selection_manifest.yml` — ❌ **not mentioned in description**
- Append-only writes to `evidence_ledger.yml` for synthesis-specific cross-cutting claims (Phase 4b) — ❌ **not mentioned in description**
- Atomic claim_ids per 5-bullet block (Phase 2a-2c Attribute-First flow) — ❌ **not mentioned in description**

The body's Phase 2a–2c (span-select → plan → generate) is the v2.2 phase-B headline feature. A fresh Claude session reading only the `description` frontmatter (which is what Claude actually uses to decide whether to invoke a skill) would NOT understand `agent-index` is the atomic-claim writer.

#### Per-criterion evaluation

| Criterion | Result |
|---|---|
| Orthogonality | ✅ Clean — distinct shape from `dossier-build` (synthesis vs raw notes) |
| Composability | ✅ With caveat — Phase 4b writes back to `evidence_ledger.yml`, which is *logically* owned by `/research-gather`. Documented and validator-checked but a tight coupling worth flagging |
| Idempotency | ⚠️ Partial — Phase 4b's evidence-id check is idempotent; full-skill re-runs probably overwrite README + 5-bullet files (not stated either way) |
| Discoverability | ⚠️ No `paths` trigger — must be explicitly invoked. Defensible (upstream artifacts are diverse) but a fresh Claude session won't auto-suggest it |
| Failure handling | ✅ Local-only (no network); validator at Phase 7 catches structural issues |
| Schema consistency | ✅ Templates anchor `pre_selection_manifest.template.yml`, `5_bullet_entry.template.md`, `agent_index_README.template.md` |
| Use-when description | ❌ **STALE** — omits the v2.2 atomic-decomp behavior |

#### Actionable: GH issue filed (see § Recommended actions, item 1).

---

### `dossier-build` — 🟡 effective supersession in v2.2 strict-live

The pre-flag suspected description-impl drift here too. The actual finding is different and arguably more significant: **none of the 4 v2.2-dogfood dossiers contain a `dossier/` subdirectory**. Verification:

```
~/Claude/research_eval_drift/
  agent_index/  bib_ledger.yml  cache/  cache_manifest.yml
  claim_graph.jsonl  dashboard.md  evidence_ledger.yml
  gather_trace.yml  pre_selection_manifest.yml  research_plan.md
  citation_audit_report.md
  # NO dossier/ directory
```

Compare against the May-8 `research_calibration_methods_dogfood_2026-05-08/` (older v1-era arc):
```
research_calibration_methods_dogfood_2026-05-08/dossier/
  01_parametric_calibration.md  02_nonparametric_calibration.md
  03_calibration_metrics.md     04_calibration_under_shift.md
  _dossier_readme.md
```

The May-8 arc used the documented flow (`bib_ledger.yml` → `dossier-build` → `dossier/*.md` → `agent-index` → `agent_index/`). The four v2.2-dogfood dossiers skip the dossier-build stage entirely — `agent-index` reads directly from `bib_ledger.yml` + `cache/`.

This is **not necessarily wrong design** — atomic decomposition needs cached source text (for span-anchoring), not pre-rendered MD tables. The v1-era MD tables may be redundant when the v2 strict-live evidence pipeline is operating end-to-end.

But the skill bodies don't reflect this:
- `dossier-build` skill body still says "Output consumed by /agent-index" — true only in v1-era pipelines
- `agent-index` skill body still says "Read every `*.md` file in `<dossier_dir>`" — only true when dossier/ exists; in v2.2 dogfood subjects, agent-index must be reading from bib_ledger directly

#### Per-criterion evaluation

| Criterion | Result |
|---|---|
| Orthogonality | ✅ Distinct artifact shape from `agent-index` |
| Composability | ⚠️ Documented downstream (`/agent-index`) appears optional in v2.2 — the contract has implicitly shifted |
| Idempotency | ✅ "should not overwrite manual edits without warning" + Phase 2 user-approval gate |
| Discoverability | ✅ Description is sharp |
| Failure handling | ✅ Local-only; Phase 6 validator |
| Schema consistency | ✅ `dossier_table.template.md` anchors the 7-column schema; non-paper variants explicit |
| Use-when description | ⚠️ Accurate for what the skill does, but doesn't reflect that v2.2 may skip it |

#### Status

**Open design question, not a code bug.** Either:
(a) `dossier-build` is genuinely optional in v2.2 strict-live — skill body should say so explicitly
(b) `dossier-build` is supposed to still run but the v2.2-dogfood dossiers were built with a non-canonical flow — needs investigation
(c) `dossier-build` should be renamed / restructured to serve a different role in v2.2 (e.g., produce a human-readable export of the agent-index for offline review)

#### Actionable: GH issue filed (see § Recommended actions, item 2).

---

### `research-kb-export` — 🟢 producer-side / 🔴 consumer-side

#### Producer side (the skill itself)

Internally well-designed:
- **Validate-before-act**: Phase 1 runs 3 validators before doing anything
- **Validate-after**: Phase 3 validates output; "Do not report success until the export validates"
- **Envelope pattern**: each claim_graph record wrapped with `export_schema_version`, `id`, `source_project`, `exported_at`, `payload`, `record_type` — lossless
- **Strong-ID preservation**: contract explicitly preserves entity / source / claim / evidence / cache IDs
- **Privacy boundary**: "Full cache blobs stay local/private; export records point to paths and hashes rather than embedding raw copyrighted content"
- **`paths` trigger**: `**/claim_graph.jsonl` — Claude can auto-suggest this skill

Sampled wire format (`inbox/research_toolkit/research_eval_drift.jsonl`):
```json
{
  "export_schema_version": 2,
  "exported_at": "2026-05-20",
  "id": "export_ent_dev2026judgereliability",
  "payload": {
    "canonical_name": "Judge Reliability Harness: ...",
    "entity_type": "paper",
    "id": "ent_dev2026judgereliability",
    "record_type": "entity",
    "topic": "eval_drift"
  },
  "record_type": "entity",
  "source_project": "research_eval_drift"
}
```

Clean. Verbatim payload, stable id structure (`export_<original_id>`), `source_project` for traceability.

#### Consumer side (research-kb)

**Completely orphaned.** Verification:
```bash
$ cd ~/Claude/research-kb && grep -rln 'research_toolkit\|inbox/research_toolkit\|export_schema_version' \
  --include='*.py' --include='*.md' --include='*.yml' --exclude-dir=.venv .
(0 matches)
```

research-kb has 15+ ingestion scripts (`ingest_corpus.py`, `ingest_acquisition_batch.py`, `ingest_bayesian_batch.py`, `ingest_arxiv_papers.py`, `ingest_blogs.py`, `ingest_healthcare_reference_cache.py`, etc.) but **none for the toolkit's inbox**. The kb runs its own corpus via:
- S2 weekly cron (Sundays 3 AM, `s2-discovery.timer`)
- PDF extraction via GROBID / Docling / MinerU
- BGE-large-en-v1.5 (1024-dim) embeddings
- PostgreSQL + pgvector + KuzuDB

The toolkit's `inbox/research_toolkit/*.jsonl` files sit there indefinitely. The skill ships data nothing consumes.

#### Inconsistency

There are **two inbox subdirs**, not one:
```
~/Claude/research-kb/inbox/research_toolkit/*.jsonl       (5 files)
~/Claude/research-kb/inbox/research_toolkit_design/*.jsonl (1 file)
```

The skill body says output goes to `~/Claude/research-kb/inbox/research_toolkit/<project_slug>.jsonl`. The second subdir is inconsistent with that — possibly a stale path from an earlier skill version.

#### Actionable: GH issues filed (see § Recommended actions, items 3–4).

---

## Pragmatic-tier health checks

### `research-plan` — 🟢
Run-once scoper; produces `research_plan.md` with 4–8 sub-areas, claim_family taxonomy, known landmarks. Description names the explicit retrofitting skip-case. No friction in BURN_IN evidence. Healthy.

### `research-gather` — 🟢
Idempotent via per-bibkey dedup. Opt-in `--cache-pdfs`. Writes v2 strict-live artifacts (evidence_ledger, cache_manifest, claim_graph) for strict-live projects. The legacy-manifest portability bug (Issue #2) traces here — its earlier versions emitted absolute paths. Current version is presumed-fixed (the 3 newer dogfood dossiers have portable relative paths) but no test guard prevents regression. **Minor potential follow-up:** writer-side guard against absolute paths in cache_manifest. Out of scope for this audit.

### `dossier-audit` — 🟢
Single-round semantics; user re-invokes per round; "Clean — stop here" termination is explicit. v1.6 extension to dataset dossiers documented. Reads project-tier evidence to propagate findings. No friction surfaced.

### `citation-audit` — 🟢
Mechanical; runs `scripts/verify_citations.py`. v3-scoped with "Not for v2 projects" guard. Reuses validators. Verified by 4 dogfood dossiers hitting 100/100/100/100 on this Linux box. Healthy.

### `url-freshness-check` — 🟢
Explicit disambiguation against `/freshness-audit`. Generic markdown utility, not coupled to v2 schema. Works on any folder. Healthy.

### `freshness-audit` — 🟢
The v2 strict-live trust audit. Composes citation-audit's Phase 5 ("As part of /freshness-audit to surface citation health"). Explicit disambig vs url-freshness-check. Healthy.

### `dataset-gather` — 🟢
8-source-category coverage (HuggingFace, Kaggle, academic, aggregators, cloud vendors, domain portals, government open data, classical ML repos). Parallel to research-gather for datasets. v1.6 dogfood evidence confirms it produces useful artifacts.

### `dataset-index` — 🟢
"Mirrors /agent-index for datasets" — explicit parallelism pattern. 5-bullet format (Source/Access/Schema/Size+License/Tasks). Same README+lookup-recipes shape as /agent-index. Composable with dataset-audit (via /dossier-audit's v1.6 extension).

### `dataset-research` — 🟢
Composite wrapper (gather + index). Granular alternatives still documented. Good UX pattern: convenience composite + accessible components. Description sharp ("when you don't need intermediate review").

---

## Integration sketch: toolkit ↔ research-kb

### The actual current state

```
research_toolkit
  ├─ /research-plan ─► research_plan.md
  ├─ /research-gather ─► bib_ledger.yml + cache_manifest.yml + evidence_ledger.yml + claim_graph.jsonl + gather_trace.yml + cache/
  ├─ /agent-index ─► agent_index/README.md + 0K_*.md + pre_selection_manifest.yml
  ├─ /citation-audit ─► citation_audit_report.md
  ├─ /freshness-audit ─► dashboard.md
  └─ /research-kb-export ─► ~/Claude/research-kb/inbox/research_toolkit/*.jsonl
                                  │
                                  ▼
                            🚫 NO CONSUMER 🚫
                                  │
research-kb (parallel arc, doesn't read inbox/research_toolkit)
  ├─ s2-discovery (weekly cron) ─► S2 metadata ─► PDFs
  ├─ MinerU / GROBID / Docling ─► chunks
  ├─ sentence-transformers (BGE-large-en-v1.5, 1024d) ─► embeddings
  ├─ PostgreSQL + pgvector ─► sources, chunks, citations tables
  ├─ KuzuDB ─► concepts (310K), concept_relationships (744K)
  └─ Integration surfaces:
       ├─ Unix-socket daemon (JSON-RPC 2.0) ─┐
       ├─ FastAPI REST                       ├─► research-agent (LangGraph multi-agent)
       └─ MCP server (22 tools) ─────────────┘
```

### The ontology mismatch

| | research_toolkit | research-kb |
|---|---|---|
| Records | entity, claim, atom, evidence, support, span | source, chunk, citation, concept, method, assumption |
| Granularity | one-atom-per-bullet, evidence-grounded | sub-document chunks (~few hundred tokens) embedded |
| Identity | bibkey-based stable IDs, sha256 cache | source_id (postgres), citation_id, concept_id |
| Storage | YAML + JSONL files on disk | PostgreSQL + pgvector + KuzuDB |
| Provenance | extraction_method (verbatim_match / paraphrase / user_asserted), substring-checked | citation graph + bibliographic coupling, PageRank-scored |
| Retrieval | manual lookup recipes + glossary | hybrid (BM25 + vector + citation authority) |

These ontologies don't map 1:1. A toolkit "atom" is a single verbatim claim with substring grounding; a kb "chunk" is a token-window embedding for retrieval. They're complementary representations of the same papers, optimized for different consumers.

### Five possible integration paths

1. **kb-side adapter** (`research-kb/scripts/ingest_toolkit_inbox.py`) — translates toolkit envelope-wrapped records into kb-native source / chunk / citation records. Heavy: requires mapping decisions for every record_type. **Effort: M-L**.

2. **toolkit-side conformance** — modify `research-kb-export` to emit kb-native records directly. Sacrifices toolkit's evidence-grounding semantics (atoms become chunks). **Effort: M**. *Loses information.*

3. **Two-channel coexistence** — add new kb tables (`dossier_claims`, `dossier_supports`) alongside `sources`/`chunks`/`citations`. The kb's hybrid search learns to surface both. Most faithful to the data models. **Effort: L**.

4. **No-integration** — accept the current de facto state. Toolkit dossiers are independent artifacts feeding paper drafts; kb is independent corpus feeding research-agent. Move `research-kb-export` to a `legacy/` directory and document the de facto separation. **Effort: XS**. *Most honest.*

5. **Retrieval-result convergence** — toolkit's dossiers become a *corpus* that the kb indexes alongside its other 36 domains. The kb's `research_kb_pdf` package would learn to consume markdown synthesis (the `agent_index/*.md` files) instead of PDFs. This makes toolkit-curated synthesis surfaceable via `research_kb search query "..."`. **Effort: M-L** but **highest information yield** — the toolkit's substring-grounded synthesis becomes retrievable.

### Recommendation

**Path 5 (retrieval-result convergence) is the most valuable integration if undertaken**, but path 4 (no-integration + explicit documentation) is the right *immediate* move. The current orphan-inbox state is documentation debt; resolving it doesn't require building anything.

Path 5 deserves its own design pass. It's not a v2.3 candidate per se — it's a research-kb feature (consuming a new corpus type). Better routed as an issue on the kb repo than the toolkit repo.

---

## Value chain — downstream investigation (per Big-picture Q1)

### Two parallel arcs

```
ARC 1 — Toolkit → Paper deliverables
  research_toolkit (12 skills)
        │
        ▼
  research_pi_attacks_defenses (23 sources, plan + bib_ledger)
  research_pi_benchmarks         (10 sources)
  research_pi_datasets            (no plan yet)
  research_encoder_lora          (11 sources)
  research_calibration_methods   (May-21, 6 sub-areas, 18 sources)
        │
        ▼
  prompt-injection-v3 / v4 / v5 (paper drafts; v4/v5 calibration chapter feeds from research_calibration_methods)
        │
        ▼
  prompt_injection_detector (V2 Methodology PoC)
  prompt_injection_classifier_showcase (DeBERTa-LoRA + Baselines)
  prompt-injection-portfolio / -submission / -clean / -sdd (presentation forms)

ARC 2 — research-kb → research-agent
  research-kb (PostgreSQL + pgvector + KuzuDB, S2-driven, 36 domains)
        │
        ├─ Unix socket daemon (JSON-RPC 2.0)
        ├─ REST API (FastAPI)
        └─ MCP server (22 tools)
              │
              ▼
        research-agent (LangGraph multi-agent: Query Planner → Literature Search ∥ Concept Explorer ∥ Citation Analyzer → analysis_join → Assumption Auditor → Connection Explorer → Synthesis Writer)
              │
              ▼
        Structured research reports
```

### What this reveals

1. **The toolkit is in the paper-deliverable arc, not the retrieval arc.** The dossiers it produces are *inputs to paper writing*, not entries in a queryable knowledge base.

2. **research-agent's `Synthesis Writer` and the toolkit's `/agent-index` do related work.** Both synthesize from primary sources. They differ in retrieval substrate (research-agent pulls from kb's hybrid search; agent-index pulls from `bib_ledger` + cached source text). Worth noting for future convergence design.

3. **The PI dossier subset is dogfood at scale.** All 4 named PI dossiers (`research_pi_attacks_defenses`, `pi_benchmarks`, `pi_datasets`, `encoder_lora`) explicitly say "A retrospective fit-test of `research_toolkit` on [some axis of] the `prompt_injection_detector` PoC". They're toolkit-validation runs at production scale — bigger than the v2.2-dogfood arc.

4. **Cross-arc subject overlap is real.** research-kb's primary domain is currently `causal_inference`; the toolkit has `research_causal_inference_ml`. Same subject, different representations. A future integration could either pick one source of truth or formally distinguish "synthesis layer" (toolkit) from "retrieval layer" (kb).

### Nodes with ambiguous contracts

| Node | Ambiguity |
|---|---|
| `/dossier-build` → `/agent-index` | dossier MD files exist in v1-era subjects, absent in v2.2-dogfood — contract has shifted |
| `/agent-index` Phase 4b | writes back to upstream `evidence_ledger.yml` — cross-skill artifact ownership |
| `/research-kb-export` → kb | declared "consumed by research-kb ingestion workflows" but no such workflow exists |
| kb-discovered papers ↔ toolkit-curated papers | overlap on subject matter but no cross-reference mechanism; possible duplication |

---

## Bigger picture — for future reexamination

(Peripheral-vision observations captured during the audit. Each is flagged-but-undeveloped; future sessions can pick these up without re-deriving.)

1. **research-kb's hybrid-search architecture is more mature than the toolkit's** — BM25 + vector + PageRank + (optional) KuzuDB graph fusion; context-aware weight profiles; 22-tool MCP server. The toolkit doesn't have a retrieval surface; its consumer is the paper-writing human. Worth thinking about whether the toolkit should ever expose a retrieval surface, or if that role is permanently the kb's.

2. **research-agent's pipeline contains skill-like nodes** (Query Planner, Literature Search, Concept Explorer, Citation Analyzer, Synthesis Writer) that overlap conceptually with toolkit skills (research-plan, research-gather, agent-index). They're separate implementations of similar problems — one synchronous + LLM-driven (research-agent), one async + human-in-loop (toolkit). Worth surveying whether either system's primitives should converge.

3. **The PI ecosystem has 10 themed dirs on this Linux box.** Beyond the 5 in-flight dossiers, there are 5 paper-draft / submission / showcase / blueprint repos. They likely diverge in maturity and possibly in source-of-truth claims about the detector PoC. Worth a separate inventory + status review.

4. **research-kb has 3 codex audit reports** (`codex-systematic-audit.md` Feb '26, `codex-systematic-audit-2026-03-25.md`, `codex-repo-audit-2026-03-30.md`) — a precedent for the audit-doc pattern this very document uses. Worth reading the kb's own audits for structural ideas + meta-pattern reuse.

5. **research-kb's `data/dlq/` and root `.dlq/extraction/` are both dead-letter queues** — suggests real ingest happens and sometimes fails. Worth checking their depth as an indicator of kb operational health if integration becomes serious.

6. **research-kb has multiple acquisition strategies** (`ingest_bayesian_batch.py`, `ingest_rl_batch.py`, `ingest_acquisition_batch.py`, `ingest_fp_batch.py`) — actively experimenting with corpus curation. The toolkit's much-simpler curation (`/research-plan` + `/research-gather`) is a different paradigm but the underlying question — "which papers go in?" — is shared.

7. **The toolkit's PI dossiers and the kb's causal_inference corpus may share papers** — Pearl, Imbens, Rubin, etc. Could be a useful early integration probe: how many toolkit-discovered papers are also in the kb's corpus, and vice versa?

8. **The two-machine workflow has implications for both systems.** research-kb has a systemd timer assuming a single machine; research-toolkit dossiers can move between machines via tarball sync. If integration happens, multi-machine coordination becomes a real question.

---

## Recommended actions

All filed on `research_toolkit` GH repo with label `tracked`. Cross-reference with `gh issue list --label tracked`.

| Issue | Action | Rationale | Effort |
|---|---|---|---|
| [#3](https://github.com/brandon-behring/research_toolkit/issues/3) | Update `agent-index` description to mention v2.2 atomic decomposition + Attribute-First + `pre_selection_manifest.yml` | Fresh Claude sessions won't know to use the v2.2 features from the description alone | XS (5 min) |
| [#4](https://github.com/brandon-behring/research_toolkit/issues/4) | Document or resolve the `dossier-build` ↔ `agent-index` contract drift in v2.2 strict-live | Skill bodies describe a flow the v2.2-dogfood dossiers don't follow | S (~1h) |
| [#5](https://github.com/brandon-behring/research_toolkit/issues/5) | Document research-kb consumer state in `research-kb-export` skill (either: "consumer not yet implemented; output is currently archival" or build the consumer) | The skill currently produces orphan files; users invoking it should know | XS (15 min) — or M-L if building the consumer |
| [#7](https://github.com/brandon-behring/research_toolkit/issues/7) | Fix inbox subdir inconsistency — `inbox/research_toolkit_design/` should either be deleted or its existence documented | One stale duplicate file across two subdirs is confusing | XS (5 min) |
| [#8](https://github.com/brandon-behring/research_toolkit/issues/8) | Consider adding `paths` triggers to `agent-index` and `dossier-build` (e.g., agent-index on `bib_ledger.yml` + absence of `agent_index/README.md`) | Improves discoverability without explicit invocation | XS for agent-index alone; depends on #4 resolution |

**Not in scope for this audit (deferred):**
- Building the kb-side consumer or kb-side adapter (Path 1, 3, or 5 above) — separate design pass
- Documenting the de facto no-integration state (Path 4) — would be a kb-repo doc, not toolkit
- Retrieval-surface design for the toolkit — major v2.3+ design question
- PI ecosystem inventory — separate audit
- research-agent ↔ toolkit primitive convergence — strategic, not tactical

---

## Audit metadata

- **Total time invested:** ~2.5 hours (Pass 1: 10min, Pass 2: 40min, Pass 3: 35min, Pass 3b: 30min, Pass 4: 35min)
- **Skill bodies read:** 12/12 (full body for the 3 strict-tier; first ~30 lines for the 9 pragmatic-tier)
- **Dogfood artifacts cross-checked:** 4 v2.2-dogfood dossiers + 1 May-8 dogfood arc (for comparison) + 6 inbox jsonl files
- **External repos surveyed:** research-kb (top-level + docs/INTEGRATION.md + CLAUDE.md + scripts/ + services/), research-agent (top-level + README first 60 lines)
- **PI ecosystem peripheral peek:** 10 PI-themed dirs identified, type-signature noted, not deep-read
- **GH issues filed:** see § Recommended actions; expect 5 issues with label `tracked`

**Triggers to revisit this document:**
- A v2.3 design cycle is scheduled
- A new dogfood arc surfaces friction in any pragmatic-tier skill
- research-kb integration is undertaken (especially Path 5 retrieval convergence)
- One of the 5 in-flight PI dossiers completes its `/agent-index` pass (new contract evidence)
- The PI ecosystem (10 dirs) is restructured / consolidated

---

## Remediation log (2026-05-21, post-audit Linux session)

All 5 GH issues remediated in a single session immediately following the audit. Toolkit-side fixes; kb-side consumer build deferred (per audit "Not in scope").

| Issue | Resolution | Files touched |
|---|---|---|
| [#3](https://github.com/brandon-behring/research_toolkit/issues/3) | Extended `agent-index` description to mention v2.2 atomic decomposition, Attribute-First, `pre_selection_manifest.yml`, and fallback for v1-era projects. | `.claude/skills/agent-index.md` (frontmatter `description`) |
| [#4](https://github.com/brandon-behring/research_toolkit/issues/4) | Adopted resolution path (a): dossier-build is explicitly **optional in v2.2+ strict-live**. Updated both skill bodies — dossier-build's description + "When to use" + Upstream/Downstream; agent-index's "Usage" + "When to use" + Upstream/Downstream + Phase 2 wording (now branches on v2.2+ vs legacy). | `.claude/skills/dossier-build.md`, `.claude/skills/agent-index.md` |
| [#5](https://github.com/brandon-behring/research_toolkit/issues/5) | Added `## Status` section to `research-kb-export` skill body documenting that no kb consumer exists, exports are archival, and the ontology gap is the root cause. Corrected misleading "Consumed by:" line in `## Output / handoff`. | `.claude/skills/research-kb-export.md` |
| [#7](https://github.com/brandon-behring/research_toolkit/issues/7) | Investigation revealed the two files were NOT duplicates but two snapshots at different claim_graph evolution states (75 records vs 157 records). Replaced canonical (`inbox/research_toolkit/research_toolkit_design.jsonl`) with the newer richer variant; deleted the misplaced `inbox/research_toolkit_design/` subdir. Older snapshot preserved at `/tmp/research_toolkit_design.jsonl.20260520.bak` for the session. | `~/Claude/research-kb/inbox/research_toolkit/research_toolkit_design.jsonl` (replaced), `~/Claude/research-kb/inbox/research_toolkit_design/` (deleted) |
| [#8](https://github.com/brandon-behring/research_toolkit/issues/8) | Added `paths: '**/bib_ledger.yml'` trigger to `agent-index`. dossier-build deliberately left without a trigger (consistent with its v2.2+ optional positioning — explicit invocation only). | `.claude/skills/agent-index.md` (frontmatter `paths`) |

**What was NOT done** (deferred to future sessions, consistent with audit "Not in scope"):
- Building the kb-side consumer for `inbox/research_toolkit/*.jsonl` — requires kb-repo work, separate design pass
- Updating the 4 v2.2-dogfood dossiers' artifact layouts (they already pass the v2.2 contract; no remediation needed)
- Re-exporting fresh JSONL from current claim_graph state for any project (the inbox files remain orphan; re-exporting is moot until a consumer exists)
- Retroactive description updates for the 9 pragmatic-tier skills (audit found no issues there)

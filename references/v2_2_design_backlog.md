# v2.2 design backlog — deeper anti-hallucination grounding

Distilled 2026-05-19 from the `~/Claude/research_toolkit_design/` dogfood project
(Phase 8). Each backlog item is byte-anchored to a primary source via the
project's `evidence_ledger.yml` entries — see the matching `evidence_id` for
the cached source + verified excerpt.

**Provenance**: each item below cites a v3 strict-live evidence record
(`extraction_method: verbatim_match`, substring + SHA-256 validated by
`scripts/verify_citations.py`). The project's `citation_audit_report.md` is
6/6 strong (100% verbatim-anchored). Confidence in the underlying citations
is mechanical, not editorial.

**Recommended Tier-1 (ship in v2.2.0 next session)**: Items 1, 3, 5. The other
three are Tier-2 (defer to v2.2.1 or later) unless friction surfaces them
sooner.

---

## A1. atomic_grounding

### Item 1: Atomic-claim decomposition in `/agent-index` (Tier-1)

- **Evidence**: `ev_factscore_atomic_methodology` (Min et al. 2023, EMNLP) +
  `ev_vista_dialogue_history_verification` (Lewis et al. 2025) in
  `research_toolkit_design/evidence_ledger.yml`.
- **v2.1 gap**: bullet-level `claim_id` hides mixed support. FActScore's
  contribution is that "generations often contain a mixture of supported and
  unsupported pieces of information" — and bullet-level scoring obscures the
  unsupported fragments inside a partially-supported bullet. VISTA's 2025
  follow-up "decomposes each turn into atomic claims, verifies them against
  trusted sources and dialogue history" and substantially improves over
  FActScore + LLM-as-Judge baselines.
- **Proposed mechanism**: `/agent-index` Phase 2 emits 2-5 atomic `claim_id`s
  per 5-bullet block, each with its own evidence_ids. `build_claim_graph.py`
  produces one claim record per atom, not per bullet. Validators reject any
  atom without supporting evidence_ids.
- **Effort**: M (changes `/agent-index` skill body, schema additions to
  claim_graph, fixture migration).
- **Priority**: Tier-1.

### Item 2: VISTA-style dialogue-history corroboration (Tier-2)

- **Evidence**: `ev_vista_dialogue_history_verification` (Lewis et al. 2025).
- **v2.1 gap**: v2.1 verifies each evidence span against ONE cache blob.
  Doesn't cross-check whether the same claim is corroborated elsewhere in
  the dossier (prior `/research-gather` runs, sibling agent_index entries,
  cached blobs from other sources).
- **Proposed mechanism**: new `scripts/cross_corroborate.py` that, for each
  claim_id, finds other evidence records supporting it and computes a
  cross-source corroboration score. Surface in dashboard's Claim Health
  section as "X% of atomic claims have ≥2 independent sources."
- **Effort**: M-L.
- **Priority**: Tier-2.
- **Demonstration status (2026-05-20, iter 5)**: the *aggregation half* of
  this item is already working in `scripts/build_claim_graph.py`.
  Demonstrated end-to-end in `~/Claude/research_toolkit_design/` by
  introducing three cross-source synthesis claims — each bound to 3
  evidence records spanning 3 different primary sources, across three
  distinct sub-areas:
  - `claim_synthesis_atomic_grounding_pattern`: FActScore + RAGTruth + VISTA
  - `claim_synthesis_sample_based_pattern`: Semantic Entropy + SelfCheckGPT + Lookback Lens
  - `claim_synthesis_multi_agent_pattern`: Tool-MAD + MAD-Fact + GSAR

  All 24 verbatim_match substring checks pass; the builder correctly merged
  3 evidence_ids and 3 entity_ids per synthesis claim, with highest-quality
  + longest-excerpt tiebreak for claim text. What Item 2 still needs is the
  *scoring* half (corroboration metric + dashboard surfacing). Demotes the
  v2.2 implementation cost from M-L to S (the hard part — multi-evidence
  binding — is shipped).

---

## A2. generation_conditioning

### Item 3: Attribute-First refactor of `/agent-index` (Tier-1)

- **Evidence**: `ev_attribute_first_pre_selection` (Slobodkin et al. 2024,
  ACL).
- **v2.1 gap**: v2.1 (and v2.0) is *post-hoc* attribution — `/agent-index`
  generates 5-bullet prose, THEN evidence_ledger binds claims back to
  sources. Slobodkin et al. 2024 explicitly identifies this as a
  hallucination vector: citations get chosen to *match* already-written
  text rather than driving the generation. Their proposal: "Attribute First,
  then Generate: Locally-attributable Grounded Text Generation" —
  span-selection BEFORE generation, generation CONDITIONED ON selected
  spans only.
- **Proposed mechanism**: rework `/agent-index` Phase 2 into three sub-steps:
  (2a) span-selection — pick cache_blob excerpts per claim_family before
  writing prose;
  (2b) planning — declare which span supports which atomic claim
  (`pre_selection_manifest.yml`);
  (2c) generation — emit bullets conditioned ONLY on selected spans (system
  prompt: "you may use ONLY text from the spans below").
  Validator: every bullet's evidence_ids must appear in
  `pre_selection_manifest.yml` from step 2b. Post-hoc rationalization
  becomes structurally impossible.
- **Effort**: L (major `/agent-index` rewrite + new pre-selection artifact +
  validator).
- **Priority**: Tier-1 — this is the structural anti-hallucination move,
  complementary to span-anchored citation (post-hoc check) by attacking
  the problem at the generation step.

---

## A3. sample_based_detection

### Item 4: Semantic-entropy sampling in `/citation-audit` (Tier-2)

- **Evidence**: `ev_semantic_entropy_meaning_clusters` (Farquhar et al. 2024,
  Nature) + `ev_selfcheck_sampling_consistency` (Manakul et al. 2023, EMNLP).
- **v2.1 gap**: v2.1's `/citation-audit` is mechanical (substring check
  against cache). For `paraphrase` and `llm_inferred` evidence entries it
  cannot verify the link. Farquhar et al. 2024 shows "Semantic entropy
  detects confabulations in free-form text generation across a range of
  language models and domains, without previous domain knowledge" by
  clustering m sampled answers by NLI bidirectional entailment and computing
  entropy over meaning-clusters. SelfCheckGPT (Manakul 2023) demonstrates
  a parallel zero-resource path: "sampled responses are likely to be similar
  and contain consistent facts" — diverging samples flag hallucinations,
  without any external database. SNNE (Nguyen 2025) extends semantic
  entropy with LogSumExp smoothing for robustness.
- **Proposed mechanism**: new sub-script
  `scripts/semantic_entropy_audit.py` that, for each `paraphrase` or
  `llm_inferred` evidence, samples k=5 alternate paraphrases of the claim
  text from an LLM, clusters them by NLI, computes entropy. High entropy →
  surfaces in citation_audit_report.md as "weakly grounded; high
  confabulation risk." Confidence cap downgrade for high-entropy claims.
- **Effort**: L (requires LLM API access + NLI model; sampling is expensive).
- **Priority**: Tier-2.

---

## A4. graded_support

### Item 5: Self-RAG-style adaptive retrieval in `/research-gather` (Tier-1)

- **Evidence**: `ev_selfrag_reflection_tokens` (Asai et al. 2023, ICLR).
- **v2.1 gap**: `/research-gather` Phase 2 issues WebSearches according to
  sub-area templates but doesn't adapt the retrieval depth based on what's
  found. Self-RAG fine-tunes an LLM to emit `IsRel` / `IsSup` / `IsUse`
  tokens "evaluated before committing to an answer," dynamically deciding
  when external information is needed and when retrieved content is
  sufficient. Asai et al. 2023: "Despite their remarkable capabilities,
  large language models (LLMs) often produce responses containing factual
  inaccuracies due to their sole reliance on the parametric knowledge they
  encapsulate" — adaptive retrieval addresses this.
- **Proposed mechanism**: `/research-gather` Phase 2 explicit reflection
  loop. After each WebSearch + WebFetch, emit a structured `IsRel` /
  `IsSup` / `IsUse` block to a `gather_trace.yml` (a new artifact). When
  `IsSup` is "partial" or "none" for a sub-area, automatically expand
  search queries OR escalate to manual review. `IsUse` < 3 → drop the
  source. Auditor reads gather_trace.yml in a follow-on `/freshness-audit`
  step.
- **Effort**: M (skill body rewrite + new gather_trace template +
  validator).
- **Priority**: Tier-1 — addresses the discovery rigor gap surfaced in
  Phase 4 BURN_IN as a deferred item.

---

### Item 5b: RAGTruth-style word-level hallucination corpus for v2.2 eval harness (Tier-2)

- **Evidence**: `ev_ragtruth_word_level_corpus` (Niu et al. 2024, ACL).
- **v2.1 gap**: v2.1 has no eval harness against a labeled corpus. We can
  hand-curate evidence_ledger entries, but there's no way to measure "v2.1
  catches X% of known hallucinations." Niu et al. 2024: "Retrieval-augmented
  generation (RAG) has become a main technique for alleviating
  hallucinations in large language models (LLMs). Despite the integration of
  RAG, LLMs may still present unsupported or contradictory claims" — they
  ship a 18,000-response corpus with word-level + case-level annotations
  and 4-class hallucination taxonomy.
- **Proposed mechanism**: new `tests/fixtures/ragtruth_subset/` fixture
  with ~50 hand-selected RAGTruth examples wrapped as v3 evidence_ledger
  entries. A new test `test_v2_catches_known_hallucinations.py` runs
  /citation-audit against the fixture and asserts catch rate ≥ a target
  threshold (e.g., 80%). Becomes a regression baseline for v2.2+ changes.
- **Effort**: M (fixture construction + test scaffolding).
- **Priority**: Tier-2 (defer until after Tier-1 v2.2 items ship).

### Item 5c: Hierarchical verification per Retromorphic Testing (Tier-2, 2026)

- **Evidence**: `ev_retromorphic_hierarchical` (Yu et al. 2026, arXiv
  2603.27752 — fresh 2026 work).
- **v2.1 gap**: /dossier-audit's CoVE-factored verification (v2.1 Tier-1
  #3) generates 2-3 questions per finding and answers them independently.
  Yu et al. 2026 propose **hierarchical** verification: detect at coarse
  granularity first (whole-passage), then drill into suspect spans. Yu et
  al.: "Large language models (LLMs) continue to hallucinate in
  retrieval-augmented generation (RAG), producing claims that are
  unsupported by or conflict with the retrieved context. Detecting such
  errors rem[ains a challenge]" — hierarchical verification is cheaper
  per-passage and surfaces problem regions faster than per-claim
  verification across an entire dossier.
- **Proposed mechanism**: extend /dossier-audit with a Phase 2.5 coarse
  pre-check that scores each dossier file's overall reliability before
  spawning per-claim verification sub-agents. Files scored "high
  confidence" skip the expensive per-claim factored verification; "low
  confidence" files get the full treatment.
- **Effort**: M.
- **Priority**: Tier-2 (refines existing v2.1 mechanism rather than
  adding a new one).

### Item 4b: Lookback Lens attention-divergence detection (Tier-3, exploratory)

- **Evidence**: `ev_lookback_lens_attention` (Chuang et al. 2024, EMNLP —
  arXiv 2407.07071).
- **v2.1 gap**: v2.1 has no signal from the model's own attention. All
  v2.1 anti-hallucination is downstream of generation (substring check,
  CoVE, source_quality). Chuang et al. 2024: "When asked to summarize
  articles or answer questions given a passage, large language models
  (LLMs) can hallucinate details and respond with unsubstantiated answers
  that are inaccurate" — they use the ratio of attention weights on
  context vs newly-generated tokens as a per-head signal, achieve 9.6%
  hallucination reduction on XSum without retraining the LM.
- **Proposed mechanism**: too invasive for v2.2. Documented as a Tier-3
  research direction — would require access to per-token attention maps
  from the generating model (Claude API doesn't expose these). Defer
  until either (a) Claude exposes attention via the API, or (b) v3.0
  pivots to using a local model where attention is accessible.
- **Effort**: L (depends on API access).
- **Priority**: Tier-3 (exploratory, low near-term impact).

### Item 5d: Tool-MAD adaptive-retrieval multi-agent debate (Tier-2)

- **Evidence**: `ev_toolmad_multi_agent_debate` (Jeong et al. 2026 —
  arXiv 2601.04742, fresh).
- **v2.1 gap**: v2.1's CoVE-factored verification (Tier-1 #3) uses ONE
  verifier sub-agent per question, in a decoupled context. Tool-MAD
  proposes COLLABORATIVE multi-agent debate where "each agent [is
  assigned] a distinct external tool, such as a search API or RAG module"
  — diverse tool access surfaces evidence one agent would miss. Jeong et
  al. 2026: "Large Language Models (LLMs) suffer from hallucinations and
  factual inaccuracies, especially in complex reasoning and fact
  verification tasks. Multi-Agent Debate (MAD) systems aim to improve
  answer accuracy by enabling multiple LLM agents to engage in dialogue."
- **Proposed mechanism**: extend `/dossier-audit` Phase 3 with a second
  spawn pattern: instead of (or in addition to) CoVE-factored
  verification, spawn N=2-3 agents each with a DIFFERENT search tool
  (one with WebFetch only, one with arXiv API, one with Semantic
  Scholar API), have them debate the finding. Surfacing disagreement
  becomes a FLAG signal. Compounds with v2.1 CoVE-factored.
- **Effort**: M-L (requires tool-diverse setup; current /dossier-audit
  has only WebSearch + WebFetch).
- **Priority**: Tier-2 (refinement, not core).

## A5. judge_calibration

### Item 6b: MAD-Fact long-form factuality eval via multi-agent debate (Tier-2)

- **Evidence**: `ev_madfact_longform_evaluation` (Ning et al. 2025 —
  arXiv 2510.22967).
- **v2.1 gap**: v2.1's /citation-audit produces single-judge mechanical
  metrics (substring pass rate). No way to evaluate the JUDGE itself, or
  combine multiple judges for robustness. Ning et al. 2025: "The
  widespread adoption of Large Language Models (LLMs) raises critical
  concerns about the factual accuracy of their outputs, especially in
  high-risk domains" — they propose multi-agent debate with role-
  separation (Clerk / Jury / Judge) to improve long-form factuality
  evaluation. MAD-Fact "consistently outperforms strong baselines on
  multiple long-form factuality benchmarks."
- **Proposed mechanism**: when /citation-audit reports a project's
  Claim Health, optionally trigger a MAD-Fact-style multi-judge
  evaluation on a sampled subset of claims. Three sub-agents (Clerk
  summarizes evidence, Jury votes per-claim, Judge breaks ties) produce
  a calibrated faithfulness score that complements the mechanical
  substring metric. Surface as a "calibrated_claim_health" score in
  dashboard.md.
- **Effort**: L (multi-agent orchestration + sampling protocol).
- **Priority**: Tier-2 (refinement, compounds with Item 6 fusion).

### Item 6: Faithfulness-metric fusion in dashboard Claim Health (Tier-2)

- **Evidence**: `ev_faithfulness_metric_fusion` (Malin et al. 2025, arXiv
  2512.05700).
- **v2.1 gap**: v2.1's Claim Health metric is single-dimensional (% verbatim-
  anchored). Doesn't combine multiple faithfulness signals. Malin et al.
  2025: "We present a methodology for improving the accuracy of
  faithfulness evaluation in Large Language Models (LLMs). The proposed
  methodology is based on the combination of elementary faithfulness
  metrics" — multi-metric fusion outperforms any single metric for
  faithfulness evaluation.
- **Proposed mechanism**: extend `build_dashboard.py` Claim Health section
  with a "fusion score" combining:
  - substring-anchor pass rate (current)
  - source_quality distribution (current confidence aggregation)
  - cross-source corroboration count (from Item 2 if shipped)
  - semantic-entropy uncertainty (from Item 4 if shipped)
  Each contributes weighted to a `claim_health_fusion: 0..1` score per
  claim and per project. Threshold for "publish-ready" tag.
- **Effort**: S-M (depends on which other items ship first; otherwise
  trivial).
- **Priority**: Tier-2 (depends on 2 + 4).

---

### Item 5e: GSAR-style typed grounding for multi-agent reports (Tier-2)

- **Evidence**: `ev_gsar_typed_grounding` (Kamelhar et al. 2026, fresh —
  arXiv 2604.23366).
- **v2.1 gap**: v2.1's `evidence_role` enum is untyped at the *claim
  category* level — a `supports` link doesn't differentiate "this is a
  causal claim" vs "this is a definitional claim" vs "this is a
  quantitative claim." Kamelhar et al. 2026: "Autonomous multi-agent LLM
  systems are increasingly deployed to investigate operational incidents
  and produce structured diagnostic reports. Their trustworthiness hinges
  on whether each claim is groun[ded]" — they introduce TYPED grounding
  where each claim is tagged with its semantic type and grounded against
  type-appropriate evidence.
- **Proposed mechanism**: extend `claim_type` enum (already
  fact/comparison/trend/risk/recommendation/contradiction/open_question/
  user_judgment) with finer-grained types for the v3 substring check.
  Different `claim_type` values get different `evidence_role` requirements
  — e.g., `claim_type: quantitative` MUST have a `verbatim_match` anchor;
  `claim_type: definitional` allows `paraphrase`.
- **Effort**: M (schema additions + validator logic).
- **Priority**: Tier-2 (refinement of existing typing).

### Item 6c: Process-reward agents for grounded reasoning (Tier-3)

- **Evidence**: `ev_process_reward_agents` (Sohn et al. 2026, fresh —
  arXiv 2604.09482).
- **v2.1 gap**: v2.1 evaluates evidence per-claim (post-generation). PRMs
  evaluate reasoning STEPS, awarding per-step credit for grounded
  inference. Sohn et al. 2026: "Reasoning in knowledge-intensive domains
  remains challenging as intermediate steps are often not locally
  verifiable: unlike math or code, evaluating step correctness may
  require synthesizing clues acr[oss many sources]."
- **Proposed mechanism**: too invasive for v2.2. Would require training
  a process-reward model on the toolkit's own outputs (cost: substantial
  labeled-data + RL training). Document as v3.0 research direction.
- **Effort**: L+ (training infrastructure).
- **Priority**: Tier-3 (research direction, not v2.2 ship target).

### Item 6d: Probabilistic certainty + consistency for /citation-audit (Tier-2)

- **Evidence**: `ev_factcheck_probabilistic_certainty` (Wang et al. 2026
  — arXiv 2601.02574).
- **v2.1 gap**: /citation-audit reports binary substring-check pass/fail.
  Wang et al. 2026 propose combining PROBABILISTIC certainty (the model's
  reported confidence in its own claim) with CONSISTENCY (across multiple
  samples) as a fact-checking signal. Wang et al.: "Large language models
  (LLMs) are increasingly used in applications requiring factual
  accuracy, yet their outputs often contain hallucinated responses. While
  fact-checking can mitigate these errors, ex[isting methods don't
  combine certainty + consistency]."
- **Proposed mechanism**: when /citation-audit encounters a `paraphrase`
  evidence link (no substring check applicable), sample k=3 variants of
  the claim text from the model with its self-reported certainty. High
  certainty + high consistency → confidence boost; low certainty OR low
  consistency → confidence cap to 0.5. Annotates per-link
  `probabilistic_factcheck_score: 0..1` in evidence_ledger.
- **Effort**: M (samples + certainty prompting + integration with
  /citation-audit).
- **Priority**: Tier-2 (complements Item 4 semantic entropy from a
  different angle).

## Tier-1 next-session implementation plan

Top 3 items for v2.2.0 (per user 2026-05-19 commitment "build the backlog
now, implement Tier-1 of v2.2 next"):

1. **Item 3 (Attribute-First refactor)** — biggest structural win, L effort.
   Closes the post-hoc rationalization gap that v2.1's substring check can
   only catch retroactively.
2. **Item 1 (Atomic-claim decomposition)** — M effort, raises evidence
   granularity. Compounds with Item 3 (each atomic claim gets pre-selected
   spans).
3. **Item 5 (Self-RAG adaptive retrieval)** — M effort, addresses the
   discovery rigor gap deferred from Phase 4 BURN_IN.

Estimated total: 3-5 days. After v2.2.0 ships, the remaining Tier-2 items
(2, 4, 6) get re-prioritized based on whatever friction the v2.2.0 dogfood
surfaces.

## v2.2 schema notes

The Tier-1 items above imply schema additions:
- `pre_selection_manifest.yml` (Item 3) — a new v2.2 artifact per
  `/agent-index` run.
- Atomic `claim_id` granularity (Item 1) — `claim_graph.jsonl` claim records
  may need an `atomic: true` flag or a parent/child relationship to support
  rolling up atomic claims into bullet-level views.
- `gather_trace.yml` (Item 5) — a new v2.2 artifact per `/research-gather`
  run.

If these ship, `schema_version: 3 → 4` is justified. Otherwise additive
fields can stay at v3.

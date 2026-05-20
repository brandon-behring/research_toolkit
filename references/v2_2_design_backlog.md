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
  Nature).
- **v2.1 gap**: v2.1's `/citation-audit` is mechanical (substring check
  against cache). For `paraphrase` and `llm_inferred` evidence entries it
  cannot verify the link. Farquhar et al. 2024 shows "Semantic entropy
  detects confabulations in free-form text generation across a range of
  language models and domains, without previous domain knowledge" by
  clustering m sampled answers by NLI bidirectional entailment and computing
  entropy over meaning-clusters.
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

## A5. judge_calibration

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

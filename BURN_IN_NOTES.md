# Burn-In Notes — research_toolkit dogfood log

This file is the load-bearing artifact of Phases 3.5 + 5. Every skill-prompt tweak, validator miss, template gap, or pipeline friction surfaced during dogfood runs gets recorded here with before/after context. If this file is empty after a real dogfood pass, that's suspicious — re-examine.

**Status legend:**
- `surfaced` — friction observed; not yet acted on
- `applied` — tweak applied to skill / template / reference
- `deferred` — friction acknowledged but not material enough to fix in this version
- `wontfix` — out of v1.x scope; goes in next-design-cycle backlog

---

## v2.2.1: Playwright escalation in cache_source.py — shipped 2026-05-20

**Theme**: cache_source.py now retries via headless Chromium when urllib
returns 403/429 OR content that looks like an unhydrated SPA (blank text,
JS-required markers). Promoted from v2.1 backlog Idea 10 (Tier-3) because
the user had hit WebFetch failures repeatedly on JS-rendered sites — known
problem, deferred too long.

### Design
- urllib stays the default fast path. Playwright is a fallback gated by
  `--escalate-on-failure`.
- Detection heuristics: HTTP 403/429 escalates immediately; HTTP 200 with
  <500 chars OR containing JS-required markers (`<noscript>`, "Please
  enable JavaScript", empty React/Next.js root divs) escalates after the
  urllib response is received.
- Playwright is lazy-imported only when escalation triggers — script stays
  usable without Playwright installed; helpful RuntimeError when escalation
  is requested but the dep is missing.
- New optional `fetch_method: urllib | playwright_rendered` field on
  cache_manifest entries. urllib default is omitted from disk for
  backward-compatible byte-stability with existing v3 fixtures.

### Modified surfaces
- `scripts/cache_source.py`: +~100 LOC for `_content_is_suspect`,
  `_fetch_via_playwright`, escalation wiring in `cache_one`, and
  `--escalate-on-failure` CLI flag.
- `validators/cache_manifest.py`: new `ALLOWED_FETCH_METHODS` enum;
  validator gates the optional field.
- `pyproject.toml`: 2.2.0 → 2.2.1; `playwright>=1.40` added to dev extras.
- `docs/getting_started.md`: Playwright install step (`pip install -e
  ".[dev]" && playwright install chromium`). Size guard bumped 200 → 250
  in tests/test_v1_5_artifacts.py.
- `docs/troubleshooting.md`: two new entries — uninstalled-Playwright
  RuntimeError, and "Playwright rendered but still empty" (auth /
  captcha / geographic blocks).
- `tests/test_cache_source.py`: 6 new tests (urllib fast path; HTTP 403
  escalation; flag-off no-escalation; short-content escalation;
  JS-marker escalation; suspect heuristics unit test). All use
  monkeypatched `_fetch_via_playwright` — no real browser launch in
  CI.

### End-state metrics
- 230 tests + 2 xfailed pass (was 224 + 2 before Phase 1.5).
- v2-smoke green, audit-strict green.
- All existing v3 fixtures stay byte-stable (fetch_method omitted on
  urllib captures means no entry changes).

### Friction items (1 surfaced, 0 applied, 1 deferred)

**1. No real-browser smoke test in CI (status: surfaced — deferred)**
- All Playwright tests use monkeypatched `_fetch_via_playwright`. A real
  Chromium launch in CI would catch regressions in the actual rendering
  step but adds dependency weight and CI runtime.
- **Deferred**: optional `PLAYWRIGHT_REAL_BROWSER=1` env-var-gated test
  for local dev; CI stays mocked. Not blocking Phases 2–4.

### Phase 1.5 conclusion

Playwright escalation ready. Phases 2–4 (fresh-topic dogfood runs) can
now reliably cache JS-rendered sources via `--escalate-on-failure`. The
v2.1 backlog Idea 10 promotion was the right call — preventive fix
before the dogfood would have hit the failure.

---

## v2.2.0 dogfood — Phase 5: cross-cutting synthesis + v2.3 candidate list — 2026-05-20

**Theme**: aggregate friction across Phase 1-4 dogfoods; decide which
Tier-2/3 backlog items deserve v2.3 promotion. Per user's "USE posture"
framing, no v2.3 design cycle is scheduled; this is forward-looking
documentation for when one happens.

### Cumulative dogfood metrics

| Phase | Topic | Sources | Synthesis | Verbatim | Corroborated | Atoms / source |
|---|---|---|---|---|---|---|
| 1 | toolkit_design migration | 23 | 4 | 35/35 (100%) | 4/27 (15%) | 1 |
| 2 | eval drift | 4 | 0 | 4/4 (100%) | 0/4 (0%) | 1 |
| 3 | causal inference | 3 | 0 | 3/3 (100%) | 0/3 (0%) | 1 |
| 4 | agent capabilities | 4 | 1 | 6/6 (100%) | 1/5 (20%) | 1 |

**Pattern A (positive)**: 100% verbatim_match substring pass across
every dogfood project, every source. The v2.1.0 substring-anchored
extraction_method is rock-solid at production scale.

**Pattern B (positive)**: cross-source synthesis emerges (1) at corpus
scale (Phase 1's 23 sources naturally produce 4 synthesis claims) OR
(2) with deliberate multi-family curation (Phase 4's hand-picked Zhao
+ Schaeffer pairing). Synthesis is NOT automatic at small-N (Phase 2,
3 have 0 synthesis claims).

**Pattern C (structural)**: atomic decomposition stayed at 1 atom per
source across ALL four phases. Per-bullet multi-atom decomposition
needs LLM-driven /agent-index Phase 2c generation against fresh prose,
not retroactive splitting of existing excerpts. This is a CLARIFICATION
of v2.2 Item 1, not a defect — but should be documented as expected
behavior in references/strict_live_v2.md.

### Cross-phase friction items (sorted by frequency × severity)

**HIGH frequency (3+ phases): atomic decomposition cap**
- Appears in Phase 1, 2, 3 (and implicitly in Phase 4 — the synthesis
  claim doesn't change the 1-atom-per-source ratio for the underlying
  primary atoms).
- **NOT a defect**: v2.2 Item 1's design intent is per-bullet multi-atom
  decomposition during /agent-index Phase 2c generation. Migration +
  gather-time atomic IDs both stay at 1-atom (correctly).
- **v2.3 documentation candidate**: clarify in strict_live_v2.md that
  multi-atom-per-bullet requires fresh LLM-driven generation.

**MEDIUM frequency (2 phases): corroboration metric at 0% small-N**
- Phase 2 and 3 dashboards report `corroborated 0/4 (0%)` and `0/3 (0%)`
  respectively. Accurate but visibility-degraded — looks like a failure
  state at first read.
- **v2.3 candidate (Tier-2)**: dashboard suppresses corroboration row
  when total atoms <6, OR annotates with "(corpus too small for
  cross-source synthesis)". Low effort, clear value.

**MEDIUM frequency (2 phases): "redundant survey paper" escalation
pattern**
- Phase 2 (Rubrics as Attack Surface → escalate_to_manual on scope
  overlap) and Phase 3 (Causal Inference Survey → escalate_to_manual
  as redundant with selected primary).
- **v2.3 candidate (Tier-2)**: research_plan.md template OR
  citation_rules.md document the canonical reject/escalate reasons:
  - "Survey of what we already have" (redundant secondary)
  - "Borderline scope" (partial fit, belongs in different dossier)
  - "Vendor marketing" (pattern-match keywords, no methodology)
  - "Login-gated / paywalled" (rights_status: restricted)
- Small documentation effort; high signal for future authors.

**LOW frequency (1 phase each), positive signals to preserve:**
- Phase 2: gather_trace IsSup distribution genuinely useful when author
  deliberately searches beyond accept-able results — validates v2.2.0
  Phase A
- Phase 3: Action Queue refresh dates earn their keep on slow subjects
  where Discovery Rigor signal is weak
- Phase 4: cross-source synthesis emerges at fresh-topic scale with
  multi-family curation — validates v2.2.0 Phase B
- Phase 1.5: Playwright escalation stayed dormant across all 4 fresh-
  topic phases (all arxiv sources urllib-friendly). Preventive, not
  curative yet. Worth keeping but not load-bearing.

**LOW frequency (1 phase): synthesis claim text comes from source
excerpt, not author-written synthesis**
- Phase 4 only — but structurally affects all synthesis claims.
  build_claim_graph picks the "highest-quality + longest-excerpt"
  tiebreak text from the contributing sources, which is fine for
  visualization but understates what the synthesis IS.
- **v2.3 candidate (Tier-3 / exploratory)**: pre_selection_manifest
  could allow an author-written `synthesis_text` field for synthesis
  selections, displayed in dashboard + agent_index instead of the
  contributing-source excerpt. Larger schema change; consider if
  multiple future projects produce synthesis claims.

**LOW frequency (1 phase): gather_trace synthetic backfill**
- Only Phase 1 had backfill; subsequent phases generated fresh traces.
  Not a recurring pattern — defer indefinitely.

**LOW frequency (1 phase): no real-browser Playwright smoke test**
- Phase 1.5 friction. Optional env-gated test; defer unless we hit a
  Playwright regression.

### v2.3 candidate list (prioritized)

**Tier-2 v2.3 candidates** (warrant a design cycle if one happens):
1. **Survey-paper escalation cheatsheet** (XS effort) — add canonical
   reject/escalate reasons to references/citation_rules.md or
   research_plan.md template. ~30 minutes of doc work; immediately
   useful for authors.
2. **Corroboration metric small-N suppression** (S effort) — modify
   build_dashboard.py to omit or annotate the corroboration row when
   total atoms <6. Mechanical change to the existing metric block.
3. **strict_live_v2.md atomic-decomposition expectation note** (XS
   effort) — clarify that multi-atom-per-bullet requires fresh
   /agent-index Phase 2c generation, not retroactive splitting.

**Tier-3 v2.3 candidates** (exploratory; only if specific friction
recurs):
4. **pre_selection_manifest synthesis_text field** (M effort) —
   author-written synthesis text alongside contributing-source excerpts.
   Schema addition. Defer until multiple projects produce synthesis
   claims AND the tiebreak-picked text noticeably understates them.
5. **Playwright real-browser smoke test** (S effort) — env-gated
   test. Defer unless Playwright path breaks.

**Backlog items NOT promoted** (Tier-2/3 from v2_2_design_backlog.md
that did NOT surface as friction across 4 dogfoods):
- Item 4 (semantic entropy audit), Item 4b (Lookback Lens), Item 4c
  (counterfactual probing): not surfaced — no synthesis claim went
  through paraphrase / llm_inferred extraction methods that would
  trigger semantic-entropy stress-testing
- Items 5b-5f (RAGTruth, Retromorphic, Tool-MAD, GSAR, KEA Explain):
  not surfaced — multi-agent debate and KG-grounding integrations
  weren't exercised at this dogfood scale
- Items 6, 6b-6e (Faithfulness fusion, MAD-Fact, Process reward,
  Probabilistic certainty, DoublyCal): not surfaced — calibration
  fusion isn't needed when all evidence is verbatim_match (the v2.1
  guarantee carries forward)

These remain valid backlog items but lack EVIDENCE-DRIVEN promotion.
Wait for specific friction before elevating.

### Decision: NO v2.2.2 patch needed

v2.2.0 ships as designed. v2.2.1 (Playwright escalation) shipped as the
one fixable item that was hitting the user repeatedly. The Phase 1-4
dogfoods surfaced documentation candidates + small dashboard tweaks +
2 cosmetic schema additions — none are blocking, none warrant a patch
release.

**v2.2 release stays USE posture.** v2.3 candidate list above documents
what to consider whenever a design cycle is scheduled. No design cycle
is scheduled.

### Closing the v2.2.0 dogfood arc

4 phases completed, 5 BURN_IN sections written, 5 commits to
research_toolkit/, 4 dogfood projects produced (research_toolkit_design
migrated; research_eval_drift, research_causal_inference_ml,
research_agent_capabilities_scaling fresh). Total time: ~12-15h across
multiple sessions.

The v2.2.0 release was validated end-to-end on real subjects spanning
fast / mid / slow velocity regimes AND retroactive migration of an
existing 23-source corpus. Both rounds of design questions ("does
v2.2 work?" + "is gather_trace's reflection mechanism actually used?")
got positive answers backed by concrete artifacts.

Next session (whenever): user picks. Options include:
- Flesh out the 4 dogfood projects from seed corpora into substantial
  dossiers
- Bring research-kb ingestion online (separate repo)
- Schedule a v2.3 design cycle if the candidate list above feels
  worth pursuing

---

## v2.2.0 dogfood — Phase 4: AI agent emergent capabilities / scaling laws — 2026-05-20

**Theme**: mid-velocity fresh-topic v2.2 pipeline pass. Targeted mechanism:
multi-family decomposition + cross-source synthesis — does v2.2 produce a
synthesis claim NATURALLY when sources span overlapping claim_families?

**Project**: `~/Claude/research_agent_capabilities_scaling/` (personal,
not committed). Seed for future expansion into a full agent-capabilities
dossier.

**End-state metrics**:
- 4 primary sources cached + verified (urllib only — all arxiv pages)
- 5 fetches in gather_trace (4 accept + 1 reject — Stanford HAI news
  article rejected as redundant secondary)
- 5 atomic claims (4 primary atoms + 1 cross-source synthesis claim)
- 6 support links (4 primary + 2 synthesis bindings)
- 6/6 verbatim_match substring pass (100%)
- **1/5 corroborated (20%)** — `claim_synthesis_emergence_debate`
  aggregates Zhao 2025 (emergent_capability family) + Schaeffer 2023
  (inverse_scaling family). **First fresh-topic dogfood to produce a
  synthesis claim.**
- 5/5 atoms fully supported
- Dashboard Action Queue: 3 tiers (volatile + active + stable)
- 21-line research-kb export, validator clean

### Friction items (3 surfaced, 0 applied, 3 deferred)

**1. Cross-source synthesis DOES emerge naturally with intentional
   multi-family source selection (status: surfaced — positive result;
   v2.2 design validated)**
- Worry going in: cross-source synthesis was the v2.2 design payoff
  but only seen in retroactive migration (Phase 1's 23 sources).
  Could v2.2 produce synthesis claims at fresh-topic scale (3-5
  sources)?
- Actual experience: yes, when the AUTHOR deliberately picks sources
  spanning ≥2 claim_families AND the sources address the same higher-
  level question from different framings. Zhao 2025 (distributional
  shifts produce apparent emergence) + Schaeffer 2023 (metric choice
  produces apparent emergence) BOTH support a single synthesis claim
  about "emergence is partly an artifact of measurement."
- **Validation of v2.2.0 Phase B (atomic + Attribute-First)**: the
  synthesis claim is a real atom (`claim_synthesis_emergence_debate`)
  with 2 distinct evidence_id supports across 2 distinct source_urls.
  The corroboration metric correctly reports 1/5 (20%).

**2. The two-evidence synthesis claim required carefully-chosen sources
   (status: surfaced — author-discipline observation)**
- The 4 sources cached were NOT randomly representative — Zhao + Schaeffer
  were deliberately chosen because they argue opposite framings of the
  same underlying question. A random 4-source set would likely NOT
  produce a synthesis claim.
- **Implication**: cross-source synthesis is an *author choice*, not
  an emergent property of any v2.2-compliant 4-source corpus. The
  toolkit supports synthesis-claim authorship cleanly; the synthesis
  itself requires the human to recognize the cross-source pattern.
- **No v2.2 fix needed**: this is correct — the author SHOULD make
  this judgment call. But it's worth documenting in
  references/dual_audience_design.md that synthesis claims aren't
  automatic.

**3. The two synthesis atoms have identical excerpts (status: surfaced —
   minor UX issue)**
- ev_distributional_scaling supports both
  `claim_agent_capabilities_zhao2025distributional_a1` AND
  `claim_synthesis_emergence_debate` from the SAME byte offset +
  sha256. Likewise for ev_mirage_metric_emergence.
- The synthesis claim's "text" in claim_graph.jsonl came from one of
  the source excerpts (highest-quality + longest-excerpt tiebreak).
  That's fine — the synthesis CLAIM is implicit in the cross-source
  juxtaposition, not in either excerpt alone.
- **v2.3 candidate**: pre_selection_manifest could allow a synthesis
  selection to record an *author-written* synthesis_text alongside
  the source excerpts ("the cross-source claim is X; here are the
  contributing spans"). Right now the synthesis claim's text is
  one of the contributing spans, which understates what synthesis
  is doing.

### Phase 4 conclusion

v2.2 produces cross-source synthesis claims at FRESH-topic scale when
the author deliberately picks multi-family sources. The corroboration
metric works as designed. This validates the v2.2.0 Phase B Attribute-
First design at the smallest-meaningful scale (4 sources + 1 synthesis).

**Cumulative metrics across the four dogfood projects**:
- Phase 1 (migration, 23 sources): 35/35 verbatim, 4/27 corroborated
- Phase 2 (eval drift, 4 sources, no synthesis): 4/4 verbatim, 0/4 corroborated
- Phase 3 (causal inference, 3 sources, no synthesis): 3/3 verbatim, 0/3 corroborated
- Phase 4 (agent capabilities, 4 sources + 1 synthesis): 6/6 verbatim, 1/5 corroborated

The pattern: **cross-source synthesis emerges at corpus scale OR with
deliberate multi-family curation**, not from any small-N corpus.

Next: Phase 5 (cross-cutting BURN_IN synthesis + v2.3 promotion review).

---

## v2.2.0 dogfood — Phase 3: causal inference for observational ML — 2026-05-20

**Theme**: stable-subject fresh-topic v2.2 pipeline pass. Targeted
mechanism: assess whether v2.2's overhead (atomic + pre_selection_manifest
+ gather_trace) is justified when freshness pressure is low. Counter to
Phase 2's fast-moving subject — does the toolkit's machinery still earn
its keep?

**Project**: `~/Claude/research_causal_inference_ml/` (personal, not
committed). Seed for future expansion into a full causal-inference dossier.

**End-state metrics**:
- 3 primary sources cached + verified (urllib only — arxiv pages render
  cleanly; Playwright never triggered)
- 4 fetches in gather_trace (3 accept + 1 escalate_to_manual)
- 3 atomic claims (1 atom per source — same retroactive limitation)
- 3/3 verbatim_match substring pass (100%)
- 0/3 corroborated (single-source-per-atom at small N)
- 3/3 atoms fully supported
- Dashboard Action Queue: stable-tier-dominated; earliest refresh
  due 2027-05-20 (one full year out — exactly what the plan predicted)
- 15-line research-kb export, validator clean

### Friction items (4 surfaced, 0 applied, 4 deferred)

**1. v2.2 overhead feels PROPORTIONATELY APPROPRIATE on slow subjects,
   not over-engineered (status: surfaced — positive result)**
- Worry going in: v2.2's machinery (pre_selection_manifest with byte
  offsets + sha256, atomic decomposition, gather_trace reflection)
  would feel heavyweight on stable foundational papers.
- Actual experience: writing pre_selection_manifest for 3 sources was
  ~5 minutes of mechanical Python (same script as Phase 2). gather_trace
  was honest (3 accepts + 1 escalation is genuine, not box-ticking).
  Atomic decomposition stayed at 1 atom per source — the same
  fundamental limitation as Phase 1+2, not a new problem.
- **Conclusion**: the structural overhead is amortized across all corpus
  sizes and velocities. It's not v2.2 that's heavy for slow subjects;
  it's that small-N corpora don't get to USE all of v2.2's signals
  (corroboration metric stays at 0/3, multi-atom synthesis doesn't
  emerge naturally at 3 sources).

**2. Action Queue genuinely useful on slow subjects (status: surfaced —
   positive result)**
- Dashboard reports "Refresh stable entries by 2027-05-20" — a year
  out. That's NOT over-engineered: it's a calendar reminder that even
  foundational papers eventually need re-verification. Without
  freshness_tier, a stable-subject dossier would silently drift past
  the "should re-check" threshold.
- For slow subjects, gather_trace contains less signal (most fetches
  rubber-stamp accept) but Action Queue contains MORE signal (it's
  the only mechanism that catches "this 2-year-old paper is still
  the canonical reference, but you should re-verify by date X").

**3. Cross-source synthesis is gated on corpus size (status: surfaced —
   v2.2 design observation)**
- 3 sources, 3 distinct sub-areas, 3 distinct claim_families → no
  natural cross-source claims. Corroboration metric reports 0/3 (0%).
- This is correct behavior but visibility-degraded on small corpora.
  Same observation as Phase 2 (4 sources, 0/4 corroboration).
- **Threshold heuristic**: cross-source synthesis emerges naturally
  around 6+ sources with overlapping claim_families. The Phase 8
  dogfood project (23 sources, 4 synthesis claims) is the right shape;
  Phase 2/3's small dogfoods aren't.
- **v2.3 candidate**: dashboard could suppress or annotate the
  corroboration metric when total atoms <6 (informational only at
  small N).

**4. The "survey paper" escalation pattern repeats (status: surfaced —
   notable signal)**
- Phase 2 escalated a paper with partial scope (Rubrics as Attack
  Surface — borderline harness_drift). Phase 3 escalated a survey
  paper (2209.00869 "A Survey of Causal Inference Frameworks") as
  redundant with wang2025threeframeworks.
- **Pattern**: "this paper exists in the search results AND touches
  the sub-area BUT we already have better coverage" is the most
  common escalate_to_manual reason. Worth documenting in
  references/citation_rules.md as a v2.3 candidate.

### Phase 3 conclusion

v2.2 is NOT over-engineered for slow subjects — the structural overhead
is proportionate. What DOES change between fast and slow subjects:
- Fast (Phase 2): gather_trace IsSup distribution is the main signal
- Slow (Phase 3): Action Queue refresh dates are the main signal
- Cross-source synthesis (Phase 1's 23-source corpus) is the natural
  payoff at corpus scale, not small-N proof-of-concept

Next: Phase 4 (agent capabilities) — mid-velocity + multi-family
decomposition. Will test whether v2.2's cross-family binding emerges
naturally with intentional multi-family source selection.

---

## v2.2.0 dogfood — Phase 2: AI eval drift fresh-topic dogfood — 2026-05-20

**Theme**: first fresh-topic v2.2 pipeline pass. Targeted mechanism:
stress gather_trace's IsSup=partial / IsSup=none path (the rubber-stamp
failure mode the user flagged as a top concern).

**Project**: `~/Claude/research_eval_drift/` (personal, not committed).
Seed for future expansion into a full eval-reliability dossier.

**End-state metrics**:
- 4 primary sources cached + verified (urllib only; no Playwright
  needed for these arxiv pages)
- 6 fetches in gather_trace (4 accept + 1 escalate_to_manual + 1 reject)
- 4 atomic claims (1 atom per source — same retroactive limitation as
  Phase 1's migration)
- 4/4 verbatim_match substring pass (100%)
- 0/4 corroborated (single-source-per-atom at this scale — by design,
  4 sources is too few for natural cross-source synthesis)
- 4/4 atoms fully supported
- Dashboard Discovery Rigor: 4/6 accept rate (67%), 1 rejected, 1
  escalated for manual review
- 20-line research-kb export, validator clean

### Friction items (4 surfaced, 0 applied, 4 deferred)

**1. The IsSup=partial / IsSup=none path IS exercisable AND DOES feel
   useful (status: surfaced — positive result confirming design intent)**
- I deliberately fetched a borderline-scope paper (Rubrics as Attack
  Surface, arXiv 2602.13576) and a vendor marketing blog
  (lxt.ai/blog/llm-benchmarks/). The first got
  IsSup=partial → decision=escalate_to_manual; the second got
  IsSup=none → decision=reject.
- **The escalate_to_manual record is genuinely useful**: the rubrics
  paper IS relevant to harness reliability but introduces an
  attack-model framing that may belong in a separate dossier.
  Without gather_trace's IsSup gradation, this would either be silently
  accepted (and dilute the dossier) or silently rejected (and lose the
  signal). The escalation makes it explicit.
- **Validation of v2.2.0 Phase A**: Self-RAG-style reflection
  earns its keep at small scales (4-source dogfood) too. The user's
  rubber-stamp concern is mitigated when the author deliberately
  searches BEYOND accept-able results.

**2. Fresh atomic decomposition still produced 1 atom per source
   (status: surfaced — confirms Phase 1 finding)**
- Same limitation as Phase 1 migration: each evidence's existing
  excerpt anchors a SINGLE atomic claim_id. Phase 2 doesn't fix this
  because the gather step naturally captures one excerpt per source.
- **The fix is /agent-index Phase 2c generation**: real per-bullet
  multi-atom decomposition happens when an LLM writes prose
  conditioned on the pre_selection_manifest's atoms. With 4 sources
  and brief 5-bullet entries, atomic decomposition felt
  proportionately appropriate — not over-engineered, but also not
  yielding the dramatic 5-atoms-per-bullet pattern the schema
  supports.
- **v2.3 candidate**: a "decompose this excerpt into 2-3 atoms"
  helper that scans an evidence entry and emits suggested atom
  splits would lower the cognitive cost when authors DO want
  multi-atom decomposition.

**3. Corroboration metric reports 0% at small N — not a defect but
   a visibility issue (status: surfaced — UX note)**
- 4 sources, 4 distinct atomic claims, no cross-source synthesis →
  dashboard reports `corroborated (≥2 independent sources): 0/4 (0%)`.
- That's accurate but misleading on first read: a healthy small-N
  dossier WILL show 0% corroboration because there aren't enough
  sources to cross-validate yet.
- **v2.3 candidate**: dashboard could note when corroboration is 0%
  on small-N corpora ("expected — corpus too small for cross-source
  synthesis"). Or suppress the metric below a 6-source threshold.

**4. cache_source.py worked first-try on all 4 arxiv URLs without
   Playwright (status: surfaced — Phase 1.5 isn't always needed)**
- All 4 sources are arxiv abstract pages — urllib renders them fine.
  No HTTP 403/429, no JS-required markers. Phase 1.5's escalation
  path stayed dormant.
- **Implication**: Phase 1.5 was preventive (good), not curative
  (yet). The real test will be Phase 3 (causal inference) and
  Phase 4 (agent capabilities) where vendor blogs and benchmark
  dashboards may surface.

### Phase 2 conclusion

The v2.2 pipeline runs cleanly end-to-end on a fresh topic. **The
deliberately-diverse gather_trace was the key validation**: it
demonstrated that the Self-RAG reflection mechanism does add signal
when the author intentionally searches beyond accept-able results.
The user's rubber-stamp concern is real BUT addressable by author
discipline (deliberately recording non-accept fetches), not requiring
a v2.2 design fix.

Next: Phase 3 (causal inference, slow-moving subject — tests whether
v2.2 feels over-engineered when freshness pressure is low).

---

## v2.2.0 dogfood — Phase 1: migrate research_toolkit_design to v2.2 — 2026-05-20

**Theme**: first real-world contact with v2.2's atomic + Attribute-First +
adaptive-retrieval flow. Migrated the Phase 8 dogfood project (23 sources,
v3 schema, ledger-only) into a full v2.2 layout by backfilling
gather_trace.yml, renaming claim_ids to atomic naming, writing
pre_selection_manifest.yml, and rendering agent_index/.

**End-state metrics** (~/Claude/research_toolkit_design/):
- 23 bib entries (unchanged from iter 10)
- 23 fetches in gather_trace.yml (synthetic backfill, all accept)
- 27 claims in claim_graph.jsonl (23 atomic + 4 cross-source synthesis)
- 35 support links, 35/35 verbatim_match substring pass (100%)
- 35 selections in pre_selection_manifest.yml
- 4/27 corroborated (≥2 independent sources) — the synthesis claims
- 24/27 atoms fully supported (3 synthesis claims have at least one
  evidence_role_strength: partial binding)
- 6 agent_index files (README + 5 topic files)
- 119-line research-kb export, validator clean

### Friction items (4 surfaced, 1 applied, 3 deferred to Phase 5)

**1. Retroactive atomic decomposition is structurally limited (status:
   surfaced — deferred to Phase 5 design discussion)**
- The migration could only produce 1 atom per existing source — every
  primary atom is `claim_toolkit_design_<bibkey>_a1`. Real
  per-bullet decomposition (2–5 atoms per bullet via /agent-index
  Phase 2c generation) requires the LLM to generate prose conditioned
  on pre-selected spans, which is fresh-research work, not migration.
- **Implication**: v2.2's "atomic decomposition" benefit shows up only
  when /agent-index runs against fresh sources. Migrating existing
  ledger-only projects yields the structural manifests but not the
  atom granularity. Document this expectation in
  references/strict_live_v2.md if not already clear.
- The agent_index/ markdown DOES cite atomic claim_ids inline
  ([claim_toolkit_design_<bibkey>_a1]), so the structural contract
  holds — it just doesn't show off the multi-atom-per-bullet pattern.

**2. Synthesis claims naturally produce the corroboration signal
   (status: applied — confirms design intent)**
- 4 synthesis claims × 3 sources each = 12 supports across the
  synthesis namespace. Dashboard reports 4/27 corroborated, which IS
  the design intent. The corroboration metric is meaningful on this
  corpus even without multi-source atomic decomposition.
- **No fix needed**: this is what the v2.2.0 backlog Item 2 (scoring
  half) was supposed to deliver. Validated.

**3. gather_trace.yml synthetic backfill validates clean but feels
   noisy (status: surfaced — deferred)**
- The 23 backfilled fetches all read `decision: accept, IsRel: true,
  IsSup: full, IsUse: 5, reason: "primary peer-reviewed source aligned
  with sub_area; retroactive backfill from iter 1-10"`. Honest about
  the synthetic origin (the reason field flags it), but the resulting
  trace doesn't exercise the reflection-mechanism's discrimination —
  every entry rubber-stamps. The dashboard's Discovery Rigor section
  reports 100% accept rate, which is structurally true but
  uninformative.
- **v2.3 candidate**: the validator could accept a top-level
  `synthetic_backfill: true` flag that surfaces in the dashboard's
  Discovery Rigor section as "(synthetic backfill — not actionable)"
  to distinguish real reflection traces from backfills. Low-priority
  unless other dogfoods produce backfilled traces too.

**4. pre_selection_manifest mechanical writing was cheap — at this
   scale (status: deferred / informational)**
- 35 selections written programmatically from existing evidence_ledger
  excerpts in ~30 lines of Python. No new byte-offset computation
  needed (existing v3 evidence anchors already had offsets + sha256).
- **Caveat**: this only worked because the project was already at v3
  schema. Migrating a v2 (non-v3) project would need fresh substring
  computation per excerpt. Document the v2→v3 path is a prerequisite
  for the v2→v2.2 migration.

### Notable validation moments

- All v2.2 validators clean on the migrated project — the
  pre_selection_manifest's `verify_excerpt_anchor` call re-verifies
  each span via substring + sha256 + bytes-equality. 35/35 pass.
- v2-smoke on the toolkit itself still 224 tests + 2 xfailed pass.
- The atomic_grounding agent_index file (`01_atomic_grounding.md`)
  ended up most demonstrative — 5 sources (FActScore + VISTA +
  RAGTruth + AtomEval + VeriFact) all citing atomic IDs inline. This
  is what a fully-realized atomic-decomposition agent_index would
  look like.

### Phase 1 conclusion

v2.2 migration of an existing v3 project is **mechanical and cheap
when the byte-anchored evidence already exists**. The benefit is
structural (additive manifests, atomic naming, agent_index
rendering), not semantic (atom-per-bullet decomposition needs fresh
generation). The corroboration metric correctly identifies the 4
cross-source synthesis claims as the multi-source backbone of the
corpus.

Migration didn't surface any v2.2 design bugs. Next: Phase 1.5
(Playwright in cache_source.py) and Phases 2–4 (fresh-topic
end-to-end runs) will be the more rigorous QA passes.

---

## v2.2.0: atomic decomposition + Attribute-First + adaptive retrieval — shipped 2026-05-20

**Theme**: ship the three Tier-1 items from the Phase 8 design backlog
as a single v2.2.0 release. Closes the structural-anti-hallucination
loop opened in v2.1.0 (substring-anchored evidence). Where v2.1 ensures
the *cited link* is real, v2.2 ensures the *generation step* never
chose the citation post-hoc.

**Phase A (commit d4ac214) — Item 5: Self-RAG adaptive retrieval.**
- Added `gather_trace.yml` artifact, template, validator
- /research-gather Phase 2 documents per-fetch reflection
  (IsRel/IsSup/IsUse + decision); /freshness-audit Phase 4 reads it
- build_dashboard.py adds a conditional Discovery Rigor section
- Extended `v2_strict_live_ai_agents` fixture with a 3-fetch trace
  (accept/reject/escalate)
- 8 new tests; v2-smoke + audit-strict wired

**Phase B (commit 177e4c4) — Items 1+3: atomic + Attribute-First.**
- New `pre_selection_manifest.yml` artifact written in /agent-index
  Phase 2b BEFORE prose; validator rejects evidence_ids that don't
  trace to a pre-selected span (post-hoc rationalization → structural
  failure)
- /agent-index emits 2–5 free-text atomic claim_ids per 5-bullet block;
  build_claim_graph.py needed no schema change (many-to-many already
  supported); build_dashboard adds two v3 Claim Health rows
  (corroborated, atoms fully supported)
- New `v2_strict_live_atomic` fixture: 3 atoms per bullet, all
  100% verbatim-anchored
- 8 new tests; v2-smoke + audit-strict wired

**Phase C (commit ?) — Docs + version bump.**
- references/strict_live_v2.md gets a v2.2 additive-extensions section
  covering gather_trace, pre_selection_manifest, atomic claim_ids, and
  the two new dashboard metrics
- references/dual_audience_design.md documents the atomic claim_id
  rendering convention (b<N>_a<M>_<descriptor> naming + inline-suffix
  preferred)
- references/citation_rules.md adds the atomic claim_id inline syntax
- references/audit_protocol.md extends the v2 update contract to cover
  atomic claims + pre_selection_manifest propagation
- docs/troubleshooting.md adds gather_trace + pre_selection_manifest
  troubleshooting entries
- pyproject.toml: 2.1.0 → 2.2.0

**End-state metrics**: 232 tests + 2 xfailed pass; make v2-smoke green;
make audit-strict green. The atomic fixture exercises the full v2.2
pipeline (1 source → 3 atomic claims → 100% verbatim-anchored
evidence). All four design decisions per the locked-in scope:
sequence (Items 1+3 bundled, 5 separate), schema (stay v3 additive),
atom shape (free-text, SROM deferred to v2.3), release shape (single
v2.2.0).

**v2.2 settles into USE posture.** v2.3 candidates from the saturated
23-source backlog include SROM 4-tuple atom upgrade, multi-agent debate
harness (Items 5d/5e), semantic-entropy citation audit (Item 4), and
the cache://sha256/<digest> locator scheme. None are planned until
specific friction surfaces.

### Friction items (3 surfaced, 0 applied, 3 deferred)

**1. Existing v3 fixture dashboard had to be regenerated (status:
   applied)**
- v2.2's new Claim Health rows (corroborated, atoms fully supported)
  appear on v3 evidence_ledgers. The `v3_strict_live_demo` and
  `v2_strict_live_ai_agents` fixture dashboards had to be regenerated.
  Tracked, no real impact: the regenerated dashboards stay byte-stable
  going forward. v2 fixtures unaffected.

**2. pre_selection_manifest cross-ref requires claim_graph to exist
   first (status: surfaced — workflow ordering)**
- The validator cross-refs atom_ids against
  sibling `claim_graph.jsonl`. If claim_graph hasn't been built yet,
  atom_ids appear "missing." Workflow: write evidence_ledger first →
  build claim_graph → THEN write pre_selection_manifest. The
  /agent-index skill body Phase 2 documents this ordering (2a span-select
  → 2b plan/manifest → 2c generate), but the validator could be more
  helpful by suggesting "run `build_claim_graph.py` first."
- **Deferred to v2.3**: validator could detect the absence of
  claim_graph.jsonl and emit a clarifying hint.

**3. Dogfood project (~/Claude/research_toolkit_design/) not migrated
   to v2.2 (status: deferred — open for next session)**
- The Phase 8 dogfood project has 23 sources at v3 schema. Migrating
  it to v2.2 (atomic decomposition + pre_selection_manifest) would
  validate the new pipeline at scale and demonstrate the corroboration
  metric (4 synthesis claims with 3 sources each → 100% corroborated
  by definition).
- **Deferred**: not blocking v2.2.0 ship; valuable as a v2.2.1 dogfood
  pass if user wants. Mechanical effort (no new research, just adapt
  existing entries to atom-level granularity).

---

## Phase 3.5: prompt-injection full-mode recreation

**Date started:** 2026-05-07
**Output:** `tests/fixtures/prompt_injection_snapshot/recreated/`
**Comparison:** `tests/fixtures/prompt_injection_snapshot/real/` (137 entries, 7 dossier files, 9 indexed files)

### Stage 1: /research-plan (reverse-engineered)

(populated as observations surface)

### Stage 2: /research-gather

**1. Crescendo first-author misattribution (status: corrected, applied during run)**
- The reverse-engineered research_plan.md listed `mehrotra2024crescendo` as a known landmark. Crescendo's lead author is Russinovich (Microsoft); Mehrotra is the lead author of TAP (Tree of Attacks, arXiv:2312.02119). The subagent caught this during WebFetch verification and registered both correctly: `russinovich2024crescendo` (arXiv:2404.01833) and `mehrotra2023tap` (arXiv:2312.02119).
- **Why it matters:** When `/research-plan` reverse-engineers a plan from existing dossier prose, author attributions in the plan can carry forward errors. The verification step in `/research-gather` (WebFetch on landmark papers) caught this. The skill chain self-corrected — exactly the design intent.
- **Action:** None required for v1.0. Document this as a positive case for the WebFetch-verify-landmarks step.

**2. bib_ledger schema is too minimal for /dossier-build (status: surfaced — design gap)**
- bib_ledger entries store only `bibkey | primary_url | title | status | claim_family`. The dossier table template requires `Title | Authors (year) | Venue | arXiv/DOI | GitHub | <description> | <contribution>`. The dossier-build skill has no specified mechanism to fill in `Authors (year)`, `Venue`, `description`, or `contribution`.
- **Why it matters:** Either `/research-gather` must populate richer fields, OR `/dossier-build` must WebFetch each entry to get them, OR the schema expands. Currently the skill body is silent on this; the agent rendering Stage 3 has to choose.
- **Action for v1.0:** Document the gap; let Stage 3 use bibkey-heuristic for Authors (e.g., `perez2022ignore` → "Perez et al. (2022)"). For v1.1 design cycle, decide between the three resolutions above.

**3. Per-claim_family distribution is highly skewed (status: noted, no action)**
- Recreated bib_ledger has 25 entries in `red_teaming_tools` and 16 in `evaluation`/`attack_direct_jailbreak`, but only 1 each in `defense_smoothing` and `other`. The real ledger's distribution differs (e.g., 44 entries in `other`, suggesting heterogeneous misc content the recreation missed).
- **Why it matters:** Helps interpret the `test_recreation_diff.py` output later — large per-family deltas don't necessarily indicate skill failure; they may reflect different categorization choices.

### Stage 3: /dossier-build

**1. Validator's column-5 prefix list ("GitHub", "HF", "Code", "Repo") fights natural rendering for vendor-product / standards-PDF tables (status: surfaced — borderline)**
- The validator requires column 5 of any paper table (col 2 = "Authors (year)") to start with "GitHub" / "HF" / "Code" / "Repo". For vendor pages and standards PDFs the natural column header would be something like "URL" or "Doc URL". Workaround: use the same 7-column schema across the whole dossier and put `—` in the GitHub cell for non-paper rows. This works but the dossier ends up looking heterogeneous across rows of the same table.
- **Why it matters:** If a dossier file is mostly vendor pages with a couple of arXiv preprints mixed in, the validator forces the file into the paper-schema even though the editorial intent might be a non-paper schema (col 2 ≠ "Authors (year)") with looser checks.
- **Action:** Document the workaround. Consider widening the prefix list (e.g., "URL", "Source") in v1.1 or recommending splitting heterogeneous content into separate files.

**2. bibkey-heuristic Authors rendering breaks down on multi-word surnames and corporate authors (status: surfaced — design gap)**
- Per BURN_IN Stage 2 #2, Authors are derived from bibkey. Heuristic works for `perez2022ignore` → "Perez et al. (2022)", but breaks for: corporate authors (`anthropic2024manyshotpdf` becomes "Anthropic" not a person; `nvidia2024garak` becomes "NVIDIA"); ambiguous slugs (`bel-air2025` — is "Bel-Air" a hyphenated surname or a place?). Manual override list would help.
- **Why it matters:** The Authors cell is validator-required to be non-empty, so heuristic failures get masked as plausible-but-wrong text rather than caught.
- **Action:** Document gap; consider a small bibkey → display-author override map in `/research-gather` output for v1.1.

**3. Cross-listing the same entry across files (e.g., GCG appears as both a paper in `01_attacks_direct` and a tool repo in `06_tools_vendors`) doesn't have a clear mechanism in the skill body (status: surfaced — friction)**
- The bib_ledger has 147 entries; at least 6 entries are conceptually both "the paper" and "the codebase" (GCG, NeMo Guardrails, ArtPrompt, JailbreakBench, BIPIA, llm-attacks repo). The skill body says one entry per dossier row but doesn't say what to do when the same source legitimately belongs in two topic files. I rendered each in the most-natural primary location and cross-referenced verbally.
- **Why it matters:** A future audit pass might flag the cross-listings as duplicates without realizing they're intentional.
- **Action:** Document this case in the skill body or add a "see also" cross-reference column. v1.1 design item.

**4. Dossier-table 7-column schema gets visually crowded for non-paper entries (status: minor friction)**
- Standards PDFs and vendor product pages have authorship like "OWASP", "NIST", "Anthropic", and the venue is just the source-org's site. The "One-line description" and "Key contribution" columns end up saying very similar things (e.g., "OWASP's prompt-injection entry" / "Authoritative OWASP entry"). Could collapse to fewer columns for non-paper-heavy files.
- **Action:** Note in template that the last two columns can be merged for vendor/standards-heavy tables; current schema works but is editorially redundant.

### Stage 4: /agent-index

**5. 5-bullet ordering enforcement only triggers when "Result" bullet is present — vendor entries skip enforcement (status: surfaced — design choice, working as intended)**
- The validator only enforces canonical Source/Code/Mechanism/Result/Status order when a `**Result:**` bullet is present. Vendor entries use the variant schema (Source/Status/Product line/Mechanism/Integration) which lacks Result, so the variant entries don't get ordering enforcement at all.
- **Why it matters:** This is intentional per the validator design but creates an editorial inconsistency — vendor entries can have arbitrary bullet orderings while paper-synthesis entries cannot. A future LLM-agent reader parsing the synthesis must branch on whether `Result` is present to know which schema to expect.
- **Action:** Document this in `5_bullet_entry.template.md` more loudly — the template mentions the variant but the schema-divergence implication for parser logic is implicit.

**6. Lookup recipes pattern (`**"What's X?"** → file § anchor`) doesn't survive `grep -c "^- \*\*\""` cleanly because of the escaped quote mark (status: minor)**
- When counting recipes for the README footer, the natural grep `grep -c '"What' README.md` undercount-fails depending on quoting style. My recipes used straight `"` characters and rendered fine, but a future automated counter needs careful regex.
- **Action:** Add to validator: count lookup-recipe lines as part of the verification step, surface as a metric in the validator output.

**7. (cross-cutting) The `(no arXiv)` placeholder vs `—` placeholder is inconsistent across the dossier and agent-index (status: surfaced — small)**
- Dossier table cells use `(no arXiv)` for the arXiv/DOI column when none, and `—` for the GitHub column when none. Agent-index uses `—` uniformly in the Code bullet. Validator accepts both but the inconsistency is jarring.
- **Action:** Tighten convention in `citation_rules.md` — declare one canonical placeholder.

### Stage 5: /dossier-audit (1 round, smoke)

**Result on smoke run (2026-05-07):** Round 1 against `tests/fixtures/prompt_injection_snapshot/recreated/agent_index/` with focus "anonymous arXiv entries and Authors-via-bibkey-heuristic accuracy". Verified 6 entries via WebFetch; produced 0 DROP / 3 CORRECT / 1 FLAG / 2 SPOT-CHECK PASSED. Both validators (`audit_trail.py`, `agent_index.py`) exit 0 after edits. Heuristic Author rendering was wrong on 3 of 5 arXiv entries (first-author surname diverged from the bibkey stem); titles/URLs were correct.

**1. Audit-trail format string differs between skill body and audit_protocol.md (status: surfaced — minor inconsistency)**
- `audit_protocol.md` § "Audit-trail note format" template lists three count buckets: "<count> dropped, <count> corrected, <count> flagged".
- `dossier-audit.md` Phase 6 uses the same three-bucket format.
- The user's invocation prompt requested four buckets including "<SPOT-CHECK PASSED count> verified clean" plus the trailing "1-sentence summary" position. Both formats validate (`audit_trail.py` only checks round number / date), but the skill body and reference do NOT mention the SPOT-CHECK count slot — agents may either omit it (per skill body) or include it (per a more useful audit trail).
- **Action for v1.1:** Decide canonical format and reflect in both skill body Phase 6 and `audit_protocol.md` § "Audit-trail note format". Including SPOT-CHECK PASSED count is more informative; recommend canonicalizing the four-bucket form.

**2. Skill body lists `Agent` tool but smoke run used inline WebFetch (status: surfaced — design ambiguity)**
- `dossier-audit.md` Phase 3 says "Use the `Agent` tool with `subagent_type=general-purpose`" to spawn a fresh sub-agent that does the WebFetch verification.
- The smoke run was executed with WebFetch calls in the same agent context (no sub-agent). This worked end-to-end — validators pass, audit-trail note appended in valid format — but it bypasses the design's intent (fresh-context sub-agent reduces confirmation bias).
- The skill's `allowed-tools` frontmatter is `Read, Edit, Bash` — does NOT include `Task`/`Agent` — so a strict-mode harness would refuse the spawn step.
- **Action for v1.1:** Either (a) add `Task` to `allowed-tools` and clarify the agent-spawning is required, or (b) drop the sub-agent design and document inline WebFetch as the canonical approach. Current state is internally inconsistent.

**3. Bibkey-derived Author heuristic produces silently-wrong renderings (status: surfaced — content quality, but skill is doing its job catching them)**
- 3 of 5 arXiv entries audited had wrong first-author surnames in the heuristic (`belairagent` → "Bel-Air" but real first author is "He"; `phute2024hardpos` → "Phute" but real is "Li"; `lin2025echoleak` → "Lin" but real is "Reddy"). This matches BURN_IN_NOTES Stage 2 #2 / Stage 3 #2 already-known weakness.
- The audit skill is the right place to catch this — but a single round of `/dossier-audit` only verifies entries that match its `--focus`. With 147 entries, ~30+ rounds would be needed to fully verify. **Action for v1.1:** consider a mode `/dossier-audit --pass=author-only` that does a fast author-only sweep across all entries (no mechanism/result verification, just first-author against arXiv abstract) — a single sweep would catch the systemic heuristic miss-rate.

**4. Updating dependent files (lookup recipes / glossary) is a manual step (status: noted, working as intended but error-prone)**
- When CORRECTing "Lin et al." to "Reddy" in the entry file, the same author name appears in `README.md` lookup recipes and `00_overview.md` glossary. The skill body Phase 5 only describes editing the entry block. The agent (correctly) hunted these other occurrences via grep, but a less-careful run could leave the README/glossary stale. **Action for v1.1:** Phase 5 should explicitly say "after CORRECT, grep for the old surname across the indexed folder and update lookup recipes / glossary in the same round."

### Stage 6: /url-freshness-check (smoke)

**Result:** 146 unique URLs extracted; 140 → 200 OK; 6 → 403; 5 of the 6 are openai.com (allowlisted as bot-blocked); 1 is darkreading.com (genuinely bot-blocked but NOT on the current allowlist). 0 hard 404s. Validator passes on `url_check_report.md`.

**1. Bash URL-extraction snippet in `references/url_check_protocol.md` returns 0 matches on macOS+brew (status: surfaced — bug in reference doc)**
- The reference doc snippet uses `grep -hroE 'https?://[^[:space:]\)\]"\<]+'` with a negated character class. On macOS BSD-grep + zsh, this regex returns 0 matches against agent_index files known to contain ~146 URLs.
- Replacement that works: `grep -hroE 'https?://[a-zA-Z0-9./?=&_~%#:+-]+'` — positive char class instead of negated.
- **Why it matters:** The bash snippet IS the skill's URL extraction step. If it returns 0, the entire skill silently misreports "no URLs found" and the user thinks everything's clean.
- **Action for v1.0/v1.1:** Update `references/url_check_protocol.md` with the working positive-char-class regex. Add a smoke test to the validator (or a meta-test) that confirms the documented bash actually extracts URLs from a known-good file. **High priority — surfaces a real false-clean condition.**

**2. darkreading.com missing from allowlist (status: surfaced — minor)**
- 1 of 6 403-returning URLs is `https://www.darkreading.com/application-security/only-250-documents-poison-any-ai-model`. darkreading.com (security news site) consistently rejects HEAD + GET-with-Range from automated user-agents. Other security-news outlets in the same situation: schneier.com, krebsonsecurity.com (potentially).
- **Action:** Add `darkreading.com/*` to allowlist in `references/url_check_protocol.md`. Consider adding `schneier.com/*` and `krebsonsecurity.com/*` proactively.

**3. Default report path is `<target_folder>/url_check_report.md` (status: surfaced — design conflict with recreation_diff test)**
- Skill body says default report path is inside the target folder. This means re-running the skill replaces the prior report. For audit purposes, suggest `--report` with a date-stamped path (`url_check_2026-05-07.md`) or at the very least inline the date in the report's `Generated:` line so historical reports are distinguishable. (The current schema already requires `Generated: <date>` so this is partly handled; just calling it out.)
- **NEW (encountered during Phase 3.5):** Placing `url_check_report.md` inside `agent_index/` makes it count as an agent_index file in `test_recreated_agent_index_file_count_matches` (10 files instead of 9). For this fixture I moved the report up one level to `recreated/url_check_report.md`. For v1.1, the skill should default to writing the report OUTSIDE the target folder (e.g., `<parent>/url_check_report.md`) since the report is not a synthesis artifact. **Action for v1.1:** Update skill default + `references/url_check_protocol.md` to recommend `<parent>/` placement.

### Recreation diff (test_recreation_diff.py)

**Result on first run (2026-05-07):** 2 of 4 tests fail informatively; 2 pass.

| Test | Status | Notes |
|---|---|---|
| `test_recreated_agent_index_file_count_matches` | PASS | 9 files in both real/ and recreated/ (after moving `url_check_report.md` to `recreated/url_check_report.md` out of `agent_index/`) |
| `test_recreated_entry_counts_within_tolerance` | FAIL | recreated 23/25/28/13/19/24/15 = 147 vs real 72/82/102/81/72/90/26 = 525 → 68-84% drift |
| `test_recreated_readme_has_required_sections` | PASS | AGENT-INDEX comment + Scope boundary + Lookup recipes + Glossary all present |
| `test_recreated_section_anchors_match` | FAIL | real uses per-file letter prefixes (A1-A5 in 01, B1-B4 in 02, C1-C6 in 03, D1-D6 in 04, …); recreated uses A1-A5 in every file |

**7. Real synthesis cross-references each paper ~3-4× across files; recreation renders each entry once (status: surfaced — design gap)**
- The real `agent_index/` has 525 `**Source:**` lines across 137 unique entries (3.8× average). Cross-references appear when a paper is cited as both a primary entry in its home topic file AND a related-work mention in another file (e.g., GCG appears in 01 as the canonical white-box attack AND in 03 as the comparison baseline that defenses must beat AND in 05 as the benchmark target for HarmBench).
- The recreation rendered 147 `**Source:**` lines (1× per entry). The skill body for `/agent-index` does not specify when to cross-reference vs. when to cite once.
- **Why it matters:** Cross-referencing is editorially load-bearing — it lets future LLM agents find a paper from any of its conceptual angles. Without explicit guidance, the skill produces a sparser synthesis.
- **Action for v1.1:** Add a "cross-reference rule" section to `agent-index.md` skill body or `dual_audience_design.md` reference. Decide: should every paper be cross-referenced from N files where N = number of conceptual angles it touches? Or only the "landmark" subset?

**8. Per-file letter-prefix convention (A, B, C, D, E, F, G) for section anchors not specified in agent-index template (status: surfaced — design gap)**
- Real prompt-injection uses `## A1.` … `## A5.` in `01_direct_attacks.md`, `## B1.` … `## B4.` in `02_indirect_and_agentic_attacks.md`, `## C1.` … `## C6.` in `03_defenses.md`, etc. This makes section anchors globally unique across the synthesis (so a lookup recipe can say "see § C2." unambiguously).
- The recreated synthesis uses `## A1.` … `## A5.` in every file. The agent_index template doesn't specify the letter convention.
- **Why it matters:** Lookup recipes in the README would collide on `## A1.` if they cross-file references. Globally-unique anchors are the editorially correct choice.
- **Action for v1.1:** Add letter-prefix-per-file convention to `agent_index_README.template.md` and `agent-index.md` skill body workflow phase 5.

**Interpretation of overall gate behavior:**
- Per the continuation plan ("Discrepancies don't fail the gate; they get logged in BURN_IN_NOTES.md"), these 2 test failures are documentation of an honest fidelity gap, not a stop-ship signal.
- The 2 failures are **expected** for v1.0 given:
  1. recreation runs in 1-2 hours of LLM work vs prompt-injection's months of human curation
  2. cross-reference convention not yet specified in skills (item #7 above)
  3. letter-prefix convention not yet specified in templates (item #8 above)
- v1.1 design cycle should resolve items #7 and #8, after which recreation_diff tests should pass cleanly.

---

## Phase 5a: eval-methodology LLM eval methodology (v1.0 GATE)

**Date started:** 2026-05-07
**Output:** `~/Claude/research_eval_methodology/bib_ledger.yml`

### Stage 2: /research-gather

**Result:** 72 verified entries written to `~/Claude/research_eval_methodology/bib_ledger.yml`. Validator exits 0. Per-claim_family distribution: benchmark_agentic 18, benchmark_static 16, llm_as_judge 13, human_eval_protocol 10, holistic_framework 9, contamination_detection 4, meta_eval 2.

**Landmark paper corrections during verification (3 corrections, 12 confirmed clean):**

**1. zhuo2023contamination (arXiv:2306.05715) — bibkey + URL both wrong (status: corrected, applied)**
- The plan listed `zhuo2023contamination` at arXiv:2306.05715 as a "data contamination survey." That arXiv ID actually resolves to Hellas et al. (2023) "Exploring the Responses of Large Language Models to Beginner Programmers' Help Requests" — completely off-topic.
- The likely intended paper is Sainz et al. (2023) "NLP Evaluation in trouble: On the Need to Measure LLM Data Contamination for each Benchmark" (arXiv:2310.18018, EMNLP 2023 Findings).
- **Correction:** Registered `sainz2023contamination` at arXiv:2310.18018 (status: verified). The original `zhuo2023contamination` bibkey is dropped.
- **Why it matters:** The reverse-engineered research_plan.md contained a real attribution error (bibkey + URL both wrong). The WebFetch verification step caught it. Same self-correction pattern as Stage 1 prompt-injection BURN_IN #1 (Crescendo first-author misattribution).

**2. wei2024judgement — bibkey was a placeholder (status: replaced, applied)**
- The plan annotation said "(relevant arXiv TBD by /research-gather)". Two strong candidates surfaced: Shi et al. (2024) "Judging the Judges: A Systematic Study of Position Bias in LLM-as-a-Judge" (arXiv:2406.07791) and Chen et al. (2024) "Humans or LLMs as the Judge? A Study on Judgement Biases" (arXiv:2402.10669).
- **Correction:** Registered both — `shi2024judgejudges` (position-bias systematic study) and `chen2024judgement` (judgement biases). The placeholder `wei2024judgement` was never registered.
- **Why it matters:** When research_plan.md uses TBD placeholders for known landmarks, /research-gather has to make an editorial pick (or in this case, register both). Skill body is silent on multi-resolution case.

**3. li2023alpacaeval — first author was wrong in plan annotation (status: corrected, applied)**
- The plan listed `li2023alpacaeval` (no arXiv; tatsu-lab/alpaca_eval). The repo URL is correct, but the actual landmark paper is Dubois et al. (2024) "Length-Controlled AlpacaEval" (arXiv:2404.04475) — first author is Dubois, not Li.
- **Correction:** Registered both — `li2023alpacaeval` (the GitHub repo as a tooling artifact; no arXiv) AND `dubois2024lengthcontrolled` (the academic paper). This represents the original AlpacaEval vs. the v2.0 length-controlled iteration.
- **Why it matters:** Same as #2 — when a "landmark" is actually a project rather than a paper, the /research-gather skill has no clear guidance for whether to register the repo, the paper, or both.

**Top 5 friction observations (will inform v1.0 tag decision):**

**F1. Validator does not enforce claim_family against plan taxonomy (status: surfaced — design gap)**
- `validators/bib_ledger.py` only checks claim_family is a non-empty string. The skill body Phase 6 says "All claim_family values appear in the plan's taxonomy" but the validator can't verify this — it has no access to the plan.
- **Why it matters:** A typo (`benchmark_static` vs `benchmark-static` vs `benchmarks_static`) would silently pass. For v1.0 I cross-checked manually but a typo-prone agent would let it through.
- **Action for v1.1:** Either (a) pass `--plan` to the validator and have it parse the taxonomy section, or (b) declare a single canonical taxonomy file under `references/` and have validator check against that. Option (a) is safer for multi-topic ledgers.

**F2. Skill body silent on bibkey collision resolution when one slug fits two papers (status: surfaced — design gap)**
- E.g., `kim2024prometheus2`, `kim2023prometheus`, `kim2024biggenbench`, `kim2024evalverse` all share Kim/year — fine, slugs distinguish. But `liu2023geval` vs `liu2023evalplus` vs `liu2023agentbench` all share Liu/2023 — also fine via slugs. The skill body says "Use slug variations" but doesn't say what to do when the same paper has multiple natural slugs (e.g., `panickssery2024selfpref` vs `panickssery2024recognize`).
- **Why it matters:** The choice affects whether two agents working on the same topic at different times produce identical bibkeys. Reproducibility hazard.
- **Action for v1.1:** Add a "canonical slug derivation" rule to citation_rules.md — e.g., "use the most distinctive 1-3 nouns from the title, lowercase, no spaces."

**F3. The "1-3 word slug" rule is ambiguous for compound benchmark names (status: surfaced — minor)**
- For `dubois2024lengthcontrolled` I picked `lengthcontrolled` (one compound). For `kim2024biggenbench` I picked `biggenbench`. For `bai2024mtbench101` I picked `mtbench101` (alphanum only). The rule says "1-3 lowercase words" but treats hyphenated/compound benchmark names ambiguously. I defaulted to "rejoin without hyphens" which violates the strict-word interpretation but reads better.
- **Action for v1.1:** Clarify in citation_rules.md that compound names from benchmarks are kept as one slug if removing hyphens preserves clarity.

**F4. `--cache-pdfs` was not requested but the skill body Phase 5 has no opt-out signal in workflow (status: surfaced — minor)**
- The user's invocation prompt didn't include `--cache-pdfs`, so I correctly skipped Phase 5. But the skill body lists Phase 5 as a numbered step in "## Workflow" and only mentions it's optional inside the phase body. A less careful agent might attempt the download step.
- **Action for v1.1:** Move Phase 5 to a "Optional phases" subsection or prefix the heading with "(optional)".

**F5. Vendor blog and GitHub URL entries don't have an "arXiv ID" field, so /dossier-build's downstream rendering loses author information (status: surfaced — recurrence of Stage 2 #2)**
- 5 of 72 entries are non-arXiv: `openai2024swebenchverified` (OpenAI blog), `zheng2023chatbotarenablog` (LMSYS blog), `lmsys2024hardprompts` (LMSYS blog), `li2024arenahard` (LMSYS blog), `li2023alpacaeval` (GitHub), `gao2023lmevalharness` (GitHub), `huggingface2024openllmleaderboard2` (HF Space). These survive validation but the bibkey-heuristic for Authors used downstream will be a guess (e.g., "lmsys2024hardprompts" → "LMSYS"? "LMSys"? a real human first author?).
- **Why it matters:** Same gap noted in Phase 3.5 prompt-injection BURN_IN Stage 2 #2 / Stage 3 #2. The schema is too minimal for /dossier-build without WebFetch round-trips.
- **Action for v1.1:** Either expand the schema with optional `authors_display` field that /research-gather populates from the source page, OR have /dossier-build mandatorily WebFetch each entry once.

**Time spent:** ~45 minutes (mostly WebSearch + WebFetch on 15 landmarks plus ~50 broader sources).

**Example bibkeys with brief justification:**
- `dubois2024lengthcontrolled` — first-author surname (Dubois), year (2024), 1-word slug capturing distinctive contribution (length-controlled debiasing). Replaces incorrect `li2023alpacaeval` paper attribution from plan.
- `shi2024judgejudges` — Shi (2024), distinctive 2-word slug from title ("Judging the Judges"). Resolves the plan's TBD placeholder for `wei2024judgement`.
- `panickssery2024selfpref` — Panickssery (2024), 1-word slug `selfpref` (self-preference). Captures the canonical bias type even though title says "recognize and favor."
- `oren2023contamination` — Oren (2023), 1-word slug `contamination`. Standard form for the canonical "Proving Test Set Contamination" paper.
- `kapoor2025hal` — Kapoor (2025, ICLR 2026), 1-word slug `hal`. Per citation_rules.md, year is arXiv submission year; recent post-cutoff entries flagged with `(post-2025; recheck)` if used in dossier prose.

### Stage 3: /dossier-build

**Result:** 5 dossier files written to `~/Claude/research_eval_methodology/dossier/` (`01_static_benchmarks.md` 16 entries, `02_agentic_benchmarks.md` 18, `03_human_eval.md` 10, `04_llm_as_judge.md` 13, `05_holistic_and_contamination.md` 15) plus `_dossier_readme.md`. Total 72 entries; matches bib_ledger count exactly. `validators/dossier.py` exits 0.

**Friction observations specific to eval-methodology (versus prompt-injection Phase 3.5):**

**1. Naturally clean file split (status: positive — no friction)**
- eval-methodology's research_plan.md sub-areas A1-A5 mapped 1:1 to claim_family values, and the final 5-file split (with A5 absorbing both holistic_framework and contamination_detection plus meta_eval) needed no editorial wrestling. By contrast prompt-injection had heterogeneous content forcing 7 dossier files. v1.0 takeaway: when the plan's sub-areas align with claim_family taxonomy, the split is mechanical.

**2. Bibkey-heuristic Authors rendering succeeded for ~93% of eval-methodology entries (status: improved over prompt-injection)**
- Of 72 entries, 5 are vendor / corporate blogs (`zheng2023chatbotarenablog`, `lmsys2024hardprompts`, `li2024arenahard`, `openai2024swebenchverified`, `huggingface2024openllmleaderboard2`). The bibkey stem doesn't yield a person — I rendered as `LMSYS team`, `OpenAI`, `HuggingFace`, `EleutherAI` per the corporate-author convention noted in prompt-injection Stage 3 #2.
- The other 67 entries' bibkey-stems matched real first-author surnames cleanly (verified spot-checks during render). eval-methodology has fewer pseudonym / hyphenated-surname / pre-2018 papers than prompt-injection, so the heuristic miss-rate is lower.
- **Recurring friction (not new):** still no `authors_display` field in bib_ledger; same v1.1 design item as Phase 3.5 Stage 3 #2.

**3. The "verbatim title" rule fights with display-name brevity in 5-bullet entries (status: surfaced — minor)**
- e.g., for `zheng2023mtbench` the dossier-table title is "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena" but the agent-index 5-bullet display name is "MT-Bench" (the practitioner handle). citation_rules.md § "Verbatim title rendering" says the dossier preserves verbatim while 5-bullet display names "can shorten to a recognizable handle." This worked but needs the agent to make ~10 such handle-shortening calls for eval-methodology (e.g., GAIA, GSM8K, MMLU, EvalPlus, OSWorld, WebArena). No skill-body guidance on which canonical handle to pick when the paper has multiple short names (e.g., HumanEval vs Codex paper title).
- **Action for v1.1:** Add a "common handles" table to citation_rules.md or templates/5_bullet_entry.template.md.

**4. Validator's column-5 prefix list works fine for eval-methodology (status: improvement vs prompt-injection)**
- eval-methodology entries are mostly arXiv preprints or GitHub repos, so column 5 = "GitHub" naturally fits all rows including blog-only entries (use "—"). prompt-injection had standards PDFs and vendor product pages where the natural column header would be "URL" or "Doc URL" — no such friction in eval-methodology. v1.0 takeaway: the strict column-5 prefix list works for paper-heavy dossiers; the v1.1 widening question (prompt-injection Stage 3 #1) only matters for vendor/standards-heavy volumes.

**5. The "1 entry per dossier row" rule fits eval-methodology cleanly with no cross-listing (status: positive — no friction)**
- Unlike prompt-injection (where ~6 entries legitimately belonged in two topic files: GCG, NeMo Guardrails, BIPIA, etc.), eval-methodology's 72 entries each have exactly one natural primary file. Cross-references are handled in the agent-index lookup recipes rather than duplicating dossier rows. prompt-injection Stage 3 #3 friction does not recur.

**Time spent (Stage 3):** ~25 minutes (~5 minutes per dossier file plus readme).

### Stage 4: /agent-index

**Result:** 7 files written to `~/interview_prep_series/docs/research/eval_methodology_synthesis/` (`00_overview.md`, 5 topic files, `README.md`). 72 `**Source:**` bullets total — matches bib_ledger and dossier exactly. README has 26 lookup recipes and 28 glossary terms (both within target ranges of 15-20 and 20-30 respectively). `validators/agent_index.py` exits 0.

**Friction observations specific to eval-methodology:**

**6. Letter-prefix-per-file convention applied without template support (status: applied but un-templated)**
- Per the user's prompt instructions, I used A1-A4 in `01`, B1-B4 in `02`, C1-C4 in `03`, D1-D4 in `04`, E1-E4 in `05` so cross-file lookup recipes are unambiguous. The `agent_index_README.template.md` and `agent-index.md` skill body do NOT specify this convention — same gap as prompt-injection Phase 3.5 Stage 4 #8. **Repeats from prompt-injection; high-priority v1.1 fix.**

**7. The "no LLM-generated specifics" rule is heavily-tested by eval-methodology because every entry is a benchmark with a numeric headline figure (status: surfaced — content rule worked correctly)**
- Many eval-methodology entries have iconic numbers (MMLU "57 subjects", GAIA "466 questions", HumanEval "164 problems", MATH "12,500 problems", BIRD "95 databases"). I confirmed each cited number against the bib_ledger title, the abstract URL pattern, or the standard reference statement. Several "common knowledge" numbers I declined to cite specifically because I couldn't point at an abstract excerpt (e.g., MMLU's "57" appears in title; MATH's 12,500 appears in title; HumanEval's 164 does NOT appear in title and I generalized to "Hand-written Python programming problems" without the count). This is the rule working as designed — but it required active discipline because plausible numbers came to mind for entries where the abstract verification was uncertain.
- **Action for v1.1:** Add an explicit "if the canonical headline number is in the title, you may cite it; otherwise generalize" clarifier in citation_rules.md.

**8. Dossier-to-synthesis information loss for "Key contribution" column (status: surfaced — minor)**
- Dossier table has 7 columns including "One-line description" and "Key contribution" (two distinct cells). The agent-index 5-bullet entry has only "Mechanism" and "Result" bullets — same 2-axis structure but with somewhat different semantic load. For ~30% of entries the dossier "Key contribution" was a slight rephrasing of "One-line description" (prompt-injection Stage 3 #4 noted this for non-paper entries; in eval-methodology it recurred for some paper entries too — e.g., when the paper's key contribution IS the dataset itself, the description and contribution end up similar).
- **Action for v1.1:** Either tighten the editorial guidance in dossier_table.template.md to require distinct content in cols 6+7, OR collapse to a single "Description" column for paper-heavy dossiers.

**9. Status-flag rendering: `(vendor blog)` and `(post-2025; recheck)` flags work but are stored on the line WITHIN the Status bullet, conflicting with the canonical-order check (status: surfaced — false-alarm risk)**
- I rendered vendor blog entries as `**Status:** (vendor blog) Verified.` which is two status flags concatenated. The validator only checks bullet ORDER (Source/Code/Mechanism/Result/Status), not the content of the Status bullet itself, so this passed. But a stricter validator could mistakenly read `(vendor blog) Verified` as two separate flags or fail an exact-match status enum.
- **Action for v1.1:** Add a brief example to `5_bullet_entry.template.md` showing how to combine `(vendor blog)` + `Verified` (e.g., comma-separated, or as a precedence rule). Same friction would recur for `(post-2025; recheck) Verified` combos.

**10. Validator's footer-count check is hidden behind `ENTRY_COUNT_FOOTER_RE` and only fires if a footer exists (status: surfaced — silent skip)**
- I did not include a `Total entries: 72` footer in any synthesis file — the validator therefore silently skips the count-consistency check. The 72-entry count is verified manually via grep but a future agent who omitted the footer could quietly under- or over-count. **Action for v1.1:** Either make the footer mandatory in the README template, or add a directory-level cross-file count to `validators/agent_index.py`.

**Time spent (Stage 4):** ~25 minutes (~3-4 minutes per topic file plus 8 minutes on README).

**Total time spent (Stages 3+4):** ~50 minutes.

**Whether anything blocks v1.0 tag:** No. All validators exit 0. Output structurally matches the templates. Friction items 6 (letter-prefix convention not in template) and 9 (status-flag composition) are recurring/known and consistent with prompt-injection Phase 3.5 — neither blocks v1.0; both go in the v1.1 backlog. Items 3 (display-name canonical handles), 7 (no-LLM-specifics edge cases), and 8 (description vs key-contribution overlap) are new eval-methodology-surfaced items deserving v1.1 design attention.

### Stage 5: /dossier-audit (1 round, smoke)

**Result on smoke run (2026-05-07):** Round 1 against `~/interview_prep_series/docs/research/eval_methodology_synthesis/` with focus "benchmark version numbers and leaderboard freshness". Verified 5 entries via WebFetch: MMLU-Pro (10 options), GAIA (466 questions), MT-Bench (80 multi-turn), AlpacaEval 2.0 / Length-Controlled, SWE-bench Verified (500 instances). Findings: 0 DROP / 1 CORRECT / 0 FLAG / 4 SPOT-CHECK PASSED. Both validators (`audit_trail.py`, `agent_index.py`) exit 0 after edits. Time spent: ~6 minutes (within ≤8 minute budget; 4 WebFetches + 1 WebSearch within ≤5+≤2 budget).

**1. Vendor-blog 403 forces audit fallback to WebSearch (status: surfaced — recurring eval-methodology wrinkle)**
- The OpenAI SWE-bench Verified blog (https://openai.com/index/introducing-swe-bench-verified/) returned 403 to WebFetch despite the entry's `(vendor blog) Verified` flag implying it had been fetched at gather time. The audit fell back to WebSearch summary (which surfaced 500-instance + 93-developer + Aug-2024 numbers). Same allowlist gap noted in Phase 3.5 Stage 6 (#1, openai.com bot-blocking).
- **Why it matters:** When a vendor blog is the primary source for a benchmark entry AND is bot-blocked, audit-time verification can only reach it indirectly (search snippets, third-party rehosts). The `(vendor blog)` flag should arguably escalate to `(vendor blog; bot-blocked at audit)` so downstream readers know the content was not directly re-verified.
- **Action for v1.1:** Either (a) extend `citation_rules.md` to add a `(vendor blog; bot-blocked)` sub-flag for openai.com / lmsys.org / similar domains, or (b) require the audit skill to record each WebFetch HTTP status in the audit-trail note.

**2. Project-version vs. paper-title disambiguation isn't covered in entry-render guidance (status: surfaced — content quality)**
- The Dubois et al. (2024) entry was titled `**Length-Controlled AlpacaEval (AlpacaEval 2.0)**` — the paper's title is "Length-Controlled AlpacaEval"; "AlpacaEval 2.0" is a separate project-version label on the AlpacaEval site (referring to the GPT-4-Preview baseline+annotator release, distinct from the LC bias-correction). The parenthetical conflated two related but mechanistically distinct things. The audit caught it via WebFetch on the paper abstract + the project site.
- **Why it matters:** Several eval-methodology entries pair an arXiv paper with a community-maintained leaderboard or project (AlpacaEval, Chatbot Arena, SWE-bench, MT-Bench). The render-time decision "should the entry title use the paper title, the project name, or both?" is unspecified in `5_bullet_entry.template.md`. The default of putting the project name parenthetically risks conflation when the project has its own version numbering.
- **Action for v1.1:** Add an editorial rule to `citation_rules.md`: when an arXiv paper introduces a methodology that a separate community project then versions independently (e.g., LC AlpacaEval vs. AlpacaEval 2.0; SWE-bench paper vs. SWE-bench Verified; MT-Bench paper vs. live leaderboard), keep the paper title as the entry title and put project-version disambiguation in the Mechanism bullet, not the title.

**3. The four-bucket audit-trail format (DROP/CORRECT/FLAG/SPOT-CHECK) reads better than the three-bucket reference template (status: confirms prompt-injection Stage 5 #1)**
- The user's invocation prompt requested four buckets; `audit_protocol.md` § "Audit-trail note format" lists only three. The four-bucket form is more informative because it surfaces verification *coverage* (4 spot-checks PASSED) alongside *changes* (1 corrected). prompt-injection Stage 5 #1 already flagged this as a v1.1 canonicalization decision; eval-methodology confirms the four-bucket form is the more useful one in practice.
- **Action for v1.1:** Same as prompt-injection Stage 5 #1 — make four-bucket canonical in both `dossier-audit.md` Phase 6 and `references/audit_protocol.md`.

**Time spent (Stage 5):** ~6 minutes (4 WebFetches + 1 WebSearch + 2 inline Edits + 2 validator runs).

### Stage 6: /url-freshness-check (smoke)

**Result (2026-05-07):** 122 unique URLs extracted; 120 → 200 OK; 1 → 403 (openai.com — allowlisted as bot-blocked); 1 → 404 (`https://github.com/huggingface/open_llm_leaderboard` — repo archived June 2024). Hard 404 fixed inline (replaced with `EleutherAI/lm-evaluation-harness` + archival note in Mechanism bullet); both validators still pass post-edit. URL report written to `~/Claude/research_eval_methodology/url_check_report.md` (per Phase 3.5 Stage 6 #3 finding — outside the agent_index folder so it doesn't inflate file counts in any future diff test).

**1. Confirms Phase 3.5 Stage 6 #1 — bash regex from `references/url_check_protocol.md` returns 0 URLs (status: confirmed — high-priority v1.0 backlog)**
- Same broken regex as Phase 3.5; same workaround (positive char class `[a-zA-Z0-9./?=&_~%#:+-]+`). Two consecutive dogfood runs hit the same bug → confirms this is a real fix needed for v1.0 (or at minimum tagged as a known issue at v1.0 with the workaround documented in toolkit README).

**2. Hard 404 in synthesis caught by url-check (status: validates the skill's value)**
- `huggingface/open_llm_leaderboard` was a plausible-sounding URL that the gather subagent included unchecked. The url-freshness-check stage caught it; the inline fix preserves the entry by replacing with the actual underlying engine repo. **This is the kind of finding the skill is designed to surface** — confidence that the toolkit catches real link rot.

**Time spent (Stage 6):** ~3 minutes (122 URLs HEAD-checked in parallel chunks + 1 inline fix + re-validation).

### Phase 5a summary — v1.0 readiness

| Metric | Value |
|---|---|
| Stages run | 6 (research-plan + research-gather + dossier-build + agent-index + dossier-audit + url-freshness-check) |
| Validators passing | 6 of 6 |
| Total entries | 72 |
| Total `**Source:**` lines in synthesis | 72 |
| Lookup recipes in README | 26 |
| Glossary terms | 28 |
| Landmark-paper corrections caught | 3 of 15 (zhuo→sainz; placeholder→shi+chen; alpacaeval-attribution) |
| Audit corrections | 1 (LC AlpacaEval title disambiguation) |
| URL fixes | 1 (open_llm_leaderboard 404 → lm-evaluation-harness) |
| Friction items added to BURN_IN | 13 (Phase 5a §§ 2-6) |
| `make test` regression | 18 pass + 2 fail (prompt-injection recreation_diff baseline unchanged) |
| **v1.0 ship gate** | **READY** — both validator-passing and friction-tracked. No blockers. |

---

## Phase 5b: PEFT PEFT (post-v1.0)

**Date:** 2026-05-07
**Output:** `~/interview_prep_series/docs/research/peft_synthesis/` (7 files, 67 entries)
**Topic:** parameter-efficient fine-tuning (LoRA family, adapters, prompt-based PEFT, IA³, surveys)

### Stage 2: /research-gather

**1. F2 LoRA-family density exceeded plan target (status: noted, no action)**
- Plan target was 18-25 lora_variant entries; subagent found 31 verified entries. The LoRA-family literature has branched extensively (DyLoRA, AdaLoRA, QLoRA, DoRA, VeRA, LoRA+, LoRA-FA, LoftQ, ReLoRA, GaLore, PiSSA, X-LoRA, MoLE, LoRAMoE, MoSLoRA, LoraHub, MultiLoRA, Delta-LoRA, BitDelta, Spectral, OLoRA, Tied-LoRA, LongLoRA, FourierFT, Punica, S-LoRA, LoRA Land, LoRA Learns Less, Chain of LoRA + base LoRA + Aghajanyan intrinsic-dim).
- **Action:** None. Plan ranges should be advisory, not strict. A skill-prompt note that the gather skill's targets are floors-not-ceilings would be a v1.1 micro-tweak.

**2. Bibkey diacritics round-trip cleanly (status: confirmed, no action)**
- `rucklé2021adapterdrop` (Andreas Rücklé) preserves the `é` through bib_ledger → dossier → agent_index → validator. UTF-8 path is fine end-to-end.

**3. Year-of-record ambiguity for arXiv-vs-venue split (status: surfaced — minor)**
- Several papers were on arXiv in year N and accepted at a conference in year N+1 (AdapterFusion: 2020 arXiv → EACL 2021; AdapterDrop: 2020 arXiv → EMNLP 2021; UniPELT: 2021 arXiv → ACL 2022; P-tuning v2: 2021 arXiv → ACL 2022). The subagent picked venue/publication year, matching eval-methodology precedent. One inconsistency: `aghajanyan2020intrinsic` kept 2020 (arXiv submission year, not ICLR 2021 publication year) because the literature consistently cites it as 2020.
- **Why it matters:** The bibkey "year" is sometimes a citation choice, not a fact about the paper. Documenting the rule (default to venue/publication year unless community-standard citation says otherwise) would help future runs.
- **Action:** Add a one-line guidance in `/research-gather` skill: "for bibkey year, prefer venue/publication year; fall back to arXiv-submission year only when literature consistently cites that year."

### Stage 3: /dossier-build

**1. dossier-build subagent guesses GitHub URLs that often 404 (status: HIGH PRIORITY for v1.1)**
- 7 of 67 GitHub URLs guessed by the dossier-build subagent were hard 404s when checked at Stage 6. All 7 followed the pattern "use the firstauthor handle + repo-name-derived-from-paper-slug." Real authors don't always own a `<lastname>/<paper-slug>` repo:
  - X-LoRA: guessed `EPFL-IMOS/X-LoRA`, real repo is `EricLBuehler/xlora`.
  - Spectral Adapter: guessed `Forence/Spectral-Adapter`, real repo is `pilancilab/spectral_adapter` (lab repo, not first-author repo).
  - LoRA Learns Less: guessed `tatsu-lab/lora_less`, real repo is `danbider/lora-tradeoffs`.
  - OFT: guessed `Zeju-Qiu/oft` (first author handle), real available impl is community `tripplyons/oft`.
  - OLoRA, MoLE, PEPP: no canonical author repo exists — heuristic should have produced `—`, not a guess.
- **Why it matters:** Heuristic-guessed URLs that 404 are a worst-case failure mode (looks authoritative, isn't). Better to render `—` and let the audit/url-check stage discover and fill.
- **Action for v1.1:** Add explicit guidance in `/dossier-build` skill body: "GitHub cell — write `—` unless you have direct knowledge of the repo path. Do NOT guess from `<author>/<paper-slug>` patterns; many papers have lab-repo paths (e.g., `pilancilab/spectral_adapter`), community-implementation paths (e.g., `tripplyons/oft`), or no repo at all."

**2. dossier subsection density choice (status: noted, no action)**
- The 31 lora_variant entries were split into 6 sub-sections (B1-B6). The validator only enforces table schema, not sub-section count. The subagent's 6-way split was reasonable; a 4-way split would also have validated. Editorial judgment, not skill-prompt issue.

### Stage 4: /agent-index

**1. Stage 3 propagation error caught at Stage 4 (status: positive, design working as intended)**
- The Stage 3 dossier accidentally listed `rabeehk/compacter` (Compacter's repo) as the Code link for `aghajanyan2020intrinsic` (intrinsic-dimensionality paper). The Stage 4 subagent caught this during 5-bullet rendering and rewrote Code to `—` with status flag `(no widely-known repo)` rather than propagating the bad link.
- **Why it matters:** Stage-4-as-second-eye on Stage-3 output is a useful default. Confirmed working.

**2. Cross-vol linking convention worked (status: confirmed)**
- Each entry has one primary location; cross-vol overlaps with prompt-injection (none in this run) and eval-methodology (e.g., calibration of PEFT'd models would touch both PEFT + calibration) are surfaced via the README scope-callout, not via inline duplication. Same pattern as eval-methodology.

### Stage 5: /dossier-audit (round 1)

**1. Audit confirmed the Stage-3-flagged uncertainties were mostly accurate (status: confirmed)**
- 16 spot-checks PASSED (DoRA ICML 2024 Oral, GaLore ICML 2024 Oral, QLoRA NeurIPS 2023 Oral, etc. all confirmed via OpenReview/conference websites). 3 CORRECTs (DyLoRA repo path, LongLoRA Spotlight status, LoRA Land tech-report flagging). 0 DROPs.
- **Why it matters:** The Stage-3 `(uncertain venue)` flag is well-calibrated — uncertainties are flagged honestly, and verification mostly confirms. Audit time is low because honest flagging localizes the work.

### Stage 6: /url-freshness-check

**1. Subagent timeout with bash-tool sandboxing (status: surfaced — workflow)**
- The url-freshness-check subagent timed out at the WebFetch verification step (over 120 URLs). Falling back to inline `curl -sS -L` bulk-check was much faster (60 seconds for all 117 URLs) and surfaced the same 7 hard-404s. Subagent path is more thorough (uses WebFetch which respects robots.txt-style allowlists) but slower.
- **Action:** Document the inline-curl fallback as a recipe for large URL sets. v1.1 might add an explicit "if N>50 URLs, use inline curl" branch in the skill body.

**2. URL-extraction regex BURN_IN finding from eval-methodology confirmed again (status: applied)**
- The positive char-class form `[a-zA-Z0-9./?=&_~%#:+-]+` works correctly on macOS grep. The negative form `[^[:space:]\)\]"\<]+` silently returns 0 URLs (high-priority bug from Phase 5a #2). Confirming the v1.0 fix-recipe applies here.

### Phase 5b summary table

| Metric | Value |
|---|---|
| Date | 2026-05-07 |
| Stages run | 6 (research-plan inline + research-gather + dossier-build + agent-index + dossier-audit + url-freshness-check) |
| Validators passing | 6 of 6 |
| Total entries | 67 |
| Total `**Source:**` lines in synthesis | 67 |
| Lookup recipes in README | 32 |
| Glossary terms | 30 |
| Landmark-paper corrections caught | 0 of 14 (all 14 known landmarks resolved cleanly via WebFetch) |
| Audit corrections | 3 (DyLoRA repo, LongLoRA Spotlight flag, LoRA Land tech-report flag) + 1 FLAG |
| URL fixes | 7 hard-404 GitHub repo fixes (HIGH PRIORITY v1.1 finding — see Stage 3 #1) |
| Friction items added to BURN_IN | 8 (Phase 5b §§ 1-8 across stages) |
| `make test` regression | 18 pass + 2 fail (prompt-injection recreation_diff baseline unchanged; identical to v1.0 baseline) |
| New material tweaks applied to skills | 0 (highest-priority finding deferred to v1.1) |
| **v1.1 tag bump** | **NO** — findings are recorded but no skill-body edits applied yet; defer to consolidated v1.1 PR after calibration. |

---

## Phase 5c: calibration calibration & uncertainty (post-v1.0)

**Date:** 2026-05-07
**Output:** `~/interview_prep_series/docs/research/calibration_synthesis/` (8 files, 88 entries)
**Topic:** calibration methods, calibration metrics, conformal prediction, UQ, OOD detection, LLM-specific calibration

### Stage 2: /research-gather

**1. Stage 2 subagent skipped per-entry WebFetch verification (status: HIGH PRIORITY for v1.1)**
- The subagent populated 88 entries but explicitly reported it did NOT WebFetch each one due to time-budget pressure (~45-60 min for 88 fetches at ~30s each = budget overrun). It marked all entries `verified` based on memory of the literature, then flagged the trade-off honestly in its final report.
- **Why it matters:** "Verified" status is supposed to mean "WebFetch-confirmed first-author + year + title." When status drift to "high-confidence-from-memory" it loses its meaning. Stage 5 audit caught 1 substantive misattribution (Yin → Zhang at arXiv:2305.18153) that per-entry WebFetch would have caught earlier.
- **Action for v1.1:** Either (a) loosen `/research-gather` skill to default to `unverified`, with `verified` only for entries that pass per-entry WebFetch; or (b) explicitly time-budget the gather skill ("expect ~30s per entry; if time-pressed, prefer fewer-but-verified to more-but-memory"); or (c) add a "fast verification" path (just check the arXiv ID resolves to non-404, even without title-matching). All three address the false-positive `verified` risk.

**2. Subagent self-counting drift (73 vs 88) (status: surfaced — minor)**
- Stage 2 subagent's top-line said "73 entries" but its own per-claim_family breakdown summed to 88. The actual file had 88. The Stage 3 subagent caught the discrepancy and rendered all 88.
- **Why it matters:** Subagent self-reports can be inconsistent with their own work. For decisions that depend on total counts (BURN_IN reporting, downstream pipeline guards), prefer a programmatic count from the validator output rather than the subagent's narrative.
- **Action:** In v1.1, add a count-check assertion to `/research-gather` skill: "your final report's total entry count must match the YAML file's actual count; mismatch → re-count before reporting."

**3. Pre-2010 classical papers without arXiv (status: confirmed pattern, no action)**
- 8 entries (Brier 1950, DeGroot 1983, Platt 1999, Zadrozny 2001/2002, Niculescu-Mizil 2005, Vovk 2005, Papadopoulos 2002) used non-arXiv URLs (DOI, JSTOR, AMS journal, Springer). The validator accepted these because the URL is intrinsically venue-stable.
- **Why it matters:** Confirms the validator's URL-or-bibkey check is permissive enough for older work without arXiv preprints.

### Stage 3: /dossier-build

**1. Six-file layout exercises letter-prefix anchors A-F (status: clean)**
- calibration's 6 dossier files use anchors A1-A4, B1-B3, C1-C4, D1-D4, E1-E3, F1. No collisions. Confirms the per-file letter-prefix convention scales beyond PEFT's A-E.

**2. dossier-build subagent held the GitHub-`—` line (status: applied — PEFT BURN_IN finding propagated)**
- Stage 3 subagent explicitly refused to guess `<author>/<paper-slug>` GitHub patterns for repos it didn't directly know, marking `—` for ~28 entries instead. This is the v1.0/v1.1-tracked behavior change from PEFT Stage 6 finding (Phase 5b §1).
- **Why it matters:** Confirms the BURN_IN finding from PEFT was actionable in-prompt — feeding the rule into the subagent's prompt was sufficient to change behavior. v1.1 PR can codify this in the skill body.

### Stage 4: /agent-index

**1. 88 entries scaled cleanly to dual-audience format (status: clean)**
- README has 32 lookup recipes + 36 glossary terms — slightly larger than PEFT's 32+30 because calibration covers 6 sub-areas vs PEFT's 5. No schema strain.

### Stage 5: /dossier-audit (round 1)

**1. arXiv-ID spot-check protocol added (status: applied)**
- Audit subagent ran 10 random arXiv-ID checks (in addition to focus-area attribution checks). Result: 10/10 PASSED — no transposition errors slipped past Stage 2's memory-based "verified" marking. While the sample is small, it suggests memory-based arXiv-ID recall is reliable for foundational calibration / OOD literature (Guo, Lakshminarayanan, Hendrycks, Lee, Lin, Lei, Blundell, Kull, Angelopoulos, Ming).
- **Why it matters:** Partly tempers the Stage 2 §1 concern. The remaining failure mode is on more obscure / newer LLM-era papers (where Stage 5 caught the Yin→Zhang error). Recommendation: in v1.1, the Stage 5 audit should default to a 10-entry random arXiv-ID spot-check whenever Stage 2 reports "memory-based verification."

**2. Display-title drift (status: surfaced — minor)**
- 2 of 3 corrections were practitioner-nickname display titles vs paper-actual titles ("Verbalized Confidence" vs "Teaching Models to Express Their Uncertainty in Words"; "LMs Mostly Know" vs "Language Models (Mostly) Know What They Know"). Stage 3+4 substituted memorable nicknames; audit flagged.
- **Action for v1.1:** Add a synthesis-time rule to `/dossier-build` skill: "display title = arXiv title verbatim; do not abbreviate."

### Stage 6: /url-freshness-check

**1. PEFT's GitHub-guess BURN_IN finding reproduced (status: confirmed — HIGH PRIORITY for v1.1)**
- 3 hard-404 GitHub URLs guessed despite the v1.0 dossier-build subagent doing the right thing for ~28 cases. Two of three (Ashukha 2020 `bayesgroup/pytorch-ensembles`, Xiong 2024 `MiaoXiong2333/UQ-NLG`) are slug-guesses; one (Brier 1950 Source) was a DOI URL with `<>` characters that broke URL parsers.
- **Why it matters:** Confirms PEFT finding for the second time across two domains. The dossier/agent-index pipeline produces ~3% hard-404 rate on guessed GitHub URLs (3/137 calibration; 7/117 PEFT). v1.1 needs to codify "no `<author>/<paper-slug>` guesses, mark `—`."
- **Action for v1.1**: Codify the dash-default rule in `/dossier-build` and `/agent-index` skill bodies as a hard rule, not a suggestion.

**2. ResearchGate / ACM / JSTOR consistent bot-block (status: noted, no action)**
- 3 of 137 URLs return 403 to curl-style requests but are valid in browsers (researchgate.net, doi.org/10.1145, doi.org/10.1198). For citation purposes these are stable; for click-through readers may need browser access. Existing allowlist already covers this pattern.

**3. Old DOI URLs with `<` `>` characters break URL parsers (status: applied — minor BURN_IN)**
- Brier 1950's full DOI form `10.1175/1520-0493(1950)078<0001:VOFEIT>2.0.CO;2` contains URL-unsafe characters. Replaced with the AMS / ADS abstract URL. Future runs should percent-encode such DOIs or use alternate stable URLs.

### Phase 5c summary table

| Metric | Value |
|---|---|
| Date | 2026-05-07 |
| Stages run | 6 (research-plan inline + research-gather + dossier-build + agent-index + dossier-audit + url-freshness-check) |
| Validators passing | 6 of 6 |
| Total entries | 88 |
| Total `**Source:**` lines in synthesis | 88 |
| Lookup recipes in README | 32 |
| Glossary terms | 36 |
| Landmark-paper corrections caught | 0 of 17 (all 17 known landmarks resolved cleanly) |
| Audit corrections | 3 (Yin→Zhang misattribution; Lin/Kadavath display-title fixes) + 0 FLAGS |
| arXiv-ID spot-checks | 10/10 PASSED |
| URL fixes | 3 hard-404s (Brier DOI URL-unsafe; 2 GitHub-slug guesses — same pattern as PEFT) |
| Friction items added to BURN_IN | 9 (Phase 5c §§ 1-9 across stages) |
| `make test` regression | 18 pass + 2 fail (prompt-injection recreation_diff baseline unchanged; identical to v1.0 + PEFT baselines) |
| New material tweaks applied to skills | 0 (highest-priority findings consolidated for v1.1 PR) |
| **v1.2 tag bump** | **NO** — findings recorded; consolidated v1.1 PR (post-PEFT+calibration) is the right next step. |

### Cross-vol findings consolidated for v1.1

The PEFT + calibration dogfood runs surfaced four reproducible v1.1 design items:

1. **GitHub-URL guessing** (PEFT §3.1, calibration §6.1) — codify dash-default rule in `/dossier-build` + `/agent-index` skill bodies. **Highest priority.**
2. **Stage 2 verification protocol** (calibration §2.1) — either default-`unverified` or explicit time-budget guidance, to prevent memory-based "verified" inflation.
3. **Stage 5 default audit protocol** (calibration §5.1) — make 10-entry random arXiv-ID spot-check the default whenever Stage 2 reports memory-based work.
4. **Display-title preservation** (calibration §5.2) — synthesis-time rule: display title = arXiv title verbatim.

These four items represent the post-v1.0 design backlog. A consolidated v1.1 PR addressing #1-#4 plus the existing v1.0 backlog (URL-extraction regex, bibkey-heuristic Authors gap, per-file letter-prefix in templates) is the right next-cycle artifact.

---

## v1.1 — applied 2026-05-07

All cross-vol findings above are now fixed in skill bodies, templates, validators, and tested.

### Changes shipped

**Validators**
- `validators/bib_ledger.py` — added optional `authors` / `venue` / `code_url` fields (string, validated when present); added arXiv URL canonical-form check (rejects `/pdf/` URLs and malformed IDs); added URL-format check on `code_url` when present.
- `validators/{research_plan,bib_ledger,dossier,agent_index,audit_trail,url_check_report}.py` — added `if __package__ in (None, "")` path-injection so `python validators/<x>.py path` works without `pip install -e .` or `python -m`. Was a silent friction pre-v1.1.

**Templates**
- `templates/bib_ledger.template.yml` — documented optional `authors` / `venue` / `code_url` fields with comment guidance ("omit field entirely when uncertain; do NOT guess `<author>/<paper-slug>` patterns").
- `templates/dossier_table.template.md` — added explicit per-file letter-prefix anchor convention (A/B/C/D/E/F by file position).
- `templates/agent_index_README.template.md` — added cross-vol overlap convention ("pick ONE primary location, do NOT duplicate") and per-file anchor reference.

**Skills**
- `.claude/skills/research-gather.md` — Phase 3 now opportunistically populates `authors`/`venue`/`code_url` when the abstract is already WebFetched. Phase 6 codifies strict `unverified` → `verified` promotion (must have WebFetch evidence). Added count-assertion: subagent's narrative entry-count must match `grep -c "^- bibkey:"` of the file.
- `.claude/skills/dossier-build.md` — added per-file letter-prefix anchor convention. Added Cell-rendering hard rules: display title verbatim from bib_ledger, GitHub `—` if not directly known (no `<firstauthor>/<paper-slug>` guessing), default Venue to "arXiv preprint" not memory-guessed.
- `.claude/skills/agent-index.md` — same hard rules carried up: display title verbatim, no GitHub URL guessing, append `(no widely-known repo)` / `(uncertain venue)` flags to Status when uncertain.
- `.claude/skills/url-freshness-check.md` — replaced negative char-class regex (silently 0 on macOS) with positive form `[a-zA-Z0-9./?=&_~%#:+-]+`. Added `if N≥50 use inline curl bulk-check` fast-path branch (60s for 100+ URLs vs WebFetch timeout). Added URL-extraction sanity check.

**References**
- `references/audit_protocol.md` — added "Default arXiv-ID spot-check" section: when Stage 2 reports memory-based work, Stage 5 must include a 10-entry random arXiv-ID spot-check by default. Added "Display-title preservation rule" with worked examples from calibration corrections.

**Tests**
- `tests/test_v1_1_fixes.py` (NEW, 27 tests) — covers all v1.1 changes:
  - Optional bib_ledger fields round-trip + reject malformed (4 tests)
  - arXiv canonical-form check accept/reject parametrized (10 tests)
  - Non-arxiv URLs pass through unchecked (1 test)
  - code_url URL-format rejection (1 test)
  - Positive URL-extraction regex extracts mixed-content URLs (2 tests)
  - Standalone validator invocation per-validator (6 tests)
  - Backward-compat regression on existing fixtures (3 tests)

**Test fixture cleanup**
- `tests/fixtures/prompt_injection_snapshot/real/bib_ledger.yml` — entry 63 (`kim2024selfreminder`) had empty `primary_url` (a v1.0-era known defect that the validator silently flagged because no test exercised prompt-injection/real). Populated with `https://www.nature.com/articles/s42256-023-00765-8` and renamed `test_prompt_injection_bib_ledger_has_one_known_violation` → `test_prompt_injection_bib_ledger_passes_cleanly`.

### Verification

- `make test`: 45 pass + 2 known-baseline fail (prompt-injection recreation_diff entry-counts + section-anchors — unchanged from v1.0; flagged in BURN_IN as deliberate v1.0 gaps not in v1.1 scope).
- `python -m pytest tests/test_v1_1_fixes.py -v`: 27 / 27 pass in <1 s.
- All 6 real-world bib_ledgers (mini, prompt-injection/real, prompt-injection/recreated, eval-methodology, PEFT, calibration) validate cleanly under v1.1 schema.
- Standalone invocation `python validators/<x>.py path` now works for all 6 validators.

### Out-of-v1.1 scope (deferred to v1.2 or never)

- v1.0 BURN_IN's two recreation_diff baseline fails (entry-counts within tolerance, section-anchors match) — these reflect the recreation's structural divergence from real, not a tooling defect. Resolving would require either re-running prompt-injection recreation with v1.1 skills or relaxing the tolerances; both are beyond v1.1's "fix the tooling" charter.
- Pydantic / config-framework / packaging changes — out of scope per project instructions.

**v1.2+ roadmap:** see `docs/roadmap_v1_2_through_v1_5.md` — sequenced post-v1.1 plan covering 10 audit items across 4 versions (v1.2 defensive hardening, v1.3 data + fixture grounding, v1.4 pipeline test surface, v1.5 ops + ergonomics). Roadmap is aspirational; each version is gated by its own user decision.

---

## v1.2 — applied 2026-05-07

**Theme:** defensive hardening — make the toolkit *resistant to subagents misbehaving* rather than just *requesting that subagents behave*.

**Items shipped (all 4):**

- **A2 cross_stage validator** (`validators/cross_stage.py`, NEW) — claim_family-vs-research-plan-taxonomy hard check; orphan-arxiv-ID soft warnings (dossier + agent_index); stale-ledger-entry warnings; `--strict` flag promotes warnings to errors. Fixes a real bug class: bib_ledger entries using a claim_family not in the plan's taxonomy were silently accepted before. Also surfaces prompt-injection/real's 9 stale ledger entries (in ledger but not synthesized) and 202 cross-reference IDs (in synthesis but not in own ledger — prompt-injection's intentional cross-reference pattern).
- **A3 anti-cheat heuristic** (`validators/bib_ledger.py`) — if ≥50 entries AND every entry has `status: verified` (no `unverified` or `mismatched`), emit a "memory-verification suspected" warning. `--strict` promotes to error. Catches the calibration §2.1 anti-pattern where Stage 2 marked all 88 entries `verified` from memory under time pressure. Validates correctly: warns on PEFT (67 entries) and calibration (88 entries); silent on prompt-injection/real (137 entries with mixed status) and mini fixture (small).
- **A4 xfail baseline tests** (`tests/test_recreation_diff.py`) — the 2 prompt-injection recreation_diff fails (entry_counts_within_tolerance, section_anchors_match) marked `@pytest.mark.xfail(strict=True)` with BURN_IN-referencing reason. They reflect v1.0 recreation drift, not tooling bugs. `strict=True` means we'll be notified if they ever pass (e.g., after v1.3 backfill re-runs prompt-injection recreation).
- **B6 CI workflow audit** — `.github/workflows/test.yml` audited: runs `python -m pytest` on push/PR for Python 3.11+3.12, installs `pip install -e ".[dev]"`. Functionally equivalent to `make test`. No gaps; v1.2 changes flow through automatically.

**Tests (NEW: tests/test_v1_2_fixes.py, 14 cases):**
- cross_stage validator: passes minimal project (1); skips on missing ledger (1); rejects unknown claim_family (1); warns on orphan dossier arxiv (1); --strict promotes (1); warns on stale ledger (1); standalone CLI (1); --strict CLI flag (1)
- anti-cheat heuristic: quiet under threshold (1); quiet with mixed status (1); warns at 50+ all-verified (1); --strict promotes (1); --strict CLI (1)
- backward compat: v1.2 changes don't break existing fixtures (1)

**Verification:**
- `make test`: **59 passed + 2 xfailed** (the 2 baselines from A4). Up from v1.1's 45 passed + 2 baseline fails.
- All 6 real-world projects (mini, prompt-injection/real, prompt-injection/recreated, eval-methodology, PEFT, calibration) cross_stage-validate cleanly in default mode.
- Anti-cheat correctly identifies PEFT + calibration as memory-verified suspects (warning); silent on properly-mixed prompt-injection/real.

**Critical bug caught + fixed during v1.2 implementation:**
- The cross_stage validator's first regex `arxiv\.org/abs/(\d{4}\.\d{4,5})` only matched URL-form references. Real-world dossiers use citation-form `arXiv:<id>` in the arXiv/DOI column. The validator silently passed on PEFT/calibration for the wrong reason (extracting 0 IDs). Fixed regex to `(?:arxiv\.org/abs/|arxiv:)(\d{4}\.\d{4,5})` (case-insensitive). Confirmed real-world matching works. **Lesson:** when a defensive validator passes on every fixture you point it at, suspect it's not actually doing the check before celebrating.

**Out-of-v1.2 scope (deferred to v1.3+):**
- Backfilling eval-methodology/27/28 ledgers with `authors`/`venue`/`code_url` fields (v1.3 A1).
- Medium fixture for stress-testing dossier-build at >5 entries (v1.3 C10).
- E2E pipeline smoke test (v1.4 B5).
- Re-running prompt-injection recreation under v1.2 skills to close the xfail'd baseline gap (v1.3 candidate).

---

## v1.3 — applied 2026-05-07

**Theme:** data + fixture grounding — make the v1.1 schema extension *useful* by populating optional fields in real ledgers, and create a medium fixture for stress-testing.

**Items shipped (both):**

- **A1 backfilled eval-methodology/27/28 ledgers** — new helper `scripts/backfill_ledger.py` extracts `authors`/`venue`/`code_url` from each vol's dossier paper-tables (which already had the human-curated metadata) and merges back into the ledger. Idempotent: skips fields that are already populated.
  - eval-methodology: 65/72 entries backfilled (90% authors+venue, 74% code_url)
  - PEFT: 65/67 entries backfilled (97% authors+venue, 84% code_url)
  - calibration: 75/88 entries backfilled (85% authors+venue, 65% code_url)
  - Skipped entries are non-arxiv classics (Platt 1999, Brier 1950, JSTOR/DOI/Springer URLs etc.) — backfill uses arxiv ID as the join key. Future v1.x could add title-fuzzy matching for these.

- **C10 medium fixture** — `tests/fixtures/medium_topic_calibration_subset/` (22 entries, calibration calibration_method + calibration_metric subset) with full v1.1+ schema coverage. Generator script `scripts/build_medium_fixture.py` regenerates from current calibration state (re-run after future calibration audits). Validates against all 5 v1.0/v1.1/v1.2 validators including cross_stage --strict.

**Tests (NEW: tests/test_v1_3_fixtures.py, 17 cases):**
- Medium fixture: passes 4 validators (research_plan, bib_ledger, dossier, agent_index) + cross_stage default + cross_stage --strict (6 cases)
- Optional-field coverage on medium fixture: ≥55% authors, ≥55% venue, ≥40% code_url (3 cases)
- Medium fixture size + below anti-cheat threshold (2 cases)
- eval-methodology/27/28 backfilled ledgers validate + ≥80% authors coverage (parametrized 6 cases — skipped if working copy absent)

**Verification:**
- `make test`: **76 passed + 2 xfailed** (up from v1.2's 59 + 2)
- Medium fixture exercises dossier sub-section logic at the size where PEFT stressed (22 entries vs mini's 5)
- Backfilled ledgers preserve all existing data — idempotent re-runs produce no diff

**Why the medium fixture coverage threshold is 55% not 80%:**
The medium fixture is a calibration subset that intentionally includes pre-2010 classical-stats papers (Brier 1950, Platt 1999, DeGroot 1983, Zadrozny 2001/2002, Niculescu-Mizil 2005, Gneiting 2007). These have venue + authors info in the dossier but no arXiv IDs in the ledger, so the arxiv-ID-based backfill skipped them. The eval-methodology/27/28 LLM-era ledgers don't have this skew so they hit the ≥80% target. Documented in test docstrings.

**Out-of-v1.3 scope (deferred to v1.4+):**
- Re-running prompt-injection recreation under v1.1+v1.2 skills (would close xfail'd baselines but is its own dogfood run).
- Title-fuzzy matching in backfill (would push medium fixture to ≥80%; currently a 55% floor is sufficient for the fixture's purpose).
- E2E pipeline smoke test (v1.4 B5).

---

## v1.4 — applied 2026-05-07

**Theme:** pipeline test surface — catch contract drift between stages without per-stage CI boilerplate.

**Item shipped:**

- **B5 end-to-end pipeline smoke test** — `tests/test_pipeline_e2e.py` (NEW, 9 cases). The 6 skills are markdown prompts run by Claude Code agents, not Python functions, so we can't mock-drive them. What this DOES test:
  1. **Sequential validator chain** — every validator (research_plan + bib_ledger + dossier + agent_index + audit_trail + cross_stage) passes against the medium fixture, run in pipeline order. Catches contract drift if stage N's output schema changes in a way stage N+1's validator can't handle (1 case + 1 strict-mode case).
  2. **Helper-script idempotency** — `scripts/backfill_ledger.py` re-running on an already-backfilled medium fixture produces zero diff (1 case). `scripts/build_medium_fixture.py` is at least syntactically valid + the fixture has the files the script promises (1 case).
  3. **Deliberate-regression detection** — mutating the fixture in 3 specific ways (orphan arxiv ID in dossier, unknown claim_family in ledger, /pdf/ URL form) is caught loudly (3 cases).
  4. **Cross-fixture sanity** — mini and medium have different entry counts; both validate cleanly. Catches "every fixture passes for the wrong reason" (1 case).
  5. **URL-check report sanity** — well-formed report passes (1 case).

**Verification:**
- `make test`: **85 passed + 2 xfailed** (up from v1.3's 76 + 2)
- E2E test runs in <1s (9 cases × <0.1s each); cheap enough to gate every PR.

**Why this is "honest E2E" not "full pipeline":**
A "real" E2E would mock WebSearch+WebFetch + drive Claude Code agents through the 6 stages, comparing outputs to baked expectations. That requires the Claude Code SDK + a deterministic LLM (or response cache) + a multi-process harness. None of those are appropriate for a v1.x toolkit hardening PR. The v1.4 scope is the part of E2E we can test honestly: validator-chain consistency + helper-script stability + regression detection. Documented as a deliberate scope choice in `tests/test_pipeline_e2e.py` docstring.

**Out-of-v1.4 scope (deferred to v1.5+):**
- Skill-body execution mocking (would require Claude Code SDK integration; large infrastructure investment).
- Network-dependent tests (intentionally avoided; v1.4 is offline-only).
- Documentation + structured BURN_IN + dogfood metrics CSV (v1.5 final scope).

---

## v1.5 — applied 2026-05-07

**Theme:** ops + ergonomics — lower the cliff for future-you / future Claude Code agents reading the repo cold; make BURN_IN queryable; track reliability metrics across runs for RLHF+.

**Items shipped (all 3):**

- **B7 docs** — `docs/getting_started.md` (118 lines) + `docs/troubleshooting.md` (177 lines). Tight, audience-appropriate for "future-self + future agents reading the repo cold" per the user's audience choice in the roadmap. Getting-started covers install, 5-minute end-to-end run, validating in progress, where-things-live. Troubleshooting covers the 7 most-recurring failure modes from BURN_IN with symptom→cause→fix structure (URL extraction silent fail, validator import error, GitHub URL 404 cluster, memory-verification warning, claim_family taxonomy mismatch, subagent count drift, the 2 xfailed baselines).

- **C8 structured BURN_IN log** — `burn_in.yml` (16 entries) is the queryable companion to `BURN_IN_NOTES.md` prose. Schema: `{id, phase, stage, finding, severity, status, fix_version?, fix_commit?, notes?}`. Backfilled all v1.0/v1.1/v1.2/v1.3/v1.4 findings from BURN_IN_NOTES.md narrative entries.
  - `scripts/burn_in_query.py` — filter by status/severity/phase/stage/fix_version with table/yaml/ids output formats.
  - As of v1.5: 5 high-severity items, all `applied`. 0 unresolved high-severity. Rest are 4 medium + 7 low (mostly `applied` or `deferred`).

- **C9 dogfood metrics CSV** — `evals/dogfood_metrics.csv` with 4 backfilled rows (prompt_injection_recreated baseline, eval-methodology v1.0 gate, PEFT v1.1, calibration v1.1). Columns: date, vol, total_entries, total_urls, hard_404_count, attribution_corrections_in_audit, toolkit_version, notes. Future runs (RLHF+) append a row each. Trend visible after 2-3 future runs.

**Tests (NEW: tests/test_v1_5_artifacts.py, 12 cases):**
- B7: getting_started + troubleshooting exist with reasonable size; getting_started mentions all 6 skills; troubleshooting covers 5 known failure topics (4 cases)
- C8: burn_in.yml parses; entries well-formed (id uniqueness, required fields, severity/status enums, fix_version when applied); query script runs; all 3 output formats produce non-empty output; high-severity items all resolved (5 cases)
- C9: dogfood_metrics.csv parses with required columns; dates in YYYY-MM-DD; includes eval-methodology+PEFT+calibration baselines (3 cases)

**Verification:**
- `make test`: **97 passed + 2 xfailed** (up from v1.4's 85 + 2; up from v1.0's pre-v1.1 48 baseline by 2x).
- 0 unresolved high-severity BURN_IN items (`burn_in_query.py --severity high --status surfaced` returns empty).
- prompt-injection/recreated, eval-methodology, PEFT, calibration all logged in metrics CSV; RLHF+ slot ready.

## v1.5.1 — applied 2026-05-07

**Theme:** small post-audit alignment patch — close 3 gaps that v1.x left unfinished.

**Items shipped (all 3):**

- **/agent-index skill references cross_stage validator.** v1.2 added `validators/cross_stage.py` but the `/agent-index` skill body's `## Validation` section only ran the per-stage validator. Now mentions cross_stage with rationale (claim_family taxonomy drift + orphan-arxiv detection) and notes that `--strict` promotes warnings to errors.
- **/research-gather + /dossier-build skill bodies reference the medium fixture.** Both skills now point at `tests/fixtures/medium_topic_calibration_subset/` as the canonical worked example for v1.1+ schema (research-gather points at the bib_ledger.yml; dossier-build points at the rendered dossier file). Subagents reading the skill bodies cold can now find a concrete reference.
- **`validators/audit_trail.py` enforces contiguous sequential round numbering.** Rounds must be `[1, 2, ..., N]`; gap or non-1 start is a hard error. Catches the failure mode where a multi-round audit subagent loses count. Zero rounds (fresh agent_index) still passes.

**Tests (NEW: tests/test_v1_5_1_fixes.py, 12 cases):**
- 3 skill-body lint tests (substring presence in `## Validation` section / Phase sections)
- 9 audit_trail sequence tests: positive (zero rounds, single round 1, contiguous 1-2-3, out-of-order-but-contiguous); negative (gap, larger gap with 3 missing reported, non-1 start, duplicate); regression check on all 4 real-world fixture READMEs

**Verification:**
- `make test`: **109 passed + 2 xfailed** (up from v1.5's 97 + 2)
- All 7 real READMEs (mini, medium, prompt-injection/real, prompt-injection/recreated, eval-methodology/27/28) pass the new audit_trail sequence rule
- 0 unresolved high-severity BURN_IN items unchanged

**Why this is v1.5.1 not v1.6:**
No breaking changes to ledger schema or skill workflows; just three small alignments + a tightened validator. Patch version is correct.

---

**Out-of-v1.5 scope (truly deferred — out of v1.x charter):**
- ~~Re-running prompt-injection recreation under v1.1+v1.2+v1.3 skills to close the 2 xfailed baselines~~ — **partially done 2026-05-07 post-v1.5**: applied v1.5 per-file letter-prefix anchor convention to `tests/fixtures/prompt_injection_snapshot/recreated/dossier/` + `agent_index/` files 02-07 (A→B/C/D/E/F/G prefixes). Result:
  - **File 02 now fully matches real/** (4 sub-sections each, B-prefix anchors aligned). The v1.5 codification works as designed.
  - **Files 01/03/04 still differ** because the v1.0 recreation chose fewer sub-sections (3 vs real's 5/6/6) — editorial granularity, not a tooling defect. The xfail reasons in `tests/test_recreation_diff.py` were updated with this honest diagnosis. xfails are now likely **permanent** (would require either re-running /research-gather + /dossier-build editorially or hand-splitting existing sub-sections).
  - The entry-counts xfail's true cause is also editorial: prompt-injection/real includes ~202 cross-reference arxiv IDs that the recreation deliberately doesn't render (it synthesizes only its own ledger). Same "permanent xfail" outcome.
  - Logged as a row in `evals/dogfood_metrics.csv` (prompt_injection_recreated_anchor_renamed under toolkit_version v1.5).
- Skill-body execution mocking + Claude Code SDK integration for true E2E (separate plan if it ever happens).
- New skills (`/dossier-export`, `/dossier-merge`, `/dossier-diff`) — explicit "out of v1.x" per the roadmap.
- Pydantic / config-framework / packaging changes — out of CLAUDE.md scope.

---

## v1.6 — applied 2026-05-08

**Theme:** new dataset-research pipeline (parallel to paper pipeline). Three new skills (`/dataset-gather`, `/dataset-index`, `/dataset-research`) + dataset_ledger validator + 2 templates + dataset_sources reference doc. Full v1.0-style release gate: ship + dogfood + audit round.

**Dogfood topic**: time-series anomaly detection. **Output**: `~/interview_prep_series/docs/research/time_series_anomaly_datasets/` (45 entries, 7 files). **Medium fixture**: `tests/fixtures/medium_dataset_subset/` (12 curated entries; v1.6 schema reference).

**Items shipped:**

- **Validator**: `validators/dataset_ledger.py` — required fields (bibkey/primary_url/name/source/status/task_family); `task_family` fixed enum (13 values); optional license/size/rows/columns/schema_url/access_method/auth_required/citation; anti-cheat heuristic at ≥30 entries; standalone CLI with `--strict`.
- **Templates**: `dataset_ledger.template.yml` + `dataset_5_bullet_entry.template.md`.
- **Reference**: `references/dataset_sources.md` — 8 source categories with per-source gotchas.
- **Skills**: `/dataset-gather` (~150 lines), `/dataset-index` (~120 lines), `/dataset-research` (~30 lines wrapper).
- **Tests**: `test_v1_6_dataset_skills.py` (31 cases — 13 enum-coverage + validator pos/neg + lint + integration). All pass.
- **Makefile**: `make dataset-smoke` target.

**Dogfood findings:**

1. **Source category `other` was 29% of entries**, materially understated by the canonical 8-category list. PhysioNet, UNB-CIC, SUTD iTrust, Yahoo Webscope, Backblaze, Morris-UAH, ELKI did not fit cleanly. **Action for v1.7**: expand `dataset_sources.md` source-category list OR document that `other` is expected-heavy for security/biomedical/critical-infrastructure topics.

2. **Cornell → UCR domain typo in Stage 4 rendering**. The dataset-index subagent rendered `https://www.cs.cornell.edu/...` for the UCR Time Series Archive (Eamonn Keogh is at UC Riverside, not Cornell). Ledger had the correct URL; rendering substituted the wrong domain. **Action for v1.7**: codify in `/dataset-index` skill body — the ledger is the source of truth; rendering MUST NOT substitute domain/host names.

3. **`source: other` overloading and Kaggle paywall blocking** — both already documented in vol-29-style detail in `dataset_sources.md` Phase A but reproduced here as v1.6 dogfood findings.

4. **paperswithcode.com/datasets is dead in 2026** — redirects to HF papers/trending. v1.7 should remove it from the canonical aggregator list.

5. **The `(uncertain license) Verified.` flag is the right intermediate state** for HF community uploads with empty dataset cards. Audit kept these in but tightened the marker — confirms v1.5.1 status-flag conventions transfer cleanly to the dataset pipeline.

6. **License coverage 95.6%** — the v1.5.1 strict-verification protocol carried over without modification. Most license uncertainty is genuine source-page emptiness, not skill-body laziness.

7. **First-run audit corrections: 1 (ASD license)** — vs vol29 RLHF first-run 0 corrections. v1.6 dataset pipeline has a slightly higher correction rate than mature paper-pipeline; expected for a brand-new pipeline.

**Verification:**

- `make test`: 140 → 171 passed + 2 xfailed (31 new v1.6 tests pass).
- `make dataset-smoke`: passes against medium_dataset_subset fixture.
- `make audit`: existing audit targets unchanged; cross_stage doesn't yet check dataset_ledger (v1.7 stretch).
- All 3 dogfood validators (dataset_ledger, agent_index, audit_trail, url_check_report) pass on the time-series anomaly artifact.

---

## v1.8 — applied 2026-05-08

**Theme:** first paired-pipeline dogfood. Tests cross-pipeline integration (paper synthesis ↔ dataset dossier on the same topic). No code changes; pure dogfood + cross-link.

**Topic**: RLHF and preference optimization. **Output**: `~/interview_prep_series/docs/research/rlhf_datasets/` (50 entries, 5 files) + bidirectional cross-link with existing `vol29_rlhf/` paper synthesis.

**Items shipped:**

- **Phase A**: 50-entry RLHF dataset ledger via `/dataset-gather`. 80% verified + 10 honest-unknown licenses. HF concentration 43/50 (RLHF data canonically lives on HF — honest, not lazy).
- **Phase B**: 5-file agent_index via `/dataset-index`. Per-file letter-prefix anchors (A/B/C). `01_huggingface_preference_data.md` (30) + `02_huggingface_arena_and_eval.md` (13) + `03_github.md` (7) + 00_overview + README.
- **Phase C**: Round 1 audit. **1 CORRECT** (Nectar's Apache-2.0 declaration in YAML didn't capture the prose restrictions on commercial use) + 8 FLAG-as-already-flagged + 8/8 spot-checks PASSED. v1.7 anti-domain-substitution rule held under pressure.
- **Phase D**: Bidirectional cross-link between `rlhf_datasets/README.md` and `vol29_rlhf/README.md`. Both validators clean post-edit.
- **Phase E**: URL check **0/50 hard-404s** — first fully-clean dataset-pipeline run. Empirical signal that v1.7 byte-faithful URL preservation works.

**Findings:**

1. **Compound-license pattern (v1.9 BURN_IN candidate)**: Nectar's HF dataset card declares `license: apache-2.0` in the YAML frontmatter but the prose section adds "non-commercial research preview, not for use competing with OpenAI, subject to LLaMA + OpenAI ToU + ShareGPT terms." The strict-verification protocol that pulls only the YAML `license:` key misses this. Audit caught it (cross-checked the prose) but the rendering subagent didn't. **Action for v1.9**: extend `/dataset-gather` HARD RULES to: "license capture must check BOTH the YAML `license:` field AND the prose section for restrictive caveats. If the prose adds restrictions beyond the YAML license, render the license field as `<base license> + custom restrictions` and document the restrictions in the citation."

2. **HF concentration is honest for some topics**: RLHF data is 86% HuggingFace; 0 entries from Zenodo/OSF/Figshare/ICPSR/UCI/OpenML/AWS/government — those just don't have RLHF data. Compare time-series-anomaly (v1.6) where `source: other` was 29% (security/ICS/biomedical hosts). The "honest but narrow" shape is correct for RLHF; the "other-overloaded" shape is correct for security/ICS. Both are valid.

3. **First fully-clean URL run for dataset pipeline**: 0/50 hard-404s. v1.6 had 1 (Cornell→UCR typo). v1.7 codified the anti-substitution rule. v1.8 confirms the rule holds under a 43-HF-namespace render where capitalization is the failure mode (Anthropic, OpenAssistant, HuggingFaceH4, RLHFlow, etc.).

4. **Bidirectional cross-link template gap**: when adding the reverse link in `vol29_rlhf/README.md`, the existing scope-callout had a list of cross-vol links (vol25/26/27/28). Added the dataset cross-link as a new bullet in that list. Pattern: "for adjacent topics: [list of paper-vols]; for paired-pipeline datasets, see [`../<topic>_datasets/`]". Worth codifying in the agent_index_README.template.md as the canonical paired-pipeline cross-link convention. **Action for v1.9**: update template to show this list-pattern explicitly.

5. **Cross-pipeline duplication is intentional, not a bug**: 8 entries appear in BOTH `vol29_rlhf/` (as paper) and `rlhf_datasets/` (as dataset artifact). Examples: UltraFeedback paper (in vol29 §F1) + UltraFeedback dataset (in rlhf_datasets §A1). HH-RLHF paper (Bai 2022) + HH-RLHF dataset. These are correctly separate references — paper dossier captures methodology; dataset dossier captures the artifact. Cross-pipeline duplication risk surfaced in v1.6 plan but holds up cleanly in practice.

**Verification:**

- `make test`: 141 → 141 passed + 2 xfailed (no test changes; v1.8 is dogfood, not code).
- All 4 dogfood validators (dataset_ledger, agent_index, audit_trail, url_check_report) green.
- Both cross-linked READMEs (rlhf_datasets, vol29_rlhf) validate post-edit.
- Anonymous clone test still works.

**Out-of-v1.8 scope (deferred):**

- Compound-license rendering rule (v1.9 BURN_IN above).
- agent_index_README.template.md update for paired-pipeline cross-link convention (v1.9).
- Second paired dogfood (calibration_datasets, peft_datasets) — done if/when needed; v1.8's signal is sufficient.
- cross_stage validator extension for dataset_ledger (still stretch from v1.6).

---

## v1.9 — applied 2026-05-08

**Theme:** consolidate the 3 BURN_IN backlog items from v1.8 paired-dogfood. Tooling-only release; no new dogfood.

**Items shipped (all 3):**

1. **Compound-license rendering rule** (`/dataset-gather` skill body + `references/audit_protocol.md`). v1.8 surfaced Nectar's `apache-2.0` YAML declaration that prose contradicted with non-commercial restrictions. v1.9 codified: when source page has BOTH structured `license:` field AND prose section discussing terms, render as `<base license> + custom restrictions: <one-line summary>`. The audit-protocol's "license risks" focus area gets a parallel sub-section so the audit stage spot-checks for the same anti-pattern. Belt-and-suspenders: rule applied at both gather time and audit time.

2. **Paired-pipeline cross-link template convention** (`templates/agent_index_README.template.md`). v1.8 produced the bidirectional cross-link pattern (vol29_rlhf ↔ rlhf_datasets) ad-hoc; v1.9 codifies it in the template so future paired-pipeline runs follow the convention consistently. Worked example preserved for cold readers.

3. **`cross_stage` validator extension for `dataset_ledger`** (`validators/cross_stage.py`). Stretch goal deferred from v1.6 + v1.7 + v1.8. v1.9 ships it: the validator now handles paper projects (bib_ledger), dataset projects (dataset_ledger), and projects with both. Dataset flow checks orphan ledger entries (in ledger but not in agent_index Source line) and orphan synthesis refs (in agent_index Source line but not in ledger). `--strict` promotes warnings to errors, parallel to bib_ledger flow.

**Tests (NEW: 10 cases added to `tests/test_v1_6_dataset_skills.py`):**
- 3 lint tests: `/dataset-gather` has compound-license rule; `audit_protocol.md` has compound-license check; template has paired-pipeline cross-link convention.
- 7 cross_stage unit tests: clean dataset project; orphan ledger warning; orphan synthesis warning; --strict promotion; both ledgers handled independently; medium_dataset_subset backward compat; real rlhf_datasets validates.

**Verification:**
- `make test`: 141 → 151 passed + 2 xfailed (10 new v1.9 tests; no regressions).
- All 10 existing real-world projects/fixtures pass under the new validator in default + strict modes.
- Backward compat: medium_dataset_subset, prompt_injection_snapshot/recreated, all 4 paper-pipeline projects (research_eval_methodology / research_peft / research_calibration / research_rlhf), 2 dataset-pipeline projects (research_time_series_anomaly, research_rlhf_datasets) all pass.

**Out-of-v1.9 scope (truly deferred):**
- Compound-license auto-detection (parsing HF dataset cards programmatically). The v1.9 rule is "skill body says check prose; subagent does it manually." Auto-detection is its own design.
- HF datasets API integration vs WebSearch+WebFetch (still marginal value).
- `docs/getting_started.md` / `docs/troubleshooting.md` v1.6+ updates.
- A v1.10 / v2.0 design discussion. v1.9 closes out the v1.8 dogfood backlog; further work is BURN_IN-driven from future dogfoods.

---

## Phase 8: meta-research dogfood + v2.2 backlog — applied 2026-05-19

**Theme**: apply the toolkit's own v2.1.0 chain to research v2.2 design
candidates. The project's primary deliverable is the v2.2 design backlog
markdown (`references/v2_2_design_backlog.md`), with every backlog item
byte-anchored to a v3 strict-live evidence record.

**Project**: `~/Claude/research_toolkit_design/` (not committed to this
repo). **6 entries** spanning 5 sub-areas of anti-hallucination
methodology:
- FActScore (Min 2023 EMNLP) — atomic-fact decomposition
- VISTA (Lewis 2025) — dialogue-history-aware atomic verification
- Slobodkin Attribute-First (2024 ACL) — span-conditioned generation
- Farquhar Semantic Entropy (Nature 2024) — confabulation detection
- Self-RAG (Asai 2023 ICLR) — adaptive retrieval + reflection tokens
- Faithfulness metric fusion (Malin 2025 arXiv 2512.05700) — multi-metric
  ensemble for LLM-as-judge

All 6 sources fetched live via `cache_source.py` (real arxiv + PMC HTML,
real SHA-256s). v3 evidence ledger built with `extraction_method:
verbatim_match` on all 6 entries, substring + SHA-256 anchors computed
for each cited excerpt. Citation audit: **6/6 substring checks pass
(100%), 100% verbatim-anchored, avg link_confidence 0.967.**

**v3 chain end-to-end pass at multi-source scale.** Dashboard correctly
shows: 6/6 evidence coverage, 6/6 cache completeness, 0 conflicts, 0
weak claims, Claim Health 6/6 strongly grounded. research_kb_export
produces 30-record JSONL (6 entities + 6 sources + 6 claims + 6
evidences + 6 cache_blobs) — all validators clean.

**Deliverable**: `references/v2_2_design_backlog.md` committed to this
repo. 6 backlog items, 3 Tier-1, each with v3 evidence cross-reference,
v2.1-gap-closed analysis, proposed mechanism, effort estimate. Top 3
Tier-1 picks for v2.2.0 next-session implementation:
1. Item 3 — Attribute-First refactor of /agent-index (L effort)
2. Item 1 — Atomic-claim decomposition in /agent-index (M effort)
3. Item 5 — Self-RAG adaptive retrieval in /research-gather (M effort)

### Friction items (5 surfaced, 0 applied, 5 deferred)

**1. `/dossier-build` and `/agent-index` skipped during Phase 8 dogfood
   (status: surfaced — known from Phase 4)**
- Per the established pattern (Phase 4 + Phase 5 also skipped these),
  the markdown-rendering steps weren't run in this session. The v3 trust
  chain doesn't depend on them; project artifacts are the ledgers +
  claim_graph + dashboard + export.
- **Implication for v2.2**: this confirms friction item #7 from Phase 5
  BURN_IN — `/dossier-build` and `/agent-index` aren't on the v3 trust
  chain critical path; the docs / skill descriptions should explicitly
  state this split.

**2. Real WebSearch / WebFetch effort scales linearly with source count
   (status: surfaced — confirmed at scale)**
- 6 sources × ~10 tool calls per source (search + fetch + cache +
  excerpt extraction + offset computation + yaml entry) = ~60 tool calls
  for the gather phase alone.
- **Implication for v2.2**: Item 5 (Self-RAG adaptive retrieval) is the
  v2.2 fix — `gather_trace.yml` records IsRel/IsSup/IsUse per fetch so
  the per-source cost is reviewable + auditable.

**3. excerpt + offset computation is unguided LLM work (status:
   surfaced — Phase 4 friction #5 confirmed at v3 scale)**
- For each evidence entry: open cached text_path, find a quotable span
  (~200 chars), compute byte offset via `text_bytes.find()`, hash with
  hashlib. Tedious; per-source overhead grows with source count.
- **v2.2 candidate fix**: new `scripts/locate_excerpt.py` helper that,
  given (cache_id, target_substring), returns (text_path_offset, sha256)
  ready to paste into evidence_ledger. Could be invoked from
  /research-gather skill body.

**4. arxiv `citation_abstract` meta tag is reliable; PMC pages lack it
   (status: surfaced — NEW)**
- Farquhar et al. 2024 (PMC URL) has NO `citation_abstract` meta. Had
  to scan the cached text for a quotable methodology sentence by keyword
  search ("semantic entropy" + "confabulation"). Worked but ad-hoc.
- **v2.2 candidate**: per-source-type excerpt extraction protocols
  documented in `references/excerpt_extraction_cheatsheet.md` (arxiv:
  citation_abstract; PMC: first paragraph of abstract section; vendor
  blog: first paragraph after H1; etc.).

**5. Cross-source synthesis claims need editorial work the builder can't
   provide (status: surfaced — confirms v2.0 backlog #3)**
- Each of the 6 claims in this project is single-source — supported by
  exactly one evidence entry. A real research synthesis would aggregate
  multi-source evidence into cross-cutting claims (e.g., "atomic
  decomposition is necessary for fine-grained factuality eval, per both
  FActScore and VISTA"). v2.1's builder produces single-evidence claims;
  multi-evidence aggregation works (per Phase 5 dogfood) but the
  cross-source synthesis claim TEXT is still editorial.
- **v2.2 candidate**: when 3+ evidences support the same claim_id,
  /agent-index Phase 2 rewrites the claim text into a cross-source
  synthesis sentence. This is editorial work an LLM does in the
  /agent-index step. Documented in the backlog (Item 2 — cross-source
  corroboration).

### Phase 8 (loop iters 4-10): extended corpus + dogfood at saturation

**Theme**: /loop iterations extending the 6-source dogfood project to
23 sources (16 added across 7 iters) + 4 cross-source synthesis claims
demonstrating the builder's multi-evidence aggregation at v3 scale.

**Iter-by-iter source additions:**
- iter 4 (commit f0cfc6c): typed grounding + process reward + probabilistic factcheck (3 sources)
- iter 5 (commit a6bc3c2): 3 cross-source synthesis claims (no new sources)
- iter 6 (commit 3c79a43): AtomEval SROM atoms + Counterfactual Probing (2 sources)
- iter 7 (commit 70805ed): DoublyCal two-tier calibration + KEA Explain KG-kernel (2 sources)
- iter 8 (commit dbf1502): C²-Cite + Generation-vs-Posthoc citation paradigms (2 sources)
- iter 9 (commit 5c39dce): 4th synthesis claim (gen-time) + VeriFact (1 source + synthesis)
- iter 10 (this iter): FAIR-RAG iterative refinement (1 source)

**End-state metrics**: 23 bib entries, 23 evidence entries, 27 claims
(23 atomic + 4 cross-source synthesis), **35/35 verbatim_match substring
checks pass (100%)**, avg link_confidence 0.948, all 23 sources verified
via real WebSearch + WebFetch + cache_source.py with real SHA-256s.

**Source distribution by claim_family (final):**
- atomic_grounding (5): FActScore, VISTA, RAGTruth, AtomEval, VeriFact
- generation_conditioning (3): Attribute-First, C²-Cite, Gen-vs-Posthoc
- sample_based_detection (4): Semantic Entropy, SelfCheckGPT, Lookback
  Lens, Counterfactual Probing
- graded_support (6): Self-RAG, Retromorphic Testing, Tool-MAD, GSAR,
  KEA Explain, FAIR-RAG
- judge_calibration (5): Faithfulness Fusion, MAD-Fact, Process Reward,
  Probabilistic Factcheck, DoublyCal

**Cross-source synthesis claims demonstrated:**
- `claim_synthesis_atomic_grounding_pattern` (FActScore + RAGTruth + VISTA)
- `claim_synthesis_sample_based_pattern` (Semantic Entropy + SelfCheckGPT + Lookback Lens)
- `claim_synthesis_multi_agent_pattern` (Tool-MAD + MAD-Fact + GSAR)
- `claim_synthesis_gen_time_attribution_pattern` (Attribute-First + C²-Cite + Gen-vs-Posthoc)

All four synthesis claims correctly aggregate 3 evidence_ids + 3
entity_ids each via `build_claim_graph.py`'s highest-quality +
longest-excerpt tiebreak. Backlog Item 2 (cross-source corroboration)
demonstrated working at v3 scale — demoted from M-L effort to S.

### Friction items surfaced (iters 4-10)

**6. MDPI publisher returns 403 to urllib User-Agent (status: surfaced
   — NEW iter 7)**
- iter 7 attempted to cache an MDPI 2026 paper (AEVS framework for KG
  triple grounding). `cache_source.py` got HTTP 403 Forbidden.
- **v2.2 candidate**: `cache_source.py` should accept `--user-agent`
  flag (or default to a Mozilla-like UA string) for publishers that
  filter Python urllib. Pivoted to arxiv-only sources for that iter.

**7. Cache root inconsistency between iter 1-3 sources (global) and
   iter 4-10 sources (project-local) (status: surfaced — confirms v2.0
   backlog #2)**
- iter 1-3 sources point to `/Users/.../research_cache/...` (global
  cache root). iter 4-10 cached with `--cache-root` flag pointing to
  `/Users/.../research_toolkit_design/cache/` (project-local). Both
  work — validator just checks file existence — but mixing paths is
  ugly.
- **v2.2 candidate**: confirms backlog #2 + v2.1 design idea 4
  (cache://sha256/<digest> locator scheme + cache_root_resolution
  block). Normalize on Tier-1 implementation.

**8. WebSearch occasional unavailability (status: surfaced — iter 5)**
- iter 5 attempted fresh WebSearch; got "claude-opus-4-7[1m] is
  temporarily unavailable". Pivoted to synthesis work on existing
  sources. Worked the next iter.
- **No fix needed**: external API availability is outside scope. Worth
  documenting that long-running /loop iterations should be resilient
  to transient WebSearch outages — synthesis / aggregation / validation
  work can substitute for fresh discovery.

**9. Saturation point at ~20 sources for solo dogfood (status:
   surfaced — iter 9-10 observation)**
- Iter 9 added VeriFact + synthesis claim; iter 10 added FAIR-RAG. New
  sources increasingly extend existing claim_family entries rather than
  introducing genuinely new mechanisms. Diminishing returns curve is
  visible.
- **Implication for v2.2 Tier-1 implementation**: the backlog is
  saturated enough to support implementation. Item 1 has 4 evidences
  (FActScore, VISTA, AtomEval, VeriFact); Item 3 has 3 (Attribute-First,
  C²-Cite, Gen-vs-Posthoc); Item 5 has 2 (Self-RAG, FAIR-RAG). Adequate.

**10. Iter discipline: 2 sources per iter is a healthy cadence
   (status: surfaced — methodological observation)**
- ~10 tool calls per source × 2 sources = 20 tool calls/iter for new
  discovery, plus validation/audit/export overhead. Iter typically
  completes in ~5 min of tool-active time. Sustainable for /loop.

---

## v2.1.0: anti-hallucination strict-live (Phase 7) — shipped 2026-05-19

**Theme**: 6 of 7 Tier-1 items from the external-research synthesis (3 batches,
8 streams) shipped as a coherent v2.1.0 bundle. Top concern (per user
2026-05-19): hallucination / over-claiming. v2.1.0 closes the gap between
"the source is real" (v2.0's cache_manifest) and "the link between source
and claim is real" (v2.1's span-anchored extraction_method).

**Schema**: `schema_version: 3` introduces required per-link verification
fields on `evidence_ledger.supports[*]`. v2 entries are grandfathered.

**Tier-1 items shipped** (6 of 7):
- #1 (commit `dd8beba`): span-anchored extraction_method + link_confidence
  + excerpt_anchor + substring validation. The load-bearing
  anti-hallucination mechanism — independent corroboration by GenProve
  (arXiv 2601.04932) and DataHub FineGrainedLineage.
- #1b (`dd8beba`): FACT-framework Claim Health section in dashboard.md
  (v3 only) — verbatim-anchored %, strong/partial/weak grounding counts.
  Pairs with /citation-audit's mechanical verifier.
- #2 (`dd8beba`): new `/citation-audit` skill + scripts/verify_citations.py
  driver. Substring + hash check across all supports[]; per-method
  breakdown; per-claim grounding strength.
- #3 (`48639e2`): CoVE factored verification in /dossier-audit Phase 3.
  Implements Dhuliawala et al. arXiv 2309.11495 — verification questions
  in fully decoupled contexts prevent post-rationalization.
- #4 (`dd8beba`): evidence_role_strength {full, partial, none} (Self-RAG
  IsSup) + multi-domain confidence.domains (GRADE-style) shipped as part
  of the v3 schema.
- #5 (`48639e2`): verbose validator error messages with closest-match
  suggestions in validators/freshness.py (via difflib.get_close_matches).
- #6 (`48639e2`): "Use when X" descriptions + paths globs across 6 v2/v3
  skills. Combats undertriggering when many skills compete.

**Tier-1 #7 shipped** (post-initial-v2.1.0 ship, before tagging release):
- #7 (commit `<v2.1.0d>`): WARC revisit records + 304-first conditional GET
  in `scripts/cache_source.py` + `validators/cache_manifest.py`. New
  `record_type` enum on cache_manifest entries (`capture` | `revisit` |
  `metadata` | `conversion`). Revisit records carry `refers_to_cache_id`,
  `refers_to_fetched_at`, `revisit_profile`
  (`server-not-modified` | `identical-payload-digest`), `http_status`,
  `http_etag`, `http_last_modified` — zero new bytes when the remote
  content hasn't changed. cache_source.py accepts `--if-etag`,
  `--if-last-modified`, `--prior-cache-id`, `--prior-sha256` to drive the
  conditional GET. 7 new tests cover the three response paths (304
  Not-Modified → revisit; 200 with identical hash → revisit; 200 with new
  content → capture linked to prior). All 7 of 7 Tier-1 items now shipped.

**Tests**: 201 passed + 2 xfailed. New v3 fixture
(`tests/fixtures/v3_strict_live_demo/`) with 1-entry verbatim_match anchor
demonstrating the substring validation works end-to-end. 8 new v3 tests
covering: fixture-passes, missing-extraction_method, missing-link_confidence,
link_confidence-above-cap, substring-mismatch, wrong-sha256,
llm_inferred-requires-inference_chain, manual_override-requires-user_note.

**Verification**: make v2-smoke clean across all 3 fixtures (v2 ai_agents
legacy, v2 multi_entry legacy, v3 demo strict). make builders-smoke clean.

**Ships as one-shot stable bundle** (per user 2026-05-19 framing). v2.1.0
is the active release; further design churn unlikely unless real-world
dogfood surfaces specific incidents. v2.1.1 backlog: Tier-1 #7 (WARC
revisit) + cross-project entity canonicalization in research-kb (Phase 8).

---

## Phase 6: v2 strict-live first-contact dogfood — applied 2026-05-19

**Theme**: first end-to-end run of the v2 chain on a real topic. Phase 0-3.5
shipped the v2 surface (validators, builders, skills, fixtures, docs) but the
chain had never been run against fresh sources. This dogfood is the
definition-of-done gate.

**Topic**: Browser-agent prompt-injection benchmarks. Project at
`~/Claude/research_browser_agent_pi_bench/`. One entry: AgentDojo
(Debenedetti et al. 2024, arXiv:2406.13352) — cached via real HTTP fetch of
the abstract page (47 KB HTML).

**Chain executed**:
1. `/research-plan` — research_plan.md written, validator OK.
2. `/research-gather` (v2 sub-phases manually executed) — bib_ledger.yml,
   cache_manifest.yml, evidence_ledger.yml hand-written; cache_source.py ran
   against arxiv.org/abs/2406.13352 and produced a real cache entry;
   build_claim_graph.py auto-generated claim_graph.jsonl.
3. *(skipped for dogfood scope)* `/dossier-build`, `/agent-index` — markdown
   rendering only; v2 trust artifacts don't depend on their output.
4. `/freshness-audit` Phase 5 (build_dashboard.py) — dashboard.md generated:
   "stale blockers: 0, evidence coverage: 2/2, cache completeness: 1/1, weak
   claims: 0, Refresh active benchmark pages by 2026-08-17."
5. `/research-kb-export` — produced
   `~/Claude/research-kb/inbox/research_toolkit/research_browser_agent_pi_bench.jsonl`,
   validator OK.

**Verdict**: v2 chain PASSES the definition-of-done gate. The full chain ran
without manual yaml editing of *validated* artifacts (bib_ledger entries,
evidence_ledger entries, claim_graph, dashboard, export). Validators clean,
export sits in research-kb inbox ready for future ingestion. Friction items
below are surfacings, not blockers.

### Friction items (8 surfaced, 5 deferred to v2.1, 3 applicable for v2.0.1)

**1. cache_source.py default cache_root produces absolute paths (status: surfaced — design tension)**
- Default `--cache-root ~/Claude/research_cache` writes raw blobs at
  `~/Claude/research_cache/blobs/sha256/<hash>` and prints those absolute
  paths in the manifest YAML entry. The v2 fixture (the only documented
  example) uses project-local relative paths (`cache/raw/<file>.html`)
  because its cache lives inside the project.
- Absolute paths break portability — copying the project to another machine
  breaks the cache references. Relative paths from a global cache require
  awkward `../..` traversal.
- **Why it matters**: the inconsistency means a user dogfooding from scratch
  produces something that doesn't structurally match the canonical fixture.
- **Action for v2.1**: pick one. Either (a) default cache_source.py to
  project-local cache (then it can produce relative paths), or (b)
  explicitly document that global cache + absolute paths is the convention,
  and update the fixture to demonstrate it.

**2. cache_source.py prints YAML but doesn't append to cache_manifest.yml (status: surfaced — automation gap)**
- Skill body says "record the resulting cache entry in cache_manifest.yml"
  but the script only prints stdout. User copy/pastes into the manifest.
- Per-source manual paste is fine for 1-2 sources; tedious for 20+.
- **Action for v2.1**: add `--append <manifest>` flag to cache_source.py
  that appends directly. Also stops the copy/paste error mode (truncated
  paths, lost fields).

**3. Acronym handling miss for "PI" (status: applied 2026-05-19 — small fix)**
- Dashboard title rendered "Browser Agent Pi Bench" instead of "Browser
  Agent PI Bench" — "pi" wasn't in the ACRONYMS set in build_dashboard.py.
- Fixing inline below; trivial.

**4. /research-gather Phase 4 sub-steps are mostly manual (status: surfaced — design tension)**
- Phase 4 v2 sub-section enumerates 3 steps (cache_manifest, evidence_ledger,
  claim_graph). claim_graph is fully mechanized via build_claim_graph.py;
  cache_manifest and evidence_ledger are LLM-driven (write per fixture
  template).
- A user-as-LLM agent has to: read the template, populate fields, find the
  excerpt by grepping the cached HTML, assign bibkeys, etc. Tedious for many
  sources.
- **Why it matters**: this is the longest stage in a real dogfood (20-source
  effort). The friction compounds with source count.
- **Action for v2.1**: design a `build_evidence_ledger_skeleton.py` and
  `build_cache_manifest_append.py` so the skill becomes "search → review →
  run builders" rather than "search → write YAML by hand → run one builder."

**5. Excerpt extraction is unguided (status: surfaced — skill body gap)**
- evidence_ledger.yml entries require a non-empty `excerpt` field. For
  arXiv papers, the abstract is typically the right excerpt. For benchmark
  websites or vendor blogs, it's less obvious which span to quote.
- The skill body doesn't say "grep `<meta name='citation_abstract'>` from
  the cached HTML" or similar. LLM has to figure out where to look.
- **Action for v2.1**: add an "excerpt-selection cheatsheet" reference doc
  with per-source-type hints (arXiv: citation_abstract meta tag; vendor
  blog: first paragraph after H1; etc.).

**6. No automated check that bib_ledger entries fall within plan time scope (status: surfaced — minor)**
- Research plan declared "2025-2026 releases"; my landmark AgentDojo is
  2024-06-19. The chain accepted this silently.
- **Action**: probably wontfix — time scope in the plan is editorial, not
  contractual. The dogfood-ing user can self-correct.

**7. /dossier-build and /agent-index aren't on the v2 trust chain critical path (status: surfaced — narrative gap)**
- Skipped both during the dogfood without breaking anything. The v2
  validators (freshness, evidence, cache_manifest, claim_graph,
  research_kb_export) all pass without dossier files or agent-index
  markdown existing.
- **Why it matters**: the skill bodies and workflow_overview.md present the
  chain as "/research-gather → /dossier-build → /agent-index → /freshness-audit
  → /research-kb-export" — implying linear dependency. But the v2 trust
  artifacts are strictly a sub-chain: gather → freshness → export. The
  markdown chain (dossier + agent-index) is a parallel rendering track.
- **Action for v2.1**: split the skill chain documentation into "trust chain"
  vs. "rendering chain" — they share inputs but produce different artifacts.

**8. claim_graph builder produces 2 entities when bib + dataset share a URL (status: deferred — known design choice, see v2.0 backlog item #4)**
- Not exercised in this single-entry dogfood. Will revisit when a multi-source
  project has paired bib + dataset entries.

### Phase 4 of /freshness-audit (rescan volatile sources) sufficiency verdict

**Inconclusive — dogfood ran offline-style.** I cached arxiv.org/abs/2406.13352
directly without first WebSearching for "recent browser-agent benchmarks 2026"
to surface fresher sources. A complete dogfood would have started with the
rescan and surfaced any 2025-2026 benchmark releases I might have missed
(BrowserGuard, SafeBrowse, AgentSec, etc.). The skill body's Phase 4 lists
the right categories (arXiv / HF / GitHub / leaderboards / vendor blogs /
policy) but doesn't enforce running them; this dogfood proves the chain
works structurally but didn't exercise discovery rigor.

**Action**: defer Phase 4 sufficiency verdict to a future dogfood that
specifically exercises the rescan path (or implement v2.1 proactive
mechanisms per [[project-research-toolkit]] backlog item #1).

### Applied fixes during this dogfood

- Added "pi" to `scripts/build_dashboard.py` ACRONYMS set (was rendering
  "Pi" instead of "PI" for `browser_agent_pi_bench` topic). Will be in the
  Phase 4 commit alongside this BURN_IN entry.

---

## Phase 7: v2 strict-live multi-source dogfood — applied 2026-05-19

**Theme**: Phase 4's dogfood was single-source (AgentDojo only). Phase 5's
job is multi-source mixed-tier coverage: 5+ entries, multiple freshness
tiers, multi-evidence per claim, restricted source, hand-injected
contradiction. Surfaces friction the v2.1 Tier-1 design needs to address.

**Topic** (extended from Phase 4): browser-agent prompt-injection benchmarks.
Project at `~/Claude/research_browser_agent_pi_bench/`. **5 entries**:
- `debenedetti2024agentdojo` — active, primary paper (AgentDojo, real cache)
- `owasp2025llm01` — stable, official standard (OWASP LLM01:2025, real cache)
- `anthropic2026computeruse` — volatile, official vendor (real cache)
- `browserbench2025adversarial` — volatile, primary benchmark (synthetic
  cache, example.com URL)
- `restricted2025threatreport` — stable, secondary, **restricted** distribution
  (synthetic cache, rights_status=restricted, restricted=true)

**Chain executed** (only the v2 trust chain — skipped /dossier-build and
/agent-index as in Phase 4 since they're rendering-only):
1. Cache 3 real sources via `scripts/cache_source.py` (AgentDojo carryover +
   OWASP LLM01 + Anthropic computer-use docs).
2. Create 2 synthetic cache blobs for benchmark + restricted scenarios.
3. Hand-write `bib_ledger.yml` (5 entries with mixed freshness_tiers),
   `cache_manifest.yml` (5 cache entries, mixed global + project-local
   paths), `evidence_ledger.yml` (6 evidence entries; one multi-supporting
   claim `claim_browser_pi_real_threat` with 4 evidence_ids spanning all
   source qualities).
4. Run `scripts/build_claim_graph.py` — auto-generated 5 entities + 5
   sources + 4 claims (multi-evidence tiebreak picks primary's excerpt as
   text; entity_ids aggregate from all contributing ledger entries) + 6
   evidences + 5 cache_blob records.
5. **Hand-inject contradiction claim**: python one-liner edited
   `claim_defense_efficacy_disputed` to `claim_type: contradiction`,
   `status: conflicted`, `confidence.score: 0.70`, added second evidence_id.
6. Run `scripts/build_dashboard.py` — dashboard reflects: 4/4 coverage,
   5/5 cache, **1 conflict** (the injected), **1 weak claim** (the same
   one at 0.70), 3-tier Action Queue (volatile + active + stable lines).
7. `validators/freshness.py --strict` ✅, `validators/research_kb_export.py` ✅.

**Verdict**: v2 chain passes at multi-source scale. Builder's multi-evidence
aggregation works correctly: claim_browser_pi_real_threat correctly took
the primary evidence's excerpt as canonical text, aggregated entity_ids
from all 4 contributing ledger entries, and listed all 4 evidence_ids.
Confidence factors aggregate across source_quality and verification_method
values seen.

### Friction items (9 surfaced, 1 applied, 8 deferred to v2.1.0)

**1. Manual bib_ledger entries scale linearly with source count (status: surfaced — already #4 in Phase 4)**
- Phase 4 had 1 entry. Phase 5 had 5 entries. Friction is linear in source
  count: every entry needs hand-extracted title/authors/venue/code_url +
  v2 fields populated.
- **v2.1.0 fix**: skeleton builders + per-source-type cheatsheet (Tier-2
  R1 Idea 6 + new `templates/excerpt_extraction_cheatsheet.md`).

**2. Excerpt extraction from large pages is unguided (status: surfaced — confirmed at scale)**
- OWASP page = 305 KB; Anthropic computer-use docs = 1.6 MB. The text_path
  derivative contains all HTML noise (menus, footer, JS comments). Finding
  the quotable substring is manual grep.
- **v2.1.0 fix (linked to Tier-1 #1 span-anchored extraction_method)**: with
  byte-offset anchoring required for verbatim_match, the friction shifts
  from "find the right span" to "find AND record its offset" — making it
  more rigorous but more work per evidence. Possibly mitigates with a
  `scripts/locate_excerpt.py` helper.

**3. Hand-injecting contradiction claim required ad-hoc Python (NEW friction)**
- No skill or template documents "how to add a `claim_type: contradiction`
  record to `claim_graph.jsonl`." The builder produces `fact` by default;
  upgrading requires direct jsonl edit.
- **v2.1.0 fix**: new `references/synthesis_claims_protocol.md` documents
  the pattern: rebuild claim_graph from ledgers, then append synthesis-only
  claims (contradiction / open_question / user_judgment) via a separate
  `scripts/append_synthesis_claim.py` or direct jsonl edit.

**4. Action Queue falls back to generic "entries" when tier has mixed entity_types (status: surfaced — design choice working as intended)**
- Volatile tier had `vendor_eval` + `benchmark` → noun fallback "entries."
- Stable tier had `attack_taxonomy` + `vendor_eval` → also "entries."
- Active tier had only `benchmark` → specific "benchmark pages."
- Working as designed (Phase 3 polish item 10b); just noting it for the
  multi-source case.

**5. Restricted source's evidence still aggregates into multi-evidence claim confidence (status: surfaced — NEW, important)**
- `ev_restricted_finding` (secondary, restricted) contributed to
  `claim_browser_pi_real_threat`'s confidence factors and entity_ids,
  alongside primary/official evidence.
- The primary evidence's excerpt wins tiebreak (correct) and the score
  doesn't drop, BUT the claim's entity_ids now include
  `ent_restricted2025threatreport`. If this claim is exported via
  research_kb_export.jsonl, the restricted entity is exported too.
- **v2.1.0 fix (via Tier-1 #1)**: span-anchored extraction_method + per-link
  `link_confidence` would let the validator exclude restricted-source
  contributions from confidence aggregation, OR flag them explicitly. Pair
  with restricted-export-filter (one of the surfaced anti-patterns in the
  research synthesis).

**6. Mixed global + project-local cache paths in one manifest (status: surfaced — Phase 4 friction #1 confirmed at scale)**
- 3 entries with absolute paths (`/Users/brandonbehring/Claude/research_cache/blobs/sha256/...`)
  from cache_source.py default.
- 2 entries with relative paths (`cache/raw/browserbench.html`) from project-local cache.
- Validator handles both via `_resolve()`; visually confusing in the YAML.
- **v2.1.0 fix**: Tier-2 R1 Idea 4 (cache_locator URI scheme like
  `cache://sha256/<digest>` + `cache_root_resolution:` mapping). Not in
  Tier-1 because doesn't directly address hallucination.

**7. Real-world cached pages contain non-content noise (status: surfaced — NEW)**
- Anthropic docs at 1.6 MB extracted to a text file with ~95% non-content
  (navigation, sidebars, JS, "Try it" widgets). Grep needed `prompt
  injection` keyword to find the relevant span.
- text_path derivative is "everything decoded as UTF-8" — no semantic
  filtering.
- **v2.1.0 deferred**: content-aware extraction (boilerpipe / Readability /
  trafilatura) is a separate concern. Defer to v2.2; v2.1 will surface it
  via Tier-1 #1's substring check (which doesn't care about noise — it
  just verifies the cited substring exists).

**8. No /research-gather guidance for restricted sources (status: surfaced — NEW)**
- The skill says "cache every reachable source" but doesn't say "for
  restricted sources, set rights_status: restricted + restricted: true on
  cache_manifest entry AND make sure not to export the cache_id downstream
  if the source can't be shared." The dogfood produced a restricted entry
  but the chain doesn't enforce restricted-aware exports.
- **v2.1.0 fix**: explicit restricted-handling section in
  `/research-gather` skill body + an export-time filter (`scripts/research_kb_export.py`
  drops cache_ids where the manifest entry has `rights_status: restricted`
  or `cache_only`).

**9. Cross-source claims need editorial judgment that builders can't supply (status: surfaced — confirms v2.0 backlog #3 "claim_type inference")**
- `claim_browser_pi_real_threat` aggregates 4 evidence entries from 4
  different sources. The builder uses the primary's excerpt as claim text
  but that excerpt is AgentDojo-specific ("AgentDojo poses a challenge...").
  A better synthesis would unify the evidence into a single cross-source
  statement ("Prompt injection in browser agents is recognized as a top
  risk by both academic [Debenedetti 2024] and standards [OWASP 2025]
  sources, with vendors [Anthropic 2026] adding defensive layers.").
- **v2.1.0 fix**: this is editorial / synthesis work. The skill body can
  guide it but the builder shouldn't synthesize. Possible v2.2 item:
  /research-gather Phase 4b synthesis pass that LLM-rewrites claim text
  when 3+ evidences support it.

### Applied during this dogfood
- Hand-injected contradiction claim into claim_graph.jsonl (cannot become
  a Tier-1 fix because it's editorial; documented as friction #3 above).

### Updates to v2.1.0 Tier-1 priorities based on Phase 5

**Confirms Tier-1 #1 (span-anchored extraction_method) as TOP priority.**
The multi-source friction items #5 (restricted-source confidence
contamination), #8 (no restricted-aware export filter), and #7 (text_path
noise) are all addressed by mechanical substring validation: once every
verbatim_match excerpt is validated against `text_path[start:end]`, the
restricted source either passes (it has a real quoted span) or fails (no
match, fall through to manual_override which caps confidence at 0.5 and
flags for filtering). Pair with #2 (citation-audit skill running every
build).

**No re-ordering required.** The 7 Tier-1 items stand. The multi-source
scale validates that builders + dashboard work correctly; the missing
piece is per-link evidence verification, which is exactly #1.

---

## v2.0 backlog (seeded 2026-05-19, pending dogfood)

Items the v2.0 audit + completion plan repeatedly punted on. Status will be revisited during Phase 4 dogfood and consolidated into the v2.1 design cycle.

1. **Proactive freshness mechanisms** — `/freshness-audit` Phase 4 is currently LLM-driven (lists rescan categories: arXiv / HF / GitHub / leaderboards / vendor blogs / policy). Sufficiency depends on the LLM's discovery rigor. v2.1 candidates: scheduled rescans via `/loop`, change-detection diffs on cached sources, content-hash polling for volatile-tier entries.
   - **Status:** `deferred` — verdict pending Phase 4 dogfood.

2. **`/dossier-build` evidence-ID preservation in rendered tables** — Phase 1 decision (2026-05-19): dropped the "preserves strict-live verification status" claim from the description because the skill is rendering-only. If Phase 4 dogfood shows dossier tables would benefit from evidence-ID cells (e.g., reviewer wants to trace claims from dossier rows), revisit as v2.1 feature.
   - **Status:** `deferred` — pending dogfood signal.

3. **Builder claim_type inference** — `scripts/build_claim_graph.py` emits all claims as `claim_type: fact`. The validator allows `fact / comparison / trend / risk / recommendation / contradiction / open_question / user_judgment`. Inferring from evidence content (e.g., contradictory excerpts → `contradiction`) would require either evidence_role propagation or LLM judgment. Current handling: any non-fact claim_type must be hand-curated in `claim_graph.jsonl` or added by `/agent-index` Phase 4b.
   - **Status:** `deferred` — current "always fact" is mechanical-honest; LLM/skill orchestration handles richer cases.

4. **Entity-merging across bib + dataset by primary_url** — builder design choice: one entity per bibkey (so bib + dataset entries sharing a primary_url produce 2 entities). The hand-curated v2_strict_live_ai_agents fixture merges them into 1 entity (`ent_benchmark_agent_security` with alias "ASB"). Both are valid; builder chose deterministic-simple, fixture chose editorial-clean. If Phase 4 dogfood produces noisy claim_graphs with redundant entities, revisit as v2.1 (e.g., `merge_with:` field on ledger entries).
   - **Status:** `deferred` — design choice, not a bug.

5. **`/freshness-audit` Phase 4 sufficiency verdict** — does the LLM-driven volatile-area rescan catch recent changes the initial gather missed? Only first-contact dogfood will tell. If yes: close as adequate, document in Phase 4 BURN_IN. If no: open as v2.1 design item (likely overlaps with #1).
   - **Status:** `deferred` — pending Phase 4.

6. **research-kb ingestion pipeline** — explicitly out of scope for v2.0 (separate repo, not local). The toolkit ships a lossless verbatim-wrap export contract; future ingestion can parse `payload.*` directly. When the user brings research-kb code local, add a contract verification step.
   - **Status:** `wontfix` (in this repo) — belongs in research-kb.

---

## Cross-cutting observations

(non-stage-specific friction lives here — e.g., "templates dir resolution from foreign CWD", "WebFetch rate-limit recovery")

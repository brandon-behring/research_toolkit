# Subagent audit — research_toolkit, 2026-05-28

## Context

You asked whether `research_toolkit` "took advantage of subagents for good context delegation." This audit applies your own multi-agent research dossier (`claude-books/docs/research/06-multi-agent-patterns/`, 5 T1-official sources, snapshot 2026-05-22) as the reference standard. No external "best practice" assertions — every pattern and decision gate cited here comes from those sources.

This is a learning/hygiene audit at v2.5.0 (Wave 7 = 23-wide composed KG). No concrete pain trigger fired; nothing here proposes a v2.6 change. It's input to roadmap thinking, not the roadmap.

---

## 1. The reference framework (your research's converged vocabulary)

### 1.1 Four primary patterns (when to *actually* reach for subagents)

The decision framework's three "yes" scenarios + the one verification pattern. From [`blog-when-to-use-multi-agent.md`](../../../claude-books/docs/research/06-multi-agent-patterns/blog-when-to-use-multi-agent.md) and [`blog-multi-agent-research-system.md`](../../../claude-books/docs/research/06-multi-agent-patterns/blog-multi-agent-research-system.md):

- **Context Protection** — one subtask generates >1000 tokens of irrelevant intermediate data; isolated subagent returns a compact synthesis to the coordinator
- **Parallelization** — independently-decomposable facets run in parallel subagents. *Gain is thoroughness, not speed.*
- **Specialization** — task routed to a domain-focused subagent (triggered by >20 tools or conflicting system-prompt personas in a single-agent design)
- **Verification Subagent** — separate verifier blackbox-tests the main agent's output, blind to the writer's conversation history. **"The only multi-agent pattern that consistently succeeds across domains"** (line 68 of dossier README). Critical mitigation: verifier must run a complete check, not declare early victory.

### 1.2 Four supporting/architectural patterns

The structural pieces that make the above work. From [`docs-multiagent-sessions.md`](../../../claude-books/docs/research/06-multi-agent-patterns/docs-multiagent-sessions.md), [`docs-best-practices-writer-reviewer.md`](../../../claude-books/docs/research/06-multi-agent-patterns/docs-best-practices-writer-reviewer.md):

- **Isolated-Context Window** — subagents have their own model/system-prompt/tools/MCP; do not inherit parent state
- **Hub-and-Spoke Coordination** — lead agent analyzes, spawns 3-5 subagents in parallel, synthesizes
- **Artifacts Pattern** — subagents output to filesystem; coordinator gets a lightweight reference back, not the full output
- **Writer/Reviewer Pattern** — two sessions; reviewer reads code fresh, with no inherited bias from the writer

### 1.3 The decision gates (try these BEFORE multi-agent)

From the dossier README's compact table (lines 57-67):

1. Can improved single-agent prompting get the result?
2. Does Tool Search Tool reduce tool overhead enough?
3. Does context compaction extend the horizon enough?
4. **Are there *true* context boundaries in the task, or is the decomposition synthetic?**
5. Is task value worth 3-10× token cost?

If yes to 1-3: stay single-agent. If no to 4: do NOT split (anti-pattern territory). If no to 5: stay single-agent.

### 1.4 Three anti-patterns

- **Problem-Centric / Role-Based Decomposition** — splitting by role (planner/implementer/tester) instead of by context boundary. Drives the documented 40% multi-agent pilot failure rate. Symptom: more tokens coordinating than executing; telephone-game context loss at every handoff.
- **Overspawning** — 10+ subagents for queries that the decomposition heuristic (1 / 2-4 / 10+) would put in the simple tier
- **Depth > 1 Hierarchies** — subagents spawning subagents. Hard-ignored in Managed Agents.

### 1.5 Architectural facts to remember

- Depth-1 only (coordinator → subagents; no nesting)
- 25-thread concurrency cap per session
- Shared container/filesystem/vault but isolated per-thread context
- ~4× token multiplier for agents, ~15× for multi-agent (vs chat)
- Token usage explains ~80% of performance variance — fewer richer agents often beats more thinner ones

---

## 2. Toolkit's current subagent usage

### 2.1 The one placement — and it's exemplary

`/dossier-audit` Step 3b is the toolkit's only subagent dispatch. Its shape:

- Step 3a: ONE subagent generates 2-3 verification questions per in-scope entry (question generation, blind to dossier prose to avoid anchoring)
- Step 3b: MULTIPLE subagents, one per question, each receives `{question, source_url}` only — never the synthesis text it's checking. WebFetch-based blackbox verification.
- Step 3c: Main thread aggregates DROP/CORRECT/FLAG/SPOT-CHECK verdicts.

Framework mapping: this is the **Verification Subagent** pattern (the one consistently-succeeding pattern from the research) wired together with **Isolated-Context Window** (verifiers never see synthesis) + **Hub-and-Spoke** (auditor coordinator spawns N verifiers in parallel) + **Artifacts Pattern** (each verifier writes a finding, main thread merges). Four of the eight framework patterns, applied correctly to one concrete task.

The "early-victory" mitigation from the framework (verifier must run a complete check, not declare done early) shows up in the toolkit as structured output: each verifier must produce a categorical verdict, not free-form approval. Different shape, same defense.

### 2.2 The supporting discipline (when single-agent + discipline substitutes for subagents)

Across every other skill, the toolkit defaults to single-agent execution and invests in *discipline* to manage context pressure:

- `/research-gather` Phase 2: ~25-30 tool-call dispatch cap, with explicit guidance to "split high-volume sub-areas across two narrower agents rather than one wide one" (manual workaround for what Parallelization would do structurally)
- `gather_trace.yml` with `fetch_id` dedup (BURN_IN `w2-cross-track-fetch-id`): the merge primitive that *would* be needed for Parallelization, already shipped — for the merge of parallel *tracks*, not parallel *subagents*
- Canonical enum pinning in gather briefs (BURN_IN `w3-gather-enum-drift`): keeps a wide-context agent first-try-clean by tightening the prompt; what Specialization would do structurally
- The Attribute-First firewall in `/agent-index` Phase 2a → 2b → 2c: serializes span-select → manifest lock → prose render to make "post-hoc rationalization structurally impossible"; what Writer/Reviewer would do structurally

This is exactly what decision gates 1-3 prescribe: improve prompting / use the merge primitives in-process / extend the single-agent horizon. Each instance has a BURN_IN trail showing the design was the *result* of friction, not a guess.

---

## 3. Per-skill audit

Verdict legend:
- ✅ Single-agent correct (and why)
- 🟡 Latent — would benefit at higher scale; specifies the trigger
- 🟢 Crosses the threshold at current scale — names the framework pattern + merge primitive
- ⛔ Anti-pattern detected (none expected; the explicit check is the point)

### 3.1 Planning + discovery

| Skill | Verdict | Framework analysis |
|---|---|---|
| `/research-plan` | ✅ | Single-pass generative task; no loop, no facets, no >1000-token intermediate data. Decision gate 4: no true context boundary. Single-agent correct. |
| `/topic-discovery` | ✅ | Corpus-internal traversal of a small fixed input. Decision gate 5: not worth 3-10× token cost at this volume. Single-agent correct. |

### 3.2 Gathering

| Skill | Verdict | Framework analysis |
|---|---|---|
| `/research-gather` Phase 2 (per-sub-area discovery) | 🟢 | 4-8 sub-areas, each independent → **Parallelization** pattern. Each sub-area's WebSearch+WebFetch loop generates substantial intermediate context that's irrelevant to the others → also satisfies **Context Protection**. The ~25 tool-call cap + "split high-volume sub-areas across two narrower agents" is the manual workaround for exactly this pattern. Effort-scaling: 4-8 agents fits the "direct comparison" tier (2-4) or low end of "complex" (10+). Merge primitive (`fetch_id` dedup) already shipped from the cross-track work in Wave 2. Phase 3 (bibkey + claim_family assignment) stays main-thread — **Specialization** of the classifier brief, applied to a narrower input. |
| `/research-gather` Phase 4 (cache loops) | ✅ | `scripts/cache_source.py` calls are I/O-bound and deterministic; parallelism belongs at the script/process layer (Python multiprocessing), not subagent. Decision gate 1: not a prompting problem. |
| `/dataset-gather` Phase 2 (per-category sweep) | 🟡 | 8 source-category sweeps, each with a distinct strategy (HF / Kaggle / Zenodo / Google DS / cloud / domain / gov / UCI-OpenML) → **Specialization + Parallelization**. Same shape as `/research-gather` but run far less often. Trigger: a dataset-heavy project where category sweep dominates runtime. |

### 3.3 Dossier rendering

| Skill | Verdict | Framework analysis |
|---|---|---|
| `/dossier-build` | ✅ | Renders ~100-200 table rows from one ledger. Decision gate 4: no true context boundary between rows; rows are uniform. Decision gate 5: rendering completes in seconds; not worth 3-10× cost. Single-agent correct. |
| `/dataset-index` | ✅ | Same shape as `/dossier-build`. Single-agent correct. |

### 3.4 Synthesis (the high-stakes one)

| Skill | Verdict | Framework analysis |
|---|---|---|
| `/agent-index` Phase 2a (per-entry span-select) | 🟢 | At 23-wide scale: ~25 sources × 23 projects ≈ 575 entries × 2-5 atomic claims each. Each entry's span-select reads `cache_manifest.yml` → `text_path` then calls `build_excerpt_anchor.py`. True context boundary per entry (decision gate 4 ✅); each entry's cached-text read generates substantial intermediate context irrelevant to other entries (**Context Protection** ✅); independently parallelizable (**Parallelization** ✅). Phase 2b (manifest lock) and Phase 2c (prose render) **must stay serial in main thread** — the Attribute-First firewall is structurally enforced by the picker-never-becomes-the-writer rule, which subagent dispatch makes architectural rather than disciplinary (**Writer/Reviewer Pattern**, exact match). Merge primitive: `text_path_offset` + `sha256_of_span` (byte-correct, deterministic, idempotent per entry); no cross-entry conflict possible. |
| `/agent-index` Phase 2b/2c | ✅ | Manifest lock + prose render must serialize to maintain the Attribute-First guarantee. Decision gate 4: parallelization here would *break* the firewall. Single-agent correct (and required). |
| `/agent-index` Phase 4c (synthesis_entry scaffold) | ✅ | <10 synthesis claims per dossier. Decision gate 5: volume too low. Single-agent correct. |

### 3.5 Audit + verification

| Skill | Verdict | Framework analysis |
|---|---|---|
| `/dossier-audit` Step 3b | ✅ exemplary | Already implements **Verification Subagent + Isolated-Context Window + Hub-and-Spoke + Artifacts**. The one consistently-succeeding multi-agent pattern from the research, applied correctly. Keep. |
| `/freshness-audit` Phase 3 (stale-refresh) | 🟡 | Per-entry re-fetch is independently parallelizable (**Parallelization**). Same merge primitive as `/research-gather` (`cache_id` + sha256). Trigger: an audit run where stale-refresh takes >5 minutes or context overflows. Not yet observed. |
| `/citation-audit` | ✅ | Calls `scripts/verify_citations.py` — a deterministic substring-check script. Decision gate 1: prompting irrelevant; this is mechanical. If parallelism is wanted, it belongs at the Python process layer, not the skill layer. |
| `/url-freshness-check` | ✅ | Already parallelized at the right layer — inline Bash `curl &` chunks. Subagent dispatch would be slower than the existing implementation for the URL-HEAD workload. |

### 3.6 Export + utility

| Skill | Verdict | Framework analysis |
|---|---|---|
| `/research-kb-export` | ✅ | Validation + JSONL emit only. No loop, no facets. Single-agent correct. |
| `/dataset-research` | ✅ | Wrapper around `/dataset-gather` + `/dataset-index`; no own work. |
| `/dataset-synthesize` | ✅ | Already uses prompt caching + cost bounds at the API layer. Subagent dispatch would not improve context delegation — the Claude API call shape is fixed by the synthetic-data contract. |

---

## 4. Cross-cutting observations

### 4.1 The toolkit's design philosophy, viewed through the framework

The toolkit's bias is: **single-agent + discipline, with one Verification Subagent exception**. This is exactly what the decision framework prescribes — try the gates 1-3 fixes (prompting / Tool Search / compaction substitutes / merge primitives in-process) before reaching for subagents, and reach for subagents only when the consistently-succeeding pattern (verification) is the right answer.

Every supporting discipline you've shipped has a BURN_IN trail. The canonical enum pinning came from `w3-gather-enum-drift`. The `fetch_id` dedup primitive came from `w2-cross-track-fetch-id`. The Attribute-First firewall came from the v2.2 design cycle's anti-rationalization push. None of these were speculative; each was a friction-driven response. That's the right posture per the framework's own advice on cost-justification.

### 4.2 Where the discipline starts to *look like* context-pressure evidence

A few of the in-process disciplines are subagent-pattern-shaped responses to context-window limits, implemented without subagent dispatch:

- The ~25 tool-call dispatch cap in `/research-gather` Phase 2 — a manual stand-in for what **Parallelization** would do structurally
- The Attribute-First firewall in `/agent-index` — a clever in-context stand-in for what **Writer/Reviewer** would do structurally (the picker can't see what the writer will produce because the writer hasn't run yet, but they share a context until Phase 2c starts)
- The `gather_trace.yml` `fetch_id` dedup primitive — designed for cross-track merge (multi-process), reusable as-is for cross-subagent merge if dispatch ever ships

These aren't bugs; they're working code at current scale. They're *also* the right merge primitives for the day a real friction trigger arrives. If/when that day comes, the conversion would be structural, not architectural.

### 4.3 The two skills that cross the threshold at 23-wide

`/research-gather` Phase 2 and `/agent-index` Phase 2a are the two placements where (a) all four decision gates resolve in favor of multi-agent at current scale (true context boundaries; substantial irrelevant intermediate context; cost worth it given 23-wide repetition; not addressable by more prompting), and (b) the merge primitives are already shipped. Phase 2a additionally has the strongest framework match — the Attribute-First firewall is **Writer/Reviewer** applied to span-selection vs. prose-rendering, currently enforced by serialization-in-one-context, convertible to structural enforcement at any time.

---

## 5. Watch list — what crosses at what trigger

For each at-threshold or latent placement, the framework pattern that fits and the concrete trigger:

### 5.1 At threshold now (would justify v2.6 design cycle)

| Placement | Framework pattern | Merge primitive | Trigger |
|---|---|---|---|
| `/research-gather` Phase 2 | Parallelization + Context Protection + Artifacts | `gather_trace_<subarea>.yml` fragments merged by `fetch_id` | A single sub-area dispatch ever exceeds ~30 tool calls, OR a Wave-N project where main-thread context degrades during gather |
| `/agent-index` Phase 2a | Parallelization + Writer/Reviewer (structural) + Artifacts | `pre_selection_manifest_<batch>.yml` fragments merged by `claim_id` + byte-offset+sha256 | A `/agent-index` run on a single dossier exceeds ~10 minutes, OR composed-KG projects hit 30+ wide |

### 5.2 Latent (defer until friction)

| Placement | Framework pattern | Merge primitive | Trigger |
|---|---|---|---|
| `/freshness-audit` Phase 3 | Parallelization + Artifacts | cache_manifest fragments merged by `cache_id` + sha256 | An audit run where stale-refresh dominates >5 min, OR a 23-wide composed audit hits context overflow |
| `/dataset-gather` Phase 2 | Parallelization + Specialization (per-category brief) | dataset_ledger fragments merged by canonical dataset key | A dataset-heavy project where the 8-category sweep dominates runtime |

### 5.3 Explicit NOT in scope

| Placement | Why not |
|---|---|
| `/dossier-build` rendering | Decision gate 4: no true context boundary between rows |
| `/dataset-index` rendering | Same |
| `/topic-discovery` | Decision gate 5: corpus-internal, low volume |
| `/citation-audit` | Mechanical script; parallelism belongs at Python layer if anywhere |
| `/research-plan` | Single-pass generative |
| `/research-kb-export` | Validation + JSONL emit only |
| `/url-freshness-check` | Already parallelized at the right layer (Bash `curl &`) |
| `/agent-index` Phase 2b/2c | Parallelizing here would *break* the Attribute-First firewall |

---

## 6. Anti-pattern check

Explicit verdicts against each of the three framework anti-patterns:

- **Problem-Centric / Role-Based Decomposition** — **not found.** No skill chains planner→implementer→tester→reviewer subagents. The closest analog (`/dossier-audit`'s Step 3a question-gen → Step 3b verify → Step 3c aggregate) is *context-centric* decomposition — each subagent gets a different input scope, not a different role on the same data. This is the framework-blessed shape.
- **Overspawning** — **not at risk.** The toolkit's effort-scaling stays in the "direct comparison" tier (2-4 verifiers per audit) for current usage. Even the at-threshold candidates above (Phase 2a span-select) max out around 12-15 subagents at 575+ entries, well below the 25-thread concurrency cap.
- **Depth > 1 Hierarchies** — **not found.** Every subagent (current `/dossier-audit` 3a/3b, plus any future placement from §5) is spawned from the main thread. No subagent spawns subagents.

---

## 7. What this audit does NOT do

- Does not propose v2.6 changes — the at-threshold §5.1 placements are candidates for the design cycle when a concrete trigger fires, not commitments
- Does not edit any SKILL.md
- Does not write a BURN_IN_NOTES entry — this is hygiene/learning material, not friction-driven
- Does not assert subagent patterns beyond what your dossier sources say — every pattern named here traces back to a T1 file in `claude-books/docs/research/06-multi-agent-patterns/`

Future-you reads this when a concrete trigger does fire (a slow gather, a Phase 2a timeout, a context overflow during an audit) and uses the §5 watch list to scope the design-cycle response. Until then, the toolkit is making the right calls: single-agent + discipline aligns with the decision framework's bias, and the one subagent placement is the documented gold-standard pattern.

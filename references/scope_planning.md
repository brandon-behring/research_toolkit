# Scope planning

Guidance for `/research-plan` on how to scope a research topic so the rest of the pipeline produces something useful instead of something exhaustive.

## How aggressive to be with "out of scope"

Default to **aggressive** scope-cutting. The most common failure mode in research workflows is "everything is interesting, nothing gets covered well." Concretely:

- If a sub-area would itself require a multi-week effort, cut it. List it in `## Out-of-scope` with a note like "deserves its own research plan; deferred."
- If a sub-area is closely related but methodologically distinct (e.g., supervised vs unsupervised, training-time vs inference-time), make it a separate plan instead of subsuming it.
- The `## Out-of-scope` section is a hard requirement of the validator (must be non-empty). Empty out-of-scope means the topic isn't really scoped — the plan was written defensively to leave the door open. Don't.

## When to split a topic into multiple plans

If your initial decomposition produces:
- More than 8 sub-areas, OR
- Sub-areas with very different source-type profiles (e.g., one sub-area wants arXiv papers, another wants vendor blogs, another wants regulatory documents),

split into multiple plans. Each plan should fit a single research-gathering posture (mostly arXiv + GitHub, OR mostly vendor blogs, OR mostly standards bodies). Mixed source-type plans produce inconsistent dossiers because the citation rules differ across source types.

## Sizing the claim_family taxonomy

Aim for **3–8 categories**. Fewer than 3 and the taxonomy isn't really a categorization; more than 8 and it becomes hard for `/research-gather` to consistently classify entries.

Good claim_family values:
- Topical (`benchmark`, `dataset`, `toolkit`, `survey`)
- Methodological (`attack_direct`, `attack_indirect`, `defense_detection`, `defense_alignment`)
- Phase-of-pipeline (`training_time`, `inference_time`, `post_deployment`)

Bad claim_family values:
- Year-based (`2023`, `2024`) — overlaps with bibkey year and doesn't carry semantic info
- Author-centric (`zou_lab`, `anthropic_team`) — entries get reclassified as authorship changes
- Free-text descriptions (`papers about prompt injection in RAG systems`) — too long, agents can't classify reliably

The taxonomy is declared once in `research_plan.md` and used throughout the rest of the pipeline. Changing it later means re-running `/research-gather` to re-classify entries.

## When to add `Known landmark papers`

Add this section when there are 2+ canonical references in the topic that you already know about. Listing them up front:

- Prevents `/research-gather` from claiming credit for trivially-known work via WebSearch
- Lets the gather skill cross-check that it found the canonical references (and warn if it didn't)
- Gives the dossier a baseline structure — you know A1 starts with the foundational paper

Don't list every paper you've ever read. List the 2–5 references that anyone working in this topic would consider mandatory.

## Time-budget calibration

Rough sizing for the rest of the pipeline:
- 5 papers, 1 sub-area → 1–2 hours dossier + index work
- 20 papers, 3 sub-areas → 1 day  
- 50 papers, 5 sub-areas → 2–3 days
- 100+ papers, 7+ sub-areas → 1+ week (and consider splitting into multiple plans)

If the plan implies >1 week of pipeline work, the topic is probably over-scoped. Cut.

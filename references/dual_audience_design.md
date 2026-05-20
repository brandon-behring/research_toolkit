# Dual-audience design principles

When writing reference docs (research syntheses, literature surveys, knowledge-base material, glossaries), design them so future LLM agents can extract context efficiently — not just for human readers.

The agent-index produced by `/agent-index` is the load-bearing example. The skill body MUST load this reference before generating output and apply every principle below.

## Why this matters

Brandon works across machines with agents heavily (multi-machine workflow, multiple project memory dirs, frequent project switches). Docs that an agent can land in cold are higher-leverage than prose-only docs that require human interpretation. Designing dual-audience adds modest cost up front; it pays off across many future agent sessions reading the material as ground-truth context.

## How to apply (the 9 principles)

1. **Front-load metadata at the top of each file** — scope, out-of-scope (with file pointer), coverage window, last-updated date, key terms covered, related files. Agents typically read the top first; the agent-index belongs there.

2. **Predictable layout across sibling files** — same section ordering everywhere, so once an agent reads one, it knows the structure of the rest. Topic files use the same `## A1.` / `## A2.` / etc. anchor pattern; intra-section content uses the same 5-bullet structure.

3. **Stable anchor-friendly headers** — preserve canonical section IDs (`A1` / `A2` / `B1` / …) so cross-references survive and deep-links work. The anchor IDs are part of the schema; renaming a section breaks every lookup-recipe pointer to it.

4. **Per-entry consistent field shape** — Source / Code / Mechanism / Result / Status as bullets, not free-form prose. Lets agents parse without bespoke logic. Vendor / standards profiles use a different but equally consistent bullet schema.

5. **Lookup recipes in the README** — "If you need X, read file Y § Z" routing for the most common questions. ~15–25 recipes per agent-index. Covers ~80% of likely questions; saves an agent from re-deriving where to look.

6. **Glossary at end of overview** — canonical term + aliases + one-line definition + primary citation. Resolves ambiguous lookups without forcing the agent to do a web search. Place in the README or in `00_overview.md`.

7. **Inline staleness/verification markers** — `(unverified)`, `(vendor blog)`, and `(recheck after YYYY-MM-DD)` flags appear *on the entry*, not in a footer. The agent reading entry-by-entry sees the staleness signal in context.

8. **Plain declarative prose** — no rhetorical questions, allusions, or framing that requires inference. Each sentence stands alone. "X does Y" beats "you might wonder whether X does Y."

9. **Explicit "out of scope" sections** — bound each file so an agent looking for the wrong thing knows quickly to look elsewhere. The Scope boundary callout in the README is the load-bearing example.

## Evidence-ID rendering (v2 strict-live)

For strict-live v2 projects, every claim-bearing bullet must be traceable to
an entry in `evidence_ledger.yml`. The agent-index displays evidence IDs in
one of two ways; both are valid, pick whichever reads better per block:

**Sixth-bullet form** (default, mirrors the canonical 5-bullet block):
```markdown
- **<Display name>** — <Authors> (<Year>).
  - **Source:** <URL>
  - **Code:** <URL or "—">
  - **Mechanism:** <one-liner>
  - **Result:** <key claim>
  - **Status:** Verified | (vendor blog) | ...
  - **Evidence:** ev_<topic>_0001
```

**Inline suffix form** (more compact, used when the entry has multiple
evidence-backed claims or the bullet list is already long):
```markdown
- **Result:** GPT-5 jailbreak success rate ≈17% [ev_jailbreak_rate]
```

Square brackets are required so an agent can grep `\[ev_[a-z0-9_]+\]` to
extract every evidence reference in the file. Multiple evidence IDs go in
one bracket: `[ev_jailbreak_rate, ev_jailbreak_corroboration]`.

ID format: `ev_<topic_slug>_NNNN` where NNNN is zero-padded for stable
ordering. Topic slug matches the project's top-level `topic:` field, so the
agent can distinguish synthesis-added cross-cutting evidence (`ev_<topic>_NNNN`)
from per-source primary evidence (also `ev_<topic>_NNNN` — same namespace;
the source_type field in evidence_ledger disambiguates).

The invariant: **every evidence ID rendered in markdown must exist in
`evidence_ledger.yml`**. `/agent-index` Phase 4b appends synthesis-specific
entries to keep this invariant intact when the agent-index introduces new
cross-cutting claims that weren't covered by `/research-gather`.

### v2.2 atomic claim IDs

For v2.2+ strict-live projects, the rendering convention extends to
**atomic claim IDs** — each bullet decomposes into 2–5 distinct
claim_ids, one per atomic fact in the bullet's prose. Naming pattern:

```
claim_<topic_slug>_b<bullet_number>_a<atom_number>_<descriptor>
```

Example (atomic_demo fixture, bullet B1, three atoms):
- `claim_atomic_demo_b1_a1_accuracy`
- `claim_atomic_demo_b1_a2_latency`
- `claim_atomic_demo_b1_a3_training`

Rendering convention: when a bullet's prose mixes multiple atoms,
inline-suffix form is preferred, with each substring tagged separately:

```markdown
- **Result:** The system achieves 91.2% accuracy [claim_..._a1_accuracy], inference latency averaged 42ms [claim_..._a2_latency], and training used 1.2B tokens [claim_..._a3_training].
```

Soft cap: 5 atoms per bullet. The validator emits a warning at >5 to
flag over-fragmentation. Free-text atoms in v2.2; SROM 4-tuple
(subject-relation-object-modifier) atomic structure deferred to v2.3.

## What NOT to put in agent-index

- **LLM-generated specifics**. Quantitative claims (ASR percentages, dataset sizes) MUST appear in primary source abstract or verified body excerpt. Inventing specific numbers is the most common failure mode for synthesis work; never assert a number you can't point to in the linked Source.

- **Content requiring re-derivation**. If a fact requires reading the cited paper's full body to verify, don't claim it in the synthesis — link to the paper and let the agent fetch the body if needed. Synthesis abstracts what's in the abstract, not what's deep in the methods.

- **Time-sensitive claims without date markers**. Vendor acquisitions, version numbers, and shipping status drift quarterly. Always include the date the claim was last verified and the next recheck date.

- **Author opinions disguised as fact**. "X is the best defense" is an opinion. "X reports the highest ASR reduction in [authors] 2024" is a fact citation. Synthesis is about the latter.

## Verification checklist (apply before declaring an agent-index complete)

- [ ] AGENT-INDEX HTML comment in the README
- [ ] Scope boundary callout (called out as a heading or marked block)
- [ ] ≥15 lookup recipes covering the most common question types
- [ ] Glossary present (in README or `00_overview.md`)
- [ ] Every synthesis entry has Source bullet with URL or bibkey
- [ ] Every quantitative claim is supported by primary source abstract OR marked `(unverified body claim)`
- [ ] Section anchors (`## A1.` etc.) are stable across the topic files
- [ ] No rhetorical questions, no "you might think" framings, no allusions to current events
- [ ] `(unverified)` / `(vendor blog)` flags inline on the affected entries, not in a footer

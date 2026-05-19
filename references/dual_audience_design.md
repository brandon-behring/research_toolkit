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

# <Topic> — Research Synthesis

<!-- AGENT-INDEX: this folder is a self-contained reference for <topic>. Read this README first. -->

**Purpose:** <one-sentence purpose>. Designed for dual consumption — humans (reading directly) and future LLM agents (grounding reasoning in this literature).
**Primary intended consumer:** <e.g., future Claude Code / LLM agents working in adjacent projects who need detailed context on <topic>>. Secondary consumers: humans reading the material directly.
**Self-containedness guarantee:** this folder has no hard dependence on sibling files outside itself. Move it elsewhere and it still works.
**Scope:** <date range, sub-areas covered>.
**Coverage:** <N> entries across <K> topic files; structured 5-bullet entries (Source / Code / Mechanism / Result / Status).
**Last updated:** <YYYY-MM-DD>.

## ⚠️ Scope boundary

<1–2 paragraphs explicitly stating what this folder is NOT — point readers to where the related material lives if they're in the wrong folder>

**Cross-vol overlap convention:** when an entry is methodologically relevant to multiple research vols (e.g., calibration of PEFT'd models touches both PEFT PEFT and calibration calibration), pick ONE primary location based on claim_family and reference adjacency in this scope-boundary callout. **Do NOT duplicate entries across vols** — the duplicate-detection rule lives here, not in the synthesis files.

## How this is organized

Sub-section anchors use a per-file letter prefix (`## A1.` in file 01, `## B1.` in file 02, etc.) — see the dossier's section-anchor convention for the full table. Lookup recipes in this README reference these anchors.

| File | Topic | When to read |
|---|---|---|
| `00_overview.md` | <if present: navigation + glossary + threat model> | Start here if new to <topic> |
| `01_<area>.md` | <topic 1> (anchors A1./A2./...) | <when this is the right entry point> |
| `02_<area>.md` | <topic 2> (anchors B1./B2./...) | <…> |

## Lookup recipes

Routes by question type. Each points to a specific file and section anchor.

- **"What's the foundational paper for <X>?"** → `01_<area>.md` § A1 (<Authors year>, *<title>*).
- **"What benchmark should I use for <X>?"** → `0K_<area>.md` § <section>.
- **"What's <ACRONYM>?"** → `00_overview.md` § Glossary.
- (~15–25 recipes total; covers ~80% of likely questions)

## Glossary

Canonical term + aliases + one-line definition. Lives here in the README, OR pointed to from `00_overview.md`. Resolves ambiguous lookups without forcing the reader to search.

- **<TERM>**: <one-line definition>. <Citation if non-obvious>.
- ...

## Verification & limits

- Citations resolved as of <YYYY-MM-DD>.
- <Note any post-cutoff vendor/blog claims that should be re-verified>.
- This synthesis is a snapshot. <Note volatility characteristics of the field>.
- <Add audit-trail notes here as `**Independent audit, round N (YYYY-MM-DD):** ...` paragraphs after each `/dossier-audit` invocation.>

## Attribution

Synthesized from a research dossier maintained by the research_toolkit (`~/Claude/research_toolkit/`). URLs link to primary sources (arXiv, GitHub, vendor blogs, conference proceedings). No local file paths are referenced.

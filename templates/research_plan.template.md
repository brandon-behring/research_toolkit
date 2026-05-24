# Research Plan: <topic>

A 1–2 sentence statement of what this research is for, what use case the output serves, and the rough size (paper count, time budget). Distinguish narrow scoping from exhaustive coverage; most plans should be narrow.

## Sub-areas

Required: 4–8 top-level bullets. Each sub-area has its own source-type list and any constraint notes.

- A1. <sub-area name>
  - Source types: arXiv, conference proceedings, vendor blog, dataset card, leaderboard, CTF, standards body, GitHub, ...
  - Notes: <free-text scoping notes specific to this sub-area>
- A2. <sub-area name>
  - Source types: ...
  - Notes: ...
- A3. <sub-area name>
  - Source types: ...
  - Notes: ...
- A4. <sub-area name>
  - Source types: ...
  - Notes: ...

## Out-of-scope

Required: 1+ bullet. List what's deliberately outside the research's purview. The validator fails on empty out-of-scope sections — empty out-of-scope means the topic isn't actually scoped.

When `/research-gather` encounters a source that's real but out-of-scope (or otherwise doesn't fit cleanly), it should emit an `escalate_to_manual` record in `gather_trace.yml` using one of the canonical reasons documented in `references/citation_rules.md` (§ Escalation reason cheatsheet) — survey of what we already have, borderline scope, vendor marketing, or login-gated/paywalled.

- <thing this research won't cover>
- <another thing>

## Claim family taxonomy

Required: 3+ bullets. The set of `claim_family` values that `bib_ledger.yml` entries can use. Keep it tight (3–8 categories typically); large taxonomies get unwieldy fast.

- <category 1>
- <category 2>
- <category 3>

## Known landmark papers

Optional. Pre-known canonical references the user expects to be in the dossier. `/research-gather` should not need to re-discover these via WebSearch. Specifying them up front prevents the gather skill from claiming credit for trivially-known work.

- <bibkey>: <one-line reason this is canonical>
- <bibkey>: <one-line reason>

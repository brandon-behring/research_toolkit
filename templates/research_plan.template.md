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

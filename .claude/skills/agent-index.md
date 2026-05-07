---
name: agent-index
description: Synthesize a dossier into a dual-audience indexed folder. Renders entries as 5-bullet blocks (Source/Code/Mechanism/Result/Status), writes an AGENT-INDEX README with scope-boundary callout, lookup recipes, and glossary. Designed for both human readers and future LLM agents grounding reasoning in the literature.
allowed-tools: Read, Write, Edit, Bash
---

# /agent-index — Synthesize dossier as agent-ready indexed folder

## Usage

```
/agent-index <dossier_dir> [--output-dir <dir>] [--topic <slug>]
```

**Examples:**
```
/agent-index ~/Claude/research_timeseries/dossier/ --output-dir ~/some_project/docs/timeseries_research/
/agent-index ~/Claude/research_jailbreak/dossier/ --topic jailbreak --output-dir ~/some_project/docs/jailbreak_research/
```

**Default output dir**: `<consumer-project>/docs/<topic>_research/` if invoked from a project root, else prompts the user.

## When to use

- After `/dossier-build` produces a content-stable dossier directory.
- Run **once** per dossier; re-run only after material dossier edits.
- This is the highest-leverage skill in the pipeline — its output is what future LLM agents read as ground-truth context for the topic.

**Upstream:** `/dossier-build` produces dossier table files.
**Downstream:** `/dossier-audit` verifies the synthesis. `/url-freshness-check` may be run on the output before publishing.

## Workflow

### Phase 1: load reference (HARD REQUIREMENT)

Read `~/Claude/research_toolkit/references/dual_audience_design.md` BEFORE generating any output. The 9 design principles are mandatory for the synthesis. The skill MUST satisfy the verification checklist at the end of that reference.

Read `~/Claude/research_toolkit/references/citation_rules.md` for URL canonical forms, status flags, and the "no LLM-generated specifics" rule (the most load-bearing content rule).

### Phase 2: read dossier + plan

Read every `*.md` file in `<dossier_dir>` (excluding `_dossier_readme.md`). Extract entries from each table.

Read the corresponding `research_plan.md` (typically `<dossier_dir>/../research_plan.md`) to:
- Get the topic-file naming convention
- Get the section-anchor scheme (`A1`, `A2`, `B1`, etc.)
- Cross-reference the claim_family taxonomy

### Phase 3: pick topic-file split

The agent-index typically has one synthesis file per dossier file, plus an `00_overview.md` (optional but common) and a `README.md`.

Naming convention: `00_overview.md`, `01_<topic>.md`, `02_<topic>.md`, ... — these become the file table in the README.

### Phase 4: render 5-bullet entries

Read `~/Claude/research_toolkit/templates/5_bullet_entry.template.md` for the canonical schema.

For each dossier entry, render as a 5-bullet block:

```markdown
- **<Display name>** — <Authors short> (<Venue / Year>).
  - **Source:** <primary URL>
  - **Code:** <code repo URL or "—" for none>
  - **Mechanism:** <factual one-liner: what does the paper actually do?>
  - **Result:** <distinct contribution / key claim>
  - **Status:** Verified | Unverified | (vendor blog) | ...
```

Order matters — Source / Code / Mechanism / Result / Status. Code may be omitted (e.g., for leaderboard or vendor-page entries with no separate code repo). For vendor / standards / lab profiles, use a content-appropriate variant (Source / Status / Product line / Mechanism / Integration). See `templates/5_bullet_entry.template.md` § "Variant".

**Critical rule**: any quantitative claim in Mechanism or Result MUST be from the primary source's abstract. If only in the body, mark with `(unverified body claim)`. **Never invent specific numbers** — that's the most common hallucination mode for synthesis work.

#### Cell-rendering rules carried up from /dossier-build (HARD RULES — reproduced 2x as 404s in vol27/vol28 dogfood)

- **Display title**: copy the dossier's title verbatim. **Do not abbreviate to a practitioner nickname.** Example failure (vol28 Stage 5 fix): "Verbalized Confidence" → must be "Teaching Models to Express Their Uncertainty in Words". "LMs (Mostly) Know What They Know" → "Language Models (Mostly) Know What They Know". If the paper's actual arXiv title is awkwardly long, render it verbatim anyway and let the section header / lookup-recipe carry the practitioner nickname.
- **Code field**: prefer the dossier's `<GitHub>` cell. When it's `—`, write `—` here too. **Do NOT guess `<firstauthor>/<paper-slug>` GitHub URLs.** vol27 found 7/117 such guesses 404'd; vol28 found 3/137 more. Real repos live at lab orgs (`pilancilab/spectral_adapter`), unrelated handles (`EricLBuehler/xlora`, `tripplyons/oft`), or simply don't exist. The url-freshness-check stage will surface real repos via inline correction; your job is not to invent them. If you find yourself typing `github.com/<paper-firstauthor>/<paper-name>`, STOP and use `—`.
- **Status field**: when Code is `—` because no repo exists, append `(no widely-known repo)` to Status (e.g., `(no widely-known repo) Verified.`). When Venue defaulted to "arXiv preprint" because the dossier didn't have a verified venue, append `(uncertain venue)`. These flags localize audit work.

### Phase 5: write the README

Read `~/Claude/research_toolkit/templates/agent_index_README.template.md` for the canonical structure.

Required README sections:
- AGENT-INDEX HTML comment (`<!-- AGENT-INDEX: ... -->`)
- Front-loaded metadata (Purpose, Scope, Coverage, Last updated)
- Scope boundary callout (`## ⚠️ Scope boundary` or `## Scope boundary`)
- File table (`## How this is organized`)
- Lookup recipes (~15–25 routing entries)
- Glossary (or pointer to `00_overview.md`)
- Verification & limits (audit-trail placeholder)
- Attribution

### Phase 6: cross-reference + glossary

Build the glossary from technical terms used in the dossier. Each entry: term + 1-2 alias variants + one-line definition + primary citation.

Build the lookup recipes from typical questions a reader might ask. Cover ~80% of likely questions; omit obscure edge cases. Each recipe: `**"What's X?"** → `<file>` § <anchor> (<reference>)`.

### Phase 7: verify

Apply the verification checklist from `references/dual_audience_design.md` § "Verification checklist". Then run the validator.

## Templates

- `Read ~/Claude/research_toolkit/templates/agent_index_README.template.md` — README structure.
- `Read ~/Claude/research_toolkit/templates/5_bullet_entry.template.md` — entry schema.

## References

- `Read ~/Claude/research_toolkit/references/dual_audience_design.md` — HARD REQUIREMENT — load before generating.
- `Read ~/Claude/research_toolkit/references/citation_rules.md` — URL forms, status flags, no-LLM-generated-specifics rule.

## Validation

```bash
python ~/Claude/research_toolkit/validators/agent_index.py <output_dir>
```

Validator checks: AGENT-INDEX comment in README; scope-boundary callout; lookup recipes section; glossary present; every entry has Source bullet with URL/bibkey; canonical 5-bullet ordering on paper-synthesis entries (those with Result bullet); footer entry counts match grep counts.

## Output / handoff

**Produces:**
- `<output_dir>/README.md` — agent-index hub with lookup recipes, glossary, scope boundary
- `<output_dir>/00_overview.md` (optional) — extended overview / threat model / glossary
- `<output_dir>/01_<topic>.md` … `<output_dir>/0K_<topic>.md` — synthesis files with 5-bullet entries

**Consumed by:**
- `/dossier-audit <output_dir> --focus <area>` — independent verification round
- `/url-freshness-check <output_dir>` — URL liveness check
- Future LLM agents grounding reasoning in this literature
- Human readers as a reference document

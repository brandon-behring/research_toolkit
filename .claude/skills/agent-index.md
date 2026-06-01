---
name: agent-index
description: Synthesize a dossier into a dual-audience indexed folder. For v2.2+ strict-live projects, runs Attribute-First atomic decomposition (Phase 2a-2c span-select → plan → generate), emitting `pre_selection_manifest.yml` and atomic claim_ids before any bullet prose is written — making post-hoc rationalization structurally impossible. Renders entries as 5-bullet blocks (Source/Code/Mechanism/Result/Status), writes an AGENT-INDEX README with scope-boundary callout, lookup recipes, and glossary. For v1-era projects without `evidence_ledger.yml`, falls back to legacy rendering.
allowed-tools: Read, Write, Edit, Bash
---

# /agent-index — Synthesize dossier as agent-ready indexed folder

## Usage

```
/agent-index <input_dir> [--output-dir <dir>] [--topic <slug>]
```

`<input_dir>` is either a project root (v2.2+ strict-live; reads from `bib_ledger.yml` + `cache_manifest.yml`) or a legacy `dossier/` directory (v1-era / v2.0 / v2.1; reads `*.md` table files).

**Examples:**
```
# v2.2+ strict-live: point at the project root
/agent-index ~/Claude/research_eval_drift/ --output-dir ~/Claude/research_eval_drift/agent_index/

# v1-era / v2.0 / v2.1: point at the dossier dir
/agent-index ~/Claude/research_timeseries/dossier/ --output-dir ~/some_project/docs/timeseries_research/
/agent-index ~/Claude/research_jailbreak/dossier/ --topic jailbreak --output-dir ~/some_project/docs/jailbreak_research/
```

**Default output dir**: `<project_dir>/agent_index/` for v2.2+ strict-live; `<consumer-project>/docs/<topic>_research/` for legacy flow when invoked from a project root; else prompts the user.

## When to use

- After upstream inputs are content-stable:
  - **v2.2+ strict-live**: `/research-gather` has produced `bib_ledger.yml` + `cache_manifest.yml` + `evidence_ledger.yml` + `claim_graph.jsonl`, and span-selection can read directly from cached source files. `/dossier-build` is **not required** (skipped in the 4 v2.2-dogfood dossiers).
  - **v1-era / v2.0 / v2.1**: `/dossier-build` has produced a content-stable `dossier/` directory of MD table files.
- Run **once** per topic; re-run only after material upstream edits.
- This is the highest-leverage skill in the pipeline — its output is what future LLM agents read as ground-truth context for the topic.

**Upstream:**
- v2.2+ strict-live: `/research-gather` produces `bib_ledger.yml` + `cache_manifest.yml` (Attribute-First reads spans directly from cached source files via `cache_manifest.yml.text_path`).
- v1-era / v2.0 / v2.1: `/dossier-build` produces `dossier/*.md` table files.

**Downstream:** `/dossier-audit` verifies the synthesis. `/url-freshness-check` may be run on the output before publishing.

## Workflow

### Phase 1: load reference (HARD REQUIREMENT)

Read `~/Claude/research_toolkit/references/dual_audience_design.md` BEFORE generating any output. The 9 design principles are mandatory for the synthesis. The skill MUST satisfy the verification checklist at the end of that reference.

Read `~/Claude/research_toolkit/references/citation_rules.md` for URL canonical forms, status flags, and the "no LLM-generated specifics" rule (the most load-bearing content rule).

For strict-live v2 projects, read
`~/Claude/research_toolkit/references/strict_live_v2.md` and preserve compact
evidence IDs on each substantive table row / 5-bullet block. Markdown should
stay readable, but every claim-bearing bullet must be traceable to
`evidence_ledger.yml`.

### Phase 2: read entries + plan

**For v2.2+ strict-live projects** (no `dossier/` directory required):

Read `<project_dir>/bib_ledger.yml` directly. Each entry there is a candidate for 5-bullet rendering. The cached source text needed for Phase 2a span-selection lives at the paths declared in `<project_dir>/cache_manifest.yml` → `entries[].text_path` (relative to the manifest's `cache_root`).

**For v1-era / v2.0 / v2.1 projects** (legacy flow):

Read every `*.md` file in `<dossier_dir>` (excluding `_dossier_readme.md`). Extract entries from each table.

Read the corresponding `research_plan.md` (typically `<dossier_dir>/../research_plan.md` in legacy mode, or `<project_dir>/research_plan.md` in v2.2+) to:
- Get the topic-file naming convention
- Get the section-anchor scheme (`A1`, `A2`, `B1`, etc.)
- Cross-reference the claim_family taxonomy

#### v2.2 Attribute-First sub-phases (strict-live projects only)

For strict-live v2.2+ projects, Phase 2 splits into 2a → 2b → 2c BEFORE
any bullet text is generated. This commits to evidence spans before
writing prose, making post-hoc rationalization structurally impossible.

**Phase 2a — span-select.** For each entry in the dossier, open its
cached source(s) (`cache_manifest.yml` → `text_path`) and pick the
spans that will become evidence for the entry's atomic claims. A
single entry usually decomposes into 2–5 atomic claims (FActScore /
AtomEval lesson — bullet-level claims hide mixed support). Each atomic
claim binds to one span; record byte offsets + sha256 + excerpt.
**Do not hand-compute the offsets/hash** — run
`scripts/build_excerpt_anchor.py <cache_manifest.yml> --cache-id <id> --excerpt "<verbatim text>"`
(add `--occurrence N` when the excerpt repeats, e.g. an abstract duplicated in an HTML
page's `<meta>` + body). It resolves the cached text via the manifest's `cache_root`,
emits `text_path_offset` + `sha256_of_span`, and self-verifies them through
`verify_excerpt_anchor` before printing — so a successful run is guaranteed to pass
`/citation-audit`.

**Phase 2b — plan.** Emit `<output_dir>/pre_selection_manifest.yml`
with one `selections[]` entry per (bullet, atom) pair. Schema is in
`templates/pre_selection_manifest.template.yml`. The manifest is the
structural contract: only these spans may appear as evidence for the
declared atom_ids.

Use atom_id naming `claim_<topic>_b<bullet>_a<atom>_<descriptor>`
(e.g., `claim_atomic_demo_b1_a1_accuracy`). Each atomic claim_id is
distinct from the others within a bullet; downstream `build_claim_graph`
emits one claim record per atom, not per bullet.

**v2.3 C2 — synthesis_entry attribution wire-up (when synthesis_entry.yml
exists in the project).** If `<output_dir>/synthesis_entry.yml` is
present (multi-source consolidation entries per daf6699), AND the
atom_id matches `claim_synthesis_*` (i.e., this selection represents a
synthesis atom whose source_urls span ≥3 sources), AND the synthesis_entry's
`source_urls` set matches the atom's supporting evidence source_urls,
emit `synthesis_entry_ref: syn_<topic>_<slug>` on the selection. Then
`build_claim_graph.py` will:
1. Resolve the claim text from `synthesis_entry.attribution_map`
   (longest-substring-match against the fallback excerpt) or
   `synthesis_entry.title`.
2. Persist `synthesis_entry_id` on the claim record so the dashboard
   can link to the consolidation entry.
3. Emit a WARN to stderr if the source_urls drift between the synthesis_entry
   and the supporting evidence (a curation signal — fix the entry, not
   the link).

When in doubt or when no synthesis_entry exists, omit the field — the
builder falls back cleanly to the v2.2 longest-excerpt tiebreak.

**Phase 2c — generate.** Now write the bullet prose, conditioned ONLY
on the spans in pre_selection_manifest. The bullet's evidence_ids in
evidence_ledger.yml must be a subset of the atom_ids declared in 2b.
Validator (Phase 7) rejects any evidence_id whose anchor isn't in the
pre_selection_manifest — this catches post-hoc citation insertion.

Cap atoms at ~5 per bullet. The validator emits a warning (not error)
at >5 to flag over-fragmentation. Free-text atoms in v2.2; SROM
4-tuple structure (subject-relation-object-modifier) is a deferred
v2.3 enhancement.

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
  - **Evidence:** ev_<topic>_0001
```

Order matters — Source / Code / Mechanism / Result / Status. Code may be omitted (e.g., for leaderboard or vendor-page entries with no separate code repo). For vendor / standards / lab profiles, use a content-appropriate variant (Source / Status / Product line / Mechanism / Integration). See `templates/5_bullet_entry.template.md` § "Variant".

**Critical rule**: any quantitative claim in Mechanism or Result MUST be from the primary source's abstract. If only in the body, mark with `(unverified body claim)`. **Never invent specific numbers** — that's the most common hallucination mode for synthesis work.

For v2 strict-live outputs, `Evidence` may be a compact inline suffix instead
of a sixth bullet when that is more readable (for example, `... [ev_x_0001]`).
The invariant is that every substantive row/block has at least one evidence ID
that exists in `evidence_ledger.yml` (enforced by Phase 4b below).

#### Cell-rendering rules carried up from /dossier-build (HARD RULES — reproduced 2x as 404s in PEFT/calibration dogfood)

- **Display title**: copy the dossier's title verbatim. **Do not abbreviate to a practitioner nickname.** Example failure (calibration Stage 5 fix): "Verbalized Confidence" → must be "Teaching Models to Express Their Uncertainty in Words". "LMs (Mostly) Know What They Know" → "Language Models (Mostly) Know What They Know". If the paper's actual arXiv title is awkwardly long, render it verbatim anyway and let the section header / lookup-recipe carry the practitioner nickname.
- **Code field**: prefer the dossier's `<GitHub>` cell. When it's `—`, write `—` here too. **Do NOT guess `<firstauthor>/<paper-slug>` GitHub URLs.** PEFT found 7/117 such guesses 404'd; calibration found 3/137 more. Real repos live at lab orgs (`pilancilab/spectral_adapter`), unrelated handles (`EricLBuehler/xlora`, `tripplyons/oft`), or simply don't exist. The url-freshness-check stage will surface real repos via inline correction; your job is not to invent them. If you find yourself typing `github.com/<paper-firstauthor>/<paper-name>`, STOP and use `—`.
- **Status field**: when Code is `—` because no repo exists, append `(no widely-known repo)` to Status (e.g., `(no widely-known repo) Verified.`). When Venue defaulted to "arXiv preprint" because the dossier didn't have a verified venue, append `(uncertain venue)`. These flags localize audit work.

### Phase 4b: append synthesis evidence (v2 strict-live only)

For v2 projects, `/research-gather` writes one evidence entry per primary source.
Synthesis often introduces **cross-cutting claims** that span multiple sources
(e.g., "X family of attacks is consistently mitigated by Y defense across [refs]")
— these need their own evidence entries.

Locate the project's `evidence_ledger.yml`. Convention: parent directory of the
indexed folder (`<output_dir>/../evidence_ledger.yml`). If the indexed folder
is the project root, use `<output_dir>/evidence_ledger.yml`. Skip this phase if
no `evidence_ledger.yml` exists (the project is v1, not v2).

For each evidence ID referenced in your rendered 5-bullet blocks
(`Evidence: ev_<topic>_NNNN` bullets and inline `[ev_x_NNNN]` suffixes):

1. Check whether the ID already exists in `evidence_ledger.yml`.
2. If yes, leave it (research-gather already populated it).
3. If no, append a new entry:
   - `evidence_id`: the ID you cited in the markdown
   - `source_type`: `synthesis` (a synthesis-specific quality distinct from primary/secondary)
   - `source_quality`: `secondary` (cross-cutting claims aren't primary observation)
   - `verification_method`: `manual` (you're aggregating from multiple primary entries already verified in evidence_ledger; `manual` is the validator-allowed value for an aggregated/cross-referenced entry — allowed enum: `api`, `inaccessible`, `manual`, `pdf`, `webfetch`, `websearch_snippet`)
   - `supports`: list the claim IDs and the field paths in your synthesis files
   - `cache_ids`: list the cache_ids of the primary sources you cross-referenced
   - `confidence`: optional; if you include it, factors should list the primary sources cross-referenced

Do NOT duplicate primary-source evidence entries here. This phase is strictly
for synthesis-level claims that arise from your aggregation work. If you find
yourself wanting to add an evidence entry for "what paper X says," that belongs
in `/research-gather`'s output, not here — note it as a v2.1 backlog item rather
than retrofitting.

After appending, re-validate:

```bash
python ~/Claude/research_toolkit/validators/evidence_ledger.py <evidence_ledger_path>
```

### Phase 4c: consolidate synthesis_entry.yml (v2.4+ strict-live only)

**Skip this entire phase** if `claim_graph.jsonl` contains no
`claim_synthesis_*` atoms with `corroboration_count >= 3` (the
synthesis_entry validator's bar). The vast majority of small dossiers
won't qualify — most synthesis is implicit in 5-bullet prose, not
materialized as cross-cutting claims with ≥3 distinct primary sources.

When the project DOES have qualifying synthesis atoms, this phase
consolidates them into `synthesis_entry.yml` so downstream tooling
(dashboard, build_claim_graph attribution resolution) can render
author-written synthesis text instead of falling back to the
contributing-source excerpt tiebreak.

**Step 1 — mechanical scaffold.** Run:

```bash
python ~/Claude/research_toolkit/scripts/scaffold_synthesis_entry.py \
  <project_dir> --merge
```

This drafts skeleton `synthesis_entry.yml` entries for every qualifying
atom: `synthesis_id`, `source_urls` (union of supporters), `title`
(copied from claim text), `claim_family` (dominant from supporters'
bib_ledger entries), `tier_summary` (computed via
`scripts/source_tiers.assign_tier`), `volatility` (mapped from most-
volatile freshness_tier), and `status: unverified`. `--merge` preserves
any hand-authored entries already in the file.

The scaffold deliberately leaves `attribution_map` absent — that field
is the LLM-judgment payload.

**Step 2 — write `attribution_map` (the LLM-judgment step).** For each
new entry, open `synthesis_entry.yml` and add `attribution_map: {key:
[source_urls]}` where:
- **Keys** are short phrasings of the claim that should match what
  `build_claim_graph.py` (v2.3 C2 resolver) sees in the claim_graph
  claim text. The resolver does longest-substring-match against claim
  text, so keys that overlap with the claim text bind cleanly.
- **Values** are the subset of `source_urls` that specifically support
  THAT phrasing (not the full union; not every source supports every
  sub-claim).

Worked example:

```yaml
- synthesis_id: syn_emergence_debate
  # ...other fields populated by the scaffold...
  attribution_map:
    "Emergence is partly an artifact of measurement choices":
    - https://arxiv.org/abs/2304.15004
    - https://arxiv.org/abs/2505.01234
    "Inverse-scaling phenomena disappear under metric reformulation":
    - https://arxiv.org/abs/2304.15004
```

**Step 3 — wire into `pre_selection_manifest.yml`.** For each new
`synthesis_id`, find the matching `claim_synthesis_*` selection in
`<project_dir>/pre_selection_manifest.yml` and add the optional
`synthesis_entry_ref: <synthesis_id>` field. The v2.3 Commit 3 resolver
will then resolve claim text via this attribution chain instead of the
fallback excerpt tiebreak.

**Step 4 — verify.** Re-run `build_claim_graph.py` and `validators/synthesis_entry.py`:

```bash
python ~/Claude/research_toolkit/scripts/build_claim_graph.py <project_dir>
python ~/Claude/research_toolkit/validators/synthesis_entry.py \
  <project_dir>/synthesis_entry.yml
```

Watch for stderr `WARN: ... source_urls mismatch ...` messages from
`build_claim_graph.py` — these indicate `attribution_map` source_urls
drifted from the supporting evidence's source_urls. Fix at this stage
(usually a typo in `attribution_map`), not later.

After verifying, flip the `status` field to `verified` on each new
entry.

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

For v2.2+ strict-live projects, also verify that every evidence_id cited
in the rendered bullets has a matching atom_id selection in
`pre_selection_manifest.yml`. Pre-selection commits drift the evidence
contract: any bullet citing a span NOT in the manifest is a structural
post-hoc rationalization and must be rewritten.

```bash
python ~/Claude/research_toolkit/validators/pre_selection_manifest.py <output_dir>/pre_selection_manifest.yml
```

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

After the per-stage validator passes, also run the v1.2 cross-stage validator from the project root (one level above `<output_dir>` if the output is `<project_dir>/agent_index/`, or however your project is laid out):

```bash
python ~/Claude/research_toolkit/validators/cross_stage.py <project_dir>
```

This catches **claim_family taxonomy drift** (a bib_ledger entry uses a `claim_family` not in `research_plan.md`'s taxonomy — the per-stage validators miss this) and **orphan arXiv IDs** (a `**Source:**` line points at an arXiv ID that has no matching ledger entry — common when the synthesis cross-references foundational papers without adding them to the bibliography). Default mode emits warnings; pass `--strict` to fail on orphan/stale findings.

## Output / handoff

**Produces:**
- `<output_dir>/README.md` — agent-index hub with lookup recipes, glossary, scope boundary
- `<output_dir>/00_overview.md` (optional) — extended overview / threat model / glossary
- `<output_dir>/01_<topic>.md` … `<output_dir>/0K_<topic>.md` — synthesis files with 5-bullet entries
- (v2 strict-live only) appended entries in `<output_dir>/../evidence_ledger.yml` for synthesis-specific cross-cutting claims (Phase 4b)
- (v2.2+ strict-live only) `<output_dir>/pre_selection_manifest.yml` — span selections committed in Phase 2b BEFORE any bullet is generated (Attribute-First contract); every bullet's evidence_ids must trace to an atom_id selection here

**Consumed by:**
- `/dossier-audit <output_dir> --focus <area>` — independent verification round
- `/url-freshness-check <output_dir>` — URL liveness check
- Future LLM agents grounding reasoning in this literature
- Human readers as a reference document

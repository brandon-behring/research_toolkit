---
name: research-plan
description: Scope a research topic before any web searching — decompose into 4-8 sub-areas, declare in/out-of-scope, draft a claim_family taxonomy, and list known landmark papers. Output is a research_plan.md consumed by /research-gather.
allowed-tools: Read, Write, Bash
---

# /research-plan — Scope a research topic

## Usage

```
/research-plan "<topic>" [--output <path>]
```

**Examples:**
```
/research-plan "Time-series anomaly detection benchmarks"
/research-plan "Adaptive jailbreak attacks 2024-2025" --output ~/Claude/research_jailbreak/research_plan.md
```

**Default output**: `~/Claude/research_<slug>/research_plan.md` where `<slug>` is the topic snake_cased.

## When to use

- Starting a new research effort on a topic with no existing dossier.
- Run **once** per topic. The plan is referenced throughout the rest of the pipeline (`/research-gather`, `/dossier-build`, `/agent-index`).
- Skip this skill only when retrofitting a pre-existing dossier (e.g., the prompt_injection_snapshot has no plan because it predates this stage).

**Upstream:** none — this is the first stage.
**Downstream:** `/research-gather` reads the plan to decide what sources to find.

## Workflow

### Phase 1: load reference

Read `~/Claude/research_toolkit/references/scope_planning.md` to apply scoping discipline before any decomposition.

### Phase 2: decompose into sub-areas

Propose 4–8 sub-areas (`A1`, `A2`, …). For each:
- One-line name
- Source types you'd expect to find primary sources in (arXiv, conference proceedings, vendor blog, dataset card, leaderboard, CTF, standards body, GitHub library)
- A free-text scoping note (what's IN the sub-area; what's OUT)

If decomposition yields >8 sub-areas, ask whether to split into multiple plans (per `references/scope_planning.md`).

### Phase 3: declare out-of-scope

The `## Out-of-scope` section is a hard validator requirement. Aggressively cut adjacent sub-areas:
- Adjacent sub-domains that deserve their own plan
- Methodologically distinct work that overlaps the topic name but has different evaluation conventions
- Time-budget-incompatible scope (a sub-area that would itself take >1 week)

### Phase 4: draft claim_family taxonomy

Aim for 3–8 categories. Use the topical / methodological / phase-of-pipeline patterns in `references/scope_planning.md` § "Sizing the claim_family taxonomy". Avoid year-based, author-centric, or free-text taxonomies.

### Phase 5: list known landmark papers (optional)

Add a `## Known landmark papers` section with bibkeys + one-liners for any pre-known canonical references. This prevents `/research-gather` from claiming credit for trivially-known work.

Bibkey convention: `{firstauthor_lowercase}{year}{slug}`. See `references/citation_rules.md`.

### Phase 6: write the plan

Read `~/Claude/research_toolkit/templates/research_plan.template.md` for the canonical structure. Write the plan at the user-chosen `--output` path (or default).

## Templates

- `Read ~/Claude/research_toolkit/templates/research_plan.template.md` — canonical research plan structure.

## References

- `Read ~/Claude/research_toolkit/references/scope_planning.md` — scoping discipline.
- `Read ~/Claude/research_toolkit/references/citation_rules.md` — bibkey convention.

## Validation

Run as the final step. The skill MUST report failure with stderr if the validator exits non-zero — do not surface the artifact as complete.

```bash
python ~/Claude/research_toolkit/validators/research_plan.py <output_path>
```

The validator checks: H1 starts with `Research Plan:`; `## Sub-areas` has 4–8 top-level bullets; `## Out-of-scope` is non-empty; `## Claim family taxonomy` has ≥3 entries.

## Output / handoff

**Produces:** `research_plan.md` at the `--output` path (or default `~/Claude/research_<slug>/research_plan.md`).

**Consumed by:** `/research-gather <plan_path>` — reads the plan and discovers primary sources for each sub-area.

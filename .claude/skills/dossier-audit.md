---
name: dossier-audit
description: Run one round of complementary-scope independent audit on an indexed folder. Spawns a fresh general-purpose sub-agent with WebSearch + WebFetch to verify entries against primary sources; receives a DROP/CORRECT/FLAG/SPOT-CHECK report; applies fixes inline; appends round-N audit-trail note. Single-round — user re-invokes per round. v1.6: also runs against /dataset-index outputs — use focus areas like "license risks + access stability" for dataset dossiers.
allowed-tools: Read, Edit, Write, Bash, WebSearch, WebFetch
---

# /dossier-audit — One round of independent audit

## Usage

```
/dossier-audit <indexed_folder> --focus "<focus area>" [--aggressiveness standard|aggressive]
```

**Examples:**
```
/dossier-audit ~/some_project/docs/jailbreak_research/ --focus "anonymous 2025 arXiv entries"
/dossier-audit ~/some_project/docs/timeseries_research/ --focus "tool version numbers" --aggressiveness aggressive
```

**Default aggressiveness**: `standard` (generalize unverifiable claims, keep entries). Use `aggressive` to drop entire entries when any single claim can't be verified.

## When to use

- After `/agent-index` produces a synthesis.
- Run **once per round**; user controls iteration. The skill does NOT auto-iterate.
- Each round picks a different focus area (complementary scope) — see `references/audit_protocol.md` § "Complementary-scope rule".
- Stop iterating when a round returns "Clean — stop here."

**Upstream:** `/agent-index` produces the indexed folder.
**Downstream:** another `/dossier-audit` round with a different focus, OR stop.

## Workflow

### Phase 1: load reference

Read `~/Claude/research_toolkit/references/audit_protocol.md` — covers the complementary-scope rule, the DROP/CORRECT/FLAG report shape, regression checks, audit-trail format, and the stopping rule.

For strict-live v2 projects, also read
`~/Claude/research_toolkit/references/strict_live_v2.md`. Audit findings must
update `evidence_ledger.yml`, `cache_manifest.yml`, and `claim_graph.jsonl`
alongside Markdown edits; otherwise `/freshness-audit --strict` will fail.

### Phase 2: detect prior rounds

Read `<indexed_folder>/README.md`. Search for `**Independent audit, round N (date):**` notes. Extract:
- Round numbers already run
- Focus areas already covered
- Cumulative findings counts

If the user-specified `--focus` overlaps with a prior round's coverage, surface a warning and ask whether to proceed (overlap is OK if the user wants a re-check, but should be deliberate).

### Phase 3: spawn the audit agent

Use the `Agent` tool with `subagent_type=general-purpose`. The prompt includes:

1. **Scope description**: the indexed folder path + focus area + aggressiveness posture
2. **Prior rounds report**: a list of focus areas covered by previous rounds (so the agent knows what NOT to re-check)
3. **DROP/CORRECT/FLAG protocol**: instructions on how to format findings (per `audit_protocol.md`)
4. **Tools available**: WebSearch + WebFetch for verification against primary sources
5. **Per-finding format**: file + section anchor + entry display name + reason + Source URL

The agent should produce a structured report. Read it carefully before applying.

### Phase 4: review the report

Surface the report to the user. For each finding category:
- **DROP findings**: list each entry to be removed; user can override (keep with FLAG instead) per finding
- **CORRECT findings**: list field changes; user can spot-check the proposed correction
- **FLAG findings**: list specifics that will be generalized in place
- **SPOT-CHECK PASSED**: report verification coverage

### Phase 5: apply fixes inline

Apply each finding using Edit tool with exact-match replacement:
- DROP: remove the entry block; decrement footer entry count
- CORRECT: edit the specific field
- FLAG: append `(unverified, YYYY-MM-DD)` annotation OR generalize the specific number/claim
- SPOT-CHECK PASSED: no change

If any DROP would empty out a sub-section, surface that as a structural change requiring user decision.

#### v2 strict-live propagation (when the project is v2)

For v2 projects, audit findings must also propagate to `evidence_ledger.yml`,
`cache_manifest.yml`, and `claim_graph.jsonl` at the project root (parent
directory of `<indexed_folder>`). Otherwise `/freshness-audit --strict` will
fail because the v2 artifacts will desync from the markdown.

For each finding, apply the corresponding v2 edits:

- **DROP** (removed entry for bibkey `<bk>`):
  - In `evidence_ledger.yml`: remove every evidence entry whose `supports` field
    references claim IDs tied to `<bk>` (search the `supports.<entry>.claim_id`
    for the dropped bibkey).
  - In `claim_graph.jsonl`: remove every record whose `id` references `<bk>`
    (`ent_<bk>*`, `src_<bk>*`, `claim_<bk>*`, etc.). Also remove orphaned
    `evidence` and `cache_blob` records that no surviving claim references.
  - In `cache_manifest.yml`: leave entries alone unless no surviving evidence
    entry references the `cache_id` — only then remove. Cache blobs are cheap
    to keep and may be reused.

- **CORRECT** (changed a field on `<bk>`):
  - If the change touches an evidence-backed field (title, year, authors,
    headline result): update the corresponding `claim` record's `text` in
    `claim_graph.jsonl`. Update `evidence_ledger.yml` entry's `verification_method`
    to reflect re-verification (e.g., `webfetch_2026_05_19`); update the
    entry's `confidence.factors` to note the correction.
  - If the change is cosmetic (formatting, anchor name): no v2 propagation needed.

- **FLAG** (annotated `(unverified, YYYY-MM-DD)` or generalized a number):
  - In `evidence_ledger.yml`: lower the `confidence.score` on the relevant
    evidence entry and add a factor noting the audit annotation
    (e.g., `audit_round_<N>_flagged`).
  - In `claim_graph.jsonl`: optionally set the matching `claim` record's
    `status` to `conflicted` if the FLAG indicates the claim contradicts
    verified evidence.

Apply all v2 edits before running Phase 7 regression checks. If you cannot
determine the project root (e.g., `<indexed_folder>` is detached or v2
artifacts are missing), report this and ask the user — do NOT silently skip.

### Phase 6: write audit-trail note

Append to `<indexed_folder>/README.md` under the existing `## Verification & limits` section (NOT a new top-level section). Format:

```markdown
**Independent audit, round <N> (<YYYY-MM-DD>):** A <complementary-scope|aggressive>
review pass focused on <focus area>. Prior rounds covered <prior focuses>. Findings:
<DROP count> dropped, <CORRECT count> corrected, <FLAG count> flagged. <Brief
summary>. Recommendation: <re-run with focus / clean — stop here>.
```

### Phase 7: regression checks

Before reporting success:
- `grep -c "^  - \*\*Source:\*\*"` per file → record entry counts (decremented by DROPs)
- `wc -l` on each file → confirm shrinkage matches DROP count
- `grep` for known-corrected old strings → returns empty (CORRECT findings actually applied)
- `python ~/Claude/research_toolkit/validators/agent_index.py <indexed_folder>` → still passes after edits

For v2 strict-live projects, additionally run from the project root
(`<indexed_folder>/..`):

```bash
python ~/Claude/research_toolkit/validators/freshness.py --strict <project_dir>
python ~/Claude/research_toolkit/validators/evidence_ledger.py <project_dir>/evidence_ledger.yml
python ~/Claude/research_toolkit/validators/claim_graph.py <project_dir>/claim_graph.jsonl
```

These catch desync between the markdown edits and the v2 ledger/graph
propagation from Phase 5. A common failure: DROP removed a bibkey from markdown
but the matching `evidence` record in `claim_graph.jsonl` still references the
deleted claim — claim_graph validation flags the orphan.

If any regression check fails, do NOT report success. Surface the issue; the user fixes it and re-runs.

### Phase 8: recommend next step

If the round produced 0 new DROP / CORRECT / FLAG findings → recommend "Clean — stop here."

Otherwise → suggest a next focus area (one not yet covered) for the next round.

## Templates

(none — this skill writes inline edits, not new artifacts.)

## References

- `Read ~/Claude/research_toolkit/references/audit_protocol.md` — full protocol.
- `Read ~/Claude/research_toolkit/references/citation_rules.md` — for status flags applied during FLAG findings.

## Validation

```bash
python ~/Claude/research_toolkit/validators/audit_trail.py <indexed_folder>/README.md
```

Validator checks: round numbers are positive integers; no duplicate round numbers; dates are in YYYY-MM-DD format.

After the audit-trail note is added, the agent_index validator must still pass:

```bash
python ~/Claude/research_toolkit/validators/agent_index.py <indexed_folder>
```

This is the regression check from Phase 7 — schema must remain valid after edits.

## Output / handoff

**Produces:**
- Inline edits to `<indexed_folder>/0K_<topic>.md` files (DROP / CORRECT / FLAG fixes applied)
- Round-N audit-trail note appended to `<indexed_folder>/README.md`
- (v2 strict-live only) propagated edits to `<project_dir>/evidence_ledger.yml`, `<project_dir>/claim_graph.jsonl`, and (rarely) `<project_dir>/cache_manifest.yml` so the v2 trust state stays consistent with the markdown

**Consumed by:**
- Another `/dossier-audit` round with a different `--focus` (if the round produced findings)
- Or no further consumer (if the round was clean and the user stops iteration)

## Stopping rule

The user controls iteration. Each round is independent. Stop when a round returns "Clean — stop here" — that is the design's stopping signal. The skill does NOT auto-iterate.

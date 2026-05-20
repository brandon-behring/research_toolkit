# Audit protocol

Detailed protocol for `/dossier-audit`. One round = one complementary-scope verification pass with a structured DROP / CORRECT / FLAG / SPOT-CHECK report. The user controls iteration; the skill does not auto-iterate.

## Complementary-scope rule

Each round explicitly lists what previous rounds covered, then picks an area those rounds did NOT cover. This prevents redundant verification and ensures the cumulative audit reaches different parts of the synthesis.

When invoking `/dossier-audit`, supply:
- `target` — the indexed folder to audit
- `focus` — what this round will cover (e.g., "anonymous 2025 arXiv entries", "tool version numbers in 06", "long-tail mid-tier specifics")
- `prior_rounds` (optional) — a list of focus areas covered in previous rounds, so the agent knows what NOT to re-check

If the indexed folder's README already has audit-trail notes from prior rounds, the skill auto-detects them and prepends to `prior_rounds`.

## Aggressiveness levels

Two postures, parameterized by the round's risk tolerance:

- **Standard** (default): if a single quantitative claim in an entry can't be verified, generalize that claim (e.g. "95% ASR" → "high ASR") but keep the entry. Authors / org / mechanism stay if they're correct.
- **Aggressive**: drop the entire entry if any single claim in it can't be fully verified. Used when the audit's purpose is "general second-pass for confidence" — favoring accuracy over completeness.

Pass `aggressiveness=aggressive` to escalate. Document the choice in the round's audit-trail note.

## Compound-license check (v1.9)

When the audit `--focus` is "license risks" (the recommended dataset-pipeline audit focus), spot-check 3-5 entries by re-reading the **prose** of the source page (not just the structured `license:` field). If the prose adds restrictions beyond the YAML license, mark as CORRECT and apply inline:

```
license: '<base license> + custom restrictions: <one-line summary>'
```

The Nectar v1.8 audit caught one such case (`apache-2.0` declared in YAML, but prose restricted to non-commercial research preview). v1.9 codifies the check as standard audit-stage hygiene rather than ad-hoc spot-checking.

**When this check is most valuable**: HuggingFace community uploads, Stanford / academic releases (where ToU may add restrictions), Reddit-derived datasets (where redistribution restrictions are subtle), and any dataset whose YAML license is "permissive" (Apache-2.0, MIT) — those are the highest-risk for prose-overriding-YAML.

## Default arXiv-ID spot-check (v1.1)

When `/research-gather` reports memory-based or time-pressed verification (i.e., entries marked `verified` without per-entry WebFetch confirmation), Stage 5 must include a default 10-entry random arXiv-ID spot-check ALONGSIDE the focus-area work:

1. Pick 10 random entries spanning all topic files (no clustering on one sub-area).
2. For each, WebFetch `primary_url` and confirm: title matches, first author surname matches the bibkey's `{firstauthor}`, year matches the bibkey's `{year}`.
3. Report results in a SPOT-CHECK PASSED table separate from focus-area findings.

Rationale: calibration dogfood produced 1 misattribution-out-of-88 (Yin → Zhang at arXiv:2305.18153) that only Stage 5 caught. The fixed-cost 10-entry sweep catches transposition errors and sloppy attribution at low marginal cost (~10 WebFetches ≈ 5 minutes).

Skip the spot-check only when Stage 2 explicitly reports per-entry WebFetch verification on every entry.

## Display-title preservation rule (v1.1)

Audit must check that display titles match the canonical (arXiv) title verbatim. Practitioner nicknames substituted during synthesis are CORRECT findings:

- "Verbalized Confidence" → "Teaching Models to Express Their Uncertainty in Words" (Lin et al. 2022)
- "LMs (Mostly) Know" → "Language Models (Mostly) Know What They Know" (Kadavath et al. 2022)
- "DoRA" alone → "DoRA: Weight-Decomposed Low-Rank Adaptation"

Section headers and lookup recipes carry the practitioner nickname; the bullet-entry display title carries the canonical paper title. Two slots, two purposes — do not collapse them.

## DROP / CORRECT / FLAG / SPOT-CHECK PASSED report shape

Every round produces a report with these sections:

```markdown
## Round N audit report — <date>, focus: <focus area>

### Prior rounds covered
- Round 1: <focus>
- Round 2: <focus>

### DROP findings (entries removed entirely)
- `<file>` § `<anchor>` — `<entry display name>`
  - Reason: <which claim couldn't be verified>
  - Source attempted: <URL>

### CORRECT findings (specific fields fixed)
- `<file>` § `<anchor>` — `<entry display name>`
  - Field: <Authors / Org / Mechanism / Source URL / ...>
  - Was: <wrong value>
  - Now: <correct value>
  - Source: <URL where the correct value is verified>

### FLAG findings (unverified specifics generalized in place)
- `<file>` § `<anchor>` — `<entry display name>`
  - Specific claim: <quantitative claim that wasn't in abstract>
  - Action: <generalized to "..."> OR <added (unverified, YYYY-MM-DD) annotation>

### SPOT-CHECK PASSED
- `<file>` § `<anchor>` — verified against primary source URL
- `<file>` § `<anchor>` — verified
- ...

### Recommendation
Either:
- "Re-run with focus: <suggested next focus area>" — if findings remain plausible
- "Clean — stop here" — if this round produced no DROP / CORRECT / FLAG findings beyond noise
```

## Applying findings

`/dossier-audit` applies the report's findings inline:
- DROP: removes the entry block from the file. Decrements footer entry count.
- CORRECT: edits the specific field; uses Edit tool with exact-match replacement.
- FLAG: appends `(unverified, YYYY-MM-DD)` annotation to the entry's affected line.
- SPOT-CHECK PASSED: no change; just contributes to verification coverage.

After applying findings, the skill writes the round-N audit-trail note to the indexed folder's README under the `## Verification & limits` section, NOT as a new top-level section.

## v2 strict-live update contract

When the audited folder lives inside a strict-live v2 project (i.e., a parent
directory containing `evidence_ledger.yml` + `cache_manifest.yml` +
`claim_graph.jsonl`), markdown-only edits are not enough. The v2 ledgers must
stay consistent with the markdown, or `/freshness-audit --strict` will fail
the regression check and downstream `/research-kb-export` will ship desynced
data.

For each finding, propagate the change to the v2 artifacts at the project
root (parent directory of the indexed folder):

- **DROP** (entry for bibkey `<bk>` removed):
  - Remove every `evidence_ledger.yml` entry whose `supports[*].claim_id`
    references a claim tied to `<bk>`.
  - Remove every `claim_graph.jsonl` record whose `id` references `<bk>`
    (`ent_<bk>`, `claim_<...>` whose `entity_ids` contained `ent_<bk>`,
    related `evidence`/`cache_blob` records orphaned by the removal).
  - Leave `cache_manifest.yml` alone unless no surviving evidence entry
    references the `cache_id`. Cache blobs are cheap; orphaned ones don't
    fail validation, just bloat the manifest.
- **CORRECT** (a field changed on `<bk>`):
  - If the field is evidence-backed (title, authors, year, headline result):
    update the matching `claim_graph.jsonl` `claim.text` and bump the
    `evidence_ledger.yml` entry's `verification_method` (e.g., to
    `webfetch_<YYYY_MM_DD>`).
  - If the field is cosmetic (formatting, anchor name): no v2 update.
- **FLAG** (annotated `(unverified, YYYY-MM-DD)` or generalized a number):
  - Lower the `confidence.score` on the relevant evidence entry's optional
    `confidence` field. Add a factor noting the audit annotation
    (e.g., `audit_round_<N>_flagged`).
  - Optionally set the matching `claim_graph.jsonl` claim's `status` to
    `conflicted` if the FLAG indicates a quantitative discrepancy.

After applying v2 propagation, the Phase 7 regression checks include
`python validators/freshness.py --strict <project_root>` in addition to the
markdown-only checks. Failure means the v2 ledgers and the markdown are now
out of sync; fix and re-run.

## Audit-trail note format

```markdown
**Independent audit, round <N> (<YYYY-MM-DD>):** A <complementary-scope|aggressive>
review pass focused on <focus area>. Prior rounds covered <prior focuses>. Findings:
<count> dropped, <count> corrected, <count> flagged. <Brief summary of what
discrepancies were typical>. Recommendation: <re-run with focus / clean — stop here>.
```

The `validators/audit_trail.py` validator enforces:
- Round number is a positive integer
- No duplicate round numbers
- Date is in YYYY-MM-DD format

## Regression checks (after each round)

Before reporting success, the skill runs:
- `grep -c "^  - \*\*Source:\*\*"` per file → entry counts (recorded for reference)
- `wc -l` on each file → confirm shrinkage matches DROP count
- `grep` for known-corrected patterns (specific old strings the round corrected) → returns empty
- `python ~/Claude/research_toolkit/validators/agent_index.py <target>` → still passes after edits

If any regression check fails, the skill reports failure WITHOUT having written the audit-trail note. The user can fix the issue and re-run.

## Stopping rule

After applying findings, if the round produced 0 new DROP / CORRECT / FLAG findings:
- Document `**Independent audit, round N (date):** Clean — no new findings.`
- Recommend stopping iteration.

The user decides whether to stop or run another round with a different focus. The skill does NOT auto-iterate (per the toolkit's design choice).

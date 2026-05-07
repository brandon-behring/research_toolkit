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

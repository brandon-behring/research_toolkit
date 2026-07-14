---
name: audit
description: Audit a dossier or corpus for structural validity, claim entailment, source methodology, freshness, rights, and downstream consumer impact.
allowed-tools: Read, Write, Edit, Bash, WebSearch, WebFetch
---

# Independent dossier audit

## Usage

```text
/research-toolkit:audit <dossier-or-corpus> [focus]
```

## Workflow

1. Read `${CLAUDE_PLUGIN_ROOT}/references/canonical_contract.md`,
   `freshness_policy.md`, and `security_and_rights.md`.
2. Freeze an immutable snapshot and record the audit question, reviewer,
   commits, model, tool policy, and input hashes. Do not review a moving target.
3. Run the deterministic boundary first:

   ```bash
   "${CLAUDE_PLUGIN_ROOT}/bin/research-toolkit" audit <dossier> --json
   # or
   "${CLAUDE_PLUGIN_ROOT}/bin/research-toolkit" corpus check <corpus-root> --json
   ```

4. Review each claim in complete source context. Distinguish byte presence from
   entailment; test scope, qualifiers, counterevidence, and currentness.
5. Assess methods and risk of bias separately from publisher authority. Check
   sampling, comparison, measurement, statistical uncertainty, limitations,
   conflicts, and applicability when relevant.
6. Audit source provenance as a separate gate. Reject persisted credentials,
   signed URLs, unsanitized query values, URL-derived hashes, and missing
   `final_url` on a changed effective URL. Do not treat requested or final
   provenance as semantically canonical without review. Flag any current-run browser capture,
   because browser execution is disabled pending a verified OS/network sandbox;
   flag parsed PDFs that lack an explicit source-specific risk decision.
7. Review synthesis prose and result sentences even when they are absent from
   an older claim graph.
8. Independently review every proposed `narrow`, `rewrite`, `remove`, or
   `unresolved` disposition and all high-consequence claims. Preserve the raw
   question, snapshot hash, answer, and adjudication.
9. Write `ClaimReviewRecord` entries. Keep audit findings separate from fixes;
   apply only adjudicated corrections to canonical records.
10. Run impact analysis before accepting a removal or supersession:

   ```bash
   "${CLAUDE_PLUGIN_ROOT}/bin/research-toolkit" impact <dossier> --claim-id <claim-id>
   ```

11. Rebuild derived artifacts and rerun deterministic validation.

**HARD RULE:** A supporting URL, matching substring, or valid claim ID never
substitutes for a semantic entailment decision.

## Validation

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/research-toolkit" audit <dossier>
```

## Output / handoff

Produce review records, a finding register, affected consumer paths, and an
adjudication-ready correction set. Hand clean dossiers to
`/research-toolkit:release` and stale ones to `/research-toolkit:freshness`.

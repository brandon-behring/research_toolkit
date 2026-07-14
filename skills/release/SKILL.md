---
name: release
description: Gate a reviewed dossier release on provenance, semantic review, freshness, rights, consumer bindings, deterministic artifacts, and exact hashes.
allowed-tools: Read, Write, Edit, Bash
---

# Research release gate

## Usage

```text
/research-toolkit:release <dossier> [release-id]
```

## Workflow

1. Read `${CLAUDE_PLUGIN_ROOT}/references/canonical_contract.md`,
   `freshness_policy.md`, and `security_and_rights.md`.
2. Refuse a release ID outside `rr-YYYYMMDD.N`. Record exact toolkit, dossier,
   consumer, and synthesis-KB commits plus dirty digests.
3. Require adjudicated reviews for every active claim and independent review
   wherever policy requires it. Block unwaived Critical or High findings.
4. Require source watches to be current at the release cutoff and replay full
   discovery when quarterly or pre-release policy requires it.
5. Fail closed on retrieval provenance. Reject persisted credentials, signed or
   unsanitized query values, URL-derived hashes, missing changed `final_url`,
   unreviewed identity-changing redirects, and any current-run browser capture. Browser execution is
   disabled pending a verified process sandbox and default-deny network
   boundary. Require an explicit risk decision for every parsed PDF; raw-only
   captures remain the default.
6. Verify rights and visibility before export. Restricted bodies remain local;
   exports contain only permitted metadata, hashes, citations, and excerpts.
7. Rebuild every `derived/` artifact from canonical records. Generate consumer
   bindings, deletion-aware tombstones, the release manifest, and downstream
   `research-lock.json` records.
8. Run the complete deterministic gate:

   ```bash
   "${CLAUDE_PLUGIN_ROOT}/bin/research-toolkit" audit <dossier> --release
   "${CLAUDE_PLUGIN_ROOT}/bin/research-toolkit" release check <dossier>
   ```

9. Rebuild a second time from the same inputs and require byte-identical
   outputs. Confirm all manifest and lock hashes agree.
10. Present the release evidence and unresolved waivers to the user. Do not
   publish, push, merge, or ingest into an external system without explicit
   authorization.

**HARD RULE:** A release manifest records evidence of completed gates; it must
never be used to waive or conceal a red gate.

## Validation

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/research-toolkit" release check <dossier>
```

## Output / handoff

Produce `release.json`, deterministic derived artifacts, consumer bindings,
research locks, validator results, reviewer acceptance, and explicit waivers.

---
name: research
description: Build or refresh an auditable research dossier when the user needs current evidence, claim-level review, consumer lineage, and a gated release.
allowed-tools: Read, Write, Edit, Bash, WebSearch, WebFetch
---

# Research dossier workflow

## Usage

```text
/research-toolkit:research "<topic>" [dossier-directory]
```

## Workflow

1. Read `${CLAUDE_PLUGIN_ROOT}/references/decision_protocol.md`,
   `canonical_contract.md`, `security_and_rights.md`, and the relevant source
   methodology references.
2. Inspect the target repository, prior dossier, consumers, and dirty state.
   Freeze commits and hashes in an isolated run manifest.
3. Resolve consequential options with the decision protocol. Do not retrieve
   sources until the manifest is decision-complete.
4. Initialize a new boundary when needed:

   ```bash
   "${CLAUDE_PLUGIN_ROOT}/bin/research-toolkit" research run <dossier> --initialize \
     --dossier-id <id> --topic "<topic>" --run-id <run-id> --date <YYYY-MM-DD>
   ```

5. Execute the canonical stages in order:

   ```text
   discover → intake → capture → normalize → evidence/claims
   → independent audit → synthesis/render → release → watch/refresh
   ```

6. Log every query, result, acceptance, rejection, escalation, and source
   snapshot. Prefer primary and official sources; use secondary material for
   discovery or explicitly bounded context.
   Capture public source bytes through the bounded plugin script and state
   rights/access explicitly; never infer either from reachability:

   ```bash
   "${CLAUDE_PLUGIN_ROOT}/bin/research-toolkit" cache-source <URL> \
     --topic <topic> --rights-status unknown --visibility public \
     --no-extract-pdfs
   ```

   Treat every query value as potentially sensitive. Prefer a query-free
   canonical URL and never submit a signed/authenticated URL. The retriever
   rejects generic queries before DNS and accepts only its small allowlist of
   public resource identifiers. Cache output records sanitized requested
   provenance plus sanitized `final_url` whenever the effective URL changes;
   canonical identity remains a separate review decision.
   Do not pass `--escalate-on-failure`: browser execution is disabled pending a
   verified process sandbox and default-deny network boundary. PDF parsing is
   also outside the default path; omitting `--no-extract-pdfs` requires an
   explicit, recorded source-specific risk decision.
7. Separate source authority, independence, study design, limitations, rights,
   and currency. Preserve counterevidence.
8. Create atomic claims and many-to-many evidence links. A real excerpt is not
   sufficient: record a semantic review for entailment and currency.
9. Obtain independent review for unsupported, uncertain, volatile,
   quantitative, security, compliance, and synthesis claims.
10. Build consumer bindings and deterministic derived artifacts. Never edit a
    generated artifact directly.
11. Run `${CLAUDE_PLUGIN_ROOT}/bin/research-toolkit audit <dossier>` after each
    canonical stage and halt on failure. Cap a failing stage at three narrow
    retries and leave a resumable checkpoint.
12. Hand off to `/research-toolkit:release`; do not publish from this skill.

**HARD RULE:** Never advance, export, or claim completion while a validation or
required semantic-review gate is red.

**RETRIEVAL HARD RULE:** A JS-only or query-unsafe source is unresolved, not
permission to run a browser or weaken the URL boundary. Review redirects that
change source identity, authority, scope, or rights before acceptance.

## Validation

The canonical `research-toolkit audit` gate must be green; invoke it through
the isolated bundled launcher shown below.

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/research-toolkit" audit <dossier>
"${CLAUDE_PLUGIN_ROOT}/bin/research-toolkit" impact <dossier> --claim-id <claim-id>
```

## Output / handoff

Produce canonical records, immutable run provenance, adjudicated reviews, due
source watches, and deterministic derived artifacts. Hand a reviewed dossier to
`/research-toolkit:release`.

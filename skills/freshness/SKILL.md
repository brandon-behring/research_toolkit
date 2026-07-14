---
name: freshness
description: Check watched research sources, classify changes, replay discovery when due, and prepare human-reviewed refresh work without automatic publication.
allowed-tools: Read, Write, Edit, Bash, WebSearch, WebFetch
---

# Living freshness workflow

## Usage

```text
/research-toolkit:freshness <dossier-or-corpus> [--today YYYY-MM-DD]
```

## Workflow

1. Read `${CLAUDE_PLUGIN_ROOT}/references/freshness_policy.md`,
   `canonical_contract.md`, and `security_and_rights.md`.
2. Select due records without mutation:

   ```bash
   "${CLAUDE_PLUGIN_ROOT}/bin/research-toolkit" freshness poll <dossier> \
     --today <YYYY-MM-DD> --json
   ```

3. Retrieve due public sources through
   `${CLAUDE_PLUGIN_ROOT}/bin/research-toolkit cache-source` under the security
   and rights boundary. State `--rights-status` and `--visibility`; never infer
   them from HTTP success. Use the default-safe form:

   ```bash
   "${CLAUDE_PLUGIN_ROOT}/bin/research-toolkit" cache-source <sanitized-public-url> \
     --topic <topic> --rights-status unknown --visibility public \
     --no-extract-pdfs
   ```

   Treat every query value as potentially sensitive and refuse signed or
   authenticated URLs. Generic queries fail before DNS; only allowlisted public
   identifiers are retrievable. The command records sanitized requested
   provenance and sanitized `final_url` whenever the effective URL changes;
   review any identity/authority/rights change. URL fingerprints are forbidden
   and do not make an unsafe query suitable for export. Browser
   execution and `--escalate-on-failure` are disabled pending a verified process
   sandbox and default-deny network boundary. PDF parsing requires a separate,
   explicit risk decision.
4. Classify each result as `unchanged`, `cosmetic`, `material`, `breaking`,
   `unreachable`, or `retracted`. Do not equate HTTP success or a recent fetch
   date with semantic freshness.
5. Run impact analysis for changed or unavailable sources:

   ```bash
   "${CLAUDE_PLUGIN_ROOT}/bin/research-toolkit" impact <dossier> --source-id <source-id>
   ```

   Review every affected evidence link, claim, synthesis, and consumer; source
   replacement alone does not preserve entailment.

6. Replay stored discovery queries quarterly, before release, and whenever a
   source event suggests the topic landscape changed. Log new queries and
   exclusion decisions.
7. Write `RefreshEvent` records beneath the active run. Require human semantic
   review before changing claims, consumers, or watch dates.
8. Rebuild canonical and derived artifacts only after adjudication, then run
   dossier and release gates.

**HARD RULE:** Scheduled or unattended polling is read-only. Never publish,
push, edit claims, or accept semantic changes automatically.

**RETRIEVAL HARD RULE:** Do not turn a JS-only, query-unsafe, or
identity-changing redirect into an apparently accepted refresh. Keep it
unresolved and route it to human review.

## Validation

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/research-toolkit" audit <dossier>
"${CLAUDE_PLUGIN_ROOT}/bin/research-toolkit" freshness poll <dossier> \
  --today <YYYY-MM-DD>
```

## Output / handoff

Produce due-source reports, refresh events, impact paths, and a reviewed change
set. Use `/research-toolkit:research` for material re-research and
`/research-toolkit:release` after acceptance.

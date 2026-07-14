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
   research-toolkit freshness poll <dossier> --today <YYYY-MM-DD> --json
   ```

3. Retrieve due sources under the security and rights boundary. Record the
   requested, canonical, and final URLs plus raw and normalized digests.
4. Classify each result as `unchanged`, `cosmetic`, `material`, `breaking`,
   `unreachable`, or `retracted`. Do not equate HTTP success or a recent fetch
   date with semantic freshness.
5. Run impact analysis for changed or unavailable sources:

   ```bash
   research-toolkit impact <dossier> --source-id <source-id>
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

## Validation

```bash
research-toolkit audit <dossier>
research-toolkit freshness poll <dossier> --today <YYYY-MM-DD>
```

## Output / handoff

Produce due-source reports, refresh events, impact paths, and a reviewed change
set. Use `/research-toolkit:research` for material re-research and
`/research-toolkit:release` after acceptance.

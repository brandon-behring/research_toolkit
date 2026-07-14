---
name: topic-discovery
description: Mine a knowledge corpus into a current, deduplicated research backlog with explicit scope choices, evidence gaps, priorities, and consumer value.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Topic discovery

## Usage

```text
/research-toolkit:topic-discovery <corpus> [output]
```

## Workflow

1. Read `${CLAUDE_PLUGIN_ROOT}/references/decision_protocol.md` and
   `topic_discovery_protocol.md`.
2. Inspect corpus loaders, identifiers, existing dossiers, backlog records,
   consumer learning objectives, and release status before asking questions.
3. Resolve corpus boundary, audience, desired topic mix, exclusions, priority
   rubric, and output limit with the decision protocol.
4. Mine deepen opportunities from unresolved reading items, high-level learning
   objectives, thinly supported claims, and frontier sections. Mine adjacent
   opportunities from cross-domain intersections and explicit open problems.
5. Emit only corpus identifiers returned by the repository's loader. Never
   invent a volume, chapter, or objective ID.
6. Deduplicate against existing backlog entries, dossiers, releases, and
   consumer bindings. Log every dropped candidate and reason.
7. Score each candidate from evidence gap, consequence, transferability,
   consumer demand, and research tractability. Keep the rationale traceable to
   corpus passages.
8. Append only net-new candidates; preserve existing lifecycle history.
9. Validate the backlog using the existing deterministic validator until a v1
   canonical backlog contract replaces it:

   ```bash
   python ${CLAUDE_PLUGIN_ROOT}/validators/topic_backlog.py <output>
   ```

## Validation

```bash
python ${CLAUDE_PLUGIN_ROOT}/validators/topic_backlog.py <output>
```

## Output / handoff

Produce a prioritized, deduplicated backlog with decision provenance. Hand a
selected entry to `/research-toolkit:research`.

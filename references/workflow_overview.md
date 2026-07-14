# Workflow overview

## Public Claude interface

```text
/research-toolkit:topic-discovery ──▶ /research-toolkit:research
                                             │
                                             ▼
                                  /research-toolkit:audit
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼                                           ▼
            /research-toolkit:freshness                 /research-toolkit:release

/research-toolkit:dataset-research ──▶ audit ──▶ release
```

All commands are plugin-namespaced. The old flat skills are not aliases.

## Canonical stage order

```text
discover → intake → capture → normalize → evidence/claims
→ independent audit → synthesis/render → release → watch/refresh
```

| Stage | Agent judgment | Deterministic boundary |
|---|---|---|
| discover | scope, queries, coverage, source candidates | run/query records validate |
| intake | authority, independence, rights, relevance | `SourceRecord` validates |
| capture | source retrieval and escalation choice | bytes, paths, and hashes validate |
| normalize | extraction-quality judgment | normalized digest validates |
| evidence/claims | atomic propositions and support selection | IDs and references validate |
| independent audit | entailment, currency, methods, bias | `ClaimReviewRecord` validates |
| synthesis/render | bounded interpretation | derived outputs are reproducible |
| release | reviewer acceptance and waiver decision | artifact and lock hashes validate |
| watch/refresh | semantic change classification | due dates and impact paths validate |

## CLI

```bash
research-toolkit research run --help
research-toolkit audit <dossier>
research-toolkit freshness poll <dossier>
research-toolkit impact <dossier> --claim-id <id>
research-toolkit release check <dossier>
research-toolkit corpus check <root>
research-toolkit dataset run --help
```

During migration, the existing flat deterministic producer commands remain
callable. They do not make the old Claude skills discoverable.

## Failure rule

Every stage ends in a deterministic gate and, where meaning is involved, an
explicit semantic review. Retry a failing stage at most three times with the
narrowest correction. Then halt with a named checkpoint; never export or
release a partially green dossier.

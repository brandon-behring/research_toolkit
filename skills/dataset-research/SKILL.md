---
name: dataset-research
description: Research and release a dataset dossier with licensing, privacy, leakage, duplication, recipe, cost, and reproducibility controls.
allowed-tools: Read, Write, Edit, Bash, WebSearch, WebFetch
---

# Dataset research workflow

## Usage

```text
/research-toolkit:dataset-research "<topic>" [dossier-directory]
```

## Workflow

1. Read `${CLAUDE_PLUGIN_ROOT}/references/decision_protocol.md`,
   `canonical_contract.md`, `dataset_sources.md`, and
   `security_and_rights.md`.
2. Inspect existing datasets, recipes, model constraints, consumers, and dirty
   state. Resolve task, population, split policy, license, privacy, evaluation,
   budget, and release choices with the decision protocol.
3. Initialize the deterministic boundary:

   ```bash
   research-toolkit dataset run <dossier> --initialize \
     --dossier-id <id> --topic "<topic>" --run-id <run-id> --date <YYYY-MM-DD>
   ```

4. Discover across appropriate registries and primary dataset sources. Record
   queries, versions, checksums, access conditions, licenses, and exclusions.
   Preserve every source URL exactly; never substitute a remembered domain
   (the historical Cornell→UCR failure is the canonical warning).
5. Validate dataset cards and primary artifacts rather than copying aggregator
   claims. Record schema, units, provenance, population, collection method,
   missingness, known biases, and version history.
6. Check license compatibility, PII/sensitive fields, consent, policy limits,
   train/evaluation leakage, near duplicates, and contamination. Apply the
   compound-license check: read prose restrictions as well as the declared
   license field (the Nectar mixed-terms case is the canonical warning).
7. Pin the complete recipe: source versions and hashes, filtering, transforms,
   split seed, model/version, prompt/template hashes, resume semantics, and
   cost/accounting assumptions.
8. Create atomic claims, evidence links, and independent reviews under the same
   contract as research dossiers. Never infer a license or usage permission
   from accessibility.
9. Run `research-toolkit audit <dossier>` and halt on failure. Hand the reviewed
   dossier to `/research-toolkit:release`.

## Validation

```bash
research-toolkit audit <dossier>
research-toolkit dataset run <dossier>
```

## Output / handoff

Produce a reproducible dataset dossier, review records, checksummed recipe,
rights decisions, and derived index. Release only through
`/research-toolkit:release`.

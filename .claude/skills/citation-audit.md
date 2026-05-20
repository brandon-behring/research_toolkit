---
name: citation-audit
description: Use when the user has a strict-live v3 project with evidence_ledger.yml at schema_version 3 and asks to audit citations, verify claim grounding, or check that quoted excerpts actually appear in cached sources. Runs scripts/verify_citations.py to produce a mechanical FACT-framework citation audit report (substring check + per-method breakdown + per-claim grounding strength). No LLM required for the verification step itself.
allowed-tools: Read, Bash
paths: '**/evidence_ledger.yml'
---

# /citation-audit — Mechanical citation verification (v3 strict-live)

## Usage

```
/citation-audit <project_dir> [--today YYYY-MM-DD]
```

## When to use

- After `/research-gather` produces (or after manual edits to) a v3
  evidence_ledger.yml with `extraction_method: verbatim_match` anchors.
- Before `/research-kb-export` to ensure no broken citations ship.
- As part of `/freshness-audit` to surface citation health alongside trust state.

**Not for v2 projects** — v3 schema introduces `extraction_method` and
`excerpt_anchor`; v2 evidence entries have no per-link substring grounding to verify.

**Upstream:** `/research-gather` produces evidence_ledger.yml.
**Downstream:** `/freshness-audit` Phase 5 (dashboard build) consumes the
metrics; `/research-kb-export` should not run while substring failures are open.

## Workflow

### Phase 1: detect schema version

```bash
grep "^schema_version:" <project_dir>/evidence_ledger.yml
```

If `schema_version: 2`, this skill is **not applicable** — report that the
project is v2 legacy and exit. Suggest the user migrate to v3 with
`scripts/migrate_v2_to_v3.py` (when available) if they want per-link
verification.

### Phase 2: run the mechanical audit

```bash
python ~/Claude/research_toolkit/scripts/verify_citations.py <project_dir> --today <YYYY-MM-DD>
```

The script:
- Reads `<project_dir>/evidence_ledger.yml` and `<project_dir>/cache_manifest.yml`.
- For each `supports[]` link with `extraction_method: verbatim_match`,
  loads the cached text_path file, slices the bytes at the declared
  offset, hashes the slice, compares to `sha256_of_span`, and checks the
  slice text matches the excerpt (whitespace-normalized).
- Bins each link into `strong / partial / weak` by extraction method.
- Computes per-claim grounding strength (best bucket across all supporting links).
- Writes `<project_dir>/citation_audit_report.md`.
- Exits 0 on all-pass, 1 on any substring failure.

### Phase 3: read the report

Read `<project_dir>/citation_audit_report.md`. Surface to the user:
- Summary line: `<strong>/<total>` grounding rate.
- Substring pass rate.
- Any per-claim bucket downgrades (claims with only `weak` evidence).
- Substring check failures (full list).

### Phase 4: act on failures (if any)

For each substring failure:
- **sha256_of_span mismatch**: the cached text drifted (the file was
  re-extracted or normalized differently). Re-fetch the source via
  `scripts/cache_source.py` and recompute the offset + hash.
- **excerpt does not match span**: the excerpt in the evidence entry
  doesn't appear at the declared offset. Either the offset is wrong, or
  the excerpt was paraphrased. Either fix the offset or change
  `extraction_method` to `paraphrase` (and `link_confidence` to ≤0.85).
- **text_path file does not exist**: the cache blob was deleted. Re-cache
  via `scripts/cache_source.py`.

### Phase 5: re-run

After fixes, re-run Phase 2 until exit code is 0.

## Templates

(none — this skill writes a report, not a templated artifact)

## References

- `Read ~/Claude/research_toolkit/references/strict_live_v2.md` — for the
  v3 strict-live regime overview.

## Validation

The script itself validates output:

```bash
python ~/Claude/research_toolkit/scripts/verify_citations.py <project_dir>
echo "Exit code: $?"  # 0 = all pass, 1 = substring failures
```

## Output / handoff

**Produces:**
- `<project_dir>/citation_audit_report.md` — human-readable per-claim
  grounding breakdown.
- Exit code 0 / 1 signals all-pass / failures-present.

**Consumed by:**
- `/freshness-audit` — embeds the same metrics in `dashboard.md` Claim
  Health section.
- `/research-kb-export` — should not run while exit code is 1.
- The user, who acts on per-claim grounding-strength flags.

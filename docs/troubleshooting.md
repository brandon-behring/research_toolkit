# Troubleshooting

Common failure modes distilled from BURN_IN_NOTES.md. Each entry: symptom →
cause → fix.

## URL extraction returns 0 URLs (silent fail)

**Symptom:** `/url-freshness-check` reports `total: 0` despite the artifact
clearly having URLs. No error.

**Cause:** macOS `grep -E` silently produces 0 matches on negative char-class
regexes like `[^[:space:]\)\]"\<]+`. The bracketed escape sequences are
interpreted differently than on GNU grep.

**Fix:** the v1.1 skill body uses the positive char-class form:

```bash
grep -hroE 'https?://[a-zA-Z0-9./?=&_~%#:+-]+' "$TARGET_FOLDER"
```

Confirm extraction worked:

```bash
N=$(wc -l < .url_check_tmp/urls.txt)
test "$N" -gt 0 || echo "FATAL: regex bug" >&2
```

The url-freshness-check skill body has this sanity check baked in.

## Validator can't be imported (`ModuleNotFoundError: validators`)

**Symptom:** `python validators/bib_ledger.py path` fails with
`ModuleNotFoundError: No module named 'validators'`.

**Cause:** Pre-v1.1, validators required `pip install -e .` or `python -m
validators.<name>` to resolve the relative import `from validators._common
import cli_main`.

**Fix:** v1.1+ injects the toolkit root into `sys.path` when run as a script:

```python
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
```

If you see this error: you're on a pre-v1.1 toolkit. Pull latest, or run
via `python -m validators.<name> <path>`.

## GitHub URLs in dossier 404 in bulk (3-7%)

**Symptom:** `/url-freshness-check` reports many hard 404s on GitHub URLs.
Pattern: the broken URLs follow `github.com/<paper-firstauthor>/<paper-slug>`.

**Cause:** Pre-v1.1, the `/dossier-build` and `/agent-index` skills guessed
GitHub URLs from the `<author>/<paper-name>` heuristic. Real repos live at
lab orgs (`pilancilab/spectral_adapter`), unrelated handles
(`EricLBuehler/xlora`, `tripplyons/oft`), or simply don't exist.

**Fix:** v1.1 skill bodies hard-code the dash-default rule:

> If you find yourself typing `github.com/<paper-firstauthor>/<paper-name>`,
> STOP. That's the failing pattern. Use `—`.

Backfilling with `scripts/backfill_ledger.py` populates the ledger's
`code_url` field from the dossier (which has human-curated repo info).

If you see fresh 404s on a new run: investigate whether the dossier-build or
agent-index skill is being run on outdated guidance. Check:

```bash
grep -A3 "Cell rendering" ~/Claude/research_toolkit/.claude/skills/dossier-build.md
```

The HARD RULES section should be present.

## "Memory-verification suspected" warning

**Symptom:** `python -m validators.bib_ledger ledger.yml` emits:

```
WARN memory-verification suspected: <N> entries, all marked 'verified' (no
'unverified' or 'mismatched'). Per-entry WebFetch verification typically
produces ≥2 mismatched/unverified entries on a run this size.
```

**Cause:** Stage 2 (`/research-gather`) marked every entry `verified` from
memory under time pressure rather than per-entry WebFetch confirmation. This
is the calibration §2.1 anti-pattern that produced 1 misattribution out of 88
which only Stage 5 audit caught.

**Fix:** the warning is informational. To resolve:

1. **Re-run Stage 2** with explicit per-entry WebFetch (the v1.1 skill body
   defaults to `unverified` until evidence; subagent should follow this).
2. **Or:** treat the ledger as `unverified` and run a strong `/dossier-audit`
   with the default 10-entry random arXiv-ID spot-check (per
   `references/audit_protocol.md`).

To gate CI on this warning, add `--strict`:

```bash
python -m validators.bib_ledger ledger.yml --strict
```

## Cross-stage validator says `claim_family X not in taxonomy`

**Symptom:** `python -m validators.cross_stage <project>` errors:

```
bib_ledger uses 1 claim_family value(s) not in research_plan.md taxonomy:
['my_new_family']
```

**Cause:** A bib_ledger entry uses a `claim_family` value that isn't in the
`research_plan.md` "## Claim family taxonomy" section. Pre-v1.2 this was
silent.

**Fix:** either:

1. **Add the family to the plan** if the ledger is correct (preferred when
   the plan was incomplete).
2. **Re-classify the entry** if the family was a typo or scope drift.

Cross-stage validation is a hard error, not a warning — it blocks downstream
stages.

## Subagent reports wrong entry count

**Symptom:** `/research-gather` final report says "73 entries" but
`grep -c "^- bibkey:" bib_ledger.yml` shows 88.

**Cause:** Subagent self-counting drift (calibration §2.2). Subagents under context
pressure can produce inconsistent narrative counts vs file counts.

**Fix:** v1.1 skill body adds a count-assertion in Phase 6:

```bash
grep -c "^- bibkey:" <output_dir>/bib_ledger.yml
```

The narrative count must match. If it doesn't, recount before reporting.

For a structured query of all known friction:

```bash
python scripts/burn_in_query.py --status surfaced --severity high
```

## Kaggle WebFetch returns 403 / empty metadata (dataset pipeline)

**Symptom:** During `/dataset-gather`, WebFetch on `kaggle.com/datasets/<owner>/<slug>`
returns a 403, an empty page, or metadata fields that all come back blank.

**Cause:** Kaggle's dataset metadata is gated behind a logged-in session. The
public dataset URL renders a login wall to anonymous fetchers; the underlying
JSON metadata is only served to authenticated browsers / the Kaggle CLI.

**Fix:** Don't fight the paywall. In the ledger entry:

- Set `auth_required: true`.
- Leave fields you can't extract (`size_rows`, `columns`, `schema_url`) as `unknown`.
- Document the limitation in the audit pass — Kaggle entries are honest-incomplete
  rather than confidently-wrong.

If the topic is Kaggle-heavy, consider noting in the dataset-pipeline README that
many entries will require Kaggle login for access — set reader expectations.

## `source: other` is 20-40% of dataset_ledger entries

**Symptom:** After `/dataset-gather`, a noticeable fraction of entries have
`source: other` rather than mapping to one of the 8 canonical categories
(HF / Kaggle / academic / aggregators / cloud / domain / gov / classical_ml).

**Cause:** The topic is in a domain where canonical aggregators don't dominate.
The v1.6 dogfood on time-series anomaly detection found 29% `source: other` —
PhysioNet (biomedical), iTrust (critical-infrastructure security),
Yahoo Webscope (the legacy Yahoo data archive), Backblaze (drive-failure logs),
ELKI (academic clustering toolkit), etc.

**Fix:** This is **expected** for security / biomedical / IoT / critical-infrastructure
topics. Do not force these entries into a closer-but-wrong category. See
`references/dataset_sources.md` § "When `source: other` is the right answer"
for the canonical list of legitimate `other` repositories and the rule
(v1.7 codified) that `source: other` is the correct call when the dataset is
primarily distributed by its host institution rather than a generic aggregator.

If `source: other` exceeds ~40%, the search may be missing canonical-aggregator
hits — re-run with explicit HF / Kaggle queries to verify nothing was overlooked.

## "memory-verification suspected" warning on `dataset_ledger.yml`

**Symptom:** `python -m validators.dataset_ledger ledger.yml` emits:

```
WARN memory-verification suspected: <N> entries, all marked 'verified'
```

at ≥30 entries. The bib_ledger version of this warning fires at ≥50; the
dataset_ledger threshold is lower (30) because dataset metadata is harder to
recall from memory than paper bibliography.

**Cause:** `/dataset-gather` Stage 2 bulk-marked entries as `verified` from
memory rather than per-entry WebFetch confirmation. Same anti-pattern as the
calibration §2.1 finding (v1.5c) but for datasets.

**Fix:** Re-run with strict per-entry WebFetch verification. Aim for 85-95%
verified plus a few honest `unverified` entries (e.g., gated Kaggle datasets,
dead-link recovery cases). 100% verified at scale is the signature of memory
inflation, not real verification.

To gate CI on this warning:

```bash
python -m validators.dataset_ledger ledger.yml --strict
```

## agent_index has the wrong domain in a Source URL (Cornell vs UCR pattern)

**Symptom:** A 5-bullet dataset entry's `**Source:**` URL points to the wrong
domain — e.g., `cs.cornell.edu/...` for the UCR Time Series Archive (which is
hosted at `cs.ucr.edu`; Eamonn Keogh, the maintainer, is at UCR).

**Cause:** The rendering subagent substituted a domain from prior knowledge of
the maintainer's affiliation rather than reading it off the dataset_ledger entry.
This is the v1.6 dogfood failure: the agent "knew" Keogh works on time-series
and remembered Cornell from elsewhere, then conflated the two. Surfaced under
audit, not validation.

**Fix:** v1.7 codified the rule in `/dataset-index` skill body:

> NO domain substitution from memory. The `**Source:**` URL must come from the
> dataset_ledger entry's `primary_url` field — unchanged, character-for-character.

If you see this pattern, re-run `/dataset-index` (the skill body now has the
rule baked in). Fix the immediate occurrence by reading the ledger entry's
`primary_url` and copying it verbatim.

## License says one thing in YAML, another in prose (compound-license)

**Symptom:** A dataset_ledger entry declares e.g. `license: apache-2.0`, but
the `Size+License` bullet's prose paragraph says "non-commercial use only" or
adds restrictions not in the SPDX identifier.

**Cause:** Stage 2 (`/dataset-gather`) read the source page's structured `license:`
field but didn't read the prose section that adds restrictions on top. The v1.8
Nectar dogfood surfaced this — Nectar declared `apache-2.0` in YAML but added
non-commercial use restrictions in the prose. Phase A audit missed it; Phase C
license-focused audit caught it.

**Fix:** v1.9 codified the compound-license rule in `/dataset-gather` Phase 3
and in `references/audit_protocol.md`:

> If the source page's license declaration AND prose disagree, render the
> license field as `<base> + custom restrictions: <one-line summary>`. Don't
> drop either side.

To catch existing compound-license cases in already-rendered ledgers, run:

```
/dossier-audit <ledger_dir> --focus "license risks"
```

The audit pass cross-checks YAML license fields against the prose bullets and
flags disagreements.

## cross_stage warns about orphan ledger entries / orphan synthesis refs

**Symptom:** `python -m validators.cross_stage <project>` emits warnings like:

```
WARN: 3 dataset_ledger entries not found in agent_index synthesis
WARN: 2 Source URLs in agent_index not found in dataset_ledger
```

(v1.9 extended `cross_stage` to handle dataset_ledger ↔ agent_index pairs the
same way it handles bib_ledger ↔ agent_index.)

**Cause:** Ledger and synthesis are out of sync. Either the ledger has entries
not yet rendered into the agent_index (Stage 2 didn't run on the latest ledger),
or the agent_index has Source URLs from outside the ledger (manual edit, or a
prior ledger version that's since been pruned).

**Fix:** First diagnose which direction the drift goes:

- **Orphan ledger entries** (ledger has more than agent_index): re-run
  `/dataset-index` to render the missing entries.
- **Orphan synthesis refs** (agent_index has more than ledger): either add the
  missing entries to the ledger (preferred — ledger is canonical) or remove
  the unknowable bullets from the agent_index.

`--strict` promotes both warnings to errors:

```bash
python -m validators.cross_stage <project> --strict
```

Use `--strict` pre-publish; default warnings during in-progress runs.

## strict-live v2 freshness fails on a stale entry

**Symptom:** `python validators/freshness.py --strict <project>` reports
`stale as of <date>`.

**Cause:** v2 treats freshness as a blocker. The entry's `verified_at` (or
`retrieved_at`) plus `stale_after_days` is older than today's strict-live
window.

**Fix:** run:

```bash
/freshness-audit <project> --strict
```

Re-fetch the primary/official source, cache the artifact, update
`cache_manifest.yml`, add or update field-level evidence in `evidence_ledger.yml`,
and then update the ledger entry's `verified_at`, `evidence_ids`, and
`cache_ids`.

## cache_manifest hash mismatch

**Symptom:** `python validators/cache_manifest.py <manifest>` reports
`sha256: expected <X>, actual <Y>` on a cache entry.

**Cause:** the raw blob at `raw_path` was modified after the manifest was
written (manual edit, lost-and-restored from a different revision, line-ending
normalization on checkout). The manifest's recorded hash no longer matches the
file on disk.

**Fix:** if the source is still reachable, run `python scripts/cache_source.py
<url> --topic <topic>` to regenerate the blob + hash + manifest entry, then
replace the manifest entry. If the source is unreachable, recompute the hash
inline (`shasum -a 256 <raw_path>`) and update the entry's `sha256` and
`bytes` fields — but only if you trust the modified content is still
authoritative.

## cache_manifest references a file that doesn't exist

**Symptom:** `python validators/cache_manifest.py <manifest>` reports
`raw_path: file does not exist`, `text_path: file does not exist`, or
`metadata_path: file does not exist`.

**Cause:** the cache directory was not committed (default — `research_cache/`
is gitignored), the project was restored from a partial backup, or the path
in the manifest was renamed.

**Fix:** if you have the source URL, re-cache with
`python scripts/cache_source.py <url> --topic <topic>` and replace the
manifest entry with the script's printed YAML. If the URL is unreachable
(403, removed, paywalled), remove the manifest entry AND every reference to
its `cache_id` from `bib_ledger.yml`, `dataset_ledger.yml`, and
`evidence_ledger.yml`, then re-run `/freshness-audit --strict` so the project
is internally consistent.

## Restricted source slipped through to research-kb export

**Symptom:** A `cache_id` for a source you didn't intend to redistribute
appears in `research_kb_export.jsonl` cache_blob records.

**Cause:** the export script does verbatim wrap of the claim_graph. If the
ledgers reference a restricted source's `cache_id`, that ID flows through.
The `rights_status: restricted` flag on the cache entry doesn't block the
export by itself.

**Fix:** for restricted sources, set both `rights_status: restricted` (or
`cache_only`) AND `restricted: true` on the cache_manifest entry, then
remove its `cache_id` from any `evidence_ledger`/`bib_ledger`/`dataset_ledger`
entry you intend to export. The export only propagates cache_ids that the
ledgers explicitly list. For paywalled or access-controlled sources, record
the access notes in `metadata.json` so future readers know what's needed to
re-fetch.

## research-kb export fails validation

**Symptom:** `validators/research_kb_export.py` rejects a JSONL export.

**Cause:** every export record must have `export_schema_version: 2`,
`record_type`, `id`, `source_project`, `exported_at`, and a non-empty `payload`.

**Fix:** generate with the bundled exporter after freshness passes:

```bash
python scripts/research_kb_export.py <project>
python validators/research_kb_export.py ~/Claude/research-kb/inbox/research_toolkit/<project>.jsonl
```

## gather_trace fails: bad IsSup / IsUse / decision / bibkey

**Symptom:** `python validators/gather_trace.py gather_trace.yml` reports
errors like:
- `fetches[N].is_supported: 'kinda' not in ['full', 'none', 'partial']`
- `fetches[N].is_useful: must be integer in [1, 5]`
- `fetches[N].decision: 'maybe' not in ['accept', 'escalate_to_manual', 'reject']`
- `fetches[N]: decision 'accept' requires an assigned_bibkey`
- `fetches[N].assigned_bibkey: 'foo' not found in bib_ledger (closest match: ['fooatall'])`

**Cause:** /research-gather Phase 2 reflection emitted an out-of-enum
value, an out-of-range IsUse score, or an inconsistent (decision,
assigned_bibkey) pair. The accept↔assigned_bibkey invariant is
strict: accept requires the key; reject and escalate_to_manual must
omit it.

**Fix:** edit the gather_trace.yml fetch in question. IsSup must be one
of `full | partial | none`; IsUse must be integer 1–5; decision must be
`accept | reject | escalate_to_manual`. For unknown bibkey errors,
check the closest-match hint — usually a typo in the bibkey or a
missing bib_ledger entry that should be added first.

## pre_selection_manifest fails: span/excerpt/atom_id mismatch

**Symptom:** `python validators/pre_selection_manifest.py
pre_selection_manifest.yml` reports errors like:
- `selections[N].span.excerpt does not match span at offset [start:end]`
- `selections[N].span.sha256_of_span: expected X, actual Y for bytes [start:end]`
- `selections[N].atom_id: 'claim_foo' not found among claim records in sibling claim_graph.jsonl`
- `selections[N].cache_id: 'cache_x' not found in cache_manifest`

**Cause:** /agent-index Phase 2b committed to a span that doesn't match
the cached text, OR a span that supports an atom_id that doesn't exist
in claim_graph (synthesis bug), OR a cache_id outside the manifest.

**Fix:**
- Excerpt mismatch: re-pick the span by opening the cache `text_path`
  and copying the exact byte range. Recompute sha256 over those bytes.
- Atom_id missing from claim_graph: this means the atom wasn't created
  in evidence_ledger. Add the matching `supports[].claim_id` entry to
  evidence_ledger first, then rebuild claim_graph, then re-validate.
- Cache_id missing: add the entry to cache_manifest (cache the source
  first via `scripts/cache_source.py`).

The pre_selection_manifest contract is intentionally rigid — it's the
structural anti-hallucination guarantee. Errors here are almost always
"the manifest got written before the supporting artifacts caught up;
rebuild bottom-up."

## cache_source.py: --escalate-on-failure but Playwright not installed

**Symptom:** running `cache_source.py --escalate-on-failure <url>` against
a JS-rendered URL raises:
`RuntimeError: Playwright escalation requested but the 'playwright' package
is not installed.`

**Cause:** v2.2.1's Playwright escalation is gated behind the optional
`dev` extras; the bare `pip install -e .` install doesn't pull it in.

**Fix:** install Playwright + Chromium browser:
```bash
pip install -e ".[dev]"
playwright install chromium
```

Re-run the same command. cache_source.py will lazy-import playwright when
escalation triggers (urllib 403/429 or suspect content).

## cache_source.py escalated to Playwright but still got empty / garbage

**Symptom:** Playwright-rendered cache has fetch_method: playwright_rendered
but the extracted text is still empty, garbled, or login-gated.

**Causes:**
- Site requires authentication (login wall after page load)
- Captcha / Cloudflare turnstile check
- Geographic block (IP-based)
- The page's JS waits for user interaction (click, scroll) before rendering content
- The URL redirects to a different domain that's still JS-locked

**Fix:** None of these are auto-fixable. Options:
- Treat as `restricted: true` in the manifest entry; document the access
  barrier in evidence_ledger's `rights_status: restricted`.
- Manually paste extracted text into a local file and reference it as
  `extraction_method: manual_override` in evidence_ledger.
- Surface as a friction item in BURN_IN; consider v2.3 candidate to add
  authenticated session support to Playwright invocation.

## Test suite has 2 xfailed cases — is that normal?

**Symptom:** `make test` reports `2 xfailed`.

**Cause:** v1.2 marked the prompt-injection recreation_diff baseline tests
(`test_recreated_entry_counts_within_tolerance`,
`test_recreated_section_anchors_match`) as `xfail strict=True`. They reflect
v1.0 prompt-injection recreation drift, not v1.2 tooling defects.

**Fix:** none — this is the expected state. If they ever pass (e.g., after a
v1.x re-run of prompt-injection recreation under newer skills), `strict=True` will fail
the suite to flag the change.

## cache_manifest.yml uses absolute paths and breaks on a new machine (v2.3 #13)

**Symptom:** Cloning a project repo onto a new machine (or CI runner), running
`validators/cache_manifest.py` reports `file does not exist:
~/Claude/research_cache/blobs/sha256/...` even though the cache lives at the
same logical location on the new machine. Or the validator complains that
paths are `not portable across machines`.

**Cause:** Pre-v2.3 (`cache_source.py` ≤ v2.2.1) serialized absolute /
~-prefixed paths into `raw_path`/`text_path`/`metadata_path` despite
`cache_root` being declared at the top of the manifest. Closing #2 didn't
ship the writer-side fix; the reader (`_resolve()`) silently accepted both
formats so the bug stayed invisible until manifests crossed machines.

**Fix:** v2.3 ships `scripts/migrate_manifest_paths.py`. It reads
`cache_root` from the top of the manifest, strips the prefix from each
entry's path fields, and writes back relative paths.

```bash
python scripts/migrate_manifest_paths.py path/to/cache_manifest.yml
# or preview without writing:
python scripts/migrate_manifest_paths.py path/to/cache_manifest.yml --dry-run
```

Idempotent — re-running on an already-portable manifest is a no-op. Revisit
entries are skipped (they reference captures by ID, no paths to fix).

**Caveat:** the script uses `yaml.safe_dump` to re-serialize, so YAML
comments above `entries:` are NOT preserved. If your manifest has hand-edited
comments worth keeping, manually copy them back after running the script.

## docling install fails on macOS with 'cstdint' file not found (v2.3 / #11)

**Symptom:** `pip install docling` fails while building `docling-parse`
with `'cstdint' file not found` during the C++ compile step.

**Cause:** `docling>=2.30` requires `docling-parse>=5.0`, which currently
ships **source-only** on PyPI (no binary wheels for darwin x86_64
Python 3.12). pip falls back to building from source, which hits a known
libc++ header path issue in the docling-parse C++ codebase.

**Fix (already applied in pyproject.toml):** pin `docling>=2.0,<2.30`.
The 2.29.x line works with `docling-parse 4.7.2` which has binary wheels.
This is what `pip install -e ".[dev]"` will install by default.

If you need docling-parse 5.x specifically (e.g., for a newer Docling
feature), workarounds:
- **Conda:** `conda install -c conda-forge docling` (pulls a prebuilt wheel).
- **Python 3.11:** docling-parse 5.x has wheels for some 3.11 platforms.
- **Skip extraction:** pass `--no-extract-pdfs` and PDFs land at
  `extraction_status: raw_only` (pre-v2.3 behavior). You'll lose
  Attribute-First Phase 2a span-anchoring on those PDFs.

`scripts/cache_source.py` lazy-imports docling, so the toolkit still works
without it installed — equation-rich PDFs just land at `extraction_status:
ok_text_only` with a WARN suggesting installation.

## Cache_source.py WARN: extraction degraded (v2.3 / #11)

**Symptom:** Caching a PDF prints `WARN: <url> extraction degraded
(<status>) — <reason>` to stderr.

**Cause + fix by status:**

| Status | What it means | Fix |
|---|---|---|
| `ok_text_only` | math detected, Docling unavailable | install `docling` or accept text-only extraction |
| `degraded` | image-PDF or near-empty text | find a non-scanned source; or accept the degraded entry |
| `partial` | encrypted PDF | find a non-encrypted source; password-removal isn't automated |
| `failed` | both extractors errored | check the source URL fetched real PDF bytes (some servers return error HTML with `Content-Type: application/pdf`) |
| `stub` | HTML page is a JS shell | re-cache with `--escalate-on-failure` to render via Playwright |

The same WARN goes to `<cache_root>/extraction_log_<hostname>.jsonl` for
later analysis. `/research-gather --cache-pdfs` reads this log and prints
an aggregated summary at end-of-run.

## First PDF cache takes ~30 seconds (v2.3 / Docling)

**Symptom:** The first PDF cached after a fresh install hangs for
~30-60 seconds before completing.

**Cause:** Docling (Stage 2 of the PDF cascade) downloads ~600 MB of
models on first use. Subsequent runs hit the local cache and are fast.

**Fix:** Pre-pull the models proactively via `python
scripts/precache_docling_models.py`. For multi-machine workflows, point
`$DOCLING_CACHE_DIR` at a synced location (Dropbox / Drive) so each
machine doesn't pay the download separately.

## How to file a new issue you can't fix immediately

Add to `burn_in.yml` AND `BURN_IN_NOTES.md`:

```yaml
- id: <phase>-<stage>-<n>
  phase: <phase>
  stage: <stage>
  finding: 'one-line summary'
  severity: high|medium|low
  status: surfaced
```

Then in `BURN_IN_NOTES.md` add the prose elaboration under the appropriate
phase section. The structured entry makes it queryable; the prose makes it
explainable.

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
is the vol28 §2.1 anti-pattern that produced 1 misattribution out of 88
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

**Cause:** Subagent self-counting drift (vol28 §2.2). Subagents under context
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

## Test suite has 2 xfailed cases — is that normal?

**Symptom:** `make test` reports `2 xfailed`.

**Cause:** v1.2 marked the vol25 recreation_diff baseline tests
(`test_recreated_entry_counts_within_tolerance`,
`test_recreated_section_anchors_match`) as `xfail strict=True`. They reflect
v1.0 vol25 recreation drift, not v1.2 tooling defects.

**Fix:** none — this is the expected state. If they ever pass (e.g., after a
v1.x re-run of vol25 recreation under newer skills), `strict=True` will fail
the suite to flag the change.

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

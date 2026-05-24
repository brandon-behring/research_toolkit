# Template format — research_toolkit

Applies to `templates/*.yml`, `templates/*.template.yml`, and any
`templates/*.template.md` files. Templates serve as the canonical
schema reference + as starter content for skill workflows.

## File location + naming

- Path: `templates/<name>.template.{yml,md}` (or `templates/<name>.yml`
  for templates without the `.template` suffix — older convention).
- The `.template.{yml,md}` suffix signals "starter scaffold; copy +
  fill in" rather than "live data".

## Top-of-file comment block

Every template begins with a comment block (5-20 lines) describing:

1. **Purpose** — what the template is for.
2. **Maintainer** — which skill writes/reads it.
3. **Validator** — which validator enforces its schema.
4. **Required vs optional fields** — high-level note.

Example (`templates/synthesis_entry.template.yml`):

```yaml
# Synthesis entry template
# Maintained by /research-gather Phase 4b (synthesis pass; v2.3+) or by hand when
# consolidating multiple sources into a single citation-ready note. Validated by
# validators/synthesis_entry.py.
#
# A synthesis_entry is the complement to a per-source bib_ledger entry: instead
# of one URL → one entry, a synthesis_entry weaves multiple primary sources
# into a single claim with explicit source-attribution.
```

Format:
- `#` line comments (standard YAML), not `#:` or other variants.
- One topic per paragraph (separated by `#` blank-comment lines).
- Reference validator + skill in the first paragraph.

## Field ordering

Per-entry field order (applies to entries in `bib_ledger`, `evidence_ledger`,
`dataset_ledger`, `pre_selection_manifest`):

1. **Identifiers** first: `bibkey` / `evidence_id` / `selection_id` /
   `dataset_id`
2. **Primary data**: `primary_url`, `name` / `title`, `source_url`
3. **Classification**: `status`, `task_family`, `source_quality`,
   `source_type`
4. **v2 strict-live fields** (group together):
   - `retrieved_at`
   - `verified_at`
   - `verification_method`
   - `verified_fields`
   - `freshness_tier`
   - `stale_after_days`
5. **Ledger links**: `evidence_ids`, `cache_ids`, `claim_ids`
6. **Optional / extension fields**: free-form metadata last

Top-level (above `entries:`):

```yaml
schema_version: 2  # or 3 for v3-strict
topic: <topic-slug>
generated_at: YYYY-MM-DD
current_as_of: YYYY-MM-DD
freshness_policy: strict_live

entries:
  - ...
```

## Optional field handling

**Show optional fields with example values + inline comments**, NOT
commented-out:

```yaml
- bibkey: example2026foo
  primary_url: 'https://example.com/foo'
  title: Example Foo
  status: verified  # required
  retrieved_at: '2026-05-23'  # required
  verified_at: '2026-05-23'   # required when status=verified
  freshness_tier: stable      # one of: volatile, active, stable, historical
  evidence_ids: []            # (optional) — populate when evidence_ledger entries exist
  cache_ids:
    - cache_xxx               # (optional) — populate after caching
```

Show a 2nd entry (or commented-out 2nd entry block) demonstrating
the multi-entry shape:

```yaml
# Optional second entry (delete if single-entry):
#  - bibkey: another2026bar
#    primary_url: '...'
#    ...
```

## YAML conventions

Per `references/citation_rules.md`:

- **Quote values containing**: `:`, `#`, `[`, `{`, `}`, `&`, `*`,
  `?`, `|`, `>`, `!`, `%`, `@`, `` ` ``, or those starting with `-`.
- **Date format**: `'YYYY-MM-DD'` (string, ISO 8601).
- **Lists**: block style (newlines + `- `), not flow style (`[a, b]`)
  unless the list is short + scalar.
- **`sort_keys=False`** when emitting YAML programmatically (preserves
  field order).

## Comment placement

- **Section headers** (above a group of fields): use a blank-comment
  line above the header.

  ```yaml
  #
  # Verification fields (required for status=verified)
  retrieved_at: ...
  ```

- **Field-level comments** (explaining a specific field): inline
  after the value.

  ```yaml
  freshness_tier: stable  # one of: volatile, active, stable, historical
  ```

- **Block comments** (paragraph of explanation): above the relevant
  block; ≤80 chars per line; wrap as needed.

## Length

Templates aim for 40-120 lines. If your template exceeds 200 lines,
consider splitting into multiple template files or moving
schema details into a reference doc.

## Cross-references

- [`code-style.md`](code-style.md) — Python style for validators that
  consume templates.
- [`../../references/citation_rules.md`](../../references/citation_rules.md)
  — YAML quoting + bibkey naming.
- [`../../validators/`](../../validators/) — each template should have
  a matching validator (e.g., `templates/foo.template.yml` ↔
  `validators/foo.py`).

# Skill spec format — research_toolkit

Applies to `.claude/skills/*.md` files. Skills are discovered by
Claude Code (and similar agentic environments) via frontmatter +
filename; the body documents what they do and how.

## File location + naming

- Path: `.claude/skills/<skill-slug>.md`
- Slug: `kebab-case` matching the slash-command (e.g., `dataset-gather`
  → `/dataset-gather`).
- One file per skill; no `<name>-v2.md` variants.

## Frontmatter

YAML frontmatter (between `---` markers) at the top of the file.
Field order (constant across all skills):

```yaml
---
name: skill-slug
description: <single sentence; imperative; 15-35 words>
allowed-tools: Read, Write, Edit, Bash, WebSearch, WebFetch
paths: ['some/glob/**', 'other/**']  # optional
---
```

### `name`

Matches the filename slug (without `.md`).

### `description`

- Single sentence, 15-35 words, fits on one line.
- Starts with imperative verb or "Use when..." (verb-initial).
- Communicates **what** + **when/context** in one breath.

Good:

```yaml
description: Discover public datasets for a research topic and populate dataset_ledger.yml.
```

```yaml
description: Use when starting a new research effort on a topic with no existing dossier, or when the user asks to scope a topic before web searching.
```

Bad:

```yaml
description: This skill helps with things related to datasets.  # vague + descriptive voice
description: Dataset gatherer.  # not a sentence
```

### `allowed-tools`

Comma-separated string. NOT a YAML list, NOT a JSON array.

```yaml
allowed-tools: Read, Write, Edit, Bash, WebSearch, WebFetch
```

Include only the tools the skill actually uses (principle of least
privilege).

### `paths` (optional)

YAML list of glob patterns where the skill is relevant. Most skills
omit this; some use it for context-scoping.

**Footgun — omit on pipeline skills.** A skill with `paths` is
*auto-loaded only when a file matching one of the globs is in context*.
It will not appear in the model's available-skills list (and the model
cannot invoke it via the Skill tool) from a session opened anywhere the
globs don't match — so it reads as "not loaded / broken," even though
explicit `/slash` invocation by the user still works. Reserve `paths`
for skills that should *never* auto-fire outside a specific context.
**Do not put `paths` on pipeline skills that a runbook or orchestrator
invokes by name** (`research-gather`, `agent-index`, `citation-audit`,
`freshness-audit`, `research-kb-export`, `dossier-audit`,
`url-freshness-check` had it removed for exactly this reason — see
`BURN_IN_NOTES.md`, 2026-05-25).

## Section structure (H2 order)

Dominant pattern across the 12 existing skills:

```markdown
## Usage
## When to use
## Workflow
## Templates
## References
## Validation
## Output / handoff
```

Each section's purpose:

### `## Usage`

Command + example. Show the actual slash-command invocation + any
required arguments.

```markdown
## Usage

```bash
/dataset-gather <topic-slug>
```

(Bash code block; no language tag also acceptable for usage examples.)

### `## When to use`

Bullet list of triggering signals. Pair with "When NOT to use" inline
if there's a confusable alternative skill.

```markdown
## When to use

- The user asks to "find datasets for X" or "what data is out there for Y"
- Starting a new research topic where the dataset landscape is unknown
- NOT for: refining an existing dataset_ledger (use /dataset-index instead)
```

### `## Workflow`

Multi-phase breakdown. Each phase is an H3 sub-heading. Procedure-driven,
imperative voice ("Read X", "Run Y") — not descriptive ("This phase
reads X").

```markdown
## Workflow

### Phase 1 — Discovery

Read `~/Claude/research_toolkit/templates/dataset_ledger.template.yml`.
For each candidate source, query HuggingFace Hub + ...

### Phase 2 — Curation

...
```

### `## Templates`

List of template files the skill reads/writes. Markdown links with
`~/Claude/research_toolkit/...` home-relative paths.

```markdown
## Templates

- [`dataset_ledger.template.yml`](~/Claude/research_toolkit/templates/dataset_ledger.template.yml)
```

### `## References`

List of reference docs the skill should consult before/during execution.

```markdown
## References

- [`citation_rules.md`](~/Claude/research_toolkit/references/citation_rules.md)
  — URL canonical forms + bibkey convention.
```

### `## Validation`

Code block running the relevant validator. This is the mandatory
"no silent partial success" gate per `README.md`.

```markdown
## Validation

```bash
python ~/Claude/research_toolkit/validators/dataset_ledger.py <output_path>
```
```

If validation fails, the skill MUST report failure (don't proceed
silently).

### `## Output / handoff`

What artifacts the skill produces + which downstream skills consume them.

```markdown
## Output / handoff

- Writes: `<project>/dataset_ledger.yml`
- Consumed by: `/dataset-index` (renders to agent-index folder)
```

## Voice + tone

- **Imperative**, not descriptive. "Read X", "Write Y", not "This
  skill reads X."
- **Terse**, not verbose. Bullet-heavy in early sections; prose in
  mid-workflow detail.
- **Procedure-driven**. "For each entry, render as ..." not "We will
  iterate over entries and produce ..."

## "HARD REQUIREMENTS" / "HARD RULES" callouts

Skills with high failure modes (gather/audit/index) use bold-faced
HARD callouts:

```markdown
**HARD RULE**: Never write an entry without a verified `primary_url`.
```

Use sparingly — only for rules that, if violated, produce
silent data corruption or unsafe output.

## Length

- Min: ~80 lines (thin wrappers like `dataset-research.md`).
- Median: ~150 lines.
- Max: ~350 lines (high-complexity skills like `agent-index.md`,
  `research-gather.md`).

If your skill spec exceeds 400 lines, consider splitting (e.g., move
detailed workflow rules into a reference doc + link).

## Code blocks

Language tags: `bash`, `yaml`, `python`, `markdown`. Or untagged for
generic CLI usage.

```markdown
```yaml
field: value
```

```bash
python validators/foo.py
```

```
/dataset-gather <topic>
```
```

Backticks around field names, paths, enum values:

```markdown
Field `claim_family` accepts values `primary`, `secondary`, `tertiary`.
File at `~/Claude/research_toolkit/templates/foo.yml`.
```

## Cross-references

- [`../../README.md`](../../README.md) — TDD discipline (the `## Validation`
  section is the mandatory close-gate).
- [`code-style.md`](code-style.md) — Python code conventions
  (relevant for skills that write code).
- [`templates.md`](templates.md) — Template format conventions
  (relevant when a skill produces a template-shaped output).

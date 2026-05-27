---
name: topic-discovery
description: Mine a knowledge corpus (default: the interview-prep LaTeX series) into a prioritized, deduplicated topic_backlog.yml of deepen and adjacent research topics, each handing off to /research-plan.
allowed-tools: Read, Bash, Glob, Grep, Write, Edit
---

# /topic-discovery — Mine a corpus into a prioritized topic backlog

## Usage

```
/topic-discovery [--corpus <dir>] [--output <path>] [--limit <N>]
```

**Examples:**
```
/topic-discovery
/topic-discovery --corpus ~/interview_prep_series --output ~/Claude/topic_backlog.yml
/topic-discovery --limit 20
```

**Default `--corpus`**: `~/interview_prep_series`.
**Default `--output`**: `~/Claude/topic_backlog.yml` (append-only across runs).
**`--limit`**: cap net-new entries this run (default: no cap).

## When to use

- When you want to know "what should I research next?" grounded in a corpus you
  already maintain — not a blank-page brainstorm.
- To refresh a living backlog: re-run periodically; it dedups topics already
  researched and appends only net-new candidates.
- NOT for researching a topic (that's `/research-plan` → `/research-gather`).
- NOT for discovering datasets or papers on the web (corpus-internal only — no
  WebSearch/WebFetch).

**Upstream:** a knowledge corpus (volumes + learning objectives + reading lists).
**Downstream:** `/research-plan "<title>"` per selected backlog entry.

## Workflow

### Phase 1 — load reference + corpus (HARD REQUIREMENT)

Read `~/Claude/research_toolkit/references/topic_discovery_protocol.md` BEFORE
mining — it defines the deepen/adjacent signals, dedup sources, and scoring
rubric. Read `~/Claude/research_toolkit/templates/topic_backlog.template.yml`
for the schema and `~/Claude/research_toolkit/validators/topic_backlog.py` for
what's enforced.

Load the corpus via the prep repo's own loaders (Step 0 of the protocol):
`scripts/lib/volume_scope.py::get_all_volumes()` and
`scripts/lib/los_utils.py::extract_volume_los(repo_root, vol_dir)`, run with
Bash from `--corpus`. Use the documented direct-parse fallback only if
`scripts/lib` is absent.

**HARD RULE:** emit only `topic_id` / `source_volume` / `source_los` values the
loader actually returned. Never invent corpus identifiers.

### Phase 2 — mine DEEPEN candidates

Per protocol Step 1, in priority order: `reading_list.yml` `to_acquire` markers
→ high-Bloom LOS clusters (whitelist: analyze, evaluate, design, synthesize,
formulate, architect, create, develop, diagnose, construct) grouped by
`chapter_num` → frontier `\section{}` titles. **One topic per chapter cluster,
never one per LOS.** Each deepen entry cites `source_volume`.

### Phase 3 — mine ADJACENT candidates

Per protocol Step 2: scaffold/placeholder volumes (few real LOS), cross-track
intersections from `shared/company-tags.yml` `domains:` co-occurrence, and prose
"Future / Open problems" asides. Omit `source_volume`; set `track: cross`.

**HARD RULE:** a run must surface ≥1 of EACH kind. The validator's `--strict`
both-kinds check (≥8 entries) rejects a one-sided mine — confirm both before
writing.

### Phase 4 — dedup against prior research (HARD REQUIREMENT — silent-failure mode)

Per protocol Step 3, build the "already-covered" set from: this backlog's own
`status ∈ {researched, planned, dropped}` entries; `~/Claude/research_*/` dir
slugs + their `bib_ledger.yml` `topic:` field; and
`~/Claude/research-kb/inbox/research_toolkit/*.jsonl` stems. Drop matches and log
each drop + reason. **`/topic-discovery` is append-only — never rewrite or
re-emit an existing entry.**

### Phase 5 — score + assign priority/rationale

Apply the protocol Step 4 additive rubric (strong signal +2, frontier density
+1, AI-safety/causal interest bias +2, transferability +1; ≥5→P0, 3-4→P1,
≤2→P2). Write a one-line `rationale` naming the top contributing signal(s) and
≥3 `claim_family_seeds` per entry.

### Phase 6 — write/append topic_backlog.yml

Write to `--output`. If the file exists, APPEND net-new entries only
(deduplicate by `topic_id`; fail with a clear error on a duplicate `topic_id`
that isn't already present). Preserve existing entries verbatim.

### Phase 7 — validate (mid-run checkpoint + final, HARD REQUIREMENT)

Mid-run: after Phase 3, run the validator `--strict` against a scratch write to
confirm BOTH kinds are present before committing the full backlog — fail fast on
a one-sided mine.

Final:

```bash
python ~/Claude/research_toolkit/validators/topic_backlog.py <output>
```

Non-zero exit → report the failure with stderr; do NOT claim success.

### Count-assertion (HARD REQUIREMENT for the final report)

Your final report's topic count MUST equal the file count. Compute before
reporting:

```bash
grep -c "^- topic_id:" <output>
```

If the narrative count differs, recount before reporting.

## Templates

- [`topic_backlog.template.yml`](~/Claude/research_toolkit/templates/topic_backlog.template.yml) — schema spec.

## References

- [`topic_discovery_protocol.md`](~/Claude/research_toolkit/references/topic_discovery_protocol.md) — HARD REQUIREMENT — load before mining.

## Validation

```bash
python ~/Claude/research_toolkit/validators/topic_backlog.py <output>
```

Enforces required fields + enums (`kind`, `priority`, `status`), unique kebab
`topic_id`, ≥3 `claim_family_seeds`, `source_volume` present for `deepen`
entries, valid `seed_sources` URLs, and (≥8 entries, `--strict`) the both-kinds
+ priority-spread shape checks.

## Output / handoff

**Produces:** `<output>` (default `~/Claude/topic_backlog.yml`) — a living,
append-only backlog of prioritized research topics.

**Consumed by:** `/research-plan "<title>"` per selected entry. After a topic is
researched, `scripts/backlog_stamp.py <backlog> <topic_id> --status researched
--dossier <path>` flips its lifecycle fields so the next run dedups it.

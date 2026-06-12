# RS1 — dossiers repo + contract migration (2026-06-12)

**Slice owner**: research_toolkit ([#39](https://github.com/brandon-behring/research_toolkit/issues/39)).
**Decided contracts**: R4 + R1a + R12 in hub
`lever_of_archimedes/docs/plans/active/2026-06-research-side-design-review/decisions.yaml`.
**Status**: in execution 2026-06-12.

What moves: every `~/Claude/research_*` dossier dir except `research_toolkit` and `research_cache`
(66 dirs, incl. `research_toolkit_design`) + 5 catalogue files (`research_INDEX.md`,
`research_BACKLOG.md`, `research_TOPIC_BACKLOG.md`, `research_graph.json`, `research_graph.html`) →
private repo `~/Claude/research-dossiers/`, verbatim names, blanket transition symlinks at `~/Claude`
root (RS7 removes). Envelope contract flips to in-dossier (`synthesis_export.jsonl`);
`research-kb/inbox/` dies.

## Decisions made (16 user-answered forks, this session)

1. **Envelope creation = byte-copy** from inbox (preserves `exported_at` + bytes; re-ingest provably
   a no-op). Rejected: regeneration (mutates provenance for zero content gain).
2. **Envelope filename = `synthesis_export.jsonl`** (consumer-true; consumer is synthesis-kb).
3. **ml_security envelopes live in their producer dossiers** inside `prompt-injection-portfolio`
   (R1a-faithful); `ingest_dossiers.py` gains a 5-entry slug→dir override map. Rejected: stub folders
   in research-dossiers (a mini-inbox by another name).
4. **Inbox tarred to Archive before anything** (`research_kb_inbox_final_2026-06-12.tar.gz`) — the P0
   snapshot does not cover the inbox and ~62 stale envelopes are otherwise lost.
5. **Functional macOS `cache_root:` values normalized post-import** (separate commit; audit found 6,
   not the census's 2 — principle decided, count corrected in execution). Prose/artifact macOS
   mentions stay verbatim.
6. **Symlinks = blanket** (all 71 moved entries) — R12's falsifier is an uncovered reference class.
7. **`bundle_research_corpus.py` = minimal repoint only**; retirement deferred (R7 git transport
   supersedes its dossier scope, but cache shipping has no replacement until R11/RS7).
8. **Verification = FULL 40-slug re-ingest** (exceeds the issue's 1-dossier bar; byte-identical
   envelopes + idempotent upserts make it cheap and it proves the whole slug→dir map).
9. **Census delta (66 dirs vs issue's "67") diff-classified, continue**: INDEX is stale at 51
   (2026-05-27/28 claude-books wave never indexed); all 66 are dossier-shaped. No unexplained entries.
10. **Inbox `rm -rf` only AFTER the verification gate passes** (destructive last).
11. **prompt-injection-portfolio: envelope commit on its checked-out session branch**
    (`session/2026-05-26-adoption-and-research-ops`); branch state untouched.
12. **Ingest CLI: `--inbox` → `--root` (env `DOSSIER_ROOT`), no back-compat alias** — stale
    invocations fail loudly at argparse.
13. **Fail-loud tightening in-slice**: ingest exits non-zero if any requested slug was skipped
    (today: silent `SKIP …; exit 0`).
14. **`scripts/research_kb_export.py` → `scripts/synthesis_export.py`, no shim** (one caller:
    `bundle_research_corpus.py`); validator module `validators/research_kb_export.py` keeps its name
    (schema unchanged, export_schema_version 2).
15. **`research_graph.html` moves too** — the one small scope addition beyond issue #39 (rendered
    twin of `research_graph.json`; both in bundle CATALOGUE).
16. **Future dossiers are born inside research-dossiers** — toolkit skill docs swept so the
    documented authoring default is `~/Claude/research-dossiers/research_<topic>`; external projects
    (pi-portfolio style) keep authoring in their own repos per R1a.

## Alternatives considered and rejected

- Rename-clean migration — rejected by R12 (slug churn in DB `source_project`, envelopes, INDEX).
- Single staging/`envelopes/` dir in the new repo — recreates the inbox R1a kills.
- Deprecation shims/aliases for renamed surfaces — single-user fleet; fail-loud beats theater.

## Verification gate

Pre-move per-domain SQL snapshot (`/var/tmp/rs1_premove_counts.json`; 40 dossiers · claims
406/201/240/456 · concepts 249/156/169/173) must match exactly after a full 40-slug re-ingest from
the new paths. Plus: scaffold round-trip into the repo, live-grep zero `research-kb/inbox`, both test
suites green. Recovery paths: P0 snapshot (2026-06-11) + inbox tar (2026-06-12).

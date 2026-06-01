# Agent discipline

Operational discipline for skills that dispatch research-gathering agents. Sourced from external-dogfood lessons (see `BURN_IN_NOTES.md` § External dogfood — claude-books research sprint, items #1 and #4).

## Per-agent tool-call budget

**Cap each dispatched research agent at ~25-30 tool calls.** A typical accepted source costs:
- 1 WebSearch (discovery)
- 1 WebFetch (read the canonical URL)
- 1 `cache_source.py` invocation (v2.2+ strict-live only; ~3-5 sec each)
- 1 Write (per-source note)

= ~3-4 tool calls per source. A 12-source sub-area ≈ 50 calls — comfortably above the cap and at real risk of a socket-layer crash during the run.

**For high-source-count sub-areas**: dispatch two narrower-scoped agents rather than one wide one.

Pattern:
- ❌ One agent for "Anthropic Academy courses" with 10 sub-tasks (10 fetches + 10 writes ≈ 30+ calls; observed to crash at 47 calls in claude-books dogfood)
- ✅ Two agents: "Academy: Claude Code track" (5 courses) + "Academy: API/MCP track" (5 courses). Each ≈ 15 calls. Resilient to a partial failure — the other agent's work survives.

Pattern (synthesis variant):
- ❌ One agent that fetches AND synthesizes 8 sources
- ✅ One agent fetches 5 sources; a second synthesizes. The synthesizer doesn't need WebFetch; it reads the cached output of the first.

## Mid-phase validator checkpoint

**After every 5–6 sources written, run the relevant validator on the partial output.** Failing fast catches systematic drift before it propagates.

For `/research-gather`:
```bash
python ~/Claude/research_toolkit/validators/bib_ledger.py <output_dir>/bib_ledger.yml
```

For `/dossier-build`:
```bash
python ~/Claude/research_toolkit/validators/dossier.py <output_dir>
```

For ad-hoc per-source markdown caches (non-strict-live applications):
- Run whatever linter the project ships (e.g., the `.lint.py` pattern from `claude-books/docs/research/`).
- Or grep for common drift signals — `cert_domains: \[.*D[1-5]` for D-prefix bugs, `^source_title: [^"].*: ` for unquoted colons.

## Recovery from agent crash mid-sub-area

If an agent crashes (socket layer; OOM; timeout) after writing some notes:

1. **Don't restart from zero.** Written notes are durable; only the topic README and any partial in-flight note are at risk.
2. **Inventory what was written**: `ls <output_dir>/<topic>/`. The slug naming convention makes it obvious which sources are done.
3. **Recover the missed work**:
   - For ≤2 missed notes: write them inline from the parent (use WebFetch directly, skip the dispatch overhead).
   - For 3+ missed notes: dispatch a smaller recovery agent narrowly scoped to the remaining sources.
4. **Write the topic README inline** (often the crashed agent's last-step task). The README is meta-info and doesn't need a fresh fetch.
5. **Update task tracking**: mark the original task as completed (partial recovery) AND note the crash for `BURN_IN_NOTES.md` if it surfaces a real toolkit weakness.

## Incremental write — the cache is the checkpoint

**Write each result to its on-disk artifact the moment it is confirmed, never in one dump at the end.** A long gather or synthesis can drop on a socket close after hours of work; anything held only in memory is lost. A `/research-gather` run lost ~3.6h of sources this way — the sources-JSON it was building in memory was empty when the agent dropped.

The content-addressed cache (`scripts/cache_source.py`) is the durable checkpoint that makes this survivable: every fetched blob is already on disk under `<cache_root>/metadata/sha256/<sha>.json` (recording its `topic`), `text/sha256/<sha>.txt`, and `blobs/sha256/<sha>` BEFORE the agent would have written the sources list. So a gather must append each source to the sources-JSON immediately after it is cached + anchored, not accumulate-then-dump — but even when that discipline slips, the cache lets you reconstruct.

### Resume from the cache (canonical recovery path)

When a gather drops, reconstruct from the cache instead of refetching:

```bash
python ~/Claude/research_toolkit/scripts/resume_gather_from_cache.py <topic_slug> \
  [--existing <partial_sources.json>]
```

It scans the cache for the topic, rebuilds a sources-JSON skeleton, fills cache-known fields (`sha`, `primary_url`, `published_online`), marks judgment fields as `TODO`/empty, and flags low-quality (tiny/stub) blobs to re-fetch. The merge is dedup-safe (by `sha` and `primary_url`) and never overwrites a human-completed record, so re-running it is idempotent. Complete the placeholder fields from each blob's cached text, then continue with only the sub-areas still missing.

This replaces the manual blob-by-blob reconstruction the recovery steps above otherwise require.

## Background dispatch for time-isolated work

If a research sub-area's outputs aren't needed for the immediate next step, dispatch the agent with `run_in_background: true`. The parent agent can:

- Do other work (parallel topics; doc edits; etc.)
- Get notified when the background agent completes
- Integrate the result later

**Anti-pattern**: dispatching the next wave of agents in parallel WITHOUT background mode when you can't usefully act on the results until they all return. Foreground multi-dispatch is fine for waves where you wait for all and synthesize; background is right when the result feeds a later phase and you have non-overlapping work in the meantime.

## Cross-references

- `references/strict_live_v2.md` — what evidence/cache/freshness artifacts the dispatched agent must produce per strict-live contract.
- `references/citation_rules.md` § Source-tier worked examples — the agent's tier-assignment cheat sheet.
- `BURN_IN_NOTES.md` § External dogfood — claude-books research sprint — original case study that motivated this reference.

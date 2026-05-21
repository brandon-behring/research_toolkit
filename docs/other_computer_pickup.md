# Other-computer pickup recipe

Sync this work to a second machine. The repo carries everything except
the personal scratch dossiers and cached source blobs — those transfer
via a separate tarball uploaded to Google Drive.

## Prerequisites

- Python 3.11+
- git with an SSH key configured for `github.com:brandon-behring`
- Optional: Playwright (only needed for v2.2.1's JS-rendered escalation
  path; `pip install -e ".[dev]" && playwright install chromium`)

## Step 1 — Clone the toolkit and wire skills

```bash
git clone git@github.com:brandon-behring/research_toolkit.git ~/Claude/research_toolkit
cd ~/Claude/research_toolkit
make install       # pip install -e ".[dev]"
make symlinks      # symlinks all skill bodies into ~/.claude/skills/
```

Verify Claude Code sees the skills:

```bash
ls ~/.claude/skills/research-*.md ~/.claude/skills/dossier-*.md ~/.claude/skills/agent-*.md
```

## Step 2 — Restore the dossier tarball

Download `research_dossiers_<DATE>.tar.gz` from Google Drive (uploaded
by the originating machine). Extract into `~/Claude/`:

```bash
cd ~/Claude
tar -xzf ~/Downloads/research_dossiers_<DATE>.tar.gz
```

This restores:
- `~/Claude/research_*/` — every personal research project (dossiers,
  caches, manifests). The 4 from the v2.2 dogfood arc are
  `research_toolkit_design`, `research_eval_drift`,
  `research_causal_inference_ml`, `research_agent_capabilities_scaling`.
- `~/Claude/research_cache/` — global content-addressed cache. Some
  `research_toolkit_design` entries reference this via absolute paths
  (legacy from before per-project cache dirs); they'd break without it.
- `~/Claude/research-kb/inbox/` — structurally-validated jsonl exports
  staged for future research-kb ingestion.

## Step 3 — Verify everything transferred cleanly

```bash
cd ~/Claude/research_toolkit
make v2-smoke      # all validators green; 224+ tests pass implicitly
make test          # full test suite
```

Then verify a dossier end-to-end (catches absolute-path breakage and
substring-anchor drift):

```bash
TODAY=$(date +%Y-%m-%d)
python scripts/verify_citations.py ~/Claude/research_toolkit_design --today $TODAY
# Expect: 100% verbatim_match substring pass on all 49 supports.
# If you see "file not found" errors, the global cache didn't extract
# correctly — re-check Step 2.
```

## What's NOT in the sync

- **Plan files** at `~/.claude/plans/*.md` — ephemeral session state.
- **Auto-memory** at `~/.claude/projects/*/memory/` — session-local.
- **Claude Code conversation history** — local to the originating
  machine. The other computer starts fresh.

To bring forward conversation context, the most reliable thing is the
committed `BURN_IN_NOTES.md` + `references/v2_2_design_backlog.md` —
both have full narrative coverage of the recent design + dogfood arcs.
Start the next session by reading those.

## Reverse sync (other computer → originating)

After the other computer does work, mirror this recipe in reverse:

```bash
# On the other computer
cd ~/Claude/research_toolkit
git push                                          # send code changes back
cd ~/Claude
tar -czf ~/Downloads/research_dossiers_<DATE>.tar.gz \
  research_*/ --exclude='research_toolkit/' \
  research_cache/ research-kb/inbox/             # send dossier changes back
```

Then upload the tarball to Google Drive and rsync/extract on the
originating machine.

# research_toolkit

Claude Code skill collection for systematic research workflows: scope a topic → gather primary sources → build a dossier → synthesize an agent-ready indexed folder → audit it.

> **Status:** Phase 4 complete. Phase 3.5 (vol25 recreation) and Phase 5 (first-use dogfood) are next; toolkit will be tagged v1.0 after Phase 5.

## The 6 skills

| Skill | Stage | Input | Output | Validator |
|---|---|---|---|---|
| `/research-plan` | 0 | Topic free-text | `research_plan.md` | `validators/research_plan.py` |
| `/research-gather` | 1 | `research_plan.md` | `bib_ledger.yml` (+ optional `papers/`) | `validators/bib_ledger.py` |
| `/dossier-build` | 2 | `bib_ledger.yml` | N topic dossier files | `validators/dossier.py` |
| `/agent-index` | 3 | Dossier files | Indexed folder + AGENT-INDEX README | `validators/agent_index.py` |
| `/dossier-audit` | 4 | Indexed folder + scope focus | One round of DROP/CORRECT/FLAG fixes + audit-trail note | `validators/audit_trail.py` |
| `/url-freshness-check` | utility | Any markdown folder | URL HEAD-check report | `validators/url_check_report.py` |

The handoff contract is enforced by validators — skill N's output validator IS skill N+1's input validator. If schemas drift, downstream skills fail at the validator step before they can produce broken output.

See `references/workflow_overview.md` for the full stage diagram.

## Repository layout

```
~/Claude/research_toolkit/
├── README.md                                 # this file
├── Makefile                                  # `make install` / `make test`
├── pyproject.toml                            # PyYAML + pytest
├── .claude/skills/                           # 6 skill bodies (source of truth)
├── templates/                                # 6 schema/structure templates loaded by skills
├── references/                               # 6 design + protocol docs (workflow_overview,
│                                             # scope_planning, dual_audience_design,
│                                             # citation_rules, audit_protocol, url_check_protocol)
├── validators/                               # 6 schema validators (one per artifact type)
└── tests/
    ├── conftest.py
    ├── test_validators.py                    # positive + negative case for each validator
    ├── test_skill_outputs.py                 # vol25 fixture sanity + known violation assertion
    ├── test_recreation_diff.py               # real/ vs recreated/ schema-equivalence (Phase 3.5)
    └── fixtures/
        ├── mini_topic_timeseries_anomaly/    # 4-paper "new use case" smoke test
        └── vol25_snapshot/
            ├── real/                         # frozen vol25 dossier + synthesis
            └── recreated/                    # populated by Phase 3.5 (currently empty)
```

## Install

```bash
git clone <remote> ~/Claude/research_toolkit
cd ~/Claude/research_toolkit
make install              # creates .venv, installs PyYAML + pytest
make test                 # 16 pass + 4 skip on a clean checkout

# Make skills discoverable from any project's CWD:
mkdir -p ~/.claude/skills
for skill in research-plan research-gather dossier-build agent-index dossier-audit url-freshness-check; do
  ln -s ~/Claude/research_toolkit/.claude/skills/$skill.md ~/.claude/skills/$skill.md
done
```

After symlinking, the 6 skills are invokable from any project's Claude Code session without per-repo setup.

## Maintenance contract

Skill bodies hard-code paths to `~/Claude/research_toolkit/templates/...` and `~/Claude/research_toolkit/references/...`. If you move the toolkit, update those paths in every skill body — the symlinks keep relative-path expectations in working order, but absolute paths are baked into the skill bodies for reliability across consumer-project CWDs.

When updating a skill / template / reference, edit the source-of-truth file under `~/Claude/research_toolkit/`. The symlinks in `~/.claude/skills/` track changes automatically; no need to re-link.

## TDD discipline

Each skill has a mandatory `## Validation` final step that runs `python ~/Claude/research_toolkit/validators/<name>.py <output_path>`. If validation fails, the skill reports failure with stderr — there is no path to silent partial success.

**Validator scope** (per design choice in the implementation plan): schema-only — fields, types, enums, counts, structural shape. Fast, deterministic, no network IO.
**Validator non-scope** (intentional): URL liveness (that's `/url-freshness-check`), content faithfulness (that's `/dossier-audit`), hallucination patterns.

**Two fixture types** under `tests/fixtures/`:

- `mini_topic_timeseries_anomaly/` — hand-curated 4-paper fixture covering NAB, MSL/SMAP, TODS, and the Schmidl 2022 PVLDB survey. Demonstrates the canonical 5-bullet schema on a domain unrelated to prompt-injection. Lives forever as the "new use case" smoke test.
- `vol25_snapshot/` — both `real/` (frozen at toolkit-creation time, copy of the prompt-injection vol25 dossier + synthesis) and `recreated/` (populated by Phase 3.5 when the new skills are run on the same domain). `test_recreation_diff.py` reports schema-equivalence + diff between the two.

**Known violations** in the vol25 snapshot are documented in `tests/fixtures/vol25_snapshot/README.md`. The dossier and agent_index validators handle vol25's heterogeneous content types (paper synthesis vs leaderboard vs vendor profile vs standards profile) via per-content-type schema detection.

## Roadmap

- **Phase 3.5** (next): run the new skills on the prompt-injection domain to populate `tests/fixtures/vol25_snapshot/recreated/`. `test_recreation_diff.py` will report how faithfully the skills reproduce the human-curated vol25 synthesis.
- **Phase 5** (gates v1.0): user picks one real new research topic; runs the full pipeline end-to-end; tweaks any skill prompts that surface friction; mini and vol25 fixture validators must still pass after the tweaks. Document tweaks in `BURN_IN_NOTES.md` (gitignored locally; committed when ready).

## License + remote

Local git repo with a private GitHub remote. Personal toolkit; not designed for outside contribution at this time.

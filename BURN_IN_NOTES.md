# Burn-In Notes — research_toolkit dogfood log

This file is the load-bearing artifact of Phases 3.5 + 5. Every skill-prompt tweak, validator miss, template gap, or pipeline friction surfaced during dogfood runs gets recorded here with before/after context. If this file is empty after a real dogfood pass, that's suspicious — re-examine.

**Status legend:**
- `surfaced` — friction observed; not yet acted on
- `applied` — tweak applied to skill / template / reference
- `deferred` — friction acknowledged but not material enough to fix in this version
- `wontfix` — out of v1.x scope; goes in next-design-cycle backlog

---

## Phase 3.5: vol25 full-mode recreation

**Date started:** 2026-05-07
**Output:** `tests/fixtures/vol25_snapshot/recreated/`
**Comparison:** `tests/fixtures/vol25_snapshot/real/` (137 entries, 7 dossier files, 9 indexed files)

### Stage 1: /research-plan (reverse-engineered)

(populated as observations surface)

### Stage 2: /research-gather

**1. Crescendo first-author misattribution (status: corrected, applied during run)**
- The reverse-engineered research_plan.md listed `mehrotra2024crescendo` as a known landmark. Crescendo's lead author is Russinovich (Microsoft); Mehrotra is the lead author of TAP (Tree of Attacks, arXiv:2312.02119). The subagent caught this during WebFetch verification and registered both correctly: `russinovich2024crescendo` (arXiv:2404.01833) and `mehrotra2023tap` (arXiv:2312.02119).
- **Why it matters:** When `/research-plan` reverse-engineers a plan from existing dossier prose, author attributions in the plan can carry forward errors. The verification step in `/research-gather` (WebFetch on landmark papers) caught this. The skill chain self-corrected — exactly the design intent.
- **Action:** None required for v1.0. Document this as a positive case for the WebFetch-verify-landmarks step.

**2. bib_ledger schema is too minimal for /dossier-build (status: surfaced — design gap)**
- bib_ledger entries store only `bibkey | primary_url | title | status | claim_family`. The dossier table template requires `Title | Authors (year) | Venue | arXiv/DOI | GitHub | <description> | <contribution>`. The dossier-build skill has no specified mechanism to fill in `Authors (year)`, `Venue`, `description`, or `contribution`.
- **Why it matters:** Either `/research-gather` must populate richer fields, OR `/dossier-build` must WebFetch each entry to get them, OR the schema expands. Currently the skill body is silent on this; the agent rendering Stage 3 has to choose.
- **Action for v1.0:** Document the gap; let Stage 3 use bibkey-heuristic for Authors (e.g., `perez2022ignore` → "Perez et al. (2022)"). For v1.1 design cycle, decide between the three resolutions above.

**3. Per-claim_family distribution is highly skewed (status: noted, no action)**
- Recreated bib_ledger has 25 entries in `red_teaming_tools` and 16 in `evaluation`/`attack_direct_jailbreak`, but only 1 each in `defense_smoothing` and `other`. The real ledger's distribution differs (e.g., 44 entries in `other`, suggesting heterogeneous misc content the recreation missed).
- **Why it matters:** Helps interpret the `test_recreation_diff.py` output later — large per-family deltas don't necessarily indicate skill failure; they may reflect different categorization choices.

### Stage 3: /dossier-build

**1. Validator's column-5 prefix list ("GitHub", "HF", "Code", "Repo") fights natural rendering for vendor-product / standards-PDF tables (status: surfaced — borderline)**
- The validator requires column 5 of any paper table (col 2 = "Authors (year)") to start with "GitHub" / "HF" / "Code" / "Repo". For vendor pages and standards PDFs the natural column header would be something like "URL" or "Doc URL". Workaround: use the same 7-column schema across the whole dossier and put `—` in the GitHub cell for non-paper rows. This works but the dossier ends up looking heterogeneous across rows of the same table.
- **Why it matters:** If a dossier file is mostly vendor pages with a couple of arXiv preprints mixed in, the validator forces the file into the paper-schema even though the editorial intent might be a non-paper schema (col 2 ≠ "Authors (year)") with looser checks.
- **Action:** Document the workaround. Consider widening the prefix list (e.g., "URL", "Source") in v1.1 or recommending splitting heterogeneous content into separate files.

**2. bibkey-heuristic Authors rendering breaks down on multi-word surnames and corporate authors (status: surfaced — design gap)**
- Per BURN_IN Stage 2 #2, Authors are derived from bibkey. Heuristic works for `perez2022ignore` → "Perez et al. (2022)", but breaks for: corporate authors (`anthropic2024manyshotpdf` becomes "Anthropic" not a person; `nvidia2024garak` becomes "NVIDIA"); ambiguous slugs (`bel-air2025` — is "Bel-Air" a hyphenated surname or a place?). Manual override list would help.
- **Why it matters:** The Authors cell is validator-required to be non-empty, so heuristic failures get masked as plausible-but-wrong text rather than caught.
- **Action:** Document gap; consider a small bibkey → display-author override map in `/research-gather` output for v1.1.

**3. Cross-listing the same entry across files (e.g., GCG appears as both a paper in `01_attacks_direct` and a tool repo in `06_tools_vendors`) doesn't have a clear mechanism in the skill body (status: surfaced — friction)**
- The bib_ledger has 147 entries; at least 6 entries are conceptually both "the paper" and "the codebase" (GCG, NeMo Guardrails, ArtPrompt, JailbreakBench, BIPIA, llm-attacks repo). The skill body says one entry per dossier row but doesn't say what to do when the same source legitimately belongs in two topic files. I rendered each in the most-natural primary location and cross-referenced verbally.
- **Why it matters:** A future audit pass might flag the cross-listings as duplicates without realizing they're intentional.
- **Action:** Document this case in the skill body or add a "see also" cross-reference column. v1.1 design item.

**4. Dossier-table 7-column schema gets visually crowded for non-paper entries (status: minor friction)**
- Standards PDFs and vendor product pages have authorship like "OWASP", "NIST", "Anthropic", and the venue is just the source-org's site. The "One-line description" and "Key contribution" columns end up saying very similar things (e.g., "OWASP's prompt-injection entry" / "Authoritative OWASP entry"). Could collapse to fewer columns for non-paper-heavy files.
- **Action:** Note in template that the last two columns can be merged for vendor/standards-heavy tables; current schema works but is editorially redundant.

### Stage 4: /agent-index

**5. 5-bullet ordering enforcement only triggers when "Result" bullet is present — vendor entries skip enforcement (status: surfaced — design choice, working as intended)**
- The validator only enforces canonical Source/Code/Mechanism/Result/Status order when a `**Result:**` bullet is present. Vendor entries use the variant schema (Source/Status/Product line/Mechanism/Integration) which lacks Result, so the variant entries don't get ordering enforcement at all.
- **Why it matters:** This is intentional per the validator design but creates an editorial inconsistency — vendor entries can have arbitrary bullet orderings while paper-synthesis entries cannot. A future LLM-agent reader parsing the synthesis must branch on whether `Result` is present to know which schema to expect.
- **Action:** Document this in `5_bullet_entry.template.md` more loudly — the template mentions the variant but the schema-divergence implication for parser logic is implicit.

**6. Lookup recipes pattern (`**"What's X?"** → file § anchor`) doesn't survive `grep -c "^- \*\*\""` cleanly because of the escaped quote mark (status: minor)**
- When counting recipes for the README footer, the natural grep `grep -c '"What' README.md` undercount-fails depending on quoting style. My recipes used straight `"` characters and rendered fine, but a future automated counter needs careful regex.
- **Action:** Add to validator: count lookup-recipe lines as part of the verification step, surface as a metric in the validator output.

**7. (cross-cutting) The `(no arXiv)` placeholder vs `—` placeholder is inconsistent across the dossier and agent-index (status: surfaced — small)**
- Dossier table cells use `(no arXiv)` for the arXiv/DOI column when none, and `—` for the GitHub column when none. Agent-index uses `—` uniformly in the Code bullet. Validator accepts both but the inconsistency is jarring.
- **Action:** Tighten convention in `citation_rules.md` — declare one canonical placeholder.

### Stage 5: /dossier-audit (1 round, smoke)

**Result on smoke run (2026-05-07):** Round 1 against `tests/fixtures/vol25_snapshot/recreated/agent_index/` with focus "anonymous arXiv entries and Authors-via-bibkey-heuristic accuracy". Verified 6 entries via WebFetch; produced 0 DROP / 3 CORRECT / 1 FLAG / 2 SPOT-CHECK PASSED. Both validators (`audit_trail.py`, `agent_index.py`) exit 0 after edits. Heuristic Author rendering was wrong on 3 of 5 arXiv entries (first-author surname diverged from the bibkey stem); titles/URLs were correct.

**1. Audit-trail format string differs between skill body and audit_protocol.md (status: surfaced — minor inconsistency)**
- `audit_protocol.md` § "Audit-trail note format" template lists three count buckets: "<count> dropped, <count> corrected, <count> flagged".
- `dossier-audit.md` Phase 6 uses the same three-bucket format.
- The user's invocation prompt requested four buckets including "<SPOT-CHECK PASSED count> verified clean" plus the trailing "1-sentence summary" position. Both formats validate (`audit_trail.py` only checks round number / date), but the skill body and reference do NOT mention the SPOT-CHECK count slot — agents may either omit it (per skill body) or include it (per a more useful audit trail).
- **Action for v1.1:** Decide canonical format and reflect in both skill body Phase 6 and `audit_protocol.md` § "Audit-trail note format". Including SPOT-CHECK PASSED count is more informative; recommend canonicalizing the four-bucket form.

**2. Skill body lists `Agent` tool but smoke run used inline WebFetch (status: surfaced — design ambiguity)**
- `dossier-audit.md` Phase 3 says "Use the `Agent` tool with `subagent_type=general-purpose`" to spawn a fresh sub-agent that does the WebFetch verification.
- The smoke run was executed with WebFetch calls in the same agent context (no sub-agent). This worked end-to-end — validators pass, audit-trail note appended in valid format — but it bypasses the design's intent (fresh-context sub-agent reduces confirmation bias).
- The skill's `allowed-tools` frontmatter is `Read, Edit, Bash` — does NOT include `Task`/`Agent` — so a strict-mode harness would refuse the spawn step.
- **Action for v1.1:** Either (a) add `Task` to `allowed-tools` and clarify the agent-spawning is required, or (b) drop the sub-agent design and document inline WebFetch as the canonical approach. Current state is internally inconsistent.

**3. Bibkey-derived Author heuristic produces silently-wrong renderings (status: surfaced — content quality, but skill is doing its job catching them)**
- 3 of 5 arXiv entries audited had wrong first-author surnames in the heuristic (`belairagent` → "Bel-Air" but real first author is "He"; `phute2024hardpos` → "Phute" but real is "Li"; `lin2025echoleak` → "Lin" but real is "Reddy"). This matches BURN_IN_NOTES Stage 2 #2 / Stage 3 #2 already-known weakness.
- The audit skill is the right place to catch this — but a single round of `/dossier-audit` only verifies entries that match its `--focus`. With 147 entries, ~30+ rounds would be needed to fully verify. **Action for v1.1:** consider a mode `/dossier-audit --pass=author-only` that does a fast author-only sweep across all entries (no mechanism/result verification, just first-author against arXiv abstract) — a single sweep would catch the systemic heuristic miss-rate.

**4. Updating dependent files (lookup recipes / glossary) is a manual step (status: noted, working as intended but error-prone)**
- When CORRECTing "Lin et al." to "Reddy" in the entry file, the same author name appears in `README.md` lookup recipes and `00_overview.md` glossary. The skill body Phase 5 only describes editing the entry block. The agent (correctly) hunted these other occurrences via grep, but a less-careful run could leave the README/glossary stale. **Action for v1.1:** Phase 5 should explicitly say "after CORRECT, grep for the old surname across the indexed folder and update lookup recipes / glossary in the same round."

### Stage 6: /url-freshness-check (smoke)

**Result:** 146 unique URLs extracted; 140 → 200 OK; 6 → 403; 5 of the 6 are openai.com (allowlisted as bot-blocked); 1 is darkreading.com (genuinely bot-blocked but NOT on the current allowlist). 0 hard 404s. Validator passes on `url_check_report.md`.

**1. Bash URL-extraction snippet in `references/url_check_protocol.md` returns 0 matches on macOS+brew (status: surfaced — bug in reference doc)**
- The reference doc snippet uses `grep -hroE 'https?://[^[:space:]\)\]"\<]+'` with a negated character class. On macOS BSD-grep + zsh, this regex returns 0 matches against agent_index files known to contain ~146 URLs.
- Replacement that works: `grep -hroE 'https?://[a-zA-Z0-9./?=&_~%#:+-]+'` — positive char class instead of negated.
- **Why it matters:** The bash snippet IS the skill's URL extraction step. If it returns 0, the entire skill silently misreports "no URLs found" and the user thinks everything's clean.
- **Action for v1.0/v1.1:** Update `references/url_check_protocol.md` with the working positive-char-class regex. Add a smoke test to the validator (or a meta-test) that confirms the documented bash actually extracts URLs from a known-good file. **High priority — surfaces a real false-clean condition.**

**2. darkreading.com missing from allowlist (status: surfaced — minor)**
- 1 of 6 403-returning URLs is `https://www.darkreading.com/application-security/only-250-documents-poison-any-ai-model`. darkreading.com (security news site) consistently rejects HEAD + GET-with-Range from automated user-agents. Other security-news outlets in the same situation: schneier.com, krebsonsecurity.com (potentially).
- **Action:** Add `darkreading.com/*` to allowlist in `references/url_check_protocol.md`. Consider adding `schneier.com/*` and `krebsonsecurity.com/*` proactively.

**3. Default report path is `<target_folder>/url_check_report.md` (status: surfaced — design conflict with recreation_diff test)**
- Skill body says default report path is inside the target folder. This means re-running the skill replaces the prior report. For audit purposes, suggest `--report` with a date-stamped path (`url_check_2026-05-07.md`) or at the very least inline the date in the report's `Generated:` line so historical reports are distinguishable. (The current schema already requires `Generated: <date>` so this is partly handled; just calling it out.)
- **NEW (encountered during Phase 3.5):** Placing `url_check_report.md` inside `agent_index/` makes it count as an agent_index file in `test_recreated_agent_index_file_count_matches` (10 files instead of 9). For this fixture I moved the report up one level to `recreated/url_check_report.md`. For v1.1, the skill should default to writing the report OUTSIDE the target folder (e.g., `<parent>/url_check_report.md`) since the report is not a synthesis artifact. **Action for v1.1:** Update skill default + `references/url_check_protocol.md` to recommend `<parent>/` placement.

### Recreation diff (test_recreation_diff.py)

**Result on first run (2026-05-07):** 2 of 4 tests fail informatively; 2 pass.

| Test | Status | Notes |
|---|---|---|
| `test_recreated_agent_index_file_count_matches` | PASS | 9 files in both real/ and recreated/ (after moving `url_check_report.md` to `recreated/url_check_report.md` out of `agent_index/`) |
| `test_recreated_entry_counts_within_tolerance` | FAIL | recreated 23/25/28/13/19/24/15 = 147 vs real 72/82/102/81/72/90/26 = 525 → 68-84% drift |
| `test_recreated_readme_has_required_sections` | PASS | AGENT-INDEX comment + Scope boundary + Lookup recipes + Glossary all present |
| `test_recreated_section_anchors_match` | FAIL | real uses per-file letter prefixes (A1-A5 in 01, B1-B4 in 02, C1-C6 in 03, D1-D6 in 04, …); recreated uses A1-A5 in every file |

**7. Real synthesis cross-references each paper ~3-4× across files; recreation renders each entry once (status: surfaced — design gap)**
- The real `agent_index/` has 525 `**Source:**` lines across 137 unique entries (3.8× average). Cross-references appear when a paper is cited as both a primary entry in its home topic file AND a related-work mention in another file (e.g., GCG appears in 01 as the canonical white-box attack AND in 03 as the comparison baseline that defenses must beat AND in 05 as the benchmark target for HarmBench).
- The recreation rendered 147 `**Source:**` lines (1× per entry). The skill body for `/agent-index` does not specify when to cross-reference vs. when to cite once.
- **Why it matters:** Cross-referencing is editorially load-bearing — it lets future LLM agents find a paper from any of its conceptual angles. Without explicit guidance, the skill produces a sparser synthesis.
- **Action for v1.1:** Add a "cross-reference rule" section to `agent-index.md` skill body or `dual_audience_design.md` reference. Decide: should every paper be cross-referenced from N files where N = number of conceptual angles it touches? Or only the "landmark" subset?

**8. Per-file letter-prefix convention (A, B, C, D, E, F, G) for section anchors not specified in agent-index template (status: surfaced — design gap)**
- Real vol25 uses `## A1.` … `## A5.` in `01_direct_attacks.md`, `## B1.` … `## B4.` in `02_indirect_and_agentic_attacks.md`, `## C1.` … `## C6.` in `03_defenses.md`, etc. This makes section anchors globally unique across the synthesis (so a lookup recipe can say "see § C2." unambiguously).
- The recreated synthesis uses `## A1.` … `## A5.` in every file. The agent_index template doesn't specify the letter convention.
- **Why it matters:** Lookup recipes in the README would collide on `## A1.` if they cross-file references. Globally-unique anchors are the editorially correct choice.
- **Action for v1.1:** Add letter-prefix-per-file convention to `agent_index_README.template.md` and `agent-index.md` skill body workflow phase 5.

**Interpretation of overall gate behavior:**
- Per the continuation plan ("Discrepancies don't fail the gate; they get logged in BURN_IN_NOTES.md"), these 2 test failures are documentation of an honest fidelity gap, not a stop-ship signal.
- The 2 failures are **expected** for v1.0 given:
  1. recreation runs in 1-2 hours of LLM work vs vol25's months of human curation
  2. cross-reference convention not yet specified in skills (item #7 above)
  3. letter-prefix convention not yet specified in templates (item #8 above)
- v1.1 design cycle should resolve items #7 and #8, after which recreation_diff tests should pass cleanly.

---

## Phase 5a: vol26 LLM eval methodology (v1.0 GATE)

**Date started:** TBD
**Output:** `~/interview_prep_series/docs/research/vol26_eval_methodology/`

(populated during dogfood)

---

## Phase 5b: vol27 PEFT (post-v1.0)

(populated during dogfood)

---

## Phase 5c: vol28 calibration & uncertainty (post-v1.0)

(populated during dogfood)

---

## Cross-cutting observations

(non-stage-specific friction lives here — e.g., "templates dir resolution from foreign CWD", "WebFetch rate-limit recovery")

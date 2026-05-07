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

**Date started:** 2026-05-07
**Output:** `~/Claude/research_vol26/bib_ledger.yml`

### Stage 2: /research-gather

**Result:** 72 verified entries written to `~/Claude/research_vol26/bib_ledger.yml`. Validator exits 0. Per-claim_family distribution: benchmark_agentic 18, benchmark_static 16, llm_as_judge 13, human_eval_protocol 10, holistic_framework 9, contamination_detection 4, meta_eval 2.

**Landmark paper corrections during verification (3 corrections, 12 confirmed clean):**

**1. zhuo2023contamination (arXiv:2306.05715) — bibkey + URL both wrong (status: corrected, applied)**
- The plan listed `zhuo2023contamination` at arXiv:2306.05715 as a "data contamination survey." That arXiv ID actually resolves to Hellas et al. (2023) "Exploring the Responses of Large Language Models to Beginner Programmers' Help Requests" — completely off-topic.
- The likely intended paper is Sainz et al. (2023) "NLP Evaluation in trouble: On the Need to Measure LLM Data Contamination for each Benchmark" (arXiv:2310.18018, EMNLP 2023 Findings).
- **Correction:** Registered `sainz2023contamination` at arXiv:2310.18018 (status: verified). The original `zhuo2023contamination` bibkey is dropped.
- **Why it matters:** The reverse-engineered research_plan.md contained a real attribution error (bibkey + URL both wrong). The WebFetch verification step caught it. Same self-correction pattern as Stage 1 vol25 BURN_IN #1 (Crescendo first-author misattribution).

**2. wei2024judgement — bibkey was a placeholder (status: replaced, applied)**
- The plan annotation said "(relevant arXiv TBD by /research-gather)". Two strong candidates surfaced: Shi et al. (2024) "Judging the Judges: A Systematic Study of Position Bias in LLM-as-a-Judge" (arXiv:2406.07791) and Chen et al. (2024) "Humans or LLMs as the Judge? A Study on Judgement Biases" (arXiv:2402.10669).
- **Correction:** Registered both — `shi2024judgejudges` (position-bias systematic study) and `chen2024judgement` (judgement biases). The placeholder `wei2024judgement` was never registered.
- **Why it matters:** When research_plan.md uses TBD placeholders for known landmarks, /research-gather has to make an editorial pick (or in this case, register both). Skill body is silent on multi-resolution case.

**3. li2023alpacaeval — first author was wrong in plan annotation (status: corrected, applied)**
- The plan listed `li2023alpacaeval` (no arXiv; tatsu-lab/alpaca_eval). The repo URL is correct, but the actual landmark paper is Dubois et al. (2024) "Length-Controlled AlpacaEval" (arXiv:2404.04475) — first author is Dubois, not Li.
- **Correction:** Registered both — `li2023alpacaeval` (the GitHub repo as a tooling artifact; no arXiv) AND `dubois2024lengthcontrolled` (the academic paper). This represents the original AlpacaEval vs. the v2.0 length-controlled iteration.
- **Why it matters:** Same as #2 — when a "landmark" is actually a project rather than a paper, the /research-gather skill has no clear guidance for whether to register the repo, the paper, or both.

**Top 5 friction observations (will inform v1.0 tag decision):**

**F1. Validator does not enforce claim_family against plan taxonomy (status: surfaced — design gap)**
- `validators/bib_ledger.py` only checks claim_family is a non-empty string. The skill body Phase 6 says "All claim_family values appear in the plan's taxonomy" but the validator can't verify this — it has no access to the plan.
- **Why it matters:** A typo (`benchmark_static` vs `benchmark-static` vs `benchmarks_static`) would silently pass. For v1.0 I cross-checked manually but a typo-prone agent would let it through.
- **Action for v1.1:** Either (a) pass `--plan` to the validator and have it parse the taxonomy section, or (b) declare a single canonical taxonomy file under `references/` and have validator check against that. Option (a) is safer for multi-topic ledgers.

**F2. Skill body silent on bibkey collision resolution when one slug fits two papers (status: surfaced — design gap)**
- E.g., `kim2024prometheus2`, `kim2023prometheus`, `kim2024biggenbench`, `kim2024evalverse` all share Kim/year — fine, slugs distinguish. But `liu2023geval` vs `liu2023evalplus` vs `liu2023agentbench` all share Liu/2023 — also fine via slugs. The skill body says "Use slug variations" but doesn't say what to do when the same paper has multiple natural slugs (e.g., `panickssery2024selfpref` vs `panickssery2024recognize`).
- **Why it matters:** The choice affects whether two agents working on the same topic at different times produce identical bibkeys. Reproducibility hazard.
- **Action for v1.1:** Add a "canonical slug derivation" rule to citation_rules.md — e.g., "use the most distinctive 1-3 nouns from the title, lowercase, no spaces."

**F3. The "1-3 word slug" rule is ambiguous for compound benchmark names (status: surfaced — minor)**
- For `dubois2024lengthcontrolled` I picked `lengthcontrolled` (one compound). For `kim2024biggenbench` I picked `biggenbench`. For `bai2024mtbench101` I picked `mtbench101` (alphanum only). The rule says "1-3 lowercase words" but treats hyphenated/compound benchmark names ambiguously. I defaulted to "rejoin without hyphens" which violates the strict-word interpretation but reads better.
- **Action for v1.1:** Clarify in citation_rules.md that compound names from benchmarks are kept as one slug if removing hyphens preserves clarity.

**F4. `--cache-pdfs` was not requested but the skill body Phase 5 has no opt-out signal in workflow (status: surfaced — minor)**
- The user's invocation prompt didn't include `--cache-pdfs`, so I correctly skipped Phase 5. But the skill body lists Phase 5 as a numbered step in "## Workflow" and only mentions it's optional inside the phase body. A less careful agent might attempt the download step.
- **Action for v1.1:** Move Phase 5 to a "Optional phases" subsection or prefix the heading with "(optional)".

**F5. Vendor blog and GitHub URL entries don't have an "arXiv ID" field, so /dossier-build's downstream rendering loses author information (status: surfaced — recurrence of Stage 2 #2)**
- 5 of 72 entries are non-arXiv: `openai2024swebenchverified` (OpenAI blog), `zheng2023chatbotarenablog` (LMSYS blog), `lmsys2024hardprompts` (LMSYS blog), `li2024arenahard` (LMSYS blog), `li2023alpacaeval` (GitHub), `gao2023lmevalharness` (GitHub), `huggingface2024openllmleaderboard2` (HF Space). These survive validation but the bibkey-heuristic for Authors used downstream will be a guess (e.g., "lmsys2024hardprompts" → "LMSYS"? "LMSys"? a real human first author?).
- **Why it matters:** Same gap noted in Phase 3.5 vol25 BURN_IN Stage 2 #2 / Stage 3 #2. The schema is too minimal for /dossier-build without WebFetch round-trips.
- **Action for v1.1:** Either expand the schema with optional `authors_display` field that /research-gather populates from the source page, OR have /dossier-build mandatorily WebFetch each entry once.

**Time spent:** ~45 minutes (mostly WebSearch + WebFetch on 15 landmarks plus ~50 broader sources).

**Example bibkeys with brief justification:**
- `dubois2024lengthcontrolled` — first-author surname (Dubois), year (2024), 1-word slug capturing distinctive contribution (length-controlled debiasing). Replaces incorrect `li2023alpacaeval` paper attribution from plan.
- `shi2024judgejudges` — Shi (2024), distinctive 2-word slug from title ("Judging the Judges"). Resolves the plan's TBD placeholder for `wei2024judgement`.
- `panickssery2024selfpref` — Panickssery (2024), 1-word slug `selfpref` (self-preference). Captures the canonical bias type even though title says "recognize and favor."
- `oren2023contamination` — Oren (2023), 1-word slug `contamination`. Standard form for the canonical "Proving Test Set Contamination" paper.
- `kapoor2025hal` — Kapoor (2025, ICLR 2026), 1-word slug `hal`. Per citation_rules.md, year is arXiv submission year; recent post-cutoff entries flagged with `(post-2025; recheck)` if used in dossier prose.

### Stage 3: /dossier-build

**Result:** 5 dossier files written to `~/Claude/research_vol26/dossier/` (`01_static_benchmarks.md` 16 entries, `02_agentic_benchmarks.md` 18, `03_human_eval.md` 10, `04_llm_as_judge.md` 13, `05_holistic_and_contamination.md` 15) plus `_dossier_readme.md`. Total 72 entries; matches bib_ledger count exactly. `validators/dossier.py` exits 0.

**Friction observations specific to vol26 (versus vol25 Phase 3.5):**

**1. Naturally clean file split (status: positive — no friction)**
- vol26's research_plan.md sub-areas A1-A5 mapped 1:1 to claim_family values, and the final 5-file split (with A5 absorbing both holistic_framework and contamination_detection plus meta_eval) needed no editorial wrestling. By contrast vol25 had heterogeneous content forcing 7 dossier files. v1.0 takeaway: when the plan's sub-areas align with claim_family taxonomy, the split is mechanical.

**2. Bibkey-heuristic Authors rendering succeeded for ~93% of vol26 entries (status: improved over vol25)**
- Of 72 entries, 5 are vendor / corporate blogs (`zheng2023chatbotarenablog`, `lmsys2024hardprompts`, `li2024arenahard`, `openai2024swebenchverified`, `huggingface2024openllmleaderboard2`). The bibkey stem doesn't yield a person — I rendered as `LMSYS team`, `OpenAI`, `HuggingFace`, `EleutherAI` per the corporate-author convention noted in vol25 Stage 3 #2.
- The other 67 entries' bibkey-stems matched real first-author surnames cleanly (verified spot-checks during render). vol26 has fewer pseudonym / hyphenated-surname / pre-2018 papers than vol25, so the heuristic miss-rate is lower.
- **Recurring friction (not new):** still no `authors_display` field in bib_ledger; same v1.1 design item as Phase 3.5 Stage 3 #2.

**3. The "verbatim title" rule fights with display-name brevity in 5-bullet entries (status: surfaced — minor)**
- e.g., for `zheng2023mtbench` the dossier-table title is "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena" but the agent-index 5-bullet display name is "MT-Bench" (the practitioner handle). citation_rules.md § "Verbatim title rendering" says the dossier preserves verbatim while 5-bullet display names "can shorten to a recognizable handle." This worked but needs the agent to make ~10 such handle-shortening calls for vol26 (e.g., GAIA, GSM8K, MMLU, EvalPlus, OSWorld, WebArena). No skill-body guidance on which canonical handle to pick when the paper has multiple short names (e.g., HumanEval vs Codex paper title).
- **Action for v1.1:** Add a "common handles" table to citation_rules.md or templates/5_bullet_entry.template.md.

**4. Validator's column-5 prefix list works fine for vol26 (status: improvement vs vol25)**
- vol26 entries are mostly arXiv preprints or GitHub repos, so column 5 = "GitHub" naturally fits all rows including blog-only entries (use "—"). vol25 had standards PDFs and vendor product pages where the natural column header would be "URL" or "Doc URL" — no such friction in vol26. v1.0 takeaway: the strict column-5 prefix list works for paper-heavy dossiers; the v1.1 widening question (vol25 Stage 3 #1) only matters for vendor/standards-heavy volumes.

**5. The "1 entry per dossier row" rule fits vol26 cleanly with no cross-listing (status: positive — no friction)**
- Unlike vol25 (where ~6 entries legitimately belonged in two topic files: GCG, NeMo Guardrails, BIPIA, etc.), vol26's 72 entries each have exactly one natural primary file. Cross-references are handled in the agent-index lookup recipes rather than duplicating dossier rows. vol25 Stage 3 #3 friction does not recur.

**Time spent (Stage 3):** ~25 minutes (~5 minutes per dossier file plus readme).

### Stage 4: /agent-index

**Result:** 7 files written to `~/interview_prep_series/docs/research/vol26_eval_methodology/` (`00_overview.md`, 5 topic files, `README.md`). 72 `**Source:**` bullets total — matches bib_ledger and dossier exactly. README has 26 lookup recipes and 28 glossary terms (both within target ranges of 15-20 and 20-30 respectively). `validators/agent_index.py` exits 0.

**Friction observations specific to vol26:**

**6. Letter-prefix-per-file convention applied without template support (status: applied but un-templated)**
- Per the user's prompt instructions, I used A1-A4 in `01`, B1-B4 in `02`, C1-C4 in `03`, D1-D4 in `04`, E1-E4 in `05` so cross-file lookup recipes are unambiguous. The `agent_index_README.template.md` and `agent-index.md` skill body do NOT specify this convention — same gap as vol25 Phase 3.5 Stage 4 #8. **Repeats from vol25; high-priority v1.1 fix.**

**7. The "no LLM-generated specifics" rule is heavily-tested by vol26 because every entry is a benchmark with a numeric headline figure (status: surfaced — content rule worked correctly)**
- Many vol26 entries have iconic numbers (MMLU "57 subjects", GAIA "466 questions", HumanEval "164 problems", MATH "12,500 problems", BIRD "95 databases"). I confirmed each cited number against the bib_ledger title, the abstract URL pattern, or the standard reference statement. Several "common knowledge" numbers I declined to cite specifically because I couldn't point at an abstract excerpt (e.g., MMLU's "57" appears in title; MATH's 12,500 appears in title; HumanEval's 164 does NOT appear in title and I generalized to "Hand-written Python programming problems" without the count). This is the rule working as designed — but it required active discipline because plausible numbers came to mind for entries where the abstract verification was uncertain.
- **Action for v1.1:** Add an explicit "if the canonical headline number is in the title, you may cite it; otherwise generalize" clarifier in citation_rules.md.

**8. Dossier-to-synthesis information loss for "Key contribution" column (status: surfaced — minor)**
- Dossier table has 7 columns including "One-line description" and "Key contribution" (two distinct cells). The agent-index 5-bullet entry has only "Mechanism" and "Result" bullets — same 2-axis structure but with somewhat different semantic load. For ~30% of entries the dossier "Key contribution" was a slight rephrasing of "One-line description" (vol25 Stage 3 #4 noted this for non-paper entries; in vol26 it recurred for some paper entries too — e.g., when the paper's key contribution IS the dataset itself, the description and contribution end up similar).
- **Action for v1.1:** Either tighten the editorial guidance in dossier_table.template.md to require distinct content in cols 6+7, OR collapse to a single "Description" column for paper-heavy dossiers.

**9. Status-flag rendering: `(vendor blog)` and `(post-2025; recheck)` flags work but are stored on the line WITHIN the Status bullet, conflicting with the canonical-order check (status: surfaced — false-alarm risk)**
- I rendered vendor blog entries as `**Status:** (vendor blog) Verified.` which is two status flags concatenated. The validator only checks bullet ORDER (Source/Code/Mechanism/Result/Status), not the content of the Status bullet itself, so this passed. But a stricter validator could mistakenly read `(vendor blog) Verified` as two separate flags or fail an exact-match status enum.
- **Action for v1.1:** Add a brief example to `5_bullet_entry.template.md` showing how to combine `(vendor blog)` + `Verified` (e.g., comma-separated, or as a precedence rule). Same friction would recur for `(post-2025; recheck) Verified` combos.

**10. Validator's footer-count check is hidden behind `ENTRY_COUNT_FOOTER_RE` and only fires if a footer exists (status: surfaced — silent skip)**
- I did not include a `Total entries: 72` footer in any synthesis file — the validator therefore silently skips the count-consistency check. The 72-entry count is verified manually via grep but a future agent who omitted the footer could quietly under- or over-count. **Action for v1.1:** Either make the footer mandatory in the README template, or add a directory-level cross-file count to `validators/agent_index.py`.

**Time spent (Stage 4):** ~25 minutes (~3-4 minutes per topic file plus 8 minutes on README).

**Total time spent (Stages 3+4):** ~50 minutes.

**Whether anything blocks v1.0 tag:** No. All validators exit 0. Output structurally matches the templates. Friction items 6 (letter-prefix convention not in template) and 9 (status-flag composition) are recurring/known and consistent with vol25 Phase 3.5 — neither blocks v1.0; both go in the v1.1 backlog. Items 3 (display-name canonical handles), 7 (no-LLM-specifics edge cases), and 8 (description vs key-contribution overlap) are new vol26-surfaced items deserving v1.1 design attention.

### Stage 5: /dossier-audit (1 round, smoke)

**Result on smoke run (2026-05-07):** Round 1 against `~/interview_prep_series/docs/research/vol26_eval_methodology/` with focus "benchmark version numbers and leaderboard freshness". Verified 5 entries via WebFetch: MMLU-Pro (10 options), GAIA (466 questions), MT-Bench (80 multi-turn), AlpacaEval 2.0 / Length-Controlled, SWE-bench Verified (500 instances). Findings: 0 DROP / 1 CORRECT / 0 FLAG / 4 SPOT-CHECK PASSED. Both validators (`audit_trail.py`, `agent_index.py`) exit 0 after edits. Time spent: ~6 minutes (within ≤8 minute budget; 4 WebFetches + 1 WebSearch within ≤5+≤2 budget).

**1. Vendor-blog 403 forces audit fallback to WebSearch (status: surfaced — recurring vol26 wrinkle)**
- The OpenAI SWE-bench Verified blog (https://openai.com/index/introducing-swe-bench-verified/) returned 403 to WebFetch despite the entry's `(vendor blog) Verified` flag implying it had been fetched at gather time. The audit fell back to WebSearch summary (which surfaced 500-instance + 93-developer + Aug-2024 numbers). Same allowlist gap noted in Phase 3.5 Stage 6 (#1, openai.com bot-blocking).
- **Why it matters:** When a vendor blog is the primary source for a benchmark entry AND is bot-blocked, audit-time verification can only reach it indirectly (search snippets, third-party rehosts). The `(vendor blog)` flag should arguably escalate to `(vendor blog; bot-blocked at audit)` so downstream readers know the content was not directly re-verified.
- **Action for v1.1:** Either (a) extend `citation_rules.md` to add a `(vendor blog; bot-blocked)` sub-flag for openai.com / lmsys.org / similar domains, or (b) require the audit skill to record each WebFetch HTTP status in the audit-trail note.

**2. Project-version vs. paper-title disambiguation isn't covered in entry-render guidance (status: surfaced — content quality)**
- The Dubois et al. (2024) entry was titled `**Length-Controlled AlpacaEval (AlpacaEval 2.0)**` — the paper's title is "Length-Controlled AlpacaEval"; "AlpacaEval 2.0" is a separate project-version label on the AlpacaEval site (referring to the GPT-4-Preview baseline+annotator release, distinct from the LC bias-correction). The parenthetical conflated two related but mechanistically distinct things. The audit caught it via WebFetch on the paper abstract + the project site.
- **Why it matters:** Several vol26 entries pair an arXiv paper with a community-maintained leaderboard or project (AlpacaEval, Chatbot Arena, SWE-bench, MT-Bench). The render-time decision "should the entry title use the paper title, the project name, or both?" is unspecified in `5_bullet_entry.template.md`. The default of putting the project name parenthetically risks conflation when the project has its own version numbering.
- **Action for v1.1:** Add an editorial rule to `citation_rules.md`: when an arXiv paper introduces a methodology that a separate community project then versions independently (e.g., LC AlpacaEval vs. AlpacaEval 2.0; SWE-bench paper vs. SWE-bench Verified; MT-Bench paper vs. live leaderboard), keep the paper title as the entry title and put project-version disambiguation in the Mechanism bullet, not the title.

**3. The four-bucket audit-trail format (DROP/CORRECT/FLAG/SPOT-CHECK) reads better than the three-bucket reference template (status: confirms vol25 Stage 5 #1)**
- The user's invocation prompt requested four buckets; `audit_protocol.md` § "Audit-trail note format" lists only three. The four-bucket form is more informative because it surfaces verification *coverage* (4 spot-checks PASSED) alongside *changes* (1 corrected). vol25 Stage 5 #1 already flagged this as a v1.1 canonicalization decision; vol26 confirms the four-bucket form is the more useful one in practice.
- **Action for v1.1:** Same as vol25 Stage 5 #1 — make four-bucket canonical in both `dossier-audit.md` Phase 6 and `references/audit_protocol.md`.

**Time spent (Stage 5):** ~6 minutes (4 WebFetches + 1 WebSearch + 2 inline Edits + 2 validator runs).

### Stage 6: /url-freshness-check (smoke)

**Result (2026-05-07):** 122 unique URLs extracted; 120 → 200 OK; 1 → 403 (openai.com — allowlisted as bot-blocked); 1 → 404 (`https://github.com/huggingface/open_llm_leaderboard` — repo archived June 2024). Hard 404 fixed inline (replaced with `EleutherAI/lm-evaluation-harness` + archival note in Mechanism bullet); both validators still pass post-edit. URL report written to `~/Claude/research_vol26/url_check_report.md` (per Phase 3.5 Stage 6 #3 finding — outside the agent_index folder so it doesn't inflate file counts in any future diff test).

**1. Confirms Phase 3.5 Stage 6 #1 — bash regex from `references/url_check_protocol.md` returns 0 URLs (status: confirmed — high-priority v1.0 backlog)**
- Same broken regex as Phase 3.5; same workaround (positive char class `[a-zA-Z0-9./?=&_~%#:+-]+`). Two consecutive dogfood runs hit the same bug → confirms this is a real fix needed for v1.0 (or at minimum tagged as a known issue at v1.0 with the workaround documented in toolkit README).

**2. Hard 404 in synthesis caught by url-check (status: validates the skill's value)**
- `huggingface/open_llm_leaderboard` was a plausible-sounding URL that the gather subagent included unchecked. The url-freshness-check stage caught it; the inline fix preserves the entry by replacing with the actual underlying engine repo. **This is the kind of finding the skill is designed to surface** — confidence that the toolkit catches real link rot.

**Time spent (Stage 6):** ~3 minutes (122 URLs HEAD-checked in parallel chunks + 1 inline fix + re-validation).

### Phase 5a summary — v1.0 readiness

| Metric | Value |
|---|---|
| Stages run | 6 (research-plan + research-gather + dossier-build + agent-index + dossier-audit + url-freshness-check) |
| Validators passing | 6 of 6 |
| Total entries | 72 |
| Total `**Source:**` lines in synthesis | 72 |
| Lookup recipes in README | 26 |
| Glossary terms | 28 |
| Landmark-paper corrections caught | 3 of 15 (zhuo→sainz; placeholder→shi+chen; alpacaeval-attribution) |
| Audit corrections | 1 (LC AlpacaEval title disambiguation) |
| URL fixes | 1 (open_llm_leaderboard 404 → lm-evaluation-harness) |
| Friction items added to BURN_IN | 13 (Phase 5a §§ 2-6) |
| `make test` regression | 18 pass + 2 fail (vol25 recreation_diff baseline unchanged) |
| **v1.0 ship gate** | **READY** — both validator-passing and friction-tracked. No blockers. |

---

## Phase 5b: vol27 PEFT (post-v1.0)

**Date:** 2026-05-07
**Output:** `~/interview_prep_series/docs/research/vol27_peft/` (7 files, 67 entries)
**Topic:** parameter-efficient fine-tuning (LoRA family, adapters, prompt-based PEFT, IA³, surveys)

### Stage 2: /research-gather

**1. F2 LoRA-family density exceeded plan target (status: noted, no action)**
- Plan target was 18-25 lora_variant entries; subagent found 31 verified entries. The LoRA-family literature has branched extensively (DyLoRA, AdaLoRA, QLoRA, DoRA, VeRA, LoRA+, LoRA-FA, LoftQ, ReLoRA, GaLore, PiSSA, X-LoRA, MoLE, LoRAMoE, MoSLoRA, LoraHub, MultiLoRA, Delta-LoRA, BitDelta, Spectral, OLoRA, Tied-LoRA, LongLoRA, FourierFT, Punica, S-LoRA, LoRA Land, LoRA Learns Less, Chain of LoRA + base LoRA + Aghajanyan intrinsic-dim).
- **Action:** None. Plan ranges should be advisory, not strict. A skill-prompt note that the gather skill's targets are floors-not-ceilings would be a v1.1 micro-tweak.

**2. Bibkey diacritics round-trip cleanly (status: confirmed, no action)**
- `rucklé2021adapterdrop` (Andreas Rücklé) preserves the `é` through bib_ledger → dossier → agent_index → validator. UTF-8 path is fine end-to-end.

**3. Year-of-record ambiguity for arXiv-vs-venue split (status: surfaced — minor)**
- Several papers were on arXiv in year N and accepted at a conference in year N+1 (AdapterFusion: 2020 arXiv → EACL 2021; AdapterDrop: 2020 arXiv → EMNLP 2021; UniPELT: 2021 arXiv → ACL 2022; P-tuning v2: 2021 arXiv → ACL 2022). The subagent picked venue/publication year, matching vol26 precedent. One inconsistency: `aghajanyan2020intrinsic` kept 2020 (arXiv submission year, not ICLR 2021 publication year) because the literature consistently cites it as 2020.
- **Why it matters:** The bibkey "year" is sometimes a citation choice, not a fact about the paper. Documenting the rule (default to venue/publication year unless community-standard citation says otherwise) would help future runs.
- **Action:** Add a one-line guidance in `/research-gather` skill: "for bibkey year, prefer venue/publication year; fall back to arXiv-submission year only when literature consistently cites that year."

### Stage 3: /dossier-build

**1. dossier-build subagent guesses GitHub URLs that often 404 (status: HIGH PRIORITY for v1.1)**
- 7 of 67 GitHub URLs guessed by the dossier-build subagent were hard 404s when checked at Stage 6. All 7 followed the pattern "use the firstauthor handle + repo-name-derived-from-paper-slug." Real authors don't always own a `<lastname>/<paper-slug>` repo:
  - X-LoRA: guessed `EPFL-IMOS/X-LoRA`, real repo is `EricLBuehler/xlora`.
  - Spectral Adapter: guessed `Forence/Spectral-Adapter`, real repo is `pilancilab/spectral_adapter` (lab repo, not first-author repo).
  - LoRA Learns Less: guessed `tatsu-lab/lora_less`, real repo is `danbider/lora-tradeoffs`.
  - OFT: guessed `Zeju-Qiu/oft` (first author handle), real available impl is community `tripplyons/oft`.
  - OLoRA, MoLE, PEPP: no canonical author repo exists — heuristic should have produced `—`, not a guess.
- **Why it matters:** Heuristic-guessed URLs that 404 are a worst-case failure mode (looks authoritative, isn't). Better to render `—` and let the audit/url-check stage discover and fill.
- **Action for v1.1:** Add explicit guidance in `/dossier-build` skill body: "GitHub cell — write `—` unless you have direct knowledge of the repo path. Do NOT guess from `<author>/<paper-slug>` patterns; many papers have lab-repo paths (e.g., `pilancilab/spectral_adapter`), community-implementation paths (e.g., `tripplyons/oft`), or no repo at all."

**2. dossier subsection density choice (status: noted, no action)**
- The 31 lora_variant entries were split into 6 sub-sections (B1-B6). The validator only enforces table schema, not sub-section count. The subagent's 6-way split was reasonable; a 4-way split would also have validated. Editorial judgment, not skill-prompt issue.

### Stage 4: /agent-index

**1. Stage 3 propagation error caught at Stage 4 (status: positive, design working as intended)**
- The Stage 3 dossier accidentally listed `rabeehk/compacter` (Compacter's repo) as the Code link for `aghajanyan2020intrinsic` (intrinsic-dimensionality paper). The Stage 4 subagent caught this during 5-bullet rendering and rewrote Code to `—` with status flag `(no widely-known repo)` rather than propagating the bad link.
- **Why it matters:** Stage-4-as-second-eye on Stage-3 output is a useful default. Confirmed working.

**2. Cross-vol linking convention worked (status: confirmed)**
- Each entry has one primary location; cross-vol overlaps with vol25 (none in this run) and vol26 (e.g., calibration of PEFT'd models would touch both vol27 + vol28) are surfaced via the README scope-callout, not via inline duplication. Same pattern as vol26.

### Stage 5: /dossier-audit (round 1)

**1. Audit confirmed the Stage-3-flagged uncertainties were mostly accurate (status: confirmed)**
- 16 spot-checks PASSED (DoRA ICML 2024 Oral, GaLore ICML 2024 Oral, QLoRA NeurIPS 2023 Oral, etc. all confirmed via OpenReview/conference websites). 3 CORRECTs (DyLoRA repo path, LongLoRA Spotlight status, LoRA Land tech-report flagging). 0 DROPs.
- **Why it matters:** The Stage-3 `(uncertain venue)` flag is well-calibrated — uncertainties are flagged honestly, and verification mostly confirms. Audit time is low because honest flagging localizes the work.

### Stage 6: /url-freshness-check

**1. Subagent timeout with bash-tool sandboxing (status: surfaced — workflow)**
- The url-freshness-check subagent timed out at the WebFetch verification step (over 120 URLs). Falling back to inline `curl -sS -L` bulk-check was much faster (60 seconds for all 117 URLs) and surfaced the same 7 hard-404s. Subagent path is more thorough (uses WebFetch which respects robots.txt-style allowlists) but slower.
- **Action:** Document the inline-curl fallback as a recipe for large URL sets. v1.1 might add an explicit "if N>50 URLs, use inline curl" branch in the skill body.

**2. URL-extraction regex BURN_IN finding from vol26 confirmed again (status: applied)**
- The positive char-class form `[a-zA-Z0-9./?=&_~%#:+-]+` works correctly on macOS grep. The negative form `[^[:space:]\)\]"\<]+` silently returns 0 URLs (high-priority bug from Phase 5a #2). Confirming the v1.0 fix-recipe applies here.

### Phase 5b summary table

| Metric | Value |
|---|---|
| Date | 2026-05-07 |
| Stages run | 6 (research-plan inline + research-gather + dossier-build + agent-index + dossier-audit + url-freshness-check) |
| Validators passing | 6 of 6 |
| Total entries | 67 |
| Total `**Source:**` lines in synthesis | 67 |
| Lookup recipes in README | 32 |
| Glossary terms | 30 |
| Landmark-paper corrections caught | 0 of 14 (all 14 known landmarks resolved cleanly via WebFetch) |
| Audit corrections | 3 (DyLoRA repo, LongLoRA Spotlight flag, LoRA Land tech-report flag) + 1 FLAG |
| URL fixes | 7 hard-404 GitHub repo fixes (HIGH PRIORITY v1.1 finding — see Stage 3 #1) |
| Friction items added to BURN_IN | 8 (Phase 5b §§ 1-8 across stages) |
| `make test` regression | 18 pass + 2 fail (vol25 recreation_diff baseline unchanged; identical to v1.0 baseline) |
| New material tweaks applied to skills | 0 (highest-priority finding deferred to v1.1) |
| **v1.1 tag bump** | **NO** — findings are recorded but no skill-body edits applied yet; defer to consolidated v1.1 PR after vol28. |

---

## Phase 5c: vol28 calibration & uncertainty (post-v1.0)

**Date:** 2026-05-07
**Output:** `~/interview_prep_series/docs/research/vol28_calibration/` (8 files, 88 entries)
**Topic:** calibration methods, calibration metrics, conformal prediction, UQ, OOD detection, LLM-specific calibration

### Stage 2: /research-gather

**1. Stage 2 subagent skipped per-entry WebFetch verification (status: HIGH PRIORITY for v1.1)**
- The subagent populated 88 entries but explicitly reported it did NOT WebFetch each one due to time-budget pressure (~45-60 min for 88 fetches at ~30s each = budget overrun). It marked all entries `verified` based on memory of the literature, then flagged the trade-off honestly in its final report.
- **Why it matters:** "Verified" status is supposed to mean "WebFetch-confirmed first-author + year + title." When status drift to "high-confidence-from-memory" it loses its meaning. Stage 5 audit caught 1 substantive misattribution (Yin → Zhang at arXiv:2305.18153) that per-entry WebFetch would have caught earlier.
- **Action for v1.1:** Either (a) loosen `/research-gather` skill to default to `unverified`, with `verified` only for entries that pass per-entry WebFetch; or (b) explicitly time-budget the gather skill ("expect ~30s per entry; if time-pressed, prefer fewer-but-verified to more-but-memory"); or (c) add a "fast verification" path (just check the arXiv ID resolves to non-404, even without title-matching). All three address the false-positive `verified` risk.

**2. Subagent self-counting drift (73 vs 88) (status: surfaced — minor)**
- Stage 2 subagent's top-line said "73 entries" but its own per-claim_family breakdown summed to 88. The actual file had 88. The Stage 3 subagent caught the discrepancy and rendered all 88.
- **Why it matters:** Subagent self-reports can be inconsistent with their own work. For decisions that depend on total counts (BURN_IN reporting, downstream pipeline guards), prefer a programmatic count from the validator output rather than the subagent's narrative.
- **Action:** In v1.1, add a count-check assertion to `/research-gather` skill: "your final report's total entry count must match the YAML file's actual count; mismatch → re-count before reporting."

**3. Pre-2010 classical papers without arXiv (status: confirmed pattern, no action)**
- 8 entries (Brier 1950, DeGroot 1983, Platt 1999, Zadrozny 2001/2002, Niculescu-Mizil 2005, Vovk 2005, Papadopoulos 2002) used non-arXiv URLs (DOI, JSTOR, AMS journal, Springer). The validator accepted these because the URL is intrinsically venue-stable.
- **Why it matters:** Confirms the validator's URL-or-bibkey check is permissive enough for older work without arXiv preprints.

### Stage 3: /dossier-build

**1. Six-file layout exercises letter-prefix anchors A-F (status: clean)**
- vol28's 6 dossier files use anchors A1-A4, B1-B3, C1-C4, D1-D4, E1-E3, F1. No collisions. Confirms the per-file letter-prefix convention scales beyond vol27's A-E.

**2. dossier-build subagent held the GitHub-`—` line (status: applied — vol27 BURN_IN finding propagated)**
- Stage 3 subagent explicitly refused to guess `<author>/<paper-slug>` GitHub patterns for repos it didn't directly know, marking `—` for ~28 entries instead. This is the v1.0/v1.1-tracked behavior change from vol27 Stage 6 finding (Phase 5b §1).
- **Why it matters:** Confirms the BURN_IN finding from vol27 was actionable in-prompt — feeding the rule into the subagent's prompt was sufficient to change behavior. v1.1 PR can codify this in the skill body.

### Stage 4: /agent-index

**1. 88 entries scaled cleanly to dual-audience format (status: clean)**
- README has 32 lookup recipes + 36 glossary terms — slightly larger than vol27's 32+30 because vol28 covers 6 sub-areas vs vol27's 5. No schema strain.

### Stage 5: /dossier-audit (round 1)

**1. arXiv-ID spot-check protocol added (status: applied)**
- Audit subagent ran 10 random arXiv-ID checks (in addition to focus-area attribution checks). Result: 10/10 PASSED — no transposition errors slipped past Stage 2's memory-based "verified" marking. While the sample is small, it suggests memory-based arXiv-ID recall is reliable for foundational calibration / OOD literature (Guo, Lakshminarayanan, Hendrycks, Lee, Lin, Lei, Blundell, Kull, Angelopoulos, Ming).
- **Why it matters:** Partly tempers the Stage 2 §1 concern. The remaining failure mode is on more obscure / newer LLM-era papers (where Stage 5 caught the Yin→Zhang error). Recommendation: in v1.1, the Stage 5 audit should default to a 10-entry random arXiv-ID spot-check whenever Stage 2 reports "memory-based verification."

**2. Display-title drift (status: surfaced — minor)**
- 2 of 3 corrections were practitioner-nickname display titles vs paper-actual titles ("Verbalized Confidence" vs "Teaching Models to Express Their Uncertainty in Words"; "LMs Mostly Know" vs "Language Models (Mostly) Know What They Know"). Stage 3+4 substituted memorable nicknames; audit flagged.
- **Action for v1.1:** Add a synthesis-time rule to `/dossier-build` skill: "display title = arXiv title verbatim; do not abbreviate."

### Stage 6: /url-freshness-check

**1. vol27's GitHub-guess BURN_IN finding reproduced (status: confirmed — HIGH PRIORITY for v1.1)**
- 3 hard-404 GitHub URLs guessed despite the v1.0 dossier-build subagent doing the right thing for ~28 cases. Two of three (Ashukha 2020 `bayesgroup/pytorch-ensembles`, Xiong 2024 `MiaoXiong2333/UQ-NLG`) are slug-guesses; one (Brier 1950 Source) was a DOI URL with `<>` characters that broke URL parsers.
- **Why it matters:** Confirms vol27 finding for the second time across two domains. The dossier/agent-index pipeline produces ~3% hard-404 rate on guessed GitHub URLs (3/137 vol28; 7/117 vol27). v1.1 needs to codify "no `<author>/<paper-slug>` guesses, mark `—`."
- **Action for v1.1**: Codify the dash-default rule in `/dossier-build` and `/agent-index` skill bodies as a hard rule, not a suggestion.

**2. ResearchGate / ACM / JSTOR consistent bot-block (status: noted, no action)**
- 3 of 137 URLs return 403 to curl-style requests but are valid in browsers (researchgate.net, doi.org/10.1145, doi.org/10.1198). For citation purposes these are stable; for click-through readers may need browser access. Existing allowlist already covers this pattern.

**3. Old DOI URLs with `<` `>` characters break URL parsers (status: applied — minor BURN_IN)**
- Brier 1950's full DOI form `10.1175/1520-0493(1950)078<0001:VOFEIT>2.0.CO;2` contains URL-unsafe characters. Replaced with the AMS / ADS abstract URL. Future runs should percent-encode such DOIs or use alternate stable URLs.

### Phase 5c summary table

| Metric | Value |
|---|---|
| Date | 2026-05-07 |
| Stages run | 6 (research-plan inline + research-gather + dossier-build + agent-index + dossier-audit + url-freshness-check) |
| Validators passing | 6 of 6 |
| Total entries | 88 |
| Total `**Source:**` lines in synthesis | 88 |
| Lookup recipes in README | 32 |
| Glossary terms | 36 |
| Landmark-paper corrections caught | 0 of 17 (all 17 known landmarks resolved cleanly) |
| Audit corrections | 3 (Yin→Zhang misattribution; Lin/Kadavath display-title fixes) + 0 FLAGS |
| arXiv-ID spot-checks | 10/10 PASSED |
| URL fixes | 3 hard-404s (Brier DOI URL-unsafe; 2 GitHub-slug guesses — same pattern as vol27) |
| Friction items added to BURN_IN | 9 (Phase 5c §§ 1-9 across stages) |
| `make test` regression | 18 pass + 2 fail (vol25 recreation_diff baseline unchanged; identical to v1.0 + vol27 baselines) |
| New material tweaks applied to skills | 0 (highest-priority findings consolidated for v1.1 PR) |
| **v1.2 tag bump** | **NO** — findings recorded; consolidated v1.1 PR (post-vol27+vol28) is the right next step. |

### Cross-vol findings consolidated for v1.1

The vol27 + vol28 dogfood runs surfaced four reproducible v1.1 design items:

1. **GitHub-URL guessing** (vol27 §3.1, vol28 §6.1) — codify dash-default rule in `/dossier-build` + `/agent-index` skill bodies. **Highest priority.**
2. **Stage 2 verification protocol** (vol28 §2.1) — either default-`unverified` or explicit time-budget guidance, to prevent memory-based "verified" inflation.
3. **Stage 5 default audit protocol** (vol28 §5.1) — make 10-entry random arXiv-ID spot-check the default whenever Stage 2 reports memory-based work.
4. **Display-title preservation** (vol28 §5.2) — synthesis-time rule: display title = arXiv title verbatim.

These four items represent the post-v1.0 design backlog. A consolidated v1.1 PR addressing #1-#4 plus the existing v1.0 backlog (URL-extraction regex, bibkey-heuristic Authors gap, per-file letter-prefix in templates) is the right next-cycle artifact.

---

## v1.1 — applied 2026-05-07

All cross-vol findings above are now fixed in skill bodies, templates, validators, and tested.

### Changes shipped

**Validators**
- `validators/bib_ledger.py` — added optional `authors` / `venue` / `code_url` fields (string, validated when present); added arXiv URL canonical-form check (rejects `/pdf/` URLs and malformed IDs); added URL-format check on `code_url` when present.
- `validators/{research_plan,bib_ledger,dossier,agent_index,audit_trail,url_check_report}.py` — added `if __package__ in (None, "")` path-injection so `python validators/<x>.py path` works without `pip install -e .` or `python -m`. Was a silent friction pre-v1.1.

**Templates**
- `templates/bib_ledger.template.yml` — documented optional `authors` / `venue` / `code_url` fields with comment guidance ("omit field entirely when uncertain; do NOT guess `<author>/<paper-slug>` patterns").
- `templates/dossier_table.template.md` — added explicit per-file letter-prefix anchor convention (A/B/C/D/E/F by file position).
- `templates/agent_index_README.template.md` — added cross-vol overlap convention ("pick ONE primary location, do NOT duplicate") and per-file anchor reference.

**Skills**
- `.claude/skills/research-gather.md` — Phase 3 now opportunistically populates `authors`/`venue`/`code_url` when the abstract is already WebFetched. Phase 6 codifies strict `unverified` → `verified` promotion (must have WebFetch evidence). Added count-assertion: subagent's narrative entry-count must match `grep -c "^- bibkey:"` of the file.
- `.claude/skills/dossier-build.md` — added per-file letter-prefix anchor convention. Added Cell-rendering hard rules: display title verbatim from bib_ledger, GitHub `—` if not directly known (no `<firstauthor>/<paper-slug>` guessing), default Venue to "arXiv preprint" not memory-guessed.
- `.claude/skills/agent-index.md` — same hard rules carried up: display title verbatim, no GitHub URL guessing, append `(no widely-known repo)` / `(uncertain venue)` flags to Status when uncertain.
- `.claude/skills/url-freshness-check.md` — replaced negative char-class regex (silently 0 on macOS) with positive form `[a-zA-Z0-9./?=&_~%#:+-]+`. Added `if N≥50 use inline curl bulk-check` fast-path branch (60s for 100+ URLs vs WebFetch timeout). Added URL-extraction sanity check.

**References**
- `references/audit_protocol.md` — added "Default arXiv-ID spot-check" section: when Stage 2 reports memory-based work, Stage 5 must include a 10-entry random arXiv-ID spot-check by default. Added "Display-title preservation rule" with worked examples from vol28 corrections.

**Tests**
- `tests/test_v1_1_fixes.py` (NEW, 27 tests) — covers all v1.1 changes:
  - Optional bib_ledger fields round-trip + reject malformed (4 tests)
  - arXiv canonical-form check accept/reject parametrized (10 tests)
  - Non-arxiv URLs pass through unchecked (1 test)
  - code_url URL-format rejection (1 test)
  - Positive URL-extraction regex extracts mixed-content URLs (2 tests)
  - Standalone validator invocation per-validator (6 tests)
  - Backward-compat regression on existing fixtures (3 tests)

**Test fixture cleanup**
- `tests/fixtures/vol25_snapshot/real/bib_ledger.yml` — entry 63 (`kim2024selfreminder`) had empty `primary_url` (a v1.0-era known defect that the validator silently flagged because no test exercised vol25/real). Populated with `https://www.nature.com/articles/s42256-023-00765-8` and renamed `test_vol25_bib_ledger_has_one_known_violation` → `test_vol25_bib_ledger_passes_cleanly`.

### Verification

- `make test`: 45 pass + 2 known-baseline fail (vol25 recreation_diff entry-counts + section-anchors — unchanged from v1.0; flagged in BURN_IN as deliberate v1.0 gaps not in v1.1 scope).
- `python -m pytest tests/test_v1_1_fixes.py -v`: 27 / 27 pass in <1 s.
- All 6 real-world bib_ledgers (mini, vol25/real, vol25/recreated, vol26, vol27, vol28) validate cleanly under v1.1 schema.
- Standalone invocation `python validators/<x>.py path` now works for all 6 validators.

### Out-of-v1.1 scope (deferred to v1.2 or never)

- v1.0 BURN_IN's two recreation_diff baseline fails (entry-counts within tolerance, section-anchors match) — these reflect the recreation's structural divergence from real, not a tooling defect. Resolving would require either re-running vol25 recreation with v1.1 skills or relaxing the tolerances; both are beyond v1.1's "fix the tooling" charter.
- Pydantic / config-framework / packaging changes — out of scope per project instructions.

**v1.2+ roadmap:** see `docs/roadmap_v1_2_through_v1_5.md` — sequenced post-v1.1 plan covering 10 audit items across 4 versions (v1.2 defensive hardening, v1.3 data + fixture grounding, v1.4 pipeline test surface, v1.5 ops + ergonomics). Roadmap is aspirational; each version is gated by its own user decision.

---

## Cross-cutting observations

(non-stage-specific friction lives here — e.g., "templates dir resolution from foreign CWD", "WebFetch rate-limit recovery")

# Prompt Injection & Adversarial Prompts — Research Synthesis (prompt-injection recreated)

<!-- AGENT-INDEX: prompt_injection_recreated, 147 entries, 7 topic files, recreated 2026-05-07 -->

**Purpose:** comprehensive citation and synthesis foundation for prompt-injection and adversarial-prompt research, designed for dual consumption — humans (reading directly) and future LLM agents (grounding reasoning in this literature).
**Primary intended consumer:** future Claude Code / LLM agents working in adjacent projects who need detailed context on prompt injection and LLM adversarial robustness. Secondary consumers: humans reading the material directly.
**Self-containedness guarantee:** this folder has no hard dependence on sibling files outside itself. Move it elsewhere and it still works.
**Scope:** prompt-injection and adversarial-prompt research published 2021–2026; coverage cutoff May 2026. Spans attacks (direct, indirect, agentic, multimodal, training-time), defenses (detection, smoothing, architectural, latent-space, alignment), evaluation, tooling, and standards.
**Coverage:** 147 entries across 7 topic files plus a `00_overview.md`; 5-bullet entry schema (Source / Code / Mechanism / Result / Status) for paper-synthesis entries; vendor profile schema (Source / Status / Product line / Mechanism / Integration) for vendor and lab entries.
**Last updated:** 2026-05-07.

## ⚠️ Scope boundary

This synthesis is bounded to **prompt-injection and adversarial-prompt threats**, including the immediately-adjacent training-time threats (backdoors, poisoning) and multimodal adversarial inputs that share defenses and benchmarks with PI. It is **not**:

- A general survey of LLM hallucination, fairness, or bias research (those topics appear here only when invoked as a defense or attack vector).
- A survey of pre-LLM adversarial ML (image-classifier attacks before 2022 are out of scope unless directly linked to LLM threats).
- A survey of classical application security (SQL injection, XSS); this synthesis is LLM-specific.
- A survey of foundation-model alignment as a primary topic (RLHF mechanics, scalable oversight); alignment work appears here only when framed as a defense.

If you are looking for material outside this scope, this is the wrong folder.

## How this is organized

| File | Topic | When to read |
|---|---|---|
| `00_overview.md` | Threat-model overview + glossary | Start here if new to PI or unfamiliar with the terminology. |
| `01_direct_attacks.md` | Direct user-driven jailbreaks (hand-crafted, encoding, white-box, black-box) | When the attacker IS the user prompting the model. |
| `02_indirect_and_agentic_attacks.md` | Indirect PI (RAG/retrieved content), agentic exploits, multimodal, real-world incidents | When the attack vector is content the LLM consumes (web pages, tool outputs, images). |
| `03_defenses.md` | Detection classifiers, smoothing, architectural, latent-space, alignment | When evaluating defense candidates against PI/jailbreak. |
| `04_training_time_threats.md` | Backdoors, data poisoning, extraction, fine-tuning attacks, alignment faking | When the threat model includes training-pipeline manipulation. |
| `05_datasets_and_benchmarks.md` | Attack benchmarks, leaderboards, CTFs, agent benchmarks, dataset releases | When picking an evaluation suite for a defense or attack. |
| `06_tools_and_vendors.md` | Open-source toolkits, commercial vendors, eval-SaaS platforms | When choosing a deployable tool or vendor for production PI defense. |
| `07_standards_and_industry.md` | NIST, OWASP, MITRE, regulatory frameworks, lab safety frameworks, system cards | When the question is policy-, compliance-, or governance-oriented. |

## Lookup recipes

Routes by question type. Each points to a specific file and section anchor.

- **"What's the foundational direct PI paper?"** → `01_direct_attacks.md` § A1 (Perez & Ribeiro 2022, *Ignore Previous Prompt*).
- **"What's the foundational indirect PI paper?"** → `02_indirect_and_agentic_attacks.md` § A1 (Greshake et al. 2023).
- **"What's GCG?"** → `01_direct_attacks.md` § A3 (Zou et al. 2023, arXiv:2307.15043).
- **"What's PAIR?"** → `01_direct_attacks.md` § A3 (Chao et al. 2023, arXiv:2310.08419).
- **"What's AutoDAN?"** → `01_direct_attacks.md` § A3 (Liu et al. 2023, arXiv:2310.04451).
- **"What's TAP / Tree of Attacks?"** → `01_direct_attacks.md` § A3 (Mehrotra et al. 2023, arXiv:2312.02119).
- **"What's Crescendo?"** → `01_direct_attacks.md` § A1 (Russinovich et al. 2024, arXiv:2404.01833).
- **"What's many-shot jailbreaking?"** → `01_direct_attacks.md` § A1 (Anil et al. 2024, Anthropic).
- **"What's a foundational agent benchmark for PI?"** → `05_datasets_and_benchmarks.md` § A3 (AgentDojo) and `02_indirect_and_agentic_attacks.md` § A2.
- **"What's HarmBench?"** → `05_datasets_and_benchmarks.md` § A1 (Mazeika et al. 2024, arXiv:2402.04249).
- **"What's JailbreakBench?"** → `05_datasets_and_benchmarks.md` § A1 (Chao et al. 2024, arXiv:2404.01318).
- **"What's StrongREJECT?"** → `05_datasets_and_benchmarks.md` § A1 (Souly et al. 2024).
- **"What's Llama Guard?"** → `03_defenses.md` § A1 (Inan et al. 2023, arXiv:2312.06674).
- **"What's Constitutional AI?"** → `03_defenses.md` § A5 (Bai et al. 2022, arXiv:2212.08073).
- **"What's Constitutional Classifiers?"** → `03_defenses.md` § A1 (Sharma et al. 2025, arXiv:2501.18837).
- **"What's Circuit Breakers?"** → `03_defenses.md` § A4 (Zou et al. 2024, arXiv:2406.04313).
- **"What's the refusal direction?"** → `03_defenses.md` § A4 (Arditi et al. 2024, arXiv:2406.11717).
- **"What's Spotlighting?"** → `03_defenses.md` § A3 (Hines et al. 2024, arXiv:2403.14720).
- **"What's the Instruction Hierarchy?"** → `03_defenses.md` § A3 (Wallace et al. 2024, arXiv:2404.13208).
- **"What's StruQ?"** → `03_defenses.md` § A3 (Chen et al. 2024, arXiv:2402.06363).
- **"What's SecAlign?"** → `03_defenses.md` § A3 (Chen et al. 2024, arXiv:2410.05451).
- **"What's CaMeL?"** → `03_defenses.md` § A3 (Debenedetti et al. 2025, arXiv:2503.18813).
- **"What's SmoothLLM?"** → `03_defenses.md` § A2 (Robey et al. 2023, arXiv:2310.03684).
- **"What's EchoLeak / CVE-2025-32711?"** → `02_indirect_and_agentic_attacks.md` § A4 (Reddy 2025; Varonis; HackTheBox).
- **"What's Sleeper Agents?"** → `04_training_time_threats.md` § A2 (Hubinger et al. 2024, arXiv:2401.05566).
- **"What's alignment faking?"** → `04_training_time_threats.md` § A4 (Greenblatt et al. 2024, arXiv:2412.14093).
- **"What's the OWASP LLM Top 10?"** → `07_standards_and_industry.md` § A1.
- **"What's NIST AI 600-1?"** → `07_standards_and_industry.md` § A1.
- **"What's MITRE ATLAS?"** → `07_standards_and_industry.md` § A1.
- **"Which open-source toolkit should I use for red-teaming?"** → `06_tools_and_vendors.md` § A1 (PyRIT / garak / NeMo Guardrails).
- **"Which vendor offers commercial PI defense?"** → `06_tools_and_vendors.md` § A2.
- **"What's an acronym I don't recognize?"** → `00_overview.md` § Glossary.

## Glossary

The full glossary lives in `00_overview.md` § Glossary, covering all canonical acronyms and term aliases (PI, IPI, GCG, PAIR, AutoDAN, TAP, Crescendo, AgentDojo, HarmBench, OWASP LLM Top 10, NIST AI 600-1, MITRE ATLAS, RSP / Preparedness / FSF, etc.). Refer there for definitions before searching the synthesis files.

## Verification & limits

- Citations resolved as of 2026-05-07.
- Status flags on entries: `Verified` means title + authors + year cross-checked against the primary source. `Unverified` means the bibkey resolves locally but no primary-source check has been run yet. `(vendor blog)` flags entries sourced from vendor blogs or press releases — treat any quantitative claims with skepticism.
- This synthesis was generated from a recreated `bib_ledger.yml` produced via `/research-gather`; some `Authors (year)` renderings are bibkey-derived heuristics (per BURN_IN Stage 2 #2). A follow-up `/dossier-audit` round would tighten verification status across entries.
- Entries marked `(post-2025; recheck)` should be re-verified before reuse.
- This synthesis is a snapshot. Vendor product pages, regulatory frameworks, and frontier-lab safety frameworks drift on a quarterly cycle — re-verify any vendor / standards / lab-framework entry before relying on its current state.
- (Audit-trail notes appear here as `**Independent audit, round N (YYYY-MM-DD):** ...` paragraphs after each `/dossier-audit` invocation.)

**Independent audit, round 1 (2026-05-07):** A complementary-scope review pass focused on
anonymous arXiv entries and Authors-via-bibkey-heuristic accuracy. Prior rounds covered
none. Findings: 0 dropped, 3 corrected, 1 flagged, 2 verified clean. Bibkey-heuristic
author rendering was wrong on three arXiv entries (first-author surname differed from
the bibkey stem); titles/URLs were correct. Recommendation: re-run with focus on
real-world incident disclosure dates and CVE numbers.

## Attribution

Synthesized from a research dossier maintained by the research_toolkit (`~/Claude/research_toolkit/`). URLs link to primary sources (arXiv, GitHub, vendor blogs, conference proceedings, HF model/dataset cards). No local file paths are referenced.

# Vol 25 Prompt Injection — Research Synthesis

<!-- AGENT-INDEX: this folder is a self-contained reference. Read this README first. -->
**Purpose:** Comprehensive synthesis of prompt-injection research designed for dual consumption — humans (interview prep, portfolio, public sharing) and agents (LLM tools needing detailed context on prompt-injection literature).
**Primary intended consumer:** future Claude Code / LLM agents that need to ground reasoning in prompt-injection literature without leaving the folder. Secondary consumers: humans reading the material directly; agents in adjacent projects; public consumers grounding their own agents.
**Self-containedness guarantee:** this folder has no hard dependence on sibling files outside itself. Move it elsewhere and it still works.
**Scope:** Adversarial prompt research, 2022–2026, with emphasis on 2024–2026.
**Coverage:** ~580 entries across 7 topic files, every entry from the source dossier preserved with structured fields (Source / Code / Mechanism / Result / Status).
**Last updated:** 2026-05-06.

## ⚠️ Scope boundary

This folder is **research-survey material**, not part of this repository's prompt-injection-detector PoC claims. The PoC is a time-boxed methodology artifact (see `../../CLAUDE.md` "Project Frame"). Do not infer that the PoC implements anything described in this folder.

## How this is organized

| File | Topic | When to read |
|---|---|---|
| `00_overview.md` | Threat model, taxonomy, timeline, glossary | Start here if new to the area |
| `01_direct_attacks.md` | Hand-crafted, encoding, white/black-box optimization | Looking up an attack technique |
| `02_indirect_and_agentic_attacks.md` | Indirect PI, RAG, agent hijacking, multimodal, computer-use | Tool-using / agent threat models |
| `03_defenses.md` | Detection, smoothing, architectural, latent-space, alignment | Designing or evaluating a defense |
| `04_training_time_threats.md` | Backdoors, poisoning, extraction, MIA, model stealing | Training-pipeline / supply-chain risk |
| `05_datasets_and_benchmarks.md` | HarmBench, JailbreakBench, AdvBench, leaderboards, CTFs | Picking an eval suite or red-team venue |
| `06_tools_and_vendors.md` | OSS tools, commercial vendors, eval SaaS | Tooling / vendor landscape |
| `07_standards_and_industry.md` | OWASP, NIST, MITRE, EU AI Act, lab frameworks | Compliance / governance / regulatory context |

## Lookup recipes

Routes by question type. Each points to a specific file and section anchor.

- **"What's the foundational paper for direct prompt injection?"** → `01_direct_attacks.md` § A1 (Perez & Ribeiro 2022, *"Ignore Previous Prompt"*).
- **"What's the canonical reference for indirect prompt injection?"** → `02_indirect_and_agentic_attacks.md` § B1 (Greshake et al. 2023).
- **"What's the canonical reference for white-box jailbreaks?"** → `01_direct_attacks.md` § A4 (GCG, Zou et al. 2023).
- **"What multi-turn jailbreak should I know about?"** → `01_direct_attacks.md` § A2 (Crescendo, Russinovich/Microsoft 2024).
- **"What's the canonical RAG-poisoning attack?"** → `02_indirect_and_agentic_attacks.md` § B1 (PoisonedRAG, Zou et al. 2024).
- **"What's the canonical multimodal/VLM jailbreak?"** → `02_indirect_and_agentic_attacks.md` § B3 (Visual Adversarial Examples, Qi et al. 2023).
- **"What's the computer-use / browser-agent attack landscape?"** → `02_indirect_and_agentic_attacks.md` § B4 (WASP, AdvWeb, AdInject, Chameleon, BrowseSafe).
- **"What's the canonical Anthropic alignment paper?"** → `03_defenses.md` § C5 (Constitutional AI, Bai et al. 2022).
- **"What benchmark should I use to evaluate a jailbreak defense?"** → `05_datasets_and_benchmarks.md` § Datasets — Jailbreak/Harm Evaluation (HarmBench + JailbreakBench + StrongREJECT judge).
- **"What's the best open-source safety classifier?"** → `03_defenses.md` § C1 + `06_tools_and_vendors.md` § OSS-classifiers (Llama Guard 3/4, ShieldGemma 2, WildGuard).
- **"What does OWASP say about prompt injection?"** → `07_standards_and_industry.md` § Standards Frameworks → OWASP LLM Top 10 (LLM01).
- **"What's the strongest published defense currently?"** → `03_defenses.md` § C3 (Architectural — Spotlighting, CaMeL, Instruction Hierarchy) and § C1 (Constitutional Classifiers).
- **"What's the best agentic-tool benchmark?"** → `05_datasets_and_benchmarks.md` § Datasets-D Agentic (AgentDojo, AgentHarm).
- **"What's a real-world prompt-injection CVE?"** → `02_indirect_and_agentic_attacks.md` § B1 (EchoLeak / CVE-2025-32711).
- **"What's the vendor landscape for runtime AI security?"** → `06_tools_and_vendors.md` § Commercial vendors + § Tool selection by deployment shape.
- **"How do I avoid AdvBench overfitting?"** → `05_datasets_and_benchmarks.md` § Eval stack recommendations + `03_defenses.md` § C6 (StrongREJECT judge, adaptive methodology).
- **"What red-team CTFs can I participate in?"** → `05_datasets_and_benchmarks.md` § CTFs (Lakera Gandalf, Anthropic Bug Bounty, DEF CON GRT, Gray Swan Arena).
- **"What is GCG / PAIR / TAP / AutoDAN / Crescendo?"** → `00_overview.md` § Glossary.
- **"What's the compliance stack for production LLMs?"** → `07_standards_and_industry.md` § Compliance posture (NIST AI 600-1 + ISO/IEC 42001 + EU AI Act Article 15).
- **"What survived adaptive attacks?"** → `03_defenses.md` § C6 (Adaptive-attack methodology — Andriushchenko 2024, Nasr/Carlini/Tramèr et al. 2025).
- **"What's a sleeper-agent / training-time threat?"** → `04_training_time_threats.md` § D1 (Hubinger et al. 2024).

## Verification & limits

- Citations resolved as of 2026-05-06.
- Many post-2025 vendor disclosures are flagged `(unverified)` or `(vendor blog)` per the source dossier — readers and agents should apply appropriate skepticism to those entries; status flags appear inline on each affected entry.
- This synthesis is a snapshot. The field moves fast: adversarial-poetry-class attacks emerged in late 2025; agentic attacks evolve quarterly; vendor acquisition status (Lakera→Check Point, Protect AI→Palo Alto Networks, Robust Intelligence→Cisco, etc.) is accurate as of May 2026.
- Entry counts mirror the source dossier's actual tables; some dossier footers under-count their own sub-tables, so the entries-per-file figures here may differ slightly from headline numbers in the source.
- **URL freshness check (2026-05-06):** All 674 unique URLs across the collection were HEAD-checked. 95% returned 2xx; the remaining 5% are mostly bot-blocked sites (OpenAI, Microsoft) or rate-limited services (Gray Swan Arena), which are real but reject HEAD requests. A small set (~7 URLs) returned hard 404s and are flagged inline at the affected entries — primarily blog-slug drift (Lakera blog post URLs), repo-rename drift (BAP, ELBA-Bench, GenTel-Safe GitHub Pages), and the archived Biden-era White House AI Bill of Rights page (now under `bidenwhitehouse.archives.gov`).
- **Independent audit, round 1 (2026-05-06):** A separate review pass verified entries against primary sources (arXiv abstracts, vendor news, conference proceedings). No outright fabricated entries were found, but corrections were applied for: (1) six wrong author attributions on high-impact papers (Promptware Kill Chain, Adversarial Poetry, *The Attacker Moves Second*, Real AI Agents Fake Memories, *Lessons from Defending Gemini*, Jailbreaking Leaves a Trace); (2) three organization/version corrections (CaMeL is Google Research not DeepMind; arXiv:2407.21783 is the Llama 3 Herd paper, with Llama Guard 3 as a component; AILuminate paper introduces v1.0 with v1.1 in release notes); (3) five quantitative claims that the source dossier had imported but that don't appear in the cited papers' abstracts were dropped or generalized rather than asserted (Constitutional Classifiers "0.005/1000" rate, AgentHarm "104 tools" figure, PoisonedRAG per-dataset ASR breakdown, JailbreakBench misuse/benign split, Universal Jailbreak Backdoors specific poisoning percentage); (4) ~25 anonymous-attribution entries had real authors filled in; (5) vendor acquisition entries gained specific dates and dollar amounts where confirmed by news sources. Per the author's preference, accuracy was prioritized over completeness — quantitative specifics not in the abstract were dropped rather than asserted.
- **Independent audit, round 2 (2026-05-06):** A complementary-scope review pass focused on what round 1 explicitly didn't reach — tool version numbers in `06`, glossary entries in `00`, OWASP / EU AI Act / MITRE ATLAS specifics in `07`, C2 perturbation/smoothing entries in `03`, D6 training-time defenses in `04`, cross-file consistency, Datasets-G memorization sizes, plus C1 entries marked Verified in round 1 but not directly fetched. All 13 OSS tool versions in `06` cross-checked against PyPI / GitHub Releases (~10/13 within tolerance, 3 generalized). MITRE ATLAS reference updated from stale v5.4 (Feb 2026) to v5.6 (May 2026) and stale specific counts removed in favor of pointing to the live release page. EU AI Act Article 15 summary corrected to enumerate all five named threats (data poisoning, **model poisoning**, adversarial examples, model evasion, confidentiality attacks). PyRIT URL standardized to `microsoft/PyRIT` across files. Three vendor-marketing-grade specific numbers (TrojAI throughput, Lasso Security accuracy/breadth, Repello AI attack-pattern count) replaced with general descriptions because they are vendor-published and not independently verifiable. DPP and AutoDefense mechanism descriptions generalized to abstract-supported wording. No entries were dropped (all 499 5-bullet entries across `01–06` retained). Round 2 verified an additional ~50 entries against primary sources (full list preserved in chat audit-report).
- **Independent audit, round 3 (2026-05-06):** A long-tail review pass sampling 70+ mid-tier entries across A3 encoding, A4 white-box, A5 black-box, B1/B2/B3 indirect-agentic-multimodal, C3 architectural, C4 latent-space, D2 poisoning, D4 MIA, Datasets-A/B/F, and the Anthropic/Apollo/HiddenLayer industry reports. Five CORRECT findings applied: StructuralSleight mechanism (UTOS templates, not "discrete optimization"); Image Hijacks ASR (>80% per abstract, not >90%); Operationalizing CaMeL authors (Tallam & Miller, not Bagdasarian); Best-of-Venom poison rate (1–5% per abstract, not 15%); SPV-MIA acronym (Self-Prompt + Probabilistic Variation, not "specific population variance"). Seven specific quantitative claims that the audit FLAGged as plausibly-in-body-but-not-in-abstract were generalized to abstract-supported wording (MasterKey baseline, Adversarial Reasoning DeepSeek-R1 figure, Bijection Learning Claude 3.5 Sonnet figure, PRP ASR, BrowseSafe dataset/F1 specifics, GBTL drop magnitude, FSD AUC delta). Audit concluded the synthesis has converged: all sampled entries cite the right papers, mechanism summaries are mostly faithful, residual issues are body-vs-abstract numerical drift typical of converged surveys. No round 4 spawned per audit's "clean" verdict.

## Attribution

Synthesized from a research dossier maintained by the author. URLs link to primary sources (arXiv, GitHub, Hugging Face, vendor blogs, conference proceedings). No local file paths are referenced.

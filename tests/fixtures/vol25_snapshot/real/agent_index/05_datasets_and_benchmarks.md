# Datasets, Benchmarks, Leaderboards, and CTFs

<!-- AGENT-INDEX: keep this block stable; future agents read it first. -->
**Scope:** Datasets and benchmarks for evaluating prompt-injection / jailbreak attacks, defenses, and agent safety; public leaderboards; CTFs and red-team programs.
**Out of scope:** Attack/defense research papers — see `01_direct_attacks.md` through `04_training_time_threats.md`. Tools — see `06_tools_and_vendors.md`.
**Coverage window:** 2020–2026 (datasets); through 2026 (leaderboards / CTFs).
**Last updated:** 2026-05-06.
**Subsections (stable anchors):** Datasets-A jailbreak/harm · Datasets-B safety/trust suites · Datasets-C PI-specific · Datasets-D agentic · Datasets-E multimodal · Datasets-F specialized · Datasets-G memorization/privacy · Datasets-H hallucination/truthfulness · Leaderboards · CTFs · Eval stack recommendations.
**Key terms covered:** AdvBench, HarmBench, JailbreakBench/JBB-Behaviors, JailBreakV-28K, JailbreakHub, ForbiddenQuestions, WildJailbreak, WildGuardMix, DoNotAnswer, ToxicChat, BeaverTails, PKU-SafeRLHF, RealToxicityPrompts, TDC 2023, TrustLLM, DecodingTrust, SafetyBench, HH-RLHF, Anthropic red-team-attempts, AILuminate, HackAPrompt 1.0/2.0, Open-Prompt-Injection, BIPIA, PINT, AgentDojo, InjecAgent, AgentHarm, WASP, Agent-SafetyBench, PLeak, MM-SafetyBench, VHELM, RTVLM, MultiTrust, WMDP, CoSafe, SC-Safety, CHiSafetyBench, PromptBench/PromptRobust, StrongREJECT, SALAD-Bench, XSTest, SimpleSafetyTests, WikiMIA, LLM-PBE Enron-Email, TOFU, Pile-CC, TruthfulQA, HalluLens, HaluEval, FActScore, Lakera Gandalf, Anthropic Bug Bounty, DEF CON GRT, Microsoft AI Bug Bounty, Gray Swan Arena, Prompt Airlines, Doublespeak, LLM CTF @ SaTML, HackerOne AIxCC.
**Related files:** `03_defenses.md` (C6 adaptive methodology), `06_tools_and_vendors.md` (eval harnesses).

## Topic overview

This file enumerates the dataset, benchmark, leaderboard, and CTF surface for LLM safety and adversarial-robustness research. The 2024 wave of standardized benchmarks (HarmBench, JailbreakBench, AgentDojo, AgentHarm) is the substrate every adaptive-attack and defense paper now reports against.

If forced to pick exactly three datasets — one classification, one open-ended generation, one agentic — the dossier-recommended stack is **WildGuardMix + HarmBench/StrongREJECT + AgentDojo**. WildGuardMix gives 92K labeled prompt/response pairs across 13 risk categories with explicit harmful/benign/refusal labels and multi-task design — the strongest open alternative to proprietary moderation APIs. HarmBench + StrongREJECT covers open-ended generation: HarmBench's 510 behaviors give breadth (standard / contextual / multimodal) and StrongREJECT's rubric-based or fine-tuned judge fixes the inflated-ASR bug that plagued AdvBench-style refusal-string evaluation. AgentDojo's 629 injected test cases cover the indirect-PI threat that defines real production agent risk in 2026.

The CTF surface is more active than the academic paper count suggests. Lakera Gandalf, Anthropic's Model Safety Bug Bounty (CC++), DEF CON AI Village GRT, Gray Swan Arena, HackAPrompt 2.0, and Prompt Airlines are continuously running adversarial-testing programs with live cash prizes; each is enumerated below with status as of May 2026.

## Datasets — A. Jailbreak / Harm Evaluation

`#datasets-jailbreak-harm`

The core jailbreak / harm-evaluation datasets. These are the substrates papers in `01_direct_attacks.md` and `03_defenses.md` measure against.

### Entries

- **AdvBench** — Zou et al. (CMU+Google, 2023).
  - **Source:** https://arxiv.org/abs/2307.15043
  - **Code:** https://github.com/llm-attacks/llm-attacks
  - **Mechanism:** 520 harmful behaviors + 500 strings (~1,000 total). CSV schema: `goal`, `target`. GCG attack target set.
  - **Result:** Foundational AdvBench dataset; widely overfitted to. Pair with StrongREJECT judge to avoid inflated ASR.
  - **Status:** Verified. Mirror at https://huggingface.co/datasets/walledai/AdvBench. License: MIT.

- **HarmBench** — Mazeika, Phan, Yin, Zou et al. (CAIS, 2024), *ICML 2024*.
  - **Source:** https://arxiv.org/abs/2402.04249
  - **Code:** https://github.com/centerforaisafety/HarmBench
  - **Mechanism:** 510 behaviors × 7 categories with standard / contextual / multimodal splits.
  - **Result:** Reference benchmark for the adaptive-attack era; ships HarmBench-Mistral-7b-val-cls judge model.
  - **Status:** Verified. Mirror at https://huggingface.co/datasets/walledai/HarmBench. License: MIT. → Also see `03_defenses.md` §§ C1, C5, C6.

- **JailbreakBench / JBB-Behaviors** — Chao, Debenedetti, Robey et al. (2024), *NeurIPS 2024 D&B*.
  - **Source:** https://arxiv.org/abs/2404.01318
  - **Code:** https://github.com/JailbreakBench/jailbreakbench
  - **Mechanism:** 100 behaviors plus jailbreak artifacts; 10 OpenAI-policy categories. (The dataset card carries a misuse/benign split that the body documents.)
  - **Result:** Open robustness benchmark with continuous PR-driven leaderboard.
  - **Status:** Verified. HF: https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors. License: MIT. → Also see `03_defenses.md` § C6.

- **JailBreakV-28K** — Luo et al. (2024), *COLM 2024*.
  - **Source:** https://arxiv.org/abs/2404.03027
  - **Code:** https://github.com/EddyLuo1232/JailBreakV_28K
  - **Mechanism:** 28K text-image pairs (20K text + 8K image); 16 safety policies × 5 attack types.
  - **Result:** Large-scale multimodal jailbreak benchmark.
  - **Status:** Verified. HF: https://huggingface.co/datasets/JailbreakV-28K/JailBreakV-28k. License: MIT. → Also see Datasets-E.

- **JailbreakHub / In-the-Wild Prompts** — Shen et al. (TrustAIRLab, 2024), *ACM CCS 2024*.
  - **Source:** https://arxiv.org/abs/2308.03825
  - **Code:** https://github.com/verazuo/jailbreak_llms
  - **Mechanism:** 15,140 prompts (1,405 jailbreaks) collected Dec 2022 – Dec 2023 from Reddit / Discord / web sources.
  - **Result:** Largest empirical in-the-wild jailbreak corpus.
  - **Status:** Verified. HF: https://huggingface.co/datasets/TrustAIRLab/in-the-wild-jailbreak-prompts. License: MIT.

- **ForbiddenQuestions** — Shen et al. (2023).
  - **Source:** https://arxiv.org/abs/2308.03825
  - **Code:** https://github.com/verazuo/jailbreak_llms
  - **Mechanism:** 390 questions × 13 OpenAI-policy scenarios; GPT-template-expanded.
  - **Result:** Refusal-rate evaluation companion to JailbreakHub.
  - **Status:** Verified. HF path `TrustAIRLab/forbidden_question_set` plausible but not directly verified. License: MIT.

- **WildJailbreak** — AI2 / Jiang et al. (2024).
  - **Source:** https://arxiv.org/abs/2406.18510
  - **Code:** —
  - **Mechanism:** 262K pairs plus adversarial eval (210 benign + 2,000 harmful); vanilla-vs-adversarial × harmful-vs-benign quadrants.
  - **Result:** Synthetic-data jailbreak dataset for fine-tuning safety models.
  - **Status:** Verified. HF: https://huggingface.co/datasets/allenai/wildjailbreak. License: ODC-BY (gated).

- **WildGuardMix** — AI2 / Han et al. (2024), *NeurIPS 2024 D&B*.
  - **Source:** https://arxiv.org/abs/2406.18495
  - **Code:** —
  - **Mechanism:** 92K pairs (Train 87K + Test 5,299); multi-task moderation — prompt harm + response harm + refusal.
  - **Result:** Strongest open alternative to proprietary moderation APIs.
  - **Status:** Verified. HF: https://huggingface.co/datasets/allenai/wildguardmix. License: ODC-BY (gated). → Also see `03_defenses.md` § C1.

- **DoNotAnswer** — Wang et al. (LibrAI, 2023), *EACL Findings 2024*.
  - **Source:** https://arxiv.org/abs/2308.13387
  - **Code:** https://github.com/Libr-AI/do-not-answer
  - **Mechanism:** 939 prompts × 5 risk areas / 12 harm types.
  - **Result:** Refusal-rate evaluation; widely used as a model-conservatism benchmark.
  - **Status:** Verified. HF path `LibrAI/do-not-answer` plausible; Japanese mirror confirmed at `kunishou/do-not-answer-ja`. License: CC-BY-NC-SA 4.0.

- **ToxicChat** — Lin et al. (LMSYS / UCSD, 2023), *EMNLP Findings 2023*.
  - **Source:** https://arxiv.org/abs/2310.17389
  - **Code:** —
  - **Mechanism:** ~10K real Vicuna-demo queries with `user_input`, `toxicity`, `jailbreaking` labels.
  - **Result:** Real-traffic toxicity reference dataset; versioned (e.g., 0124).
  - **Status:** Verified. HF: https://huggingface.co/datasets/lmsys/toxic-chat. License: CC-BY-NC 4.0. → Also see `03_defenses.md` § C1.

- **BeaverTails** — PKU-Alignment / Ji et al. (2023), *NeurIPS 2023 D&B*.
  - **Source:** https://arxiv.org/abs/2307.04657
  - **Code:** https://github.com/PKU-Alignment/beavertails
  - **Mechanism:** 333K+ QA pairs × 14 harm-category labels; companion BeaverTails-Evaluation set (700).
  - **Result:** Foundational decoupled-help/harm annotation dataset.
  - **Status:** Verified. HF: https://huggingface.co/datasets/PKU-Alignment/BeaverTails. License: CC-BY-NC 4.0. → Also see `03_defenses.md` § C5.

- **PKU-SafeRLHF** — PKU-Alignment (2024).
  - **Source:** https://arxiv.org/abs/2406.15513
  - **Code:** https://github.com/PKU-Alignment/safe-rlhf
  - **Mechanism:** 83.4K dual + 166.8K total preferences; 265K QA across 19 harm categories × 3 severity levels.
  - **Result:** Multi-level safety preference dataset; successor to BeaverTails.
  - **Status:** Verified. HF dataset path under PKU-Alignment org (canonical PKU-SafeRLHF datasets on HF redirect through the org page). License: CC-BY-NC 4.0. → Also see `03_defenses.md` § C5.

- **RealToxicityPrompts** — Gehman et al. (AI2, 2020), *EMNLP Findings 2020*.
  - **Source:** https://arxiv.org/abs/2009.11462
  - **Code:** https://github.com/allenai/real-toxicity-prompts
  - **Mechanism:** 99,442 web prompts paired with toxicity scores.
  - **Result:** Pre-LLM-era toxic-continuation standard; still used as a baseline.
  - **Status:** Verified. HF: https://huggingface.co/datasets/allenai/real-toxicity-prompts. License: Apache-2.0.

- **TDC 2023 (Trojan + Red Team)** — CAIS / Mazeika et al. (2023), *NeurIPS 2023 competition*.
  - **Source:** https://trojandetection.ai/
  - **Code:** https://github.com/centerforaisafety/tdc2023-starter-kit
  - **Mechanism:** Two-track competition: Red Team (50 dev / 50 test × Llama-2-7B / Vicuna) and Trojan (1,000 trojaned LLMs).
  - **Result:** Foundational red-team competition dataset.
  - **Status:** Verified. License: MIT.

## Datasets — B. Safety / Trust Suites

`#datasets-safety-trust`

Multi-dimensional safety benchmarks that evaluate trustworthiness across multiple axes (helpfulness, harmlessness, honesty, fairness, privacy).

### Entries

- **TrustLLM** — Sun, Huang et al. (Lehigh + 70 co-authors, 2024), *ICML 2024*.
  - **Source:** https://arxiv.org/abs/2401.05561
  - **Code:** https://github.com/HowieHwong/TrustLLM
  - **Mechanism:** 30+ datasets, 18 sub-categories, across 6 trust dimensions.
  - **Result:** Multi-dimensional trust benchmark; widely cited.
  - **Status:** Verified. HF: https://huggingface.co/datasets/TrustLLM/TrustLLM-dataset. License: MIT.

- **DecodingTrust** — Wang, Li, Xie et al. (UIUC + Microsoft, 2023), *NeurIPS 2023 Outstanding Benchmark*.
  - **Source:** https://arxiv.org/abs/2306.11698
  - **Code:** https://github.com/AI-secure/DecodingTrust
  - **Mechanism:** 8 perspective tracks, ~33 sub-evaluations across toxicity / bias / adversarial-robustness / OOD / demos / privacy / ethics / fairness.
  - **Result:** Foundational comprehensive trust benchmark.
  - **Status:** Verified. License: CC-BY-SA 4.0.

- **SafetyBench** — Zhang, Lei, Wu et al. (THU-CoAI, 2024), *ACL 2024*.
  - **Source:** https://arxiv.org/abs/2309.07045
  - **Code:** https://github.com/thu-coai/SafetyBench
  - **Mechanism:** 11,435 multiple-choice questions × 7 categories; bilingual (zh/en).
  - **Result:** Multiple-choice safety benchmark with strong cross-lingual coverage.
  - **Status:** Verified. HF: https://huggingface.co/datasets/thu-coai/SafetyBench. License: Apache-2.0.

- **Anthropic HH-RLHF** — Bai, Kadavath et al. (Anthropic, 2022).
  - **Source:** https://arxiv.org/abs/2204.05862
  - **Code:** https://github.com/anthropics/hh-rlhf
  - **Mechanism:** ~170K helpfulness/harmlessness preferences across helpful-base / online / rejection-sampled / harmless-base splits.
  - **Result:** Foundational HH preference dataset for RLHF training.
  - **Status:** Verified. HF: https://huggingface.co/datasets/Anthropic/hh-rlhf. License: MIT. → Also see `03_defenses.md` § C5.

- **Anthropic red-team-attempts** — Ganguli, Lovitt et al. (2022).
  - **Source:** https://arxiv.org/abs/2209.07858
  - **Code:** —
  - **Mechanism:** 38,961 multi-turn red-team transcripts with `min_harmlessness_score` and `num_params` annotations.
  - **Result:** Foundational red-team-transcript dataset for HH research.
  - **Status:** Verified. HF: https://huggingface.co/datasets/Anthropic/hh-rlhf (red-team subdir). License: MIT.

- **AILuminate v1.0** — MLCommons AI Safety Working Group (2024–2025).
  - **Source:** https://arxiv.org/abs/2503.05731
  - **Code:** https://github.com/mlcommons/ailuminate
  - **Mechanism:** Practice (~12K public) + private Test (~12K) across 12 hazard categories; safety grades Poor → Excellent.
  - **Result:** First MLCommons-grade safety benchmark with public leaderboard. The arXiv paper introduces v1.0; v1.1 release notes cited separately on the MLCommons site.
  - **Status:** Verified. License: CC-BY (DEMO Practice subset).

## Datasets — C. Prompt Injection Specific

`#datasets-pi-specific`

Datasets purpose-built for prompt-injection evaluation.

### Entries

- **HackAPrompt 1.0 dataset** — Schulhoff et al. (Learn Prompting / UMD, 2023), *EMNLP 2023 Best Theme*.
  - **Source:** https://arxiv.org/abs/2311.16119
  - **Code:** https://github.com/PromptLabs/hackaprompt
  - **Mechanism:** ~600K prompts; ~67.6K curated. 10 levels × 3 LLMs; 29-technique taxonomy.
  - **Result:** Largest competition-derived prompt-hacking dataset.
  - **Status:** Verified. HF: https://huggingface.co/datasets/hackaprompt/hackaprompt-dataset. License: MIT. → Also see `01_direct_attacks.md` § A1, § CTFs.

- **Open-Prompt-Injection** — Liu, Jia, Geng et al. (2024), *USENIX Security 2024*.
  - **Source:** https://arxiv.org/abs/2310.12815
  - **Code:** https://github.com/liu00222/Open-Prompt-Injection
  - **Mechanism:** 5 attacks × 10 defenses × 7 tasks × 10 LLMs; toolkit (not a static dataset).
  - **Result:** Reference toolkit for PI benchmarking.
  - **Status:** Verified. License: MIT. → Also see `01_direct_attacks.md` § A1, `02_indirect_and_agentic_attacks.md` § B1, `03_defenses.md` § C3.

- **BIPIA** — Yi et al. (Microsoft, 2023), *KDD 2025*.
  - **Source:** https://arxiv.org/abs/2312.14197
  - **Code:** https://github.com/microsoft/BIPIA
  - **Mechanism:** ~150K cases × 5 task domains (Email / WebQA / TableQA / Summarization / CodeQA); bilingual (en/zh).
  - **Result:** First broad indirect-PI benchmark.
  - **Status:** Verified. License: MIT. → Also see `01_direct_attacks.md` § A1, `02_indirect_and_agentic_attacks.md` § B1, `03_defenses.md` § C3.

- **PINT (Prompt Injection Test)** — Lakera AI (2024), *Lakera blog*.
  - **Source:** https://www.lakera.ai/blog (PINT benchmark blog index — direct pint-benchmark slug returns 404 as of May 2026)
  - **Code:** https://github.com/lakeraai/pint-benchmark
  - **Mechanism:** 4,314 inputs (3,016 en + 1,298 non-en); held-out by design.
  - **Result:** Held-out PI benchmark to prevent overfitting; framework public, dataset proprietary.
  - **Status:** Verified — framework MIT; dataset intentionally private.

## Datasets — D. Agentic

`#datasets-agentic`

Datasets specifically targeting tool-using LLM agents.

### Entries

- **AgentDojo** — Debenedetti et al. (ETH SpyLab, 2024), *NeurIPS 2024 D&B*.
  - **Source:** https://arxiv.org/abs/2406.13352
  - **Code:** https://github.com/ethz-spylab/agentdojo
  - **Mechanism:** 97 tasks + 629 security cases across email / banking / Slack / travel environments.
  - **Result:** The de-facto agentic adaptive-evaluation harness.
  - **Status:** Verified. License: AGPL-3.0. → Also see `02_indirect_and_agentic_attacks.md` § B2, `03_defenses.md` § C6.

- **InjecAgent** — Zhan, Liang et al. (UIUC, 2024), *ACL Findings 2024*.
  - **Source:** https://arxiv.org/abs/2403.02691
  - **Code:** https://github.com/uiuc-kang-lab/InjecAgent
  - **Mechanism:** 1,054 cases × 17 user × 62 attacker tools; direct-harm + data-exfiltration.
  - **Result:** First tool-use indirect-PI benchmark.
  - **Status:** Verified. License: MIT. → Also see `02_indirect_and_agentic_attacks.md` § B2.

- **AgentHarm** — Andriushchenko et al. (Gray Swan + UK AISI, 2024), *ICLR 2025*.
  - **Source:** https://arxiv.org/abs/2410.09024
  - **Code:** —
  - **Mechanism:** 110 base scenarios → 440 augmented across 11 harm categories; tool-call traces.
  - **Result:** First agentic-harmfulness benchmark with category-level breakdowns.
  - **Status:** Verified. HF: https://huggingface.co/datasets/ai-safety-institute/AgentHarm. License: MIT (gated). → Also see `02_indirect_and_agentic_attacks.md` § B2.

- **WASP** — Evtimov et al. (Meta FAIR, 2025), *NeurIPS D&B*.
  - **Source:** https://arxiv.org/abs/2504.18575
  - **Code:** https://github.com/facebookresearch/wasp
  - **Mechanism:** Realistic VWA-based web-agent hijack scenarios.
  - **Result:** Up to 86% partial-success ASR.
  - **Status:** Verified. License: CC-BY-NC 4.0. → Also see `02_indirect_and_agentic_attacks.md` §§ B2, B4.

- **Agent-SafetyBench** — Zhang, Cui et al. (THU-CoAI, 2024).
  - **Source:** https://arxiv.org/abs/2412.14470
  - **Code:** https://github.com/thu-coai/Agent-SafetyBench
  - **Mechanism:** 2,000 cases × 349 environments; 8 risk × 10 failure-mode categories.
  - **Result:** None of 16 evaluated agents reach 60% safety.
  - **Status:** Verified. HF: https://huggingface.co/datasets/thu-coai/Agent-SafetyBench. License: Apache-2.0. → Also see `02_indirect_and_agentic_attacks.md` § B2.

- **PLeak** — Hui et al. (2024), *ACM CCS 2024*.
  - **Source:** https://arxiv.org/abs/2405.06823
  - **Code:** https://github.com/BHui97/PLeak
  - **Mechanism:** Optimization framework + corpus for system-prompt extraction.
  - **Result:** 68% recovery on Poe-hosted apps.
  - **Status:** Verified. License: MIT. → Also see `02_indirect_and_agentic_attacks.md` § B1.

## Datasets — E. Multimodal

`#datasets-multimodal`

Datasets for multimodal (image, audio, video) safety evaluation.

### Entries

- **MM-SafetyBench** — Liu et al. (2024), *ECCV 2024*.
  - **Source:** https://arxiv.org/abs/2311.17600
  - **Code:** https://github.com/isXinLiu/MM-SafetyBench
  - **Mechanism:** 5,040 text-image pairs × 13 scenarios; query-relevant image attacks.
  - **Result:** Foundational multimodal safety benchmark.
  - **Status:** Verified. License: Apache-2.0. → Also see `02_indirect_and_agentic_attacks.md` § B3.

- **VHELM (safety subset)** — Lee, Bommasani et al. (Stanford CRFM, 2024).
  - **Source:** https://arxiv.org/abs/2410.07112
  - **Code:** https://github.com/stanford-crfm/helm
  - **Mechanism:** 21 datasets × 9 aspects; safety / toxicity / bias / robustness as 4 of 9.
  - **Result:** Holistic VLM evaluation framework with safety subset.
  - **Status:** Verified. License: Apache-2.0.

- **RTVLM (Red-Team VLM)** — Li et al. (2024), *ACL Findings 2024*.
  - **Source:** https://arxiv.org/abs/2401.12915
  - **Code:** —
  - **Mechanism:** 12 subtasks × 4 aspects; first red-team VLM dataset.
  - **Result:** Reference VLM red-team dataset.
  - **Status:** Verified arXiv ID; canonical GitHub or HuggingFace URL not verified.

- **JailBreakV-28k (multimodal subset)** — Luo et al. (2024).
  - **Source:** https://arxiv.org/abs/2404.03027
  - **Code:** https://github.com/EddyLuo1232/JailBreakV_28K
  - **Mechanism:** 8K image-based attacks (subset of full JailBreakV-28k).
  - **Result:** Nature / Random / Typography / SD / Blank attack categories.
  - **Status:** Verified. License: MIT. → See Datasets-A for the full corpus.

- **MultiTrust** — Zhang et al. (Tsinghua + RealAI, 2024), *NeurIPS 2024 D&B*.
  - **Source:** https://arxiv.org/abs/2406.07057
  - **Code:** https://github.com/thu-ml/MMTrustEval
  - **Mechanism:** 32 tasks × 21 MLLMs; truthfulness / safety / robustness / fairness / privacy.
  - **Result:** 5-axis multimodal trust benchmark.
  - **Status:** Verified. HF: https://huggingface.co/datasets/thu-ml/MultiTrust. License: Apache-2.0. → Also see `02_indirect_and_agentic_attacks.md` § B3.

## Datasets — F. Specialized (regional / capability-specific)

`#datasets-specialized`

Region-specific or capability-specific safety datasets — Chinese-language safety, hazardous-knowledge unlearning, prompt robustness, refusal calibration.

### Entries

- **WMDP** — Li, Pan, Gopal et al. (CAIS + Scale, 2024), *ICML 2024*.
  - **Source:** https://arxiv.org/abs/2403.03218
  - **Code:** https://github.com/centerforaisafety/wmdp
  - **Mechanism:** 3,668 multiple-choice questions across bio / cyber / chemistry hazardous-knowledge categories.
  - **Result:** Hazardous-knowledge evaluation plus RMU unlearning benchmark.
  - **Status:** Verified. HF: https://huggingface.co/datasets/cais/wmdp and https://huggingface.co/datasets/cais/wmdp-corpora. License: MIT (filtered). → Also see `03_defenses.md` § C4, `04_training_time_threats.md` § D6.

- **CoSafe** — Yu et al. (2024), *EMNLP 2024*.
  - **Source:** https://arxiv.org/abs/2406.17626
  - **Code:** https://github.com/ErxinYu/CoSafe-Dataset
  - **Mechanism:** 1,400 multi-turn dialogues × 14 categories; coreference-based multi-turn jailbreaks.
  - **Result:** Multi-turn coreference-jailbreak dataset.
  - **Status:** Verified. License: MIT.

- **SC-Safety / SuperCLUE-Safety** — Xu et al. (CLUE, 2023).
  - **Source:** https://arxiv.org/abs/2310.05818
  - **Code:** https://www.cluebenchmarks.com/
  - **Mechanism:** 4,912 open-ended Chinese questions × 20+ sub-dimensions; multi-round adversarial Chinese safety.
  - **Result:** Reference Chinese-safety benchmark.
  - **Status:** Verified arXiv; access via cluebenchmarks.com. License: Custom CLUE.

- **CHiSafetyBench** — Zhang et al. (2024).
  - **Source:** https://arxiv.org/abs/2406.10311
  - **Code:** —
  - **Mechanism:** 1,861 MCQ + 462 risky open-ended questions; hierarchical Chinese safety: 5 areas × 31 categories.
  - **Result:** Hierarchical Chinese safety benchmark.
  - **Status:** Verified arXiv ID; GitHub / HF dataset URL not verified.

- **PromptBench / PromptRobust** — Zhu, Wang et al. (Microsoft, 2023).
  - **Source:** https://arxiv.org/abs/2306.04528 ; https://arxiv.org/abs/2312.07910
  - **Code:** https://github.com/microsoft/promptbench
  - **Mechanism:** 4,032 adversarial prompts × 13 datasets × 8 tasks (~567K).
  - **Result:** Char / word / sent / semantic attacks framework.
  - **Status:** Verified. License: MIT.

- **StrongREJECT** — Souly, Lu, Bowen et al. (Berkeley, 2024), *NeurIPS 2024 D&B*.
  - **Source:** https://arxiv.org/abs/2402.10260
  - **Code:** https://github.com/dsbowen/strong_reject
  - **Mechanism:** 313 forbidden prompts plus rubric judge.
  - **Result:** Spearman 0.90 with humans on jailbreak success — fixes inflated-ASR bug in AdvBench-style refusal-string evaluation.
  - **Status:** Verified. License: MIT.

- **SALAD-Bench** — Li, Dong et al. (OpenSafetyLab, 2024), *ACL Findings 2024*.
  - **Source:** https://arxiv.org/abs/2402.05044
  - **Code:** https://github.com/OpenSafetyLab/SALAD-BENCH
  - **Mechanism:** 21K base × 6 domains × 16 tasks × 65 categories; QA + MCQ; ships MD-Judge / MC-Judge.
  - **Result:** Comprehensive safety benchmark with companion judge models.
  - **Status:** Verified. HF: https://huggingface.co/datasets/walledai/SaladBench. License: Apache-2.0.

- **XSTest** — Röttger, Kirk, Vidgen et al. (2024), *NAACL 2024*.
  - **Source:** https://arxiv.org/abs/2308.01263
  - **Code:** https://github.com/paul-rottger/xstest
  - **Mechanism:** 250 safe (10 types) + 200 unsafe contrasts; over-refusal / exaggerated-safety evaluation.
  - **Result:** Reference benchmark for refusal-calibration / over-refusal.
  - **Status:** Verified. HF: https://huggingface.co/datasets/walledai/XSTest. License: CC-BY-4.0.

- **SimpleSafetyTests** — Vidgen, Kirk et al. (2023).
  - **Source:** https://arxiv.org/abs/2311.08370
  - **Code:** —
  - **Mechanism:** 100 prompts × 5 harm areas; smoke-test set.
  - **Result:** Lightweight smoke-test for safety regression.
  - **Status:** Verified. HF: https://huggingface.co/datasets/Bertievidgen/SimpleSafetyTests. License: CC-BY-NC-4.0.

## Datasets — G. Memorization / Privacy

`#datasets-memorization`

Datasets for memorization, MIA, and PII-extraction evaluation.

### Entries

- **WikiMIA** — Shi, Ajith, Xia et al. (2023), *ICLR 2024*.
  - **Source:** https://arxiv.org/abs/2310.16789
  - **Code:** https://github.com/swj0419/detect-pretrain-code
  - **Mechanism:** 4 length splits (32, 64, 128, 256). Label 0 = unseen, 1 = seen.
  - **Result:** Foundational MIA benchmark for LLMs.
  - **Status:** Verified. HF: https://huggingface.co/datasets/swj0419/WikiMIA. License: MIT. → Also see `04_training_time_threats.md` § D4.

- **LLM-PBE Enron-Email** — LLM-PBE consortium / Li et al. (2024), *VLDB*.
  - **Source:** https://arxiv.org/abs/2408.12065
  - **Code:** —
  - **Mechanism:** ~500K Enron emails; 4K train / 2K attack splits.
  - **Result:** PII extraction (email / phone / name).
  - **Status:** Verified. HF: https://huggingface.co/datasets/LLM-PBE/enron-email. License: per Enron license.

- **TOFU** — Maini, Feng, Schwarzschild et al. (2024), *COLM 2024*.
  - **Source:** https://arxiv.org/abs/2401.06121
  - **Code:** https://github.com/locuslab/tofu
  - **Mechanism:** 200 fictitious authors × 20 QA pairs = 4,000 examples; forget / retain / real-authors / world-facts splits.
  - **Result:** Reference unlearning benchmark.
  - **Status:** Verified. HF: https://huggingface.co/datasets/locuslab/TOFU. License: MIT. → Also see `04_training_time_threats.md` § D6.

- **Pile-CC** — EleutherAI (Pile component, 2020).
  - **Source:** https://arxiv.org/abs/2101.00027
  - **Code:** https://github.com/EleutherAI/the-pile
  - **Mechanism:** ~227 GB CommonCrawl subset; standard for "training-data extraction" experiments.
  - **Result:** Reference training-corpus subset for extraction research.
  - **Status:** Verified. Mirror at https://huggingface.co/datasets/monology/pile-uncopyrighted. License: MIT (toolkit); per-source content.

## Datasets — H. Hallucination / Truthfulness (related)

`#datasets-hallucination`

Adjacent rather than central to prompt injection, but routinely co-evaluated.

### Entries

- **TruthfulQA** — Lin, Hilton, Evans (Oxford + OpenAI, 2022), *ACL 2022*.
  - **Source:** https://arxiv.org/abs/2109.07958
  - **Code:** https://github.com/sylinrl/TruthfulQA
  - **Mechanism:** 817 questions × 38 categories; MC1 / MC2 / generation modes.
  - **Result:** Reference truthfulness benchmark.
  - **Status:** Verified. HF: https://huggingface.co/datasets/truthfulqa/truthful_qa. License: Apache-2.0.

- **HalluLens** — Bang et al. (Meta FAIR, 2025), *ACL 2025*.
  - **Source:** https://arxiv.org/abs/2504.17550
  - **Code:** https://github.com/facebookresearch/HalluLens
  - **Mechanism:** 3 dynamic extrinsic tasks; dynamic test generation prevents leakage.
  - **Result:** Leakage-resistant hallucination benchmark.
  - **Status:** Verified. License: CC-BY-NC 4.0.

- **HaluEval** — Li et al. (RUC AI Box, 2023), *EMNLP 2023*.
  - **Source:** https://arxiv.org/abs/2305.11747
  - **Code:** https://github.com/RUCAIBox/HaluEval
  - **Mechanism:** 5K queries + 30K examples (QA / dialogue / summarization); hallucinated-vs-correct pairs.
  - **Result:** Reference hallucination-detection dataset.
  - **Status:** Verified. License: MIT.

- **FActScore** — Min et al. (UW + Meta, 2023), *EMNLP 2023*.
  - **Source:** https://arxiv.org/abs/2305.14251
  - **Code:** https://github.com/shmsw25/FActScore
  - **Mechanism:** Atomic-fact decomposition; long-form factuality metric.
  - **Result:** Reference long-form factuality metric.
  - **Status:** Verified. License: MIT.

## Leaderboards

`#leaderboards`

Public leaderboards tracking model performance on safety / adversarial-robustness benchmarks.

### Entries

- **JailbreakBench Leaderboard** — Chao et al. consortium.
  - **Source:** https://jailbreakbench.github.io/
  - **Mechanism:** Attack/defense ASR on JBB-Behaviors vs Llama-2-7B / Vicuna-13B / GPT-3.5 / 4. Continuous PR-driven refresh.
  - **Result:** Active community leaderboard; PAIR, GCG, prompt-RS variants surface near top.
  - **Status:** Verified.

- **HarmBench Leaderboard** — CAIS.
  - **Source:** https://harmbench.org/
  - **Mechanism:** 18 attacks × 33 models on 510 behaviors; periodic CAIS-curated refresh.
  - **Result:** GCG / PAIR / AutoDAN / TAP near top; Llama-3 + R2D2 most robust.
  - **Status:** Verified.

- **TrustLLM Leaderboard** — Lehigh consortium.
  - **Source:** https://trustllmbenchmark.github.io/TrustLLM-Website/leaderboard.html
  - **Mechanism:** 6 trust dimensions × 18 sub-categories.
  - **Result:** Closed APIs (GPT-4, Claude) generally lead; periodic refresh.
  - **Status:** Verified.

- **AILuminate Public** — MLCommons.
  - **Source:** https://ailuminate.mlcommons.org/benchmarks
  - **Mechanism:** 12 hazard categories × English (with fr/zh/hi rolling out); quarterly refresh.
  - **Result:** Top closed models = "Excellent"; many open models in "Good"–"Fair" range.
  - **Status:** Verified.

- **Gray Swan Arena** — Gray Swan AI.
  - **Source:** https://app.grayswan.ai/arena/leaderboard/global
  - **Mechanism:** Per-challenge: agent red-team, multimodal, indirect PI, safeguards. Continuous live competition.
  - **Result:** Per-challenge sub-leaderboards; cash prizes drive participation.
  - **Status:** Verified.

- **LMSYS / LMArena Chatbot Arena** — LMArena.
  - **Source:** https://lmarena.ai/
  - **Mechanism:** Crowdsourced pairwise human-preference Elo. Continuous refresh.
  - **Result:** Claude 4-class, Gemini 3-class, GPT-class clustered ~1,490–1,505 Elo as of mid-2026.
  - **Status:** Verified.

- **AgentDojo Results** — ETH SpyLab.
  - **Source:** https://agentdojo.spylab.ai/results
  - **Mechanism:** Utility + targeted-attack on 97 tasks × 629 variants. Periodic refresh.
  - **Result:** GPT-4o + Claude 3.5 Sonnet at top of utility; both vulnerable to PI.
  - **Status:** Verified.

- **HF Open LLM Leaderboard v2 (archived)** — Hugging Face.
  - **Source:** https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard
  - **Mechanism:** MMLU-Pro, IFEval, BBH, MUSR, MATH, GPQA. Frozen/retired 2025.
  - **Result:** Archive only; tasks no longer updated.
  - **Status:** Verified — frozen.

- **DEF CON AI Village CTF** — AI Village (DEF CON).
  - **Source:** https://aivillage.org/
  - **Mechanism:** GRT-1 (2023), GRT-2 (2024), GRT-3 (2025). Annual.
  - **Result:** GRT-1 attracted 2,244 hackers / 17K attempts / 8 LLMs.
  - **Status:** Verified.

## CTFs / Public Red-Team Programs

`#ctfs`

Live CTFs and public red-team programs for hands-on adversarial testing.

### Entries

- **Lakera Gandalf** — Lakera.
  - **Source:** https://gandalf.lakera.ai/
  - **Mechanism:** 7 standard levels + Adventures (Reverse / Misinformation / Summarizer) + adaptive Level 8.
  - **Result:** Open / no signup; **active** as of May 2026; anchor data for the GandalfTheRed paper.
  - **Status:** Verified.

- **Anthropic Model Safety Bug Bounty** — Anthropic (HackerOne).
  - **Source:** https://www.anthropic.com/news/testing-our-safety-defenses-with-a-new-bug-bounty-program
  - **Mechanism:** Universal-jailbreak finding bounties; targets Constitutional Classifiers + ASL-3 Deployment Safeguards.
  - **Result:** Vetted access; up to $25–26K per universal jailbreak. Feb 2025 expansion paid out $55K.
  - **Status:** Verified — active.

- **DEF CON AI Village GRT** — AI Village + Humane Intelligence + NIST/CISA.
  - **Source:** https://aivillage.org/
  - **Mechanism:** In-person CTF; GRT-3 attacks on model-card evals.
  - **Result:** Active annually; GRT-3 ran DEF CON 33 (Aug 2025).
  - **Status:** Verified.

- **HackAPrompt** — Learn Prompting.
  - **Source:** https://www.hackaprompt.com/
  - **Mechanism:** 10 levels × 3 victim LLMs; data released publicly; cash prizes.
  - **Result:** HackAPrompt 1.0 closed; **2.0 launched 2025**.
  - **Status:** Verified.

- **Microsoft AI Bug Bounty** — Microsoft MSRC.
  - **Source:** https://www.microsoft.com/en-us/msrc/bounty-ai
  - **Mechanism:** Copilot, Bing GenAI, Copilot M365, etc. Open program with MSRC AI Severity rubric.
  - **Result:** Active; up to $30K bounties.
  - **Status:** Verified.

- **Gray Swan Arena** — Gray Swan AI.
  - **Source:** https://app.grayswan.ai/arena
  - **Mechanism:** Continuous: agent RT, multimodal, indirect PI, safeguards. Free signup; cash prize pools.
  - **Result:** Active; Indirect PI Challenge ran Nov 5–26, 2025 ($40K, co-sponsored Anthropic + Meta).
  - **Status:** Verified.

- **Prompt Airlines** — Wiz Research.
  - **Source:** https://promptairlines.com/
  - **Mechanism:** 5-level fictional airline-chatbot CTF.
  - **Result:** Active since July 2024; open / no signup.
  - **Status:** Verified.

- **Doublespeak** — Forces Unseen.
  - **Source:** https://doublespeak.chat/
  - **Mechanism:** 7 free + 11 premium levels.
  - **Result:** Active; free + paid tiers.
  - **Status:** Verified.

- **LLM CTF @ SaTML** — ETH SPY Lab + SaTML conference.
  - **Source:** https://llmctf.com/
  - **Mechanism:** Two-phase: defense submission then attack.
  - **Result:** Annual; SaTML 2024 + 2025 held; 2026 winter announcement expected.
  - **Status:** Verified.

- **HackerOne AIxCC + per-vendor VDPs** — HackerOne + OpenAI, xAI, etc.
  - **Source:** https://hackerone.com/ (per-vendor VDPs at vendor's HackerOne page; the consolidated /ai-safety landing returns 404 as of May 2026)
  - **Mechanism:** Coordinated VDP across multiple AI vendors; per-program rules.
  - **Result:** Active; most major labs have running programs.
  - **Status:** Verified.

- **AgentDojo (continuous)** — ETH SpyLab.
  - **Source:** https://github.com/ethz-spylab/agentdojo
  - **Mechanism:** Self-host attack/defense; PR-based leaderboard.
  - **Result:** Active; community-driven artifact updates.
  - **Status:** Verified.

## Eval stack recommendations

`#eval-stack`

If forced to pick three datasets — one classification, one open-ended generation, one agentic — the dossier-recommended stack is:

1. **WildGuardMix (classification)** — 92K labeled prompt/response pairs across 13 risk categories with explicit harmful/benign/refusal labels and multi-task design. Strongest open alternative to proprietary moderation APIs. Pair with Llama Guard 3 / WildGuard / ShieldGemma 2 as the classifier under test.

2. **HarmBench + StrongREJECT judge (open-ended generation)** — HarmBench's 510 behaviors give breadth (standard / contextual / multimodal); StrongREJECT's rubric-based or fine-tuned judge fixes the inflated-ASR bug that plagued AdvBench-style refusal-string evaluation. Together yield Spearman ~0.9 with humans on whether a generation is *both* compliant and useful to an attacker.

3. **AgentDojo (agentic)** — Only widely-adopted dynamic environment with realistic tool surfaces and a security model that separates utility from attack-success. 629 injected test cases cover the indirect-PI threat that defines real production agent risk in 2026.

For adversarial-evaluation discipline, additionally adopt the methodology of Andriushchenko et al. (2024) and Nasr, Carlini, Tramèr et al. (2025): never report a defense's results on a fixed attack — always co-report the strongest adaptive attack against that defense (see `03_defenses.md` § C6).

## Verification notes

- **DoNotAnswer** HF path `LibrAI/do-not-answer` is plausible; GitHub `Libr-AI/do-not-answer` verified; HF mirror exists (Japanese mirror confirmed at `kunishou/do-not-answer-ja`).
- **ForbiddenQuestions** — paper exists; dataset is published with the JailbreakHub release in the TrustAIRLab ecosystem; HF path `TrustAIRLab/forbidden_question_set` plausible but **not directly verified** in this session.
- **RTVLM** — paper verified (arXiv:2401.12915); canonical GitHub or HuggingFace URL **not verified**.
- **CHiSafetyBench** — paper verified (arXiv:2406.10311); GitHub / HF dataset URL **not verified**.
- **CCH-Bench** — does **NOT** appear to exist as a distinct named benchmark; likely confusion with CHiSafetyBench.
- **SC-Safety / SuperCLUE-Safety** — paper verified (arXiv:2310.05818); access via cluebenchmarks.com, no HF mirror confirmed.
- **PINT (Lakera)** — dataset intentionally private (Lakera withholds to prevent overfitting); framework is public.
- **AILuminate Practice** — DEMO Creative-Commons subset is public on GitHub; full Practice (12K) and private Test (12K) require organizational access via MLCommons.
- **HackAPrompt 2.0** — competition launched 2025; specific dataset path not verified in this session.
- **Pile-CC** — content takedowns and license variation; the canonical URL has shifted; treat any specific HF mirror as dated.

**Total entries in this file:** Datasets-A: 14 / Datasets-B: 6 / Datasets-C: 4 / Datasets-D: 6 / Datasets-E: 5 / Datasets-F: 9 / Datasets-G: 4 / Datasets-H: 4 = 52 datasets + 9 leaderboards + 11 CTFs = **72 entries**.

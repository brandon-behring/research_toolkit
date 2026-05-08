# Defenses — Detection, Smoothing, Architectural, Latent-Space, Alignment

<!-- AGENT-INDEX: keep this block stable; future agents read it first. -->
**Scope:** Defense research and defensive evaluation methodology for LLMs facing prompt injection, jailbreaks, and adversarial inputs.
**Out of scope:** Attack research — see `01_direct_attacks.md` (direct), `02_indirect_and_agentic_attacks.md` (indirect / agentic). Training-time defense — see `04_training_time_threats.md` § D6.
**Coverage window:** 2022–2026.
**Last updated:** 2026-05-06.
**Subsections (stable anchors):** C1 Detection-based · C2 Perturbation/smoothing · C3 Architectural/structural · C4 Latent-space · C5 Alignment training as defense · C6 Adaptive attack methodology.
**Key terms covered:** Llama Guard 1/2/3/4, Llama Prompt Guard 2, ShieldGemma 1/2, WildGuard, Constitutional Classifiers, Constitutional Classifiers++, Microsoft Prompt Shields, Lakera Guard, Rebuff, LLM Guard, NeMo Guardrails, HarmBench classifier, SafeDecoding, Aegis, DuoGuard, Gradient Cuff, JBShield, LlamaFirewall, Qwen3Guard, gpt-oss-safeguard, PromptShield, DataSentinel, SmoothLLM, RA-LLM, Erase-and-check, Self-Reminder, Goal Prioritization, AutoDefense, Spotlighting, Dual-LLM, Instruction Hierarchy, StruQ, SecAlign, CaMeL, Defensive Token, PromptArmor, RepE, Circuit Breakers, RMU, Refusal Direction, LAT, Layer-specific Editing, AdaSteer, AlphaSteer, Constitutional AI, RLHF, DPO, IPO, KTO, SimPO, ORPO, Safe RLHF, R2D2, BeaverTails, PKU-SafeRLHF, Adaptive Attacks (Andriushchenko 2024), Nasr, Carlini, Tramèr et al. 2025.
**Related files:** `00_overview.md` (taxonomy), `01_direct_attacks.md` + `02_indirect_and_agentic_attacks.md` (attacks), `05_datasets_and_benchmarks.md` (eval suites), `06_tools_and_vendors.md` (OSS guards).

## Topic overview

Two classes have meaningful production traction by mid-2026: **architectural separation** of trusted instructions from untrusted data (Spotlighting, Instruction Hierarchy, StruQ/SecAlign, CaMeL — these ship in OpenAI, Anthropic, Google, and Meta production stacks); and **high-recall classifiers as one layer of defense-in-depth** (Llama Guard 3/4, ShieldGemma, WildGuard, Constitutional Classifiers, gpt-oss-safeguard, Qwen3Guard). Constitutional Classifiers found no universal jailbreak across 3,000+ hours of Anthropic red-teaming with a 0.38% over-refusal increase — the most-cited 2025 defense paper.

Adaptive-attack work is a third pillar: Andriushchenko et al. (2024, ICLR 2025) and Nasr, Carlini, Tramèr et al. (2025) jointly show that virtually all single-mechanism defenses — perplexity filters, SmoothLLM, paraphrase, retokenization, prefix guidance, in-context defense, semantic smoothing, plus 12 named recent defenses — fall to >90% ASR under adaptive optimization. Refusal-direction ablation (Arditi et al. 2024) further shows refusal training is brittle to a rank-1 weight edit. Pure perturbation/smoothing approaches are now insufficient as standalone defenses.

The six subsections below trace the defense surface. **C1** covers detection — input/output classifiers and guardrails. **C2** covers perturbation and smoothing. **C3** covers architectural and structural defenses (the strongest empirical category). **C4** covers latent-space and representation-level interventions. **C5** covers alignment training itself as defense. **C6** covers adaptive-attack methodology — the discipline of stress-testing all of the above. The 2025–2026 research investment is concentrated in latent-space defenses (Circuit Breakers, LAT, JBShield, SAE-feature monitoring), capability/dataflow control for agents (CaMeL, LlamaFirewall, Operationalizing CaMeL), and adversarial-evaluation discipline (HarmBench, AgentDojo, Attacker-Moves-Second framework).

## C1. Detection-Based Defenses (Input/Output Classifiers)

`#c1-detection`

These defenses run a classifier on input or output to flag harmful or injected content. Llama Guard, ShieldGemma, WildGuard, and Constitutional Classifiers are the canonical open-weight or vendor-provided detectors; commercial offerings (Lakera Guard, Microsoft Prompt Shields, gpt-oss-safeguard) provide hosted alternatives.

### Entries

- **Llama Guard: LLM-based Input-Output Safeguard** — Inan et al. (2023), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2312.06674
  - **Code:** https://github.com/meta-llama/PurpleLlama
  - **Mechanism:** Llama2-7B fine-tuned for prompt + response classification.
  - **Result:** Foundational LLM-based safeguard family; the entry-point for the Llama Guard line.
  - **Status:** Verified.

- **Llama Guard 2 (8B)** — Meta (2024), *Model card*.
  - **Source:** https://github.com/meta-llama/PurpleLlama
  - **Code:** https://github.com/meta-llama/PurpleLlama
  - **Mechanism:** MLCommons-aligned 8B safeguard; refines Llama Guard 1 categories.
  - **Result:** Production-ready successor to Llama Guard 1.
  - **Status:** Unverified — model card only; no formal arXiv paper.

- **Llama Guard 3 (8B + 11B Vision)** — Meta / Llama 3 Herd (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2407.21783
  - **Code:** https://github.com/meta-llama/PurpleLlama
  - **Mechanism:** 8-language input/output safety classifier plus an 11B vision-enabled variant.
  - **Result:** Most-cited open-weight safety classifier of 2024.
  - **Status:** Verified — note that arXiv:2407.21783 is the *Llama 3 Herd of Models* paper; Llama Guard 3 is described as a component within that release rather than as a standalone paper.

- **Llama Guard 3-1B-INT4** — Meta (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2411.17713
  - **Code:** https://github.com/meta-llama/PurpleLlama
  - **Mechanism:** Quantized 1B variant for on-device safety.
  - **Result:** Brings Llama Guard 3 to mobile / edge deployments.
  - **Status:** Verified.

- **Llama Guard 4 (12B)** — Meta (2025), *Model card*.
  - **Source:** https://huggingface.co/meta-llama/Llama-Guard-4-12B
  - **Code:** https://huggingface.co/meta-llama/Llama-Guard-4-12B
  - **Mechanism:** Native multimodal early-fusion 12B safeguard.
  - **Result:** Successor to Llama Guard 3; multimodal-first design.
  - **Status:** Unverified — Meta model card and HuggingFace; no formal arXiv paper located as of May 2026.

- **NeMo Guardrails** — Rebedea et al. (2023), *EMNLP 2023 Demo*.
  - **Source:** https://arxiv.org/abs/2310.10501
  - **Code:** https://github.com/NVIDIA-NeMo/Guardrails
  - **Mechanism:** Programmable rails toolkit using the Colang DSL.
  - **Result:** Most-cited programmable-guardrail framework; production-deployed.
  - **Status:** Verified.

- **Llama Prompt Guard / Prompt Guard 2 (86M)** — Meta (2024–2025), *Model card*.
  - **Source:** https://github.com/meta-llama/PurpleLlama
  - **Code:** https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M
  - **Mechanism:** mDeBERTa-base 86M classifier for direct + indirect injection.
  - **Result:** Lightweight, multilingual injection / jailbreak detector.
  - **Status:** Unverified — model card only; no formal paper.

- **Lakera Guard** — Lakera (2023–2026), *Vendor docs*.
  - **Source:** https://www.lakera.ai/lakera-guard
  - **Code:** https://github.com/lakeraai/pint-benchmark
  - **Mechanism:** Heuristic plus classifier plus Gandalf-trained models in a real-time injection / jailbreak detector.
  - **Result:** Commercial production deployment; Check Point acquisition Sep 2025.
  - **Status:** Unverified — vendor docs only; no peer-reviewed paper.

- **Microsoft Prompt Shields** — Microsoft (2024–2025), *Azure docs*.
  - **Source:** https://learn.microsoft.com/azure/ai-services/content-safety/concepts/jailbreak-detection
  - **Code:** —
  - **Mechanism:** Azure unified API: User-Prompt Attack + Document Attack detection.
  - **Result:** Hyperscaler-default detector inside Azure AI Content Safety.
  - **Status:** Unverified — vendor docs only; closed-weights.

- **ShieldGemma (2B / 9B / 27B)** — Zeng et al. (Google 2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2407.21772
  - **Code:** https://huggingface.co/google/shieldgemma-2b
  - **Mechanism:** Gemma2-based safety classifier suite.
  - **Result:** Open-weights alternative to Llama Guard; multiple size options.
  - **Status:** Verified.

- **ShieldGemma 2 (image moderation)** — Google (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2504.01081
  - **Code:** https://huggingface.co/google/shieldgemma-2-4b-it
  - **Mechanism:** 4B multimodal safety scorer for text + image.
  - **Result:** Google's first multimodal-first safety classifier.
  - **Status:** Verified.

- **Constitutional Classifiers** — Sharma et al. (Anthropic 2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2501.18837
  - **Code:** —
  - **Mechanism:** Synthetic-data classifiers trained from natural-language constitutions.
  - **Result:** 3,000+ red-team hours found no universal jailbreak; ~0.38% over-refusal increase and ~23.7% inference overhead per the paper's reported figures.
  - **Status:** Verified.

- **Constitutional Classifiers++** — Anthropic (2026), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2601.04603
  - **Code:** —
  - **Mechanism:** Two-stage cascade with linear probes; 40× compute reduction.
  - **Result:** 0.05% production refusal rate; the production-grade successor.
  - **Status:** Verified — late-2025/2026 numbering; verify final venue assignment.

- **Cost-Effective CC (representation re-use)** — Anthropic Alignment (2025), *Anthropic blog*.
  - **Source:** https://alignment.anthropic.com/2025/cost-effective-constitutional-classifiers/
  - **Code:** —
  - **Mechanism:** Re-use base-model representations as classifier features.
  - **Result:** Engineering optimization for Constitutional Classifiers deployment.
  - **Status:** Unverified — Anthropic alignment blog post, no arXiv.

- **Rebuff** — ProtectAI (2023–2025), *OSS*.
  - **Source:** https://github.com/protectai/rebuff
  - **Code:** https://github.com/protectai/rebuff
  - **Mechanism:** Heuristics + LLM check + vector DB + canary tokens.
  - **Result:** Influential early OSS PI detector; **archived May 16, 2025**.
  - **Status:** Verified — repo archived.

- **LLM Guard** — LaiyerAI / ProtectAI (2023–2025), *OSS*.
  - **Source:** https://llm-guard.com/
  - **Code:** https://github.com/protectai/llm-guard
  - **Mechanism:** Modular scanner pipeline (anonymizer, PI, secrets, ban-substring).
  - **Result:** Most-popular OSS runtime guard; Protect AI flagship after Rebuff archival.
  - **Status:** Verified.

- **Baseline Defenses (perplexity / paraphrase / retokenize)** — Jain et al. (2023), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2309.00614
  - **Code:** —
  - **Mechanism:** Three baseline defenses: perplexity filtering, paraphrase, retokenization.
  - **Result:** Reference baseline that 2024–2026 work measures against.
  - **Status:** Verified.

- **Detecting Attacks with Perplexity** — Alon & Kamfonas (2023), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2308.14132
  - **Code:** —
  - **Mechanism:** LightGBM on perplexity plus token length detects GCG suffixes.
  - **Result:** Effective on non-fluent suffixes; broken by AdvPrompter / COLD-Attack class.
  - **Status:** Verified.

- **Token-Level Adversarial Prompt Detection** — Hu et al. (2023), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2311.11509
  - **Code:** —
  - **Mechanism:** Token-level perplexity plus context features.
  - **Result:** Refines Alon & Kamfonas baseline.
  - **Status:** Verified.

- **HarmBench classifier (Llama 2 13B fine-tune)** — Mazeika et al. (2024), *ICML 2024*.
  - **Source:** https://arxiv.org/abs/2402.04249
  - **Code:** https://github.com/centerforaisafety/HarmBench
  - **Mechanism:** Generative classifier across 7 harm categories.
  - **Result:** Reference judge model for HarmBench evaluation.
  - **Status:** Verified. → Primary treatment in `05_datasets_and_benchmarks.md` § Datasets-A; cross-ref C5 (R2D2 defense), C6 (eval methodology).

- **WildGuard / WildGuardMix** — Han et al. (AI2 2024), *NeurIPS 2024 D&B*.
  - **Source:** https://arxiv.org/abs/2406.18495
  - **Code:** https://github.com/allenai/wildguard
  - **Mechanism:** Open one-stop moderation: prompt harm + response harm + refusal.
  - **Result:** Matches GPT-4 on multi-task moderation; strongest open alternative to proprietary moderation APIs.
  - **Status:** Verified.

- **SafeDecoding** — Xu et al. (2024), *ACL 2024*.
  - **Source:** https://arxiv.org/abs/2402.08983
  - **Code:** https://github.com/uw-nsl/SafeDecoding
  - **Mechanism:** Safety-aware decoding (token-probability amplification at decode time).
  - **Result:** Output-side defense that complements input classifiers.
  - **Status:** Verified.

- **Aegis (NeMo) Content Safety** — Ghosh et al. (NVIDIA 2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2404.05993
  - **Code:** https://huggingface.co/nvidia/Aegis-AI-Content-Safety-LlamaGuard-Defensive-1.0
  - **Mechanism:** LlamaGuard-fine-tuned permissive and defensive variants.
  - **Result:** NVIDIA's contribution to the open-classifier ecosystem.
  - **Status:** Verified.

- **DuoGuard** — Deng et al. (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2502.05163
  - **Code:** https://github.com/yihedeng9/DuoGuard
  - **Mechanism:** 0.5B multilingual guardrail trained via two-player RL.
  - **Result:** Lightweight multilingual classifier.
  - **Status:** Verified.

- **ToxicChat** — Lin et al. (2023), *EMNLP 2023 Findings*.
  - **Source:** https://arxiv.org/abs/2310.17389
  - **Code:** https://huggingface.co/datasets/lmsys/toxic-chat
  - **Mechanism:** 10K real Vicuna user-prompt toxicity benchmark.
  - **Result:** Real-traffic toxicity reference dataset.
  - **Status:** Verified. → Also see `05_datasets_and_benchmarks.md` § Datasets-A.

- **Robust Safety Classifier / Adversarial Prompt Shield** — Kim et al. (2023), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2311.00172
  - **Code:** —
  - **Mechanism:** BERT-style adversarially-trained classifier.
  - **Result:** Adversarial-training contribution to safety classification.
  - **Status:** Verified.

- **Gradient Cuff** — Hu et al. (2024), *NeurIPS 2024*.
  - **Source:** https://arxiv.org/abs/2403.00867
  - **Code:** https://github.com/IBM/Gradient-Cuff
  - **Mechanism:** Refusal-loss landscape (functional value plus gradient norm).
  - **Result:** Detects jailbreaks via refusal-loss geometry.
  - **Status:** Verified.

- **JBShield** — Zhang et al. (2025), *USENIX Security 2025*.
  - **Source:** https://arxiv.org/abs/2502.07557
  - **Code:** https://github.com/NISPLab/JBShield
  - **Mechanism:** Concept-activation classifier plus manipulation.
  - **Result:** Latent-space-aware classifier.
  - **Status:** Verified.

- **LlamaFirewall (PurpleLlama)** — Chennabasappa et al. (Meta 2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2505.03574
  - **Code:** https://github.com/meta-llama/PurpleLlama
  - **Mechanism:** Open guardrail system — PromptGuard 2 + Agent Alignment + CodeShield.
  - **Result:** Multi-scanner runtime defense for agents.
  - **Status:** Verified. → Also see `06_tools_and_vendors.md` § OSS-defense-guards.

- **Qwen3Guard (0.6 / 4 / 8B)** — Qwen Team (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2510.14276
  - **Code:** https://github.com/QwenLM/Qwen3Guard
  - **Mechanism:** Tri-class plus token-level streaming head.
  - **Result:** Alibaba's contribution to open-classifier landscape.
  - **Status:** Verified.

- **gpt-oss-safeguard (20B, 120B)** — OpenAI (2025), *OpenAI blog*.
  - **Source:** https://openai.com/index/gpt-oss-safeguard/
  - **Code:** https://huggingface.co/openai/gpt-oss-safeguard-20b
  - **Mechanism:** Policy-at-inference reasoning safety classifier.
  - **Result:** OpenAI's first open-weights safety classifier.
  - **Status:** Unverified — OpenAI blog only, no arXiv.

- **PromptShield** — Jacob et al. (2025), *CODASPY 2025*.
  - **Source:** https://arxiv.org/abs/2501.15145
  - **Code:** —
  - **Mechanism:** Deployable injection detector plus benchmark.
  - **Result:** Practitioner-oriented detector with companion benchmark.
  - **Status:** Verified.

- **OpenAI Omni-Moderation** — OpenAI (2024), *API docs*.
  - **Source:** https://platform.openai.com/docs/guides/moderation
  - **Code:** —
  - **Mechanism:** Multimodal text + image moderation across 13 categories.
  - **Result:** OpenAI's hosted moderation endpoint.
  - **Status:** Unverified — API docs only, no arXiv.

- **DataSentinel** — Liu et al. (2025), *IEEE S&P 2025 Distinguished*.
  - **Source:** https://arxiv.org/abs/2504.11358
  - **Code:** —
  - **Mechanism:** Game-theoretic minimax-trained injection detector.
  - **Result:** IEEE S&P 2025 Distinguished Paper; also serves as the data-channel sentinel in C3.
  - **Status:** Verified. → Also see § C3.

## C2. Perturbation / Smoothing Defenses

`#c2-smoothing`

These defenses transform or aggregate over the input — random char swaps, paraphrase, retokenization, semantic smoothing — to disrupt adversarial structure. Andriushchenko et al. (2024) and Nasr, Carlini, Tramèr et al. (2025) showed all of these classes fall to >90% ASR under adaptive attack. They remain useful as one layer of defense-in-depth but are not standalone solutions.

### Entries

- **SmoothLLM** — Robey et al. (2023), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2310.03684
  - **Code:** https://github.com/arobey1/smooth-llm
  - **Mechanism:** Random character swaps / patches / inserts plus majority vote.
  - **Result:** Foundational randomized-smoothing defense for LLMs; broken under adaptive attack.
  - **Status:** Verified.

- **RA-LLM** — Cao et al. (2023), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2309.14348
  - **Code:** —
  - **Mechanism:** Word-level random masking plus a rejection-rate threshold.
  - **Result:** Alternative randomized-smoothing approach.
  - **Status:** Verified.

- **Erase-and-check (certified)** — Kumar et al. (2023), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2309.02705
  - **Code:** https://github.com/aounon/certified-llm-safety
  - **Mechanism:** Certified subsequence enumeration.
  - **Result:** First certified-robustness result for LLM safety; provides formal guarantees within its threat model.
  - **Status:** Verified.

- **Paraphrase / Retokenization** — Jain et al. (2023), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2309.00614
  - **Code:** —
  - **Mechanism:** Semantic-preserving rewrite or sub-token re-segmentation.
  - **Result:** Two of three baselines from Jain et al.; broken by adaptive attacks.
  - **Status:** Verified. → Also see C1 entry (Baseline Defenses).

- **Self-Reminder** — Xie et al. (2023), *Nature Machine Intelligence*.
  - **Source:** https://doi.org/10.1038/s42256-023-00765-8
  - **Code:** —
  - **Mechanism:** Wrap user query with a safety self-reminder.
  - **Result:** Lightweight prompt-engineering defense.
  - **Status:** Verified.

- **Goal Prioritization** — Zhang et al. (2023), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2311.09096
  - **Code:** https://github.com/thu-coai/JailbreakDefense_GoalPriority
  - **Mechanism:** Make safety > helpfulness explicit at inference and during training.
  - **Result:** Frames goal conflict as the load-bearing alignment failure.
  - **Status:** Verified.

- **LLM Self-Defense** — Helbling et al. (2023), *ICLR 2024 Tiny Paper*.
  - **Source:** https://arxiv.org/abs/2308.07308
  - **Code:** https://github.com/poloclub/llm-self-defense
  - **Mechanism:** Cascaded self-evaluation prompt.
  - **Result:** Output-side self-evaluation defense.
  - **Status:** Verified.

- **Defensive Prompt Patch (DPP)** — Xiong et al. (2024), *ACL 2025 Findings*.
  - **Source:** https://arxiv.org/abs/2405.20099
  - **Code:** https://github.com/IBM/DPP
  - **Mechanism:** Optimized interpretable defensive suffix prompt prepended to user input.
  - **Result:** Defensive-prompt complement to attack-side suffix optimization (mirrors the GCG-style attack surface).
  - **Status:** Verified — mechanism description generalized 2026-05-06 to match the abstract; the body uses a hierarchical genetic algorithm.

- **Backtranslation defense** — Wang et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2402.16459
  - **Code:** https://github.com/YihanWang617/LLM-Jailbreaking-Defense-Backtranslation
  - **Mechanism:** Inverse-prompt inference plus re-check.
  - **Result:** Roundtrip-based detection of injected content.
  - **Status:** Verified.

- **Semantic Smoothing** — Ji et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2402.16192
  - **Code:** https://github.com/UCSB-NLP-Chang/SemanticSmooth
  - **Mechanism:** Aggregate over semantically transformed copies of the input.
  - **Result:** Semantic version of randomized smoothing.
  - **Status:** Verified.

- **In-Context Defense (ICD)** — Wei, Wang & Wang (2023), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2310.06387
  - **Code:** —
  - **Mechanism:** Few-shot refusal demonstrations as context.
  - **Result:** In-context-learning analog of safety fine-tuning.
  - **Status:** Verified.

- **AutoDefense** — Zeng et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2403.04783
  - **Code:** https://github.com/XHMY/AutoDefense
  - **Mechanism:** Multi-agent LLM ensemble that assigns specialized roles to defender agents and filters generated output.
  - **Result:** Multi-agent ensemble defense; specific role names are documented in the paper body.
  - **Status:** Verified — mechanism description generalized 2026-05-06 to match the abstract.

- **Prefix Guidance (PG)** — Zhao et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2408.08924
  - **Code:** —
  - **Mechanism:** Force first tokens to a refusal-style prefix plus a classifier check.
  - **Result:** Enforces refusal-shaped output as defense.
  - **Status:** Verified.

- **Sandwich defense (community)** — LearnPrompting (2023), *LearnPrompting docs*.
  - **Source:** https://learnprompting.org/docs/prompt_hacking/defensive_measures/sandwich_defense
  - **Code:** —
  - **Mechanism:** Repeat the system instruction *after* the user input.
  - **Result:** Community-popular prompt-engineering defense; broken under adaptive attack.
  - **Status:** Unverified — community docs only, no paper.

## C3. Architectural / Structural Defenses

`#c3-architectural`

These defenses change the architecture of how the model receives input — separating trusted instructions from untrusted data, training models to prefer privileged instructions, or running a privileged-LLM / quarantined-LLM split. This is the strongest empirical category as of mid-2026; Spotlighting, Instruction Hierarchy, StruQ/SecAlign, and CaMeL ship in major production stacks.

### Entries

- **Spotlighting** — Hines et al. (Microsoft 2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2403.14720
  - **Code:** —
  - **Mechanism:** Three signaling techniques — delimiting, datamarking, encoding — to mark untrusted text.
  - **Result:** ASR >50% → <2% on tested workloads.
  - **Status:** Verified. → Also see `02_indirect_and_agentic_attacks.md` § B1.

- **Dual-LLM pattern** — Willison (2023, blog), *Blog essay*.
  - **Source:** https://simonwillison.net/2023/Apr/25/dual-llm-pattern/
  - **Code:** —
  - **Mechanism:** Privileged LLM plus Quarantined LLM with a symbolic-variable interface.
  - **Result:** Pre-academic architectural pattern that CaMeL formalized.
  - **Status:** Unverified — Simon Willison blog (2023-04-25); cited in CaMeL paper.

- **Instruction Hierarchy** — Wallace et al. (OpenAI 2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2404.13208
  - **Code:** —
  - **Mechanism:** Train models to prefer system > developer > user > tool instructions.
  - **Result:** Foundational training-time architectural defense; ships in OpenAI production.
  - **Status:** Verified.

- **StruQ (Structured Queries)** — Chen et al. (2024), *USENIX Security 2025*.
  - **Source:** https://arxiv.org/abs/2402.06363
  - **Code:** https://github.com/sizhe-chen/struq
  - **Mechanism:** Reserved special tokens separate prompt vs data.
  - **Result:** Structured-query defense pattern with formal training method.
  - **Status:** Verified.

- **SecAlign** — Chen et al. (2024), *ACM CCS 2025*.
  - **Source:** https://arxiv.org/abs/2410.05451
  - **Code:** https://github.com/facebookresearch/SecAlign
  - **Mechanism:** Preference optimization on prompt-injected pairs.
  - **Result:** DPO-style alignment specifically for indirect-PI robustness.
  - **Status:** Verified.

- **CaMeL: Defeating PI by Design** — Debenedetti et al. (Google Research 2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2503.18813
  - **Code:** https://github.com/google-research/camel-prompt-injection
  - **Mechanism:** Privileged LLM emits a Python program; capabilities track data origin.
  - **Result:** Capability-based meta-layer; the most architecturally ambitious 2025 defense.
  - **Status:** Verified.

- **Operationalizing CaMeL (enterprise)** — Tallam & Miller (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2505.22852
  - **Code:** —
  - **Mechanism:** Engineering hardening of CaMeL for production deployment.
  - **Result:** Production-engineering followup to CaMeL.
  - **Status:** Verified — authors corrected 2026-05-06 (earlier draft incorrectly attributed to Bagdasarian).

- **DataSentinel** — Liu et al. (2025), *IEEE S&P 2025 Distinguished*.
  - **Source:** https://arxiv.org/abs/2504.11358
  - **Code:** —
  - **Mechanism:** Game-theoretic injection detector positioned at the data-channel sentinel.
  - **Result:** IEEE S&P 2025 Distinguished Paper; bridges C1 (classifier) and C3 (architectural sentinel role).
  - **Status:** Verified. → Also listed in § C1.

- **Defensive Token (test-time)** — Chen et al. (2025), *AISec 2025*.
  - **Source:** https://arxiv.org/abs/2507.07974
  - **Code:** https://github.com/Sizhe-Chen/DefensiveToken
  - **Mechanism:** Inserted special tokens with optimized embeddings.
  - **Result:** Test-time defense that complements training-time hierarchies.
  - **Status:** Verified.

- **PromptArmor** — Shi et al. (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2507.15219
  - **Code:** —
  - **Mechanism:** Off-the-shelf LLM detects and strips injections before the agent sees them.
  - **Result:** <1% FPR/FNR on AgentDojo.
  - **Status:** Verified. → Also see `06_tools_and_vendors.md` § Commercial vendors.

- **Prompt Control-Flow Integrity (PCFI)** — Alam, Islam, Ameen, Miah, Shin (2026), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2603.18433
  - **Code:** —
  - **Mechanism:** Provenance-tagged runtime control-flow integrity for agent traces.
  - **Result:** Formal CFI analog for LLM agents.
  - **Status:** Verified — authors filled in 2026-05-06.

- **Lessons from Defending Gemini Against Indirect PI** — Shi, Lin, Song et al. (Google DeepMind 2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2505.14534
  - **Code:** —
  - **Mechanism:** Layered defense plus adaptive evaluation and automated red teaming.
  - **Result:** Production-engineering retrospective from Gemini; the canonical Google reference.
  - **Status:** Verified — authors corrected 2026-05-06 (earlier draft incorrectly attributed to "Lichtensztein"; no such author on the paper).

- **BIPIA (benchmark + structural defenses)** — Yi et al. (Microsoft 2023), *KDD 2025*.
  - **Source:** https://arxiv.org/abs/2312.14197
  - **Code:** https://github.com/microsoft/BIPIA
  - **Mechanism:** Boundary-awareness plus explicit-reminder defenses tested in BIPIA.
  - **Result:** Reference structural-defense baseline.
  - **Status:** Verified. → Also see `01_direct_attacks.md` § A1, `02_indirect_and_agentic_attacks.md` § B1.

- **Open-Prompt-Injection (benchmark + defenses)** — Liu et al. (2023), *USENIX Security 2024*.
  - **Source:** https://arxiv.org/abs/2310.12815
  - **Code:** https://github.com/liu00222/Open-Prompt-Injection
  - **Mechanism:** Benchmark plus classification of structural defenses.
  - **Result:** First formal taxonomy of architectural defense types.
  - **Status:** Verified. → Also see `01_direct_attacks.md` § A1, `02_indirect_and_agentic_attacks.md` § B1.

## C4. Latent-Space / Representation-Level Defenses

`#c4-latent-space`

These defenses operate on internal model activations — probing, steering, or reshaping them. Circuit Breakers (Zou et al. 2024) is the canonical reference. Refusal Direction (Arditi et al. 2024) is the canonical *attack on* this defense surface: it shows refusal lives in a single residual-stream direction that can be ablated with a rank-1 weight edit.

### Entries

- **Representation Engineering (RepE)** — Zou et al. (2023), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2310.01405
  - **Code:** https://github.com/andyzoujm/representation-engineering
  - **Mechanism:** Top-down probes plus steering on activation populations.
  - **Result:** Foundational representation-engineering paper for safety.
  - **Status:** Verified.

- **Circuit Breakers (Representation Rerouting)** — Zou et al. (2024), *NeurIPS 2024*.
  - **Source:** https://arxiv.org/abs/2406.04313
  - **Code:** https://github.com/GraySwanAI/circuit-breakers
  - **Mechanism:** Reroute harmful representations to an orthogonal subspace.
  - **Result:** Top-3 most-cited 2024 defense paper; broken adaptively by Schwinn et al. (2024).
  - **Status:** Verified.

- **RMU (Representation Misdirection for Unlearning) / WMDP** — Li et al. (CAIS 2024), *ICML 2024*.
  - **Source:** https://arxiv.org/abs/2403.03218
  - **Code:** https://github.com/centerforaisafety/wmdp
  - **Mechanism:** Misdirect activations on the forget-set toward a random vector.
  - **Result:** Hazard-knowledge unlearning method; ships with the WMDP benchmark.
  - **Status:** Verified. → Also see `04_training_time_threats.md` § D6, `05_datasets_and_benchmarks.md` § Datasets-F.

- **Refusal in LMs is Mediated by a Single Direction** — Arditi et al. (2024), *NeurIPS 2024*.
  - **Source:** https://arxiv.org/abs/2406.11717
  - **Code:** https://github.com/andyrdt/refusal_direction
  - **Mechanism:** Refusal lives in a 1-D residual-stream direction.
  - **Result:** Rank-1 weight edit removes safety; foundational interpretability + attack reference.
  - **Status:** Verified.

- **Latent / Targeted LAT** — Sheshadri et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2407.15549
  - **Code:** https://github.com/aengusl/latent-adversarial-training
  - **Mechanism:** Perturb residual-stream activations during fine-tuning.
  - **Result:** Removes refusal-jailbreaks better than R2D2.
  - **Status:** Verified. → Also see § C5.

- **Layer-specific Editing (LED)** — Zhao et al. (2024), *EMNLP 2024 Findings*.
  - **Source:** https://arxiv.org/abs/2405.18166
  - **Code:** —
  - **Mechanism:** Realign safety-critical early layers via targeted weight edits.
  - **Result:** Layer-specific safety realignment.
  - **Status:** Verified.

- **Jailbreaking Leaves a Trace** — Kadali & Papalexakis (2026), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2602.11495
  - **Code:** —
  - **Mechanism:** Tensor decomposition of hidden states for jailbreak detection.
  - **Result:** Latent-space jailbreak fingerprinting.
  - **Status:** Verified — authors corrected 2026-05-06.

- **ALERT (Internal Discrepancy Amplification)** — Lin, Li, Zeng, Li, Wei, Ning, Li, Chen, Tong (2026), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2601.03600
  - **Code:** —
  - **Mechanism:** Layer / module / token-wise amplification of jailbreak features.
  - **Result:** Latent-feature-amplification approach to detection.
  - **Status:** Verified — authors filled in 2026-05-06.

- **Scaling Monosemanticity (SAE safety features)** — Templeton et al. (Anthropic 2024), *Transformer Circuits thread*.
  - **Source:** https://transformer-circuits.pub/2024/scaling-monosemanticity/
  - **Code:** —
  - **Mechanism:** Sparse autoencoder features for deception / sycophancy / dangerous content.
  - **Result:** Foundational SAE-feature work tying interpretability to safety.
  - **Status:** Verified — Anthropic Transformer Circuits thread, no arXiv.

- **AdaSteer** — Wu et al. (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2504.09466
  - **Code:** —
  - **Mechanism:** Dual-direction adaptive activation steering.
  - **Result:** Adaptive variant of refusal-direction steering.
  - **Status:** Verified.

- **AlphaSteer (null-space refusal)** — Sheng, Shen, Zhao et al. (2025), *ICLR 2026*.
  - **Source:** https://arxiv.org/abs/2506.07022
  - **Code:** —
  - **Mechanism:** Refusal steering with null-space constraint.
  - **Result:** Constraint-based refusal steering.
  - **Status:** Verified — authors filled in 2026-05-06.

- **DRO Direct Preference Optimization** — Wu et al. (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2502.01930
  - **Code:** —
  - **Mechanism:** KL / Wasserstein-uncertainty DPO.
  - **Result:** Distributionally robust DPO variant.
  - **Status:** Verified.

- **Distributionally Robust RLHF** — Liu et al. (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2503.00539
  - **Code:** —
  - **Mechanism:** DRO version of reward-based RLHF plus reward-free DPO.
  - **Result:** Distributional-robustness extension to alignment training.
  - **Status:** Verified.

## C5. Alignment Training as Defense

`#c5-alignment-training`

Alignment training itself is a defense surface: RLHF, DPO, IPO, KTO, SimPO, ORPO, Safe RLHF, Constitutional AI all attempt to make the model refuse harmful requests by default. Sycophancy and over-refusal (XSTest) are the failure modes; refusal-direction work (C4) shows the safety achieved here is brittle.

### Entries

- **InstructGPT / RLHF** — Ouyang et al. (2022), *NeurIPS 2022*.
  - **Source:** https://arxiv.org/abs/2203.02155
  - **Code:** —
  - **Mechanism:** SFT + Reward Model + PPO RLHF foundational pipeline.
  - **Result:** Foundational alignment-training paper.
  - **Status:** Verified.

- **Helpful & Harmless RLHF** — Bai et al. (Anthropic 2022), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2204.05862
  - **Code:** https://github.com/anthropics/hh-rlhf
  - **Mechanism:** Iterated weekly RLHF for HH (Helpful + Harmless) assistant.
  - **Result:** Foundational HH-RLHF dataset and training pipeline.
  - **Status:** Verified. → Also see `05_datasets_and_benchmarks.md` § Datasets-B.

- **Constitutional AI** — Bai et al. (Anthropic 2022), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2212.08073
  - **Code:** —
  - **Mechanism:** Supervised learning + RLAIF using constitutional principles.
  - **Result:** Anthropic's foundational alignment-training framework.
  - **Status:** Verified.

- **RLAIF** — Lee et al. (Google 2023), *ICML 2024*.
  - **Source:** https://arxiv.org/abs/2309.00267
  - **Code:** —
  - **Mechanism:** Off-the-shelf LLM as preference labeler matches RLHF.
  - **Result:** Reduces dependence on human feedback for alignment.
  - **Status:** Verified.

- **DPO (Direct Preference Optimization)** — Rafailov et al. (2023), *NeurIPS 2023*.
  - **Source:** https://arxiv.org/abs/2305.18290
  - **Code:** https://github.com/eric-mitchell/direct-preference-optimization
  - **Mechanism:** Closed-form RLHF as a classification loss.
  - **Result:** Replaces RM + PPO with single-stage classification training.
  - **Status:** Verified.

- **IPO** — Azar et al. (2023), *AISTATS 2024*.
  - **Source:** https://arxiv.org/abs/2310.12036
  - **Code:** —
  - **Mechanism:** Theoretically grounded preference optimization bypassing DPO approximations.
  - **Result:** IPO is the principled successor to DPO that addresses preference-data noise.
  - **Status:** Verified.

- **KTO** — Ethayarajh et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2402.01306
  - **Code:** https://github.com/ContextualAI/HALOs
  - **Mechanism:** Prospect-theory-style HALO (Human-Aware Loss); binary good/bad labels.
  - **Result:** Replaces preference pairs with simpler binary labels.
  - **Status:** Verified.

- **SimPO** — Meng et al. (2024), *NeurIPS 2024*.
  - **Source:** https://arxiv.org/abs/2405.14734
  - **Code:** https://github.com/princeton-nlp/SimPO
  - **Mechanism:** Reference-free length-normalized preference optimization.
  - **Result:** Outperforms DPO on several benchmarks without a reference model.
  - **Status:** Verified.

- **ORPO** — Hong et al. (2024), *EMNLP 2024*.
  - **Source:** https://arxiv.org/abs/2403.07691
  - **Code:** https://github.com/xfactlab/orpo
  - **Mechanism:** Odds-ratio penalty fused with SFT in a single stage.
  - **Result:** Simplifies the SFT-then-DPO two-stage pipeline.
  - **Status:** Verified.

- **HarmBench R2D2** — Mazeika et al. (2024), *ICML 2024*.
  - **Source:** https://arxiv.org/abs/2402.04249
  - **Code:** https://github.com/centerforaisafety/HarmBench
  - **Mechanism:** Robust Refusal Dynamic Defense — adversarial fine-tune.
  - **Result:** HarmBench's adversarial-training defense baseline.
  - **Status:** Verified. → Primary treatment in `05_datasets_and_benchmarks.md` § Datasets-A; cross-ref C1 (classifier).

- **RAFT** — Dong et al. (2023), *TMLR 2024*.
  - **Source:** https://arxiv.org/abs/2304.06767
  - **Code:** https://github.com/RLHFlow/RAFT
  - **Mechanism:** Iterative best-of-n / rejection-sampling fine-tuning.
  - **Result:** Lightweight alternative to PPO RLHF.
  - **Status:** Verified.

- **Safe RLHF** — Dai et al. (2023), *ICLR 2024 Spotlight*.
  - **Source:** https://arxiv.org/abs/2310.12773
  - **Code:** https://github.com/PKU-Alignment/safe-rlhf
  - **Mechanism:** Decouple reward (helpful) and cost (harmless) via Lagrangian.
  - **Result:** PKU's safe-RLHF framework; multi-objective alignment.
  - **Status:** Verified.

- **BeaverTails** — Ji et al. (PKU 2023), *NeurIPS 2023 D&B*.
  - **Source:** https://arxiv.org/abs/2307.04657
  - **Code:** https://github.com/PKU-Alignment/beavertails
  - **Mechanism:** 333K QA pairs with separate help + harm annotations.
  - **Result:** Foundational dataset for decoupled help/harm annotation.
  - **Status:** Verified. → Also see `05_datasets_and_benchmarks.md` § Datasets-A.

- **PKU-SafeRLHF (multi-level)** — Ji et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2406.15513
  - **Code:** https://github.com/PKU-Alignment/safe-rlhf
  - **Mechanism:** 19 harm categories, 3 severity levels, 265K QA pairs.
  - **Result:** Multi-level safety preference dataset; successor to BeaverTails.
  - **Status:** Verified. → Also see `05_datasets_and_benchmarks.md` § Datasets-A.

- **Targeted LAT (alignment)** — Sheshadri et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2407.15549
  - **Code:** https://github.com/aengusl/latent-adversarial-training
  - **Mechanism:** LAT used for alignment fine-tuning.
  - **Result:** Removes refusal jailbreaks better than R2D2.
  - **Status:** Verified. → Also listed in § C4.

## C6. Adaptive Attack Methodology

`#c6-adaptive-methodology`

The discipline of evaluating defenses against attackers who know the defense and adapt to it. Andriushchenko et al. (2024) and Nasr, Carlini, Tramèr et al. (2025) are the field-defining results: virtually all single-mechanism defenses fall to >90% ASR under adaptive optimization. The methodology requirement traces back to Tramèr, Carlini et al. (2020) in the image-domain.

### Entries

- **Adaptive Attacks on Safety-Aligned LLMs** — Andriushchenko, Croce, Flammarion (2024), *ICLR 2025*.
  - **Source:** https://arxiv.org/abs/2404.02151
  - **Code:** https://github.com/tml-epfl/llm-adaptive-attacks
  - **Mechanism:** Random-search suffix plus logprob-of-"Sure" → 100% ASR.
  - **Result:** 100% ASR on Vicuna / Mistral / Phi-3 / Llama-2/3 / Gemma / GPT-3.5/4o. Field-defining adaptive-attack methodology paper.
  - **Status:** Verified.

- **The Attacker Moves Second** — Nasr, Carlini, Sitawarin, Tramèr et al. (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2510.09023
  - **Code:** —
  - **Mechanism:** Adaptive attack strategy with second-mover advantage.
  - **Result:** Bypasses 12 recent defenses with adaptive attacks (>90% ASR each).
  - **Status:** Verified — authors corrected 2026-05-06 per arXiv primary source (lead author is Milad Nasr; earlier draft incorrectly led with Wallace).

- **Adaptive Attacks Break Indirect-PI Agent Defenses** — Zhan, Fang, Panchal, Kang (2025), *NAACL 2025 Findings*.
  - **Source:** https://arxiv.org/abs/2503.00061
  - **Code:** —
  - **Mechanism:** Adaptive attacks bypass agent indirect-PI defenses (Spotlighting variants, classifier guards).
  - **Result:** Extends adaptive-attack methodology to the agentic regime.
  - **Status:** Verified — authors filled in 2026-05-06.

- **HarmBench: Standardized Evaluation** — Mazeika et al. (2024), *ICML 2024*.
  - **Source:** https://arxiv.org/abs/2402.04249
  - **Code:** https://github.com/centerforaisafety/HarmBench
  - **Mechanism:** Standardized red-team and defense evaluation across 7 categories.
  - **Result:** 510 behaviors, 7 harm categories, R2D2 adversarial-training defense.
  - **Status:** Verified. → Primary treatment in `05_datasets_and_benchmarks.md` § Datasets-A.

- **JailbreakBench** — Chao et al. (2024), *NeurIPS 2024 D&B*.
  - **Source:** https://arxiv.org/abs/2404.01318
  - **Code:** https://github.com/JailbreakBench/jailbreakbench
  - **Mechanism:** Open robustness benchmark plus leaderboard plus artifacts.
  - **Result:** JBB-Behaviors dataset across 10 OpenAI-policy categories.
  - **Status:** Verified. → Primary treatment in `05_datasets_and_benchmarks.md` § Datasets-A.

- **EasyJailbreak** — Zhou et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2403.12171
  - **Code:** https://github.com/EasyJailbreak/EasyJailbreak
  - **Mechanism:** Unified Selector / Mutator / Constraint / Evaluator framework with 11 attack methods.
  - **Result:** Standardized attack-implementation framework.
  - **Status:** Verified. → Primary treatment in `06_tools_and_vendors.md` § OSS-RT-runners.

- **AgentDojo (CaMeL eval target)** — Debenedetti et al. (2024), *NeurIPS 2024 D&B*.
  - **Source:** https://arxiv.org/abs/2406.13352
  - **Code:** https://github.com/ethz-spylab/agentdojo
  - **Mechanism:** Adversarial benchmark for LLM agent tools and data flows.
  - **Result:** The de-facto agentic adaptive-evaluation harness.
  - **Status:** Verified. → Primary treatment in `02_indirect_and_agentic_attacks.md` § B2; also see `05_datasets_and_benchmarks.md` § Datasets-D.

- **LLM Jailbreak Attack vs Defense — Comprehensive Study** — Xu et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2402.13457
  - **Code:** —
  - **Mechanism:** 9 attacks × 7 defenses × 6 models.
  - **Result:** Comprehensive comparative evaluation.
  - **Status:** Verified.

- **Bypassing Prompt Injection and Jailbreak Detection in Guardrails** — Hackett, Birch, Trawicki, Suri, Garraghan (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2504.11168
  - **Code:** —
  - **Mechanism:** Empirical bypass of guardrail classifiers.
  - **Result:** Adaptive attack against the C1 detection class.
  - **Status:** Verified — authors filled in 2026-05-06.

- **How Not to Detect PI with an LLM** — Choudhary et al. (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2507.05630
  - **Code:** —
  - **Mechanism:** Critique of LLM-as-detector approaches.
  - **Result:** Methodological caution paper for LLM-judge defenses.
  - **Status:** Verified.

- **Defenses are not Adaptively Attacked (foundational, image-domain)** — Tramèr, Carlini et al. (2020), *NeurIPS 2020*.
  - **Source:** https://arxiv.org/abs/2002.08347
  - **Code:** —
  - **Mechanism:** Image-domain adaptive-attack methodology framework.
  - **Result:** Foundational reference imported into LLM safety; the methodology requirement.
  - **Status:** Verified.

- **Indirect Prompt Injections: Are Firewalls All You Need?** — Bhagwatkar, Kasa, Puri, Huang, Rish, Taylor, Dvijotham, Lacoste (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2510.05244
  - **Code:** —
  - **Mechanism:** Stronger benchmarks against firewall-style guardrails.
  - **Result:** Adaptive evaluation specifically of firewall-class defenses.
  - **Status:** Verified — authors filled in 2026-05-06.

## Defense landscape 2024–2026

**Strongest empirical support** — two classes have meaningful production traction. **Architectural separation** of trusted instructions vs untrusted data: Spotlighting (Hines et al. 2024), Instruction Hierarchy (Wallace et al. 2024), StruQ/SecAlign (Chen et al. 2024), CaMeL (Debenedetti et al. 2025). These ship in OpenAI, Anthropic, Google, and Meta production stacks. **High-recall classifiers as one layer of defense-in-depth**: Llama Guard 3/4, ShieldGemma, WildGuard, Constitutional Classifiers, gpt-oss-safeguard, Qwen3Guard. **Constitutional Classifiers found no universal jailbreak across 3,000+ hours of Anthropic red-teaming** (with ~0.38% over-refusal increase) — most-cited 2025 defense paper.

**Likely already broken under adaptive attack.** Andriushchenko et al. (2024, arXiv:2404.02151) and Nasr, Carlini, Tramèr et al. (2025, arXiv:2510.09023) jointly show virtually all single-mechanism defenses — perplexity filters, SmoothLLM, paraphrase, retokenization, prefix guidance, in-context defense, semantic smoothing, plus 12 named recent defenses — fall to >90% ASR under adaptive optimization. Refusal-direction ablation (Arditi et al. 2024) further shows refusal training is brittle to a rank-1 weight edit. Pure perturbation/smoothing approaches are now insufficient as standalone defenses.

**Where 2025–2026 research is investing.** **Latent-space defenses** — Circuit Breakers (Zou 2024), Latent Adversarial Training (Sheshadri 2024), JBShield (2025), SAE-feature monitoring (Anthropic). **Capability/dataflow control for agents** — CaMeL, LlamaFirewall, Operationalizing CaMeL. **Adversarial evaluation discipline** — HarmBench, AgentDojo, Attacker-Moves-Second framework now de-facto required.

**Top 3 most-cited defense papers (past 18 months):**
1. **Llama Guard 3** / Llama 3 Herd ([arXiv:2407.21783](https://arxiv.org/abs/2407.21783))
2. **Circuit Breakers** (Zou et al. 2024, [arXiv:2406.04313](https://arxiv.org/abs/2406.04313))
3. **Constitutional Classifiers** (Sharma et al. / Anthropic 2025, [arXiv:2501.18837](https://arxiv.org/abs/2501.18837))

Honorable mentions: Refusal Direction (Arditi 2024), Instruction Hierarchy (Wallace 2024).

## Verification notes

Entries that need pre-citation re-verification:

- **Llama Guard 4 12B** — Meta model card and HuggingFace; no formal arXiv paper located as of May 2026.
- **Lakera Guard / PromptGuard tech docs**, **Microsoft Prompt Shields**, **Rebuff**, **LLM Guard**, **Sandwich defense**, **OpenAI Moderation API**, **gpt-oss-safeguard**, **Scaling Monosemanticity** — vendor docs / blogs only; no peer-reviewed paper.
- **Dual-LLM pattern** — Simon Willison blog (2023-04-25); cited in CaMeL paper but no academic primary.
- **arXiv IDs in 25xx/26xx series** (Constitutional Classifiers++, ALERT, Jailbreaking Leaves a Trace, AlphaSteer, Operationalizing CaMeL) — late-2025/2026 numbering; verify final venue assignments.
- **AgentDojo (arXiv:2406.13352), WMDP/RMU (arXiv:2403.03218), BIPIA (arXiv:2312.14197), Tramèr 2020 (arXiv:2002.08347)** — widely-cited; arXiv IDs verified.

**Total entries in this file:** C1: 34 / C2: 14 / C3: 14 / C4: 13 / C5: 15 / C6: 12 → **102 entries**. Note the source dossier footer states ~80 (C1: 27); the actual table in the dossier carries the higher counts here, which this file preserves.

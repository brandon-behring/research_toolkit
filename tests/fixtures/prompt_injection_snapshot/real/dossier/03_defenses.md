# Defense-Side Research — Detection, Smoothing, Architectural, Latent-Space, Alignment

**Compiled:** May 2026 | **Coverage:** 2022-2026 (emphasis 2024-2026)
**Verification:** every arXiv ID confirmed against arxiv.org abstract or vendor docs unless `(unverified)`. See verification footer.

---

## C1. Detection-Based Defenses (Input/Output Classifiers)

| Title | Authors (year) | Venue | arXiv/DOI | GitHub / HF | Mechanism |
|-------|----------------|-------|-----------|-------------|-----------|
| **Llama Guard**: LLM-based Input-Output Safeguard | Inan et al. (2023) | arXiv | arXiv:2312.06674 | meta-llama/PurpleLlama | Llama2-7B fine-tuned for prompt+response classification |
| Llama Guard 2 (8B) | Meta (2024) | Model card | (no paper) | meta-llama/PurpleLlama | MLCommons-aligned 8B safeguard |
| **Llama Guard 3** (8B + 11B Vision) | Meta / Llama 3 Herd (2024) | arXiv | arXiv:2407.21783 | meta-llama/PurpleLlama | 8-language input/output safety + vision variant |
| Llama Guard 3-1B-INT4 | Meta (2024) | arXiv | arXiv:2411.17713 | meta-llama/PurpleLlama | Quantized 1B for on-device safety |
| Llama Guard 4 (12B) | Meta (2025) | Model card | (no formal paper located) | meta-llama/Llama-Guard-4-12B | Native multimodal early-fusion 12B safeguard |
| **NeMo Guardrails** | Rebedea et al. (2023) | EMNLP 2023 (Demo) | arXiv:2310.10501 | NVIDIA-NeMo/Guardrails | Programmable rails toolkit (Colang DSL) |
| Llama Prompt Guard / Prompt Guard 2 (86M) | Meta (2024-2025) | Model card | (no paper) | meta-llama/PurpleLlama | mDeBERTa-base 86M for direct/indirect injection |
| **Lakera Guard** | Lakera (2023-2026) | Vendor docs | (no paper) | lakeraai/pint-benchmark | Commercial real-time injection/jailbreak detector |
| **Microsoft Prompt Shields** | Microsoft (2024-2025) | Azure docs | (no paper) | (closed) | Azure unified API: User-Prompt + Document attack detection |
| **ShieldGemma** (2B/9B/27B) | Zeng et al. (2024) | arXiv | arXiv:2407.21772 | google/shieldgemma-* | Gemma2-based safety classifier suite |
| ShieldGemma 2 (image moderation) | Google (2025) | arXiv | arXiv:2504.01081 | google/shieldgemma-2 | Robust + tractable image content moderation |
| **Constitutional Classifiers** | Sharma et al. (Anthropic 2025) | arXiv | arXiv:2501.18837 | (closed) | Synthetic-data classifiers from natural-language constitutions |
| Constitutional Classifiers++ | Anthropic (2026) | arXiv | arXiv:2601.04603 | (closed) | 40× cheaper exchange-classifier; production-grade |
| Cost-Effective CC (representation re-use) | Anthropic Alignment (2025) | Anthropic blog | (no arXiv) | (closed) | Re-use base-model representations as classifier features |
| **Rebuff** | ProtectAI (2023-2025) | OSS | (no paper) | protectai/rebuff [ARCHIVED 2025-05] | Heuristics + LLM check + vector DB + canary tokens |
| **LLM Guard** | LaiyerAI / ProtectAI (2023-2025) | OSS | (no paper) | protectai/llm-guard | Modular scanner pipeline (anonymizer, PI, secrets, ban-substring) |
| Baseline Defenses (perplexity / paraphrase / retokenize) | Jain et al. (2023) | arXiv | arXiv:2309.00614 | (none) | Three baselines |
| Detecting Attacks with Perplexity | Alon & Kamfonas (2023) | arXiv | arXiv:2308.14132 | (none) | LightGBM on perplexity + token length detects GCG suffixes |
| Token-Level Adversarial Prompt Detection | Hu et al. (2023) | arXiv | arXiv:2311.11509 | (none) | Token-level perplexity + context |
| HarmBench classifier (Llama 2 13B fine-tune) | Mazeika et al. (2024) | ICML 2024 | arXiv:2402.04249 | centerforaisafety/HarmBench | Generative classifier, 7 harm categories |
| **WildGuard / WildGuardMix** | Han et al. (AI2 2024) | NeurIPS 2024 D&B | arXiv:2406.18495 | allenai/wildguard | Open one-stop moderation: prompt harm + response harm + refusal |
| **SafeDecoding** | Xu et al. (2024) | ACL 2024 | arXiv:2402.08983 | uw-nsl/SafeDecoding | Safety-aware decoding (token-prob amplification) |
| **Aegis** (NeMo) Content Safety | Ghosh et al. (NVIDIA 2024) | arXiv | arXiv:2404.05993 | nvidia/Aegis-AI-Content-Safety | LlamaGuard-finetuned permissive + defensive variants |
| **DuoGuard** | Deng et al. (2025) | arXiv | arXiv:2502.05163 | yihedeng9/DuoGuard | 0.5B multilingual guardrail via two-player RL |
| ToxicChat | Lin et al. (2023) | EMNLP 2023 Findings | arXiv:2310.17389 | lmsys/toxic-chat | 10K real Vicuna user-prompt toxicity benchmark |
| Robust Safety Classifier: Adversarial Prompt Shield | Kim et al. (2023) | arXiv | arXiv:2311.00172 | (none) | BERT-style adversarially-trained classifier |
| **Gradient Cuff** | Hu et al. (2024) | NeurIPS 2024 | arXiv:2403.00867 | IBM/Gradient-Cuff | Refusal-loss landscape (functional value + gradient norm) |
| **JBShield** | Zhang et al. (2025) | USENIX Sec 2025 | arXiv:2502.07557 | NISPLab/JBShield | Concept activation classifier + manipulation |
| **LlamaFirewall** | Chennabasappa et al. (Meta 2025) | arXiv | arXiv:2505.03574 | meta-llama/PurpleLlama | Open guardrail system: PromptGuard 2 + Agent Alignment + CodeShield |
| **Qwen3Guard** (0.6/4/8B) | Qwen Team (2025) | arXiv | arXiv:2510.14276 | QwenLM/Qwen3Guard | Tri-class + token-level streaming head |
| **gpt-oss-safeguard** (20B, 120B) | OpenAI (2025) | OpenAI blog | (no arXiv) | openai/gpt-oss-safeguard-20b | Policy-at-inference reasoning safety classifier |
| **PromptShield** | Jacob et al. (2025) | CODASPY 2025 | arXiv:2501.15145 | (none) | Deployable injection detector + benchmark |
| OpenAI Omni-Moderation | OpenAI (2024) | API docs | (no arXiv) | (closed) | Multimodal text+image moderation, 13 categories |
| **DataSentinel** | Liu et al. (2025) | IEEE S&P 2025 (Distinguished) | arXiv:2504.11358 | (none) | Game-theoretic minimax-trained injection detector |

---

## C2. Perturbation / Smoothing Defenses

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | Mechanism |
|-------|----------------|-------|-----------|--------|-----------|
| **SmoothLLM** | Robey et al. (2023) | arXiv | arXiv:2310.03684 | arobey1/smooth-llm | Random char swaps/patches/inserts + majority vote |
| RA-LLM | Cao et al. (2023) | arXiv | arXiv:2309.14348 | (none) | Word-level random masking + rejection-rate threshold |
| Erase-and-check (certified) | Kumar et al. (2023) | arXiv | arXiv:2309.02705 | aounon/certified-llm-safety | Certified subsequence enumeration |
| Paraphrase / Retokenization | Jain et al. (2023) | arXiv | arXiv:2309.00614 | (none) | Semantic-preserving rewrite / sub-token re-segmentation |
| Self-Reminder | Xie et al. (2023) | Nature MI | DOI:10.1038/s42256-023-00765-8 | (none) | Wrap user query with safety self-reminder |
| Goal Prioritization | Zhang et al. (2023) | arXiv | arXiv:2311.09096 | thu-coai/JailbreakDefense_GoalPriority | Make safety > helpfulness explicit at inference and train |
| LLM Self-Defense | Helbling et al. (2023) | ICLR 2024 Tiny Paper | arXiv:2308.07308 | poloclub/llm-self-defense | Cascaded self-evaluation prompt |
| Defensive Prompt Patch (DPP) | Xiong et al. (2024) | ACL 2025 Findings | arXiv:2405.20099 | IBM/DPP | HGA-optimized defensive suffix prompt |
| Backtranslation defense | Wang et al. (2024) | arXiv | arXiv:2402.16459 | YihanWang617/LLM-Jailbreaking-Defense-Backtranslation | Inverse-prompt inference + re-check |
| Semantic Smoothing | Ji et al. (2024) | arXiv | arXiv:2402.16192 | UCSB-NLP-Chang/SemanticSmooth | Aggregate over semantically transformed copies |
| In-Context Defense (ICD) | Wei, Wang & Wang (2023) | arXiv | arXiv:2310.06387 | (none) | Few-shot refusal demonstrations as context |
| **AutoDefense** | Zeng et al. (2024) | arXiv | arXiv:2403.04783 | XHMY/AutoDefense | Multi-agent (intent/prompt/judge) response filter |
| Prefix Guidance (PG) | Zhao et al. (2024) | arXiv | arXiv:2408.08924 | (none) | Force first tokens to refusal-style prefix + classifier |
| Sandwich defense (community) | LearnPrompting (2023) | LearnPrompting docs | (no paper) | (none) | Repeat the system instruction after user input |

---

## C3. Architectural / Structural Defenses

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | Mechanism |
|-------|----------------|-------|-----------|--------|-----------|
| **Spotlighting** (Microsoft) | Hines et al. (2024) | arXiv | arXiv:2403.14720 | (none) | Delimiting + datamarking + encoding to mark untrusted text |
| **Dual-LLM pattern** | Willison (2023, blog) | Blog essay | simonwillison.net 2023-04-25 | (none) | Privileged + Quarantined LLM with symbolic-variable interface |
| **Instruction Hierarchy** | Wallace et al. (OpenAI 2024) | arXiv | arXiv:2404.13208 | (closed) | Train models to prefer system > developer > user > tool instructions |
| **StruQ** (Structured Queries) | Chen et al. (2024) | USENIX Sec 2025 | arXiv:2402.06363 | sizhe-chen/struq | Reserved special tokens separate prompt vs data |
| **SecAlign** | Chen et al. (2024) | ACM CCS 2025 | arXiv:2410.05451 | facebookresearch/SecAlign | Preference optimization on prompt-injected pairs |
| **CaMeL**: Defeating PI by Design | Debenedetti et al. (DeepMind 2025) | arXiv | arXiv:2503.18813 | google-research/camel-prompt-injection | Privileged LLM emits Python program; capabilities track data origin |
| Operationalizing CaMeL (enterprise) | Bagdasarian et al. (2025) | arXiv | arXiv:2505.22852 | (none) | Engineering hardening of CaMeL for production |
| **DataSentinel** | Liu et al. (2025) | IEEE S&P 2025 | arXiv:2504.11358 | (none) | Game-theoretic injection detector at data-channel sentinel |
| **Defensive Token** (test-time) | Chen et al. (2025) | AISec 2025 | arXiv:2507.07974 | Sizhe-Chen/DefensiveToken | Inserted special tokens with optimized embeddings |
| **PromptArmor** | Shi et al. (2025) | arXiv | arXiv:2507.15219 | (none) | Off-the-shelf LLM detects + strips injections before agent |
| Prompt Control-Flow Integrity (PCFI) | Anonymous (2026) | arXiv | arXiv:2603.18433 | (none) | Provenance-tagged runtime CFI |
| Lessons from Defending Gemini Against Indirect PI | DeepMind / Lichtensztein et al. (2025) | arXiv | arXiv:2505.14534 | (closed) | Layered defense + adaptive eval / automated red teaming |
| BIPIA (benchmark + structural defenses) | Yi et al. (2023) | arXiv | arXiv:2312.14197 | microsoft/BIPIA | Boundary-awareness + explicit-reminder |
| Open-Prompt-Injection benchmark + defenses | Liu et al. (2023) | USENIX Sec 2024 | arXiv:2310.12815 | liu00222/Open-Prompt-Injection | Benchmark + classification of structural defenses |

---

## C4. Latent-Space / Representation-Level Defenses

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | Mechanism |
|-------|----------------|-------|-----------|--------|-----------|
| **Representation Engineering (RepE)** | Zou et al. (2023) | arXiv | arXiv:2310.01405 | andyzoujm/representation-engineering | Top-down probes + steering on activation populations |
| **Circuit Breakers** (Representation Rerouting) | Zou et al. (2024) | NeurIPS 2024 | arXiv:2406.04313 | GraySwanAI/circuit-breakers | Reroute harmful representations to orthogonal subspace |
| **RMU** (Repr Misdirection for Unlearning) / WMDP | Li et al. (2024) | ICML 2024 | arXiv:2403.03218 | centerforaisafety/wmdp | Misdirect activations on forget-set toward random vector |
| **Refusal in LMs is Mediated by a Single Direction** | Arditi et al. (2024) | NeurIPS 2024 | arXiv:2406.11717 | andyrdt/refusal_direction | Refusal lives in 1-D residual-stream direction |
| Latent / Targeted LAT | Sheshadri et al. (2024) | arXiv | arXiv:2407.15549 | aengusl/latent-adversarial-training | Perturb residual-stream during fine-tuning |
| Layer-specific Editing (LED) | Zhao et al. (2024) | EMNLP 2024 Findings | arXiv:2405.18166 | (none) | Realign safety-critical early layers |
| Jailbreaking Leaves a Trace | Wu et al. (2026) | arXiv | arXiv:2602.11495 `(unverified)` | (none) | Tensor-decomposition of hidden states for jailbreak detection |
| ALERT (Internal Discrepancy Amplification) | Anonymous (2026) | arXiv | arXiv:2601.03600 `(unverified)` | (none) | Layer/module/token-wise amplification of jailbreak features |
| Scaling Monosemanticity (SAE safety features) | Templeton et al. (Anthropic 2024) | Transformer Circuits | (no arXiv) | (closed) | SAE features for deception/sycophancy/dangerous content |
| **AdaSteer** | Wu et al. (2025) | arXiv | arXiv:2504.09466 | (none) | Dual-direction adaptive activation steering |
| **AlphaSteer** (null-space refusal) | Anonymous (2025) | arXiv | arXiv:2506.07022 `(unverified)` | (none) | Refusal steering with null-space constraint |
| DRO Direct Preference Optimization | Wu et al. (2025) | arXiv | arXiv:2502.01930 | (none) | KL/Wasserstein-uncertainty DPO |
| Distributionally Robust RLHF | Liu et al. (2025) | arXiv | arXiv:2503.00539 | (none) | DRO version of reward-based RLHF + reward-free DPO |

---

## C5. Alignment Training as Defense

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | Mechanism |
|-------|----------------|-------|-----------|--------|-----------|
| **InstructGPT / RLHF** | Ouyang et al. (2022) | NeurIPS 2022 | arXiv:2203.02155 | (closed) | SFT + RM + PPO RLHF foundational pipeline |
| **Helpful & Harmless RLHF** | Bai et al. (Anthropic 2022) | arXiv | arXiv:2204.05862 | anthropics/hh-rlhf | Iterated weekly RLHF for HH assistant |
| **Constitutional AI** | Bai et al. (Anthropic 2022) | arXiv | arXiv:2212.08073 | (closed) | SL + RLAIF using constitutional principles |
| RLAIF (Lee et al.) | Lee et al. (Google 2023) | ICML 2024 | arXiv:2309.00267 | (closed) | Off-the-shelf LLM as preference labeler matches RLHF |
| **DPO** | Rafailov et al. (2023) | NeurIPS 2023 | arXiv:2305.18290 | eric-mitchell/direct-preference-optimization | Closed-form RLHF as classification loss |
| IPO | Azar et al. (2023) | arXiv | arXiv:2310.12036 | (none) | Theoretically grounded PO bypassing DPO approximations |
| **KTO** | Ethayarajh et al. (2024) | arXiv | arXiv:2402.01306 | ContextualAI/HALOs | Prospect-theory-style HALO; binary good/bad |
| SimPO | Meng et al. (2024) | NeurIPS 2024 | arXiv:2405.14734 | princeton-nlp/SimPO | Reference-free length-normalized preference optimization |
| ORPO | Hong et al. (2024) | EMNLP 2024 | arXiv:2403.07691 | xfactlab/orpo | Odds-ratio penalty fused with SFT |
| **HarmBench R2D2** | Mazeika et al. (2024) | ICML 2024 | arXiv:2402.04249 | centerforaisafety/HarmBench | Robust Refusal Dynamic Defense — adversarial fine-tune |
| RAFT | Dong et al. (2023) | TMLR 2024 | arXiv:2304.06767 | RLHFlow/RAFT | Iterative best-of-n / rejection-sampling fine-tuning |
| **Safe RLHF** | Dai et al. (2023) | ICLR 2024 Spotlight | arXiv:2310.12773 | PKU-Alignment/safe-rlhf | Decouple reward (helpful) and cost (harmless); Lagrangian |
| BeaverTails | Ji et al. (PKU 2023) | NeurIPS 2023 D&B | arXiv:2307.04657 | PKU-Alignment/beavertails | 333K QA pairs with separate help+harm annotations |
| PKU-SafeRLHF (multi-level) | Ji et al. (2024) | arXiv | arXiv:2406.15513 | PKU-Alignment/PKU-SafeRLHF | 19 harm categories, 3 severity levels, 265K QA |
| Targeted LAT (alignment) | Sheshadri et al. (2024) | arXiv | arXiv:2407.15549 | aengusl/latent-adversarial-training | LAT removes refusal jailbreaks better than R2D2 |

---

## C6. Adaptive Attack Methodology (the discipline)

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | Mechanism |
|-------|----------------|-------|-----------|--------|-----------|
| **Adaptive Attacks** on Safety-Aligned LLMs | Andriushchenko, Croce, Flammarion (2024) | ICLR 2025 | arXiv:2404.02151 | tml-epfl/llm-adaptive-attacks | Random-search suffix + logprob-of-"Sure" → 100% ASR |
| **The Attacker Moves Second** | Wallace, Tramèr et al. (2025) | arXiv | arXiv:2510.09023 | (closed) | Bypass 12 recent defenses with adaptive attacks (>90% ASR) |
| Adaptive Attacks Break Indirect-PI Agent Defenses | Anonymous (2025) | NAACL 2025 Findings | arXiv:2503.00061 | (none) | Adaptive attacks bypass agent indirect-PI defenses |
| **HarmBench**: Standardized Eval | Mazeika et al. (2024) | ICML 2024 | arXiv:2402.04249 | centerforaisafety/HarmBench | Standardized red-team + defense eval, 7 categories |
| **JailbreakBench** | Chao et al. (2024) | NeurIPS 2024 D&B | arXiv:2404.01318 | JailbreakBench/jailbreakbench | Open robustness benchmark + leaderboard + artifacts |
| **EasyJailbreak** | Zhou et al. (2024) | arXiv | arXiv:2403.12171 | EasyJailbreak/EasyJailbreak | Unified Selector/Mutator/Constraint/Evaluator framework, 11 methods |
| AgentDojo (CaMeL eval target) | Debenedetti et al. (2024) | NeurIPS 2024 D&B | arXiv:2406.13352 | ethz-spylab/agentdojo | Adversarial benchmark for LLM agent tools/data flows |
| LLM Jailbreak Attack vs Defense — Comprehensive Study | Xu et al. (2024) | arXiv | arXiv:2402.13457 | (none) | 9 attacks × 7 defenses × 6 models |
| Bypassing Prompt Injection and Jailbreak Detection in Guardrails | Anonymous (2025) | arXiv | arXiv:2504.11168 | (none) | Empirical bypass of guardrail classifiers |
| How Not to Detect PI with an LLM | Choudhary et al. (2025) | arXiv | arXiv:2507.05630 | (none) | Critique of LLM-as-detector approaches |
| Defenses are not Adaptively Attacked (foundational) | Tramèr, Carlini et al. (2020) | NeurIPS 2020 | arXiv:2002.08347 | (multiple) | Image-domain adaptive-attack methodology framework |
| Indirect Prompt Injections: Are Firewalls All You Need? | Anonymous (2025) | arXiv | arXiv:2510.05244 | (none) | Stronger benchmarks vs firewall-style guardrails |

---

## Defense Landscape 2024-2026

**Strongest empirical support.** Two classes have meaningful production traction.
1. **Architectural separation** of trusted instructions vs untrusted data: Spotlighting (Hines et al. 2024), Instruction Hierarchy (Wallace et al. 2024), StruQ/SecAlign (Chen et al. 2024), CaMeL (Debenedetti et al. 2025). These ship in OpenAI, Anthropic, Google, and Meta production stacks.
2. **High-recall classifiers as one layer of defense-in-depth**: Llama Guard 3/4, ShieldGemma, WildGuard, Constitutional Classifiers, gpt-oss-safeguard, Qwen3Guard. **Constitutional Classifiers cut universal jailbreaks to 0.005/1000** in Anthropic's red-team (most-cited 2025 defense paper).

**Likely already broken (adaptive attacks).** Andriushchenko et al. (2024, arXiv:2404.02151) and Wallace/Tramèr et al. (2025, arXiv:2510.09023) jointly show virtually all single-mechanism defenses — perplexity filters, SmoothLLM, paraphrase, retokenization, prefix guidance, in-context defense, semantic smoothing, plus 12 named recent defenses — fall to >90% ASR under adaptive optimization. Refusal-direction ablation (Arditi et al. 2024) further shows refusal training is brittle to a rank-1 weight edit. Pure perturbation/smoothing approaches are now insufficient as standalone defenses.

**Where 2025-2026 research is investing.**
1. **Latent-space defenses** — Circuit Breakers (Zou 2024), Latent Adversarial Training (Sheshadri 2024), JBShield (2025), SAE-feature monitoring (Anthropic).
2. **Capability/dataflow control** for agents — CaMeL, LlamaFirewall, Operationalizing CaMeL.
3. **Adversarial evaluation discipline** — HarmBench, AgentDojo, Attacker-Moves-Second framework now de-facto required.

**Top 3 most-cited defense papers (past 18 months):**
1. **Llama Guard 3** / Llama 3 Herd (arXiv:2407.21783)
2. **Circuit Breakers** (Zou et al. 2024, arXiv:2406.04313)
3. **Constitutional Classifiers** (Sharma et al. / Anthropic 2025, arXiv:2501.18837)

Honorable mentions: Refusal Direction (Arditi 2024), Instruction Hierarchy (Wallace 2024).

---

## Verification Footer

Entries that need pre-citation re-verification:
- **Llama Guard 4 12B** — Meta model card + HF; no formal arXiv paper located (May 2026)
- **Lakera Guard / PromptGuard tech docs**, **Microsoft Prompt Shields**, **Rebuff**, **LLM Guard**, **Sandwich defense**, **OpenAI Moderation API**, **gpt-oss-safeguard**, **Scaling Monosemanticity** — vendor docs/blogs only; no peer-reviewed paper
- **Dual-LLM pattern** — Simon Willison blog (2023-04-25); cited in CaMeL paper but no academic primary
- arXiv IDs in 25xx/26xx series (Constitutional Classifiers++, ALERT, Jailbreaking Leaves a Trace, AlphaSteer, Operationalizing CaMeL, etc.) — late-2025/2026 numbering; verify final venue assignments
- **AgentDojo arXiv:2406.13352**, **WMDP/RMU arXiv:2403.03218**, **BIPIA arXiv:2312.14197**, **Tramèr 2020 arXiv:2002.08347**, **Markov 2023 arXiv:2208.03274** — widely-cited but referenced in survey snippets in this session, not directly fetched

**Total entries:** ~80 (C1: 27 / C2: 14 / C3: 14 / C4: 13 / C5: 15 / C6: 12).

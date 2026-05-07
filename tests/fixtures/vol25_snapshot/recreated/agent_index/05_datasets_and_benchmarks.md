# 05 — Datasets, benchmarks, leaderboards, CTFs

**Scope:** primary sources on adversarial-prompt evaluation: standardized attack benchmarks, leaderboards, CTF / red-team programs, trustworthiness benchmarks, and dataset releases.
**Out of scope:** open-source toolkits and red-team frameworks (see `06_tools_and_vendors.md`); the underlying attack/defense papers themselves (see `01_direct_attacks.md`, `02_indirect_and_agentic_attacks.md`, `03_defenses.md`).

## A1. Attack benchmarks (HarmBench, JailbreakBench, AdvBench, StrongREJECT)

- **HarmBench** — Mazeika et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2402.04249
  - **Code:** —
  - **Mechanism:** Standardized eval framework for automated red-teaming and refusal robustness.
  - **Result:** Canonical attack benchmark for measuring jailbreak robustness.
  - **Status:** Verified

- **JailbreakBench** — Chao et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2404.01318
  - **Code:** https://github.com/JailbreakBench/jailbreakbench
  - **Mechanism:** Open benchmark for jailbreak attack and defense evaluation.
  - **Result:** Reproducible benchmark with public attack-success leaderboard.
  - **Status:** Verified

- **StrongREJECT** — Souly et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2402.10260
  - **Code:** —
  - **Mechanism:** Critique of weak jailbreak metrics; proposes a stricter StrongREJECT scoring rubric.
  - **Result:** Establishes a higher-quality jailbreak-eval metric.
  - **Status:** Unverified

- **AdvBench (HF)** — walledai (HF 2024).
  - **Source:** https://huggingface.co/datasets/walledai/AdvBench
  - **Code:** https://huggingface.co/datasets/walledai/AdvBench
  - **Mechanism:** HF-hosted release of AdvBench harmful-behavior prompts.
  - **Result:** Hosted release of the canonical AdvBench dataset.
  - **Status:** Unverified

- **JBB-Behaviors (HF)** — JailbreakBench (HF 2024).
  - **Source:** https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors
  - **Code:** https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors
  - **Mechanism:** HF-hosted release of JailbreakBench harmful-behavior templates.
  - **Result:** Hosted release of JBB-Behaviors.
  - **Status:** Unverified

- **JailbreakHub (HF)** — walledai (HF 2024).
  - **Source:** https://huggingface.co/datasets/walledai/JailbreakHub
  - **Code:** https://huggingface.co/datasets/walledai/JailbreakHub
  - **Mechanism:** HF dataset aggregating wild-collected jailbreak prompts.
  - **Result:** Aggregated jailbreak-prompt corpus for evaluation.
  - **Status:** Unverified

- **In-the-wild Jailbreak Prompts (HF)** — TrustAIRLab (HF 2024).
  - **Source:** https://huggingface.co/datasets/TrustAIRLab/in-the-wild-jailbreak-prompts
  - **Code:** https://huggingface.co/datasets/TrustAIRLab/in-the-wild-jailbreak-prompts
  - **Mechanism:** HF dataset of in-the-wild jailbreak prompts.
  - **Result:** Field-collected jailbreak prompts for evaluation.
  - **Status:** Unverified

- **JailBreakV-28K (HF)** — JailbreakV-28K (HF 2024).
  - **Source:** https://huggingface.co/datasets/JailbreakV-28K/JailBreakV-28k
  - **Code:** https://huggingface.co/datasets/JailbreakV-28K/JailBreakV-28k
  - **Mechanism:** HF-hosted release of the JailBreakV-28K multimodal jailbreak benchmark.
  - **Result:** Hosted release of JailBreakV-28K multimodal benchmark.
  - **Status:** Unverified

## A2. Trustworthiness and surveys

- **DecodingTrust** — Wang et al. (arXiv 2023).
  - **Source:** https://arxiv.org/abs/2306.11698
  - **Code:** —
  - **Mechanism:** Multi-axis trustworthiness benchmark covering toxicity, bias, robustness, and ethics dimensions.
  - **Result:** Establishes comprehensive trustworthiness eval suite for GPT models.
  - **Status:** Unverified

- **TrustLLM** — Huang et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2401.05561
  - **Code:** —
  - **Mechanism:** Multi-dimensional trustworthiness benchmark for LLMs.
  - **Result:** Field-level reference benchmark for LLM trustworthiness.
  - **Status:** Unverified

- **Jailbreak Survey (Yi)** — Yi et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2407.04295
  - **Code:** —
  - **Mechanism:** Survey of jailbreak attacks and defenses for LLMs.
  - **Result:** Synthesizes the jailbreak attack/defense literature.
  - **Status:** Unverified

## A3. CTFs, red-team programs, agent benchmarks

- **PINT-benchmark** — Lakera (2024).
  - **Source:** https://github.com/lakeraai/pint-benchmark
  - **Code:** https://github.com/lakeraai/pint-benchmark
  - **Mechanism:** Open benchmark for evaluating prompt-injection detection systems.
  - **Result:** Standardized PI-detection eval suite.
  - **Status:** (vendor blog)

- **Gandalf the Red** — Lakera (arXiv 2025).
  - **Source:** https://arxiv.org/abs/2501.07927
  - **Code:** —
  - **Mechanism:** Academic write-up of the Gandalf adaptive-security CTF.
  - **Result:** Public CTF data published as adaptive-security study.
  - **Status:** Unverified

- **gandalf_ignore_instructions (HF)** — Lakera (HF 2024).
  - **Source:** https://huggingface.co/datasets/Lakera/gandalf_ignore_instructions
  - **Code:** https://huggingface.co/datasets/Lakera/gandalf_ignore_instructions
  - **Mechanism:** HF dataset of Gandalf "ignore instructions" jailbreak attempts.
  - **Result:** Public release of Gandalf attack-attempt corpus.
  - **Status:** (vendor blog)

- **mosscap_prompt_injection (HF)** — Lakera (HF 2024).
  - **Source:** https://huggingface.co/datasets/Lakera/mosscap_prompt_injection
  - **Code:** https://huggingface.co/datasets/Lakera/mosscap_prompt_injection
  - **Mechanism:** HF dataset of Mosscap prompt-injection attempts.
  - **Result:** Companion CTF data to Gandalf for PI evaluation.
  - **Status:** (vendor blog)

- **DEF CON GRT** — Humane Intelligence (2023).
  - **Source:** https://www.humane-intelligence.org/grt
  - **Code:** —
  - **Mechanism:** DEF CON 31 generative-AI red-team challenge with public eval.
  - **Result:** Public-scale GenAI red-team event with structured eval.
  - **Status:** (vendor blog)

- **BrowserART (HF)** — Scale AI (HF 2024).
  - **Source:** https://huggingface.co/datasets/ScaleAI/BrowserART
  - **Code:** https://huggingface.co/datasets/ScaleAI/BrowserART
  - **Mechanism:** HF dataset for the BrowserART browser-agent red-team toolkit.
  - **Result:** Hosted release of BrowserART agent red-team corpus.
  - **Status:** Unverified

- **Llama Guard 3 8B (HF)** — Meta (HF 2024).
  - **Source:** https://huggingface.co/meta-llama/Llama-Guard-3-8B
  - **Code:** https://huggingface.co/meta-llama/Llama-Guard-3-8B
  - **Mechanism:** HF model card for Llama Guard 3 (8B) safety classifier.
  - **Result:** Production-scale safety classifier release.
  - **Status:** Unverified

- **ShieldGemma 2B (HF)** — Google (HF 2024).
  - **Source:** https://huggingface.co/google/shieldgemma-2b
  - **Code:** https://huggingface.co/google/shieldgemma-2b
  - **Mechanism:** HF model card for ShieldGemma 2B safety classifier.
  - **Result:** Open ShieldGemma safety classifier release.
  - **Status:** Unverified

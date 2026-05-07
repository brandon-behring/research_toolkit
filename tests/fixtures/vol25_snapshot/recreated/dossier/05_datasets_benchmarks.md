# Datasets, benchmarks, leaderboards, CTFs

This file collects primary sources on adversarial-prompt evaluation: standardized attack benchmarks, leaderboards, CTF / red-team programs, trustworthiness benchmarks, and dataset releases. Hosted models that double as eval baselines are included where appropriate.

## A1. Attack benchmarks (HarmBench, JailbreakBench, AdvBench, StrongREJECT)

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| HarmBench: A Standardized Evaluation Framework for Automated Red Teaming and Robust Refusal | Mazeika et al. (2024) | arXiv preprint | arXiv:2402.04249 | — | Standardized eval framework for automated red-teaming and refusal robustness. | Canonical attack benchmark for measuring jailbreak robustness. |
| JailbreakBench: An Open Robustness Benchmark for Jailbreaking Large Language Models | Chao et al. (2024) | arXiv preprint | arXiv:2404.01318 | — | Open benchmark for jailbreak attack and defense evaluation. | Reproducible benchmark with public attack-success leaderboard. |
| A StrongREJECT for Empty Jailbreaks | Souly et al. (2024) | arXiv preprint | arXiv:2402.10260 | — | Critique of weak jailbreak metrics; proposes StrongREJECT eval. | Establishes higher-quality jailbreak-eval metric. |
| walledai/AdvBench | walledai (2024) | HF dataset card | (no arXiv) | walledai/AdvBench | HF dataset for AdvBench harmful-behavior prompts. | Hosted release of the canonical AdvBench dataset. |
| JailbreakBench/JBB-Behaviors | JailbreakBench (2024) | HF dataset card | (no arXiv) | JailbreakBench/JBB-Behaviors | HF dataset of JailbreakBench harmful-behavior templates. | Hosted release of JBB-Behaviors. |
| walledai/JailbreakHub | walledai (2024) | HF dataset card | (no arXiv) | walledai/JailbreakHub | HF dataset aggregating wild-collected jailbreak prompts. | Aggregated jailbreak-prompt corpus for evaluation. |
| TrustAIRLab/in-the-wild-jailbreak-prompts | TrustAIRLab (2024) | HF dataset card | (no arXiv) | TrustAIRLab/in-the-wild-jailbreak-prompts | HF dataset of in-the-wild jailbreak prompts. | Field-collected jailbreak prompts for evaluation. |
| JailbreakV-28K/JailBreakV-28k | JailbreakV-28K (2024) | HF dataset card | (no arXiv) | JailbreakV-28K/JailBreakV-28k | HF dataset for the JailBreakV-28K multimodal jailbreak benchmark. | Hosted release of JailBreakV-28K multimodal benchmark. |

## A2. Trustworthiness and surveys

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| DecodingTrust: A Comprehensive Assessment of Trustworthiness in GPT Models | Wang et al. (2023) | arXiv preprint | arXiv:2306.11698 | — | Multi-axis trustworthiness benchmark covering toxicity, bias, robustness, ethics. | Establishes comprehensive trustworthiness eval suite for GPT models. |
| TrustLLM: Trustworthiness in Large Language Models | Huang et al. (2024) | arXiv preprint | arXiv:2401.05561 | — | Comprehensive multi-dimensional trustworthiness benchmark for LLMs. | Field-level reference benchmark for LLM trustworthiness. |
| Jailbreak Attacks and Defenses Against Large Language Models: A Survey | Yi et al. (2024) | arXiv preprint | arXiv:2407.04295 | — | Survey of jailbreak attacks and defenses for LLMs. | Synthesizes the jailbreak attack/defense literature. |

## A3. CTFs, red-team programs, agent benchmarks

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| pint-benchmark: A benchmark for prompt injection detection systems | Lakera (2024) | GitHub repo | (no arXiv) | lakeraai/pint-benchmark | Open benchmark for evaluating prompt-injection detection systems. | Standardized PI-detection eval suite. |
| Gandalf the Red: Adaptive Security for LLMs | Lakera (2025) | arXiv preprint | arXiv:2501.07927 | — | Academic write-up of the Gandalf adaptive-security CTF. | Public CTF data published as adaptive-security study. |
| Lakera/gandalf_ignore_instructions | Lakera (2024) | HF dataset card | (no arXiv) | Lakera/gandalf_ignore_instructions | HF dataset of Gandalf "ignore instructions" jailbreak attempts. | Public release of Gandalf attack-attempt corpus. |
| Lakera/mosscap_prompt_injection | Lakera (2024) | HF dataset card | (no arXiv) | Lakera/mosscap_prompt_injection | HF dataset of Mosscap prompt-injection attempts. | Companion CTF data to Gandalf for PI evaluation. |
| Generative AI Red Teaming Challenge | DEF CON / Humane Intelligence (2023) | Humane Intelligence program page | (no arXiv) | — | DEF CON 31 generative-AI red-team challenge with public eval. | Public-scale GenAI red-team event with structured eval. |
| ScaleAI/BrowserART | Scale AI (2024) | HF dataset card | (no arXiv) | ScaleAI/BrowserART | HF dataset for BrowserART browser-agent red-team toolkit. | Hosted release of BrowserART agent red-team corpus. |
| meta-llama/Llama-Guard-3-8B | Meta (2024) | HF model card | (no arXiv) | meta-llama/Llama-Guard-3-8B | HF model card for Llama Guard 3 (8B) safety classifier. | Production-scale safety classifier release. |
| google/shieldgemma-2b | Google (2024) | HF model card | (no arXiv) | google/shieldgemma-2b | HF model card for ShieldGemma 2B safety classifier. | Open ShieldGemma safety classifier release. |

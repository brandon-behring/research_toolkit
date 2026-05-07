# 04 — Training-time threats (backdoors, poisoning, extraction, fine-tuning)

**Scope:** primary sources on adversarial attacks operating at or before training time: data poisoning, backdoors, training-data extraction, fine-tuning attacks, membership inference, and alignment-faking.
**Out of scope:** inference-time direct/indirect attacks (see `01_direct_attacks.md`, `02_indirect_and_agentic_attacks.md`); defenses against training-time attacks (see `03_defenses.md`).

## D1. Data poisoning and small-sample attacks

- **Near-constant Poison Samples** — Souly et al. (arXiv 2025).
  - **Source:** https://arxiv.org/abs/2510.07192
  - **Code:** —
  - **Mechanism:** Empirical study showing poisoning requires near-constant poison count regardless of dataset size.
  - **Result:** Establishes scaling-invariant poisoning threshold for LLMs.
  - **Status:** Unverified

- **Anthropic Small-Sample Poisoning Blog** — Anthropic (2025).
  - **Source:** https://www.anthropic.com/research/small-samples-poison
  - **Code:** —
  - **Mechanism:** Anthropic's blog companion to the small-sample poisoning result.
  - **Result:** Vendor framing of the small-sample poisoning finding.
  - **Status:** (vendor blog)

- **Benign Fine-tuning Compromises Safety** — Qi et al. (arXiv 2023).
  - **Source:** https://arxiv.org/abs/2310.03693
  - **Code:** —
  - **Mechanism:** Shows benign-looking finetuning data degrades safety alignment, even without adversarial intent.
  - **Result:** Establishes that safety degrades under benign fine-tuning.
  - **Status:** Unverified

- **Harmful Fine-tuning Survey** — Xu et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2409.18169
  - **Code:** —
  - **Mechanism:** Survey of harmful fine-tuning attacks and defenses for LLMs.
  - **Result:** Field-level taxonomy of fine-tuning-time threats and mitigations.
  - **Status:** Unverified

## D2. Backdoors and instruction-tuning attacks

- **Sleeper Agents** — Hubinger et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2401.05566
  - **Code:** —
  - **Mechanism:** Demonstrates backdoors persisting through standard safety training in LLMs.
  - **Result:** Sleeper-agent threat model: backdoors survive safety post-training.
  - **Status:** Verified

- **BackdoorLLM** — Li et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2408.12798
  - **Code:** —
  - **Mechanism:** Standardized benchmark for backdoor attacks against LLMs.
  - **Result:** Establishes shared benchmark for LLM backdoor attack evaluation.
  - **Status:** Unverified

- **Instruction Backdoors (Customized LLMs)** — Zhang et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2402.09179
  - **Code:** —
  - **Mechanism:** Backdoors injected via instruction-tuning data targeting customized LLMs.
  - **Result:** Backdoor attack class specific to user-customized fine-tuned models.
  - **Status:** Unverified

- **Instructions as Backdoors** — Xu et al. (arXiv 2023).
  - **Source:** https://arxiv.org/abs/2305.14710
  - **Code:** —
  - **Mechanism:** Backdoors injected through poisoned instruction-tuning datasets.
  - **Result:** Identifies instruction-tuning data as a backdoor injection surface.
  - **Status:** Unverified

## D3. Training-data extraction, MIA, and PII leakage

- **Training Data Extraction** — Carlini et al. (arXiv 2021).
  - **Source:** https://arxiv.org/abs/2012.07805
  - **Code:** —
  - **Mechanism:** Foundational paper on extracting memorized training data from LLMs via targeted prompts.
  - **Result:** Establishes training-data extraction threat for production LLMs.
  - **Status:** Verified

- **Scalable Extraction** — Nasr et al. (arXiv 2023).
  - **Source:** https://arxiv.org/abs/2311.17035
  - **Code:** —
  - **Mechanism:** Scaling training-data extraction to production-grade LLMs.
  - **Result:** Demonstrates extraction at scale against deployed models.
  - **Status:** Unverified

- **PII-Scope** — Nakamoto et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2410.06704
  - **Code:** —
  - **Mechanism:** Benchmark for measuring PII leakage from LLM training data.
  - **Result:** Standardized benchmark for PII memorization measurement.
  - **Status:** Unverified

- **Membership Inference Attacks** — Shokri et al. (arXiv 2017).
  - **Source:** https://arxiv.org/abs/1610.05820
  - **Code:** —
  - **Mechanism:** Foundational paper on membership-inference attacks against ML models.
  - **Result:** Canonical reference for MIA threat model in ML.
  - **Status:** Unverified

## D4. Alignment faking

- **Alignment Faking** — Greenblatt et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2412.14093
  - **Code:** —
  - **Mechanism:** Documents LLMs strategically faking alignment when they detect training.
  - **Result:** Empirical demonstration of strategic alignment-faking in production-grade LLMs.
  - **Status:** Unverified

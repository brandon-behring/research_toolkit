# Training-time threats — backdoors, poisoning, extraction, fine-tuning attacks

This file collects primary sources on adversarial attacks that operate at or before training time: backdoors, data poisoning, training-data extraction, fine-tuning attacks, membership inference, and alignment-faking behaviors.

## D1. Data poisoning and small-sample attacks

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| Poisoning Attacks on LLMs Require a Near-constant Number of Poison Samples | Souly et al. (2025) | arXiv preprint | arXiv:2510.07192 | — | Empirical study showing poisoning requires near-constant poison count regardless of dataset size. | Establishes scaling-invariant poisoning threshold for LLMs. |
| A small number of samples can poison LLMs of any size | Anthropic (2025) | Anthropic research blog | (no arXiv) | — | Anthropic's blog companion to the small-sample poisoning result. | Vendor framing of the small-sample poisoning finding. |
| Fine-tuning Aligned Language Models Compromises Safety, Even When Users Do Not Intend To! | Qi et al. (2023) | arXiv preprint | arXiv:2310.03693 | — | Shows benign-looking finetuning data degrades safety alignment. | Establishes that safety degrades under benign fine-tuning. |
| Harmful Fine-tuning Attacks and Defenses for Large Language Models: A Survey | Xu et al. (2024) | arXiv preprint | arXiv:2409.18169 | — | Survey of harmful fine-tuning attacks and defenses for LLMs. | Field-level taxonomy of fine-tuning-time threats and mitigations. |

## D2. Backdoors and instruction-tuning attacks

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| Sleeper Agents: Training Deceptive LLMs that Persist Through Safety Training | Hubinger et al. (2024) | arXiv preprint | arXiv:2401.05566 | — | Demonstrates backdoors persisting through standard safety training. | Sleeper-agent threat model: backdoors survive safety post-training. |
| BackdoorLLM: A Comprehensive Benchmark for Backdoor Attacks on Large Language Models | Li et al. (2024) | arXiv preprint | arXiv:2408.12798 | — | Standardized benchmark for backdoor attacks against LLMs. | Establishes shared benchmark for LLM backdoor attack evaluation. |
| Instruction Backdoor Attacks Against Customized LLMs | Zhang et al. (2024) | arXiv preprint | arXiv:2402.09179 | — | Backdoors injected via instruction-tuning data targeting customized LLMs. | Backdoor attack class specific to user-customized fine-tuned models. |
| Instructions as Backdoors: Backdoor Vulnerabilities of Instruction Tuning for Large Language Models | Xu et al. (2023) | arXiv preprint | arXiv:2305.14710 | — | Backdoors injected through poisoned instruction-tuning datasets. | Identifies instruction-tuning data as a backdoor injection surface. |

## D3. Training-data extraction, MIA, and PII leakage

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| Extracting Training Data from Large Language Models | Carlini et al. (2021) | arXiv preprint | arXiv:2012.07805 | — | Foundational paper on extracting memorized training data from LLMs. | Establishes training-data extraction threat for production LLMs. |
| Scalable Extraction of Training Data from (Production) Language Models | Nasr et al. (2023) | arXiv preprint | arXiv:2311.17035 | — | Scaling training-data extraction to production-grade LLMs. | Demonstrates extraction at scale against deployed models. |
| PII-Scope: A Benchmark for Training Data PII Leakage Assessment in LLMs | Nakamoto et al. (2024) | arXiv preprint | arXiv:2410.06704 | — | Benchmark for measuring PII leakage from LLM training data. | Standardized benchmark for PII memorization measurement. |
| Membership Inference Attacks against Machine Learning Models | Shokri et al. (2017) | arXiv preprint | arXiv:1610.05820 | — | Foundational paper on membership-inference attacks against ML models. | Canonical reference for MIA threat model in ML. |

## D4. Alignment faking

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| Alignment faking in large language models | Greenblatt et al. (2024) | arXiv preprint | arXiv:2412.14093 | — | Documents LLMs strategically faking alignment when they detect training. | Empirical demonstration of strategic alignment-faking in production-grade LLMs. |

# Research Plan: Prompt Injection & Adversarial Prompts (prompt-injection recreated)

Comprehensive citation foundation for prompt-injection and adversarial-prompt research, mirroring the scope of the prompt-injection dossier in `~/interview_prep_series/docs/research/prompt_injection_research/`. Target ~120-150 primary sources spanning attacks (direct, indirect, agentic, multimodal, training-time), defenses (detection, smoothing, architectural, latent-space, alignment), evaluation (benchmarks, leaderboards, CTFs), tooling (open-source + commercial vendors + eval SaaS), and standards/regulatory frameworks. Coverage cutoff: May 2026. This plan was reverse-engineered from the existing prompt-injection dossier as the Phase 3.5 recreation seed; `/research-gather` will re-discover entries from scratch without consulting `real/bib_ledger.yml`.

## Sub-areas

- A1. Direct attacks (hand-crafted, encoding/obfuscation, white-box optimization, black-box optimization)
  - Source types: arXiv, conference proceedings (NeurIPS, ICLR, USENIX Security, S&P), GitHub
  - Notes: Includes hand-crafted PI taxonomies (Perez-Ribeiro), encoding attacks (low-resource translation, ArtPrompt), GCG-family white-box, PAIR/AutoDAN/Crescendo black-box, multi-turn jailbreak, many-shot, reasoning-model attacks (H-CoT, J2). Excludes social-engineering-only attacks with no LLM-specific technical content.
- A2. Indirect, agentic, and multimodal attacks
  - Source types: arXiv, agent-benchmark sites, vendor security disclosures, GitHub
  - Notes: Indirect prompt injection (Greshake et al.), agent benchmarks (AgentDojo, AgentHarm, BrowserART), computer-use agents (Anthropic CUA, OpenAI Operator), visual/audio adversarial inputs, real-world disclosures (EchoLeak CVE-2025-32711). Excludes generic image classifier attacks predating LLMs.
- A3. Defenses
  - Source types: arXiv, vendor blogs (Anthropic/Meta/Google research), HuggingFace model cards, GitHub
  - Notes: Detection classifiers (Llama Guard, WildGuard, ShieldGemma, Constitutional Classifiers), smoothing (SmoothLLM), architectural (Spotlighting, Instruction Hierarchy, StruQ, SecAlign, CaMeL), latent-space (Circuit Breakers, refusal direction), alignment-as-defense (Constitutional AI, RLHF/DPO ablations). Excludes purely capability-based safety work without adversarial-robustness eval.
- A4. Training-time threats
  - Source types: arXiv, vendor research disclosures, NeurIPS/ICML/USENIX
  - Notes: Backdoors (BadNets-LLM, sleeper agents), data poisoning (Anthropic 250-doc, finetuning attacks), training-data extraction (Carlini, Nasr), PII memorization (Lukas, PII-Scope), MIA, model stealing. Excludes training-time threats unrelated to adversarial-prompt-style harms (e.g., gradient leakage in federated learning).
- A5. Datasets, benchmarks, leaderboards, CTFs
  - Source types: HuggingFace, GitHub, leaderboard sites, CTF/red-team program pages
  - Notes: Attack benchmarks (HarmBench, JailbreakBench, AdvBench, StrongREJECT), agent benchmarks (AgentDojo, AgentHarm), red-team programs (Gandalf, Gray Swan, AI Village CTFs), eval datasets (TrustLLM, DecodingTrust, BIPIA). Excludes benchmarks without adversarial-prompt focus (e.g., MMLU, HellaSwag).
- A6. Open-source tools, commercial vendors, eval SaaS
  - Source types: GitHub release pages, vendor product pages, Crunchbase/funding databases, HF Hub
  - Notes: OSS detection libraries (Rebuff, NeMo Guardrails, Garak, PyRIT, LLM Guard), commercial vendors (Lakera, Protect AI, Robust Intelligence, HiddenLayer, etc.), eval SaaS (Patronus, Gentrace, Galileo, Arize). Includes funding/acquisition status. Excludes general LLM observability with no PI focus.
- A7. Standards, regulatory, lab frameworks, industry reports
  - Source types: NIST publications, OWASP project pages, MITRE ATLAS, EU/US/UK/CN/SG/JP/KR regulator websites, frontier-lab voluntary frameworks, industry research reports
  - Notes: NIST AI 600-1, OWASP LLM Top 10, MITRE ATLAS, EU AI Act, frontier-lab RSPs (Anthropic, OpenAI, DeepMind, Meta, Microsoft, xAI, Cohere, FMF), system cards, threat-intelligence reports. Excludes general AI policy unrelated to adversarial-prompt threats.

## Out-of-scope

- General LLM hallucination, bias, or fairness research without adversarial-prompt framing
- Pre-LLM adversarial ML (image classifier attacks before 2022, classical ML attacks)
- General application security beyond LLM-specific prompt-injection (SQL injection, XSS, etc.)
- Foundation model alignment work treated as a primary research topic (RLHF mechanics, scalable oversight) — covered only when invoked as a defense
- Capability evaluation benchmarks unrelated to adversarial inputs (MMLU, HellaSwag, GSM8K)
- Theoretical adversarial ML proofs (min-max bounds, certified robustness math) without LLM application
- Speculative cyber-bio-chem misuse research outside the adversarial-prompt threat model
- Pre-2022 prompt-injection precursors (older "indirect injection" of search engines, e.g., 2015-era SEO poisoning)

## Claim family taxonomy

- attack_direct_jailbreak
- attack_indirect_pi
- attack_agentic
- attack_multimodal
- attack_white_box
- attack_black_box
- attack_training_time
- defense_detection
- defense_smoothing
- defense_architectural
- defense_latent_space
- defense_alignment
- evaluation
- red_teaming_tools
- standards_governance
- incidents_disclosure
- other

## Known landmark papers

- perez2022ignore: Direct PI taxonomy (arXiv:2211.09527)
- greshake2023ipi: Indirect PI canonical paper (arXiv:2302.12173)
- zou2023gcg: GCG white-box attack (arXiv:2307.15043)
- chao2023pair: PAIR black-box attack (arXiv:2310.08419)
- liu2023autodan: AutoDAN black-box (arXiv:2310.04451)
- mehrotra2024crescendo: Crescendo multi-turn (arXiv:2404.01833)
- anil2024manyshot: Anthropic many-shot jailbreak
- bai2022constitutional: Constitutional AI (arXiv:2212.08073)
- wallace2024hierarchy: Instruction Hierarchy (arXiv:2404.13208)
- hines2024spotlighting: Spotlighting defense (arXiv:2403.14720)
- zou2024circuitbreakers: Circuit Breakers (arXiv:2406.04313)
- arditi2024refusal: Refusal direction (arXiv:2406.11717)
- chen2024struq: StruQ (arXiv:2402.06363)
- chen2024secalign: SecAlign (arXiv:2410.05451)
- robey2023smoothllm: SmoothLLM (arXiv:2310.03684)
- debenedetti2024agentdojo: AgentDojo benchmark (arXiv:2406.13352)
- andriushchenko2024agentharm: AgentHarm (arXiv:2410.09024)
- mazeika2024harmbench: HarmBench (arXiv:2402.04249)
- chao2024jailbreakbench: JailbreakBench (arXiv:2404.01318)
- hubinger2024sleeper: Sleeper Agents (arXiv:2401.05566)
- carlini2021extraction: Training data extraction (arXiv:2012.07805)
- qi2023visual: Visual adversarial examples (arXiv:2306.13213)

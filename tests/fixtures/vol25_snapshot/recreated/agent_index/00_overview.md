# Overview — Prompt Injection & Adversarial Prompts (vol25 recreated)

**Purpose:** orient the reader to the threat model, terminology, and structural taxonomy used across the rest of this synthesis.
**Scope:** prompt-injection and adversarial-prompt research published 2021–2026; coverage cutoff May 2026.
**Out of scope:** general LLM hallucination, fairness/bias research without adversarial framing, pre-LLM adversarial ML, classical app security (SQL/XSS).
**Last updated:** 2026-05-07.

## Threat model summary

Prompt injection (PI) is a class of attack on LLM-integrated systems where an adversary causes the model to deviate from its developer-specified instructions by introducing instructions through input channels the developer treats as data. Three canonical sub-classes:

- **Direct PI / jailbreak:** the user is the attacker; their prompt is the attack surface.
- **Indirect PI:** an attacker plants instructions in third-party content (web pages, emails, documents) that the LLM later retrieves; the user is a victim, not the attacker.
- **Agentic PI:** an LLM agent's tool outputs (search results, file contents, screenshots) become the injection vector; effects compound across tool calls.

Two adjacent threat classes are included in this synthesis because they share defenses and evaluation infrastructure with PI: training-time threats (backdoors, poisoning, alignment-faking) and multimodal adversarial inputs (vision/audio injections).

## Glossary

- **PI / Prompt Injection** — adversarial instruction inserted via an input channel the system treats as data. (Greshake et al. 2023 for indirect PI; Perez & Ribeiro 2022 for direct PI.)
- **IPI / Indirect Prompt Injection** — PI variant where the injection arrives via retrieved third-party content. (Greshake et al. 2023.)
- **Jailbreak** — attack causing an aligned LLM to produce content it was trained to refuse. Often used interchangeably with direct PI.
- **GCG / Greedy Coordinate Gradient** — white-box adversarial-suffix optimization attack. (Zou et al. 2023, arXiv:2307.15043.)
- **PAIR** — black-box jailbreak that uses an attacker LLM to query the target. (Chao et al. 2023, arXiv:2310.08419.)
- **AutoDAN** — genetic-algorithm jailbreak generating fluent attack prompts. (Liu et al. 2023, arXiv:2310.04451.)
- **TAP / Tree of Attacks** — tree-search black-box jailbreak. (Mehrotra et al. 2023, arXiv:2312.02119.)
- **Crescendo** — multi-turn jailbreak that escalates a benign topic. (Russinovich et al. 2024, arXiv:2404.01833.)
- **Many-shot jailbreaking** — in-context attack using many fake-assistant turns. (Anil et al. 2024, Anthropic.)
- **Constitutional AI** — RLAIF training using a constitution to drive harmlessness. (Bai et al. 2022, arXiv:2212.08073.)
- **Constitutional Classifiers** — input-output classifiers trained against a constitution. (Sharma et al. 2025, arXiv:2501.18837.)
- **Llama Guard** — open input/output safety classifier from Meta. (Inan et al. 2023, arXiv:2312.06674.)
- **Circuit Breakers** — latent-space defense rerouting harmful representations. (Zou et al. 2024, arXiv:2406.04313.)
- **Refusal direction** — single-direction representation mediating refusal. (Arditi et al. 2024, arXiv:2406.11717.)
- **Spotlighting** — input-marking defense against indirect PI. (Hines et al. 2024, arXiv:2403.14720.)
- **Instruction Hierarchy** — training that enforces precedence among system/user/tool instructions. (Wallace et al. 2024, arXiv:2404.13208.)
- **StruQ** — structured-query architectural defense. (Chen et al. 2024, arXiv:2402.06363.)
- **SecAlign** — preference-optimization defense against PI. (Chen et al. 2024, arXiv:2410.05451.)
- **CaMeL** — capability-controlled architectural defense. (Debenedetti et al. 2025, arXiv:2503.18813.)
- **SmoothLLM** — randomized-perturbation smoothing defense. (Robey et al. 2023, arXiv:2310.03684.)
- **AgentDojo** — dynamic agent benchmark for PI attacks/defenses. (Debenedetti et al. 2024, arXiv:2406.13352.)
- **AgentHarm** — agentic harmfulness benchmark. (Andriushchenko et al. 2024, arXiv:2410.09024.)
- **HarmBench** — automated red-teaming benchmark. (Mazeika et al. 2024, arXiv:2402.04249.)
- **JailbreakBench** — open jailbreak robustness benchmark. (Chao et al. 2024, arXiv:2404.01318.)
- **AdvBench** — harmful-behavior dataset. (walledai HF release.)
- **StrongREJECT** — improved jailbreak success metric. (Souly et al. 2024, arXiv:2402.10260.)
- **BIPIA** — indirect-PI benchmark. (Yi et al. 2023, arXiv:2312.14197.)
- **InjecAgent** — IPI benchmark for tool-using agents. (Zhan et al. 2024, arXiv:2403.02691.)
- **EchoLeak / CVE-2025-32711** — first widely-disclosed real-world zero-click PI exploit. (Reddy 2025; Microsoft Copilot.)
- **Sleeper Agents** — backdoors persisting through safety training. (Hubinger et al. 2024, arXiv:2401.05566.)
- **Alignment faking** — strategic deception during training. (Greenblatt et al. 2024, arXiv:2412.14093.)
- **Red-team CTF** — capture-the-flag-style adversarial event for LLMs (e.g., Gandalf, Mosscap, DEF CON GRT).
- **OWASP LLM Top 10** — OWASP project listing top LLM application risks; LLM01 is prompt injection.
- **NIST AI 600-1** — NIST AI RMF generative-AI profile.
- **MITRE ATLAS** — adversarial-AI threat catalog modeled after ATT&CK.
- **RSP / Preparedness Framework / FSF** — frontier-lab voluntary safety frameworks (Anthropic / OpenAI / DeepMind respectively).

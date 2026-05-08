# Prompt Injection — Threat Model, Taxonomy, Timeline, Glossary

<!-- AGENT-INDEX: keep this block stable; future agents read it first. -->
**Scope:** Threat model, taxonomy, historical timeline, glossary, and reading routes for the prompt-injection literature. The synthesizing top-of-funnel layer.
**Out of scope:** Per-paper detail — see 01–07 topic files. No defense recommendations specific to a stack — see `03_defenses.md`. No vendor / tool comparisons — see `06_tools_and_vendors.md`.
**Coverage window:** 2022–2026 (emphasis 2024–2026).
**Last updated:** 2026-05-06.
**Subsections (stable anchors):** What is prompt injection · Five-threat distinction · Attacker-capability ladder · Six-surface attack-surface map · OWASP LLM Top 10 (2025) · Standards landscape · Timeline of pivotal moments · Reading routes · Glossary.
**Key terms covered:** Prompt injection (direct + indirect), Jailbreak, Adversarial suffix, Sleeper backdoor, GCG, AutoDAN, PAIR, TAP, Crescendo, Many-shot, Best-of-N, ArtPrompt, Greshake indirect PI, Spotlighting, CaMeL, Circuit Breakers, Constitutional Classifiers, Llama Guard, ShieldGemma, WildGuard, OWASP LLM01–LLM10, MITRE ATLAS, NIST AI 600-1 MP-2.3-005, ISO/IEC 42001, EU AI Act Article 15, ASR, Threat model, Attack surface, Black-box vs white-box adversary, Indirect-content writer, Training-data writer.
**Related files:** `README.md` (lookup recipes), `01–07` (per-topic depth), `07_standards_and_industry.md` (compliance stack).

## What is prompt injection

**Prompt injection** is the class of attacks in which adversarial input causes a language model to ignore or override its system instructions, reveal protected content, or take an action the deployer did not authorize. The term was coined in September 2022 by Riley Goodside, popularized by Simon Willison's blog post the same month, and formalized in November 2022 by Perez & Ribeiro's *"Ignore Previous Prompt"* — the first systematic framework, which split prompt-injection attacks into two canonical classes: **goal hijacking** (force an action the model would otherwise refuse) and **prompt leaking** (force disclosure of the system prompt or other privileged context).

Prompt injection comes in two delivery modes that the literature treats as separate threat classes:

- **Direct prompt injection** — the attacker controls the user-facing input channel. Simple to demonstrate (paste an adversarial prompt into ChatGPT). All of `01_direct_attacks.md` covers this surface.
- **Indirect prompt injection** — the attacker controls *content the model retrieves or processes* (a webpage, an email, a PDF, a database record, an image, a tool output). Greshake et al. (2023) introduced the term and showed that any LLM-integrated application that ingests untrusted content is exposed. All of `02_indirect_and_agentic_attacks.md` covers this surface.

The defender's hard problem is that LLM input is unstructured: trusted instructions, untrusted user text, and untrusted retrieved content all share the same token stream. Without architectural separation (instruction hierarchy, capability-tracking dataflow control, or external classifiers), the model has no robust way to tell them apart. This is the load-bearing observation behind every defense in `03_defenses.md`.

## The five threats people call "jailbreak"

`#five-threats`

Treating "jailbreak" as one thing erases security-relevant distinctions. Five distinct threats often share the label:

1. **Alignment failure** — the model is unsafe by default in some scenarios; not adversarial, just under-trained. (Mitigation: alignment training. See `03_defenses.md` § C5.)
2. **Jailbreak** — adversarial direct user input that elicits refused outputs. (See `01_direct_attacks.md` §§ A1–A5.)
3. **Direct prompt injection** — adversarial direct user input that overrides system instructions or extracts protected context. Often co-occurs with jailbreak. (See `01_direct_attacks.md` § A1.)
4. **Indirect prompt injection** — adversarial *retrieved* content (webpage, email, tool output) that overrides instructions. Most production-relevant — EchoLeak (CVE-2025-32711) is the canonical real-world incident. (See `02_indirect_and_agentic_attacks.md` § B1.)
5. **Sleeper backdoor** — model was poisoned or backdoored at training time and behaves correctly until a trigger fires. Survives safety fine-tuning. (See `04_training_time_threats.md` § D1.)

Defenses are not interchangeable across these classes: a jailbreak classifier does nothing about a sleeper agent; instruction-hierarchy training does nothing about training-time poisoning.

## Attacker-capability ladder

`#attacker-ladder`

Attacks differ less by technique than by what surface the attacker can write to. Five rungs, weakest to strongest:

1. **Black-box API** — attacker can call the model and read outputs. Examples: PAIR, TAP, Crescendo, Many-shot.
2. **Grey-box (logits)** — attacker can read token-level probabilities. Examples: BEAST, Best-of-N adaptive variants.
3. **Open-weights white-box** — attacker has gradients on the deployed model (or a near-equivalent surrogate). Examples: GCG, AutoDAN, ARCA, AmpleGCG, I-GCG.
4. **Indirect-content writer** — attacker can place content on a page, email, tool, or document the model reads. Examples: Greshake indirect PI, PoisonedRAG, EchoLeak, MCPTox.
5. **Training-data writer** — attacker contributes to the training corpus, the instruction-tuning data, or the RLHF preferences. Examples: Sleeper Agents, AutoPoison, Universal Jailbreak Backdoors, Persistent Pre-training Poisoning (250-doc).

The two top rungs (4–5) are where production-grade harm originates: an attacker who can write a webpage or contribute one document to a training corpus does not need to break alignment training to compromise downstream agents.

## Six attack surfaces

`#attack-surfaces`

Cross the five attacker rungs with the channel through which input reaches the model:

| Surface | Examples | Primary section |
|---|---|---|
| System prompt | Application-controlled instructions | `03_defenses.md` § C3 (Instruction Hierarchy, StruQ) |
| User input | Chatbox, API, agent prompt | `01_direct_attacks.md` (all) |
| Retrieved context | RAG, search, document upload | `02_indirect_and_agentic_attacks.md` § B1 |
| Tool output | Function-call return, MCP-server response | `02_indirect_and_agentic_attacks.md` § B2 |
| Multimodal channel | Image, audio, video, screen content | `02_indirect_and_agentic_attacks.md` §§ B3, B4 |
| Training data | Pre-training corpus, SFT data, RLHF prefs | `04_training_time_threats.md` (all) |

A defense that only addresses one surface (e.g., classifying user prompts) leaves the other five surfaces exposed.

## OWASP LLM Top 10 (2025)

`#owasp-llm-top-10`

OWASP's Generative AI Security Project published the v2025 list in November 2024. One-liner per risk:

- **LLM01 — Prompt Injection.** Direct and indirect injection. The #1 risk; the rest of this document maps to LLM01 directly or indirectly.
- **LLM02 — Sensitive Information Disclosure.** PII, secrets, system prompts revealed via inference-time extraction or memorization.
- **LLM03 — Supply Chain.** Compromised models, datasets, plugins. See `04_training_time_threats.md` (PoisonGPT, RIPPLeS).
- **LLM04 — Data and Model Poisoning.** Training-time compromise. See `04_training_time_threats.md` § D2.
- **LLM05 — Improper Output Handling.** Downstream injection (Markdown image exfiltration, XSS via LLM output, code execution from generated code).
- **LLM06 — Excessive Agency.** Agent over-permissioned; confused-deputy attacks via tool use. See `02_indirect_and_agentic_attacks.md` § B2.
- **LLM07 — System Prompt Leakage.** Adversary recovers the protected system prompt via PI / memorization. See `01_direct_attacks.md` § A1, `04_training_time_threats.md` § D5.
- **LLM08 — Vector and Embedding Weaknesses.** RAG poisoning, embedding inversion, retriever attacks. See `02_indirect_and_agentic_attacks.md` § B1.
- **LLM09 — Misinformation.** Hallucinations and ungrounded outputs at scale. Adjacent rather than central; see `05_datasets_and_benchmarks.md` § Datasets-H.
- **LLM10 — Unbounded Consumption.** Resource exhaustion / denial-of-service on inference; cost amplification.

For the depth treatment of how each LLM0n maps to research and defenses, see `07_standards_and_industry.md` § Standards Frameworks.

## Standards landscape at a glance

`#standards-landscape`

- **OWASP LLM Top 10 (2025)** — Application-developer's working checklist; v2025 released November 2024. LLM01 is prompt injection. See `07_standards_and_industry.md`.
- **MITRE ATLAS** — TTP knowledge base for AI/ML, ATT&CK-style. Current release v5.6.0 (May 2026); for live tactic/technique counts and case studies (including EchoLeak and Cursor MCP exfiltration) see https://atlas.mitre.org/. See `07_standards_and_industry.md`.
- **NIST AI 600-1 (Generative AI Profile, July 2024)** — Mandates pre- and post-deployment adversarial testing (control MP-2.3-005). Not satisfied by vendor attestation alone. See `07_standards_and_industry.md`.
- **ISO/IEC 42001:2023** — World's first certifiable AI Management System. Names prompt injection and tool abuse; required for procurement in growing share of EU/US/JP enterprises. See `07_standards_and_industry.md`.
- **EU AI Act, Regulation (EU) 2024/1689** — Article 15 on accuracy, robustness, and cybersecurity becomes enforceable **2 August 2026** for high-risk systems. Most aggressive binding regulation on adversarial robustness. Article 55 imposes systemic-risk evaluations on GPAI providers. See `07_standards_and_industry.md`.

## Timeline of pivotal moments

`#timeline`

A dated bullet list of what shifted the field. Not exhaustive — the canonical landmarks only.

- **Sep 2022** — Riley Goodside posts the *"Translate to French / Haha pwned"* demonstration. Simon Willison blogs about it and names the attack class **prompt injection**.
- **Nov 2022** — Perez & Ribeiro's *"Ignore Previous Prompt"* (NeurIPS ML Safety Workshop, Best Paper) is the first systematic PI framework. Defines goal hijacking + prompt leaking.
- **Feb 2023** — Greshake et al., *"Not what you've signed up for"* (AISec 2023). First **indirect** PI taxonomy. Establishes the remote-code-execution analogy: any LLM-integrated app that reads untrusted content is exposed.
- **Jul 2023** — Zou et al. introduce **GCG** (Greedy Coordinate Gradient, arXiv:2307.15043). Foundational white-box jailbreak; suffixes transfer across ChatGPT, Claude, Bard, Llama-2.
- **Oct 2023** — Chao et al. release **PAIR** (Prompt Automatic Iterative Refinement, arXiv:2310.08419). Foundational black-box / LLM-on-LLM jailbreak in <20 queries.
- **Jan 2024** — Hubinger et al. publish **Sleeper Agents** (Anthropic, arXiv:2401.05566). Backdoored LLMs persist through SFT, RL, and adversarial training.
- **Feb 2024** — Mazeika et al. release **HarmBench** (ICML 2024, arXiv:2402.04249); 510 behaviors across 7 categories with adversarial training defense (R2D2). Establishes shared eval substrate.
- **Apr 2024** — Four landmark papers within weeks: **JailbreakBench** (NeurIPS D&B), **Many-shot Jailbreaking** (Anthropic), **Crescendo** (Microsoft, arXiv:2404.01833), and **Instruction Hierarchy** (OpenAI, arXiv:2404.13208). Multi-turn and agentic threat models become first-class.
- **Jun 2024** — Zou et al., **Circuit Breakers** (NeurIPS 2024, arXiv:2406.04313). Latent-space defense reroutes harmful representations to orthogonal subspace.
- **Oct 2024** — Zhang et al., **Persistent Pre-training Poisoning** (arXiv:2410.13722). 0.1% pre-training poison persists through SFT+DPO.
- **Jan 2025** — Sharma et al., **Constitutional Classifiers** (Anthropic, arXiv:2501.18837). 3,000+ red-team hours found no universal jailbreak; reported 0.38% increase in over-refusals and ~23.7% inference overhead.
- **May 2025** — Anthropic activates **ASL-3 deployment standard** with Claude Opus 4 (Responsible Scaling Policy v3). **EchoLeak / CVE-2025-32711** (June 2025) becomes the first documented zero-click indirect-PI exploit in a production LLM (Microsoft 365 Copilot, CVSS 9.3).
- **Oct 2025** — Souly et al. (Anthropic + UK AISI + Alan Turing) publish the **250-document poisoning result** (arXiv:2510.07192). ~250 documents are sufficient to backdoor models from 600M to 13B parameters.
- **Nov 2025** — Bisconti, Prandi, Pierucci et al. release **Adversarial Poetry** (arXiv:2511.15304). Verse-form prompts achieve 18× ASR vs prose; >90% ASR on some providers.
- **Aug 2026** — **EU AI Act Article 15** becomes enforceable. Adversarial robustness moves from voluntary to binding for high-risk systems.

## Reading routes

`#reading-routes`

Pre-built sequences for common roles. Read in order; cross-reference as needed.

- **Defender (designing or evaluating a guardrail).** `03_defenses.md` (especially C1, C3, C6) → `07_standards_and_industry.md` (compliance posture) → `06_tools_and_vendors.md` (vendor selection) → `05_datasets_and_benchmarks.md` (eval suites).
- **Red-teamer / attacker (offensive evaluation).** `01_direct_attacks.md` (all) → `02_indirect_and_agentic_attacks.md` (all) → `04_training_time_threats.md` (durable compromises) → `05_datasets_and_benchmarks.md` § CTFs (live programs).
- **Evaluator (picking a benchmark, running a study).** `05_datasets_and_benchmarks.md` (all) → `03_defenses.md` § C6 (adaptive-attack methodology) → `02_indirect_and_agentic_attacks.md` § B2 (agent benchmarks).
- **Agent developer (building tool-using AI).** `02_indirect_and_agentic_attacks.md` (all) → `03_defenses.md` § C3 (architectural separation, CaMeL) → `06_tools_and_vendors.md` (LlamaFirewall, agent guardrails) → `05_datasets_and_benchmarks.md` § Datasets-D.
- **Compliance / governance reader.** `07_standards_and_industry.md` (all) → `03_defenses.md` § C6 (what passes adaptive-attack scrutiny) → `04_training_time_threats.md` (training-pipeline / supply-chain risk).

## Glossary

`#glossary`

Alphabetized. Format: **Canonical name** — full name and aliases. One-line definition. Citation. → file § anchor.

- **Adversarial suffix** — A token sequence appended to a harmful query to override safety. Pioneered by GCG. Zou et al. (2023), [arXiv:2307.15043](https://arxiv.org/abs/2307.15043). → `01_direct_attacks.md` § A4.
- **AgentDojo** — Dynamic environment to evaluate prompt injection attacks and defenses for LLM agents. Debenedetti et al. (2024), [arXiv:2406.13352](https://arxiv.org/abs/2406.13352). → `02_indirect_and_agentic_attacks.md` § B2 and `05_datasets_and_benchmarks.md` § Datasets-D.
- **AgentHarm** — Benchmark for measuring harmfulness of LLM agents (UK AISI + Gray Swan). Andriushchenko et al. (2024), [arXiv:2410.09024](https://arxiv.org/abs/2410.09024). → `02_indirect_and_agentic_attacks.md` § B2 and `05_datasets_and_benchmarks.md` § Datasets-D.
- **AILuminate** — MLCommons AI Safety v1.1 benchmark; 12 hazard categories with safety grades Poor → Excellent. → `05_datasets_and_benchmarks.md` § Datasets-B.
- **Alignment failure** — Non-adversarial unsafe output rooted in training-data quality or RLHF specification, not in attacker action. → `03_defenses.md` § C5.
- **ArtPrompt** — ASCII-art-based jailbreak; first "vision-in-text" attack. Jiang et al. (2024), [arXiv:2402.11753](https://arxiv.org/abs/2402.11753). → `01_direct_attacks.md` § A3.
- **ASR (Attack Success Rate)** — Standard metric: fraction of attempts that produce the targeted harmful output. Definition varies by judge model — see StrongREJECT for a careful treatment.
- **Attack surface** — A channel through which input reaches the model: system prompt, user input, retrieved context, tool output, multimodal channel, training data. → § Six attack surfaces.
- **AutoDAN** — Hierarchical genetic algorithm that evolves DAN-style prompts; first stealthy + perplexity-evading jailbreak. Liu et al. (2023, ICLR 2024), [arXiv:2310.04451](https://arxiv.org/abs/2310.04451). → `01_direct_attacks.md` § A4.
- **BadEdit** — Backdoors LLMs via post-training weight editing; ~15 samples suffice. Li et al. (2024, ICLR), [arXiv:2403.13355](https://arxiv.org/abs/2403.13355). → `04_training_time_threats.md` § D1.
- **BadNets** — Foundational ML backdoor paper (image-domain). Gu, Dolan-Gavitt, Garg (2017), [arXiv:1708.06733](https://arxiv.org/abs/1708.06733). → `04_training_time_threats.md` § D1.
- **Best-of-N** — Random prompt augmentations until a harmful response slips through; works at high N (Anthropic). Hughes et al. (2024), [arXiv:2412.03556](https://arxiv.org/abs/2412.03556). → `01_direct_attacks.md` § A2.
- **BIPIA** — Bilingual Indirect PI Attack benchmark (Microsoft). Yi et al. (2023), [arXiv:2312.14197](https://arxiv.org/abs/2312.14197). → `02_indirect_and_agentic_attacks.md` § B1, `05_datasets_and_benchmarks.md` § Datasets-C.
- **Bijection Learning** — Teach an arbitrary string-string bijection in-context, then issue the harmful request encoded; >86% ASR on Claude 3.5 Sonnet. Huang et al. (Haize, 2024, ICLR 2025), [arXiv:2410.01294](https://arxiv.org/abs/2410.01294). → `01_direct_attacks.md` § A3.
- **Black-box adversary** — Attacker can call the model and read outputs but not gradients or activations. Defines the lowest rung of the attacker-capability ladder.
- **CaMeL** — Capability-based meta-layer; privileged LLM emits a Python program where data origin is tracked. Debenedetti et al. (Google Research 2025), [arXiv:2503.18813](https://arxiv.org/abs/2503.18813). The arXiv paper title is "Defeating Prompt Injections by Design"; CaMeL is the system name. → `03_defenses.md` § C3.
- **Circuit Breakers** — Latent-space defense; reroutes harmful representations to orthogonal subspace. Zou et al. (2024, NeurIPS), [arXiv:2406.04313](https://arxiv.org/abs/2406.04313). → `03_defenses.md` § C4.
- **COLD-Attack** — Energy-based controllable jailbreak via Langevin dynamics. Yu et al. (2024, ICML), [arXiv:2402.08679](https://arxiv.org/abs/2402.08679). → `01_direct_attacks.md` § A4.
- **Constitutional AI** — RLAIF using natural-language constitutional principles. Bai et al. (Anthropic 2022), [arXiv:2212.08073](https://arxiv.org/abs/2212.08073). → `03_defenses.md` § C5.
- **Constitutional Classifiers** — Synthetic-data-trained classifier guardrails using natural-language constitution; foundational for Anthropic's deployment-time defense. Sharma et al. (2025), [arXiv:2501.18837](https://arxiv.org/abs/2501.18837). → `03_defenses.md` § C1.
- **Crescendo** — Multi-turn jailbreak via gradual benign-to-harmful escalation in <5 turns. Russinovich et al. (Microsoft 2024), [arXiv:2404.01833](https://arxiv.org/abs/2404.01833). → `01_direct_attacks.md` § A2.
- **DAN ("Do Anything Now")** — Persona-roleplay jailbreak family that asks the model to simulate an unrestricted alter-ego. Reddit/community 2022–2024; academic catalog at Shen et al. [arXiv:2308.03825](https://arxiv.org/abs/2308.03825). → `01_direct_attacks.md` § A2.
- **DataSentinel** — Game-theoretic minimax-trained injection detector. Liu et al. (2025, IEEE S&P Distinguished), [arXiv:2504.11358](https://arxiv.org/abs/2504.11358). → `03_defenses.md` §§ C1, C3.
- **Direct PI** — Prompt injection via the user-input channel. → `01_direct_attacks.md` § A1.
- **DPO (Direct Preference Optimization)** — Closed-form alignment training as a classification loss; replaces RM+PPO. Rafailov et al. (2023, NeurIPS), [arXiv:2305.18290](https://arxiv.org/abs/2305.18290). → `03_defenses.md` § C5.
- **Dual-LLM pattern** — Privileged + Quarantined LLM with symbolic-variable interface. Willison (2023, blog). → `03_defenses.md` § C3.
- **EchoLeak (CVE-2025-32711)** — First real-world zero-click indirect-PI exploit in a production LLM (M365 Copilot); CVSS 9.3. Reddy & Gujral (Aim Security 2025), [arXiv:2509.10540](https://arxiv.org/abs/2509.10540). → `02_indirect_and_agentic_attacks.md` § B1.
- **EU AI Act Article 15** — Binding regulation on accuracy, robustness, and cybersecurity for high-risk AI. Enforceable 2 August 2026. → `07_standards_and_industry.md` § Regulatory.
- **FlipAttack** — Jailbreak via left-side text-flipping; ~98% ASR on GPT-4o. Liu et al. (2024, ICML 2025), [arXiv:2410.02832](https://arxiv.org/abs/2410.02832). → `01_direct_attacks.md` § A3.
- **GCG (Greedy Coordinate Gradient)** — Gradient-guided suffix-token search; foundational white-box jailbreak. Zou et al. (2023), [arXiv:2307.15043](https://arxiv.org/abs/2307.15043). → `01_direct_attacks.md` § A4.
- **Goodside (Riley)** — Researcher who in September 2022 publicly demonstrated PI against GPT-3 (Translate to French / Haha pwned). Catalyst for naming the attack class.
- **Govern / Map / Measure / Manage** — The four functions of the NIST AI Risk Management Framework. → `07_standards_and_industry.md` § Standards Frameworks.
- **GPAI** — General-Purpose AI. EU AI Act category; GPAI providers with systemic risk are subject to Article 55 systemic-risk evaluations.
- **GPAI Code of Practice** — Voluntary EU compliance pathway for GPAI providers under Article 56.
- **Greshake (indirect PI foundational)** — Greshake et al. (2023, AISec) introduced indirect prompt injection. [arXiv:2302.12173](https://arxiv.org/abs/2302.12173). → `02_indirect_and_agentic_attacks.md` § B1.
- **HackAPrompt** — Global-scale prompt-hacking competition; 600K+ adversarial prompts and 29-technique taxonomy. Schulhoff et al. (2023, EMNLP Best Theme), [arXiv:2311.16119](https://arxiv.org/abs/2311.16119). → `01_direct_attacks.md` § A1, `05_datasets_and_benchmarks.md` § Datasets-C, `05_datasets_and_benchmarks.md` § CTFs.
- **HarmBench** — Standardized red-team + defense eval benchmark; 510 behaviors × 7 categories. Mazeika et al. (2024, ICML), [arXiv:2402.04249](https://arxiv.org/abs/2402.04249). → `05_datasets_and_benchmarks.md` § Datasets-A.
- **Image Hijacks** — Adversarial images that control generative-model behavior at runtime. Bailey et al. (2023), [arXiv:2309.00236](https://arxiv.org/abs/2309.00236). → `02_indirect_and_agentic_attacks.md` § B3.
- **Indirect PI** — Prompt injection via retrieved/data-borne content. → `02_indirect_and_agentic_attacks.md` § B1.
- **Indirect-content writer** — Attacker rung 4: can write content to pages, emails, tools, or documents the model reads.
- **InjecAgent** — Indirect-PI benchmark for tool-integrated LLM agents. Zhan et al. (2024, ACL Findings), [arXiv:2403.02691](https://arxiv.org/abs/2403.02691). → `02_indirect_and_agentic_attacks.md` § B2, `05_datasets_and_benchmarks.md` § Datasets-D.
- **Instruction Hierarchy** — Train models to prefer system > developer > user > tool instructions. Wallace et al. (OpenAI 2024), [arXiv:2404.13208](https://arxiv.org/abs/2404.13208). → `03_defenses.md` § C3.
- **ISO/IEC 42001** — World's first certifiable AI Management System standard. → `07_standards_and_industry.md` § Standards Frameworks.
- **Jailbreak** — Adversarial direct user input that elicits a refused or harmful output. Often co-occurring with direct PI but conceptually distinct.
- **JailbreakBench** — Open robustness benchmark and leaderboard. Chao et al. (2024, NeurIPS D&B), [arXiv:2404.01318](https://arxiv.org/abs/2404.01318). → `05_datasets_and_benchmarks.md` § Datasets-A.
- **Llama Guard** — Meta's LLM-based input/output safety classifier family. Inan et al. (2023), [arXiv:2312.06674](https://arxiv.org/abs/2312.06674); Llama Guard 3 documented as a component of [the Llama 3 Herd of Models paper, arXiv:2407.21783](https://arxiv.org/abs/2407.21783). → `03_defenses.md` § C1.
- **LLM01–LLM10 (OWASP)** — The 10 risks in OWASP Top 10 for LLM Applications v2025. → `07_standards_and_industry.md` § Standards Frameworks.
- **Many-shot Jailbreaking** — Hundreds of faux Q/A demos in a single prompt achieve safety bypass; enabled by 1M-token contexts. Anil et al. (Anthropic 2024, NeurIPS). → `01_direct_attacks.md` § A2.
- **Membership Inference Attack (MIA)** — Determine whether a specific record was in a model's training set. → `04_training_time_threats.md` § D4.
- **MITRE ATLAS** — TTP knowledge base for AI/ML attacks. → `07_standards_and_industry.md` § Standards Frameworks.
- **MP-2.3-005** — NIST AI 600-1 control mandating pre- and post-deployment adversarial testing. → `07_standards_and_industry.md` § Standards Frameworks.
- **NIST AI RMF** — NIST AI Risk Management Framework v1.0 (Jan 2023); voluntary, sector-agnostic. → `07_standards_and_industry.md`.
- **NIST AI 600-1** — Generative AI profile of NIST AI RMF (July 2024); operationalizes adversarial-testing controls. → `07_standards_and_industry.md`.
- **OWASP LLM Top 10** — Application-developer's working checklist for LLM security risks; v2025 the current edition. → `07_standards_and_industry.md`.
- **PAIR (Prompt Automatic Iterative Refinement)** — Black-box LLM-on-LLM jailbreak in <20 queries. Chao et al. (2023), [arXiv:2310.08419](https://arxiv.org/abs/2310.08419). → `01_direct_attacks.md` § A5.
- **Persistent pre-training poisoning** — Pre-training data poison persists through SFT/RLHF. Souly et al. (2025, 250-doc result), [arXiv:2510.07192](https://arxiv.org/abs/2510.07192); Zhang et al. (2024) [arXiv:2410.13722](https://arxiv.org/abs/2410.13722). → `04_training_time_threats.md` § D2.
- **Persuasive Adversarial Prompts (PAP)** — Taxonomy of 40 persuasion techniques; 92% ASR with no optimization. Zeng et al. (2024, ACL), [arXiv:2401.06373](https://arxiv.org/abs/2401.06373). → `01_direct_attacks.md` § A2.
- **PoisonedRAG** — RAG knowledge-corruption attack; 5 docs in a 10⁶-doc DB → 90%+ ASR. Zou et al. (2024, USENIX), [arXiv:2402.07867](https://arxiv.org/abs/2402.07867). → `02_indirect_and_agentic_attacks.md` § B1.
- **Prompt extraction** — Recover the system prompt or other privileged context via PI / memorization. → `01_direct_attacks.md` § A1, `04_training_time_threats.md` § D5.
- **Prompt hijacking** — Force the model to execute the attacker's goal (vs prompt extraction's read-out goal). → `01_direct_attacks.md` § A1.
- **Prompt injection** — Adversarial input that overrides system instructions. → §§ What is prompt injection / Five threats.
- **Refusal** — A safety-trained response declining to comply. The behavioral target of most jailbreaks.
- **Refusal direction** — Refusal in language models is mediated by a single residual-stream direction; ablation removes safety. Arditi et al. (2024, NeurIPS), [arXiv:2406.11717](https://arxiv.org/abs/2406.11717). → `03_defenses.md` § C4.
- **Representation Engineering (RepE)** — Top-down probes and steering on activation populations. Zou et al. (2023), [arXiv:2310.01405](https://arxiv.org/abs/2310.01405). → `03_defenses.md` § C4.
- **ShieldGemma** — Google's Gemma2-based safety classifier suite. Zeng et al. (2024), [arXiv:2407.21772](https://arxiv.org/abs/2407.21772). → `03_defenses.md` § C1.
- **Sleeper backdoor** — Training-time backdoor that survives safety fine-tuning; activates on a trigger. Hubinger et al. (Anthropic 2024), [arXiv:2401.05566](https://arxiv.org/abs/2401.05566). → `04_training_time_threats.md` § D1.
- **SmoothLLM** — Random char swaps + majority vote defense; broken under adaptive attack. Robey et al. (2023), [arXiv:2310.03684](https://arxiv.org/abs/2310.03684). → `03_defenses.md` § C2.
- **Spotlighting** — Architectural defense via delimiting / datamarking / encoding to mark untrusted text. Hines et al. (Microsoft 2024), [arXiv:2403.14720](https://arxiv.org/abs/2403.14720). → `03_defenses.md` § C3 and `02_indirect_and_agentic_attacks.md` § B1.
- **StruQ** — Structured Queries; reserved special tokens separate prompt from data. Chen et al. (2024, USENIX 2025), [arXiv:2402.06363](https://arxiv.org/abs/2402.06363). → `03_defenses.md` § C3.
- **TAP (Tree of Attacks)** — Tree-of-thought search over PAIR-style attacker-LLM interactions; 60% fewer queries. Mehrotra et al. (2023, NeurIPS 2024), [arXiv:2312.02119](https://arxiv.org/abs/2312.02119). → `01_direct_attacks.md` § A5.
- **Threat model (LLM)** — The (attacker rung × attack surface × defender capability) tuple that grounds whether a defense applies. → §§ Attacker-capability ladder / Six attack surfaces.
- **Training-data writer** — Attacker rung 5: can contribute to pre-training, instruction-tuning, or RLHF data.
- **Universal jailbreak** — A single prompt that bypasses safety for many target queries; the empirical target of GCG, AmpleGCG, Constitutional Classifiers' negative result (3000 hours, no universal jailbreak found).
- **Universal Jailbreak Backdoors (Rando & Tramèr)** — RLHF preference-data poisoning produces a universal "sudo" trigger. Rando & Tramèr (2023, ICLR 2024), [arXiv:2311.14455](https://arxiv.org/abs/2311.14455). → `04_training_time_threats.md` § D1.
- **WildGuard** — AI2's open one-stop moderation classifier (prompt harm + response harm + refusal). Han et al. (2024, NeurIPS D&B), [arXiv:2406.18495](https://arxiv.org/abs/2406.18495). → `03_defenses.md` § C1.
- **White-box adversary** — Attacker rung 3: gradients on the deployed model (or near-equivalent surrogate).

---

For depth on any of the above, follow the file-and-section pointers. For a routing question not covered by the glossary, consult `README.md` § Lookup recipes.

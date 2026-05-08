# Indirect, Agentic, Multimodal, and Computer-Use Attacks

<!-- AGENT-INDEX: keep this block stable; future agents read it first. -->
**Scope:** Indirect prompt-injection research — attacks via untrusted external content (RAG, tools, agents, multimodal channels, browser/CUA surfaces).
**Out of scope:** Direct (user-supplied) prompt attacks — see `01_direct_attacks.md`. Defenses — see `03_defenses.md`.
**Coverage window:** 2022–2026 (emphasis 2024–2026).
**Last updated:** 2026-05-06.
**Subsections (stable anchors):** B1 Indirect PI · B2 Agentic AI attacks · B3 Multimodal / VLM attacks · B4 Computer-use / browser-agent attacks.
**Key terms covered:** Greshake (indirect PI), HouYi, BIPIA, Neural Exec, PoisonedRAG, Phantom, PLeak, GenTel-Safe, Spotlighting, TaskTracker, EchoLeak (CVE-2025-32711), LLMail-Inject, Promptware Kill Chain, InjecAgent, AgentDojo, AgentHarm, ASB, BadAgent, AgentPoison, ToolEmu, R-Judge, WASP, AdvWeb, MCPTox, ToolHijacker, Visual Adversarial Examples, Image Hijacks, Jailbreak in Pieces, MM-SafetyBench, FigStep, ImgTrojan, HADES, BAP, MultiTrust, Arondight, IDEATOR, MML, AudioJailbreak, EVA, AdInject, VPI-Bench, AgentTypo, CrossInject, Chameleon, BrowseSafe, Anthropic browser-use, OpenAI Atlas hardening.
**Related files:** `00_overview.md` (taxonomy), `01_direct_attacks.md` (direct attacks), `03_defenses.md` (CaMeL, Spotlighting, BrowseSafe), `05_datasets_and_benchmarks.md` (AgentDojo, AgentHarm, BIPIA), `07_standards_and_industry.md` (OWASP LLM06).

## Topic overview

Indirect prompt injection is the threat model where the attacker does *not* control the user-facing prompt but does control content the model retrieves, processes, or acts on. The Greshake et al. *"Not what you've signed up for"* paper (AISec 2023) is foundational — it framed indirect PI by analogy to remote code execution: any LLM-integrated application that ingests untrusted content is exposed.

The four subsections below cover increasingly autonomous attack surfaces. **B1** covers indirect PI proper — RAG poisoning, document-borne injection, prompt leaking, and the EchoLeak class of real-world incidents. **B2** covers agentic attacks where the model has tool-use capabilities and the attacker compromises the agent via tool descriptions, memory, or knowledge bases. **B3** covers multimodal / VLM attacks where the adversarial payload is in an image, audio, or video. **B4** covers computer-use / browser-agent attacks — the newest frontier, where Anthropic and OpenAI have publicly conceded the threat may not be fully solvable.

The 2024–2026 trajectory is clear from the entries below: indirect PI matured from concept to industrial reality with EchoLeak (CVE-2025-32711) as the watershed; agentic attacks are the fastest-moving area, with defenses lagging 12–18 months behind; multimodal attacks crossed from gradient-image perturbations to typography-only and encryption-decryption cross-modal attacks needing no gradients; computer-use is where the next defensive paradigms (BrowseSafe, Anthropic safeguards, OpenAI Atlas hardening) are being defined. See § Trends & open questions for the synthesis.

## B1. Indirect Prompt Injection

`#b1-indirect-pi`

These attacks compromise the model via retrieved or data-borne content rather than the user prompt: poisoned RAG documents, manipulated webpages, attacker-controlled emails, document-borne triggers. The 2025 watershed is **EchoLeak (CVE-2025-32711)**, the first documented zero-click indirect-PI exploit in a production LLM system (Microsoft 365 Copilot, CVSS 9.3).

### Entries

- **Not what you've signed up for: Indirect PI** — Greshake et al. (2023), *AISec 2023*.
  - **Source:** https://arxiv.org/abs/2302.12173 ; https://doi.org/10.1145/3605764.3623985
  - **Code:** https://github.com/greshake/llm-security
  - **Mechanism:** Foundational paper introducing indirect PI; taxonomy: data theft, worming, ecosystem contamination.
  - **Result:** Established the remote-code-execution analogy; the field-defining indirect-PI taxonomy.
  - **Status:** Verified. GitHub path `greshake/llm-security` not directly confirmed in search.

- **HouYi: PI against LLM-integrated Apps** — Liu et al. (2023), *USENIX Security 2024*.
  - **Source:** https://arxiv.org/abs/2306.05499
  - **Code:** https://github.com/LLMSecurity/HouYi
  - **Mechanism:** Black-box framework against 36 deployed LLM apps.
  - **Result:** 31/36 apps vulnerable; cross-cutting between direct and indirect surfaces.
  - **Status:** Verified. → Also see `01_direct_attacks.md` § A1.

- **Formalizing and Benchmarking PI Attacks/Defenses** — Liu, Yupei et al. (2023/2024), *USENIX Security 2024*.
  - **Source:** https://arxiv.org/abs/2310.12815
  - **Code:** https://github.com/liu00222/Open-Prompt-Injection
  - **Mechanism:** First formalization framework plus benchmark.
  - **Result:** Common benchmark + taxonomy of separator/escape/fake-completion/combined attacks.
  - **Status:** Verified. → Also see `01_direct_attacks.md` § A1, `03_defenses.md` § C3.

- **BIPIA: Bilingual Indirect PI Attack benchmark** — Yi et al. (Microsoft 2023), *KDD 2025*.
  - **Source:** https://arxiv.org/abs/2312.14197
  - **Code:** https://github.com/microsoft/BIPIA
  - **Mechanism:** First indirect-PI benchmark; Email / WebQA / TableQA / Summarization / CodeQA scenarios.
  - **Result:** 5 scenarios × 250 attacker goals; bilingual coverage (en/zh).
  - **Status:** Verified. → Also see `01_direct_attacks.md` § A1, `03_defenses.md` § C3.

- **Neural Exec: Execution Trigger Learning** — Pasquini et al. (2024), *AISec 2024*.
  - **Source:** https://arxiv.org/abs/2403.03792
  - **Code:** https://github.com/pasquini-dario/LLM_NeuralExec
  - **Mechanism:** Differentiable trigger search; the resulting triggers persist through RAG preprocessing.
  - **Result:** First demonstration that adversarial triggers can survive multi-stage RAG pipelines.
  - **Status:** Verified.

- **Universal PI Attacks against LLMs** — Liu, Jia et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2403.04957
  - **Code:** https://github.com/SheltonLiu-N/Universal-Prompt-Injection
  - **Mechanism:** Gradient-based universal injection strings.
  - **Result:** Bridges PI attacks with the GCG optimization family.
  - **Status:** Verified — GitHub path inferred from author surname; not directly confirmed in search.

- **PoisonedRAG: Knowledge Corruption Attacks to RAG** — Zou, Geng et al. (2024), *USENIX Security 2025*.
  - **Source:** https://arxiv.org/abs/2402.07867
  - **Code:** https://github.com/sleeepeer/PoisonedRAG
  - **Mechanism:** First RAG poisoning; inject 5 documents into a 10⁶-document database.
  - **Result:** 90%+ ASR across NQ / HotpotQA / MS-MARCO.
  - **Status:** Verified. → Cross-ref `01_direct_attacks.md` § A1, `04_training_time_threats.md` § D2.

- **Phantom: General Trigger Attacks on RAG** — Chaudhari et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2405.20485
  - **Code:** —
  - **Mechanism:** Two-stage trigger attack — works on Gemma / Vicuna / Llama, transfers to GPT-4.
  - **Result:** Generalizes PoisonedRAG-style attacks across retrieval corpora.
  - **Status:** Verified.

- **Backdoored Retrievers for PI** — Cohen et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2410.14479
  - **Code:** —
  - **Mechanism:** Backdoors injected into dense-retriever fine-tuning.
  - **Result:** Compromised retriever surfaces poisoned context to a clean LLM.
  - **Status:** Verified.

- **PLeak: Prompt Leaking Attacks** — Hui, Chen et al. (2024), *ACM CCS 2024*.
  - **Source:** https://arxiv.org/abs/2405.06823
  - **Code:** https://github.com/BHui97/PLeak
  - **Mechanism:** Closed-box system-prompt extraction via optimization.
  - **Result:** 68% recovery on Poe-hosted apps.
  - **Status:** Verified — GitHub path not directly confirmed in search.

- **GenTel-Safe: Unified Benchmark + Shield** — Li, Chen et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2409.19521
  - **Code:** https://gentellab.github.io/ (GitHub Pages returns 404 as of May 2026 — verify alternative repo path before use)
  - **Mechanism:** 84,812-prompt PI benchmark plus a Shield detector.
  - **Result:** Shield detector reaches 96.8% accuracy.
  - **Status:** Verified.

- **Spotlighting: Defending Indirect PI** — Hines et al. (Microsoft 2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2403.14720
  - **Code:** —
  - **Mechanism:** Three signaling techniques (delimiting / datamarking / encoding) mark untrusted text.
  - **Result:** ASR >50% → <2% on tested workloads.
  - **Status:** Verified. → Primary treatment in `03_defenses.md` § C3.

- **TaskTracker: Catching Task Drift via Activations** — Abdelnabi et al. (Microsoft 2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2406.00799
  - **Code:** https://github.com/microsoft/TaskTracker
  - **Mechanism:** Activation-space drift detection for indirect-PI events.
  - **Result:** 500K-instance benchmark; activation-deltas detect drift the model itself does not flag.
  - **Status:** Verified.

- **EchoLeak (CVE-2025-32711)** — Reddy & Gujral (Aim Security 2025), *arXiv preprint + Aim Security disclosure*.
  - **Source:** https://arxiv.org/abs/2509.10540 ; https://www.aim.security/lp/aim-labs-echoleak-blogpost
  - **Code:** —
  - **Mechanism:** First real-world zero-click PI in M365 Copilot; XPIA bypass + Markdown reference exfiltration + Teams-proxy abuse.
  - **Result:** CVSS 9.3; the canonical 2025 production-grade indirect-PI exploit.
  - **Status:** Verified — Aim Security disclosure (June 2025); arXiv post-mortem at 2509.10540.

- **LLMail-Inject: Adaptive PI Challenge Dataset** — Abdelnabi et al. (Microsoft 2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2506.09956
  - **Code:** https://github.com/microsoft/llmail-inject-challenge
  - **Mechanism:** Competition-derived dataset of adaptive PI attempts on a simulated email assistant.
  - **Result:** 208K adaptive attacks from 839 contestants.
  - **Status:** Verified.

- **Indirect PI in the Wild: Empirical Study** — Khodayari, Zhang, Acharya, Pellegrino (2026), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2604.27202
  - **Code:** —
  - **Mechanism:** 1.2-billion-URL crawl; 15.3K validated injections in 11.7K pages.
  - **Result:** First large-scale empirical measurement of indirect-PI prevalence on the public web.
  - **Status:** Verified — authors filled in 2026-05-06.

- **Promptware Kill Chain** — Brodt, Feldman, Schneier, Nassi (2026), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2601.09625
  - **Code:** —
  - **Mechanism:** Seven-stage kill-chain framework; survey of 36 studies and 21 incidents at 4+ stages.
  - **Result:** Formal kill-chain analog of MITRE ATT&CK for prompt-injection-driven exploits.
  - **Status:** Verified — authors corrected 2026-05-06 (earlier draft incorrectly inferred Bargury authorship from EchoLeak co-disclosure).

- **Slack AI Data Exfiltration** — PromptArmor (2024), *Industry advisory*.
  - **Source:** https://promptarmor.com/
  - **Code:** —
  - **Mechanism:** Real-world Slack AI exfiltration via Markdown link injection.
  - **Result:** Live production-scale indirect-PI demonstration before EchoLeak.
  - **Status:** Unverified — industry advisory, no arXiv.

- **ChatGPT Cross-Plugin Request Forgery** — Rehberger / Embrace The Red (2023), *Blog disclosure*.
  - **Source:** https://embracethered.com/blog/posts/2023/chatgpt-plugin-vulns-chat-with-code/
  - **Code:** —
  - **Mechanism:** First end-to-end indirect PI to confused-deputy + PII exfiltration via plugin chain.
  - **Result:** Catalyst disclosure for OpenAI plugin policy changes.
  - **Status:** Unverified — blog disclosure, no arXiv.

## B2. Agentic AI Attacks

`#b2-agentic-attacks`

These attacks compromise tool-using LLM agents — the threat model where the model has *capabilities* (function calls, tool invocations, memory writes) rather than just outputs. The 2024 wave (InjecAgent, AgentDojo, AgentHarm, ASB) established benchmarks; 2025–2026 moved to MCP-specific tool-poisoning, memory-layer persistence, and agentic coding assistants.

### Entries

- **InjecAgent: Indirect PI in Tool-Integrated Agents** — Zhan, Liang et al. (2024), *ACL Findings 2024*.
  - **Source:** https://arxiv.org/abs/2403.02691
  - **Code:** https://github.com/uiuc-kang-lab/InjecAgent
  - **Mechanism:** First tool-use indirect-PI benchmark; 1,054 cases × 17 user × 62 attacker tools.
  - **Result:** Established that tool-integrated agents are systematically more vulnerable to indirect PI than chat-only models.
  - **Status:** Verified.

- **AgentDojo: Dynamic Environment for Agent PI** — Debenedetti et al. (ETH 2024), *NeurIPS 2024 Datasets & Benchmarks*.
  - **Source:** https://arxiv.org/abs/2406.13352
  - **Code:** https://github.com/ethz-spylab/agentdojo
  - **Mechanism:** Live environment (email / banking / travel / Slack) with 97 tasks and 629 security cases.
  - **Result:** Most widely-adopted dynamic agentic-PI benchmark; security model separates utility from attack-success.
  - **Status:** Verified. → Also see `03_defenses.md` § C6, `05_datasets_and_benchmarks.md` § Datasets-D.

- **AgentHarm: Measuring Agent Harmfulness** — Andriushchenko et al. (UK AISI 2024), *ICLR 2025*.
  - **Source:** https://arxiv.org/abs/2410.09024
  - **Code:** https://github.com/METR/inspect_evals
  - **Mechanism:** 110 base scenarios → 440 augmented across 11 harm categories with tool-call traces.
  - **Result:** First agentic-harmfulness benchmark with category-level breakdowns.
  - **Status:** Verified. → Also see `05_datasets_and_benchmarks.md` § Datasets-D.

- **Agent Security Bench (ASB)** — Zhang, Huang et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2410.02644
  - **Code:** https://github.com/agiresearch/ASB
  - **Mechanism:** 10 PI + memory-poisoning + 4 mixed-attack scenarios; 10 scenarios × 400+ tools.
  - **Result:** 84.3% average ASR across tested agents.
  - **Status:** Verified — GitHub path not directly confirmed in search.

- **Agent-SafetyBench** — Zhang, Cui et al. (Tsinghua 2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2412.14470
  - **Code:** https://github.com/thu-coai/Agent-SafetyBench
  - **Mechanism:** 349 environments × 2,000 cases; 8 risk categories × 10 failure modes.
  - **Result:** None of 16 evaluated agents reach 60% safety.
  - **Status:** Verified. → Also see `05_datasets_and_benchmarks.md` § Datasets-D.

- **BadAgent: Inserting Backdoors in LLM Agents** — Wang, Xue et al. (2024), *ACL 2024*.
  - **Source:** https://arxiv.org/abs/2406.03007
  - **Code:** https://github.com/DPamK/BadAgent
  - **Mechanism:** Active and passive backdoors via fine-tuning.
  - **Result:** First framework to demonstrate persistent agent-level backdoors.
  - **Status:** Verified. → Also see `04_training_time_threats.md` § D1.

- **Watch Out for Your Agents! Backdoor Threats** — Yang et al. (2024), *NeurIPS 2024*.
  - **Source:** https://arxiv.org/abs/2402.11208
  - **Code:** https://github.com/lancopku/agent-backdoor-attacks
  - **Mechanism:** Three backdoor forms; current text-domain defenses fail.
  - **Result:** Establishes that text-only backdoor defenses do not transfer to tool-using agents.
  - **Status:** Verified.

- **AgentPoison: Poisoning Memory or Knowledge Bases** — Chen et al. (2024), *NeurIPS 2024*.
  - **Source:** https://arxiv.org/abs/2407.12784
  - **Code:** https://github.com/BillChan226/AgentPoison
  - **Mechanism:** Poison the agent's memory or RAG knowledge base.
  - **Result:** <0.1% poison rate → ≥80% ASR.
  - **Status:** Verified.

- **ToolEmu: LM-Emulated Sandbox for Agent Risks** — Ruan et al. (2023), *ICLR 2024 Spotlight*.
  - **Source:** https://arxiv.org/abs/2309.15817
  - **Code:** https://github.com/ryoungj/ToolEmu
  - **Mechanism:** LM-emulated sandbox plus a safety evaluator; 36 toolkits / 144 cases.
  - **Result:** First broad simulation framework for agentic risk evaluation.
  - **Status:** Verified.

- **R-Judge: Agent Risk Awareness** — Yuan et al. (2024), *EMNLP Findings 2024*.
  - **Source:** https://arxiv.org/abs/2401.10019
  - **Code:** https://rjudgebench.github.io/
  - **Mechanism:** 569 multi-turn cases × 27 scenarios.
  - **Result:** GPT-4o reaches only 74.4% on agent-trace risk identification.
  - **Status:** Verified.

- **WASP: Web Agent Security Benchmark** — Evtimov et al. (Meta FAIR 2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2504.18575
  - **Code:** https://github.com/facebookresearch/wasp
  - **Mechanism:** Realistic VWA-based web-agent benchmark.
  - **Result:** Up to 86% partial-success ASR.
  - **Status:** Verified. → Also see B4, `05_datasets_and_benchmarks.md` § Datasets-D.

- **AdvWeb: Black-box Attacks on VLM Web Agents** — Xu, Kang et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2410.17401
  - **Code:** https://github.com/AI-secure/AdvWeb
  - **Mechanism:** DPO-trained adversarial-prompter approach against VLM web agents.
  - **Result:** 97.5% ASR on SeeAct / GPT-4V.
  - **Status:** Verified — GitHub path not directly confirmed in search. → Also see B4.

- **MCPTox: Tool Poisoning on Real MCP Servers** — Wang, Gao, Wang, Liu, Sun, Cheng, Shi, Du, Li (2025), *AAAI 2026*.
  - **Source:** https://arxiv.org/abs/2508.14925
  - **Code:** —
  - **Mechanism:** First real-MCP tool-poisoning benchmark; 45 servers / 353 tools / 1,312 cases.
  - **Result:** o1-mini reaches 72.8% ASR.
  - **Status:** Verified — authors filled in 2026-05-06.

- **ToolHijacker: PI to Tool Selection** — Shi et al. (2025), *NDSS 2026*.
  - **Source:** https://arxiv.org/abs/2504.19793
  - **Code:** —
  - **Mechanism:** No-box optimization of malicious tool documentation.
  - **Result:** 96.7% ASR.
  - **Status:** Verified.

- **Large-Scale Public Agent Red-Team Competition** — Dziemian, Lin, Fu et al. (32-author including Chaudhuri, Zou, Rando, Wang, Kolter, Fredrikson) (2026), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2603.15714
  - **Code:** —
  - **Mechanism:** Competition data across Gemini 2.5 Pro / Claude / GPT-5.
  - **Result:** First large-scale public adversarial-evaluation dataset on frontier agents.
  - **Status:** Verified — authors filled in 2026-05-06.

- **Memory Poisoning Attack and Defense on Memory-Based Agents** — Devarangadi Sunil, Sinha, Maheshwari, Todmal, Mallik, Mishra (2026), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2601.05504
  - **Code:** —
  - **Mechanism:** Persistent-memory attack on long-context agents.
  - **Result:** >95% ASR on the targeted memory architectures.
  - **Status:** Verified — authors filled in 2026-05-06.

- **Real AI Agents with Fake Memories: Web3 Agents** — Patlan, Sheng, Hebbar, Mittal, Viswanath (Princeton 2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2503.16248
  - **Code:** —
  - **Mechanism:** Memory-injection in ElizaOS triggers blockchain transfers.
  - **Result:** First production-grade memory-injection attack on a deployed Web3 agent (CrAIBench dataset).
  - **Status:** Verified — authors corrected 2026-05-06.

- **Context Manipulation Attacks (Plan Injection)** — anonymous (2025), *ICML 2025*.
  - **Source:** https://arxiv.org/abs/2506.17318
  - **Code:** —
  - **Mechanism:** Plan-injection attacks at the agent-trace level.
  - **Result:** 3× more potent than prompt injection on the same target.
  - **Status:** Verified — author list not surfaced in dossier.

- **PI Attacks on Agentic Coding Assistants (SoK)** — Maloyan & Namiot (2026), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2601.17548
  - **Code:** —
  - **Mechanism:** Systematization-of-knowledge across Claude Code / Copilot / Cursor.
  - **Result:** 78-study SoK; first comprehensive coding-assistant PI survey.
  - **Status:** Verified.

- **MCP Threat Modeling and Tool Poisoning** — Huang, Huang, Tran, Fard (2026), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2603.22489
  - **Code:** —
  - **Mechanism:** Formal MCP threat model.
  - **Result:** Reference threat model for MCP-server-mediated agent attacks.
  - **Status:** Verified — authors filled in 2026-05-06.

- **Securing AI Agents Against PI (defense survey)** — Ramakrishnan & Balaji (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2511.15759
  - **Code:** —
  - **Mechanism:** Comprehensive defense taxonomy through end-2025.
  - **Result:** Field-defining defense survey for the agentic era.
  - **Status:** Verified — authors filled in 2026-05-06.

## B3. Multimodal / VLM Attacks

`#b3-multimodal-attacks`

These attacks compromise vision-language models, audio LMs, or other multimodal models. The 2023 wave (Visual Adversarial Examples, Image Hijacks, Jailbreak in Pieces) established the gradient-image-perturbation paradigm; 2024–2026 moved to typography-only and encryption-decryption cross-modal attacks (FigStep, MML at 97.8% ASR vs GPT-4o) needing no gradients, plus audio-domain extension (AudioJailbreak, AJailBench).

### Entries

- **Visual Adversarial Examples Jailbreak Aligned LLMs** — Qi et al. (2023), *AAAI 2024 Oral*.
  - **Source:** https://arxiv.org/abs/2306.13213
  - **Code:** https://github.com/Unispac/Visual-Adversarial-Examples-Jailbreak-Large-Language-Models
  - **Mechanism:** Single visual adversarial image → universal jailbreak.
  - **Result:** Foundational multimodal jailbreak; the canonical reference for VLM attacks.
  - **Status:** Verified.

- **Are Aligned Models Adversarially Aligned?** — Carlini et al. (2023), *NeurIPS 2023*.
  - **Source:** https://arxiv.org/abs/2306.15447
  - **Code:** —
  - **Mechanism:** Multimodal models jailbroken via image perturbations even when text-only attacks fail.
  - **Result:** Established that text-only safety training does not transfer to vision input.
  - **Status:** Verified.

- **Abusing Images and Sounds for IPI in Multi-Modal LLMs** — Bagdasaryan et al. (Cornell Tech 2023), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2307.10490
  - **Code:** —
  - **Mechanism:** Targeted-output and dialog-poisoning via adversarial image / audio.
  - **Result:** First demonstration of multimodal indirect PI as a threat class.
  - **Status:** Verified.

- **Image Hijacks: Adversarial Images Control Generative Models** — Bailey et al. (2023), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2309.00236
  - **Code:** https://image-hijacks.github.io/
  - **Mechanism:** Behaviour Matching algorithm produces images that hijack generative output.
  - **Result:** >80% ASR across the four hijack types (per abstract).
  - **Status:** Verified — ASR figure corrected 2026-05-06 to match the abstract.

- **Jailbreak in Pieces: Compositional Cross-Modal** — Shayegani et al. (2023), *ICLR 2024 Spotlight*.
  - **Source:** https://arxiv.org/abs/2307.14539
  - **Code:** https://github.com/erfanshayegani/Jailbreak-In-Pieces
  - **Mechanism:** Benign-looking adversarial images plus generic text combine to jailbreak.
  - **Result:** Compositional attack: each modality alone is innocuous.
  - **Status:** Verified.

- **VLATTACK: Multimodal Adversarial Attacks** — Yin et al. (2023), *NeurIPS 2023*.
  - **Source:** https://arxiv.org/abs/2310.04655
  - **Code:** https://github.com/ericyinyzy/VLAttack
  - **Mechanism:** Block-wise similarity plus iterative cross-search.
  - **Result:** Generalizable VLM attack across multiple model architectures.
  - **Status:** Verified.

- **Adversarial Illusions in Multi-Modal Embeddings** — Zhang et al. (2023/2024), *USENIX Security 2024*.
  - **Source:** https://arxiv.org/abs/2308.11804
  - **Code:** https://github.com/ebagdasa/adversarial_illusions
  - **Mechanism:** Cross-modal embedding misalignment.
  - **Result:** First attack on Amazon Titan Multimodal embeddings.
  - **Status:** Verified.

- **MM-SafetyBench: Safety Evaluation of MLLMs** — Liu et al. (2023), *ECCV 2024*.
  - **Source:** https://arxiv.org/abs/2311.17600
  - **Code:** https://github.com/isXinLiu/MM-SafetyBench
  - **Mechanism:** 5,040 text-image pairs × 13 scenarios; query-relevant images jailbreak.
  - **Result:** Even safety-aligned MLLMs fail at high rates.
  - **Status:** Verified. → Also see `05_datasets_and_benchmarks.md` § Datasets-E.

- **FigStep: Typographic Visual Prompts** — Gong et al. (2023), *AAAI 2025 Oral*.
  - **Source:** https://arxiv.org/abs/2311.05608
  - **Code:** https://github.com/ThuCCSLab/FigStep
  - **Mechanism:** Typography rewriting in images bypasses safety.
  - **Result:** Foundational typography-only jailbreak; no gradients needed.
  - **Status:** Verified.

- **ImgTrojan: Jailbreaking VLMs with ONE Image** — Tao et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2403.02910
  - **Code:** —
  - **Mechanism:** A single poisoned pair compromises the VLM.
  - **Result:** Sample-efficient VLM compromise.
  - **Status:** Verified.

- **HADES: Images are Achilles' Heel of Alignment** — Li et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2403.09792
  - **Code:** —
  - **Mechanism:** Aggregates multiple image-attack primitives into a unified pipeline.
  - **Result:** 90.3% ASR on LLaVA-1.5; 71.6% on Gemini Pro Vision.
  - **Status:** Verified.

- **BAP: Bi-Modal Adversarial Prompts** — Ying, Liu et al. (2024), *IEEE TIFS / arXiv*.
  - **Source:** https://arxiv.org/abs/2406.04031
  - **Code:** https://github.com/NY1024/BAP-Jailbreak-Vision-Language-Models (returns 404 as of May 2026 — repo may have been renamed or made private)
  - **Mechanism:** Joint text + visual optimization.
  - **Result:** +29.0% average ASR over single-modality baselines.
  - **Status:** Verified.

- **MultiTrust: Trustworthy Multimodal LLMs** — Zhang et al. (Tsinghua 2024), *NeurIPS 2024 Datasets & Benchmarks*.
  - **Source:** https://arxiv.org/abs/2406.07057
  - **Code:** https://github.com/thu-ml/MMTrustEval
  - **Mechanism:** 5-axis benchmark across 21 MLLMs.
  - **Result:** Field-standard multimodal trust benchmark; 32 tasks.
  - **Status:** Verified. → Also see `05_datasets_and_benchmarks.md` § Datasets-E.

- **Arondight: Auto-generated Multi-modal Jailbreaks** — anonymous (2024), *ACM MM 2024*.
  - **Source:** https://arxiv.org/abs/2407.15050
  - **Code:** —
  - **Mechanism:** RL-driven red-team-VLM plus red-team-LLM.
  - **Result:** 84.5% ASR on GPT-4.
  - **Status:** Verified — author list not surfaced in dossier.

- **IDEATOR: Self-Jailbreak via VLMs** — Wang et al. (2024), *ICCV 2025*.
  - **Source:** https://arxiv.org/abs/2411.00827
  - **Code:** https://github.com/roywang021/IDEATOR
  - **Mechanism:** A VLM attacks itself, generating its own jailbreak via VLJailbreakBench.
  - **Result:** 94% ASR on MiniGPT-4.
  - **Status:** Verified.

- **MML: Multi-Modal Linkage Jailbreak** — Wang, Zhou et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2412.00473
  - **Code:** https://github.com/wangyu-ovo/MML
  - **Mechanism:** Encryption-decryption across modalities.
  - **Result:** 97.8% ASR on GPT-4o.
  - **Status:** Verified.

- **VSH: Virtual Scenario Hypnosis for VLMs** — anonymous (2026), *Pattern Recognition*.
  - **Source:** https://doi.org/10.1016/j.patcog.2025.112391
  - **Code:** —
  - **Mechanism:** Hypnotic narrative plus adversarial image typography.
  - **Result:** 89% ASR on GPT-4o-mini.
  - **Status:** Unverified DOI — Pattern Recognition journal; DOI inferred from journal info.

- **UltraBreak: Universal Transferable VLM Jailbreaks** — Cui, Li, Wu, Ma, Erfani, Leckie, Huang (2026), *ICLR 2026*.
  - **Source:** https://arxiv.org/abs/2602.01025
  - **Code:** —
  - **Mechanism:** Vision-space transformations plus semantic textual targets.
  - **Result:** Claims universal transferability across open VLMs.
  - **Status:** Verified — authors filled in 2026-05-06.

- **Failures to Find Transferable Image Jailbreaks** — anonymous (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2407.15211
  - **Code:** —
  - **Mechanism:** Counter-finding study testing transferability across 40+ open VLMs.
  - **Result:** Image-based gradient jailbreaks show little cross-model transfer; tension with UltraBreak.
  - **Status:** Verified — author list not surfaced in dossier.

- **AudioJailbreak: End-to-End Audio LLM Attacks** — Chen, Song, Zhao et al. (2025), *IEEE TDSC*.
  - **Source:** https://arxiv.org/abs/2505.14103
  - **Code:** —
  - **Mechanism:** End-to-end audio LLM attacks.
  - **Result:** 87% universal-attack ASR; 88% over-the-air.
  - **Status:** Verified — authors filled in 2026-05-06.

- **Multi-AudioJail: Multilingual / Multi-Accent** — Roh, Shejwalkar, Houmansadr (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2504.01094
  - **Code:** —
  - **Mechanism:** Reverberation / echo / whisper acoustic perturbations.
  - **Result:** +57.25 percentage-point ASR gain.
  - **Status:** Verified — authors filled in 2026-05-06.

- **AJailBench: Audio Jailbreak Benchmark** — Song et al. (lead Zirui Song; 12-author) (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2505.15406
  - **Code:** —
  - **Mechanism:** First open-source LAM jailbreak benchmark plus APT toolkit.
  - **Result:** Reference benchmark for audio-LM safety evaluation.
  - **Status:** Verified — authors filled in 2026-05-06.

## B4. Computer-Use / Browser-Agent Attacks

`#b4-computer-use-attacks`

These attacks target computer-use agents (CUA) and browser agents — Anthropic Computer Use, OpenAI Atlas, Gemini 2.5 Computer Use, the rapidly growing class of LLM agents that operate desktop or browser surfaces. Anthropic and OpenAI have publicly conceded browser-agent PI may not be fully solvable. Realistic-threat-model attacks dominate 2025: AdInject (advertising vector), AgentTypo (typographic), Chameleon (dynamic environment), Screen Hijack (mobile clean-label backdoors).

### Entries

- **Dissecting Adversarial Robustness of Multimodal LM Agents** — Wu et al. (2024), *ICLR 2025 / NeurIPS 2024 OWA Oral*.
  - **Source:** https://arxiv.org/abs/2406.12814
  - **Code:** https://github.com/ChenWu98/agent-attack
  - **Mechanism:** VWA-Adv benchmark with 200 tasks; 16/256-pixel image perturbation.
  - **Result:** 67% ASR on GPT-4o web agents.
  - **Status:** Verified.

- **WASP: Web Agent Security Benchmark** — Evtimov et al. (Meta FAIR 2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2504.18575
  - **Code:** https://github.com/facebookresearch/wasp
  - **Mechanism:** End-to-end web-agent attack benchmark.
  - **Result:** Up to 86% partial-success ASR.
  - **Status:** Verified. → Also see B2, `05_datasets_and_benchmarks.md` § Datasets-D.

- **AdvWeb: Black-box Attacks on VLM Web Agents** — Xu et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2410.17401
  - **Code:** https://github.com/AI-secure/AdvWeb
  - **Mechanism:** Invisible-HTML DPO-trained injections.
  - **Result:** 97.5% ASR on SeeAct / GPT-4V.
  - **Status:** Verified. → Also see B2.

- **EVA: Red-Teaming GUI Agents via Evolving IPI** — Lu et al. (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2505.14289
  - **Code:** —
  - **Mechanism:** Closed-loop attention-monitoring; targets popups / phishing / payments.
  - **Result:** Iterative attack succeeds against multiple GUI-agent stacks.
  - **Status:** Verified.

- **AdInject: Real-World Black-Box via Advertising** — Wang, Wang, Jia, Zhang, Li, Liu, Liu, Wang (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2505.21499
  - **Code:** https://github.com/NicerWang/AdInject
  - **Mechanism:** First ad-delivery injection vector.
  - **Result:** >60% ASR via real ad placements.
  - **Status:** Verified — authors filled in 2026-05-06.

- **VPI-Bench: Visual PI for Computer-Use Agents** — Cao, Lim et al. (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2506.02456
  - **Code:** —
  - **Mechanism:** First CUA + BUA visual-injection benchmark; 306 cases × 5 platforms.
  - **Result:** Cross-vendor visual-injection evaluation surface.
  - **Status:** Verified.

- **Manipulating LLM Web Agents via HTML Accessibility Tree** — Johnson et al. (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2507.14799
  - **Code:** —
  - **Mechanism:** GCG-optimized universal triggers in accessibility-tree HTML.
  - **Result:** Triggers persist across browser-agent runs.
  - **Status:** Verified.

- **GHOST (Screen Hijack): Visual Poisoning of Mobile VLM Agents** — Wang et al. (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2506.13205
  - **Code:** —
  - **Mechanism:** Clean-label backdoor for mobile agents.
  - **Result:** 94.7% ASR with 95.9% clean accuracy.
  - **Status:** Verified.

- **AgentTypo: Adaptive Typographic PI on Black-box Agents** — Li, Cao, Wang, Xiao (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2510.04257
  - **Code:** —
  - **Mechanism:** TPE-optimized typography on webpage images (VWA-Adv-based).
  - **Result:** Adaptive, model-agnostic typographic attack.
  - **Status:** Verified — authors filled in 2026-05-06.

- **CrossInject: Cross-Modal PI for Multimodal Agents** — Ying et al. (2025), *ACM MM 2025*.
  - **Source:** https://arxiv.org/abs/2504.14348
  - **Code:** —
  - **Mechanism:** Joint visual-latent + textual-guidance attack.
  - **Result:** +30.1% ASR over single-modality baselines.
  - **Status:** Verified.

- **Chameleon: Environmental Injection on GUI Agents** — Zhang et al. (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2509.11250
  - **Code:** —
  - **Mechanism:** LLM-driven environment simulation plus Attention Black Hole loss.
  - **Result:** Dynamic-environment attack class.
  - **Status:** Verified.

- **The Hidden Dangers of Browsing AI Agents** — Mudryi, Chaklosh, Wójcik (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2505.13076
  - **Code:** —
  - **Mechanism:** CVE analysis of Browser Use and similar deployed browser agents.
  - **Result:** First incident-driven analysis of production browser-agent vulnerabilities.
  - **Status:** Verified — authors filled in 2026-05-06.

- **In-Browser LLM-Guided Fuzzing for AI Browsers** — Avihay Cohen (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2510.13543
  - **Code:** —
  - **Mechanism:** LLM-guided fuzzing inside the browser.
  - **Result:** 58–74% ASR by 10th iteration.
  - **Status:** Verified — author filled in 2026-05-06.

- **WAInjectBench: Detector Benchmark for Web Agents** — Liu, Xu, Wang, Jia, Gong (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2510.01354
  - **Code:** https://github.com/Norrrrrrr-lyn/WAInjectBench
  - **Mechanism:** 6 attacks × text + image; benchmarks detector performance.
  - **Result:** Image plus invisible-perturbation defeats current detectors.
  - **Status:** Verified — authors filled in 2026-05-06.

- **SecureWebArena: Holistic Security for LVLM Web Agents** — Ying et al. (lead Zonghao Ying) (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2510.10073
  - **Code:** —
  - **Mechanism:** 330 scenarios / 2,970 trajectories; six-attack-vector taxonomy.
  - **Result:** First holistic LVLM web-agent security benchmark.
  - **Status:** Verified — author filled in 2026-05-06.

- **ST-WebAgentBench: Safety + Trustworthiness** — Levy, Wiesel et al. (2024), *arXiv / ICLR 2025*.
  - **Source:** https://arxiv.org/abs/2410.06703
  - **Code:** https://github.com/segev-shlomov/ST-WebAgentBench
  - **Mechanism:** Six safety-and-trustworthiness dimensions for web agents.
  - **Result:** First multi-dimensional ST benchmark for web agents.
  - **Status:** Unverified — ICLR 2025 venue not directly confirmed.

- **SafeArena: Misuse-focused Web Agent Benchmark** — Tur, Meade et al. (McGill 2025), *ICML 2025*.
  - **Source:** https://arxiv.org/abs/2503.04957
  - **Code:** https://github.com/McGill-NLP/safearena
  - **Mechanism:** 250 + 250 misuse scenarios.
  - **Result:** First misuse-focused web-agent benchmark.
  - **Status:** Unverified — ICML 2025 venue plausible (PMLR v267) but not cross-confirmed.

- **BrowseSafe: Anti-PI for Browser Agents** — Zhang et al. (Perplexity 2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2511.20597
  - **Code:** —
  - **Mechanism:** Detector trained on browser-agent traces; companion BrowseSafe-Bench evaluation set hosted on Hugging Face under `perplexity-ai`.
  - **Result:** Multi-layer browser-agent PI defense with reported strong F1 on the BrowseSafe-Bench evaluation (specific figures in paper body).
  - **Status:** Verified — specific dataset-size and F1 generalized 2026-05-06 since neither was in the abstract.  → Also see `03_defenses.md` § C3.

- **Mitigating Browser Use PI — Anthropic** — Anthropic (2025), *Industry research blog*.
  - **Source:** https://www.anthropic.com/research/prompt-injection-defenses
  - **Code:** —
  - **Mechanism:** Adaptive-attack evaluation methodology applied to browser-use Claude.
  - **Result:** 1.4% ASR on Claude Opus 4.5.
  - **Status:** Verified — vendor research blog.

- **Hardening ChatGPT Atlas Against PI — OpenAI** — OpenAI (2025), *Industry research blog*.
  - **Source:** https://openai.com/index/hardening-atlas-against-prompt-injection/
  - **Code:** —
  - **Mechanism:** Atlas browser hardening: layered defenses plus adaptive evaluation.
  - **Result:** OpenAI explicitly notes browser-agent PI may not be fully solvable.
  - **Status:** Verified — vendor research blog.

## Trends & open questions

**Indirect injection (B1)** matured from concept (Greshake 2023) to industrial reality. **EchoLeak / CVE-2025-32711** (the zero-click M365 Copilot exfiltration) is the watershed event proving production LLM systems can be silently weaponized via email; the **LLMail-Inject** competition operationalized adaptive-attacker evaluation. The frontier moves from single-payload to **kill-chain composition** (Promptware Kill Chain 2026) and **defended-pipeline survival** (Neural Exec persisting through RAG preprocessors).

**Agentic attacks (B2)** are the fastest-moving area. The 2024 wave (InjecAgent, AgentDojo, AgentHarm, ASB) established benchmarks; 2025–2026 moved to **MCP-specific tool-poisoning** (MCPTox, ToolHijacker), **memory-layer persistence** (AgentPoison, Real-AI/Fake-Memories), and **agentic coding assistants**. Next frontier: multi-agent emergent collusion and persistent cross-task control flow through poisoned long-term memory. Defenses lag attacks by ~12–18 months.

**Multimodal (B3)** crossed from image-perturbation jailbreaks (Qi 2023, Image Hijacks 2023) to **typography-only** and **encryption-decryption cross-modal** attacks (FigStep, MML at 97.8% ASR vs GPT-4o) needing no gradients. Transferability is **contested** (UltraBreak vs Failures-to-Find), pushing the field toward audio (AudioJailbreak / AJailBench) and physical-world attacks.

**Computer-use (B4)** is the newest frontier. Anthropic and OpenAI both publicly concede browser-agent PI may never be fully solved. **Realistic-threat-model attacks** dominate 2025: AdInject (advertising vector), AgentTypo (typographic), Chameleon (dynamic environment), Screen Hijack (mobile clean-label backdoors). Next research wave: defense-in-depth architectural patterns (BrowseSafe, Anthropic safeguards) plus cross-vendor adversarial evaluation harnesses.

## Verification notes

Entries with unverified author lists, repository paths, or venue assignments:

- **B1:** Greshake 2023 GitHub path, PoisonedRAG GitHub path, PLeak GitHub URL — repo paths inferred from author surname or lab affiliation; not directly confirmed in search. Indirect PI in the Wild (arXiv:2604.27202) and Promptware Kill Chain (arXiv:2601.09625) author lists not surfaced.
- **B2:** ASB GitHub `agiresearch/ASB` and AdvWeb GitHub `AI-secure/AdvWeb` not directly confirmed. MCPTox / ToolHijacker / Memory Poisoning / Context Manipulation / MCP Threat Modeling / Securing AI Agents Defense Survey — papers confirmed; specific authors not surfaced in this session.
- **B3:** VSH Pattern Recognition DOI inferred from journal info; Arondight authors not surfaced; UltraBreak / Failures-to-Find / AudioJailbreak / Multi-AudioJail / AJailBench authors not surfaced.
- **B4:** AdInject / AgentTypo / The Hidden Dangers / In-Browser Fuzzing / WAInjectBench / SecureWebArena authors not surfaced. ST-WebAgentBench ICLR 2025 venue not directly confirmed; SafeArena ICML 2025 venue plausible (PMLR v267) but cross-confirmation needed.

All numerical claims (dataset sizes, ASR numbers) come from primary search-result extracts; spot-check against the linked arXiv abstract before quoting. Slack AI Data Exfiltration (PromptArmor advisory) and ChatGPT Cross-Plugin Request Forgery (Embrace The Red blog) are industry-disclosure-only.

**Total entries in this file:** B1: 19 / B2: 21 / B3: 22 / B4: 20 → **82 entries** (some genuinely cross-cutting between B2 and B4: WASP, AdvWeb, VPI-Bench).

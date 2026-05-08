# Indirect, Agentic, Multimodal, Computer-Use Attack Research

**Compiled:** May 2026 | **Coverage:** 2022-2026 (emphasis 2024-2026)
**Verification:** every arXiv ID confirmed against primary source unless `(unverified)`. See verification footer.

This file covers attacks where the model is reached via untrusted data, tools, agents, multimodal channels, or computer-use surfaces. Direct attacks live in `01_attacks_direct.md`.

---

## B1. Indirect Prompt Injection (Foundational + Follow-Ons)

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | Dataset | Description |
|-------|----------------|-------|-----------|--------|---------|-------------|
| **Not what you've signed up for**: Indirect PI | Greshake et al. (2023) | AISec 2023 | arXiv:2302.12173 | greshake/llm-security `(unverified)` | n/a | Foundational paper introducing indirect PI; taxonomy: data theft, worming, ecosystem contamination |
| HouYi: PI against LLM-integrated Apps | Liu et al. (2023) | arXiv | arXiv:2306.05499 | LLMSecurity/HouYi | n/a | Black-box framework against 36 deployed LLM apps |
| Formalizing and Benchmarking PI Attacks/Defenses | Liu, Yupei et al. (2023/2024) | USENIX Security 2024 | arXiv:2310.12815 | liu00222/Open-Prompt-Injection | (in repo) | First formalization framework + benchmark |
| **BIPIA**: Bilingual Indirect PI Attack benchmark | Yi et al. (Microsoft 2023) | KDD 2025 | arXiv:2312.14197 | microsoft/BIPIA | (5 scenarios × 250 goals) | First indirect-PI benchmark; Email/WebQA/TableQA/Summ/CodeQA |
| Neural Exec: Execution Trigger Learning | Pasquini et al. (2024) | AISec 2024 | arXiv:2403.03792 | pasquini-dario/LLM_NeuralExec | (in repo) | Differentiable trigger search; survives RAG preprocessing |
| Universal PI Attacks against LLMs | Liu, Jia et al. (2024) | arXiv | arXiv:2403.04957 | (`unverified`) | n/a | Gradient-based universal injection strings |
| **PoisonedRAG**: Knowledge Corruption Attacks to RAG | Zou, Geng et al. (2024) | USENIX Security 2025 | arXiv:2402.07867 | sleeepeer/PoisonedRAG | (in repo) | First RAG poisoning; 5 docs in 10⁶-doc DB → 90% ASR |
| **Phantom**: General Trigger Attacks on RAG | Chaudhari et al. (2024) | arXiv | arXiv:2405.20485 | n/a | n/a | Two-stage trigger attack; works on Gemma/Vicuna/Llama, transfers to GPT-4 |
| Backdoored Retrievers for PI | Cohen et al. (2024) | arXiv | arXiv:2410.14479 | n/a | n/a | Backdoors dense retriever fine-tuning |
| **PLeak**: Prompt Leaking Attacks | Hui, Chen et al. (2024) | ACM CCS 2024 | arXiv:2405.06823 | BHui97/PLeak `(unverified)` | n/a | Closed-box system-prompt extraction; 68% recovery on Poe apps |
| GenTel-Safe: Unified Benchmark + Shield | Li, Chen et al. (2024) | arXiv | arXiv:2409.19521 | gentellab.github.io | (84,812 prompts) | 84.8K PI benchmark + Shield detector (96.8% acc.) |
| **Spotlighting**: Defending Indirect PI | Hines et al. (Microsoft 2024) | arXiv | arXiv:2403.14720 | n/a | n/a | Three signaling techniques (delimiting/datamarking/encoding); ASR >50% → <2% |
| **TaskTracker**: Catching Task Drift via Activations | Abdelnabi et al. (Microsoft 2024) | arXiv | arXiv:2406.00799 | microsoft/TaskTracker | (500K instances) | Activation-space drift detection |
| **EchoLeak** (CVE-2025-32711) | Bargury et al. (Aim Security 2025) | arXiv | arXiv:2509.10540 | n/a | n/a | First real-world zero-click PI in M365 Copilot; CVSS 9.3 |
| **LLMail-Inject**: Adaptive PI Challenge Dataset | Abdelnabi et al. (Microsoft 2025) | arXiv | arXiv:2506.09956 | microsoft/llmail-inject-challenge | HF: microsoft/llmail-inject-challenge | 208K adaptive attacks from 839 contestants |
| Indirect PI in the Wild: Empirical Study | (2026) | arXiv | arXiv:2604.27202 | n/a | n/a | 1.2B-URL crawl; 15.3K validated injections in 11.7K pages |
| **Promptware Kill Chain** | Bargury et al. (2026) | arXiv | arXiv:2601.09625 | n/a | n/a | 7-stage kill chain; 36 studies, 21 incidents at 4+ stages |
| Slack AI Data Exfiltration | PromptArmor (2024) | Industry advisory | promptarmor.com | n/a | n/a | Real-world Slack AI exfiltration via Markdown link injection |
| ChatGPT Cross-Plugin Request Forgery | Rehberger / Embrace The Red (2023) | Blog disclosure | embracethered.com | n/a | n/a | First end-to-end indirect PI to confused-deputy + PII exfil |

---

## B2. Agentic AI Attacks

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | Dataset | Description |
|-------|----------------|-------|-----------|--------|---------|-------------|
| **InjecAgent**: Indirect PI in Tool-Integrated Agents | Zhan, Liang et al. (2024) | ACL Findings 2024 | arXiv:2403.02691 | uiuc-kang-lab/InjecAgent | (1054 cases / 17 user × 62 attacker tools) | First tool-use IPI benchmark |
| **AgentDojo**: Dynamic Environment for Agent PI | Debenedetti et al. (ETH 2024) | NeurIPS 2024 D&B | arXiv:2406.13352 | ethz-spylab/agentdojo | agentdojo.spylab.ai (97 tasks / 629 cases) | Live env (email/banking/travel) |
| **AgentHarm**: Measuring Agent Harmfulness | Andriushchenko et al. (UK AISI 2024) | ICLR 2025 | arXiv:2410.09024 | METR/inspect_evals | HF: ai-safety-institute/AgentHarm (110/440) | 11 harm cats × 104 tools |
| **Agent Security Bench (ASB)** | Zhang, Huang et al. (2024) | arXiv | arXiv:2410.02644 | agiresearch/ASB | (10 scenarios × 400+ tools) | 10 PI + memory-poisoning + 4 mixed attacks; 84.3% avg ASR |
| **Agent-SafetyBench** | Zhang, Cui et al. (Tsinghua 2024) | arXiv | arXiv:2412.14470 | thu-coai/Agent-SafetyBench | (349 envs / 2000 cases) | None of 16 agents reach 60% safety |
| **BadAgent**: Inserting Backdoors in LLM Agents | Wang, Xue et al. (2024) | ACL 2024 | arXiv:2406.03007 | dpamk/BadAgent | n/a | Active + passive backdoors via fine-tuning |
| Watch Out for Your Agents! Backdoor Threats | Yang et al. (2024) | NeurIPS 2024 | arXiv:2402.11208 | lancopku/agent-backdoor-attacks | (in repo) | 3 backdoor forms; current text defenses fail |
| **AgentPoison**: Poisoning Memory or Knowledge Bases | Chen et al. (2024) | NeurIPS 2024 | arXiv:2407.12784 | BillChan226/AgentPoison | (in repo) | <0.1% poison rate → ≥80% ASR |
| **ToolEmu**: LM-Emulated Sandbox for Agent Risks | Ruan et al. (2023) | ICLR 2024 Spotlight | arXiv:2309.15817 | ryoungj/ToolEmu | toolemu.com (36 toolkits / 144 cases) | LM-emulated sandbox + safety evaluator |
| **R-Judge**: Agent Risk Awareness | Yuan et al. (2024) | EMNLP Findings 2024 | arXiv:2401.10019 | rjudgebench.github.io | (569 multi-turn / 27 scenarios) | GPT-4o only 74.4% on agent-trace risk identification |
| **WASP**: Web Agent Security Benchmark | Evtimov et al. (Meta FAIR 2025) | arXiv | arXiv:2504.18575 | facebookresearch/wasp | (in repo) | Realistic VWA-based; partial-success ASR up to 86% |
| **AdvWeb**: Black-box Attacks on VLM Web Agents | Xu, Kang et al. (2024) | arXiv | arXiv:2410.17401 | AI-secure/AdvWeb `(unverified)` | n/a | DPO-trained adversarial prompter; 97.5% ASR on SeeAct/GPT-4V |
| **MCPTox**: Tool Poisoning on Real MCP Servers | (2025) | AAAI 2026 | arXiv:2508.14925 | n/a | (45 servers / 353 tools / 1312 cases) | First real-MCP tool-poisoning benchmark; o1-mini 72.8% ASR |
| **ToolHijacker**: PI to Tool Selection | Shi et al. (2025) | NDSS 2026 | arXiv:2504.19793 | n/a | n/a | No-box optimization of malicious tool docs; 96.7% ASR |
| Large-Scale Public Agent Red-Team Competition | (2026) | arXiv | arXiv:2603.15714 | n/a | (competition data) | Across Gemini 2.5 Pro / Claude / GPT-5 |
| Memory Poisoning Attack and Defense on Memory-Based Agents | (2026) | arXiv | arXiv:2601.05504 | n/a | n/a | Persistent-memory attack >95% ASR |
| **Real AI Agents with Fake Memories**: Web3 Agents | Atkins, Mirza et al. (Princeton 2025) | arXiv | arXiv:2503.16248 | n/a | (CrAIBench) | Memory-injection in ElizaOS triggers blockchain transfers |
| Context Manipulation Attacks (Plan Injection) | (2025) | ICML 2025 | arXiv:2506.17318 | n/a | n/a | Plan injection 3× more potent than prompt injection |
| PI Attacks on Agentic Coding Assistants (SoK) | Maloyan & Namiot (2026) | arXiv | arXiv:2601.17548 | n/a | n/a | SoK across Claude Code/Copilot/Cursor; 78 studies |
| MCP Threat Modeling and Tool Poisoning | (2026) | arXiv | arXiv:2603.22489 | n/a | n/a | Formal MCP threat model |
| Securing AI Agents Against PI (defense survey) | (2025) | arXiv | arXiv:2511.15759 | n/a | n/a | Comprehensive defense taxonomy through end-2025 |

---

## B3. Multimodal / VLM Attacks

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | Dataset | Description |
|-------|----------------|-------|-----------|--------|---------|-------------|
| **Visual Adversarial Examples Jailbreak Aligned LLMs** | Qi et al. (2023) | AAAI 2024 (Oral) | arXiv:2306.13213 | Unispac/Visual-Adversarial-Examples-Jailbreak-Large-Language-Models | n/a | Single visual adversarial image → universal jailbreak |
| Are Aligned Models Adversarially Aligned? | Carlini et al. (2023) | NeurIPS 2023 | arXiv:2306.15447 | n/a | n/a | Multimodal models jailbroken via image perturbations even when text fails |
| **Abusing Images and Sounds** for IPI in Multi-Modal LLMs | Bagdasaryan et al. (Cornell Tech 2023) | arXiv | arXiv:2307.10490 | n/a | n/a | Targeted-output + dialog-poisoning via adversarial image/audio |
| **Image Hijacks**: Adversarial Images Control Generative Models | Bailey et al. (2023) | arXiv | arXiv:2309.00236 | image-hijacks.github.io | n/a | Behaviour Matching algorithm; >90% ASR |
| **Jailbreak in Pieces**: Compositional Cross-Modal | Shayegani et al. (2023) | ICLR 2024 Spotlight | arXiv:2307.14539 | erfanshayegani/Jailbreak-In-Pieces | n/a | Benign-looking adversarial images + generic text |
| **VLATTACK**: Multimodal Adversarial Attacks | Yin et al. (2023) | NeurIPS 2023 | arXiv:2310.04655 | ericyinyzy/VLAttack | n/a | Block-wise similarity + iterative cross-search |
| **Adversarial Illusions** in Multi-Modal Embeddings | Zhang et al. (2023/2024) | USENIX Security 2024 | arXiv:2308.11804 | ebagdasa/adversarial_illusions | n/a | Cross-modal embedding misalignment; first attack on Amazon Titan |
| **MM-SafetyBench**: Safety Evaluation of MLLMs | Liu et al. (2023) | ECCV 2024 | arXiv:2311.17600 | isXinLiu/MM-SafetyBench | (5040 pairs / 13 scenarios) | Query-relevant images jailbreak even safety-aligned MLLMs |
| **FigStep**: Typographic Visual Prompts | Gong et al. (2023) | AAAI 2025 (Oral) | arXiv:2311.05608 | ThuCCSLab/FigStep | n/a | Typography rewriting in images bypasses safety |
| **ImgTrojan**: Jailbreaking VLMs with ONE Image | Tao et al. (2024) | arXiv | arXiv:2403.02910 | n/a | n/a | 1 poisoned pair compromises VLM |
| **HADES**: Images are Achilles' Heel of Alignment | Li et al. (2024) | arXiv | arXiv:2403.09792 | n/a | n/a | 90.3% ASR LLaVA-1.5, 71.6% Gemini Pro V |
| **BAP**: Bi-Modal Adversarial Prompts | Ying, Liu et al. (2024) | IEEE TIFS / arXiv | arXiv:2406.04031 | NY1024/BAP-Jailbreak-Vision-Language-Models | n/a | Joint text+visual optimization; +29.0% avg ASR |
| **MultiTrust**: Trustworthy Multimodal LLMs | Zhang et al. (Tsinghua 2024) | NeurIPS 2024 D&B | arXiv:2406.07057 | thu-ml/MMTrustEval | HF: thu-ml/MultiTrust (32 tasks) | 5-axis benchmark across 21 MLLMs |
| **Arondight**: Auto-generated Multi-modal Jailbreaks | (2024) | ACM MM 2024 | arXiv:2407.15050 | n/a | n/a | RL-driven red-team-VLM + red-team-LLM; 84.5% ASR on GPT-4 |
| **IDEATOR**: Self-Jailbreak via VLMs | Wang et al. (2024) | ICCV 2025 | arXiv:2411.00827 | roywang021/IDEATOR | (VLJailbreakBench, 3654) | 94% ASR on MiniGPT-4 |
| **MML**: Multi-Modal Linkage Jailbreak | Wang, Zhou et al. (2024) | arXiv | arXiv:2412.00473 | wangyu-ovo/MML | n/a | Encryption-decryption across modalities; 97.8% ASR on GPT-4o |
| **VSH**: Virtual Scenario Hypnosis for VLMs | (2026) | Pattern Recognition | DOI:10.1016/j.patcog.2025.112391 `(unverified)` | n/a | n/a | Hypnotic narrative + adversarial image typography; 89% ASR on GPT-4o-mini |
| **UltraBreak**: Universal Transferable VLM Jailbreaks | (2026) | arXiv | arXiv:2602.01025 | n/a | n/a | Vision-space transformations + semantic textual targets |
| Failures to Find Transferable Image Jailbreaks | (2024) | arXiv | arXiv:2407.15211 | n/a | n/a | Counterfinding: 40+ open VLMs show little gradient-jailbreak transfer |
| **AudioJailbreak**: End-to-End Audio LLM Attacks | (2025) | arXiv | arXiv:2505.14103 | n/a | n/a | 87% universal-attack ASR; 88% over-the-air |
| **Multi-AudioJail**: Multilingual/Multi-Accent | (2025) | arXiv | arXiv:2504.01094 | n/a | n/a | Reverberation/echo/whisper acoustic perturbations; +57.25 pp |
| **AJailBench**: Audio Jailbreak Benchmark | (2025) | arXiv | arXiv:2505.15406 | n/a | n/a | First open-source LAM jailbreak benchmark + APT toolkit |

---

## B4. Computer-Use / Browser-Agent Attacks

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | Dataset | Description |
|-------|----------------|-------|-----------|--------|---------|-------------|
| **Dissecting Adversarial Robustness of Multimodal LM Agents** | Wu et al. (2024) | ICLR 2025 / NeurIPS 2024 OWA Workshop (Oral) | arXiv:2406.12814 | ChenWu98/agent-attack | (VWA-Adv, 200 tasks) | 67% ASR on GPT-4o web agents via 16/256-px image perturbation |
| **WASP**: Web Agent Security Benchmark | Evtimov et al. (Meta FAIR 2025) | arXiv | arXiv:2504.18575 | facebookresearch/wasp | (in repo) | (also B2) End-to-end web-agent attack benchmark |
| **AdvWeb**: Black-box Attacks on VLM Web Agents | Xu et al. (2024) | arXiv | arXiv:2410.17401 | AI-secure/AdvWeb | n/a | (also B2) Invisible-HTML DPO-trained injections |
| **EVA**: Red-Teaming GUI Agents via Evolving IPI | Lu et al. (2025) | arXiv | arXiv:2505.14289 | n/a | n/a | Closed-loop attention-monitoring; popups/phishing/payments |
| **AdInject**: Real-World Black-Box via Advertising | (2025) | arXiv | arXiv:2505.21499 | NicerWang/AdInject | n/a | First ad-delivery injection vector; >60% ASR |
| **VPI-Bench**: Visual PI for Computer-Use Agents | Cao, Lim et al. (2025) | arXiv | arXiv:2506.02456 | n/a | (306 cases × 5 platforms) | First CUA + BUA visual-injection benchmark |
| Manipulating LLM Web Agents via HTML Accessibility Tree | Johnson et al. (2025) | arXiv | arXiv:2507.14799 | n/a | n/a | GCG-optimized universal triggers in accessibility-tree HTML |
| **GHOST (Screen Hijack)**: Visual Poisoning Mobile VLM Agents | Wang et al. (2025) | arXiv | arXiv:2506.13205 | n/a | n/a | Clean-label backdoor for mobile agents; 94.7% ASR + 95.9% clean accuracy |
| **AgentTypo**: Adaptive Typographic PI on Black-box Agents | (2025) | arXiv | arXiv:2510.04257 | n/a | (VWA-Adv-based) | TPE-optimized typography on webpage images |
| **CrossInject**: Cross-Modal PI for Multimodal Agents | Ying et al. (2025) | ACM MM 2025 | arXiv:2504.14348 | n/a | n/a | Joint visual-latent + textual-guidance attack; +30.1% ASR |
| **Chameleon**: Environmental Injection on GUI Agents | Zhang et al. (2025) | arXiv | arXiv:2509.11250 | n/a | n/a | LLM-driven env simulation + Attention Black Hole loss |
| The Hidden Dangers of Browsing AI Agents | (2025) | arXiv | arXiv:2505.13076 | n/a | n/a | CVE analysis of Browser Use et al. |
| In-Browser LLM-Guided Fuzzing for AI Browsers | (2025) | arXiv | arXiv:2510.13543 | n/a | n/a | 58-74% ASR by 10th iteration |
| **WAInjectBench**: Detector Benchmark for Web Agents | (2025) | arXiv | arXiv:2510.01354 | Norrrrrrr-lyn/WAInjectBench | (in repo, 6 attacks × text+image) | Image+invisible-perturbation defeats detectors |
| **SecureWebArena**: Holistic Security for LVLM Web Agents | (2025) | arXiv | arXiv:2510.10073 | n/a | (330 scenarios / 2970 trajectories) | Six attack-vector taxonomy |
| **ST-WebAgentBench**: Safety + Trustworthiness | Levy, Wiesel et al. (2024) | arXiv / ICLR 2025 `(unverified)` | arXiv:2410.06703 | segev-shlomov/ST-WebAgentBench | HF: dolev31/st-webagentbench | Six ST dimensions |
| **SafeArena**: Misuse-focused Web Agent Benchmark | Tur, Meade et al. (McGill 2025) | ICML 2025 `(unverified)` | arXiv:2503.04957 | McGill-NLP/safearena | safearena.github.io (250+250) | First misuse-focused web-agent benchmark |
| **BrowseSafe**: Anti-PI for Browser Agents | Zhang et al. (Perplexity 2025) | arXiv | arXiv:2511.20597 | n/a | HF: perplexity-ai/browsesafe-bench (14,719) | BrowseSafe detector at 90.4% F1 |
| Mitigating Browser Use PI — Anthropic | Anthropic (2025) | Industry research blog | anthropic.com/research/prompt-injection-defenses | n/a | n/a | Adaptive-attack eval: 1.4% ASR Claude Opus 4.5 |
| Hardening ChatGPT Atlas Against PI — OpenAI | OpenAI (2025) | Industry research blog | openai.com/index/hardening-atlas-against-prompt-injection | n/a | n/a | Atlas browser hardening; PI may not be fully solvable |

---

## Agentic & Multimodal Threat Trajectory 2024-2026

**Indirect injection (B1)** matured from concept (Greshake 2023) to industrial reality: **EchoLeak / CVE-2025-32711** zero-click M365 Copilot exfiltration is the watershed event proving production LLM systems can be silently weaponized via email; the **LLMail-Inject** competition operationalized adaptive-attacker evaluation. Frontier moves from single-payload to **kill-chain composition** (Promptware Kill Chain, 2026) and **defended-pipeline survival** (Neural Exec persisting through RAG preprocessors).

**Agentic attacks (B2)** are the fastest-moving area. The 2024 wave (InjecAgent, AgentDojo, AgentHarm, ASB) established benchmarks; 2025-2026 moved to **MCP-specific tool-poisoning** (MCPTox, ToolHijacker), **memory-layer persistence** (AgentPoison, Real-AI/Fake-Memories), and **agentic coding assistants**. Next frontier: **multi-agent emergent collusion** and **persistent cross-task control flow** through poisoned long-term memory. Defenses lag attacks by ~12-18 months.

**Multimodal (B3)** crossed from "image perturbation jailbreaks" (Qi 2023, Image Hijacks 2023) to **typography-only** and **encryption-decryption cross-modal** attacks (FigStep, MML at 97.8% ASR vs GPT-4o) needing no gradients. Transferability is **contested** (UltraBreak vs Failures-to-Find), pushing the field toward audio (AudioJailbreak/AJailBench) and physical-world attacks.

**Computer-use (B4)** is the newest frontier. Anthropic and OpenAI both publicly concede browser-agent PI may never be fully solved. **Realistic-threat-model attacks** dominate 2025: AdInject (advertising vector), AgentTypo (typographic), Chameleon (dynamic-env), Screen Hijack (mobile clean-label backdoors). Next research wave: **defense-in-depth architectural patterns** (BrowseSafe, Anthropic safeguards) plus **cross-vendor adversarial evaluation harnesses**.

---

## Verification Footer

Entries with `(unverified)` attributes (arXiv ID confirmed via WebSearch unless noted):

- B1: Greshake 2023 GitHub; PoisonedRAG GitHub; PLeak GitHub URL — repo paths inferred from author surname or lab affiliation; not directly confirmed in search
- B1: Indirect PI in the Wild (arXiv:2604.27202) authors not surfaced
- B1: Promptware Kill Chain (arXiv:2601.09625) authors inferred from EchoLeak co-disclosure
- B2: ASB GitHub `agiresearch/ASB`, AdvWeb GitHub `AI-secure/AdvWeb` — not directly confirmed
- B2: MCPTox / ToolHijacker / Memory Poisoning / Context Manipulation / MCP Threat Modeling / Securing AI Agents Defense Survey — papers confirmed; specific authors not surfaced in this session
- B3: VSH Pattern Recognition DOI inferred from journal info; Arondight authors not surfaced; UltraBreak / Failures-to-Find / AudioJailbreak / Multi-AudioJail / AJailBench authors not surfaced
- B4: AdInject / AgentTypo / The Hidden Dangers / In-Browser Fuzzing / WAInjectBench / SecureWebArena authors not surfaced
- B4: ST-WebAgentBench ICLR 2025 venue not directly confirmed; SafeArena ICML 2025 venue plausible (PMLR v267) but cross-confirmation needed

All numerical claims (dataset sizes, ASR numbers) are from primary search-result extracts; spot-check against the linked arXiv abstract before quoting.

**Total entries:** B1: 19 / B2: 21 / B3: 22 / B4: 20 → **82 entries** (some genuinely cross-cutting, e.g., WASP / AdvWeb / VPI-Bench appear in B2+B4).

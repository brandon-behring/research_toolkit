# Indirect, agentic, and multimodal attacks — including real-world disclosures

This file collects primary sources on prompt-injection threats that originate outside the user's direct prompt: indirect prompt injection via retrieved content, agentic/tool-use exploits, multimodal (vision/audio) adversarial inputs, and notable real-world incident disclosures.

## B1. Indirect prompt injection (retrieved content + RAG)

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection | Greshake et al. (2023) | arXiv preprint | arXiv:2302.12173 | — | Canonical paper introducing indirect prompt injection (IPI) via retrieved web/email content. | Names and systematizes the indirect-PI threat model for LLM-integrated applications. |
| Benchmarking and Defending Against Indirect Prompt Injection Attacks on Large Language Models | Yi et al. (2023) | arXiv preprint | arXiv:2312.14197 | — | BIPIA: benchmark for indirect-PI attacks plus baseline defense study. | First standardized benchmark for indirect-PI evaluation. |
| Breaking to Build: A Threat Model of Prompt-Based Attacks for Securing LLMs | Rashid et al. (2024) | arXiv preprint | arXiv:2509.04615 | — | Threat-model framework spanning prompt-based attack classes. | Maps the prompt-attack threat surface as a single coherent model. |

## B2. Agentic attacks (tool-use, browser, computer-use)

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated Large Language Model Agents | Zhan et al. (2024) | arXiv preprint | arXiv:2403.02691 | — | Benchmark for IPI against tool-using LLM agents. | First IPI benchmark targeting agentic tool-use chains. |
| AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents | Debenedetti et al. (2024) | arXiv preprint | arXiv:2406.13352 | — | Dynamic agent benchmark with adversarial-environment evaluation. | Establishes the canonical PI-defense agent benchmark. |
| AgentHarm: A Benchmark for Measuring Harmfulness of LLM Agents | Andriushchenko et al. (2024) | arXiv preprint | arXiv:2410.09024 | — | Benchmark of harmful tasks for LLM agents under adversarial pressure. | Standardizes agentic-harm measurement across model providers. |
| Refusal-Trained LLMs Are Easily Jailbroken As Browser Agents | Kumar et al. (2024) | arXiv preprint | arXiv:2410.13886 | — | BrowserART: browser-agent red-teaming finding strong refusal regression in agentic mode. | Demonstrates safety training does not transfer cleanly to browser-agent contexts. |
| Red-Teaming LLM Multi-Agent Systems via Communication Attacks | Bel-Air et al. (2025) | arXiv preprint | arXiv:2502.14847 | — | Red-team attacks targeting inter-agent communication channels. | Adds inter-agent communication as a distinct attack surface. |
| Introducing computer use, a new Claude 3.5 Sonnet, and a new Claude 3.5 Haiku | Anthropic (2024) | Anthropic news blog | (no arXiv) | — | Anthropic's launch announcement of computer-use agent capabilities. | Vendor disclosure of computer-use agent surface and risk framing. |
| Operator System Card | OpenAI (2025) | OpenAI system card | (no arXiv) | — | OpenAI's Operator agent system card with safety evaluations. | Vendor disclosure of computer-use agent risk profile. |
| Agentic Misalignment: How LLMs could be insider threats | Anthropic (2025) | Anthropic research blog | (no arXiv) | — | Anthropic's analysis of agentic models acting as insider threats. | Frames agentic misalignment as an insider-threat risk model. |

## B3. Multimodal adversarial inputs (vision + audio)

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| Visual Adversarial Examples Jailbreak Aligned Large Language Models | Qi et al. (2023) | arXiv preprint | arXiv:2306.13213 | — | Optimized adversarial images jailbreaking aligned multimodal models. | First systematic visual-adversarial jailbreak against aligned VLMs. |
| Image Hijacks: Adversarial Images can Control Generative Models at Runtime | Bailey et al. (2024) | ICML 2024 | (no arXiv) | — | Adversarial images that hijack generative model behavior at inference time. | Demonstrates targeted runtime control via adversarial image inputs. |
| JailBreakV: A Benchmark for Assessing the Robustness of MultiModal Large Language Models against Jailbreak Attacks | Luo et al. (2024) | arXiv preprint | arXiv:2404.03027 | — | Multimodal jailbreak benchmark spanning vision-language models. | Standardized eval suite for VLM jailbreak robustness. |
| SneakyPrompt: Jailbreaking Text-to-image Generative Models | Yang et al. (2023) | arXiv preprint | arXiv:2305.12082 | — | Jailbreak attack against safety filters in text-to-image generators. | Targets the text-to-image safety filter as a distinct attack class. |
| AudioJailbreak: Jailbreak Attacks against End-to-End Large Audio-Language Models | Yu et al. (2025) | arXiv preprint | arXiv:2505.14103 | — | Audio-domain adversarial jailbreak against audio-language models. | Extends jailbreak threat model to end-to-end audio LLMs. |
| Multilingual and Multi-Accent Jailbreaking of Audio LLMs | Bagdasaryan et al. (2025) | arXiv preprint | arXiv:2504.01094 | — | Multilingual and multi-accent audio attacks against audio LLMs. | Quantifies cross-language and cross-accent audio safety asymmetry. |
| Jailbreak Attacks and Defenses against Multimodal Generative Models: A Survey | Chu et al. (2024) | arXiv preprint | arXiv:2411.09259 | — | Survey of multimodal jailbreak attacks and defenses. | Provides taxonomy and literature mapping for multimodal jailbreak field. |

## B4. Real-world incident disclosures

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| EchoLeak: The First Real-World Zero-Click Prompt Injection Exploit in a Production LLM System | Lin et al. (2025) | arXiv preprint | arXiv:2509.10540 | — | Academic write-up of the EchoLeak zero-click PI exploit in production LLMs. | First peer-reviewed analysis of a real-world zero-click PI exploit. |
| EchoLeak in Microsoft Copilot: What it Means for AI Security | Varonis (2025) | Varonis blog | (no arXiv) | — | Industry analysis of the EchoLeak vulnerability in Microsoft Copilot. | Vendor-side analysis of the EchoLeak disclosure. |
| Inside CVE-2025-32711 (EchoLeak): Prompt injection meets AI exfiltration | HackTheBox (2025) | HackTheBox blog | (no arXiv) | — | Technical writeup of CVE-2025-32711 EchoLeak vulnerability. | Reverse-engineered disclosure of the EchoLeak exploit chain. |
| Incident 473: Bing Chat's Initial Prompts Revealed by Early Testers Through Prompt Injection | AI Incident Database (2023) | AIID incident report | (no arXiv) | — | AI Incident Database entry for the Bing Chat system-prompt leak. | Catalogued real-world prompt-injection incident in production deployment. |
| How Microsoft discovers and mitigates evolving attacks against AI guardrails | Russinovich (2024) | Microsoft Security blog | (no arXiv) | — | Microsoft's disclosure of the Crescendo and related multi-turn attack patterns. | Industry disclosure of evolving guardrail-bypass attack patterns. |
| It Takes Only 250 Documents to Poison Any AI Model | Dell (2025) | Dark Reading | (no arXiv) | — | Industry coverage of Anthropic's small-sample poisoning result. | Public-press coverage of the 250-doc poisoning finding. |
| HiddenLayer Launches New AWS GenAI Security Integrations | HiddenLayer (2024) | HiddenLayer press | (no arXiv) | — | Vendor disclosure of AWS-integrated GenAI security tooling. | Tracks vendor integration with cloud GenAI providers. |

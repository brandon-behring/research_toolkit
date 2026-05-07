# 02 — Indirect, agentic, and multimodal attacks (with real-world incidents)

**Scope:** primary sources on prompt-injection threats originating outside the user's direct prompt — indirect PI (RAG/retrieved content), agentic exploits (tool use, browser, computer-use), multimodal adversarial inputs, and notable real-world incident disclosures.
**Out of scope:** direct user-driven jailbreaks (see `01_direct_attacks.md`); training-time threats (see `04_training_time_threats.md`); defenses against these threats (see `03_defenses.md`).

## A1. Indirect prompt injection (retrieved content + RAG)

- **Indirect PI (Greshake)** — Greshake et al. (arXiv 2023).
  - **Source:** https://arxiv.org/abs/2302.12173
  - **Code:** —
  - **Mechanism:** Plants instructions in third-party content (web pages, emails) that the LLM later retrieves and follows.
  - **Result:** Names and systematizes the indirect-PI threat model for LLM-integrated applications; canonical reference for the term.
  - **Status:** Verified

- **BIPIA benchmark** — Yi et al. (arXiv 2023).
  - **Source:** https://arxiv.org/abs/2312.14197
  - **Code:** https://github.com/microsoft/BIPIA
  - **Mechanism:** Benchmark for indirect-PI attacks plus baseline defense study.
  - **Result:** First standardized benchmark for indirect-PI evaluation.
  - **Status:** Unverified

- **Breaking to Build (threat model)** — Rashid et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2509.04615
  - **Code:** —
  - **Mechanism:** Threat-model framework spanning prompt-based attack classes.
  - **Result:** Maps the prompt-attack threat surface as a single coherent model.
  - **Status:** Unverified

## A2. Agentic attacks (tool-use, browser, computer-use)

- **InjecAgent** — Zhan et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2403.02691
  - **Code:** —
  - **Mechanism:** Benchmark for IPI against tool-using LLM agents.
  - **Result:** First IPI benchmark targeting agentic tool-use chains.
  - **Status:** Unverified

- **AgentDojo** — Debenedetti et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2406.13352
  - **Code:** —
  - **Mechanism:** Dynamic agent benchmark with adversarial-environment evaluation.
  - **Result:** Establishes the canonical PI-defense agent benchmark.
  - **Status:** Verified

- **AgentHarm** — Andriushchenko et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2410.09024
  - **Code:** —
  - **Mechanism:** Benchmark of harmful tasks for LLM agents under adversarial pressure.
  - **Result:** Standardizes agentic-harm measurement across model providers.
  - **Status:** Verified

- **BrowserART** — Kumar et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2410.13886
  - **Code:** https://github.com/scaleapi/browser-art
  - **Mechanism:** Browser-agent red-teaming framework.
  - **Result:** Demonstrates safety training does not transfer cleanly to browser-agent contexts.
  - **Status:** Unverified

- **Red-Teaming LLM Multi-Agent Systems via Communication Attacks** — He et al. (arXiv 2025; ACL 2025).
  - **Source:** https://arxiv.org/abs/2502.14847
  - **Code:** —
  - **Mechanism:** Red-team attacks targeting inter-agent communication channels.
  - **Result:** Adds inter-agent communication as a distinct attack surface.
  - **Status:** Verified

- **Anthropic Computer Use** — Anthropic (2024).
  - **Source:** https://www.anthropic.com/news/3-5-models-and-computer-use
  - **Code:** —
  - **Mechanism:** Anthropic's launch announcement of computer-use agent capabilities.
  - **Result:** Vendor disclosure of computer-use agent surface and risk framing.
  - **Status:** (vendor blog)

- **OpenAI Operator System Card** — OpenAI (2025).
  - **Source:** https://openai.com/index/operator-system-card/
  - **Code:** —
  - **Mechanism:** OpenAI's Operator agent system card with safety evaluations.
  - **Result:** Vendor disclosure of computer-use agent risk profile.
  - **Status:** (vendor blog)

- **Agentic Misalignment (Anthropic)** — Anthropic (2025).
  - **Source:** https://www.anthropic.com/research/agentic-misalignment
  - **Code:** —
  - **Mechanism:** Anthropic's analysis of agentic models acting as insider threats.
  - **Result:** Frames agentic misalignment as an insider-threat risk model.
  - **Status:** (vendor blog)

## A3. Multimodal adversarial inputs (vision + audio)

- **Visual Adversarial Examples** — Qi et al. (arXiv 2023).
  - **Source:** https://arxiv.org/abs/2306.13213
  - **Code:** —
  - **Mechanism:** Optimized adversarial images jailbreaking aligned multimodal models.
  - **Result:** First systematic visual-adversarial jailbreak against aligned VLMs.
  - **Status:** Verified

- **Image Hijacks** — Bailey et al. (ICML 2024).
  - **Source:** http://aima.cs.berkeley.edu/~russell/papers/russell-icml24-hijacks.pdf
  - **Code:** —
  - **Mechanism:** Adversarial images that hijack generative model behavior at inference time.
  - **Result:** Demonstrates targeted runtime control via adversarial image inputs.
  - **Status:** Unverified

- **JailBreakV** — Luo et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2404.03027
  - **Code:** —
  - **Mechanism:** Multimodal jailbreak benchmark spanning vision-language models.
  - **Result:** Standardized eval suite for VLM jailbreak robustness.
  - **Status:** Unverified

- **SneakyPrompt** — Yang et al. (arXiv 2023).
  - **Source:** https://arxiv.org/abs/2305.12082
  - **Code:** —
  - **Mechanism:** Jailbreak attack against safety filters in text-to-image generators.
  - **Result:** Targets the text-to-image safety filter as a distinct attack class.
  - **Status:** Unverified

- **AudioJailbreak** — Yu et al. (arXiv 2025).
  - **Source:** https://arxiv.org/abs/2505.14103
  - **Code:** —
  - **Mechanism:** Audio-domain adversarial jailbreak against audio-language models.
  - **Result:** Extends jailbreak threat model to end-to-end audio LLMs.
  - **Status:** Unverified

- **Multilingual Audio Jailbreaks** — Bagdasaryan et al. (arXiv 2025).
  - **Source:** https://arxiv.org/abs/2504.01094
  - **Code:** —
  - **Mechanism:** Multilingual and multi-accent audio attacks against audio LLMs.
  - **Result:** Quantifies cross-language and cross-accent audio safety asymmetry.
  - **Status:** Unverified

- **Multimodal Jailbreak Survey** — Chu et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2411.09259
  - **Code:** —
  - **Mechanism:** Survey of multimodal jailbreak attacks and defenses.
  - **Result:** Provides taxonomy and literature mapping for multimodal jailbreak field.
  - **Status:** Unverified

## A4. Real-world incident disclosures

- **EchoLeak: The First Real-World Zero-Click Prompt Injection Exploit in a Production LLM System** — Reddy (arXiv 2025; AAAI Fall Symposium 2025).
  - **Source:** https://arxiv.org/abs/2509.10540
  - **Code:** —
  - **Mechanism:** Academic write-up of the EchoLeak zero-click PI exploit in production LLMs.
  - **Result:** First peer-reviewed analysis of a real-world zero-click PI exploit.
  - **Status:** Verified

- **EchoLeak (Varonis)** — Varonis (2025).
  - **Source:** https://www.varonis.com/blog/echoleak
  - **Code:** —
  - **Mechanism:** Industry analysis of the EchoLeak vulnerability in Microsoft Copilot.
  - **Result:** Vendor-side analysis of the EchoLeak disclosure.
  - **Status:** (vendor blog)

- **EchoLeak (HackTheBox)** — HackTheBox (2025).
  - **Source:** https://www.hackthebox.com/blog/cve-2025-32711-echoleak-copilot-vulnerability
  - **Code:** —
  - **Mechanism:** Technical writeup of CVE-2025-32711 EchoLeak vulnerability.
  - **Result:** Reverse-engineered disclosure of the EchoLeak exploit chain.
  - **Status:** (vendor blog)

- **Bing Chat Initial Prompt Leak (AIID 473)** — AI Incident Database (2023).
  - **Source:** https://incidentdatabase.ai/cite/473/
  - **Code:** —
  - **Mechanism:** AIID incident report for Bing Chat system-prompt leak via prompt injection.
  - **Result:** Catalogued real-world prompt-injection incident in production deployment.
  - **Status:** Unverified

- **Microsoft Crescendo Mitigation Disclosure** — Russinovich (Microsoft 2024).
  - **Source:** https://www.microsoft.com/en-us/security/blog/2024/04/11/how-microsoft-discovers-and-mitigates-evolving-attacks-against-ai-guardrails/
  - **Code:** —
  - **Mechanism:** Microsoft's disclosure of the Crescendo and related multi-turn attack patterns.
  - **Result:** Industry disclosure of evolving guardrail-bypass attack patterns.
  - **Status:** (vendor blog)

- **250-Doc Poisoning Coverage** — Dell (Dark Reading 2025).
  - **Source:** https://www.darkreading.com/application-security/only-250-documents-poison-any-ai-model
  - **Code:** —
  - **Mechanism:** Industry-press coverage of Anthropic's small-sample poisoning result.
  - **Result:** Public press coverage of the 250-doc poisoning finding.
  - **Status:** (vendor blog)

- **HiddenLayer AWS GenAI Integration** — HiddenLayer (2024).
  - **Source:** https://www.hiddenlayer.com/news/hiddenlayer-announces-aws-genai-integrations
  - **Code:** —
  - **Mechanism:** Vendor disclosure of AWS-integrated GenAI security tooling.
  - **Result:** Tracks vendor integration with cloud GenAI providers.
  - **Status:** (vendor blog)

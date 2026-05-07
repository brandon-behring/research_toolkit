# Tools and vendors — open-source toolkits, commercial vendors, eval SaaS

This file collects primary sources on open-source tools, commercial vendors, eval-SaaS platforms, and red-team toolkit repos relevant to prompt-injection security. Per `templates/dossier_table.template.md` § "Non-paper variants", entries here use a non-paper schema (column 2 = "Maintainer / vendor") because they are tools and platforms rather than papers.

## A1. Open-source toolkits and red-team frameworks

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| rebuff: LLM Prompt Injection Detector | Protect AI (2024) | GitHub repo | (no arXiv) | protectai/rebuff | Open-source prompt-injection detection framework. | Self-hostable PI detector with multi-strategy detection chain. |
| llm-guard: The Security Toolkit for LLM Interactions | Protect AI (2024) | GitHub repo | (no arXiv) | protectai/llm-guard | Open security toolkit for LLM I/O scanning. | Comprehensive open scanner suite for LLM applications. |
| NeMo Guardrails: an open-source toolkit for adding programmable guardrails to LLM-based conversational systems | NVIDIA (2024) | GitHub repo | (no arXiv) | NVIDIA-NeMo/Guardrails | NVIDIA's programmable-guardrails toolkit for LLM apps. | Programmable rails framework with Colang DSL. |
| NeMo Guardrails: A Toolkit for Controllable and Safe LLM Applications with Programmable Rails | Rebedea et al. (2023) | arXiv preprint | arXiv:2310.10501 | — | Academic paper documenting the NeMo Guardrails design. | Architectural paper for NeMo Guardrails toolkit. |
| garak: the LLM vulnerability scanner | NVIDIA (2024) | GitHub repo | (no arXiv) | NVIDIA/garak | LLM-native vulnerability scanner across attack probes. | Probe-driven vuln scanner for LLM endpoints. |
| PyRIT: The Python Risk Identification Tool for generative AI | Microsoft (2024) | GitHub repo | (no arXiv) | microsoft/PyRIT | Microsoft's Python risk-identification toolkit for generative AI. | Microsoft's open red-team automation framework. |
| BIPIA: A benchmark for evaluating the robustness of LLMs and defenses to indirect prompt injection attacks | Microsoft (2023) | GitHub repo | (no arXiv) | microsoft/BIPIA | Microsoft's open benchmark repo for indirect-PI evaluation. | Code release for the BIPIA indirect-PI benchmark. |
| browser-art: Browser Agent Red teaming Toolkit | Scale AI (2024) | GitHub repo | (no arXiv) | scaleapi/browser-art | Browser-agent red-team toolkit accompanying BrowserART paper. | Reference toolkit for browser-agent jailbreak evaluation. |
| llm-attacks: Universal and Transferable Attacks on Aligned Language Models | Zou et al. (2023) | GitHub repo | (no arXiv) | llm-attacks/llm-attacks | Reference implementation of the GCG attack. | Canonical GCG attack codebase. |
| HouYi: The automated prompt injection framework for LLM-integrated applications | LLMSecurity (2023) | GitHub repo | (no arXiv) | LLMSecurity/HouYi | Automated PI framework targeting LLM-integrated apps. | Reference codebase for the HouYi PI framework. |
| ArtPrompt: Official Repo of Paper ArtPrompt | UW NSL (2024) | GitHub repo | (no arXiv) | uw-nsl/ArtPrompt | Reference implementation of the ArtPrompt ASCII-art jailbreak. | Reference codebase for ArtPrompt attack. |
| JailbreakBench: An Open Robustness Benchmark for Jailbreaking Language Models | JailbreakBench (2024) | GitHub repo | (no arXiv) | JailbreakBench/jailbreakbench | Reference repo for the JailbreakBench benchmark. | Code + leaderboard for JailbreakBench evaluation. |
| Red Teaming Language Models with Language Models | Perez et al. (2022) | arXiv preprint | arXiv:2202.03286 | — | DeepMind's red-team-with-LMs paper introducing automated red-teaming. | Foundational paper for LM-driven red-teaming. |
| Automated Red Teaming with GOAT: the Generative Offensive Agent Tester | Pavlova et al. (2024) | arXiv preprint | arXiv:2410.01606 | — | Generative offensive agent tester for automated red-teaming. | Agent-driven red-team automation. |
| PurpleLlama: Set of tools to assess and improve LLM security | Meta (2024) | GitHub repo | (no arXiv) | meta-llama/PurpleLlama | Meta's umbrella project for LLM security tools (CyberSec eval, PromptGuard, LlamaGuard). | Meta's bundled security tooling stack for Llama-family models. |
| Announcing the Adaptive Prompt Injection Challenge LLMail-Inject | Microsoft (2024) | Microsoft Security blog | (no arXiv) | — | Microsoft's announcement of the LLMail-Inject adaptive PI challenge. | Industry-run adaptive PI challenge with public participation. |

## A2. Commercial vendors and platforms

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| Lakera Guard: AI Agent Security: Runtime visibility and protection for AI applications and agents | Lakera (2024) | Vendor product page | (no arXiv) | — | Lakera's runtime AI-agent security product. | Commercial PI/jailbreak detection-and-blocking SaaS. |
| HiddenLayer: Total AI Security | HiddenLayer (2024) | Vendor product page | (no arXiv) | — | HiddenLayer's AI security platform homepage. | Commercial AI-security platform. |
| Robust Intelligence Is Now Part of Cisco | Cisco (2024) | Cisco product page | (no arXiv) | — | Vendor disclosure of the Cisco / Robust Intelligence acquisition. | Tracks Robust Intelligence's acquisition by Cisco. |
| LLM Guard: Secure Your LLM Applications | Protect AI (2024) | Vendor product page | (no arXiv) | — | Protect AI's commercial LLM Guard product page. | Commercial LLM-application security product. |
| Patronus AI: Simulating the World's Intelligence | Patronus AI (2024) | Vendor product page | (no arXiv) | — | Patronus AI eval-SaaS platform homepage. | Commercial LLM evaluation SaaS with PI/safety tests. |
| Galileo AI: The AI Observability and Evaluation Platform | Galileo (2024) | Vendor product page | (no arXiv) | — | Galileo's AI observability and eval platform. | Commercial LLM observability/evaluation SaaS. |
| Arize: LLM Observability and Evaluation Platform | Arize (2024) | Vendor product page | (no arXiv) | — | Arize's LLM observability and eval platform. | Commercial LLM observability/evaluation SaaS. |
| Gray Swan Cygnet: Secure LLM | Gray Swan (2024) | Vendor product page | (no arXiv) | — | Gray Swan Cygnet secure LLM product. | Commercial secure-LLM offering with red-team-trained robustness. |

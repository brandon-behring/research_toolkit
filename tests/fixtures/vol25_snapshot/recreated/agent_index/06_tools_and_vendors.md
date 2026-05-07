# 06 — Tools and vendors (open-source toolkits, commercial vendors, eval SaaS)

**Scope:** open-source tools, commercial vendors, eval-SaaS platforms, and red-team toolkit repos relevant to prompt-injection security. Vendor entries use a non-paper bullet schema (Source / Status / Product line / Mechanism / Integration).
**Out of scope:** datasets and benchmarks (see `05_datasets_and_benchmarks.md`); academic papers underlying the tools (see `01_direct_attacks.md`, `02_indirect_and_agentic_attacks.md`, `03_defenses.md`).

## A1. Open-source toolkits and red-team frameworks

- **rebuff** — Protect AI (GitHub 2024).
  - **Source:** https://github.com/protectai/rebuff
  - **Status:** Open-source, actively maintained
  - **Product line:** Self-hostable PI detection framework
  - **Mechanism:** Multi-strategy PI detection chain combining heuristics + classifier + canary tokens.
  - **Integration:** Drop-in middleware for LLM applications.

- **llm-guard** — Protect AI (GitHub 2024).
  - **Source:** https://github.com/protectai/llm-guard
  - **Status:** Open-source, actively maintained
  - **Product line:** Open security toolkit for LLM I/O scanning
  - **Mechanism:** Catalog of input/output scanners (PII, toxicity, jailbreak, secrets, etc.).
  - **Integration:** Standalone library + reference deployments.

- **NeMo Guardrails** — NVIDIA (GitHub 2024).
  - **Source:** https://github.com/NVIDIA-NeMo/Guardrails
  - **Status:** Open-source, actively maintained
  - **Product line:** Programmable rails framework
  - **Mechanism:** Colang DSL describing input/output/dialog/retrieval rails for conversational LLMs.
  - **Integration:** Wrapper around LLM provider APIs with configurable rail layer.

- **NeMo Guardrails (paper)** — Rebedea et al. (arXiv 2023).
  - **Source:** https://arxiv.org/abs/2310.10501
  - **Code:** https://github.com/NVIDIA-NeMo/Guardrails
  - **Mechanism:** Academic paper documenting the NeMo Guardrails design.
  - **Result:** Architectural paper for the NeMo Guardrails toolkit.
  - **Status:** Unverified

- **garak** — NVIDIA (GitHub 2024).
  - **Source:** https://github.com/NVIDIA/garak
  - **Status:** Open-source, actively maintained
  - **Product line:** LLM vulnerability scanner
  - **Mechanism:** Probe-driven scanner with attack-class plugins (DAN, encoding, RCE, etc.).
  - **Integration:** CLI scanner against any HTTP-API or library-loaded LLM.

- **PyRIT** — Microsoft (GitHub 2024).
  - **Source:** https://github.com/microsoft/PyRIT
  - **Status:** Open-source, actively maintained
  - **Product line:** Python Risk Identification Tool for generative AI
  - **Mechanism:** Red-team automation framework with attack orchestrators and scorers.
  - **Integration:** Python library; integrates with Azure OpenAI and other providers.

- **BIPIA repo** — Microsoft (GitHub 2023).
  - **Source:** https://github.com/microsoft/BIPIA
  - **Status:** Reference benchmark repo
  - **Product line:** Indirect-PI benchmark
  - **Mechanism:** Benchmark + baseline-defense scripts for evaluating indirect-PI robustness.
  - **Integration:** Standalone eval scripts.

- **browser-art repo** — Scale AI (GitHub 2024).
  - **Source:** https://github.com/scaleapi/browser-art
  - **Status:** Reference toolkit accompanying BrowserART paper
  - **Product line:** Browser-agent red-teaming toolkit
  - **Mechanism:** Accompanies Kumar et al. 2024 BrowserART paper.
  - **Integration:** Browser-agent harness for adversarial evaluation.

- **llm-attacks (GCG repo)** — Zou et al. (GitHub 2023).
  - **Source:** https://github.com/llm-attacks/llm-attacks
  - **Status:** Reference implementation
  - **Product line:** GCG attack
  - **Mechanism:** Reference implementation of the GCG white-box attack.
  - **Integration:** Standalone attack codebase.

- **HouYi repo** — LLMSecurity (GitHub 2023).
  - **Source:** https://github.com/LLMSecurity/HouYi
  - **Status:** Reference codebase
  - **Product line:** PI framework for LLM-integrated apps
  - **Mechanism:** Automated PI framework targeting deployed LLM applications.
  - **Integration:** Standalone attack framework.

- **ArtPrompt repo** — UW NSL (GitHub 2024).
  - **Source:** https://github.com/uw-nsl/ArtPrompt
  - **Status:** Reference implementation
  - **Product line:** ASCII-art jailbreak attack
  - **Mechanism:** Reference implementation of the ArtPrompt attack.
  - **Integration:** Standalone attack codebase.

- **JailbreakBench repo** — JailbreakBench (GitHub 2024).
  - **Source:** https://github.com/JailbreakBench/jailbreakbench
  - **Status:** Reference implementation + leaderboard
  - **Product line:** Jailbreak benchmark
  - **Mechanism:** Code + leaderboard for the JailbreakBench benchmark.
  - **Integration:** Standalone eval framework.

- **Red Teaming with LMs (Perez 2022)** — Perez et al. (arXiv 2022).
  - **Source:** https://arxiv.org/abs/2202.03286
  - **Code:** —
  - **Mechanism:** DeepMind's red-team-with-LMs paper introducing automated red-teaming.
  - **Result:** Foundational paper for LM-driven red-teaming.
  - **Status:** Unverified

- **GOAT (Generative Offensive Agent Tester)** — Pavlova et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2410.01606
  - **Code:** —
  - **Mechanism:** Generative offensive agent tester for automated red-teaming.
  - **Result:** Agent-driven red-team automation framework.
  - **Status:** Unverified

- **PurpleLlama** — Meta (GitHub 2024).
  - **Source:** https://github.com/meta-llama/PurpleLlama
  - **Status:** Open-source, actively maintained
  - **Product line:** Umbrella project (CyberSec eval, PromptGuard, LlamaGuard)
  - **Mechanism:** Bundled security tooling stack for Llama-family models.
  - **Integration:** Reference deployments alongside Meta's open Llama releases.

- **LLMail-Inject Challenge** — Microsoft (Microsoft Security blog 2024).
  - **Source:** https://www.microsoft.com/en-us/msrc/blog/2024/12/announcing-the-adaptive-prompt-injection-challenge-llmail-inject
  - **Status:** Public adaptive PI challenge
  - **Product line:** Email PI challenge
  - **Mechanism:** Industry-run adaptive PI challenge with public participation.
  - **Integration:** Public-event adversarial-robustness program.

## A2. Commercial vendors and platforms

- **Lakera Guard** — Lakera (vendor 2024).
  - **Source:** https://www.lakera.ai/lakera-guard
  - **Status:** Commercial SaaS (vendor blog)
  - **Product line:** AI-agent runtime security
  - **Mechanism:** Detect-and-block PI/jailbreak/data-leak at runtime for LLM applications.
  - **Integration:** API-based middleware for LLM-integrated apps.

- **HiddenLayer** — HiddenLayer (vendor 2024).
  - **Source:** https://www.hiddenlayer.com/
  - **Status:** Commercial AI-security platform (vendor blog)
  - **Product line:** Model-level + runtime AI security
  - **Mechanism:** Model fingerprinting, runtime monitoring, and adversarial-input detection.
  - **Integration:** Integrates with cloud GenAI providers (AWS, etc.).

- **Robust Intelligence (now part of Cisco)** — Cisco (vendor 2024).
  - **Source:** https://www.cisco.com/site/us/en/products/security/ai-defense/robust-intelligence-is-part-of-cisco/index.html
  - **Status:** Acquired by Cisco; integrated into Cisco AI Defense (vendor blog)
  - **Product line:** AI security platform
  - **Mechanism:** AI risk-management platform combining model testing and runtime defense.
  - **Integration:** Cisco AI Defense product line.

- **Protect AI LLM Guard** — Protect AI (vendor 2024).
  - **Source:** https://protectai.com/llm-guard
  - **Status:** Commercial product (vendor blog)
  - **Product line:** LLM application security
  - **Mechanism:** Commercial LLM-application security with PI/data-leak/jailbreak detection.
  - **Integration:** Companion to the open-source llm-guard library.

- **Patronus AI** — Patronus AI (vendor 2024).
  - **Source:** https://www.patronus.ai/
  - **Status:** Commercial eval-SaaS (vendor blog)
  - **Product line:** LLM evaluation platform
  - **Mechanism:** Commercial LLM evaluation SaaS with PI/safety test suites.
  - **Integration:** API + dashboard for LLM regression testing.

- **Galileo AI** — Galileo (vendor 2024).
  - **Source:** https://galileo.ai/
  - **Status:** Commercial eval-SaaS (vendor blog)
  - **Product line:** AI observability and evaluation
  - **Mechanism:** Commercial LLM observability/evaluation SaaS.
  - **Integration:** API + dashboard for production LLM monitoring.

- **Arize** — Arize (vendor 2024).
  - **Source:** https://arize.com/
  - **Status:** Commercial eval-SaaS (vendor blog)
  - **Product line:** LLM observability + evaluation
  - **Mechanism:** Commercial LLM observability/evaluation SaaS.
  - **Integration:** API + dashboard for production LLM monitoring.

- **Gray Swan Cygnet** — Gray Swan (vendor 2024).
  - **Source:** https://www.grayswan.ai/product/cygnet
  - **Status:** Commercial secure-LLM offering (vendor blog)
  - **Product line:** Secure LLM
  - **Mechanism:** LLM trained with extensive red-teaming for adversarial robustness.
  - **Integration:** API-accessible secure LLM as drop-in for application backends.

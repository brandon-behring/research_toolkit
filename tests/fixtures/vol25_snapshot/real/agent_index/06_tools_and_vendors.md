# Tools and Vendors — OSS, Commercial, Eval SaaS

<!-- AGENT-INDEX: keep this block stable; future agents read it first. -->
**Scope:** OSS tools, commercial vendors, and eval SaaS platforms for LLM security: red-team probe runners, runtime guards, classifiers (open weights), eval harnesses, research/academic attack implementations, observability, plus the commercial-vendor and SaaS-platform landscape.
**Out of scope:** Standards / regulations — see `07_standards_and_industry.md`. Datasets / benchmarks — see `05_datasets_and_benchmarks.md`. Research papers — see `01_direct_attacks.md` through `04_training_time_threats.md`.
**Coverage window:** 2022–2026 (with status as of May 2026).
**Last updated:** 2026-05-06.
**Subsections (stable anchors):** OSS-RT-runners · OSS-defense-guards · OSS-classifiers · OSS-eval-harnesses · OSS-attack-impls · OSS-observability · Commercial-vendors · Eval-SaaS · Tool-selection-by-deployment-shape · Status flags.
**Key terms covered:** garak, PyRIT, promptfoo, Giskard, DeepTeam, DeepEval, EasyJailbreak, LLAMATOR, Open-Prompt-Injection, Agentic Radar, OpenAnt, LLM Guard, NeMo Guardrails, Guardrails AI, Rebuff, LlamaFirewall (PurpleLlama), PromptInject, Llama Guard 3/4, Prompt Guard 2, ShieldGemma 2, WildGuard, Aegis, Granite Guardian, lm-evaluation-harness, Inspect AI, Inspect Evals, HELM, AIR-Bench, HarmBench, JailbreakBench, AgentDojo, nanoGCG, llm-attacks, BrokenHill, AutoDAN-Turbo, AutoDAN, PAIR, TAP, GPTFuzz, Phoenix, Opik, Helicone, LangKit, Lakera (Check Point), Protect AI (Palo Alto Networks), HiddenLayer, Robust Intelligence (Cisco AI Defense), CalypsoAI (F5), Patronus AI, Pillar Security, WhyLabs, MS Prompt Shields, Google ShieldGemma + Cloud, AWS Bedrock Guardrails, IBM Granite Guardian, Fiddler AI, Galileo (Cisco), Arize AI, TrojAI, ActiveFence (Alice), Zenity, Knostic, Aim Security (Cato), Mindgard, Lasso Security, Prompt Security, SPLX (Zscaler), Repello AI, Vijil, AppSOC, PromptArmor, F5 AI Guardrails, Cisco AI Defense, Snowflake Cortex Guard, LangSmith, Patronus Platform, Galileo Evaluate, Arize Phoenix Cloud, Helicone Cloud, Confident AI, Braintrust, Comet Opik Cloud, Maxim AI, Fiddler Trust Service.
**Related files:** `03_defenses.md` (the research papers behind many tools), `07_standards_and_industry.md` (compliance context for vendor selection).

## Topic overview

The LLM-security tooling landscape splits into three layers: open-source projects (red-team runners, runtime guards, classifiers, eval harnesses, attack implementations, observability), commercial vendors (the consolidated vendor landscape after the 2024–2025 acquisition wave), and eval SaaS platforms (LangSmith, Patronus, Galileo, Braintrust, Maxim).

The 2024–2025 vendor consolidation is the dominant fact. Six major acquisitions have collapsed the standalone-vendor landscape: **Lakera → Check Point** (Sep 2025), **Protect AI → Palo Alto Networks** (Apr-Jul 2025, ~$500M+ → Prisma AIRS), **Robust Intelligence → Cisco** (Aug-Oct 2024, ~$400M → Cisco AI Defense), **CalypsoAI → F5** (2025 → F5 AI Guardrails), **Aim Security → Cato Networks** (Sep 2025, ~$350M), **SPLX → Zscaler** (2025), with Galileo→Cisco intent announced for FY26 Q4. Agents/humans evaluating vendors should treat post-acquisition product lines (Prisma AIRS, Cisco AI Defense, F5 AI Guardrails) as the canonical names.

The deployment-shape recipes section below maps four common scenarios — startup with no security budget, pre-IPO with compliance pressure, research lab with adaptive-attack methodology needs, regulated finance/healthcare production — to specific tool stacks. The status-flags section at the end calls out deprecated, archived, acquired, and license-cautioned entries.

## OSS — Red-team / Probe Runners

`#oss-rt-runners`

Open-source frameworks for adversarial probing — input fuzzing, automated jailbreak generation, multi-turn red-team loops.

### Entries

- **garak** — NVIDIA, *Apache-2.0*.
  - **Source:** https://arxiv.org/abs/2406.11036
  - **Code:** https://github.com/NVIDIA/garak
  - **Mechanism:** LLM vulnerability scanner with 15+ probe categories; `pip install garak`.
  - **Result:** Most-popular OSS LLM red-team scanner; v0.15.0 May 2026; 7.7k stars.
  - **Status:** Verified.

- **PyRIT** — Microsoft (moved from Azure org), *MIT*.
  - **Source:** https://github.com/microsoft/PyRIT
  - **Code:** https://github.com/microsoft/PyRIT
  - **Mechanism:** Multi-turn risk-identification framework with attacker / scorer loop; `pip install pyrit`.
  - **Result:** Microsoft's flagship red-team automation framework; v0.13.0 Apr 2026; 3.8k stars.
  - **Status:** Verified.

- **promptfoo** — Promptfoo (acquired by OpenAI Mar 2026; remains MIT), *MIT*.
  - **Source:** https://github.com/promptfoo/promptfoo
  - **Code:** https://github.com/promptfoo/promptfoo
  - **Mechanism:** Eval + redteam CLI with 50+ vulnerability plugins; `npx promptfoo@latest`.
  - **Result:** Most-popular OSS eval/redteam CLI; v0.121.9 Apr 2026; 20.9k stars; remains MIT post-OpenAI acquisition.
  - **Status:** Verified — acquired Mar 2026, OSS license preserved.

- **Giskard OSS (v3)** — Giskard, *Apache-2.0*.
  - **Source:** https://github.com/Giskard-AI/giskard-oss
  - **Code:** https://github.com/Giskard-AI/giskard-oss
  - **Mechanism:** LLM agent eval / red-team library; `pip install giskard-checks`.
  - **Result:** Active 2026 (v2 LLM scan unmaintained); 5.3k stars.
  - **Status:** Verified.

- **DeepTeam** — Confident AI, *Apache-2.0*.
  - **Source:** https://github.com/confident-ai/deepteam
  - **Code:** https://github.com/confident-ai/deepteam
  - **Mechanism:** 50+ vulns, 20+ attacks (OWASP_ASI_2026 + MITRE-aligned); `pip install deepteam`.
  - **Result:** v1.0.4 Nov 2025; 1.6k stars.
  - **Status:** Verified.

- **DeepEval** — Confident AI, *Apache-2.0*.
  - **Source:** https://github.com/confident-ai/deepeval
  - **Code:** https://github.com/confident-ai/deepeval
  - **Mechanism:** LLM eval framework with 30+ metrics including safety; `pip install deepeval`.
  - **Result:** v3.9.9 Dec 2025; 15.2k stars.
  - **Status:** Verified.

- **EasyJailbreak** — EasyJailbreak, *GPL-3.0*.
  - **Source:** https://arxiv.org/abs/2403.12171
  - **Code:** https://github.com/EasyJailbreak/EasyJailbreak
  - **Mechanism:** Unified framework for 12+ jailbreaks (PAIR / GCG / AutoDAN / GPTFuzz). `git clone + pip -e .`.
  - **Result:** v0.1.3 Aug 2024; 848 stars.
  - **Status:** Verified — GPL-3.0 license caution: incompatible with proprietary closed-source distribution.

- **LLAMATOR** — LLAMATOR-Core, *CC BY-NC-SA 4.0 (non-commercial)*.
  - **Source:** https://github.com/LLAMATOR-Core/llamator
  - **Code:** https://github.com/LLAMATOR-Core/llamator
  - **Mechanism:** Red-team framework with attacker / judge / target roles; `pip install llamator`.
  - **Result:** v3.5.0 Jan 2026; 208 stars.
  - **Status:** Verified — CC BY-NC-SA 4.0 license caution: do NOT embed in commercial products without legal consultation.

- **Open-Prompt-Injection** — Liu et al. (USENIX 2024), *MIT*.
  - **Source:** https://arxiv.org/abs/2310.12815
  - **Code:** https://github.com/liu00222/Open-Prompt-Injection
  - **Mechanism:** 5 attacks × 10 defenses × 10 LLMs benchmark.
  - **Result:** Research-quality reference; 436 stars.
  - **Status:** Verified.

- **Agentic Radar** — SPLX (Zscaler), *Apache-2.0*.
  - **Source:** https://github.com/splx-ai/agentic-radar
  - **Code:** https://github.com/splx-ai/agentic-radar
  - **Mechanism:** Workflow scanner for agentic AI (CrewAI, LangGraph, n8n, MCP); `pip install agentic-radar`.
  - **Result:** v0.14.1 Nov 2025; 963 stars.
  - **Status:** Verified.

- **OpenAnt** — Knostic, *Apache-2.0*.
  - **Source:** https://github.com/knostic/OpenAnt
  - **Code:** https://github.com/knostic/OpenAnt
  - **Mechanism:** LLM-based vuln discovery (detect → attack-verify); `git clone + run`.
  - **Result:** Active 2026; 511 stars.
  - **Status:** Verified.

## OSS — Defense / Runtime Guard

`#oss-defense-guards`

Open-source runtime defenses — wrap or precede LLM calls to filter inputs and outputs.

### Entries

- **LLM Guard** — Protect AI (Palo Alto Networks since Jul 2025), *MIT*.
  - **Source:** https://llm-guard.com/
  - **Code:** https://github.com/protectai/llm-guard
  - **Mechanism:** 15 input scanners + 20 output scanners; `pip install llm-guard`.
  - **Result:** v0.3.16 active 2026; 2.9k stars; Protect AI's flagship after Rebuff archival.
  - **Status:** Verified.

- **NeMo Guardrails** — NVIDIA-NeMo, *Apache-2.0*.
  - **Source:** https://arxiv.org/abs/2310.10501
  - **Code:** https://github.com/NVIDIA-NeMo/Guardrails
  - **Mechanism:** Programmable Colang dialog rails; YARA scanner; `pip install nemoguardrails`.
  - **Result:** v0.21.0 Mar 2026; 6.1k stars.
  - **Status:** Verified.

- **Guardrails AI** — Guardrails AI, *Apache-2.0*.
  - **Source:** https://www.guardrailsai.com/
  - **Code:** https://github.com/guardrails-ai/guardrails
  - **Mechanism:** Validator hub; structured output + safety guards; `pip install guardrails-ai`.
  - **Result:** v0.10.0 Apr 2026; 6.8k stars.
  - **Status:** Verified.

- **Rebuff** — Protect AI, *Apache-2.0*.
  - **Source:** https://github.com/protectai/rebuff
  - **Code:** https://github.com/protectai/rebuff
  - **Mechanism:** Heuristic + LLM check + vector DB + canary tokens.
  - **Result:** **ARCHIVED May 16, 2025**; reference only.
  - **Status:** Verified — archived.

- **LlamaFirewall (PurpleLlama)** — Meta, *MIT (code) + Llama license (weights)*.
  - **Source:** https://arxiv.org/abs/2505.03574
  - **Code:** https://github.com/meta-llama/PurpleLlama
  - **Mechanism:** Multi-scanner runtime: PromptGuard + AlignmentCheck + CodeShield; `pip install llamafirewall`.
  - **Result:** Active 2026; 4.2k stars.
  - **Status:** Verified. → Also see `03_defenses.md` § C1.

- **PromptInject** — Agency Enterprise (NeurIPS Best Paper 2022), *MIT*.
  - **Source:** https://arxiv.org/abs/2211.09527
  - **Code:** https://github.com/agencyenterprise/PromptInject
  - **Mechanism:** Original goal-hijacking + prompt-leaking framework; `pip install promptinject`.
  - **Result:** Maintenance mode; 488 stars; reference implementation for the foundational PI taxonomy.
  - **Status:** Verified.

## OSS — Classifiers (open weights or training code)

`#oss-classifiers`

Open-weights safety classifiers — Meta Llama Guard family, Google ShieldGemma, AI2 WildGuard, NVIDIA Aegis, IBM Granite Guardian.

### Entries

- **Llama Guard 4 (12B multimodal)** — Meta.
  - **Source:** https://huggingface.co/meta-llama/Llama-Guard-4-12B
  - **Code:** https://huggingface.co/meta-llama/Llama-Guard-4-12B
  - **Mechanism:** Native multimodal early-fusion 12B safeguard for text + image.
  - **Result:** Most recent Llama Guard; multimodal-first design.
  - **Status:** Verified — Llama 4 Community license. → Also see `03_defenses.md` § C1.

- **Llama Guard 3 (1B / 8B / 11B-vision)** — Meta.
  - **Source:** https://arxiv.org/abs/2407.21783
  - **Code:** https://huggingface.co/meta-llama/Llama-Guard-3-8B
  - **Mechanism:** Multilingual text safety classifier with vision-enabled variant.
  - **Result:** Most-cited 2024 open-weight safety classifier.
  - **Status:** Verified — Llama 3 license.

- **Llama Prompt Guard 2 (22M / 86M)** — Meta.
  - **Source:** https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M
  - **Code:** https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M
  - **Mechanism:** Lightweight injection + jailbreak detector; mDeBERTa-base.
  - **Result:** Cheap (22M / 86M) detector for high-volume input filtering.
  - **Status:** Verified — Llama license.

- **ShieldGemma 2 (4B multimodal)** — Google DeepMind.
  - **Source:** https://arxiv.org/abs/2504.01081
  - **Code:** https://huggingface.co/google/shieldgemma-2-4b-it
  - **Mechanism:** Text + image safety scoring; 4B parameters.
  - **Result:** Google's multimodal-first safety classifier.
  - **Status:** Verified — Gemma license.

- **WildGuard (7B)** — Allen AI.
  - **Source:** https://arxiv.org/abs/2406.18495
  - **Code:** https://huggingface.co/allenai/wildguard
  - **Mechanism:** Prompt + response harm + refusal evaluation; matches GPT-4 on multi-task moderation.
  - **Result:** Strongest open Apache-2.0-licensed safety classifier.
  - **Status:** Verified — Apache-2.0.

- **Aegis Llama-Guard (Defensive / Permissive)** — NVIDIA.
  - **Source:** https://arxiv.org/abs/2404.05993
  - **Code:** https://huggingface.co/nvidia/Aegis-AI-Content-Safety-LlamaGuard-Defensive-1.0
  - **Mechanism:** LlamaGuard-fine-tuned permissive and defensive variants; 13-category content safety.
  - **Result:** NVIDIA's contribution to the open-classifier ecosystem.
  - **Status:** Verified — Llama 2 license.

- **Granite Guardian 3.3 / 4.1** — IBM.
  - **Source:** https://github.com/ibm-granite/granite-guardian
  - **Code:** https://github.com/ibm-granite/granite-guardian
  - **Mechanism:** BYO-criteria judge: jailbreak + hallucination + RAG groundedness.
  - **Result:** v4.1 Apr 2026; enterprise-grade Apache-2.0 classifier.
  - **Status:** Verified — Apache-2.0.

- **Granite Guardian HAP-38M / 125M** — IBM.
  - **Source:** https://huggingface.co/ibm-granite/granite-guardian-hap-125m
  - **Code:** https://huggingface.co/ibm-granite/granite-guardian-hap-125m
  - **Mechanism:** Lightweight English toxicity classifier.
  - **Result:** Sub-200M classifier for high-volume deployments.
  - **Status:** Verified — Apache-2.0.

## OSS — Eval Harnesses

`#oss-eval-harnesses`

OSS evaluation frameworks for benchmarking LLMs (including safety subsets).

### Entries

- **lm-evaluation-harness** — EleutherAI, *MIT*.
  - **Source:** https://github.com/EleutherAI/lm-evaluation-harness
  - **Code:** https://github.com/EleutherAI/lm-evaluation-harness
  - **Mechanism:** 60+ benchmarks; safety subsets included; `pip install lm-eval`.
  - **Result:** v0.4.11 Feb 2026; 12.4k stars; reference eval harness for LLM benchmarks.
  - **Status:** Verified.

- **Inspect AI** — UK AISI, *MIT*.
  - **Source:** https://github.com/UKGovernmentBEIS/inspect_ai
  - **Code:** https://github.com/UKGovernmentBEIS/inspect_ai
  - **Mechanism:** Government-grade eval framework; `pip install inspect-ai`.
  - **Result:** Active Apr 2026; 2.0k stars; UK AISI's flagship eval framework.
  - **Status:** Verified.

- **Inspect Evals** — UK AISI / Vector / Arcadia, *MIT*.
  - **Source:** https://github.com/UKGovernmentBEIS/inspect_evals
  - **Code:** https://github.com/UKGovernmentBEIS/inspect_evals
  - **Mechanism:** 200+ community evals including AgentDojo, HarmBench; `pip install inspect-evals`.
  - **Result:** Active; community-curated companion to Inspect AI.
  - **Status:** Verified.

- **HELM** — Stanford CRFM, *Apache-2.0*.
  - **Source:** https://github.com/stanford-crfm/helm
  - **Code:** https://github.com/stanford-crfm/helm
  - **Mechanism:** Holistic eval; AIR-Bench safety subset; `pip install crfm-helm`.
  - **Result:** v0.5.16 Apr 2026; 2.8k stars; **entering maintenance June 2026**.
  - **Status:** Verified — entering maintenance.

- **AIR-Bench 2024** — Stanford CRFM, *Apache-2.0*.
  - **Source:** https://github.com/stanford-crfm/air-bench-2024
  - **Code:** https://github.com/stanford-crfm/air-bench-2024
  - **Mechanism:** Regulation-aligned safety benchmark; `pip install air-bench`.
  - **Result:** Reference regulation-aligned safety benchmark from Stanford CRFM.
  - **Status:** Verified.

## OSS — Research / Academic Attack Implementations

`#oss-attack-impls`

OSS implementations of canonical attack methods. Used both for research reproduction and for adaptive-attack evaluation of defenses.

### Entries

- **HarmBench** — CAIS, *MIT*.
  - **Source:** https://arxiv.org/abs/2402.04249
  - **Code:** https://github.com/centerforaisafety/HarmBench
  - **Mechanism:** 18 attack methods × 33 LLMs; standardized red-team eval.
  - **Result:** v1.0 Feb 2024; 939 stars; reference benchmark for the adaptive-attack era.
  - **Status:** Verified. → Also see `03_defenses.md` § C5, C6 and `05_datasets_and_benchmarks.md` § Datasets-A.

- **JailbreakBench** — JailbreakBench, *MIT*.
  - **Source:** https://arxiv.org/abs/2404.01318
  - **Code:** https://github.com/JailbreakBench/jailbreakbench
  - **Mechanism:** JBB-Behaviors + leaderboard + judge.
  - **Result:** Active artifact updates; 586 stars.
  - **Status:** Verified. → Also see `03_defenses.md` § C6 and `05_datasets_and_benchmarks.md` § Datasets-A.

- **AgentDojo** — ETH SPY Lab, *MIT*.
  - **Source:** https://arxiv.org/abs/2406.13352
  - **Code:** https://github.com/ethz-spylab/agentdojo
  - **Mechanism:** Tool-use agent + 629 injection cases.
  - **Result:** v0.1.35 Oct 2025; 550 stars. → Also see `02_indirect_and_agentic_attacks.md` § B2, `03_defenses.md` § C6, `05_datasets_and_benchmarks.md` § Datasets-D.
  - **Status:** Verified.

- **nanoGCG** — Gray Swan AI, *MIT*.
  - **Source:** https://github.com/GraySwanAI/nanoGCG
  - **Code:** https://github.com/GraySwanAI/nanoGCG
  - **Mechanism:** Fast PyTorch GCG implementation; mellowmax + multi-position swap.
  - **Result:** v0.3.0 Feb 2025; 331 stars.
  - **Status:** Verified.

- **llm-attacks (original GCG)** — Zou et al., *MIT*.
  - **Source:** https://arxiv.org/abs/2307.15043
  - **Code:** https://github.com/llm-attacks/llm-attacks
  - **Mechanism:** Original GCG paper code.
  - **Result:** Research-frozen; 4.6k stars; reference implementation.
  - **Status:** Verified.

- **BrokenHill** — Bishop Fox, *MIT*.
  - **Source:** https://github.com/BishopFox/BrokenHill
  - **Code:** https://github.com/BishopFox/BrokenHill
  - **Mechanism:** Productionized GCG runnable on RTX 4090 / Mac.
  - **Result:** Active 2025–26; 160 stars; pentester-oriented GCG packaging.
  - **Status:** Verified.

- **AutoDAN-Turbo** — SaFoLab WISC (ICLR 2025), *MIT*.
  - **Source:** https://arxiv.org/abs/2410.05295
  - **Code:** https://github.com/SaFoLab-WISC/AutoDAN-Turbo
  - **Mechanism:** Lifelong self-exploring black-box jailbreak agent.
  - **Result:** Active; 363 stars.
  - **Status:** Verified.

- **AutoDAN** — Liu et al. (ICLR 2024), *MIT*.
  - **Source:** https://arxiv.org/abs/2310.04451
  - **Code:** https://github.com/SheltonLiu-N/AutoDAN
  - **Mechanism:** Genetic-algorithm stealthy jailbreak.
  - **Result:** Research-frozen; 440 stars.
  - **Status:** Verified.

- **PAIR (JailbreakingLLMs)** — Chao et al., *MIT*.
  - **Source:** https://arxiv.org/abs/2310.08419
  - **Code:** https://github.com/patrickrchao/JailbreakingLLMs
  - **Mechanism:** Black-box semantic jailbreak in <20 queries.
  - **Result:** Research-frozen; 732 stars; foundational black-box jailbreak implementation.
  - **Status:** Verified.

- **TAP** — RICommunity, *MIT*.
  - **Source:** https://arxiv.org/abs/2312.02119
  - **Code:** https://github.com/RICommunity/TAP
  - **Mechanism:** Tree-of-thoughts attacker / eval / target.
  - **Result:** Research-frozen; 230 stars.
  - **Status:** Verified.

- **GPTFuzz** — Yu et al., *MIT*.
  - **Source:** https://arxiv.org/abs/2309.10253
  - **Code:** https://github.com/sherdencooper/GPTFuzz
  - **Mechanism:** Mutation fuzzing of jailbreak templates.
  - **Result:** Maintenance mode; 580 stars.
  - **Status:** Verified.

## OSS — Observability with Safety Hooks

`#oss-observability`

OSS observability platforms with built-in safety / evaluator hooks.

### Entries

- **Phoenix** — Arize AI, *Elastic-2.0*.
  - **Source:** https://github.com/Arize-ai/phoenix
  - **Code:** https://github.com/Arize-ai/phoenix
  - **Mechanism:** OTEL traces + LLM evaluators.
  - **Result:** v15.3.0 May 2026; 9.5k stars.
  - **Status:** Verified — Elastic-2.0 license caution: not OSI-OSS; Arize gates resale.

- **Opik** — Comet, *Apache-2.0*.
  - **Source:** https://github.com/comet-ml/opik
  - **Code:** https://github.com/comet-ml/opik
  - **Mechanism:** Tracing + LLM-judge + production monitoring.
  - **Result:** v2.0.21 May 2026; 19.2k stars.
  - **Status:** Verified.

- **Helicone** — Helicone (Mintlify acquisition Mar 2026), *Apache-2.0*.
  - **Source:** https://github.com/Helicone/helicone
  - **Code:** https://github.com/Helicone/helicone
  - **Mechanism:** AI gateway + Llama-Guard / Prompt-Guard 2 hooks.
  - **Result:** Aug 2025; 5.6k stars; **maintenance mode after Mintlify acquisition**.
  - **Status:** Verified — maintenance mode.

- **LangKit** — WhyLabs, *Apache-2.0*.
  - **Source:** https://github.com/whylabs/langkit
  - **Code:** https://github.com/whylabs/langkit
  - **Mechanism:** Text-metrics extractor.
  - **Result:** Nov 2024 (slow); 984 stars.
  - **Status:** Verified.

## Commercial Vendors

`#commercial-vendors`

The post-2024-2025-acquisition consolidated commercial-vendor landscape. Acquisition status flagged inline; refer to § Status flags for the consolidated view.

### Entries

- **Lakera** — Zurich, CH (founded 2021).
  - **Source:** https://www.lakera.ai/
  - **Status:** $20M Series A; **ACQUIRED by Check Point Sep 16, 2025** (~$300M; deal expected to close Q4 2025).
  - **Product line:** Lakera Guard, Red Team, AI Agent Security.
  - **Mechanism:** Heuristic + classifier + Gandalf-trained models.
  - **Integration:** API gateway, AWS / Azure.

- **Protect AI** — Seattle, WA (founded 2022).
  - **Source:** https://protectai.com/
  - **Status:** **ACQUIRED by Palo Alto Networks Apr-Jul 2025** (~$500M+); now **Prisma AIRS**.
  - **Product line:** Recon (red-team), Layer (firewall), Sightline.
  - **Mechanism:** Model scanning, runtime, MLSecOps.
  - **Integration:** Prisma AIRS / Bedrock / SageMaker.

- **HiddenLayer** — Austin, TX (founded 2022).
  - **Source:** https://hiddenlayer.com/
  - **Status:** $50M+ Series A (2023); SHIELD US government contract.
  - **Product line:** AISec Platform 2.0: Discovery, Supply Chain, Attack Sim, Runtime.
  - **Mechanism:** Behavior + adversarial detection.
  - **Integration:** SaaS / on-prem / airgap.

- **Robust Intelligence** — Cambridge, MA (founded 2019).
  - **Source:** https://www.cisco.com/site/us/en/products/security/ai-defense/
  - **Status:** **ACQUIRED by Cisco Aug-Oct 2024** (~$400M); now **Cisco AI Defense**.
  - **Product line:** AI Firewall, algorithmic red-team.
  - **Mechanism:** Adversarial scan + WAF for AI.
  - **Integration:** Cisco fabric, network-inline.

- **CalypsoAI** — Dublin / NYC (founded 2018).
  - **Source:** https://calypsoai.com/
  - **Status:** **ACQUIRED by F5 Sep 11, 2025** (~$180M; completed by F5 FY Q4 ending Sep 30, 2025); now **F5 AI Guardrails + AI Red Team**.
  - **Product line:** Inference Platform, agentic RT, CASI leaderboard.
  - **Mechanism:** Policy + behavioral + agent-driven.
  - **Integration:** F5 ADC inline; SaaS.

- **Patronus AI** — San Francisco (founded 2023).
  - **Source:** https://www.patronus.ai/
  - **Status:** $40.1M (Lightspeed, Notable, Redpoint).
  - **Product line:** Lynx (hallucination), Glider, agent simulators.
  - **Mechanism:** Generative simulators + 50+ failure modes.
  - **Integration:** API / CI / pre-prod.

- **Pillar Security** — Tel Aviv / Miami (founded 2023).
  - **Source:** https://pillar.security/
  - **Status:** $9M seed (Shield Capital).
  - **Product line:** Pillar Platform — AI lifecycle security.
  - **Mechanism:** Agent traffic mapping + runtime guardrails.
  - **Integration:** SaaS / repo / data infrastructure.

- **WhyLabs** — Seattle, WA (founded 2019).
  - **Source:** https://whylabs.ai/
  - **Status:** Series B; a16z.
  - **Product line:** WhyLabs platform + LangKit.
  - **Mechanism:** Statistical drift + whylogs profiles.
  - **Integration:** SaaS observability.

- **Microsoft (Prompt Shields)** — Redmond, WA.
  - **Source:** https://learn.microsoft.com/azure/ai-services/content-safety
  - **Status:** Hyperscaler.
  - **Product line:** Azure AI Content Safety: Prompt Shields, Groundedness.
  - **Mechanism:** Direct + indirect injection classifier.
  - **Integration:** Azure OpenAI / Foundry.

- **Google (ShieldGemma + Cloud)** — Mountain View, CA.
  - **Source:** https://ai.google.dev/gemma/docs/shieldgemma
  - **Status:** Hyperscaler.
  - **Product line:** ShieldGemma 1/2 + Vertex AI Safety + Model Armor.
  - **Mechanism:** ShieldGemma classifier + custom policies.
  - **Integration:** Vertex AI / Cloud Armor.

- **AWS (Bedrock Guardrails)** — Seattle.
  - **Source:** https://aws.amazon.com/bedrock/guardrails/
  - **Status:** Hyperscaler.
  - **Product line:** Bedrock Guardrails: prompt attacks, content filters, contextual grounding.
  - **Mechanism:** Layered classifiers + filters.
  - **Integration:** Amazon Bedrock / Agents.

- **IBM (Granite Guardian + watsonx.governance)** — Armonk, NY.
  - **Source:** https://www.ibm.com/granite
  - **Status:** Enterprise.
  - **Product line:** Granite Guardian 3.x / 4.1, watsonx.governance.
  - **Mechanism:** Risk-judge models with BYOC.
  - **Integration:** watsonx / on-prem.

- **Fiddler AI** — Palo Alto, CA (founded 2018).
  - **Source:** https://www.fiddler.ai/
  - **Status:** $32M Series B.
  - **Product line:** Trust Service, Guardrails, Observability.
  - **Mechanism:** Custom Trust Models, <100ms latency.
  - **Integration:** SaaS + VPC.

- **Galileo** — San Francisco (founded 2021).
  - **Source:** https://galileo.ai/
  - **Status:** $68M (Series B Scale VP); **Cisco intent to acquire announced Apr 9, 2026 (Cisco FY26 Q4)**.
  - **Product line:** Galileo Evaluate, Observe, Protect, Luna.
  - **Mechanism:** Luna eval models + agent observability.
  - **Integration:** SaaS / VPC.

- **Arize AI** — Berkeley, CA (founded 2020).
  - **Source:** https://arize.com/
  - **Status:** Series C.
  - **Product line:** Arize AX (commercial) + Phoenix (OSS).
  - **Mechanism:** OTEL traces + LLM-judge evaluators.
  - **Integration:** SaaS + self-host.

- **TrojAI** — Saint John, Canada (founded 2019).
  - **Source:** https://troj.ai/
  - **Status:** Series A.
  - **Product line:** Detect (build), Defend (runtime firewall), Defend for MCP.
  - **Mechanism:** Inline runtime firewall plus agent-led red-team scanning. (Vendor cites high-throughput inline classification; specific tokens-per-second figure is vendor-marketing-grade and not third-party verified.)
  - **Integration:** Runtime / MCP / coding agents.

- **ActiveFence (rebranded Alice 2026)** — NY / Tel Aviv (founded 2018).
  - **Source:** https://alice.io/
  - **Status:** $100M+ total.
  - **Product line:** WonderSuite + Rabbit Hole intel.
  - **Mechanism:** Adversarial intel + content moderation.
  - **Integration:** API / SaaS.

- **Zenity** — Tel Aviv / Boston (founded 2021).
  - **Source:** https://www.zenity.io/
  - **Status:** $55M+ (Series B Oct 2024).
  - **Product line:** Zenity for AI agents, Copilots, low-code.
  - **Mechanism:** Agent inventory + policy + runtime threat prevention.
  - **Integration:** M365 Copilot, Salesforce Einstein, ServiceNow.

- **Knostic** — Herndon, VA (founded 2023).
  - **Source:** https://knostic.ai/
  - **Status:** $14.3M.
  - **Product line:** Knowledge Security Platform, Prompt Gateway, Kirin, OpenAnt (OSS).
  - **Mechanism:** Need-to-know enforcement + query simulation + prompt sanitization.
  - **Integration:** Copilot / Glean / Gemini overlay.

- **Aim Security** — Tel Aviv (founded 2022).
  - **Source:** https://www.aim.security/
  - **Status:** $28M Series A; **ACQUIRED by Cato Networks Sep 2025** (~$350M).
  - **Product line:** GenAI Security Platform.
  - **Mechanism:** DLP + injection detection.
  - **Integration:** SASE / SSE inline (Cato).

- **Mindgard** — Lancaster, UK (founded 2022).
  - **Source:** https://mindgard.ai/
  - **Status:** $11.6M ($8M Dec 2024).
  - **Product line:** DAST-AI red-team automation.
  - **Mechanism:** MITRE ATLAS / OWASP-aligned attack simulation.
  - **Integration:** CI/CD / pre-prod.

- **Lasso Security** — Tel Aviv (founded 2023).
  - **Source:** https://www.lasso.security/
  - **Status:** $14.5M.
  - **Product line:** Lasso Platform, Intent Deputy (2026).
  - **Mechanism:** Browser-side AI-traffic classification and policy enforcement. (Vendor-cited attack-type breadth and accuracy figures are vendor-marketing-grade and not third-party verified.)
  - **Integration:** Browser / API / agents.

- **Prompt Security** — Tel Aviv (founded 2023).
  - **Source:** https://prompt.security/
  - **Status:** Series A.
  - **Product line:** Enterprise GenAI usage governance.
  - **Mechanism:** Real-time policy + content scanning.
  - **Integration:** Browser / SaaS / SSO.

- **SPLX (was SplxAI)** — NY (founded 2023).
  - **Source:** https://splx.ai/
  - **Status:** $7M seed; **ACQUIRED by Zscaler Nov 3, 2025** (deal value undisclosed).
  - **Product line:** Continuous red-team + AI Runtime Protection.
  - **Mechanism:** 20+ risk-categories scan + runtime firewall.
  - **Integration:** Zscaler ZTE inline.

- **Repello AI** — Bangalore / SF (founded 2023).
  - **Source:** https://repello.ai/
  - **Status:** Seed.
  - **Product line:** AI Inventory, ARTEMIS RT, runtime guardrails.
  - **Mechanism:** OWASP / NIST / MITRE-aligned red-team automation plus runtime guardrails. (Vendor-cited attack-pattern count is marketing-grade, not third-party verified.)
  - **Integration:** SaaS / browser.

- **Vijil** — (founded 2023).
  - **Source:** https://vijil.ai/
  - **Status:** Seed (a16z).
  - **Product line:** Vijil + Darwin (post-incident).
  - **Mechanism:** Continuous black-box red-team for agents.
  - **Integration:** SaaS.

- **AppSOC** — Santa Clara, CA (founded 2021).
  - **Source:** https://appsoc.com/
  - **Status:** $25M (Tola, Race Capital).
  - **Product line:** AISPM, AI red-team.
  - **Mechanism:** Discovery + AI-BOM + risk scoring.
  - **Integration:** DevSecOps / repo.

- **PromptArmor** — San Francisco (founded 2023).
  - **Source:** https://promptarmor.com/
  - **Status:** Seed.
  - **Product line:** PI defense (ICLR 2026 paper).
  - **Mechanism:** Off-the-shelf LLM preprocessor; <1% FPR/FNR on AgentDojo.
  - **Integration:** Pre-LLM filter / API. → Also see `03_defenses.md` § C3.

- **F5 AI Guardrails** — Seattle.
  - **Source:** https://www.f5.com/
  - **Status:** Public co. (post-CalypsoAI).
  - **Product line:** AI Guardrails + AI Red Team.
  - **Mechanism:** CASI scoring + runtime ADC.
  - **Integration:** F5 BIG-IP / Distributed Cloud.

- **Cisco AI Defense** — San Jose.
  - **Source:** https://www.cisco.com/
  - **Status:** Public co. (post-Robust Intelligence).
  - **Product line:** AI runtime + algorithmic red-team.
  - **Mechanism:** Algorithmic + traffic inspection.
  - **Integration:** Cisco fabric.

- **Zscaler (after SPLX)** — San Jose.
  - **Source:** https://www.zscaler.com/
  - **Status:** Public co.
  - **Product line:** Zero Trust Exchange + SPLX AI.
  - **Mechanism:** Inline prompt/output scanning.
  - **Integration:** SSE inline.

- **Cato Networks (after Aim)** — Tel Aviv.
  - **Source:** https://www.catonetworks.com/
  - **Status:** Late-stage.
  - **Product line:** SASE with GenAI security.
  - **Mechanism:** DLP + injection detection at edge.
  - **Integration:** SASE inline.

- **Snowflake Cortex Guard** — Bozeman, MT.
  - **Source:** https://www.snowflake.com/
  - **Status:** Public co.
  - **Product line:** Cortex AI Guard.
  - **Mechanism:** Built-in LLM safety filter.
  - **Integration:** Cortex / Snowflake DB.

- **Check Point (after Lakera)** — Tel Aviv.
  - **Source:** https://www.checkpoint.com/
  - **Status:** Public co.
  - **Product line:** Check Point + Lakera AI Security.
  - **Mechanism:** Lakera Guard inline.
  - **Integration:** Check Point fabric.

- **Palo Alto Networks Prisma AIRS (after Protect AI)** — Santa Clara.
  - **Source:** https://www.paloaltonetworks.com/
  - **Status:** Public co.
  - **Product line:** Prisma AIRS — scan + posture + RT + runtime + agent.
  - **Mechanism:** End-to-end AI security platform.
  - **Integration:** Prisma fabric / Bedrock.

## Eval SaaS Platforms

`#eval-saas`

Hosted evaluation platforms — adjacent to red-teaming but focused on continuous evaluation, dataset management, and scoring.

### Entries

- **LangSmith** — LangChain.
  - **Source:** https://smith.langchain.com/
  - **Mechanism:** Tracing + 30+ eval templates including injection, PII, bias, toxicity.
  - **Result:** LangChain's eval SaaS.
  - **Status:** Verified.

- **Patronus AI Platform** — Patronus.
  - **Source:** https://www.patronus.ai/
  - **Mechanism:** Enterprise eval + adversarial test gen + 50+ failure detectors.
  - **Result:** Patronus's enterprise eval SaaS.
  - **Status:** Verified.

- **Galileo Evaluate / Protect** — Galileo (Cisco intent to acquire).
  - **Source:** https://galileo.ai/
  - **Mechanism:** Luna eval models + Guardrails + agent observability.
  - **Result:** Galileo's hosted eval/protect SaaS.
  - **Status:** Verified — pending Cisco acquisition FY26 Q4.

- **Arize Phoenix Cloud** — Arize.
  - **Source:** https://app.phoenix.arize.com/
  - **Mechanism:** Hosted Phoenix; OTEL tracing + LLM-judge evaluators.
  - **Result:** Hosted version of Phoenix OSS.
  - **Status:** Verified.

- **Helicone Cloud** — Helicone (Mintlify; maintenance mode).
  - **Source:** https://www.helicone.ai/
  - **Mechanism:** AI gateway + Llama-Guard / Prompt-Guard 2 hooks.
  - **Result:** Hosted Helicone; maintenance mode after Mintlify acquisition.
  - **Status:** Verified — maintenance mode.

- **Confident AI / DeepEval Cloud** — Confident AI.
  - **Source:** https://www.confident-ai.com/
  - **Mechanism:** DeepEval / DeepTeam dashboards.
  - **Result:** Hosted version of DeepEval/DeepTeam OSS.
  - **Status:** Verified.

- **Braintrust** — Braintrust ($80M Series B Feb 2026, ICONIQ, $800M valuation).
  - **Source:** https://www.braintrust.dev/
  - **Mechanism:** Dataset management, evaluations, online scoring.
  - **Result:** Most-recently-funded eval SaaS as of mid-2026.
  - **Status:** Verified.

- **Comet Opik Cloud** — Comet.
  - **Source:** https://www.comet.com/site/products/opik/
  - **Mechanism:** Hosted Opik; observability + evaluations.
  - **Result:** Hosted version of Opik OSS.
  - **Status:** Verified.

- **Maxim AI** — Maxim.
  - **Source:** https://www.getmaxim.ai/
  - **Mechanism:** Eval + observability platform.
  - **Result:** Eval SaaS focused on LLM application observability.
  - **Status:** Verified.

- **Fiddler Trust Service** — Fiddler.
  - **Source:** https://www.fiddler.ai/trust-service
  - **Mechanism:** Sub-100ms guardrail scoring in VPC.
  - **Result:** Fiddler's hosted guardrail-as-a-service.
  - **Status:** Verified.

## Tool selection by deployment shape

`#tool-selection`

Recipes for matching the tool stack to the deployment context.

### Startup with no security budget

Free, hosted-or-self tools only.
- **Inputs:** Llama Prompt Guard 2 22M (HF) for cheap injection screening.
- **Outputs:** Llama Guard 3 1B (HF) for content.
- **Runtime:** LLM Guard (MIT) wrapping both, or AWS / Azure / GCP guardrails free tier.
- **Pre-deploy:** promptfoo redteam mode + Garak nightly in CI.
- **Cost:** GPU inference only.

### Pre-IPO with compliance pressure

Add commercial layer for SOC 2 / EU AI Act evidence.
- Lakera Guard (Check Point), Protect AI / Prisma AIRS, or HiddenLayer for runtime + supply-chain scanning.
- Patronus or Galileo for documented eval reports.
- Keep promptfoo + DeepTeam OSS for CI gates (auditors love reproducible artifacts).
- PromptArmor preprocessor for indirect-injection coverage.

### Research lab with adaptive-attack methodology needs

- **Benchmarks:** HarmBench + JailbreakBench + AgentDojo.
- **Attack impls:** nanoGCG / BrokenHill / AutoDAN-Turbo / PAIR.
- **Test driver:** Inspect AI (UK AISI) and lm-evaluation-harness.
- **Multi-turn:** PyRIT.
- **Unified comparison:** EasyJailbreak.

### Regulated finance / healthcare production

- Inline ML-aware firewall: Cisco AI Defense (Robust Intelligence), Palo Alto Prisma AIRS (Protect AI), or F5 AI Guardrails (CalypsoAI).
- IBM Granite Guardian 4.1 or NVIDIA NeMo Guardrails self-hosted for in-VPC content/groundedness scoring (HIPAA / PCI).
- Fiddler AI for sub-100ms guardrails inside VPC.
- Continuous red-team via Mindgard or HiddenLayer Attack Simulation tied to MITRE ATLAS for examiner-ready reports.

## Status flags

`#status-flags`

Consolidated reference for deprecated, archived, acquired, and license-cautioned entries.

- **DEPRECATED / ARCHIVED:** Rebuff (archived May 16, 2025).
- **MAINTENANCE MODE:** Helicone (after Mintlify acquisition Mar 2026); HELM (entering maintenance Jun 2026); Giskard v2 LLM scan.
- **ACQUIRED (still operating under new owner):** Lakera → Check Point (announced Sep 16, 2025, ~$300M); Protect AI → Palo Alto Networks (announced Apr 28, 2025, completed Jul 22, 2025, >$500M); Robust Intelligence → Cisco (announced Aug 26, 2024, closed Oct 2024, ~$400M); CalypsoAI → F5 (Sep 11, 2025, ~$180M); Aim Security → Cato Networks (Sep 3, 2025, ~$350M); SPLX → Zscaler (Nov 3, 2025); Galileo → Cisco (intent announced Apr 9, 2026; Cisco FY26 Q4); promptfoo → OpenAI (Mar 9, 2026, but remains MIT OSS); Helicone → Mintlify (Mar 3, 2026).
- **License cautions:** LLAMATOR is **CC BY-NC-SA 4.0 (non-commercial)** — do not embed in commercial products without consulting legal. EasyJailbreak is **GPL-3.0** — not compatible with proprietary closed-source distribution. Phoenix is **Elastic-2.0** (not OSI-OSS) — Arize gates resale.

## Verification notes

Vendor status (acquisition dates, valuations) accurate as of the May 2026 dossier compile; the area is rapidly evolving and quarterly re-verification is recommended.

**Total entries in this file:** 11 OSS RT runners + 6 OSS defense guards + 8 OSS classifiers + 5 OSS eval harnesses + 11 OSS attack implementations + 4 OSS observability + 35 commercial vendors + 10 eval SaaS = **90 entries**. The source dossier footer states 86 unique pre-rebrand vendors; the count here includes post-acquisition rebrands (Cisco AI Defense, F5 AI Guardrails, Prisma AIRS, etc.) as separate entries for clarity.

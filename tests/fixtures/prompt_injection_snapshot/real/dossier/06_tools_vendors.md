# LLM Security Tools & Vendors

**Compiled:** May 2026 | All GitHub state, license, last-commit/release verified.

---

## Open-Source Tools

### Red-team / Probe Runners

| Name | Maintainer | GitHub | License | Stars | Last release | Purpose | Install | Integration |
|------|-----------|--------|---------|-------|-------------|---------|---------|-------------|
| **garak** | NVIDIA | github.com/NVIDIA/garak | Apache-2.0 | 7.7k | v0.15.0, May 2026 | LLM vuln scanner; 15+ probe categories | `pip install garak` | CI / ad-hoc |
| **PyRIT** | Microsoft (moved from Azure org) | github.com/microsoft/PyRIT | MIT | 3.8k | v0.13.0, Apr 2026 | Multi-turn risk-ID framework with attacker/scorer loop | `pip install pyrit` | Research / CI |
| **promptfoo** | Promptfoo (acq. by OpenAI Mar 2026; remains MIT) | github.com/promptfoo/promptfoo | MIT | 20.9k | v0.121.9, Apr 2026 | Eval + redteam CLI; 50+ vuln plugins | `npx promptfoo@latest` | CI / local |
| **Giskard OSS (v3)** | Giskard | github.com/Giskard-AI/giskard-oss | Apache-2.0 | 5.3k | active 2026 (v2 LLM scan unmaintained) | LLM agent eval/red-team library | `pip install giskard-checks` | Research / CI |
| **DeepTeam** | Confident AI | github.com/confident-ai/deepteam | Apache-2.0 | 1.6k | v1.0.4, Nov 2025 | 50+ vulns, 20+ attacks (OWASP_ASI_2026, MITRE) | `pip install deepteam` | CI / runtime |
| **DeepEval** | Confident AI | github.com/confident-ai/deepeval | Apache-2.0 | 15.2k | v3.9.9, Dec 2025 | LLM eval framework; 30+ metrics incl. safety | `pip install deepeval` | CI / pytest |
| **EasyJailbreak** | EasyJailbreak | github.com/EasyJailbreak/EasyJailbreak | GPL-3.0 | 848 | v0.1.3, Aug 2024 | Unified framework for 12+ jailbreaks (PAIR/GCG/AutoDAN/GPTFuzz) | `git clone + pip -e .` | Research |
| **LLAMATOR** | LLAMATOR-Core | github.com/LLAMATOR-Core/llamator | CC BY-NC-SA 4.0 (non-commercial) | 208 | v3.5.0, Jan 2026 | Red-team framework with attacker/judge/target roles | `pip install llamator` | Research / pre-prod |
| **Open-Prompt-Injection** | Liu et al. (USENIX 2024) | github.com/liu00222/Open-Prompt-Injection | MIT | 436 | research-quality | 5 attacks × 10 defenses × 10 LLMs benchmark | `git clone + pip -e .` | Research |
| **Agentic Radar** | SPLX (Zscaler) | github.com/splx-ai/agentic-radar | Apache-2.0 | 963 | v0.14.1, Nov 2025 | Workflow scanner for agentic AI (CrewAI, LangGraph, n8n, MCP) | `pip install agentic-radar` | CI / pre-deploy |
| **OpenAnt** | Knostic | github.com/knostic/OpenAnt | Apache-2.0 | 511 | active 2026 | LLM-based vuln discovery (detect → attack-verify) | `git clone + run` | Research / supply-chain |

### Defense / Runtime Guard

| Name | Maintainer | GitHub | License | Stars | Last release | Purpose | Install | Integration |
|------|-----------|--------|---------|-------|-------------|---------|---------|-------------|
| **LLM Guard** | Protect AI (Palo Alto Networks since Jul 2025) | github.com/protectai/llm-guard | MIT | 2.9k | v0.3.16, active 2026 | 15 input + 20 output scanners | `pip install llm-guard` | Runtime gateway |
| **NeMo Guardrails** | NVIDIA-NeMo | github.com/NVIDIA-NeMo/Guardrails | Apache-2.0 | 6.1k | v0.21.0, Mar 2026 | Programmable Colang dialog rails; YARA scanner | `pip install nemoguardrails` | Runtime / chatbot |
| **Guardrails AI** | Guardrails AI | github.com/guardrails-ai/guardrails | Apache-2.0 | 6.8k | v0.10.0, Apr 2026 | Validator hub; structured output + safety guards | `pip install guardrails-ai` | Runtime / RAG |
| **Rebuff** | Protect AI | github.com/protectai/rebuff | Apache-2.0 | 1.5k | **ARCHIVED May 16, 2025** | (legacy) Heuristic+LLM+vector+canary | `pip install rebuff` | Reference only |
| **LlamaFirewall (PurpleLlama)** | Meta | github.com/meta-llama/PurpleLlama | MIT (code) + Llama license (weights) | 4.2k | active 2026 | Multi-scanner runtime: PromptGuard + AlignmentCheck + CodeShield | `pip install llamafirewall` | Runtime / agent |
| **PromptInject** | Agency Enterprise (NeurIPS Best Paper 2022) | github.com/agencyenterprise/PromptInject | MIT | 488 | maintenance | Original goal-hijacking + prompt-leaking framework | `pip install promptinject` | Research / reference |

### Classifiers (open weights or training code)

| Name | Maintainer | URL | License | Type | Last update | Purpose |
|------|-----------|-----|---------|------|-------------|---------|
| **Llama Guard 4 (12B multimodal)** | Meta | huggingface.co/meta-llama/Llama-Guard-4-12B | Llama 4 Community | Weights | 2025 | Text + image safety classifier |
| Llama Guard 3 (1B/8B/11B-vision) | Meta | huggingface.co/meta-llama/Llama-Guard-3-8B | Llama 3 license | Weights | 2024 | Multilingual text safety classifier |
| **Llama Prompt Guard 2 (22M/86M)** | Meta | huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M | Llama license | Weights | 2025 | Lightweight injection + jailbreak detector |
| **ShieldGemma 2 (4B multimodal)** | Google DeepMind | huggingface.co/google/shieldgemma-2-4b-it | Gemma license | Weights | 2025 | Text + image safety scoring |
| **WildGuard (7B)** | Allen AI | huggingface.co/allenai/wildguard | Apache-2.0 | Weights | 2024 | Prompt + response harm + refusal eval; matches GPT-4 |
| Aegis Llama-Guard (Defensive/Permissive) | NVIDIA | huggingface.co/nvidia/Aegis-AI-Content-Safety-LlamaGuard-Defensive-1.0 | Llama 2 license | Weights | 2024 | 13-category content safety |
| **Granite Guardian 3.3 / 4.1** | IBM | github.com/ibm-granite/granite-guardian | Apache-2.0 | Weights + code | 4.1, Apr 2026 | BYO-criteria judge: jailbreak, hallucination, RAG groundedness |
| Granite Guardian HAP-38M / 125M | IBM | huggingface.co/ibm-granite/granite-guardian-hap-125m | Apache-2.0 | Weights | active | Lightweight English toxicity classifier |

### Eval Harnesses

| Name | Maintainer | GitHub | License | Stars | Last release | Purpose | Install |
|------|-----------|--------|---------|-------|-------------|---------|---------|
| **lm-evaluation-harness** | EleutherAI | github.com/EleutherAI/lm-evaluation-harness | MIT | 12.4k | v0.4.11, Feb 2026 | 60+ benchmarks; safety subsets | `pip install lm-eval` |
| **Inspect AI** | UK AISI | github.com/UKGovernmentBEIS/inspect_ai | MIT | 2.0k | active Apr 2026 | Government-grade eval framework | `pip install inspect-ai` |
| **Inspect Evals** | UK AISI / Vector / Arcadia | github.com/UKGovernmentBEIS/inspect_evals | MIT | active | active | 200+ community evals incl. AgentDojo, HarmBench | `pip install inspect-evals` |
| **HELM** | Stanford CRFM | github.com/stanford-crfm/helm | Apache-2.0 | 2.8k | v0.5.16, Apr 2026 (entering maintenance Jun 2026) | Holistic eval; AIR-Bench safety subset | `pip install crfm-helm` |
| AIR-Bench 2024 | Stanford CRFM | github.com/stanford-crfm/air-bench-2024 | Apache-2.0 | small | 2024 | Regulation-aligned safety benchmark | `pip install air-bench` |

### Research / Academic Attack Implementations

| Name | Maintainer | GitHub | License | Stars | Status | Purpose |
|------|-----------|--------|---------|-------|--------|---------|
| **HarmBench** | CAIS | github.com/centerforaisafety/HarmBench | MIT | 939 | v1.0, Feb 2024 | 18 attack methods × 33 LLMs |
| **JailbreakBench** | JailbreakBench | github.com/JailbreakBench/jailbreakbench | MIT | 586 | active artifact updates | JBB-Behaviors + leaderboard + judge |
| **AgentDojo** | ETH SPY Lab | github.com/ethz-spylab/agentdojo | MIT | 550 | v0.1.35, Oct 2025 | Tool-use agent + 629 injection cases |
| **nanoGCG** | Gray Swan AI | github.com/GraySwanAI/nanoGCG | MIT | 331 | v0.3.0, Feb 2025 | Fast PyTorch GCG; mellowmax, multi-position swap |
| **llm-attacks** (orig GCG) | Zou et al. | github.com/llm-attacks/llm-attacks | MIT | 4.6k | research-frozen | Original GCG paper code |
| **BrokenHill** | Bishop Fox | github.com/BishopFox/BrokenHill | MIT | 160 | active 2025-26 | Productionized GCG runnable on RTX 4090 / Mac |
| **AutoDAN-Turbo** | SaFoLab WISC (ICLR 2025) | github.com/SaFoLab-WISC/AutoDAN-Turbo | MIT | 363 | active | Lifelong self-exploring black-box jailbreak agent |
| **AutoDAN** | Liu et al. (ICLR 2024) | github.com/SheltonLiu-N/AutoDAN | MIT | 440 | research-frozen | Genetic-algorithm stealthy jailbreak |
| **PAIR (JailbreakingLLMs)** | Chao et al. | github.com/patrickrchao/JailbreakingLLMs | MIT | 732 | research-frozen | Black-box semantic jailbreak in <20 queries |
| **TAP** | RICommunity | github.com/RICommunity/TAP | MIT | 230 | research-frozen | Tree-of-thoughts attacker/eval/target |
| **GPTFuzz** | Yu et al. | github.com/sherdencooper/GPTFuzz | MIT | 580 | maintenance | Mutation fuzzing of jailbreak templates |

### Observability with Safety Hooks (open-source)

| Name | Maintainer | GitHub | License | Stars | Status | Purpose |
|------|-----------|--------|---------|-------|--------|---------|
| **Phoenix** | Arize AI | github.com/Arize-ai/phoenix | Elastic-2.0 | 9.5k | v15.3.0, May 2026 | OTEL traces + LLM evaluators |
| **Opik** | Comet | github.com/comet-ml/opik | Apache-2.0 | 19.2k | v2.0.21, May 2026 | Tracing + LLM-judge + prod monitoring |
| Helicone | Helicone (Mintlify acq. Mar 2026) | github.com/Helicone/helicone | Apache-2.0 | 5.6k | Aug 2025 | AI gateway + Llama-Guard / Prompt-Guard 2 hooks |
| LangKit | WhyLabs | github.com/whylabs/langkit | Apache-2.0 | 984 | Nov 2024 (slow) | Text metrics extractor |

---

## Commercial Vendors

| Name | HQ | Founded | Status | Website | Product line | Detection mechanism | Integration |
|------|-----|---------|--------|---------|-------------|----------------------|-------------|
| **Lakera** | Zurich, CH | 2021 | $20M Series A; **ACQUIRED by Check Point Sep 2025** | lakera.ai | Lakera Guard, Red Team, AI Agent Security | Heuristic + classifier + Gandalf-trained models | API gateway, AWS/Azure |
| **Protect AI** | Seattle, WA | 2022 | **ACQUIRED by Palo Alto Networks Apr-Jul 2025** (~$500M+); now Prisma AIRS | protectai.com | Recon (RT), Layer (firewall), Sightline | Model scanning, runtime, MLSecOps | Prisma AIRS / Bedrock / SageMaker |
| **HiddenLayer** | Austin, TX | 2022 | $50M+ Series A (2023); SHIELD US gov contract | hiddenlayer.com | AISec Platform 2.0: Discovery, Supply Chain, Attack Sim, Runtime | Behavior + adversarial detection | SaaS / on-prem / airgap |
| **Robust Intelligence** | Cambridge, MA | 2019 | **ACQUIRED by Cisco Aug-Oct 2024** (~$400M); now Cisco AI Defense | cisco.com/site/us/en/products/security/ai-defense | AI Firewall, algorithmic red-team | Adversarial scan + WAF for AI | Cisco fabric, network-inline |
| **CalypsoAI** | Dublin / NYC | 2018 | **ACQUIRED by F5 2025**; now F5 AI Guardrails + AI Red Team | calypsoai.com | Inference Platform, agentic RT, CASI leaderboard | Policy + behavioral + agent-driven | F5 ADC inline; SaaS |
| **Patronus AI** | San Francisco | 2023 | $40.1M (Lightspeed, Notable, Redpoint) | patronus.ai | Lynx (hallucination), Glider, agent simulators | Generative simulators + 50+ failure modes | API / CI / pre-prod |
| **Pillar Security** | Tel Aviv / Miami | 2023 | $9M seed (Shield Capital) | pillar.security | Pillar Platform: AI lifecycle security | Agent traffic mapping + runtime guardrails | SaaS / repo / data infra |
| **WhyLabs** | Seattle, WA | 2019 | Series B; a16z | whylabs.ai | WhyLabs platform + LangKit | Statistical drift + whylogs profiles | SaaS observability |
| **Microsoft (Prompt Shields)** | Redmond, WA | — | Hyperscaler | learn.microsoft.com/azure/ai-services/content-safety | Azure AI Content Safety: Prompt Shields, Groundedness | Direct + indirect injection classifier | Azure OpenAI / Foundry |
| **Google (ShieldGemma + Cloud)** | Mountain View | — | Hyperscaler | ai.google.dev/gemma/docs/shieldgemma | ShieldGemma 1/2 + Vertex AI Safety + Model Armor | ShieldGemma classifier + custom policies | Vertex AI / Cloud Armor |
| **AWS (Bedrock Guardrails)** | Seattle | — | Hyperscaler | aws.amazon.com/bedrock/guardrails | Bedrock Guardrails: prompt attacks, content filters, contextual grounding | Layered classifiers + filters | Amazon Bedrock / Agents |
| **IBM (Granite Guardian + watsonx.governance)** | Armonk, NY | — | Enterprise | ibm.com/granite | Granite Guardian 3.x/4.1, watsonx.governance | Risk-judge models w/ BYOC | watsonx / on-prem |
| **Fiddler AI** | Palo Alto, CA | 2018 | $32M Series B | fiddler.ai | Trust Service, Guardrails, Observability | Custom Trust Models, <100ms latency | SaaS + VPC |
| **Galileo** | San Francisco | 2021 | $68M (Series B Scale VP); **Cisco intent to acquire FY26 Q4** | galileo.ai | Galileo Evaluate, Observe, Protect, Luna | Luna eval models + agent observability | SaaS / VPC |
| **Arize AI** | Berkeley, CA | 2020 | Series C | arize.com | Arize AX (commercial) + Phoenix (OSS) | OTEL traces + LLM-judge evaluators | SaaS + self-host |
| **TrojAI** | Saint John, Canada | 2019 | Series A | troj.ai | Detect (build), Defend (runtime firewall), Defend for MCP | 10M tokens/sec firewall + agent-led RT | Runtime / MCP / coding agents |
| **ActiveFence (rebranded Alice 2026)** | NY / Tel Aviv | 2018 | $100M+ total | alice.io / activefence.com | WonderSuite + Rabbit Hole intel | Adversarial intel + content moderation | API / SaaS |
| **Zenity** | Tel Aviv / Boston | 2021 | $55M+ (Series B Oct 2024) | zenity.io | Zenity for AI agents, Copilots, low-code | Agent inventory + policy + runtime threat prevention | M365 Copilot, Salesforce Einstein, ServiceNow |
| **Knostic** | Herndon, VA | 2023 | $14.3M | knostic.ai | Knowledge Security Platform, Prompt Gateway, Kirin, OpenAnt (OSS) | Need-to-know enforcement, query simulation, prompt sanitization | Copilot / Glean / Gemini overlay |
| **Aim Security** | Tel Aviv | 2022 | $28M Series A; **ACQUIRED by Cato Networks Sep 2025** (~$350M) | aim.security | GenAI Security Platform | DLP + injection detection | SASE / SSE inline (Cato) |
| **Mindgard** | Lancaster, UK | 2022 | $11.6M ($8M Dec 2024) | mindgard.ai | DAST-AI red-team automation | MITRE ATLAS / OWASP-aligned attack sim | CI/CD / pre-prod |
| **Lasso Security** | Tel Aviv | 2023 | $14.5M | lasso.security | Lasso Platform, Intent Deputy (2026) | 3000+ attack types, 98.6% accuracy | Browser / API / agents |
| **Prompt Security** | Tel Aviv | 2023 | Series A | prompt.security | Enterprise GenAI usage governance | Real-time policy + content scanning | Browser / SaaS / SSO |
| **SPLX** (was SplxAI) | NY | 2023 | $7M seed; **ACQUIRED by Zscaler 2025** | splx.ai | Continuous red-team + AI Runtime Protection | 20+ risk categories scan + runtime firewall | Zscaler ZTE inline |
| **Repello AI** | Bangalore / SF | 2023 | seed | repello.ai | AI Inventory, ARTEMIS RT, runtime guardrails | 15M+ attack patterns; OWASP/NIST/MITRE | SaaS / browser |
| **Vijil** | — | 2023 | seed (a16z) | vijil.ai | Vijil + Darwin (post-incident) | Continuous black-box RT for agents | SaaS |
| **AppSOC** | Santa Clara, CA | 2021 | $25M (Tola, Race Capital) | appsoc.com | AISPM, AI red-team | Discovery + AI-BOM + risk scoring | DevSecOps / repo |
| **PromptArmor** | San Francisco | 2023 | seed | promptarmor.com | PI defense (ICLR 2026 paper) | Off-the-shelf LLM preprocessor; <1% FPR/FNR on AgentDojo | Pre-LLM filter / API |
| F5 AI Guardrails | Seattle | — | Public co. | f5.com | AI Guardrails + AI Red Team | CASI scoring + runtime ADC | F5 BIG-IP / Distributed Cloud |
| Cisco AI Defense | San Jose | — | Public co. | cisco.com | AI runtime + algorithmic red-team | Algorithmic + traffic inspection | Cisco fabric |
| Zscaler (after SPLX) | San Jose | — | Public co. | zscaler.com | Zero Trust Exchange + SPLX AI | Inline prompt/output scanning | SSE inline |
| Cato Networks (after Aim) | Tel Aviv | — | Late-stage | catonetworks.com | SASE with GenAI security | DLP + injection detection at edge | SASE inline |
| Snowflake Cortex Guard | Bozeman, MT | — | Public co. | snowflake.com | Cortex AI Guard | Built-in LLM safety filter | Cortex / Snowflake DB |
| Check Point (after Lakera) | Tel Aviv | 1993 | Public co. | checkpoint.com | Check Point + Lakera AI Security | Lakera Guard inline | Check Point fabric |
| Palo Alto Networks Prisma AIRS (after Protect AI) | Santa Clara | 2005 | Public co. | paloaltonetworks.com | Prisma AIRS: scan + posture + RT + runtime + agent | End-to-end AI security platform | Prisma fabric / Bedrock |

---

## Eval SaaS Platforms

| Name | URL | Vendor | Capability |
|------|-----|--------|-----------|
| **LangSmith** | smith.langchain.com | LangChain | Tracing + 30+ eval templates incl. injection, PII, bias, toxicity |
| **Patronus AI Platform** | patronus.ai | Patronus | Enterprise eval + adversarial test gen + 50+ failure detectors |
| **Galileo Evaluate / Protect** | galileo.ai | Galileo (Cisco intent to acquire) | Luna eval models, Guardrails, agent observability |
| **Arize Phoenix Cloud** | app.phoenix.arize.com | Arize | Hosted Phoenix; OTEL tracing + LLM-judge evals |
| Helicone Cloud | helicone.ai | Helicone (Mintlify; maintenance mode) | AI gateway + Llama-Guard / Prompt-Guard 2 hooks |
| Confident AI / DeepEval Cloud | confident-ai.com | Confident AI | DeepEval/DeepTeam dashboards |
| **Braintrust** | braintrust.dev | Braintrust ($80M Series B Feb 2026, ICONIQ, $800M val) | Dataset mgmt, evals, online scoring |
| Comet Opik Cloud | comet.com/site/products/opik | Comet | Hosted Opik; observability + evals |
| Maxim AI | getmaxim.ai | Maxim | Eval + observability |
| Fiddler Trust Service | fiddler.ai/trust-service | Fiddler | Sub-100ms guardrail scoring in VPC |

---

## Tool Selection by Deployment Shape

**Startup with no security budget.** Free, hosted-or-self tools only.
- Inputs: Llama Prompt Guard 2 22M (HF) for cheap injection screening
- Outputs: Llama Guard 3 1B (HF) for content
- Runtime: LLM Guard (MIT) wrapping both, or AWS/Azure/GCP guardrails free tier
- Pre-deploy: promptfoo redteam mode + Garak nightly in CI
- Cost: GPU inference only

**Pre-IPO with compliance pressure.** Add commercial layer for SOC 2 / EU AI Act evidence.
- Lakera Guard (Check Point), Protect AI / Prisma AIRS, or HiddenLayer for runtime + supply-chain scanning
- Patronus or Galileo for documented eval reports
- Keep promptfoo + DeepTeam OSS for CI gates (auditors love reproducible artifacts)
- PromptArmor preprocessor for indirect-injection coverage

**Research lab with adaptive-attack methodology needs.**
- Benchmarks: HarmBench + JailbreakBench + AgentDojo
- Attack impls: nanoGCG / BrokenHill / AutoDAN-Turbo / PAIR
- Test driver: Inspect AI (UK AISI) and lm-evaluation-harness
- Multi-turn: PyRIT
- Unified comparison: EasyJailbreak

**Regulated finance / healthcare production.**
- Inline ML-aware firewall: Cisco AI Defense (Robust Intelligence), Palo Alto Prisma AIRS (Protect AI), or F5 AI Guardrails (CalypsoAI)
- IBM Granite Guardian 4.1 or NVIDIA NeMo Guardrails self-hosted for in-VPC content/groundedness scoring (HIPAA/PCI)
- Fiddler AI for sub-100ms guardrails inside VPC
- Continuous RT via Mindgard or HiddenLayer Attack Simulation tied to MITRE ATLAS for examiner-ready reports

---

## Status Flags

- **DEPRECATED / ARCHIVED**: Rebuff (archived May 16, 2025).
- **MAINTENANCE MODE**: Helicone (after Mintlify acq. Mar 2026); HELM (entering maintenance Jun 2026); Giskard v2 LLM scan.
- **ACQUIRED (still operating under new owner)**: Lakera→Check Point (Sep 2025); Protect AI→Palo Alto Networks (Jul 2025, $500M+); Robust Intelligence→Cisco (Oct 2024, ~$400M); CalypsoAI→F5 (2025); Aim Security→Cato Networks (Sep 2025, ~$350M); SPLX→Zscaler (2025); Galileo→Cisco (announced intent, FY26 Q4); promptfoo→OpenAI (Mar 2026, but remains MIT OSS); Helicone→Mintlify (Mar 2026).
- **License caution**: LLAMATOR is **CC BY-NC-SA 4.0 (non-commercial)** — do not embed in commercial products without consulting legal. EasyJailbreak is **GPL-3.0** — not compatible with proprietary closed-source distribution. Phoenix is **Elastic-2.0** (not OSI-OSS) — Arize gates resale.

**Final tally:** 45 open-source tools + 31 commercial vendors + 10 eval SaaS platforms = **86 entries**.

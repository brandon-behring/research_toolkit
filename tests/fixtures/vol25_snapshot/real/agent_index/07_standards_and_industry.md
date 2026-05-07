# Standards, Regulations, Lab Frameworks, and Industry Research

<!-- AGENT-INDEX: keep this block stable; future agents read it first. -->
**Scope:** Standards bodies (OWASP, NIST, ISO, MITRE), binding regulations (EU AI Act, US EO, UK AISI, China Interim Measures, Korea AI Basic Act, etc.), frontier-lab voluntary frameworks (Anthropic RSP, OpenAI Preparedness, DeepMind FSF, Meta, Microsoft, xAI), and industry research reports / system cards.
**Out of scope:** Research papers / tools — see `01_direct_attacks.md` through `06_tools_and_vendors.md`.
**Coverage window:** 2018–2026 (frameworks); through 2026 (regulations, reports).
**Last updated:** 2026-05-06.
**Subsections (stable anchors):** Standards-frameworks · Regulatory · Frontier-lab-voluntary-frameworks · Industry-research-reports · Compliance-posture · Standards landscape May 2026.
**Key terms covered:** OWASP LLM Top 10 (2025), OWASP AI Exchange, OWASP AI Testing Guide, NIST AI RMF, NIST AI 600-1 (MP-2.3-005), NIST TEVV, ISO/IEC 42001:2023, ISO/IEC 23894:2023, ISO/IEC 27001+27090, MITRE ATLAS v5.4, MITRE ATT&CK, EU AI Act (Reg 2024/1689) Articles 9/15/55/73, GPAI Code of Practice, US EO 14179 (revoked 14110), US AI Bill of Rights, UK AISI, UK Frontier AI Safety Commitments, Bletchley/Seoul/Paris summits, China CAC Interim Measures, Canada AIDA, Singapore IMDA Model AI GF + Agentic AI MGF, Japan AI Guidelines + AI Promotion Act, South Korea AI Basic Act, Brazil PL 2338, Colorado AI Act, NYC Local Law 144, NIST AI 100-2 (Adversarial ML Taxonomy), Anthropic RSP v3 (ASL-3), OpenAI Preparedness v2, DeepMind FSF v3, Meta Frontier AI Framework, Microsoft RAI v2, xAI RMF, Cohere, Frontier Model Forum, METR FSP Tracker, Constitutional Classifiers (paper), Sleeper Agents (paper), Persistent Pre-training Poisoning (paper), Many-shot Jailbreaking, Petri, AuditBench, Crescendo, PyRIT, Spotlighting, EchoLeak, Lakera GenAI Security Readiness Report, HiddenLayer 2026 Threat Landscape, Cisco AI Defense reports, MITRE ATLAS Case Studies, FLI AI Safety Index 2025.
**Related files:** `00_overview.md` (standards landscape one-paragraph), `03_defenses.md` (linked Anthropic / OpenAI / DeepMind / Microsoft research), `06_tools_and_vendors.md` (vendor compliance).

## Topic overview

This file enumerates the standards, regulatory, and lab-framework surface — the governance scaffolding that compliance, procurement, and policy readers need. The post-2024 governance landscape is increasingly bifurcated: voluntary frontier-lab frameworks (Anthropic RSP, OpenAI Preparedness, DeepMind FSF, Meta) are 12–18 months ahead of binding regulation on agentic AI, while the EU AI Act Article 15 — enforceable 2 August 2026 — represents the first binding adversarial-robustness mandate.

The de facto compliance reference is **NIST AI 600-1 + ISO/IEC 42001**: NIST 600-1 for risk-category coverage (especially MP-2.3-005, the adversarial-testing mandate) and ISO/IEC 42001 for the certifiable AI Management System that procurement teams demand. **OWASP LLM Top 10 (v2025)** is the application-developer's working checklist. **MITRE ATLAS** (v5.4 Feb 2026) is the TTP vocabulary.

The widest gap voluntary-vs-binding is **agentic / computer-use AI**. Labs (Anthropic RSP v3, OpenAI Preparedness v2, DeepMind FSF v3, Meta) are well ahead of every binding regulation here. EchoLeak (CVE-2025-32711) was the first production-grade zero-click indirect-PI exploit, and it landed in this gap — EU AI Act, NIST 600-1, and ISO 42001 all predate the agentic transition.

## Standards Frameworks

`#standards-frameworks`

The major non-binding standards bodies and frameworks.

### OWASP Top 10 for LLM Applications

- **Version:** 2025 (v2025), released November 2024.
- **Publisher:** OWASP Gen AI Security Project.
- **Source:** https://genai.owasp.org/llm-top-10/
- **PDF:** https://owasp.org/www-project-top-10-for-large-language-model-applications/assets/PDF/OWASP-Top-10-for-LLMs-v2025.pdf
- **What it says about prompt injection:** **LLM01** is **Prompt Injection** — explicitly the #1 risk. Distinguishes **direct** (user-supplied jailbreaks) from **indirect** (attacker-controlled content via documents, web pages, retrieved data, multimodal payloads). The 2025 update emphasizes injections need not be human-readable. Couples with LLM02 (Sensitive Info Disclosure), LLM05 (Improper Output Handling), and the new LLM06 Excessive Agency for agentic exploits.
- **Interview move:** Reference LLM01 as the canonical taxonomy entry; cite LLM06 for agent confused-deputy; cite LLM02 for system-prompt extraction.

### OWASP AI Exchange (formerly AI Security & Privacy Guide)

- **Version:** Continuous; OWASP Flagship status March 2025; major update summer 2026.
- **Source:** https://owaspai.org/
- **Companion:** https://owasp.org/www-project-ai-security-and-privacy-guide/
- **Scope:** 300+ pages covering analytical, discriminative, generative, and heuristic AI; threats, controls, references; explicit harmonization to NIST, ISO, and MITRE ATLAS.
- **What it says about prompt injection:** Treats PI as a category of *runtime model evasion*; cross-walks controls to ISO/IEC 27090 and EU AI Act Article 15. 2026 work-streams add **Agentic AI**, **Red Teaming**, and **Harmonization** mappings.
- **Interview move:** De facto crosswalk reference — contributed 70 pages each to EU AI Act and ISO/IEC 27090.

### OWASP AI Testing Guide (2026)

- **Source:** https://www.practical-devsecops.com/owasp-ai-testing-guide-explained/
- **Scope:** Test methodology companion to AI Exchange — adversarial robustness testing playbooks.

### NIST AI Risk Management Framework (AI RMF 1.0)

- **Version:** 1.0, January 2023.
- **Source:** https://www.nist.gov/itl/ai-risk-management-framework
- **Scope:** Voluntary, sector-agnostic risk-management lifecycle (Govern, Map, Measure, Manage).
- **Note:** AI RMF 1.0 itself does not name prompt injection; it is the *framework* that profiles (like AI 600-1) instantiate. Adversarial robustness lives under Measure (TEVV) and Manage (incident response).

### NIST AI 600-1 — Generative AI Profile

- **Version:** 1.0, July 26, 2024.
- **Source:** https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf
- **What it says about PI:** Identifies PI (direct/indirect), data poisoning, jailbreak, and information leakage as top GenAI risks. **MP-2.3-005** mandates pre- and post-deployment adversarial testing including red-team PI scenarios — not satisfied by vendor attestation alone.
- **Interview move:** Cite MP-2.3-005 to convert "we should red-team" into "we are required to red-team continuously."

### NIST AI Standards Zero-Drafts / TEVV

- **Version:** Outline released July 29, 2025; draft TEVV in public comment.
- **Source:** https://airc.nist.gov/
- **Companion:** https://www.nist.gov/ai-test-evaluation-validation-and-verification-tevv
- **Scope:** Codifies pre-deployment red-team PI testing protocols.

### ISO/IEC 42001:2023 — AI Management Systems

- **Version:** First edition, December 2023.
- **Source:** https://www.iso.org/standard/42001.html
- **Scope:** World's first **certifiable** AI Management System (AIMS).
- **What it says about PI:** Names prompt injection and tool abuse explicitly under adversarial-attacks; requires test plans covering "robustness, fairness, security and compliance," adversarial testing, and threat-modeling integration (STRIDE / DREAD / PASTA / LINDDUN / OWASP-for-ML).
- **Interview move:** Cite when discussing **certifiable** compliance — increasingly the procurement gate.

### ISO/IEC 23894:2023 — AI Risk Management Guidance

- **Version:** 2023.
- **Source:** https://www.iso.org/standard/77304.html
- **Scope:** AI-specific risk management; complements ISO 31000 + 42001 + 23053.

### ISO/IEC 27001 + draft ISO/IEC 27090 (AI Security)

- **Versions:** 27001:2022 baseline; **27090 in development** (OWASP AI Exchange contributing 70 pages).
- **Source:** https://www.iso.org/standard/27001
- **Scope:** 27090 expected to enumerate AI-specific threats with control mappings; harmonizes with NIST AI RMF and EU AI Act.

### MITRE ATLAS

- **Version:** v5.6.0 (May 4, 2026 — most recent at the time of this synthesis; v5.4.0 Feb 2026 + v5.5.0 March 2026 are intermediate). For current tactic / technique / sub-technique / mitigation / case-study counts, see https://atlas.mitre.org/ and https://github.com/mitre-atlas/atlas-data/releases — counts shift with each minor release.
- **Source:** https://atlas.mitre.org/
- **Companion:** https://github.com/mitre-atlas/atlas-data
- **Scope:** Adversary tactics-techniques-procedures knowledge base for AI/ML, ATT&CK-style.
- **What it says about PI:** Multiple techniques (direct LLM Jailbreak, indirect injection via retrieved content, MCP-channel injection added v5.3.0 January 2026). 2026 case studies include "Data Exfiltration via MCP Server used by Cursor" and "Data Destruction via Indirect Prompt Injection Targeting Claude Computer-Use." 2026 update shifts emphasis from model-centric to *execution-layer* (agentic) attacks.
- **Interview move:** Canonical TTP vocabulary — cite ATLAS technique IDs the way you would cite ATT&CK T-numbers.

### MITRE ATT&CK (AI-relevant techniques)

- **Source:** https://attack.mitre.org/
- **Relevant techniques:** T1659 (Content Injection), Initial Access vectors that ATLAS extends.

## Regulatory

`#regulatory`

The binding-regulation surface — laws and regulations with enforceable obligations.

### EU AI Act — Regulation (EU) 2024/1689

- **Version:** Final, OJ July 12, 2024; entry into force August 1, 2024; staged enforcement.
- **Source:** https://artificialintelligenceact.eu/
- **Companion:** https://eur-lex.europa.eu/eli/reg/2024/1689
- **Articles relevant to PI:**
  - **Article 9** — Risk management system for high-risk AI (continuous, lifecycle).
  - **Article 15** — *Accuracy, robustness, and cybersecurity* — explicitly names cybersecurity threats including data/model poisoning, adversarial examples, model evasion, and "confidentiality attacks." **Enforceable from 2 August 2026.**
  - **Article 55** — GPAI providers with systemic risk must perform model evaluations including adversarial testing and report serious incidents.
- **Interview move:** This is the **most aggressive binding regulation** on adversarial robustness. Cite Article 15 when an interviewer asks "what regulation actually requires us to harden against PI."

### EU GPAI Code of Practice

- **Source:** https://digital-strategy.ec.europa.eu/en/policies/guidelines-gpai-providers
- **Scope:** Voluntary GPAI Code signed by leading providers (OpenAI, Anthropic, Google, Microsoft, Meta, Mistral, Cohere) as compliance pathway under Article 56.

### US Executive Order 14179 (replaces 14110)

- **Status:** Biden EO 14110 (Oct 30, 2023) **revoked January 20, 2025** by Trump.
- **Replacement:** EO 14179 "Removing Barriers to American Leadership in AI," signed Jan 23, 2025.
- **Source:** https://www.federalregister.gov/documents/2025/01/31/2025-02172/removing-barriers-to-american-leadership-in-artificial-intelligence
- **Effect:** Pro-innovation; deregulatory; revoking Biden-era safety reporting and safety-test sharing requirements.
- **Interview move:** Acknowledge the regulatory vacuum at federal level *but* cite continuing NIST AISI activity, sector regulators (SEC, CFPB, FTC under Section 5), and state laws (Colorado AI Act, NYC bias audit).

### US AI Bill of Rights Blueprint (2022)

- **Publisher:** White House OSTP, October 2022.
- **Source:** https://bidenwhitehouse.archives.gov/ostp/ai-bill-of-rights/ (archived; original whitehouse.gov path removed after Jan 2025 transition)
- **Status:** Now archived (Biden-era); cited in some agency rulemaking.

### UK — AI Security Institute (AISI)

- **Status:** Renamed from AI **Safety** Institute → AI **Security** Institute Feb 2025.
- **Source:** https://www.aisi.gov.uk/
- **Scope:** Pre-deployment frontier-model evaluation; safety-case methodology; Inspect open-source eval framework (open-sourced May 2024).

### UK Frontier AI Safety Commitments

- **Bletchley Declaration** (Nov 2023): 28 countries.
- **Seoul Summit** (May 2024): 16 leading AI companies signed Frontier AI Safety Commitments.
- **Paris AI Action Summit** (Feb 2025): Pivoted toward action plans.

### China — Interim Measures for Generative AI Services

- **Effective:** August 15, 2023.
- **Source:** https://www.chinalawtranslate.com/en/generative-ai-interim/
- **Scope:** Mandates security assessments by CAC including content-control robustness; companion CAC standard "Basic Safety Requirements for Generative AI Services" defines test corpora.

### Canada — AIDA

- **Status:** Bill C-27 stalled when Parliament prorogued January 2025; not enacted.

### Singapore — IMDA Model AI Governance Framework

- **Versions:** Original 2020; GenAI Model Framework 2024; **Agentic AI MGF 2026**.
- **Source:** https://www.imda.gov.sg/about-imda/emerging-technologies-and-research/artificial-intelligence
- **Scope:** Agentic AI framework explicitly covers tool-use risks and indirect injection.

### Japan — AI Guidelines for Business + AI Promotion Act

- **Versions:** AI Guidelines v1.0 (April 2024), v1.1 (March 2025); AI Promotion Act passed May 28, 2025.
- **Scope:** Light-touch but globally coordinated; aligned with the Hiroshima AI Process (G7).

### South Korea — AI Basic Act

- **Status:** Signed January 21, 2025; **effective January 22, 2026**.
- **Scope:** First Asian comprehensive AI law; risk-tiered like the EU AI Act.

### Other notable

- **Brazil PL 2338/2023** (in legislative review); risk-tiered.
- **Colorado AI Act (2024)**: first US state comprehensive AI law.
- **NYC Local Law 144**: bias audits for automated employment-decision tools.
- **NIST AI 100-2** (Adversarial ML Taxonomy, Jan 2024 / 2nd ed Mar 2025): formal vocabulary for evasion / poisoning / oracle / abuse attacks; cross-references PI as evasion sub-class.

## Frontier-Lab Voluntary Frameworks

`#lab-frameworks`

The voluntary commitments and frameworks published by frontier AI labs.

### Anthropic Responsible Scaling Policy (RSP)

- **Versions:** v1.0 (Sep 2023), v2 (Oct 2024), **v3.0 (current)**.
- **Source:** https://www.anthropic.com/responsible-scaling-policy
- **Scope:** AI Safety Levels (ASL-1..N). **ASL-3 Deployment Standard activated May 2025** with Claude Opus 4 — requires constitutional-classifier-grade defenses. ASL-4 partially TBD pending interpretability research. RSP-2025 added a new CBRN capability threshold and disaggregated AI R&D thresholds.
- **Interview move:** Most concrete technical operationalization of "what robustness must look like at frontier scale."

### OpenAI Preparedness Framework

- **Versions:** v1 (Dec 2023), **v2 (April 15, 2025)**.
- **Source:** https://openai.com/index/updating-our-preparedness-framework/
- **Scope:** Categories — Biological/Chemical, Cybersecurity, AI Self-Improvement, plus Persuasion (handled via Model Spec). Five risk criteria. Internal Safety Advisory Group (SAG). Sister doc: **The Instruction Hierarchy** (Wallace et al. 2024).

### Google DeepMind Frontier Safety Framework (FSF)

- **Versions:** v1 (May 2024), **v2.0 (Feb 4, 2025)**, **v3.0 (Apr 17, 2026)**.
- **Source:** https://deepmind.google/blog/strengthening-our-frontier-safety-framework/
- **Scope:** Critical Capability Levels (CCLs) including new "harmful manipulation" CCL added in v3.0. Tracked Capability Levels (TCLs). Pairs with Gemini layered defense.

### Meta Frontier AI Framework

- **Version:** v1, February 3, 2025.
- **Source:** https://ai.meta.com/static-resource/meta-frontier-ai-framework/
- **Scope:** Outcomes-led — High Risk vs Critical Risk in Cyber / Chem-Bio / Loss-of-Control. Open-source-friendly with risk gating.

### Microsoft Responsible AI Standard v2

- **Version:** v2, June 2022; **2025 RAI Transparency Report** is the operational supplement.
- **Source:** https://www.microsoft.com/en-us/ai/responsible-ai
- **Scope:** Operationalized via Azure AI Content Safety Prompt Shields, **Spotlighting** (Build 2025), and PyRIT for red-teaming.

### xAI Risk Management Framework

- **Status:** Draft, February 20, 2025.
- **Source:** https://data.x.ai/2025.02.20-RMF-Draft.pdf
- **Scope:** Two categories — malicious use, loss-of-control. Quantitative thresholds for CBRN. 2025 controversy: Grok image-generation deepfake failure triggered EU / Malaysia / Indonesia / India action.

### Cohere

- **Scope:** Enterprise-private deployment focus (North); GPAI Code of Practice signatory.
- **FLI AI Safety Index 2025:** graded **C-**.

### Frontier Model Forum (FMF)

- **Status:** Launched 2023 (Anthropic, Google, Microsoft, OpenAI; Meta added 2024).
- **Source:** https://www.frontiermodelforum.org/
- **Scope:** Cross-lab harmonization; comments on NIST TEVV draft.

### METR Frontier Safety Policy Tracker

- **Source:** https://metr.org/fsp
- **Scope:** Independent comparative tracker of frontier-lab voluntary frameworks.

## Industry Research Reports

`#industry-reports`

System cards, safety reports, and adversarial-robustness research published by frontier labs and security vendors. Grouped by publisher.

### Anthropic

- **Constitutional Classifiers** — Jan 2025. https://arxiv.org/abs/2501.18837 — Synthetic-data-trained classifier guardrails using a natural-language constitution; 3,000+ red-team hours found no universal jailbreak. → Also see `03_defenses.md` § C1.
- **Constitutional Classifiers++** — Jan 2026. https://arxiv.org/abs/2601.04603 — Two-stage cascade with linear probes; 40× compute reduction, 0.05% production refusal rate. → Also see `03_defenses.md` § C1.
- **Many-shot Jailbreaking** — April 2024. https://www.anthropic.com/research/many-shot-jailbreaking — Long-context attack: 100s of faux dialogue turns override safety training. → Also see `01_direct_attacks.md` § A2.
- **Sleeper Agents** — Jan 2024. https://arxiv.org/abs/2401.05566 — Backdoored models survive RLHF; probes can detect. → Also see `04_training_time_threats.md` § D1.
- **Simple Probes Catch Sleeper Agents** — April 2024. https://www.anthropic.com/research/probes-catch-sleeper-agents — Linear probes on residual stream detect deceptive activations. → Also see `04_training_time_threats.md` § D6.
- **Persistent Pre-training Poisoning** — Oct 2025. https://alignment.anthropic.com/2025/persistent-pretraining-poisoning/ — Pre-training data poisoning persists through fine-tuning. → Also see `04_training_time_threats.md` § D2.
- **Petri (Parallel Exploration Tool for Risky Interactions)** — Oct 2025; 2.0 (2026). https://alignment.anthropic.com/2025/petri/ — Open-source automated multi-turn auditing agent.
- **Building & Evaluating Alignment Auditing Agents** — 2025. https://alignment.anthropic.com/2025/automated-auditing/ — LLM-based auditors automate alignment workflows.
- **AuditBench** — 2026. https://alignment.anthropic.com/2026/auditbench/ — 56 models with implanted hidden behaviors as audit benchmark.
- **Claude 3.5 Sonnet Model Card Addendum** — Oct 2024. PDF — Computer-use prompt-injection mitigations.
- **Claude 3.7 Sonnet System Card** — Feb 2025. https://www.anthropic.com/claude-3-7-sonnet-system-card — Computer-use defenses; ~600-scenario PI evaluation.
- **Claude 4 (Opus 4 + Sonnet 4) System Card** — May 2025. https://www.anthropic.com/claude-4-system-card — ASL-3 activation; extended PI evaluation; agentic-safety details.
- **Anthropic Model Safety Bug Bounty (CC++)** — May 2025. https://www.anthropic.com/news/testing-our-safety-defenses-with-a-new-bug-bounty-program — Up to $25K for universal jailbreaks. → Also see `05_datasets_and_benchmarks.md` § CTFs.

### OpenAI

- **The Instruction Hierarchy** — April 2024 (ICLR 2025). https://arxiv.org/abs/2404.13208 — System > developer > user > tool ordering trained into the model. → Also see `03_defenses.md` § C3.
- **Preparedness Framework v2** — April 15, 2025. PDF — Tracked-category capability thresholds; SAG governance.
- **OpenAI's Approach to External Red Teaming** — March 2025. https://arxiv.org/abs/2503.16431 — Red-team composition, access tiers, methodology.
- **GPT-4o System Card** — Aug 2024. https://openai.com/index/gpt-4o-system-card — Multi-modality red-teaming including PI.
- **GPT-4.5 System Card** — Feb 27, 2025. PDF — 99% human-jailbreak resistance metric.
- **OpenAI o1 System Card** — Sep 2024. https://openai.com/index/openai-o1-system-card — StrongREJECT / chain-of-thought safety.
- **GPT-5 System Card** — Aug 13, 2025. PDF — 5,000+ hours external red-teaming.
- **ChatGPT Agent / Operator System Cards** — 2025. PDFs — Computer-use agent PI defenses.
- **Detecting and Reducing Scheming (× Apollo)** — 2025. https://openai.com/index/detecting-and-reducing-scheming-in-ai-models — Deliberative alignment training reduces scheming.

### Apollo Research

- **Frontier Models Are Capable of In-Context Scheming** — Dec 2024. https://arxiv.org/abs/2412.04984 — 5/6 frontier models showed scheming; o1 most persistent.
- **More Capable Models Are Better at Scheming** — 2025. https://www.apolloresearch.ai/blog — Capability-vs-safety scaling.
- **Stress Testing Deliberative Alignment** — 2025. https://www.apolloresearch.ai/research — Methodology for hardening against learned deception.

### Google DeepMind

- **Lessons from Defending Gemini Against Indirect PI** — May 2025. https://arxiv.org/abs/2505.14534 — Adversarial training plus layered classifier results. → Also see `03_defenses.md` § C3.
- **Gemini 2.5 Technical Report** — 2025. PDF — Security adversarial training added in 2.5.
- **ShieldGemma technical report** — July 2024. https://arxiv.org/abs/2407.21772 — Open-weights safety classifier. → Also see `03_defenses.md` § C1, `06_tools_and_vendors.md` § OSS-classifiers.
- **Gemini 2.5 Computer Use Model Card** — Oct 2025. PDF — Agentic PI evaluation suite.

### Microsoft

- **Crescendo Multi-Turn LLM Jailbreak** — April 2024. https://arxiv.org/abs/2404.01833 — Gradual benign-to-harmful escalation. → Also see `01_direct_attacks.md` § A2.
- **PyRIT (Python Risk Identification Tool)** — 2024+. https://github.com/microsoft/PyRIT — Open red-team automation framework. → Also see `06_tools_and_vendors.md` § OSS-RT-runners.
- **Spotlighting** — 2024 (expanded Build 2025). https://arxiv.org/abs/2403.14720 — Mark untrusted input via delimiting / datamarking / encoding. → Also see `02_indirect_and_agentic_attacks.md` § B1, `03_defenses.md` § C3.
- **Microsoft Security Blog: AI Red Team series** — 2024–2026. https://www.microsoft.com/en-us/security/blog — Skeleton Key, agent-hijack, prompt-shield evolution.
- **EchoLeak (CVE-2025-32711) disclosure** — June 2025. https://arxiv.org/abs/2509.10540 — Zero-click indirect PI in M365 Copilot; CVSS 9.3. → Also see `02_indirect_and_agentic_attacks.md` § B1.

### Meta

- **Llama Guard 3 + Vision model card** — 2024. https://www.llama.com/docs/model-cards-and-prompt-formats/llama-guard-3 — Safety classifier MLCommons-aligned. → Also see `03_defenses.md` § C1, `06_tools_and_vendors.md` § OSS-classifiers.
- **Llama Guard 4 model card** — 2025. https://www.llama.com/docs/model-cards-and-prompt-formats/llama-guard-4 — Multimodal 12B safety classifier.
- **Prompt Guard 2 model card** — 2025. https://www.llama.com/docs/model-cards-and-prompt-formats/prompt-guard — mDeBERTa multilingual injection / jailbreak classifier.

### Industry / Vendor Reports

- **Lakera 2025 GenAI Security Readiness Report** — Lakera, 2025. https://www.lakera.ai/genai-security-report-2025 — 15% incident rate; PI / data-leakage / bias dominant.
- **Lakera "Year of the Agent" Q4 2025 report** — Lakera, early 2026. https://www.lakera.ai/blog (specific slug `the-year-of-the-agent` returns 404 as of May 2026; report linked from blog index) — Indirect PI requires fewer attempts than direct.
- **Gandalf the Red: Adaptive Security for LLMs** — Lakera, Jan 2025. https://arxiv.org/abs/2501.07927 — Game-derived 279K prompt-attack dataset.
- **HiddenLayer 2026 AI Threat Landscape Report** — HiddenLayer, March 18, 2026. https://hiddenlayer.com/report-and-guide/threatreport2026 — vendor-survey report covering agentic-breach prevalence; 76% of respondents say shadow AI is a definite or probable problem.
- **HiddenLayer 2025 AI Threat Landscape Report** — HiddenLayer, early 2025. https://hiddenlayer.com/report-and-guide/ai-threat-landscape-report-2025 — Year-prior baseline.
- **Cisco AI Defense (RI) — Algorithmic Red Teaming** — Cisco, Jan 2025 + Feb 2026. https://blogs.cisco.com/ai/security-for-the-agentic-era-cisco-ai-defense-breaks-new-ground — Adaptive multi-turn algorithmic red-team in <20 min.
- **MITRE ATLAS Case Studies (v5.x)** — MITRE, Continuous. https://atlas.mitre.org/ (case studies under /studies sub-path) — 42+ real-world incidents including EchoLeak, Cursor MCP.
- **UK AISI: Inspect Evals + Sandboxing Toolkit** — UK AISI, May 2024 + ongoing. https://www.aisi.gov.uk/blog/inspect-evals — Open eval framework now industry standard for pre-deployment.
- **UK AISI: Example Safety Case for Misuse Safeguards** — UK AISI, 2025. https://www.aisi.gov.uk/research/emerging-practices-in-frontier-ai-safety-frameworks — Structured-argument template for misuse safety cases.
- **NIST ARIA program** — NIST, 2024+. https://airc.nist.gov/ — Societal-impact + TEVV pilot studies.
- **Future of Life AI Safety Index 2025** — FLI, July 2025. https://futureoflife.org/ — Independent grading of major labs.

## Compliance posture

`#compliance-posture`

The synthesized compliance picture as of May 2026.

**De facto compliance reference:** **NIST AI 600-1 + ISO/IEC 42001** is the practical pair. Enterprises use 600-1 for risk-category coverage (especially MP-2.3-005 mandate for adversarial testing) and 42001 for the certifiable management system that procurement teams demand. **OWASP LLM Top 10 (2025)** is the application-developer's working checklist. **MITRE ATLAS** is the TTP vocabulary.

**Most aggressive on adversarial robustness:** **EU AI Act**. Article 15 enforcement begins **2 August 2026** for high-risk systems and explicitly names cybersecurity threats including data poisoning, model poisoning, adversarial examples, model evasion, and confidentiality attacks. Article 55 imposes systemic-risk evaluations on GPAI providers. China's CAC algorithm registration is more invasive on content control but narrower on adversarial robustness. Post-EO 14110 revocation, the US federal regime has retreated to voluntary NIST guidance plus state laws.

**Widest gap voluntary vs binding:** **agentic / computer-use AI**. Labs (Anthropic RSP v3, OpenAI Preparedness v2, DeepMind FSF v3, Meta) are 12–18 months ahead of every binding regulation on agentic threats. EchoLeak (CVE-2025-32711) was the first production-grade zero-click indirect-PI exploit and lives in this gap. EU AI Act, NIST 600-1, and ISO 42001 all predate the agentic transition.

## Standards landscape May 2026

`#landscape-2026`

What an interviewee should know:

1. **Layered defense stack:** Instruction Hierarchy + Constitutional Classifiers / Llama Guard / ShieldGemma / Prompt Guard + Spotlighting + content-classifier guardrails + sandbox isolation + human-in-the-loop for high-risk actions.
2. **Direct vs indirect PI** — and why indirect is harder (untrusted-data origin is the load-bearing problem).
3. **Regulatory chain of authority:** voluntary RSPs (Anthropic) → Seoul Frontier AI Safety Commitments → ISO 42001 cert → NIST 600-1 TEVV → EU AI Act Article 15 enforcement.
4. **2026 agentic shift:** ATLAS v5.3+, Anthropic Petri, DeepMind FSF v3.0, Meta loss-of-control, Singapore Agentic AI MGF.
5. **One real CVE:** EchoLeak (CVE-2025-32711) — XPIA bypass, Markdown reference exfiltration, Teams-proxy abuse.

## Verification notes

- Several lab-framework version numbers and dates are fast-moving; re-verify on use.
- Industry reports change quarterly; URLs are stable but contents update — treat numerical claims as approximate without primary verification.
- Anthropic alignment-science blog URLs (`alignment.anthropic.com/...`) are stable for the reports listed.

**Total entries in this file:** 11 standards frameworks + 15 regulatory entries + 9 frontier-lab voluntary frameworks + 47 industry research reports (12 Anthropic + 9 OpenAI + 3 Apollo + 4 DeepMind + 5 Microsoft + 3 Meta + 11 Industry/Vendor) = **82 entries**.

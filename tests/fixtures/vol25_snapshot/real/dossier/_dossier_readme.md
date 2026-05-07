# Vol 25 — Prompt Injection & Adversarial Prompts: Research Dossier

**Compiled:** 2026-05-05 | **Coverage cutoff:** May 2026
**Purpose:** Comprehensive citation foundation for `vol25_prompt_injection/` (Vol 25 of the interview prep series). Every claim in the volume should anchor here; every citation should be one of the entries in `01_attacks_direct.md` … `07_standards_industry.md`.

---

## Quick stats

| Artifact | Count |
|----------|-------|
| Total verified entries across all notes | **~520** (papers + datasets + tools + standards) |
| Papers (attacks + defenses + training-time + privacy) | **~290** with arXiv IDs |
| Datasets / benchmarks | **45** with HF/GitHub URLs |
| Leaderboards | **9** with current state |
| CTFs / red-team programs | **11** with eligibility/status |
| Open-source tools | **45** with stars/license/last-release |
| Commercial vendors | **31** with funding/acquisition status |
| Eval SaaS platforms | **10** |
| Standards frameworks | **12** with PI/adv-robustness summaries |
| Regulatory regimes | **15+** including EU/US/UK/CN/SG/JP/KR |
| Frontier-lab voluntary frameworks | **8** (Anthropic, OpenAI, DeepMind, Meta, Microsoft, xAI, Cohere, FMF) |
| Industry research reports / system cards | **40+** |
| **Cached PDF papers** | **35** (`papers/` directory, ~115MB) |

---

## Directory layout

```
docs/research/vol25_prompt_injection/
├── README.md                                       (this file)
├── papers/                                         35 cached PDFs of canonical anchor papers
├── 01_attacks_direct.md                            72 entries: hand-crafted, encoding, white-box, black-box
├── 02_attacks_indirect_agentic_multimodal.md       82 entries: indirect, agentic, multimodal, computer-use
├── 03_defenses.md                                  ~80 entries: detection, smoothing, architectural, latent, alignment
├── 04_training_time_threats.md                     60 entries: backdoors, poisoning, extraction, MIA, model stealing
├── 05_datasets_benchmarks.md                       45 datasets + 9 leaderboards + 11 CTFs
├── 06_tools_vendors.md                             45 OSS + 31 commercial + 10 eval SaaS
└── 07_standards_industry.md                        12 standards + 15 regulatory + 8 lab frameworks + 40 reports
```

---

## How to use

### When drafting a Vol 25 chapter
Before writing each LOS, find the anchor citation(s) in the relevant notes file. The notes are organized to mirror Vol 25's six parts:

| Vol 25 Part | Primary notes file(s) |
|-------------|----------------------|
| Part I — Threat model & vocabulary (Ch 1-2) | `07_standards_industry.md` (OWASP/MITRE/NIST sections) |
| Part II — Direct attacks (Ch 3-5) | `01_attacks_direct.md` |
| Part III — Indirect/agentic/multimodal (Ch 6-8) | `02_attacks_indirect_agentic_multimodal.md` |
| Part IV — Inference-time defenses (Ch 9-11) | `03_defenses.md` (C1-C3 sections) |
| Part V — Training-time threats (Ch 12-14) | `03_defenses.md` (C4-C5 sections) + `04_training_time_threats.md` |
| Part VI — Eval & operations (Ch 15-17) | `05_datasets_benchmarks.md` + `06_tools_vendors.md` + `03_defenses.md` (C6 adaptive-attack section) |

### When `references.bib` is being authored
Cross-walk the entries here to BibTeX. Anchor IDs (arXiv:XXXX.YYYYY) are the BibTeX `eprint` field. For each entry I've listed:
- Authors / year
- Venue
- arXiv ID (or DOI for non-arXiv work)
- GitHub URL (for code/data artifacts)
- HuggingFace URL (for datasets)
- License (for redistributable artifacts)

### When verifying a claim
Spot-check the arXiv ID by visiting `arxiv.org/abs/{ID}` before quoting numbers in chapter prose. The `(unverified)` flag in each notes file marks entries that need pre-citation re-verification.

---

## Cached papers (`papers/`)

35 anchor PDFs, downloaded from arxiv.org May 2026:

### Foundational attacks
- `gcg_zou_2023.pdf` — GCG (arXiv:2307.15043)
- `autodan_liu_2023.pdf` — AutoDAN (arXiv:2310.04451)
- `pair_chao_2023.pdf` — PAIR (arXiv:2310.08419)
- `houyi_liu_2023.pdf` — HouYi (arXiv:2306.05499)
- `hackaprompt_schulhoff_2023.pdf` — HackAPrompt (arXiv:2311.16119)
- `crescendo_microsoft_2024.pdf` — Crescendo (arXiv:2404.01833)
- `adaptive_attacks_andriushchenko_2024.pdf` — Adaptive Attacks (arXiv:2404.02151)
- `universal_jailbreak_backdoors_rando_2023.pdf` — Universal Jailbreak Backdoors (arXiv:2311.14455)

### Indirect / multimodal / agentic attacks
- `greshake_indirect_pi_2023.pdf`, `ipi_greshake_2023.pdf` — Greshake et al. indirect PI (arXiv:2302.12173)
- `visual_adv_qi_2023.pdf` — Visual Adversarial Examples (arXiv:2306.13213)
- `agentdojo_debenedetti_2024.pdf` — AgentDojo (arXiv:2406.13352)
- `agentharm_andriushchenko_2024.pdf` — AgentHarm (arXiv:2410.09024)

### Defenses
- `constitutional_ai_bai_2022.pdf` — Constitutional AI (arXiv:2212.08073)
- `constitutional_classifiers_anthropic_2025.pdf` — Constitutional Classifiers (arXiv:2501.18837)
- `instruction_hierarchy_openai_2024.pdf` — Instruction Hierarchy (arXiv:2404.13208)
- `spotlighting_microsoft_2024.pdf` — Spotlighting (arXiv:2403.14720)
- `circuit_breakers_zou_2024.pdf` — Circuit Breakers (arXiv:2406.04313)
- `camel_deepmind_2025.pdf` — CaMeL (arXiv:2503.18813)
- `refusal_direction_arditi_2024.pdf` — Refusal Direction (arXiv:2406.11717)
- `struq_chen_2024.pdf` — StruQ (arXiv:2402.06363)
- `secalign_chen_2024.pdf` — SecAlign (arXiv:2410.05451)
- `smoothllm_robey_2023.pdf` — SmoothLLM (arXiv:2310.03684)
- `wildguard_ai2_2024.pdf` — WildGuard (arXiv:2406.18495)
- `shieldgemma_google_2024.pdf` — ShieldGemma (arXiv:2407.21772)
- `bipia_yi_2023.pdf` — BIPIA (arXiv:2312.14197)
- `open_prompt_injection_liu_2024.pdf` — Open-Prompt-Injection (arXiv:2310.12815)

### Training-time threats
- `sleeper_agents_hubinger_2024.pdf` — Sleeper Agents (arXiv:2401.05566)
- `anthropic_poisoning_2025.pdf` — 250-doc poisoning (arXiv:2510.07192)
- `carlini_training_data_extraction_2021.pdf` — Foundational extraction (arXiv:2012.07805)

### Evaluation
- `harmbench_mazeika_2024.pdf` — HarmBench (arXiv:2402.04249)
- `jailbreakbench_chao_2024.pdf` — JailbreakBench (arXiv:2404.01318)
- `llm_as_judge_zheng_2023.pdf` — MT-Bench / LLM-as-judge (arXiv:2306.05685)
- `decodingtrust_wang_2023.pdf` — DecodingTrust (arXiv:2306.11698)
- `trustllm_sun_2024.pdf` — TrustLLM (arXiv:2401.05561)

---

## Canonical citation cheat-sheet (per Vol 25 chapter section)

If forced to pick the **single highest-leverage citation** for a topic:

| Vol 25 topic | Anchor citation | arXiv ID |
|--------------|-----------------|----------|
| Direct PI taxonomy | Perez & Ribeiro 2022 "Ignore Previous Prompt" | 2211.09527 |
| Indirect PI | Greshake et al. 2023 | 2302.12173 |
| Encoding/obfuscation | Yong et al. 2023 (low-resource) + Jiang 2024 (ArtPrompt) | 2310.02446 + 2402.11753 |
| White-box optimization | GCG (Zou et al. 2023) | 2307.15043 |
| Black-box optimization | PAIR (Chao et al. 2023) | 2310.08419 |
| Multi-turn jailbreak | Crescendo (Microsoft 2024) | 2404.01833 |
| Many-shot jailbreak | Anil et al. (Anthropic 2024) | (Anthropic PDF) |
| Reasoning-model attacks | H-CoT 2025 + J2 2025 | 2502.12893 + 2502.09638 |
| Agent benchmark | AgentDojo (Debenedetti 2024) | 2406.13352 |
| Agent harmfulness | AgentHarm (UK AISI 2024) | 2410.09024 |
| Multimodal jailbreak | Qi 2023 "Visual Adversarial" | 2306.13213 |
| Computer-use defense | Anthropic browser-use safeguards 2025 + BrowseSafe (2025) | 2511.20597 |
| Real-world incident | EchoLeak CVE-2025-32711 | 2509.10540 |
| Detection (input classifier) | Llama Guard 3 (2024) | 2407.21783 |
| Detection (output classifier) | WildGuard (AI2 2024) | 2406.18495 |
| Detection (constitution-driven) | Constitutional Classifiers (Anthropic 2025) | 2501.18837 |
| Smoothing defense | SmoothLLM (Robey 2023) | 2310.03684 |
| Architectural defense | Spotlighting (Hines 2024) + Instruction Hierarchy (Wallace 2024) | 2403.14720 + 2404.13208 |
| Capability/dataflow control | CaMeL (DeepMind 2025) | 2503.18813 |
| Latent-space defense | Circuit Breakers (Zou 2024) | 2406.04313 |
| Refusal mediation | Arditi 2024 (refusal direction) | 2406.11717 |
| Alignment-as-defense | Constitutional AI (Bai 2022) | 2212.08073 |
| Adaptive-attack methodology | Andriushchenko et al. 2024 + Wallace/Tramèr 2025 | 2404.02151 + 2510.09023 |
| Eval methodology | HarmBench (Mazeika 2024) + StrongREJECT (Souly 2024) | 2402.04249 + 2402.10260 |
| LLM-as-judge | MT-Bench (Zheng 2023) | 2306.05685 |
| Sleeper agents / persistence | Hubinger et al. 2024 | 2401.05566 |
| Pre-training poisoning | Anthropic 250-doc (2025) | 2510.07192 |
| Training-data extraction | Carlini et al. 2021 + Nasr et al. 2023 | 2012.07805 + 2311.17035 |
| PII memorization | Lukas 2023 + PII-Scope 2024 | 2302.00539 + 2410.06704 |
| Standards (working checklist) | OWASP LLM Top 10 2025 | (genai.owasp.org) |
| Standards (TTP vocab) | MITRE ATLAS v5.4 | (atlas.mitre.org) |
| Standards (TEVV mandate) | NIST AI 600-1 | (NIST.AI.600-1.pdf) |
| Regulation (binding) | EU AI Act Art 15 | (Reg 2024/1689) |
| Lab framework | Anthropic RSP v3 | (anthropic.com/responsible-scaling-policy) |

---

## Verification policy

Every entry in the notes files is one of:
- **Verified** — arXiv ID confirmed against arxiv.org abstract page or canonical conference proceedings URL
- **`(unverified)`** — paper exists per search results, but ID/authorship/venue not directly retrieved this session; spot-check before citation

Numerical claims (ASR percentages, dataset sizes, model counts) come from primary search-result extracts. Treat them as approximations until confirmed against the original paper.

Date-sensitive claims (post-2025) carry highest re-verification priority — the field moves quarterly.

---

## Updates and maintenance

- **Coverage cutoff**: May 2026
- **Refresh cadence target**: every 6 months for Parts II-III (attacks/defenses move fastest); every 12 months for Parts I/V/VI (frameworks/training-time/evals are stabler)
- **Re-cache PDFs**: when a referenced paper updates a major version on arXiv, refresh the cached PDF in `papers/`

To extend the dossier, add new entries to the relevant notes file using the existing schema and update the counts in this README's "Quick stats" table.

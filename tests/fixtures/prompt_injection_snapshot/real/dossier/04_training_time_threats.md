# Training-Time Threats and LLM Privacy Attack Research

**Compiled:** May 2026 | **Coverage:** 2018-2026 (foundational); 2022-2026 (LLM-specific); emphasis 2024-2026
**Verification:** every arXiv ID confirmed against arxiv.org or primary venue unless `(unverified)`. See verification footer.

---

## D1. Backdoors / Sleeper Agents in LLMs

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | Threat surface |
|-------|----------------|-------|-----------|--------|---------------|
| **Sleeper Agents**: Deceptive LLMs Persisting Through Safety Training | Hubinger, Denison et al. (Anthropic 2024) | arXiv | arXiv:2401.05566 | anthropics/sleeper-agents-paper | training data corruption — survives SFT/RL/adversarial training |
| **BadChain**: Backdoor Chain-of-Thought | Xiang et al. (2024) | ICLR 2024 | arXiv:2401.12242 | Django-Jiang/BadChain | inference-time prompt corruption (no training access); 97% ASR on GPT-4 |
| **BadAgent**: Backdoors in LLM Agents | Wang, Xue et al. (2024) | ACL 2024 | arXiv:2406.03007 | DPamK/BadAgent | fine-tuning data corruption + tool-use |
| **BadNets**: Foundational ML Backdoor Paper | Gu, Dolan-Gavitt, Garg (2017) | MLSec / arXiv | arXiv:1708.06733 | — | training data corruption — conceptual ancestor |
| Trojaning Attack on Neural Networks | Liu et al. (2018) | NDSS 2018 | DOI:10.14722/ndss.2018.23291 | PurduePAML/TrojanNN | weight modification + retraining |
| **RIPPLeS**: Weight Poisoning of Pre-trained Models | Kurita, Michel, Neubig (2020) | ACL 2020 | arXiv:2004.06660 | neulab/RIPPLe | pre-trained-weight supply chain |
| **ProAttack**: Prompt as Backdoor Trigger | Zhao et al. (2023) | EMNLP 2023 | arXiv:2305.01219 | — | training data corruption (clean-label) |
| BadPrompt: Backdoors on Continuous Prompts | Cai et al. (2022) | NeurIPS 2022 | arXiv:2211.14719 | papersPapers/BadPrompt | prompt-tuning data corruption |
| **AutoPoison**: Exploitability of Instruction Tuning | Shu et al. (2023) | NeurIPS 2023 | arXiv:2306.17194 | azshue/AutoPoison | instruction-tuning data corruption |
| Instructions as Backdoors | Xu et al. (2023) | NAACL 2024 | arXiv:2305.14710 | cnut1648/instruction-attack | instruction-tuning corruption (instructions as triggers) |
| **VPI**: Virtual Prompt Injection Backdoors | Yan et al. (2023) | NAACL 2024 | arXiv:2307.16888 | poison-llm.github.io | instruction-tuning corruption; 0.1% poisoning → 40% bias |
| **CBA**: Composite Backdoor Attacks | Huang et al. (2023) | NAACL Findings 2024 | arXiv:2310.07676 | — | training data corruption (stealth); 100% ASR with ~3% poisoning |
| **BadEdit**: Backdooring via Model Editing | Li et al. (2024) | ICLR 2024 | arXiv:2403.13355 | — | weight modification (post-training); 15 samples |
| **Universal Jailbreak Backdoors from Poisoned Human Feedback** | Rando & Tramèr (2023) | ICLR 2024 | arXiv:2311.14455 | ethz-spylab/rlhf-poisoning | RLHF data corruption; ≥5% poisoned → universal "sudo" trigger |
| **BadGPT**: Backdoor Reward Model in InstructGPT | Shi et al. (2023) | NDSS Poster 2023 | arXiv:2304.12298 | — | reward-model (RLHF) corruption |
| **NOTABLE**: Transferable Backdoors Against Prompt-based Models | Mei et al. (2023) | ACL 2023 | arXiv:2305.17826 | — | encoder-weight corruption; transferable downstream |
| **Backdoor Token Unlearning** (BTU) | Jin et al. (2025) | AAAI 2025 | arXiv:2501.03272 | XDJPH/Backdoor-Token-Unlearning | defense (training-time) |
| **BackdoorLLM**: Comprehensive Benchmark | Li et al. (2024) | NeurIPS 2025 D&B | arXiv:2408.12798 | bboylyg/BackdoorLLM | benchmark / evaluation |

---

## D2. Data Poisoning Attacks

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | Threat surface |
|-------|----------------|-------|-----------|--------|---------------|
| **Persistent Pre-training Poisoning** (250-doc result) | Souly, Rando, Chapman et al. (Anthropic+UK AISI+Turing 2025) | arXiv | arXiv:2510.07192 | — | pre-training data corruption — THE 2025 result; 250 docs compromise 600M-13B |
| **Persistent Pre-Training Poisoning** | Zhang, Rando, Evtimov, Chi, Smith, Carlini, Tramèr, Ippolito (2024) | arXiv | arXiv:2410.13722 | — | 0.1% pre-training poison persists through SFT+DPO |
| **Poisoning Web-Scale Training Datasets is Practical** | Carlini, Jagielski et al. (2023) | IEEE S&P 2024 | arXiv:2302.10149 | — | web-crawl supply chain; ~$60 to poison 0.01% of LAION-400M |
| Concealed Data Poisoning Attacks on NLP | Wallace, Zhao, Feng, Singh (2020) | NAACL 2021 | arXiv:2010.12563 | Eric-Wallace/data-poisoning | training data corruption (poisons w/o trigger word) |
| AutoPoison | Shu et al. (2023) | NeurIPS 2023 | arXiv:2306.17194 | azshue/AutoPoison | instruction-tuning corruption (oracle-LLM-driven) |
| **Poisoning Language Models During Instruction Tuning** | Wan, Wallace et al. (2023) | ICML 2023 | arXiv:2305.00944 | AlexWan0/Poisoning-Instruction-Tuned-Models | 100 poison examples corrupt instruction-tuned LMs |
| **GBTL**: Gradient-Guided Backdoor Trigger Learning | Qiang et al. (2024) | arXiv | arXiv:2402.13459 | — | SFT data corruption; 1% of 4K → 80% performance drop |
| **PoisonGPT**: LLM Supply Chain | Mithril Security (2023) | Industry blog | (no arXiv) `(unverified)` | (unofficial) | model-zoo supply chain (typosquatted "EleuterAI") |
| **ROME**: Rank-One Editing (technique behind PoisonGPT) | Meng et al. (2022) | NeurIPS 2022 | arXiv:2202.05262 | rome.baulab.info | weight modification |
| Open Problems and Limitations of RLHF (Casper) | Casper et al. (2023) | TMLR 2023 | arXiv:2307.15217 | — | RLHF threat-model survey |
| **RLHFPoison**: Reward Poisoning | Wang et al. (2023) | arXiv | arXiv:2311.09641 | — | RLHF reward-model corruption |
| Is poisoning a real threat to LLM alignment? (DPO/PPO) | Pathmanathan et al. (2024) | arXiv | arXiv:2406.12091 | — | DPO needs ~0.5% vs PPO ~4% poisoned data |
| **PoisonBench** | Fu et al. (2024) | arXiv | arXiv:2410.08811 | TingchenFu/PoisonBench | benchmark; log-linear poison-effect law |
| **PoisonedRAG** | Zou et al. (2024) | USENIX Security 2025 | arXiv:2402.07867 | — | indirect / retrieval data corruption |
| **Best-of-Venom**: RLHF Preference Data Injection | Baumgärtner et al. (2024) | arXiv | arXiv:2404.05530 | — | RLHF data corruption; 15% poison-rate suffices |

---

## D3. Training Data Extraction

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | Threat surface |
|-------|----------------|-------|-----------|--------|---------------|
| **Extracting Training Data from LLMs** (foundational) | Carlini, Tramèr, Wallace et al. (2021) | USENIX Security 2021 (Distinguished Paper) | arXiv:2012.07805 | ftramer/LM_Memorization | inference-time extraction (open weights) |
| **Quantifying Memorization** Across Neural LMs | Carlini, Ippolito et al. (2022) | ICLR 2023 | arXiv:2202.07646 | ethz-spylab/lm_memorization_data | three log-linear scaling laws (capacity × duplication × context) |
| **Scalable Extraction from Production LMs** ("repeat poem") | Nasr, Carlini et al. (2023) | (preprint) | arXiv:2311.17035 | — | API-based extraction; 150× rate; gigabytes from production |
| **PII Leakage in LMs** | Lukas et al. (2023) | IEEE S&P 2023 | arXiv:2302.00539 | — | PII inference-time extraction |
| **PII-Scope**: Comprehensive PII Extraction Study | Nakka et al. (2024) | arXiv | arXiv:2410.06704 | — | PII attack benchmark |
| **The Secret Sharer** (foundational) | Carlini, Liu, Erlingsson, Kos, Song (2019) | USENIX Security 2019 | arXiv:1802.08232 | — | memorization audit (canaries) |
| Extracting Training Data from Diffusion Models | Carlini et al. (2023) | USENIX Security 2023 | arXiv:2301.13188 | — | diffusion analog (context for LLMs) |
| Special Characters Attack | Bai et al. (2024) | arXiv | arXiv:2405.05990 | — | API extraction (special-char triggers); 2-10× leakage |
| **Pandora's White-Box**: Precise Training Data Detection | Wang et al. (2024) | arXiv (later USENIX 2024) | arXiv:2402.17012 | pandora-llm.readthedocs.io | white-box MIA + fine-tune extraction; >50% of FT data extractable |
| **Deduplicating Training Data Makes LMs Better** | Lee et al. (2021) | ACL 2022 | arXiv:2107.06499 | — | training-data hygiene; 10× verbatim emission reduction |
| Probabilistic Memorization Measurement | Hayes et al. (2024) | arXiv | arXiv:2410.19482 | — | memorization metric refinement |
| **How Much Do Language Models Memorize?** | Morris, Cooper et al. (2025) | arXiv | arXiv:2505.24832 | — | GPT-style models ~3.6 bits/parameter capacity |
| Extracting Books from Production Language Models | Ahmed et al. (2026) | arXiv | arXiv:2601.02671 | — | Near-verbatim copyright-book extraction from Gemini 2.5 Pro / Grok 3 / Claude 3.7 / GPT-4.1 |

---

## D4. Membership Inference Attacks (MIA) on LLMs

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | Threat surface |
|-------|----------------|-------|-----------|--------|---------------|
| MIA on ML: A Survey (foundational) | Hu et al. (2021) | ACM CSUR 2022 | arXiv:2103.07853 | — | survey |
| MIA on Masked LMs | Mireshghallah et al. (2022) | EMNLP 2022 | arXiv:2203.03929 | — | MIA against MLMs (clinical-notes susceptibility) |
| **LiRA**: MIA From First Principles | Carlini et al. (2022) | IEEE S&P 2022 | arXiv:2112.03570 | — | foundational MIA methodology; shadow-model likelihood-ratio |
| **Min-K%** Pretraining-Data Detection | Shi et al. (2023) | ICLR 2024 | arXiv:2310.16789 | swj0419/detect-pretrain-code | MIA on pre-trained LLMs; WikiMIA benchmark |
| **Min-K%++** | Zhang et al. (2024) | ICLR 2025 (Spotlight) | arXiv:2404.02936 | zjysteven/mink-plus-plus | MIA refinement; +6-10% AUROC on WikiMIA |
| Neighbourhood Comparison MIA (Mattern) | Mattern et al. (2023) | ACL Findings 2023 | arXiv:2305.18462 | — | reference-free MIA |
| **SPV-MIA**: Practical MIA Against Fine-tuned LLMs | Fu et al. (2023) | NeurIPS 2024 | arXiv:2311.06062 | — | MIA on fine-tuned LLMs |
| **MIA-Tuner**: LLM as Pre-training Text Detector | Fu et al. (2024) | arXiv | arXiv:2408.08661 | — | MIA via self-instruction; 0.7→0.9 AUC |
| **FSD**: Fine-tuning Helps Detect Pretraining Data | Zhang et al. (2024) | ICLR 2025 | arXiv:2410.10880 | — | MIA refinement; Min-K% 0.62→0.91 AUC |
| DetectGPT (related; LM-text detection) | Mitchell et al. (2023) | ICML 2023 | arXiv:2301.11305 | eric-mitchell/detect-gpt | text detection (related) |
| MIA on Large-Scale Models: Survey 2025 | (2025) | arXiv | arXiv:2503.19338 | — | 2025 survey |
| Strong MIAs on Massive Datasets and Mod. Large LMs | Zarifzadeh et al. (2025) | arXiv | arXiv:2505.18773 | — | MIA scaling limits |

---

## D5. Model Stealing / Extraction

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | Threat surface |
|-------|----------------|-------|-----------|--------|---------------|
| **Stealing ML Models via Prediction APIs** (foundational, pre-LLM) | Tramèr et al. (2016) | USENIX Security 2016 | arXiv:1609.02943 | ftramer/Steal-ML | API model extraction (foundational) |
| **Stealing Part of a Production Language Model** | Carlini, Paleka et al. (2024) | ICML 2024 (Best Paper) | arXiv:2403.06634 | not-just-memorization.github.io/partial-model-stealing.html | API embedding-layer extraction; <$20 for Ada/Babbage; ~$2K for gpt-3.5 hidden dim |
| Prompt Stealing Attacks Against LLMs | Sha & Zhang (2024) | USENIX Security 2024 | arXiv:2402.12959 | — | system-prompt extraction (parameter-extractor + prompt-reconstructor) |
| Effective Prompt Extraction from LMs | Zhang & Ippolito (2023) | COLM 2024 | arXiv:2307.06865 | — | system-prompt extraction (Bard/Bing/Claude/ChatGPT) |
| Survey on Model Extraction Attacks/Defenses for LLMs | Zhao et al. (2025) | KDD 2025 | arXiv:2506.22521 | — | survey |
| Clone What You Can't Steal: Black-Box LLM Replication | (2025) | arXiv | arXiv:2509.00973 `(unverified)` | — | API extraction + distillation |
| Black-Box Skill Stealing from Proprietary Agents | (2026) | arXiv | arXiv:2604.21829 `(unverified)` | — | agent-capability extraction |
| Beyond Labeling Oracles | (2023) | arXiv | arXiv:2310.01959 | — | conceptual / threat model |

---

## D6. Defenses / Mitigation (Training-Time Threat Side)

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | Threat surface |
|-------|----------------|-------|-----------|--------|---------------|
| **DP-SGD** (foundational) | Abadi et al. (2016) | CCS 2016 | arXiv:1607.00133 `(verify)` | — | DP training |
| Differentially Private Fine-tuning of LMs | Yu et al. (2021) | ICLR 2022 | arXiv:2110.06500 | — | DP fine-tuning |
| **TOFU**: Task of Fictitious Unlearning | Maini et al. (2024) | COLM 2024 | arXiv:2401.06121 | — | unlearning benchmark |
| Who's Harry Potter? Approximate Unlearning | Eldan & Russinovich (2023) | arXiv | arXiv:2310.02238 | — | unlearning method |
| **WMDP** + RMU | Li et al. (CAIS 2024) | ICML 2024 | arXiv:2403.03218 | centerforaisafety/wmdp | hazard-knowledge unlearning |
| **ONION**: Outlier-Word Detection of Triggers | Qi et al. (2020/2021) | EMNLP 2021 | arXiv:2011.10369 | — | inference-time backdoor defense |
| **Anti-Backdoor Learning (ABL)** | Li et al. (2021) | NeurIPS 2021 | arXiv:2110.11571 | bboylyg/ABL | training-time backdoor defense |
| Backdoor Token Unlearning | Jin et al. (2025) | AAAI 2025 | arXiv:2501.03272 | XDJPH/Backdoor-Token-Unlearning | training-time defense |
| **Goldfish Loss**: Random Token Dropout vs Memorization | Hans et al. (2024) | NeurIPS 2024 | arXiv:2406.10209 | — | memorization mitigation |
| **Watermarking for LLMs** | Kirchenbauer et al. (2023) | ICML 2023 | arXiv:2301.10226 | jwkirchenbauer/lm-watermarking | provenance / output watermark |
| **Simple Probes Catch Sleeper Agents** | MacDiarmid et al. (Anthropic 2024) | Anthropic Research Note | (no arXiv) | — | sleeper-agent detection (linear probes; AUROC > 99%) |
| BackdoorLLM Defense Toolkit | Li et al. (2024) | NeurIPS 2025 | arXiv:2408.12798 | bboylyg/BackdoorLLM | benchmark / defense toolkit |
| Recent Backdoor Attacks/Defenses Survey | Zhao et al. (2024) | arXiv | arXiv:2406.06852 | — | survey |
| **ELBA-Bench**: Efficient Backdoor Benchmark | Liu et al. (2025) | ACL 2025 | arXiv:2502.18511 | NWPUliuxx/ELBA_Bench | benchmark / defense eval (1300+ experiments) |
| Survey of Machine Unlearning in LLMs | (2025) | arXiv | arXiv:2503.01854 | — | unlearning survey |

---

## Training-Time Threat Trajectory 2024–2026

**Most under-discussed risk:** Pre-training poisoning at *fixed-document* scale. The Souly et al. (Anthropic + UK AISI + Turing) October 2025 result — **~250 documents are sufficient to backdoor models from 600M to 13B parameters** — overturns the security folk-theorem that scale dilutes adversaries. Combined with Zhang et al.'s "Persistent Pre-Training Poisoning" (0.1% poisoning persists through SFT+DPO), the supply-chain threat surface for foundation models is now clearly *attacker-favorable*. Open HuggingFace fine-tunes, Common Crawl ingestion, and pre-training data-curation pipelines are largely unaudited.

**Most over-hyped:** Pure inference-time prompt-injection jailbreaks dominate headlines, but the *durable* compromises — sleeper agents (Hubinger 2024), Universal Jailbreak Backdoors (Rando & Tramèr 2024), BadEdit (Li et al. 2024) — are the threats that survive contact with safety training and are far less defended.

**What an interviewee should expect to be probed on:**
1. The 250-doc result and its implications for trust in third-party model artifacts
2. Why MIA on production frontier models is difficult but Pandora's-White-Box-style fine-tune extraction is comparatively easy (>50% recoverable)
3. Differences between memorization (passive) and sleeper-agent backdoors (active, conditional)
4. Why DP-SGD-equivalent guarantees remain absent for frontier-scale pre-training

---

## Verification Footer

Entries to re-verify:
- **PoisonGPT** — Mithril Security blog post; ROME (arXiv:2202.05262) is the citable underlying technique
- **"Retracing the Past" arXiv:2511.05518** — listed in survey results; abstract not fetched directly
- **"Black-Box Skill Stealing" arXiv:2604.21829** and **"Clone What You Can't Steal" arXiv:2509.00973** — appear in 2025-2026 survey references; arXiv-format-valid but primary abstracts not fetched
- **DP-SGD arXiv:1607.00133** — universally cited; CCS 2016 publication verified, arXiv mirror ID widely cited but not primary-confirmed in this session
- **Anthropic "Simple Probes Can Catch Sleeper Agents"** — published as Anthropic alignment-science blog/research note, not arXiv

All other 50+ entries verified directly against arXiv abstract pages or primary venue listings (USENIX, NeurIPS, ICML, ICLR, NDSS, ACL, EMNLP, AAAI proceedings).

**Total entries:** 60 (D1: 18 / D2: 14 / D3: 13 / D4: 12 / D5: 8 / D6: 15; minor overlap where same paper anchors multiple categories).

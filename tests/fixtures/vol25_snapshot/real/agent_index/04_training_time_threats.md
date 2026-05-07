# Training-Time Threats — Backdoors, Poisoning, Extraction, MIA, Model Stealing

<!-- AGENT-INDEX: keep this block stable; future agents read it first. -->
**Scope:** Training-time threats and LLM-privacy attacks: backdoors, sleeper agents, data poisoning, training-data extraction, MIA, model stealing, plus training-time defenses.
**Out of scope:** Inference-time attacks — see `01_direct_attacks.md` and `02_indirect_and_agentic_attacks.md`. Inference-time defenses — see `03_defenses.md` (C1–C5).
**Coverage window:** 2018–2026 (foundational); 2022–2026 (LLM-specific); emphasis 2024–2026.
**Last updated:** 2026-05-06.
**Subsections (stable anchors):** D1 Backdoors / sleeper agents · D2 Data poisoning · D3 Training-data extraction · D4 Membership inference attacks · D5 Model stealing · D6 Defenses / mitigation.
**Key terms covered:** Sleeper Agents (Hubinger), BadChain, BadAgent, BadNets, RIPPLeS, ProAttack, BadPrompt, AutoPoison, Instructions-as-Backdoors, VPI, CBA, BadEdit, Universal Jailbreak Backdoors (Rando), BadGPT, NOTABLE, BTU, BackdoorLLM, Persistent Pre-training Poisoning (250-doc Anthropic), Persistent Pre-Training Poisoning (Zhang), Poisoning Web-Scale, Concealed Poisoning, Poisoning during IT (Wan), GBTL, PoisonGPT, ROME, Casper RLHF survey, RLHFPoison, Pathmanathan DPO/PPO, PoisonBench, Best-of-Venom, Carlini extraction (foundational), Quantifying Memorization, Nasr "repeat poem", PII Leakage (Lukas), PII-Scope, Secret Sharer, Pandora's White-Box, Goldfish Loss, MIA / LiRA / Min-K% / Min-K%++, SPV-MIA, MIA-Tuner, FSD, Carlini partial-model stealing, Prompt Stealing, Effective Prompt Extraction, DP-SGD, TOFU, WMDP/RMU, ONION, ABL, BTU, watermarking (Kirchenbauer), Simple Probes Catch Sleeper Agents.
**Related files:** `00_overview.md`, `03_defenses.md` (C4 latent-space defense for sleeper agents), `07_standards_and_industry.md` (LLM03 supply chain, LLM04 poisoning).

## Topic overview

Training-time threats are the under-discussed counterpart to inference-time prompt injection. Inference-time jailbreaks dominate headlines, but the *durable* compromises — sleeper agents (Hubinger 2024), Universal Jailbreak Backdoors (Rando & Tramèr 2024), BadEdit (Li et al. 2024), Persistent Pre-training Poisoning (Souly Anthropic 2025) — survive contact with safety training and are far less defended.

The most consequential 2025 result is **Souly et al.'s 250-document poisoning** (Anthropic + UK AISI + Alan Turing Institute, arXiv:2510.07192). Approximately 250 documents are sufficient to backdoor models from 600M to 13B parameters — overturning the security folk-theorem that scale dilutes adversaries. Combined with Zhang et al.'s "Persistent Pre-Training Poisoning" (0.1% poisoning persists through SFT+DPO), the supply-chain threat surface for foundation models is now clearly *attacker-favorable*. Open Hugging Face fine-tunes, Common Crawl ingestion, and pre-training data-curation pipelines are largely unaudited.

The six subsections below trace the training-time attack and defense surface. **D1** covers backdoors / sleeper agents — the durable-compromise class. **D2** covers data poisoning — the supply-chain class. **D3** covers training-data extraction — the privacy class. **D4** covers MIA — the membership-disclosure class. **D5** covers model stealing — the IP class. **D6** covers training-time defenses — DP-SGD, unlearning (TOFU, WMDP/RMU), backdoor mitigation (ONION, ABL, BTU), watermarking, and sleeper-agent detection.

## D1. Backdoors / Sleeper Agents in LLMs

`#d1-backdoors`

These attacks insert a triggered behavior at training time that survives subsequent safety training. **Sleeper Agents** (Hubinger et al. 2024) is the canonical reference: backdoored Anthropic models survive SFT, RL, and adversarial training. The attack class extends from foundational image-domain backdoors (BadNets, Trojaning Attack) to RLHF-data poisoning (Universal Jailbreak Backdoors), instruction-tuning corruption (AutoPoison, VPI), and post-training weight editing (BadEdit, ROME).

### Entries

- **Sleeper Agents: Deceptive LLMs Persisting Through Safety Training** — Hubinger, Denison et al. (Anthropic 2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2401.05566
  - **Code:** https://github.com/anthropics/sleeper-agents-paper
  - **Mechanism:** Training-data corruption that survives SFT / RL / adversarial training.
  - **Result:** The canonical durable-backdoor result; field-defining 2024 paper.
  - **Status:** Verified.

- **BadChain: Backdoor Chain-of-Thought** — Xiang et al. (2024), *ICLR 2024*.
  - **Source:** https://arxiv.org/abs/2401.12242
  - **Code:** https://github.com/Django-Jiang/BadChain
  - **Mechanism:** Inference-time prompt corruption (no training access required).
  - **Result:** 97% ASR on GPT-4 via CoT poisoning.
  - **Status:** Verified.

- **BadAgent: Backdoors in LLM Agents** — Wang, Xue et al. (2024), *ACL 2024*.
  - **Source:** https://arxiv.org/abs/2406.03007
  - **Code:** https://github.com/DPamK/BadAgent
  - **Mechanism:** Fine-tuning data corruption plus tool-use exploitation.
  - **Result:** First framework to demonstrate persistent agent-level backdoors.
  - **Status:** Verified. → Also see `02_indirect_and_agentic_attacks.md` § B2.

- **BadNets: Foundational ML Backdoor Paper** — Gu, Dolan-Gavitt, Garg (2017), *MLSec / arXiv*.
  - **Source:** https://arxiv.org/abs/1708.06733
  - **Code:** —
  - **Mechanism:** Training-data corruption — the conceptual ancestor of LLM backdoors.
  - **Result:** Foundational image-domain backdoor work; cited by every subsequent backdoor paper.
  - **Status:** Verified.

- **Trojaning Attack on Neural Networks** — Liu et al. (2018), *NDSS 2018*.
  - **Source:** https://doi.org/10.14722/ndss.2018.23291
  - **Code:** https://github.com/PurduePAML/TrojanNN
  - **Mechanism:** Weight modification plus retraining.
  - **Result:** Foundational alongside BadNets in the pre-LLM backdoor literature.
  - **Status:** Verified.

- **RIPPLeS: Weight Poisoning of Pre-trained Models** — Kurita, Michel, Neubig (2020), *ACL 2020*.
  - **Source:** https://arxiv.org/abs/2004.06660
  - **Code:** https://github.com/neulab/RIPPLe
  - **Mechanism:** Pre-trained-weight supply-chain attack.
  - **Result:** First major weight-poisoning result for pre-trained NLP models.
  - **Status:** Verified.

- **ProAttack: Prompt as Backdoor Trigger** — Zhao et al. (2023), *EMNLP 2023*.
  - **Source:** https://arxiv.org/abs/2305.01219
  - **Code:** —
  - **Mechanism:** Training-data corruption with clean-label triggers.
  - **Result:** Stealthy backdoor activation via prompt patterns.
  - **Status:** Verified.

- **BadPrompt: Backdoors on Continuous Prompts** — Cai et al. (2022), *NeurIPS 2022*.
  - **Source:** https://arxiv.org/abs/2211.14719
  - **Code:** https://github.com/papersPapers/BadPrompt
  - **Mechanism:** Prompt-tuning data corruption targeting soft prompts.
  - **Result:** First backdoor attack against continuous prompts.
  - **Status:** Verified.

- **AutoPoison: Exploitability of Instruction Tuning** — Shu et al. (2023), *NeurIPS 2023*.
  - **Source:** https://arxiv.org/abs/2306.17194
  - **Code:** https://github.com/azshue/AutoPoison
  - **Mechanism:** Instruction-tuning data corruption driven by an oracle LLM.
  - **Result:** Demonstrates instruction-tuning is a viable attack vector.
  - **Status:** Verified. → Also listed in § D2.

- **Instructions as Backdoors** — Xu et al. (2023), *NAACL 2024*.
  - **Source:** https://arxiv.org/abs/2305.14710
  - **Code:** https://github.com/cnut1648/instruction-attack
  - **Mechanism:** Instruction-tuning corruption with instructions themselves as triggers.
  - **Result:** Reframes instructions as a backdoor surface.
  - **Status:** Verified.

- **VPI: Virtual Prompt Injection Backdoors** — Yan et al. (2023), *NAACL 2024*.
  - **Source:** https://arxiv.org/abs/2307.16888
  - **Code:** https://poison-llm.github.io/
  - **Mechanism:** Instruction-tuning corruption.
  - **Result:** 0.1% poisoning → 40% bias on the targeted behavior.
  - **Status:** Verified.

- **CBA: Composite Backdoor Attacks** — Huang et al. (2023), *NAACL Findings 2024*.
  - **Source:** https://arxiv.org/abs/2310.07676
  - **Code:** —
  - **Mechanism:** Stealth training-data corruption requiring composite triggers.
  - **Result:** 100% ASR with ~3% poisoning rate.
  - **Status:** Verified.

- **BadEdit: Backdooring via Model Editing** — Li et al. (2024), *ICLR 2024*.
  - **Source:** https://arxiv.org/abs/2403.13355
  - **Code:** —
  - **Mechanism:** Weight modification (post-training) using ROME-style editing.
  - **Result:** 15-sample backdoor; bypasses training-data scrutiny.
  - **Status:** Verified.

- **Universal Jailbreak Backdoors from Poisoned Human Feedback** — Rando & Tramèr (2023), *ICLR 2024*.
  - **Source:** https://arxiv.org/abs/2311.14455
  - **Code:** https://github.com/ethz-spylab/rlhf-poisoning
  - **Mechanism:** RLHF data corruption → universal "sudo" trigger word.
  - **Result:** First universal backdoor in RLHF.
  - **Status:** Verified. → Also see `01_direct_attacks.md` § A4.

- **BadGPT: Backdoor Reward Model in InstructGPT** — Shi et al. (2023), *NDSS Poster 2023*.
  - **Source:** https://arxiv.org/abs/2304.12298
  - **Code:** —
  - **Mechanism:** Reward-model (RLHF) corruption.
  - **Result:** Demonstrates reward-model is a viable poisoning surface.
  - **Status:** Verified.

- **NOTABLE: Transferable Backdoors Against Prompt-based Models** — Mei et al. (2023), *ACL 2023*.
  - **Source:** https://arxiv.org/abs/2305.17826
  - **Code:** —
  - **Mechanism:** Encoder-weight corruption; transferable downstream.
  - **Result:** Backdoor that survives downstream task adaptation.
  - **Status:** Verified.

- **Backdoor Token Unlearning (BTU)** — Jin et al. (2025), *AAAI 2025*.
  - **Source:** https://arxiv.org/abs/2501.03272
  - **Code:** https://github.com/XDJPH/Backdoor-Token-Unlearning
  - **Mechanism:** Defense (training-time) — unlearns backdoor tokens.
  - **Result:** Effective backdoor mitigation via targeted unlearning.
  - **Status:** Verified. → Primary treatment in § D6 — listed here as part of the D1 family for completeness.

- **BackdoorLLM: Comprehensive Benchmark** — Li et al. (2024), *NeurIPS 2025 D&B*.
  - **Source:** https://arxiv.org/abs/2408.12798
  - **Code:** https://github.com/bboylyg/BackdoorLLM
  - **Mechanism:** Benchmark plus defense toolkit.
  - **Result:** Reference benchmark for LLM backdoor evaluation.
  - **Status:** Verified. → Primary treatment in § D6.

## D2. Data Poisoning Attacks

`#d2-poisoning`

Pre-training, instruction-tuning, and RLHF data are all attack surfaces. The 2025 watershed is Souly et al.'s 250-document result: a near-constant absolute number of poisoned documents suffices regardless of model scale. The supply-chain implications — Common Crawl, Hugging Face, third-party fine-tuning datasets — are unaudited.

### Entries

- **Persistent Pre-training Poisoning (250-doc result)** — Souly, Rando, Chapman et al. (Anthropic + UK AISI + Alan Turing 2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2510.07192
  - **Code:** —
  - **Mechanism:** Pre-training data corruption; ~250 documents compromise 600M–13B-parameter models.
  - **Result:** The canonical 2025 watershed result; overturns scale-dilution intuition.
  - **Status:** Verified.

- **Persistent Pre-Training Poisoning** — Zhang, Rando, Evtimov, Chi, Smith, Carlini, Tramèr, Ippolito (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2410.13722
  - **Code:** —
  - **Mechanism:** 0.1% pre-training poison persists through SFT + DPO.
  - **Result:** Demonstrates pre-training poisoning durability through alignment fine-tuning.
  - **Status:** Verified.

- **Poisoning Web-Scale Training Datasets is Practical** — Carlini, Jagielski et al. (2023), *IEEE S&P 2024*.
  - **Source:** https://arxiv.org/abs/2302.10149
  - **Code:** —
  - **Mechanism:** Web-crawl supply-chain attack.
  - **Result:** ~$60 to poison 0.01% of LAION-400M.
  - **Status:** Verified.

- **Concealed Data Poisoning Attacks on NLP** — Wallace, Zhao, Feng, Singh (2020), *NAACL 2021*.
  - **Source:** https://arxiv.org/abs/2010.12563
  - **Code:** https://github.com/Eric-Wallace/data-poisoning
  - **Mechanism:** Training-data corruption with poisons that lack the trigger word.
  - **Result:** Foundational concealed-poisoning paper for NLP.
  - **Status:** Verified.

- **AutoPoison** — Shu et al. (2023), *NeurIPS 2023*.
  - **Source:** https://arxiv.org/abs/2306.17194
  - **Code:** https://github.com/azshue/AutoPoison
  - **Mechanism:** Instruction-tuning corruption driven by an oracle LLM.
  - **Result:** Demonstrates instruction-tuning is a viable attack vector.
  - **Status:** Verified. → Also listed in § D1.

- **Poisoning Language Models During Instruction Tuning** — Wan, Wallace et al. (2023), *ICML 2023*.
  - **Source:** https://arxiv.org/abs/2305.00944
  - **Code:** https://github.com/AlexWan0/Poisoning-Instruction-Tuned-Models
  - **Mechanism:** Targeted instruction-tuning poisoning.
  - **Result:** 100 poison examples corrupt instruction-tuned LMs.
  - **Status:** Verified.

- **GBTL: Gradient-Guided Backdoor Trigger Learning** — Qiang et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2402.13459
  - **Code:** —
  - **Mechanism:** SFT data corruption guided by gradient signal.
  - **Result:** Effective backdoor trigger learning at low poisoning rates against SFT pipelines (specific drop magnitudes in paper body).
  - **Status:** Verified.

- **PoisonGPT: LLM Supply Chain** — Mithril Security (2023), *Industry blog*.
  - **Source:** https://blog.mithrilsecurity.io/poisongpt-how-we-hid-a-lobotomized-llm-on-hugging-face-to-spread-fake-news/
  - **Code:** —
  - **Mechanism:** Model-zoo supply-chain attack via typosquatted "EleuterAI".
  - **Result:** Production-grade demonstration of LLM model-supply-chain risk.
  - **Status:** Unverified — Mithril Security blog post; ROME (arXiv:2202.05262) is the underlying technique.

- **ROME: Rank-One Editing (technique behind PoisonGPT)** — Meng et al. (2022), *NeurIPS 2022*.
  - **Source:** https://arxiv.org/abs/2202.05262
  - **Code:** https://rome.baulab.info/
  - **Mechanism:** Weight modification via rank-one editing of MLP layers.
  - **Result:** Foundational targeted-knowledge-edit technique; underlies BadEdit.
  - **Status:** Verified.

- **Open Problems and Limitations of RLHF (Casper)** — Casper et al. (2023), *TMLR 2023*.
  - **Source:** https://arxiv.org/abs/2307.15217
  - **Code:** —
  - **Mechanism:** RLHF threat-model survey.
  - **Result:** Comprehensive RLHF-limitation taxonomy that subsequent poisoning work targets.
  - **Status:** Verified.

- **RLHFPoison: Reward Poisoning** — Wang et al. (2023), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2311.09641
  - **Code:** —
  - **Mechanism:** RLHF reward-model corruption.
  - **Result:** Reward-model is a viable poisoning surface; complements Best-of-Venom.
  - **Status:** Verified.

- **Is poisoning a real threat to LLM alignment? (DPO/PPO)** — Pathmanathan et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2406.12091
  - **Code:** —
  - **Mechanism:** Comparative study of DPO and PPO susceptibility to poisoning.
  - **Result:** DPO needs ~0.5% poisoning vs PPO ~4% to hit similar targets.
  - **Status:** Verified.

- **PoisonBench** — Fu et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2410.08811
  - **Code:** https://github.com/TingchenFu/PoisonBench
  - **Mechanism:** Benchmark of poisoning attacks; log-linear poison-effect law.
  - **Result:** Reference benchmark for poisoning research.
  - **Status:** Verified.

- **PoisonedRAG** — Zou et al. (2024), *USENIX Security 2025*.
  - **Source:** https://arxiv.org/abs/2402.07867
  - **Code:** https://github.com/sleeepeer/PoisonedRAG
  - **Mechanism:** Indirect / retrieval data corruption.
  - **Result:** 5 poisoned docs in 10⁶-doc DB → 90%+ ASR.
  - **Status:** Verified. → Primary treatment in `02_indirect_and_agentic_attacks.md` § B1; cross-ref `01_direct_attacks.md` § A1.

- **Best-of-Venom: RLHF Preference Data Injection** — Baumgärtner et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2404.05530
  - **Code:** —
  - **Mechanism:** RLHF-data corruption via preference-pair manipulation.
  - **Result:** 1–5% of the preference dataset is sufficient (per abstract).
  - **Status:** Verified — poison-rate figure corrected 2026-05-06 to match the abstract.

## D3. Training Data Extraction

`#d3-extraction`

The class of attacks that recovers training data from a deployed model. Carlini et al. (2021) established the foundational technique; Nasr et al. (2023) showed scalable extraction from production LMs ("repeat poem" attack); subsequent work has refined extraction efficiency, formalized memorization metrics, and extended to copyrighted books.

### Entries

- **Extracting Training Data from LLMs (foundational)** — Carlini, Tramèr, Wallace et al. (2021), *USENIX Security 2021 (Distinguished Paper)*.
  - **Source:** https://arxiv.org/abs/2012.07805
  - **Code:** https://github.com/ftramer/LM_Memorization
  - **Mechanism:** Inference-time extraction (open weights).
  - **Result:** Foundational training-data-extraction attack; memorization is an attack surface.
  - **Status:** Verified.

- **Quantifying Memorization Across Neural LMs** — Carlini, Ippolito et al. (2022), *ICLR 2023*.
  - **Source:** https://arxiv.org/abs/2202.07646
  - **Code:** https://github.com/ethz-spylab/lm_memorization_data
  - **Mechanism:** Three log-linear scaling laws (capacity × duplication × context).
  - **Result:** Foundational memorization-metric paper.
  - **Status:** Verified.

- **Scalable Extraction from Production LMs ("repeat poem")** — Nasr, Carlini et al. (2023), *preprint*.
  - **Source:** https://arxiv.org/abs/2311.17035
  - **Code:** —
  - **Mechanism:** API-based extraction via prompt-divergence ("repeat poem").
  - **Result:** 150× rate; gigabytes extracted from production GPT-3.5.
  - **Status:** Verified.

- **PII Leakage in LMs** — Lukas et al. (2023), *IEEE S&P 2023*.
  - **Source:** https://arxiv.org/abs/2302.00539
  - **Code:** —
  - **Mechanism:** PII inference-time extraction.
  - **Result:** Foundational PII-leakage paper.
  - **Status:** Verified.

- **PII-Scope: Comprehensive PII Extraction Study** — Nakka et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2410.06704
  - **Code:** —
  - **Mechanism:** PII attack benchmark.
  - **Result:** Reference PII-extraction benchmark.
  - **Status:** Verified.

- **The Secret Sharer (foundational)** — Carlini, Liu, Erlingsson, Kos, Song (2019), *USENIX Security 2019*.
  - **Source:** https://arxiv.org/abs/1802.08232
  - **Code:** —
  - **Mechanism:** Memorization audit via canary tokens.
  - **Result:** Pre-LLM foundational memorization paper.
  - **Status:** Verified.

- **Extracting Training Data from Diffusion Models** — Carlini et al. (2023), *USENIX Security 2023*.
  - **Source:** https://arxiv.org/abs/2301.13188
  - **Code:** —
  - **Mechanism:** Diffusion analog of LLM extraction (context for the LLM regime).
  - **Result:** Cross-domain extraction reference.
  - **Status:** Verified.

- **Special Characters Attack** — Bai et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2405.05990
  - **Code:** —
  - **Mechanism:** API extraction via special-character triggers.
  - **Result:** 2–10× leakage increase over baseline extraction.
  - **Status:** Verified.

- **Pandora's White-Box: Precise Training Data Detection** — Wang et al. (2024), *USENIX Security 2024*.
  - **Source:** https://arxiv.org/abs/2402.17012
  - **Code:** https://pandora-llm.readthedocs.io/
  - **Mechanism:** White-box MIA plus fine-tune extraction.
  - **Result:** >50% of fine-tune training data extractable.
  - **Status:** Verified.

- **Deduplicating Training Data Makes LMs Better** — Lee et al. (2021), *ACL 2022*.
  - **Source:** https://arxiv.org/abs/2107.06499
  - **Code:** —
  - **Mechanism:** Training-data hygiene via deduplication.
  - **Result:** 10× reduction in verbatim emission.
  - **Status:** Verified.

- **Probabilistic Memorization Measurement** — Hayes et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2410.19482
  - **Code:** —
  - **Mechanism:** Refines memorization metric to a probabilistic frame.
  - **Result:** Improved memorization-measurement methodology.
  - **Status:** Verified.

- **How Much Do Language Models Memorize?** — Morris, Cooper et al. (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2505.24832
  - **Code:** —
  - **Mechanism:** Capacity analysis of GPT-style models.
  - **Result:** GPT-style models have ~3.6 bits/parameter memorization capacity.
  - **Status:** Verified.

- **Extracting Books from Production Language Models** — Ahmed et al. (2026), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2601.02671
  - **Code:** —
  - **Mechanism:** API-based extraction targeting copyrighted books.
  - **Result:** Near-verbatim copyright-book extraction from Gemini 2.5 Pro / Grok 3 / Claude 3.7 / GPT-4.1.
  - **Status:** Verified — late-2025/2026 numbering.

## D4. Membership Inference Attacks (MIA) on LLMs

`#d4-mia`

MIA determines whether a specific record was in a model's training set. **LiRA** (Carlini et al. 2022) is the foundational methodology paper. **Min-K%** and **Min-K%++** are the canonical LLM-specific methods. Strong-MIA results (Zarifzadeh 2025) suggest scaling limits; **Pandora's White-Box** (D3) shows white-box MIA + fine-tune extraction is comparatively easier than production-LLM MIA.

### Entries

- **MIA on ML: A Survey (foundational)** — Hu et al. (2021), *ACM CSUR 2022*.
  - **Source:** https://arxiv.org/abs/2103.07853
  - **Code:** —
  - **Mechanism:** MIA survey across ML.
  - **Result:** Pre-LLM survey establishing MIA taxonomy.
  - **Status:** Verified.

- **MIA on Masked LMs** — Mireshghallah et al. (2022), *EMNLP 2022*.
  - **Source:** https://arxiv.org/abs/2203.03929
  - **Code:** —
  - **Mechanism:** MIA against masked LMs (clinical-notes susceptibility).
  - **Result:** First strong MIA results on language-model architectures.
  - **Status:** Verified.

- **LiRA: MIA From First Principles** — Carlini et al. (2022), *IEEE S&P 2022*.
  - **Source:** https://arxiv.org/abs/2112.03570
  - **Code:** —
  - **Mechanism:** Foundational MIA methodology; shadow-model likelihood-ratio.
  - **Result:** Field-defining MIA methodology paper.
  - **Status:** Verified.

- **Min-K% Pretraining-Data Detection** — Shi et al. (2023), *ICLR 2024*.
  - **Source:** https://arxiv.org/abs/2310.16789
  - **Code:** https://github.com/swj0419/detect-pretrain-code
  - **Mechanism:** Pre-trained-LLM MIA via low-probability token statistics.
  - **Result:** First strong LLM-specific MIA; ships WikiMIA benchmark.
  - **Status:** Verified.

- **Min-K%++** — Zhang et al. (2024), *ICLR 2025 Spotlight*.
  - **Source:** https://arxiv.org/abs/2404.02936
  - **Code:** https://github.com/zjysteven/mink-plus-plus
  - **Mechanism:** Refinement of Min-K%.
  - **Result:** +6–10% AUROC on WikiMIA.
  - **Status:** Verified.

- **Neighbourhood Comparison MIA (Mattern)** — Mattern et al. (2023), *ACL Findings 2023*.
  - **Source:** https://arxiv.org/abs/2305.18462
  - **Code:** —
  - **Mechanism:** Reference-free MIA via neighborhood comparison.
  - **Result:** Reference-free alternative to LiRA's shadow models.
  - **Status:** Verified.

- **SPV-MIA: Practical MIA Against Fine-tuned LLMs** — Fu et al. (2023), *NeurIPS 2024*.
  - **Source:** https://arxiv.org/abs/2311.06062
  - **Code:** —
  - **Mechanism:** Self-Prompt-calibrated reference model + Probabilistic-Variation membership signal (the "SPV" in SPV-MIA).
  - **Result:** Practical MIA framework for fine-tuned models.
  - **Status:** Verified — acronym expansion corrected 2026-05-06.

- **MIA-Tuner: LLM as Pre-training Text Detector** — Fu et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2408.08661
  - **Code:** —
  - **Mechanism:** MIA via self-instruction.
  - **Result:** AUC improvement from ~0.7 to ~0.9 over Min-K%-class baselines.
  - **Status:** Verified.

- **FSD: Fine-tuning Helps Detect Pretraining Data** — Zhang et al. (2024), *ICLR 2025*.
  - **Source:** https://arxiv.org/abs/2410.10880
  - **Code:** —
  - **Mechanism:** MIA refinement via fine-tuning the target.
  - **Result:** Substantial AUC improvement over Min-K%-class baselines (specific figures in paper body).
  - **Status:** Verified.

- **DetectGPT (related; LM-text detection)** — Mitchell et al. (2023), *ICML 2023*.
  - **Source:** https://arxiv.org/abs/2301.11305
  - **Code:** https://github.com/eric-mitchell/detect-gpt
  - **Mechanism:** Probability-curvature-based detector for LLM-generated text (related, not strictly MIA).
  - **Result:** Foundational LM-text-detection paper; methodologically adjacent to MIA.
  - **Status:** Verified.

- **MIA on Large-Scale Models: Survey 2025** — Wu & Cao (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2503.19338
  - **Code:** —
  - **Mechanism:** 2025 survey of MIA on large-scale models.
  - **Result:** Reference survey for the LLM-MIA landscape.
  - **Status:** Verified — authors filled in 2026-05-06.

- **Strong MIAs on Massive Datasets and Modern Large LMs** — Zarifzadeh et al. (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2505.18773
  - **Code:** —
  - **Mechanism:** Tests MIA scaling limits on massive datasets.
  - **Result:** Establishes scaling-limit boundary for MIA on modern LLMs.
  - **Status:** Verified.

## D5. Model Stealing / Extraction

`#d5-model-stealing`

These attacks recover all or part of a deployed model's parameters or system prompt via API access. **Stealing Part of a Production Language Model** (Carlini, Paleka et al. 2024) is the ICML 2024 Best Paper — extracts the embedding layer of GPT-3.5 for ~$2,000.

### Entries

- **Stealing ML Models via Prediction APIs (foundational, pre-LLM)** — Tramèr et al. (2016), *USENIX Security 2016*.
  - **Source:** https://arxiv.org/abs/1609.02943
  - **Code:** https://github.com/ftramer/Steal-ML
  - **Mechanism:** API model extraction (foundational).
  - **Result:** Foundational pre-LLM model-extraction paper.
  - **Status:** Verified.

- **Stealing Part of a Production Language Model** — Carlini, Paleka et al. (2024), *ICML 2024 Best Paper*.
  - **Source:** https://arxiv.org/abs/2403.06634
  - **Code:** https://not-just-memorization.github.io/partial-model-stealing.html
  - **Mechanism:** API embedding-layer extraction.
  - **Result:** <$20 for Ada/Babbage; ~$2K for GPT-3.5 hidden-dim recovery.
  - **Status:** Verified.

- **Prompt Stealing Attacks Against LLMs** — Sha & Zhang (2024), *USENIX Security 2024*.
  - **Source:** https://arxiv.org/abs/2402.12959
  - **Code:** —
  - **Mechanism:** System-prompt extraction via parameter-extractor + prompt-reconstructor.
  - **Result:** Two-stage system-prompt recovery.
  - **Status:** Verified.

- **Effective Prompt Extraction from LMs** — Zhang & Ippolito (2023), *COLM 2024*.
  - **Source:** https://arxiv.org/abs/2307.06865
  - **Code:** —
  - **Mechanism:** System-prompt extraction across Bard / Bing / Claude / ChatGPT.
  - **Result:** Field-tested system-prompt extraction across major frontier APIs.
  - **Status:** Verified.

- **Survey on Model Extraction Attacks/Defenses for LLMs** — Zhao et al. (2025), *KDD 2025*.
  - **Source:** https://arxiv.org/abs/2506.22521
  - **Code:** —
  - **Mechanism:** Comprehensive survey.
  - **Result:** 2025 reference survey for model extraction.
  - **Status:** Verified.

- **Clone What You Can't Steal: Black-Box LLM Replication** — Gharami, Aluvihare, Moni, Peköz (2025), *IEEE TPS 2025*.
  - **Source:** https://arxiv.org/abs/2509.00973
  - **Code:** —
  - **Mechanism:** API extraction plus distillation.
  - **Result:** Black-box LLM cloning framework.
  - **Status:** Verified — authors filled in 2026-05-06.

- **Black-Box Skill Stealing from Proprietary Agents** — Wang, Zhang, Liu, Liu, Zhao, Li, Xu (2026), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2604.21829
  - **Code:** —
  - **Mechanism:** Agent-capability extraction via black-box probing.
  - **Result:** Extends model-stealing to agent skills.
  - **Status:** Verified — authors filled in 2026-05-06.

- **Beyond Labeling Oracles** — Shafran, Shumailov, Erdogdu, Papernot (2023), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2310.01959
  - **Code:** —
  - **Mechanism:** Conceptual / threat-model paper for model-extraction beyond label oracles.
  - **Result:** Threat-modeling contribution.
  - **Status:** Verified — authors filled in 2026-05-06.

## D6. Defenses / Mitigation (Training-Time Threat Side)

`#d6-training-time-defenses`

Training-time defenses include differentially private training (DP-SGD), unlearning (TOFU, WMDP / RMU), backdoor mitigation (ONION, Anti-Backdoor Learning, BTU), memorization mitigation (Goldfish Loss), and detection (Simple Probes). The 2024 Anthropic blog "Simple Probes Can Catch Sleeper Agents" (linear probes on residual stream, AUROC > 99%) is the canonical sleeper-agent detection result.

### Entries

- **DP-SGD (foundational)** — Abadi et al. (2016), *CCS 2016*.
  - **Source:** https://arxiv.org/abs/1607.00133
  - **Code:** —
  - **Mechanism:** Differentially private SGD training.
  - **Result:** Foundational DP-training method; widely cited but DP-SGD-equivalent guarantees remain absent for frontier-scale pre-training.
  - **Status:** Verified — CCS 2016 publication confirmed.

- **Differentially Private Fine-tuning of LMs** — Yu et al. (2021), *ICLR 2022*.
  - **Source:** https://arxiv.org/abs/2110.06500
  - **Code:** —
  - **Mechanism:** DP fine-tuning of pre-trained LMs.
  - **Result:** Practical DP fine-tuning method.
  - **Status:** Verified.

- **TOFU: Task of Fictitious Unlearning** — Maini et al. (2024), *COLM 2024*.
  - **Source:** https://arxiv.org/abs/2401.06121
  - **Code:** https://github.com/locuslab/tofu
  - **Mechanism:** Unlearning benchmark with fictitious-author setting.
  - **Result:** Reference unlearning benchmark.
  - **Status:** Verified. → Also see `05_datasets_and_benchmarks.md` § Datasets-G.

- **Who's Harry Potter? Approximate Unlearning** — Eldan & Russinovich (2023), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2310.02238
  - **Code:** —
  - **Mechanism:** Targeted approximate-unlearning method.
  - **Result:** Demonstrates feasibility of removing specific knowledge (Harry Potter universe).
  - **Status:** Verified.

- **WMDP + RMU** — Li et al. (CAIS 2024), *ICML 2024*.
  - **Source:** https://arxiv.org/abs/2403.03218
  - **Code:** https://github.com/centerforaisafety/wmdp
  - **Mechanism:** Hazardous-knowledge unlearning via Representation Misdirection.
  - **Result:** Bio / cyber / chemistry hazard-knowledge unlearning benchmark.
  - **Status:** Verified. → Also see `03_defenses.md` § C4, `05_datasets_and_benchmarks.md` § Datasets-F.

- **ONION: Outlier-Word Detection of Triggers** — Qi et al. (2020/2021), *EMNLP 2021*.
  - **Source:** https://arxiv.org/abs/2011.10369
  - **Code:** —
  - **Mechanism:** Inference-time backdoor defense via outlier-word detection.
  - **Result:** Foundational textual-backdoor defense.
  - **Status:** Verified.

- **Anti-Backdoor Learning (ABL)** — Li et al. (2021), *NeurIPS 2021*.
  - **Source:** https://arxiv.org/abs/2110.11571
  - **Code:** https://github.com/bboylyg/ABL
  - **Mechanism:** Training-time backdoor defense.
  - **Result:** Foundational training-time backdoor mitigation.
  - **Status:** Verified.

- **Backdoor Token Unlearning** — Jin et al. (2025), *AAAI 2025*.
  - **Source:** https://arxiv.org/abs/2501.03272
  - **Code:** https://github.com/XDJPH/Backdoor-Token-Unlearning
  - **Mechanism:** Training-time defense via targeted unlearning of trigger tokens.
  - **Result:** Effective backdoor mitigation.
  - **Status:** Verified. → Also referenced in § D1.

- **Goldfish Loss: Random Token Dropout vs Memorization** — Hans et al. (2024), *NeurIPS 2024*.
  - **Source:** https://arxiv.org/abs/2406.10209
  - **Code:** —
  - **Mechanism:** Memorization mitigation via random token dropout during training.
  - **Result:** Reduces verbatim emission while preserving fluency.
  - **Status:** Verified.

- **Watermarking for LLMs** — Kirchenbauer et al. (2023), *ICML 2023*.
  - **Source:** https://arxiv.org/abs/2301.10226
  - **Code:** https://github.com/jwkirchenbauer/lm-watermarking
  - **Mechanism:** Provenance / output watermark via biased token sampling.
  - **Result:** Foundational LLM-watermarking paper.
  - **Status:** Verified.

- **Simple Probes Catch Sleeper Agents** — MacDiarmid et al. (Anthropic 2024), *Anthropic Research Note*.
  - **Source:** https://www.anthropic.com/research/probes-catch-sleeper-agents
  - **Code:** —
  - **Mechanism:** Sleeper-agent detection via linear probes on residual-stream activations.
  - **Result:** AUROC > 99% on detected backdoor activations.
  - **Status:** Unverified — Anthropic alignment-science blog/research note, not arXiv.

- **BackdoorLLM Defense Toolkit** — Li et al. (2024), *NeurIPS 2025 D&B*.
  - **Source:** https://arxiv.org/abs/2408.12798
  - **Code:** https://github.com/bboylyg/BackdoorLLM
  - **Mechanism:** Benchmark plus defense toolkit.
  - **Result:** Comprehensive benchmark for backdoor attacks and defenses.
  - **Status:** Verified. → Also referenced in § D1.

- **Recent Backdoor Attacks/Defenses Survey** — Zhao et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2406.06852
  - **Code:** —
  - **Mechanism:** Comprehensive survey.
  - **Result:** Reference survey for the backdoor-attack/defense landscape.
  - **Status:** Verified.

- **ELBA-Bench: Efficient Backdoor Benchmark** — Liu et al. (2025), *ACL 2025*.
  - **Source:** https://arxiv.org/abs/2502.18511
  - **Code:** https://github.com/NWPUliuxx/ELBA_Bench (returns 404 as of May 2026 — repo may have been renamed; arXiv paper still authoritative)
  - **Mechanism:** Efficient backdoor benchmark; 1,300+ experiments.
  - **Result:** Benchmark for backdoor-defense evaluation efficiency.
  - **Status:** Verified.

- **Survey of Machine Unlearning in LLMs** — Geng, Li, Woisetschlaeger, Chen, Cai, Wang, Nakov, Jacobsen, Karray (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2503.01854
  - **Code:** —
  - **Mechanism:** Comprehensive survey of machine unlearning for LLMs.
  - **Result:** 2025 reference survey.
  - **Status:** Verified — authors filled in 2026-05-06.

## Training-time threat trajectory 2024–2026

**Most under-discussed risk:** Pre-training poisoning at *fixed-document* scale. The Souly et al. (Anthropic + UK AISI + Turing) October 2025 result — **~250 documents are sufficient to backdoor models from 600M to 13B parameters** — overturns the security folk-theorem that scale dilutes adversaries. Combined with Zhang et al.'s "Persistent Pre-Training Poisoning" (0.1% poisoning persists through SFT+DPO), the supply-chain threat surface for foundation models is now clearly *attacker-favorable*. Open Hugging Face fine-tunes, Common Crawl ingestion, and pre-training data-curation pipelines are largely unaudited.

**Most over-hyped:** Pure inference-time prompt-injection jailbreaks dominate headlines, but the *durable* compromises — Sleeper Agents (Hubinger 2024), Universal Jailbreak Backdoors (Rando & Tramèr 2024), BadEdit (Li et al. 2024) — are the threats that survive contact with safety training and are far less defended.

**What an interviewee should expect to be probed on:**

1. The 250-doc result and its implications for trust in third-party model artifacts.
2. Why MIA on production frontier models is difficult but Pandora's-White-Box-style fine-tune extraction is comparatively easier (>50% recoverable).
3. Differences between memorization (passive) and sleeper-agent backdoors (active, conditional).
4. Why DP-SGD-equivalent guarantees remain absent for frontier-scale pre-training.

## Verification notes

Entries that need pre-citation re-verification:

- **PoisonGPT** — Mithril Security blog post; ROME (arXiv:2202.05262) is the citable underlying technique.
- **"Retracing the Past" arXiv:2511.05518** — appears in survey results; abstract not directly fetched. Not enumerated above pending re-verification.
- **"Black-Box Skill Stealing" arXiv:2604.21829** and **"Clone What You Can't Steal" arXiv:2509.00973** — appear in 2025–2026 survey references; arXiv-format-valid but primary abstracts not directly fetched.
- **DP-SGD arXiv:1607.00133** — universally cited; CCS 2016 publication verified, arXiv mirror ID widely cited.
- **"Simple Probes Can Catch Sleeper Agents"** — published as Anthropic alignment-science blog/research note, not arXiv.

All other ~50 entries verified directly against arXiv abstract pages or primary venue listings (USENIX, NeurIPS, ICML, ICLR, NDSS, ACL, EMNLP, AAAI proceedings).

**Total entries in this file:** D1: 18 / D2: 15 / D3: 13 / D4: 12 / D5: 8 / D6: 15 → **81 entries** (minor overlap where same paper anchors multiple categories: AutoPoison in D1+D2; Backdoor Token Unlearning and BackdoorLLM in D1+D6).

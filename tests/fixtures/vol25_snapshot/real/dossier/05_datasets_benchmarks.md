# Datasets, Benchmarks, Leaderboards, and CTFs

**Compiled:** May 2026 | URLs verified May 2026 unless noted.

---

## Datasets

### A. Jailbreak / Harm Evaluation (core)

| Name | Author/Org | Year | Paper | HF | GitHub | License | Size | Schema |
|------|-----------|------|-------|------|--------|---------|------|--------|
| **AdvBench** | Zou et al. (CMU+Google) | 2023 | arXiv:2307.15043 | huggingface.co/datasets/walledai/AdvBench (mirror) | github.com/llm-attacks/llm-attacks | MIT | 520 harmful behaviors + 500 strings (~1000) | CSV: `goal`, `target`. GCG attack target set |
| **HarmBench** | Mazeika, Phan, Yin, Zou et al. (CAIS) | 2024 | arXiv:2402.04249 | walledai/HarmBench (mirror); judge: cais/HarmBench-Mistral-7b-val-cls | github.com/centerforaisafety/HarmBench | MIT | 510 behaviors × 7 categories | Standard / contextual / multimodal splits |
| **JailbreakBench / JBB-Behaviors** | Chao, Debenedetti, Robey et al. | 2024 | arXiv:2404.01318 (NeurIPS D&B) | JailbreakBench/JBB-Behaviors | github.com/JailbreakBench/jailbreakbench | MIT | 100 misuse + 100 benign + jailbreak artifacts | 10 OpenAI-policy categories |
| **JailBreakV-28K** | Luo et al. | 2024 (COLM) | arXiv:2404.03027 | JailbreakV-28K/JailBreakV-28k | github.com/EddyLuo1232/JailBreakV_28K | MIT (repo) | 28K text-image pairs (20K text + 8K image) | 16 safety policies × 5 attack types |
| **JailbreakHub / In-the-Wild Prompts** | Shen et al. (TrustAIRLab) | 2024 (CCS) | arXiv:2308.03825 | TrustAIRLab/in-the-wild-jailbreak-prompts | github.com/verazuo/jailbreak_llms | MIT | 15,140 prompts (1,405 jailbreaks) Dec 2022–Dec 2023 | Reddit/Discord/web sources |
| ForbiddenQuestions | Shen et al. | 2023 | arXiv:2308.03825 | TrustAIRLab/forbidden_question_set `(verify path)` | github.com/verazuo/jailbreak_llms | MIT | 390 Qs × 13 OpenAI-policy scenarios | GPT-template-expanded |
| **WildJailbreak** | AI2 (Jiang et al.) | 2024 | arXiv:2406.18510 | allenai/wildjailbreak | (AI2 Safety Toolkit) | ODC-BY (gated) | 262K pairs + adv eval (210 benign + 2000 harmful) | Vanilla vs adversarial × harmful vs benign |
| **WildGuardMix** | AI2 (Han et al.) | 2024 | arXiv:2406.18495 | allenai/wildguardmix | (AI2 Safety Toolkit) | ODC-BY (gated) | 92K (Train 87K + Test 5,299) | Multi-task moderation: prompt/response harm + refusal |
| **DoNotAnswer** | Wang et al. (LibrAI) | 2023 | EACL Findings 2024 | LibrAI/do-not-answer | github.com/Libr-AI/do-not-answer | CC-BY-NC-SA 4.0 | 939 prompts × 5 risk areas / 12 harm types | Refusal-rate eval |
| **ToxicChat** | Lin et al. (LMSYS/UCSD) | 2023 | EMNLP Findings 2023 | lmsys/toxic-chat | (HF only) | CC-BY-NC 4.0 | ~10K real Vicuna-demo queries | Versioned (e.g., 0124); `user_input`, `toxicity`, `jailbreaking` |
| **BeaverTails** | PKU-Alignment (Ji et al.) | 2023 | NeurIPS D&B 2023 / arXiv:2307.04657 | PKU-Alignment/BeaverTails | github.com/PKU-Alignment/beavertails | CC-BY-NC 4.0 | 333K+ QA × 14 harm-category labels | Companion eval: BeaverTails-Evaluation (700) |
| **PKU-SafeRLHF** | PKU-Alignment | 2024 | arXiv:2406.15513 | PKU-Alignment/PKU-SafeRLHF | github.com/PKU-Alignment/safe-rlhf | CC-BY-NC 4.0 | 83.4K dual + 166.8K total prefs; 265K QA | 19 harm cats × 3 severity levels |
| RealToxicityPrompts | Gehman et al. (AI2) | 2020 | EMNLP Findings 2020 | allenai/real-toxicity-prompts | github.com/allenai/real-toxicity-prompts | Apache-2.0 | 99,442 web prompts | Pre-LLM era; toxic-continuation standard |
| **TDC 2023** (Trojan + Red Team) | CAIS / Mazeika et al. | 2023 (NeurIPS competition) | trojandetection.ai | (starter kit dl) | github.com/centerforaisafety/tdc2023-starter-kit | MIT | RT: 50 dev / 50 test × Llama-2-7B/Vicuna; Trojan: 1,000 trojaned LLMs | Two-track competition data |

### B. Safety / Trust Suites

| Name | Author/Org | Year | Paper | HF | GitHub | License | Size | Schema |
|------|-----------|------|-------|------|--------|---------|------|--------|
| **TrustLLM** | Sun, Huang et al. (Lehigh + 70 co-authors) | 2024 (ICML) | arXiv:2401.05561 | TrustLLM/TrustLLM-dataset | github.com/HowieHwong/TrustLLM | MIT | 30+ datasets, 18 subcategories | 6 trust dimensions |
| **DecodingTrust** | Wang, Li, Xie et al. (UIUC+Microsoft) | 2023 (NeurIPS Outstanding Benchmark) | arXiv:2306.11698 | (repo download) | github.com/AI-secure/DecodingTrust | CC-BY-SA 4.0 | 8 perspective tracks, ~33 sub-evals | Toxicity/bias/adv-rob/OOD/demos/privacy/ethics/fairness |
| **SafetyBench** | Zhang, Lei, Wu et al. (THU-CoAI) | 2024 (ACL) | arXiv:2309.07045 | thu-coai/SafetyBench | github.com/thu-coai/SafetyBench | Apache-2.0 | 11,435 MCQ × 7 categories | Bilingual (zh/en) |
| **Anthropic HH-RLHF** | Bai, Kadavath et al. (Anthropic) | 2022 | arXiv:2204.05862 | Anthropic/hh-rlhf | github.com/anthropics/hh-rlhf | MIT | ~170K helpfulness/harmlessness preferences | helpful-base/online/rejection-sampled, harmless-base |
| Anthropic red-team-attempts | Ganguli, Lovitt et al. | 2022 | arXiv:2209.07858 | Anthropic/hh-rlhf (subdir) | (HF only) | MIT | 38,961 multi-turn red-team transcripts | `transcript`, `min_harmlessness_score`, `num_params` |
| **AILuminate** v1.1 | MLCommons AI Safety WG | 2024–2025 | arXiv:2503.05731 | (DEMO via repo) | github.com/mlcommons/ailuminate | CC-BY (DEMO); 12K Practice public; 12K Test private | Practice ~12K + private Test ~12K | 12 hazard categories; safety grades Poor → Excellent |

### C. Prompt Injection Specific

| Name | Author/Org | Year | Paper | HF | GitHub | License | Size | Schema |
|------|-----------|------|-------|------|--------|---------|------|--------|
| **HackAPrompt 1.0 dataset** | Schulhoff et al. (Learn Prompting/UMD) | 2023 (EMNLP Best Theme) | arXiv:2311.16119 | hackaprompt/hackaprompt-dataset | github.com/PromptLabs/hackaprompt | MIT | ~600K prompts; ~67.6K curated | 10 levels × 3 LLMs; 29-technique taxonomy |
| **Open-Prompt-Injection** | Liu, Jia, Geng et al. | 2024 (USENIX Sec) | arXiv:2310.12815 | (no HF release) | github.com/liu00222/Open-Prompt-Injection | MIT | 5 attacks × 10 defenses × 7 tasks × 10 LLMs | Toolkit (not static dataset) |
| **BIPIA** | Yi et al. (Microsoft) | 2023 (KDD 2025) | arXiv:2312.14197 | (repo) | github.com/microsoft/BIPIA | MIT | ~150K cases × 5 task domains | Email/WebQA/TableQA/Summ/CodeQA bilingual (en/zh) |
| **PINT** (Prompt Injection Test) | Lakera AI | 2024 | (Lakera blog) | (dataset NOT public) | github.com/lakeraai/pint-benchmark | MIT (framework); dataset proprietary | 4,314 inputs (3,016 en + 1,298 non-en) | Held-out by design |

### D. Agentic

| Name | Author/Org | Year | Paper | HF | GitHub | License | Size | Schema |
|------|-----------|------|-------|------|--------|---------|------|--------|
| **AgentDojo** | Debenedetti et al. (ETH SpyLab) | 2024 (NeurIPS D&B) | arXiv:2406.13352 | (data inside repo) | github.com/ethz-spylab/agentdojo | AGPL-3.0 | 97 tasks + 629 security cases | Email/banking/Slack/travel envs |
| **InjecAgent** | Zhan, Liang et al. (UIUC) | 2024 (ACL Findings) | arXiv:2403.02691 | (data inside repo) | github.com/uiuc-kang-lab/InjecAgent | MIT | 1,054 cases × 17 user × 62 attacker tools | Direct harm + data exfiltration |
| **AgentHarm** | Andriushchenko et al. (Gray Swan + UK AISI) | 2024 (ICLR 2025) | arXiv:2410.09024 | ai-safety-institute/AgentHarm | (HF) | MIT (gated) | 110 base → 440 augmented × 11 harm cats | Tool-call traces |
| **WASP** | Evtimov et al. (Meta FAIR) | 2025 (NeurIPS D&B) | arXiv:2504.18575 | (data inside repo) | github.com/facebookresearch/wasp | CC-BY-NC 4.0 | Realistic web-agent hijack scenarios | Up to 86% partial-success ASR |
| **Agent-SafetyBench** | Zhang, Cui et al. (THU-CoAI) | 2024 | arXiv:2412.14470 | thu-coai/Agent-SafetyBench | github.com/thu-coai/Agent-SafetyBench | Apache-2.0 | 2,000 cases × 349 envs | 8 risk × 10 failure modes |
| **PLeak** | Hui et al. | 2024 (CCS) | arXiv:2405.06823 | (no HF) | github.com/BHui97/PLeak | MIT | Optimization framework + corpus | 68% recovery on Poe app prompts |

### E. Multimodal

| Name | Author/Org | Year | Paper | HF | GitHub | License | Size | Schema |
|------|-----------|------|-------|------|--------|---------|------|--------|
| **MM-SafetyBench** | Liu et al. | 2024 (ECCV) | arXiv:2311.17600 | (data via repo) | github.com/isXinLiu/MM-SafetyBench | Apache-2.0 | 5,040 text-image pairs × 13 scenarios | Query-relevant image attacks |
| VHELM (safety subset) | Lee, Bommasani et al. (Stanford CRFM) | 2024 | arXiv:2410.07112 | (run on HELM) | github.com/stanford-crfm/helm | Apache-2.0 | 21 datasets × 9 aspects | Safety/toxicity/bias/robustness as 4 of 9 |
| RTVLM (Red-Team VLM) | Li et al. | 2024 (ACL Findings) | arXiv:2401.12915 | (no canonical mirror) | (URL not verified) | (not verified) | 12 subtasks × 4 aspects | First red-team VLM dataset |
| JailBreakV-28k (multimodal subset) | (see A) | 2024 | arXiv:2404.03027 | JailbreakV-28K/JailBreakV-28k | github.com/EddyLuo1232/JailBreakV_28K | MIT | 8K image-based attacks (subset) | Nature/Random/Typography/SD/Blank |
| **MultiTrust** | Zhang et al. (Tsinghua + RealAI) | 2024 (NeurIPS D&B) | arXiv:2406.07057 | thu-ml/MultiTrust | github.com/thu-ml/MMTrustEval | Apache-2.0 | 32 tasks × 21 MLLMs | Truthfulness/safety/robustness/fairness/privacy |

### F. Specialized (regional / capability-specific)

| Name | Author/Org | Year | Paper | HF | GitHub | License | Size | Schema |
|------|-----------|------|-------|------|--------|---------|------|--------|
| **WMDP** | Li, Pan, Gopal et al. (CAIS+Scale) | 2024 (ICML) | arXiv:2403.03218 | cais/wmdp; cais/wmdp-corpora | github.com/centerforaisafety/wmdp | MIT (filtered) | 3,668 MCQ (bio + cyber + chem) | Hazardous-knowledge eval + RMU benchmark |
| **CoSafe** | Yu et al. | 2024 (EMNLP) | arXiv:2406.17626 | (data via repo) | github.com/ErxinYu/CoSafe-Dataset | MIT | 1,400 multi-turn dialogues × 14 cats | Coreference-based multi-turn jailbreaks |
| SC-Safety / SuperCLUE-Safety | Xu et al. (CLUE) | 2023 | arXiv:2310.05818 | (no HF mirror) | (cluebenchmarks.com) | Custom (CLUE) | 4,912 open-ended Chinese Qs × 20+ subdims | Multi-round adversarial Chinese safety |
| CHiSafetyBench | Zhang et al. | 2024 | arXiv:2406.10311 | (URL not verified) | (URL not verified) | (not verified) | 1,861 MCQ + 462 risky open-ended | Hierarchical Chinese safety: 5 areas × 31 cats |
| **PromptBench / PromptRobust** | Zhu, Wang et al. (Microsoft) | 2023 | arXiv:2306.04528 + 2312.07910 | (data via repo) | github.com/microsoft/promptbench | MIT | 4,032 adv prompts × 13 datasets × 8 tasks (~567K) | Char/word/sent/semantic attacks framework |
| **StrongREJECT** | Souly, Lu, Bowen et al. (Berkeley) | 2024 (NeurIPS D&B) | arXiv:2402.10260 | (package) | github.com/dsbowen/strong_reject | MIT | 313 forbidden prompts + rubric judge | Spearman 0.90 with humans |
| **SALAD-Bench** | Li, Dong et al. (OpenSafetyLab) | 2024 (ACL Findings) | arXiv:2402.05044 | walledai/SaladBench (mirror); OpenSafetyLab/MD-Judge-v0.1 | github.com/OpenSafetyLab/SALAD-BENCH | Apache-2.0 | 21K base × 6 domains × 16 tasks × 65 cats | QA + MCQ; ships MD-Judge / MC-Judge |
| **XSTest** | Röttger, Kirk, Vidgen et al. | 2024 (NAACL) | arXiv:2308.01263 | walledai/XSTest (mirror) | github.com/paul-rottger/xstest | CC-BY-4.0 | 250 safe (10 types) + 200 unsafe contrasts | Over-refusal / exaggerated safety |
| SimpleSafetyTests | Vidgen, Kirk et al. | 2023 | arXiv:2311.08370 | Bertievidgen/SimpleSafetyTests | (HF only) | CC-BY-NC-4.0 | 100 prompts × 5 harm areas | Smoke-test |

### G. Memorization / Privacy

| Name | Author/Org | Year | Paper | HF | GitHub | License | Size | Schema |
|------|-----------|------|-------|------|--------|---------|------|--------|
| **WikiMIA** | Shi, Ajith, Xia et al. | 2023 (ICLR 2024) | arXiv:2310.16789 | swj0419/WikiMIA | github.com/swj0419/detect-pretrain-code | MIT | 4 length splits (32, 64, 128, 256) | Label 0 = unseen, 1 = seen |
| LLM-PBE Enron-Email | LLM-PBE consortium (Li et al.) | 2024 (VLDB) | LLM-PBE paper | LLM-PBE/enron-email | (toolkit) | (per Enron license) | ~500K Enron emails; 4K train/2K attack | PII extraction (email/phone/name) |
| **TOFU** | Maini, Feng, Schwarzschild et al. | 2024 | arXiv:2401.06121 | locuslab/TOFU | github.com/locuslab/tofu | MIT | 200 fictitious authors × 20 QA = 4,000 | Forget/retain/real-authors/world-facts splits |
| Pile-CC | EleutherAI (Pile component) | 2020 | arXiv:2101.00027 | monology/pile-uncopyrighted (mirror) | github.com/EleutherAI/the-pile | MIT (toolkit); per-source content | ~227 GB CommonCrawl subset | Standard for "training-data extraction" |

### H. Hallucination / Truthfulness (related)

| Name | Author/Org | Year | Paper | HF | GitHub | License | Size | Schema |
|------|-----------|------|-------|------|--------|---------|------|--------|
| **TruthfulQA** | Lin, Hilton, Evans (Oxford+OpenAI) | 2022 (ACL) | arXiv:2109.07958 | truthful_qa | github.com/sylinrl/TruthfulQA | Apache-2.0 | 817 Qs × 38 categories | MC1, MC2, generation modes |
| **HalluLens** | Bang et al. (Meta FAIR) | 2025 (ACL) | arXiv:2504.17550 | (data via repo) | github.com/facebookresearch/HalluLens | CC-BY-NC 4.0 | 3 dynamic extrinsic tasks | Dynamic test gen to prevent leakage |
| HaluEval | Li et al. (RUC AI Box) | 2023 (EMNLP) | arXiv:2305.11747 | (data in repo) | github.com/RUCAIBox/HaluEval | MIT | 5K queries + 30K examples (QA/dialog/summ) | Hallucinated-vs-correct pairs |
| **FActScore** | Min et al. (UW + Meta) | 2023 (EMNLP) | arXiv:2305.14251 | `pip install factscore` | github.com/shmsw25/FActScore | MIT | Atomic-fact decomposition | Long-form factuality metric |

---

## Leaderboards

| Name | URL | Organization | Tests | Refresh | Top entries (May 2026) |
|------|-----|--------------|-------|---------|------------------------|
| **JailbreakBench Leaderboard** | jailbreakbench.github.io | Chao et al. consortium | Attack/defense ASR on JBB-Behaviors vs Llama-2-7B/Vicuna-13B/GPT-3.5/4 | Continuous (PR-driven) | PAIR, GCG, prompt-RS variants — visit for live |
| **HarmBench Leaderboard** | harmbench.org | CAIS | 18 attacks × 33 models on 510 behaviors | Periodic (CAIS-curated) | GCG, PAIR, AutoDAN, TAP; Llama-3 + R2D2 most robust |
| **TrustLLM Leaderboard** | trustllmbenchmark.github.io/TrustLLM-Website/leaderboard.html | Lehigh consortium | 6 trust dims × 18 sub-cats | Periodic | Closed APIs (GPT-4, Claude) generally lead |
| **AILuminate Public** | ailuminate.mlcommons.org/benchmarks | MLCommons | 12 hazard categories × English (fr/zh/hi rolling) | Quarterly | Top closed = "Excellent"; many open = "Good"–"Fair" |
| **Gray Swan Arena** | app.grayswan.ai/arena/leaderboard/global | Gray Swan AI | Per-challenge: agent RT, multimodal, indirect PI, safeguards | Continuous | Live; per-challenge sub-leaderboards |
| **LMSYS / LMArena Chatbot Arena** | lmarena.ai | LMArena | Crowdsourced pairwise human preference Elo | Continuous | Claude 4-class, Gemini 3-class, GPT-class clustered ~1,490–1,505 |
| **AgentDojo Results** | agentdojo.spylab.ai/results | ETH SpyLab | Utility + targeted-attack on 97 tasks × 629 variants | Periodic | GPT-4o + Claude 3.5 Sonnet most utility; both vulnerable to PI |
| HF Open LLM Leaderboard v2 (archived) | huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard | HF | MMLU-Pro, IFEval, BBH, MUSR, MATH, GPQA | Frozen (retired 2025) | Archive only |
| **DEF CON AI Village CTF** | aivillage.org | AI Village (DEF CON) | GRT-1 (2023), GRT-2 (2024), GRT-3 (2025) | Annual | GRT-1: 2,244 hackers / 17K attempts / 8 LLMs |

---

## CTFs / Public Red-Team Programs

| Name | URL | Operator | Format | Eligibility | Status (May 2026) |
|------|-----|----------|--------|-------------|--------------------|
| **Lakera Gandalf** | gandalf.lakera.ai | Lakera | 7 standard levels + Adventures (Reverse/Misinformation/Summarizer) + adaptive Level 8 | Open / no signup | Active |
| **Anthropic Model Safety Bug Bounty** | anthropic.com/news/testing-our-safety-defenses-with-a-new-bug-bounty-program | Anthropic (HackerOne) | Universal-jailbreak finding bounties; Constitutional Classifiers + ASL-3 Deployment Safeguards | Vetted; up to $25-26K per universal jailbreak | Active; Feb 2025 expansion paid out $55K |
| **DEF CON AI Village GRT** | aivillage.org | AI Village + Humane Intelligence + NIST/CISA | In-person CTF; GRT-3 attacks on model-card evals | DEF CON attendees; remote portals during event | Active annually; GRT-3 ran DEF CON 33 (Aug 2025) |
| **HackAPrompt** | hackaprompt.com | Learn Prompting | 10 levels × 3 victim LLMs; data released publicly | Open; cash prizes | HackAPrompt 1.0 closed; 2.0 launched 2025 |
| **Microsoft AI Bug Bounty** | microsoft.com/en-us/msrc/bounty-ai | Microsoft MSRC | Copilot, Bing GenAI, Copilot M365 etc. | Open; MSRC AI Severity rubric | Active; up to $30K bounties |
| **Gray Swan Arena** | app.grayswan.ai/arena | Gray Swan AI | Continuous: agent RT, multimodal, indirect PI, safeguards | Free signup; cash prize pools | Active; Indirect PI Challenge ran Nov 5–26, 2025 ($40K, co-sponsored Anthropic + Meta) |
| **Prompt Airlines** | promptairlines.com | Wiz Research | 5-level fictional airline-chatbot CTF | Open / no signup | Active since July 2024 |
| **Doublespeak** | doublespeak.chat | Forces Unseen | 7 free + 11 premium levels | Free + paid | Active |
| **LLM CTF @ SaTML** | llmctf.com | ETH SPY Lab + SaTML conference | Two-phase: defense submission then attack | Open registration | Annual; SaTML 2024+2025 held; 2026 winter announcement expected |
| HackerOne AIxCC / per-vendor VDPs | hackerone.com/ai-safety + per-vendor | HackerOne + OpenAI, xAI, etc. | Coordinated VDP across multiple AI vendors | Per-program | Active; most major labs have running programs |
| **AgentDojo (continuous)** | github.com/ethz-spylab/agentdojo | ETH SpyLab | Self-host attack/defense; PR-based leaderboard | Open | Active |

---

## Eval Stack Recommendations (production jailbreak robustness)

If forced to pick exactly three datasets — one classification, one open-ended generation, one agentic:

1. **WildGuardMix (classification)** — 92K labeled prompt/response pairs across 13 risk categories with explicit harmful/benign/refusal labels and multi-task design. Strongest open alternative to proprietary moderation APIs.

2. **HarmBench + StrongREJECT judge (open-ended generation)** — HarmBench's 510 behaviors give breadth (standard/contextual/multimodal); StrongREJECT's rubric-based or fine-tuned judge fixes the inflated-ASR bug that plagued AdvBench-style refusal-string eval. Together yield Spearman ~0.9 with humans on whether a generation is *both* compliant and useful to an attacker.

3. **AgentDojo (agentic)** — Only widely-adopted dynamic environment with *realistic* tool surfaces and a security model that separates utility from attack-success. 629 injected test cases cover the indirect-PI threat that defines real production agent risk in 2026.

---

## Verification Notes

- **DoNotAnswer** HF path `LibrAI/do-not-answer` is plausible; GitHub `Libr-AI/do-not-answer` verified; HF mirror exists (Japanese mirror confirmed at `kunishou/do-not-answer-ja`).
- **ForbiddenQuestions** — paper exists, dataset is published with JailbreakHub release in TrustAIRLab ecosystem; HF path `TrustAIRLab/forbidden_question_set` plausible, **not directly verified** in this session.
- **RTVLM** — paper verified (arXiv:2401.12915); canonical GitHub or HuggingFace URL **not verified**.
- **CHiSafetyBench** — paper verified (arXiv:2406.10311); GitHub / HF dataset URL **not verified**.
- **CCH-Bench** — does NOT appear to exist as distinct named benchmark; likely confusion with CHiSafetyBench.
- **SC-Safety / SuperCLUE-Safety** — paper verified (arXiv:2310.05818); access via cluebenchmarks.com, no HF mirror confirmed.
- **PINT (Lakera)** — dataset intentionally private (Lakera withholds to prevent overfitting); framework is public.
- **AILuminate Practice** — DEMO Creative-Commons subset is public on GitHub; full Practice (12K) and private Test (12K) require organizational access via MLCommons.
- **HackAPrompt 2.0** — competition launched 2025; specific dataset path not verified in this session.
- **Pile-CC** — content takedowns and license variation; canonical URL has shifted; treat any specific HF mirror as dated.

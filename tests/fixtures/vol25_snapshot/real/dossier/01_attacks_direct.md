# Direct Attack Research — Hand-Crafted, Encoding, White-Box, Black-Box

**Compiled:** May 2026 | **Coverage:** 2022-2026 (emphasis 2024-2026)
**Verification:** every arXiv ID confirmed against arxiv.org abstract or conference proceedings unless `(unverified)`. See verification footer.

This file covers attack-side research where the attacker directly prompts the model. Indirect/agentic/multimodal attacks live in `02_attacks_indirect_agentic_multimodal.md`.

---

## A1. Direct Prompt Injection (Foundational)

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| Ignore Previous Prompt: Attack Techniques For Language Models | Perez & Ribeiro (2022) | NeurIPS ML Safety Workshop 2022 (Best Paper) | arXiv:2211.09527 | agencyenterprise/PromptInject | First systematic framework for prompt injection on GPT-3 | Defines **goal hijacking** vs **prompt leaking** as the two canonical PI attack classes |
| Evaluating the Susceptibility of Pre-Trained LMs via Handcrafted Adversarial Examples | Branch et al. (2022) | arXiv preprint | arXiv:2209.02128 | — | Earliest documentation of PI vulnerability in GPT-3 | Concurrent with Perez/Ribeiro; established that handcrafted inputs reliably override system prompts |
| Goodside "Translate to French / Haha pwned" demonstration | Riley Goodside (Sep 2022) | Twitter / Simon Willison blog | (no arXiv) `(unverified)` | — | Viral early demo that brought PI to public attention | Simon Willison named the attack class "prompt injection" |
| Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect PI | Greshake et al. (2023) | ACM AISec 2023 | arXiv:2302.12173; doi 10.1145/3605764.3623985 | — | Foundational **indirect** PI taxonomy: data-borne attacks (web, retrieval, plugins) | Established remote-code-execution analogy; full LLM compromise via retrieved content |
| HouYi: Prompt Injection attack against LLM-integrated Applications | Liu et al. (2023) | USENIX Security 2024 | arXiv:2306.05499 | LLMSecurity/HouYi | Black-box PI framework against 36 real LLM-integrated apps | 31/36 apps vulnerable; 10 vendors confirmed (Notion etc.) |
| Jailbreaking ChatGPT via Prompt Engineering: An Empirical Study | Liu et al. (2023) | TOSEM (extended) | arXiv:2305.13860 | — | Classification of 10 patterns / 3 categories of jailbreak prompts | Empirical taxonomy of 78 distinct prompts; 8 prohibited scenarios |
| Tensor Trust: Interpretable Prompt Injection Attacks from an Online Game | Toyer et al. (2023) | ICLR 2024 | arXiv:2311.01011 | — | 126K+ human-generated PI attacks + 46K defenses | Largest human-generated adversarial dataset; **prompt extraction** vs **prompt hijacking** |
| Ignore This Title and HackAPrompt | Schulhoff et al. (2023) | EMNLP 2023 (Best Theme) | arXiv:2311.16119 | — | 600K+ adversarial prompts, 29-technique taxonomy | Discovered "Context Overflow" attack; key takeaway: prompt-based defenses don't work |
| Formalizing and Benchmarking Prompt Injection Attacks and Defenses | Liu et al. (2023) | USENIX Security 2024 | arXiv:2310.12815 | liu00222/Open-Prompt-Injection | First formal framework; 5 attacks × 10 defenses × 10 LLMs × 7 tasks | Common benchmark + taxonomy of separator/escape/fake-completion/combined attacks |
| Benchmarking and Defending Against Indirect Prompt Injection (BIPIA) | Yi et al. (2023) | KDD 2025 | arXiv:2312.14197 | microsoft/BIPIA | First broad indirect-PI benchmark | 5 scenarios × 250 attacker goals; identifies two root causes |
| Automatic and Universal Prompt Injection Attacks against LLMs | Liu et al. (2024) | arXiv preprint | arXiv:2403.04957 | SheltonLiu-N/Universal-Prompt-Injection | First gradient-based universal PI; introduces M-GCG | Bridges PI-attacks with the GCG family |
| Neural Exec: Learning Execution Triggers for Prompt Injection | Pasquini et al. (2024) | ACM AISec 2024 | arXiv:2403.03792 | pasquini-dario/LLM_NeuralExec | Differentiable search for novel-shape PI triggers | Triggers persist through multi-stage RAG pipelines |
| JudgeDeceiver: Optimization-based PI on LLM-as-a-Judge | Shi et al. (2024) | ACM CCS 2024 | arXiv:2403.17710 | ShiJiawenwen/JudgeDeceiver | Gradient-based PI against LLM-as-judge selection | 97.6% ASR on MT-Bench; bypasses known-answer/perplexity detection |
| PoisonedRAG: Knowledge Corruption Attacks to RAG | Zou et al. (2024) | USENIX Security 2025 | arXiv:2402.07867 | sleeepeer/PoisonedRAG | Inject 5 poisoned texts into 10⁶-doc DB to control answers | 97/99/91% ASR on NQ/HotpotQA/MS-MARCO |
| PoisonedAlign: Enhancing PI Attacks via Poisoning Alignment | Shao et al. (2024) | ACM AISec 2025 | arXiv:2410.14827 | Sadcardation/PoisonedAlign | Poison alignment-data to make models more PI-vulnerable | 10% poisoned ORCA-DPO → +0.33 ASR |
| An Early Categorization of Prompt Injection Attacks on LLMs | Rossi et al. (2024) | arXiv preprint | arXiv:2402.00898 | — | Vulnerability checklist for LLM-interface developers | Direct vs indirect taxonomy |

---

## A2. Hand-Crafted Jailbreaks

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| DAN ("Do Anything Now") evolution | Reddit/community (Dec 2022 – 2024) | (community) | (no arXiv) `(unverified)` | 0xk1h0/ChatGPT_DAN | Persona-roleplay jailbreaks instructing model to simulate unrestricted alter-ego | DAN 5.0 introduced 35-token "life counter"; 12-version arms race |
| Multi-step Jailbreaking Privacy Attacks on ChatGPT | Li et al. (2023) | EMNLP Findings 2023 | arXiv:2304.05197 | — | Multi-stage PII extraction via roleplay scaffolding | Foundational for chained attacks |
| Jailbroken: How Does LLM Safety Training Fail? | Wei, Haghtalab, Steinhardt (2023) | NeurIPS 2023 | arXiv:2307.02483 | — | Two failure modes: **competing objectives** + **mismatched generalization** | Theoretical scaffold the field still uses |
| "Do Anything Now": Characterizing In-The-Wild Jailbreak Prompts | Shen et al. (2023) | ACM CCS 2024 | arXiv:2308.03825 | verazuo/jailbreak_llms | Empirical analysis of 1,405 in-the-wild jailbreaks (Dec 2022 – Dec 2023) | 131 jailbreak communities; 5 prompts achieve 0.95 ASR |
| DeepInception: Hypnotize LLM to Be Jailbreaker | Li et al. (2023) | COLM 2024 | arXiv:2311.03191 | tmlr-group/DeepInception | Nested fictional scenes that recursively unlock harmful content | Inspired by Milgram experiment |
| ReNeLLM: Generalized Nested Jailbreak Prompts | Ding et al. (2024) | NAACL 2024 | arXiv:2311.08268 | NJUNLP/ReNeLLM | Two-stage rewriting + scenario nesting | 76.61% time reduction vs GCG |
| Multilingual Jailbreak Challenges in LLMs | Deng et al. (2023) | ICLR 2024 | arXiv:2310.06474 | DAMO-NLP-SG/multilingual-safety-for-LLMs | Cross-lingual jailbreaks: ChatGPT 80.92%, GPT-4 40.71% unsafe | Self-Defense framework for multilingual safety FT |
| Crescendo Multi-Turn LLM Jailbreak | Russinovich et al. (Microsoft 2024) | USENIX Security 2025 | arXiv:2404.01833 | (Microsoft PyRIT) | Gradual benign-to-harmful escalation across <5 turns | Microsoft disclosure; exploits self-output pattern-following |
| Skeleton Key — Microsoft disclosure | Russinovich (Microsoft, June 2024) | Microsoft Security Blog | (no arXiv) `(unverified — vendor blog)` | — | Multi-turn behavior-modification jailbreak | Worked on Llama3-70b, Gemini Pro, GPT-3.5/4o, Mistral, Claude 3 Opus |
| Many-shot Jailbreaking | Anil et al. (Anthropic 2024) | NeurIPS 2024 | (Anthropic technical report) `(no arXiv ID confirmed)` | — | Hundreds of faux Q/A demos in single prompt → safety bypass | Power-law scaling with shots; enabled by 1M-token contexts |
| Best-of-N Jailbreaking | Hughes et al. (Anthropic 2024) | arXiv preprint | arXiv:2412.03556 | — | Random prompt augmentations until harmful response | 89% on GPT-4o, 78% on Claude 3.5 Sonnet at N=10K |
| Persuasive Adversarial Prompts (PAP) | Zeng et al. (2024) | ACL 2024 | arXiv:2401.06373 | CHATS-lab/persuasive_jailbreaker | Taxonomy of 40 persuasion techniques | 92% ASR on Llama-2-7b/GPT-3.5/GPT-4 with no optimization |
| Bad Likert Judge | Palo Alto Unit 42 (Dec 2024) | Vendor blog | (no arXiv) `(unverified)` | — | LLM acts as Likert-scale "judge" → high-Likert example contains harmful content | +60% ASR vs single-turn baseline |
| Jailbreak Attacks and Defenses Against LLMs: A Survey | Yi et al. (2024) | arXiv preprint | arXiv:2407.04295 | — | Comprehensive jailbreak taxonomy | Black-box vs white-box × prompt-level vs model-level matrix |
| Adversarial Poetry as a Universal Single-Turn Jailbreak | Bartolo et al. (2025) | arXiv preprint | arXiv:2511.15304 | — | Convert harmful prompts to verse → 18× ASR vs prose | 62% avg ASR (handcrafted); >90% on some providers |

---

## A3. Encoding and Obfuscation Attacks

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| Low-Resource Languages Jailbreak GPT-4 | Yong et al. (2023) | ICLR Workshop SeT-LLM | arXiv:2310.02446 | — | Translate harmful prompts to Zulu/Scots-Gaelic | 79% ASR on AdvBench via low-resource translation |
| GPT-4 Is Too Smart To Be Safe via Cipher (CipherChat) | Yuan et al. (2023) | ICLR 2024 | arXiv:2308.06463 | RobustNLP/CipherChat | Caesar/ASCII/Morse/Unicode ciphers + few-shot demos | SelfCipher (natural-language only) outperforms; 70.9% unsafe on GPT-4 English |
| ArtPrompt: ASCII Art-based Jailbreak Attacks | Jiang et al. (2024) | ACL 2024 | arXiv:2402.11753 | uw-nsl/ArtPrompt | Mask safety words, replace with ASCII art | First **vision-in-text** jailbreak; ViTC benchmark |
| CodeChameleon: Personalized Encryption Framework | Lv et al. (2024) | arXiv preprint | arXiv:2402.16717 | huizhang-L/CodeChameleon | Reformulate as code completion + embedded decrypt fn | 86.6% ASR on GPT-4-1106 |
| WordGame: Simultaneous Obfuscation in Query and Response | Zhang et al. (2024) | NAACL Findings 2025 | arXiv:2405.14023 | — | Replace harmful words with word puzzles in query AND response | >92% ASR on Llama-2-7b, GPT-3.5/4 |
| Endless Jailbreaks with Bijection Learning | Huang et al. (Haize 2024) | ICLR 2025 | arXiv:2410.01294 | haizelabs/bijection-learning | Teach arbitrary string-string bijection in-context | 86.3% ASR on Claude 3.5 Sonnet; larger models *more* vulnerable |
| FlipAttack: Jailbreak via Flipping | Liu et al. (2024) | ICML 2025 | arXiv:2410.02832 | yueliu1999/FlipAttack | 4 left-side text-flipping modes | ~98% ASR on GPT-4o; ~98% bypass on 5 guardrails |
| Plentiful Jailbreaks with String Compositions | Huang & Tang (Haize 2024) | NeurIPS Workshop SoLaR | arXiv:2411.01084 | — | 20 invertible string-transformation primitives composed | Generalizes leetspeak/Base64/ROT13 into composable framework |
| StructuralSleight: Uncommon Text-Encoded Structure | Xiao et al. (2024) | arXiv preprint | arXiv:2406.08754 | — | Discrete optimization over uncommon encoded structures | 94.62% ASR on GPT-4o |
| ASCII Smuggling via Unicode Tag Block (E0000-E007F) | Goodside / Thacker / Rehberger (2024) | Industry blog disclosures | (no arXiv) `(unverified)` | — | Use deprecated Unicode Tag block (invisible to humans, read by LLMs) | Hidden in PDFs/images/databases; bypasses human-in-loop |
| StegoAttack: Steganographic LLM Jailbreaks | (2025) | arXiv preprint | arXiv:2505.16765 | — | Embed harmful query within benign paragraph via first-letter steganography | 95.5% ASR; ASR drop <27% even under detectors |
| Jailbreaking LLMs via Cipher Characters | (2024) | arXiv preprint | arXiv:2405.20413 | — | Cipher-character substitutions to evade moderation | Targets the moderator, not the policy model |

---

## A4. White-Box Optimization Attacks

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| **GCG**: Universal and Transferable Adversarial Attacks on Aligned LLMs | Zou et al. (2023) | arXiv preprint | arXiv:2307.15043 | llm-attacks/llm-attacks | Greedy Coordinate Gradient: gradient-guided token search appended as suffix | Foundational white-box; transfers to ChatGPT/Claude/Bard/Llama-2 |
| **ARCA**: Auditing LLMs via Discrete Optimization | Jones et al. (2023) | ICML 2023 | arXiv:2303.04381 | — | Joint discrete optimization over input AND output | Pre-GCG discrete optimization |
| **AutoDAN**: Stealthy Jailbreak Prompts via Genetic Algorithm | Liu et al. (2023) | ICLR 2024 | arXiv:2310.04451 | SheltonLiu-N/AutoDAN | Hierarchical genetic algorithm over DAN-style prompts | Stealthy + semantically meaningful; bypasses perplexity defenses |
| **COLD-Attack**: Stealthy + Controllable Jailbreaks | Yu et al. (2024) | ICML 2024 | arXiv:2402.08679 | Yu-Fangxu/COLD-Attack | Energy-based Constrained Decoding with Langevin Dynamics | Unifies fluency/sentiment/coherence constraints |
| **BEAST**: Fast Adversarial Attacks in One GPU Minute | Sadasivan et al. (2024) | ICML 2024 | arXiv:2402.15570 | vinusankars/BEAST | Beam-search-based gradient-free attack | 89% ASR on Vicuna-7B in <1 min vs >1 hr for GCG |
| **AmpleGCG**: Universal Generative Model of Adversarial Suffixes | Liao & Sun (2024) | COLM 2024 | arXiv:2404.07921 | OSU-NLP-Group/AmpleGCG | Train generative model on intermediate GCG successes | 200 suffixes in 4 sec/query; 99% ASR on GPT-3.5 |
| AmpleGCG-Plus | Kumar, Liao et al. (2024) | arXiv preprint | arXiv:2410.22143 | (OSU-NLP-Group) | Improved AmpleGCG | Higher ASR with fewer attempts |
| **I-GCG**: Improved Optimization-Based Jailbreaking | Jia et al. (2024) | arXiv preprint | arXiv:2405.21018 | — | Multi-coordinate updates + diverse target templates | ~100% ASR; outperforms vanilla GCG |
| **Probe Sampling**: Accelerating GCG | Zhao et al. (2024) | NeurIPS 2024 | arXiv:2403.01251 | zhaoyiran924/Probe-Sampling | Use small draft model to filter candidates | 5.6× speedup on Llama-2-7b-chat |
| **AutoDAN-Turbo**: Lifelong Strategy Self-Exploration | Liu et al. (2024) | ICLR 2025 (Spotlight) | arXiv:2410.05295 | SaFoLab-WISC/AutoDAN-Turbo | Strategy library accumulates discovered tactics | 88.5% on GPT-4-1106-turbo |
| **AdvPrompter**: Fast Adaptive Adversarial Prompting | Paulus et al. (2024) | ICLR 2025 | arXiv:2404.16873 | facebookresearch/advprompter | Train auxiliary LLM to generate human-readable suffixes | ~800× faster than GCG |
| **Soft Prompt Threats**: Embedding-Space Attacks | Schwinn et al. (2024) | NeurIPS 2024 | arXiv:2402.09063 `(unverified ID)` | SchwinnL/LLM_Embedding_Attack | Continuous-embedding gradient descent (no token discretization) | Stronger per-target attack |
| **DrAttack**: Decomposition + Reconstruction | Li et al. (2024) | EMNLP Findings 2024 | arXiv:2402.16914 | xirui-li/DrAttack | Decompose → reconstruct via in-context demos → synonym search | 78% ASR on GPT-4 in 15 queries |
| **PRP**: Universal Perturbations to Attack Guard-Rails | Mangaokar et al. (2024) | ACL 2024 | arXiv:2402.15911 | — | Two-stage: universal prefix for guard model → propagate to response | 88% ASR vs blind GPT-3.5 |
| **I-FSJ**: Improved Few-Shot Jailbreaking | Zheng et al. (2024) | NeurIPS 2024 | arXiv:2406.01288 | sail-sg/I-FSJ | Special-token injection + demo-level random search | >80-95% ASR on Llama-2-7B/Llama-3-8B |
| **Universal Jailbreak Backdoors from Poisoned Human Feedback** | Rando & Tramèr (2023) | ICLR 2024 | arXiv:2311.14455 | — | Poison ≥5% of RLHF data → universal trigger word | First universal backdoor in RLHF |

---

## A5. Black-Box Optimization / LLM-on-LLM Attacks

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| **MasterKey**: Automated Jailbreak Across Multiple Chatbots | Deng et al. (2023) | NDSS 2024 | arXiv:2307.08715 | LLMSecurity/MasterKey | Time-based defense reverse-engineering + fine-tuned attacker | 21.58% ASR on commercial chatbots vs 7.33% baseline |
| **GPTFUZZER**: Auto-Generated Jailbreak Prompts | Yu et al. (2023) | arXiv preprint | arXiv:2309.10253 | sherdencooper/GPTFuzz | AFL-style fuzzing with mutate operators on seed templates | >90% ASR on ChatGPT/Llama-2 |
| **FuzzLLM**: Universal Fuzzing Framework | Yao et al. (2023) | ICASSP 2024 | arXiv:2309.05274 | RainJamesY/FuzzLLM | 3 base classes (Role Play, Output Constrain, Privilege Escalation) | Black-box, combo-attack composition |
| **PAIR**: Black-Box LLMs in Twenty Queries | Chao et al. (2023) | NeurIPS 2023 R0-FoMo | arXiv:2310.08419 | patrickrchao/JailbreakingLLMs | Attacker-LLM iteratively refines vs target-LLM | <20 queries; semantic jailbreaks |
| **TAP**: Tree of Attacks | Mehrotra et al. (2023) | NeurIPS 2024 | arXiv:2312.02119 | RICommunity/TAP | Tree-of-thought search + pruning | >80% ASR on GPT-4-Turbo/4o; 60% fewer queries than PAIR |
| **Rainbow Teaming**: Quality-Diversity Adversarial Generation | Samvelyan et al. (2024) | NeurIPS 2024 | arXiv:2402.16822 | — | MAP-Elites over adversarial prompt archive | Hundreds of diverse jailbreaks with >90% ASR |
| **Adaptive Attacks** on Safety-Aligned LLMs | Andriushchenko, Croce, Flammarion (2024) | ICLR 2025 | arXiv:2404.02151 | tml-epfl/llm-adaptive-attacks | Logprob-guided random search on suffix targeting "Sure" | 100% ASR on Vicuna/Mistral/Phi-3/Llama-2/3/Gemma/GPT-3.5/4o |
| **H-CoT**: Hijacking Chain-of-Thought Safety Reasoning | Kuo et al. (2025) | arXiv preprint | arXiv:2502.12893 | dukeceicenter/jailbreak-reasoning-openai-o1o3-deepseek-r1 | Use displayed CoT of o1/o3/R1 against itself | Refusal 98% → <2% |
| **Adversarial Reasoning at Jailbreaking Time** | Sabbaghi et al. (2025) | ICML 2025 | arXiv:2502.01633 | — | Test-time-compute search using continuous loss signal | 100% ASR on DeepSeek-R1 |
| **J2 (Jailbreaking to Jailbreak)** | Scale AI Labs (2025) | arXiv preprint | arXiv:2502.09638 | — | Once jailbroken, refusal-trained LLMs become attackers | J2(Sonnet-3.7) → 0.975 ASR vs GPT-4o |
| **Siege**: Autonomous Multi-Turn Jailbreaking | (2025) | arXiv preprint | arXiv:2503.10619 | — | BFS-style multi-turn tree search | Multi-turn extension of TAP |
| **Persona Prompts**: GA-evolved persona jailbreaks | (2025) | arXiv preprint | arXiv:2507.22171 | — | Genetic-algorithm evolved persona prompts | -50-70% refusal; +10-20% synergy with existing attacks |
| **Speak Easy**: Multi-step + Multilingual Interaction | (2025) | arXiv preprint | arXiv:2502.04322 | — | Simple multi-step + multilingual framework with HarmScore | New metric: actionability + informativeness |

---

## Attack Surface Trends 2024–2026

**Aggressively growing vectors (last 18 months):**

1. **Multi-turn / agentic exploitation.** Crescendo (Microsoft, 2024), Skeleton Key (Microsoft, 2024), Bad Likert Judge (Unit 42, 2024), Siege (2025), AgentDojo (NeurIPS 2024) collectively pivot the field from single-turn injection to *conversation-graph* attacks where each turn is benign but the trajectory is harmful. Tool-using agents (InjecAgent, AgentDojo, MCP tool-poisoning) introduced a new attack surface in 2024–2026: the model now has *capabilities*, not just outputs.

2. **Reasoning-model attacks.** With o1/o3, R1, and Gemini-Flash-Thinking exposing CoT, H-CoT (2025), Adversarial Reasoning at Jailbreaking Time (2025), and J2 (2025) weaponize the reasoning trace itself.

3. **Encoding/obfuscation has bifurcated into "endless" attacks.** Bijection Learning (2024), Plentiful Jailbreaks (2024), FlipAttack (2024), and Adversarial Poetry (2025) replace fixed-cipher attacks with *combinatorial families* of encodings teachable in-context, defeating signature-based detectors.

**Plateaued / replaced vectors:**

1. **Pure DAN-style persona roleplay.** OpenAI/Anthropic patches and aligned RLHF have neutralized DAN 1.0–11 in production. Persona attacks survive only as a *primitive* inside hybrid attacks.
2. **Vanilla GCG.** Single-target GCG without acceleration (Probe Sampling), generative amplification (AmpleGCG), or improved coordinates (I-GCG) is now baseline. Non-readable suffixes are caught by perplexity filters; AdvPrompter, COLD-Attack, AutoDAN moved the field toward fluent suffixes.

**Emerging vectors to watch in 2026:**

1. **Indirect PI through MCP and tool descriptions.** Tool-poisoning at the MCP-server-description level lets an attacker compromise *every* downstream agent that connects to the server.
2. **Steganographic multimodal channels.** StegoAttack (2025) hides payloads in cover paragraphs; ASCII-smuggling via Unicode tag block remains under-mitigated at most API gateways. Expect 2026 work on cross-modal hidden-channel composition.

---

## Verification Footer

Entries marked `(unverified)`:
- **Goodside "Translate to French"** — Twitter post + Simon Willison blog only; no arXiv equivalent.
- **DAN ("Do Anything Now") prompt evolution** — Reddit/community origin; the academic study (Shen et al. arXiv:2308.03825) catalogs the wild prompts.
- **Skeleton Key** — Microsoft Security Blog disclosure (June 2024); no arXiv ID.
- **Bad Likert Judge** — Palo Alto Unit 42 vendor blog (Dec 2024); no arXiv version.
- **ASCII Smuggling via Unicode Tag Block** — Goodside/Thacker/Rehberger blog series + AWS/Cisco/Promptfoo defense write-ups; industry-disclosed only.
- **Many-shot Jailbreaking (Anil et al.)** — Anthropic-hosted technical PDF + NeurIPS 2024 proceedings entry; no corresponding arXiv ID. The often-cited "arXiv:2404.02151" actually maps to Andriushchenko et al.'s adaptive-attacks paper.
- **Soft Prompt Threats (Schwinn et al. 2024)** — GitHub repo and citations confirm a NeurIPS 2024 paper; arXiv:2402.09063 is best-estimate but should be re-verified.

All other arXiv IDs verified against arxiv.org abstract pages or canonical conference proceedings URL.

**Total entries:** A1: 16 / A2: 15 / A3: 12 / A4: 16 / A5: 13 → **72 entries**.

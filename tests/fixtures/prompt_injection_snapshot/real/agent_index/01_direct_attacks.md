# Direct Attacks — Hand-Crafted, Encoding, White-Box, Black-Box

<!-- AGENT-INDEX: keep this block stable; future agents read it first. -->
**Scope:** Direct prompt-injection attack research where the attacker controls the model input directly (the user prompt is the attack channel).
**Out of scope:** Indirect / data-borne injection — see `02_indirect_and_agentic_attacks.md`. Defenses against these attacks — see `03_defenses.md`. Training-time backdoors — see `04_training_time_threats.md`.
**Coverage window:** 2022–2026 (emphasis 2024–2026).
**Last updated:** 2026-05-06.
**Subsections (stable anchors):** A1 Foundational direct PI · A2 Hand-crafted jailbreaks · A3 Encoding/obfuscation · A4 White-box optimization · A5 Black-box / LLM-on-LLM optimization.
**Key terms covered:** GCG, ARCA, AutoDAN, COLD-Attack, BEAST, AmpleGCG, I-GCG, AdvPrompter, AutoDAN-Turbo, Soft Prompt Threats, MasterKey, GPTFUZZER, PAIR, TAP, Rainbow Teaming, Adaptive Attacks, H-CoT, J2, Crescendo, Skeleton Key, Many-shot, Best-of-N, PAP, Bad Likert Judge, Adversarial Poetry, CipherChat, ArtPrompt, FlipAttack, Bijection Learning, ASCII Smuggling, HackAPrompt, HouYi, Tensor Trust, BIPIA, JudgeDeceiver, PoisonedRAG, Universal Jailbreak Backdoors.
**Related files:** `00_overview.md` (taxonomy), `02_indirect_and_agentic_attacks.md` (indirect attacks), `03_defenses.md` (countermeasures), `05_datasets_and_benchmarks.md` (eval suites).

## Topic overview

Direct attacks are the threat model where the attacker writes the user-facing prompt. The earliest published work — Perez & Ribeiro's *"Ignore Previous Prompt"* (Nov 2022) — split the surface into two canonical classes: **goal hijacking** (force the model to execute the attacker's goal) and **prompt leaking** (force disclosure of the system prompt). Subsequent research has extended that taxonomy to a five-fold subsection structure that mirrors the dossier and persists in this file.

The five subsections below trace the attack surface in increasing order of automation and adversary capability. **A1** covers foundational systematizations — the early empirical taxonomies and benchmarks. **A2** covers hand-crafted jailbreaks where the attacker authors prompts directly (DAN, Crescendo, PAP). **A3** covers encoding and obfuscation (CipherChat, ArtPrompt, FlipAttack, Bijection Learning). **A4** covers white-box optimization where gradients on the deployed model (or a surrogate) drive a search for adversarial suffixes (GCG, AutoDAN, AmpleGCG). **A5** covers black-box optimization, where an LLM-on-LLM loop generates and refines attacks (PAIR, TAP, Adaptive Attacks, J2).

The 2024–2026 attack-surface trends are clear from the entries below: multi-turn / agentic exploitation has become the dominant vector (Crescendo, Many-shot, Skeleton Key, Bad Likert Judge); reasoning-model attacks emerged as a new class (H-CoT, J2, Adversarial Reasoning at Jailbreaking Time); encoding attacks have bifurcated into "endless" combinatorial families (Bijection Learning, Plentiful Jailbreaks, Adversarial Poetry); and pure DAN-style persona roleplay has plateaued, surviving mostly as a primitive inside hybrid attacks. See § Trends & open questions for the synthesis.

## A1. Foundational Direct Prompt Injection

`#a1-foundational-direct-pi`

These are the systematizations and early empirical works — the papers that named, taxonomized, or benchmarked the direct-PI surface.

### Entries

- **Ignore Previous Prompt** — Perez & Ribeiro (2022), *NeurIPS ML Safety Workshop 2022 (Best Paper)*.
  - **Source:** https://arxiv.org/abs/2211.09527
  - **Code:** https://github.com/agencyenterprise/PromptInject
  - **Mechanism:** First systematic framework for prompt injection on GPT-3; introduces the canonical attack-class split.
  - **Result:** Defines **goal hijacking** vs **prompt leaking** as the two canonical PI attack classes; foundational reference cited by every subsequent direct-PI paper.
  - **Status:** Verified.

- **Evaluating the Susceptibility of Pre-Trained LMs via Handcrafted Adversarial Examples** — Branch et al. (2022), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2209.02128
  - **Code:** —
  - **Mechanism:** Earliest documentation of PI vulnerability in GPT-3; concurrent with Perez & Ribeiro.
  - **Result:** Established that handcrafted inputs reliably override system prompts, before the term "prompt injection" was widely adopted.
  - **Status:** Verified.

- **Goodside "Translate to French / Haha pwned"** — Riley Goodside (Sep 2022), *Twitter / Simon Willison blog*.
  - **Source:** https://simonwillison.net/2022/Sep/12/prompt-injection/
  - **Code:** —
  - **Mechanism:** Viral early demonstration that brought prompt injection to public attention.
  - **Result:** Simon Willison named the attack class "prompt injection"; became the catalyst for naming the field.
  - **Status:** Unverified — Twitter post + Simon Willison blog only; no arXiv equivalent.

- **Not what you've signed up for / Indirect PI** — Greshake et al. (2023), *ACM AISec 2023*.
  - **Source:** https://arxiv.org/abs/2302.12173 ; https://doi.org/10.1145/3605764.3623985
  - **Code:** —
  - **Mechanism:** Foundational **indirect** PI taxonomy: data-borne attacks via web, retrieval, plugins.
  - **Result:** Established remote-code-execution analogy; full LLM compromise via retrieved content.
  - **Status:** Verified. → Primary treatment in `02_indirect_and_agentic_attacks.md` § B1.

- **HouYi: Prompt Injection attack against LLM-integrated Applications** — Liu et al. (2023), *USENIX Security 2024*.
  - **Source:** https://arxiv.org/abs/2306.05499
  - **Code:** https://github.com/LLMSecurity/HouYi
  - **Mechanism:** Black-box PI framework against 36 real LLM-integrated apps.
  - **Result:** 31/36 apps vulnerable; 10 vendors confirmed (Notion etc.).
  - **Status:** Verified. → Also referenced in `02_indirect_and_agentic_attacks.md` § B1.

- **Jailbreaking ChatGPT via Prompt Engineering: An Empirical Study** — Liu et al. (2023), *TOSEM (extended)*.
  - **Source:** https://arxiv.org/abs/2305.13860
  - **Code:** —
  - **Mechanism:** Classification of 10 patterns / 3 categories of jailbreak prompts.
  - **Result:** Empirical taxonomy of 78 distinct prompts across 8 prohibited scenarios.
  - **Status:** Verified.

- **Tensor Trust: Interpretable Prompt Injection Attacks from an Online Game** — Toyer et al. (2023), *ICLR 2024*.
  - **Source:** https://arxiv.org/abs/2311.01011
  - **Code:** —
  - **Mechanism:** Online game produces 126K+ human-generated PI attacks plus 46K defenses.
  - **Result:** Largest human-generated adversarial dataset; formalizes **prompt extraction** vs **prompt hijacking**.
  - **Status:** Verified.

- **Ignore This Title and HackAPrompt** — Schulhoff et al. (2023), *EMNLP 2023 (Best Theme Paper)*.
  - **Source:** https://arxiv.org/abs/2311.16119
  - **Code:** https://github.com/PromptLabs/hackaprompt
  - **Mechanism:** Global-scale prompt-hacking competition; 600K+ adversarial prompts and 29-technique taxonomy.
  - **Result:** Discovered "Context Overflow" attack; key takeaway: prompt-based defenses don't work.
  - **Status:** Verified.

- **Formalizing and Benchmarking Prompt Injection Attacks and Defenses** — Liu et al. (2023), *USENIX Security 2024*.
  - **Source:** https://arxiv.org/abs/2310.12815
  - **Code:** https://github.com/liu00222/Open-Prompt-Injection
  - **Mechanism:** First formal framework; 5 attacks × 10 defenses × 10 LLMs × 7 tasks.
  - **Result:** Common benchmark + taxonomy of separator/escape/fake-completion/combined attacks.
  - **Status:** Verified. → Also see `02_indirect_and_agentic_attacks.md` § B1, `03_defenses.md` § C3.

- **BIPIA: Benchmarking and Defending Against Indirect Prompt Injection** — Yi et al. (Microsoft 2023), *KDD 2025*.
  - **Source:** https://arxiv.org/abs/2312.14197
  - **Code:** https://github.com/microsoft/BIPIA
  - **Mechanism:** First broad indirect-PI benchmark; 5 scenarios × 250 attacker goals.
  - **Result:** Identifies two root causes; bilingual coverage (en/zh).
  - **Status:** Verified. → Also see `02_indirect_and_agentic_attacks.md` § B1, `03_defenses.md` § C3.

- **Automatic and Universal Prompt Injection Attacks against LLMs** — Liu et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2403.04957
  - **Code:** https://github.com/SheltonLiu-N/Universal-Prompt-Injection
  - **Mechanism:** First gradient-based universal PI; introduces M-GCG.
  - **Result:** Bridges PI-attacks with the GCG family.
  - **Status:** Verified.

- **Neural Exec: Learning Execution Triggers for Prompt Injection** — Pasquini et al. (2024), *ACM AISec 2024*.
  - **Source:** https://arxiv.org/abs/2403.03792
  - **Code:** https://github.com/pasquini-dario/LLM_NeuralExec
  - **Mechanism:** Differentiable search for novel-shape PI triggers.
  - **Result:** Triggers persist through multi-stage RAG pipelines.
  - **Status:** Verified. → Primary treatment in `02_indirect_and_agentic_attacks.md` § B1 (indirect/RAG-focused).

- **JudgeDeceiver: Optimization-based PI on LLM-as-a-Judge** — Shi et al. (2024), *ACM CCS 2024*.
  - **Source:** https://arxiv.org/abs/2403.17710
  - **Code:** https://github.com/ShiJiawenwen/JudgeDeceiver
  - **Mechanism:** Gradient-based PI against LLM-as-judge selection.
  - **Result:** 97.6% ASR on MT-Bench; bypasses known-answer and perplexity detection.
  - **Status:** Verified.

- **PoisonedRAG: Knowledge Corruption Attacks to RAG** — Zou et al. (2024), *USENIX Security 2025*.
  - **Source:** https://arxiv.org/abs/2402.07867
  - **Code:** https://github.com/sleeepeer/PoisonedRAG
  - **Mechanism:** Inject 5 poisoned texts into a 10⁶-document database to control answers.
  - **Result:** 90%+ ASR across NQ, HotpotQA, and MS-MARCO retrieval benchmarks (per-dataset breakdown in the paper body).
  - **Status:** Verified. → Primary treatment in `02_indirect_and_agentic_attacks.md` § B1; cross-ref `04_training_time_threats.md` § D2.

- **PoisonedAlign: Enhancing PI Attacks via Poisoning Alignment** — Shao et al. (2024), *ACM AISec 2025*.
  - **Source:** https://arxiv.org/abs/2410.14827
  - **Code:** https://github.com/Sadcardation/PoisonedAlign
  - **Mechanism:** Poison alignment-data to make models more PI-vulnerable.
  - **Result:** 10% poisoned ORCA-DPO → +0.33 ASR.
  - **Status:** Verified.

- **An Early Categorization of Prompt Injection Attacks on LLMs** — Rossi et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2402.00898
  - **Code:** —
  - **Mechanism:** Vulnerability checklist for LLM-interface developers.
  - **Result:** Direct vs indirect taxonomy formalized for practitioners.
  - **Status:** Verified.

## A2. Hand-Crafted Jailbreaks

`#a2-hand-crafted-jailbreaks`

These attacks rely on human-authored prompts — persona roleplay, multi-turn escalation, persuasive framing — without algorithmic optimization. Hand-crafted jailbreaks remain practically important even after optimization-based attacks dominate the leaderboards: they reveal alignment weaknesses, transfer reliably across model versions, and evade many statistical detectors.

### Entries

- **DAN ("Do Anything Now") evolution** — Reddit / community (Dec 2022 – 2024), *community*.
  - **Source:** https://github.com/0xk1h0/ChatGPT_DAN
  - **Code:** https://github.com/0xk1h0/ChatGPT_DAN
  - **Mechanism:** Persona-roleplay jailbreaks instructing the model to simulate an unrestricted alter-ego.
  - **Result:** DAN 5.0 introduced 35-token "life counter"; 12-version arms race; academic catalog at Shen et al. 2023.
  - **Status:** Unverified — Reddit/community origin; no arXiv equivalent.

- **Multi-step Jailbreaking Privacy Attacks on ChatGPT** — Li et al. (2023), *EMNLP Findings 2023*.
  - **Source:** https://arxiv.org/abs/2304.05197
  - **Code:** —
  - **Mechanism:** Multi-stage PII extraction via roleplay scaffolding.
  - **Result:** Foundational for chained attacks; PII recovery from production ChatGPT.
  - **Status:** Verified.

- **Jailbroken: How Does LLM Safety Training Fail?** — Wei, Haghtalab, Steinhardt (2023), *NeurIPS 2023*.
  - **Source:** https://arxiv.org/abs/2307.02483
  - **Code:** —
  - **Mechanism:** Two failure modes — competing objectives + mismatched generalization.
  - **Result:** Theoretical scaffold the field still uses to explain jailbreak success.
  - **Status:** Verified.

- **"Do Anything Now": Characterizing In-The-Wild Jailbreak Prompts** — Shen et al. (2023), *ACM CCS 2024*.
  - **Source:** https://arxiv.org/abs/2308.03825
  - **Code:** https://github.com/verazuo/jailbreak_llms
  - **Mechanism:** Empirical analysis of 1,405 in-the-wild jailbreaks (Dec 2022 – Dec 2023).
  - **Result:** 131 jailbreak communities; 5 prompts achieve 0.95 ASR.
  - **Status:** Verified.

- **DeepInception: Hypnotize LLM to Be Jailbreaker** — Li et al. (2023), *COLM 2024*.
  - **Source:** https://arxiv.org/abs/2311.03191
  - **Code:** https://github.com/tmlr-group/DeepInception
  - **Mechanism:** Nested fictional scenes that recursively unlock harmful content.
  - **Result:** Inspired by Milgram experiment; layered authority figures bypass refusal.
  - **Status:** Verified.

- **ReNeLLM: Generalized Nested Jailbreak Prompts** — Ding et al. (2024), *NAACL 2024*.
  - **Source:** https://arxiv.org/abs/2311.08268
  - **Code:** https://github.com/NJUNLP/ReNeLLM
  - **Mechanism:** Two-stage rewriting + scenario nesting.
  - **Result:** 76.61% time reduction vs GCG.
  - **Status:** Verified.

- **Multilingual Jailbreak Challenges in LLMs** — Deng et al. (2023), *ICLR 2024*.
  - **Source:** https://arxiv.org/abs/2310.06474
  - **Code:** https://github.com/DAMO-NLP-SG/multilingual-safety-for-LLMs
  - **Mechanism:** Cross-lingual jailbreaks via translation to non-English languages.
  - **Result:** ChatGPT 80.92%, GPT-4 40.71% unsafe; introduces Self-Defense framework.
  - **Status:** Verified.

- **Crescendo Multi-Turn LLM Jailbreak** — Russinovich et al. (Microsoft 2024), *USENIX Security 2025*.
  - **Source:** https://arxiv.org/abs/2404.01833
  - **Code:** https://github.com/microsoft/PyRIT (implementation in PyRIT)
  - **Mechanism:** Gradual benign-to-harmful escalation across <5 turns.
  - **Result:** Microsoft disclosure; exploits self-output pattern-following.
  - **Status:** Verified.

- **Skeleton Key — Microsoft disclosure** — Russinovich (Microsoft, June 2024), *Microsoft Security Blog*.
  - **Source:** https://www.microsoft.com/en-us/security/blog/2024/06/26/mitigating-skeleton-key-a-new-type-of-generative-ai-jailbreak-technique/
  - **Code:** —
  - **Mechanism:** Multi-turn behavior-modification jailbreak; persuades model to amend rather than refuse.
  - **Result:** Worked on Llama3-70b, Gemini Pro, GPT-3.5/4o, Mistral, Claude 3 Opus.
  - **Status:** Unverified — vendor blog, no arXiv ID.

- **Many-shot Jailbreaking** — Anil et al. (Anthropic 2024), *NeurIPS 2024*.
  - **Source:** https://www.anthropic.com/research/many-shot-jailbreaking
  - **Code:** —
  - **Mechanism:** Hundreds of faux Q/A demos in a single prompt → safety bypass.
  - **Result:** Power-law scaling with shots; enabled by 1M-token contexts.
  - **Status:** Unverified — Anthropic technical report; no arXiv ID confirmed.

- **Best-of-N Jailbreaking** — Hughes et al. (Anthropic 2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2412.03556
  - **Code:** —
  - **Mechanism:** Random prompt augmentations until a harmful response slips through.
  - **Result:** 89% on GPT-4o, 78% on Claude 3.5 Sonnet at N=10K.
  - **Status:** Verified.

- **Persuasive Adversarial Prompts (PAP)** — Zeng et al. (2024), *ACL 2024*.
  - **Source:** https://arxiv.org/abs/2401.06373
  - **Code:** https://github.com/CHATS-lab/persuasive_jailbreaker
  - **Mechanism:** Taxonomy of 40 persuasion techniques (humanizing the LLM).
  - **Result:** 92% ASR on Llama-2-7b / GPT-3.5 / GPT-4 with no optimization.
  - **Status:** Verified.

- **Bad Likert Judge** — Palo Alto Unit 42 (Dec 2024), *Vendor blog*.
  - **Source:** https://unit42.paloaltonetworks.com/multi-turn-technique-jailbreaks-llms/
  - **Code:** —
  - **Mechanism:** LLM acts as Likert-scale "judge"; the high-Likert example contains harmful content.
  - **Result:** +60% ASR vs single-turn baseline.
  - **Status:** Unverified — vendor blog, no arXiv version.

- **Jailbreak Attacks and Defenses Against LLMs: A Survey** — Yi et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2407.04295
  - **Code:** —
  - **Mechanism:** Comprehensive jailbreak taxonomy: black-box vs white-box × prompt-level vs model-level.
  - **Result:** Field-defining matrix that downstream papers use as a frame.
  - **Status:** Verified.

- **Adversarial Poetry as a Universal Single-Turn Jailbreak** — Bisconti, Prandi, Pierucci et al. (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2511.15304
  - **Code:** —
  - **Mechanism:** Convert harmful prompts to verse → 18× ASR vs prose.
  - **Result:** 62% avg ASR (handcrafted); >90% on some providers.
  - **Status:** Verified — authors corrected 2026-05-06 per arXiv primary source (earlier draft had wrong attribution).

## A3. Encoding and Obfuscation Attacks

`#a3-encoding-obfuscation`

These attacks transform the harmful query into an alternative encoding — natural-language ciphers, ASCII art, low-resource languages, in-context-learned bijections. The defining 2024–2026 trend is bifurcation into "endless" combinatorial families (Bijection Learning, Plentiful Jailbreaks): rather than fixed ciphers, attackers teach the model an arbitrary string-string map in-context, producing infinitely many one-off encodings that defeat signature-based detectors.

### Entries

- **Low-Resource Languages Jailbreak GPT-4** — Yong et al. (2023), *ICLR Workshop SeT-LLM 2024*.
  - **Source:** https://arxiv.org/abs/2310.02446
  - **Code:** —
  - **Mechanism:** Translate harmful prompts to Zulu / Scots-Gaelic.
  - **Result:** 79% ASR on AdvBench via low-resource translation.
  - **Status:** Verified.

- **GPT-4 Is Too Smart To Be Safe via Cipher (CipherChat)** — Yuan et al. (2023), *ICLR 2024*.
  - **Source:** https://arxiv.org/abs/2308.06463
  - **Code:** https://github.com/RobustNLP/CipherChat
  - **Mechanism:** Caesar / ASCII / Morse / Unicode ciphers with few-shot demos.
  - **Result:** SelfCipher (natural-language only) outperforms; 70.9% unsafe on GPT-4 English.
  - **Status:** Verified.

- **ArtPrompt: ASCII Art-based Jailbreak Attacks** — Jiang et al. (2024), *ACL 2024*.
  - **Source:** https://arxiv.org/abs/2402.11753
  - **Code:** https://github.com/uw-nsl/ArtPrompt
  - **Mechanism:** Mask safety-trigger words and replace with ASCII art.
  - **Result:** First **vision-in-text** jailbreak; introduces ViTC benchmark.
  - **Status:** Verified.

- **CodeChameleon: Personalized Encryption Framework** — Lv et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2402.16717
  - **Code:** https://github.com/huizhang-L/CodeChameleon
  - **Mechanism:** Reformulate harmful query as code completion + embed a decrypt function.
  - **Result:** 86.6% ASR on GPT-4-1106.
  - **Status:** Verified.

- **WordGame: Simultaneous Obfuscation in Query and Response** — Zhang et al. (2024), *NAACL Findings 2025*.
  - **Source:** https://arxiv.org/abs/2405.14023
  - **Code:** —
  - **Mechanism:** Replace harmful words with word puzzles in BOTH query and response.
  - **Result:** >92% ASR on Llama-2-7b, GPT-3.5/4.
  - **Status:** Verified.

- **Endless Jailbreaks with Bijection Learning** — Huang et al. (Haize Labs 2024), *ICLR 2025*.
  - **Source:** https://arxiv.org/abs/2410.01294
  - **Code:** https://github.com/haizelabs/bijection-learning
  - **Mechanism:** Teach an arbitrary string-string bijection in-context, then issue the harmful request encoded.
  - **Result:** High ASR on frontier models; larger models *more* vulnerable to this attack class (per-model breakdown in paper body).
  - **Status:** Verified.

- **FlipAttack: Jailbreak via Flipping** — Liu et al. (2024), *ICML 2025*.
  - **Source:** https://arxiv.org/abs/2410.02832
  - **Code:** https://github.com/yueliu1999/FlipAttack
  - **Mechanism:** Four left-side text-flipping modes.
  - **Result:** ~98% ASR on GPT-4o; ~98% bypass on 5 guardrails.
  - **Status:** Verified.

- **Plentiful Jailbreaks with String Compositions** — Huang & Tang (Haize Labs 2024), *NeurIPS Workshop SoLaR*.
  - **Source:** https://arxiv.org/abs/2411.01084
  - **Code:** —
  - **Mechanism:** 20 invertible string-transformation primitives, composed.
  - **Result:** Generalizes leetspeak / Base64 / ROT13 into a composable framework.
  - **Status:** Verified.

- **StructuralSleight (UTOS): Uncommon Text-Organization Structures** — Li, Xiao et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2406.08754
  - **Code:** —
  - **Mechanism:** Three-strategy escalation over 12 uncommon text-organization-structure (UTOS) templates and 6 obfuscation methods.
  - **Result:** 94.62% ASR on GPT-4o.
  - **Status:** Verified — mechanism corrected 2026-05-06 to match the actual UTOS template/obfuscation construction.

- **ASCII Smuggling via Unicode Tag Block (E0000-E007F)** — Goodside / Thacker / Rehberger (2024), *Industry blog disclosures*.
  - **Source:** https://embracethered.com/blog/posts/2024/hiding-and-finding-text-with-unicode-tags/
  - **Code:** —
  - **Mechanism:** Use the deprecated Unicode Tag block (invisible to humans, read by LLMs).
  - **Result:** Hidden in PDFs / images / databases; bypasses human-in-the-loop review.
  - **Status:** Unverified — industry blog series, no arXiv.

- **StegoAttack ("Hiding in Plain Sight"): Steganographic LLM Jailbreaks** — Geng, Yi, Fei, He, Nie, Li, Liu (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2505.16765
  - **Code:** —
  - **Mechanism:** Embed harmful query within a benign paragraph via first-letter steganography.
  - **Result:** 95.5% ASR; ASR drop <27% even under detectors.
  - **Status:** Verified — authors filled in 2026-05-06.

- **Jailbreaking LLMs via Cipher Characters** — anonymous (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2405.20413
  - **Code:** —
  - **Mechanism:** Cipher-character substitutions to evade moderation.
  - **Result:** Targets the moderator, not the policy model.
  - **Status:** Verified — author list not surfaced in dossier.

## A4. White-Box Optimization Attacks

`#a4-white-box-optimization`

These attacks assume the attacker has gradients on the deployed model (or a near-equivalent surrogate). The foundational landmark is GCG (Zou et al. 2023), which combined greedy coordinate gradient with token swap to find adversarial suffixes. Subsequent work has accelerated the search (Probe Sampling), made the suffix fluent (AdvPrompter, COLD-Attack), and amortized the optimization cost across queries (AmpleGCG, AutoDAN-Turbo).

### Entries

- **GCG (Greedy Coordinate Gradient): Universal and Transferable Adversarial Attacks** — Zou et al. (2023), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2307.15043
  - **Code:** https://github.com/llm-attacks/llm-attacks
  - **Mechanism:** Gradient-guided greedy token search; appends an adversarial suffix to a harmful query.
  - **Result:** Foundational white-box jailbreak; suffixes transfer across ChatGPT, Claude, Bard, Llama-2.
  - **Status:** Verified.

- **ARCA: Auditing LLMs via Discrete Optimization** — Jones et al. (2023), *ICML 2023*.
  - **Source:** https://arxiv.org/abs/2303.04381
  - **Code:** —
  - **Mechanism:** Joint discrete optimization over input AND output.
  - **Result:** Pre-GCG discrete optimization framework that established the technique class.
  - **Status:** Verified.

- **AutoDAN: Stealthy Jailbreak Prompts via Genetic Algorithm** — Liu et al. (2023), *ICLR 2024*.
  - **Source:** https://arxiv.org/abs/2310.04451
  - **Code:** https://github.com/SheltonLiu-N/AutoDAN
  - **Mechanism:** Hierarchical genetic algorithm over DAN-style prompts.
  - **Result:** Stealthy and semantically meaningful; bypasses perplexity defenses.
  - **Status:** Verified.

- **COLD-Attack: Stealthy + Controllable Jailbreaks** — Yu et al. (2024), *ICML 2024*.
  - **Source:** https://arxiv.org/abs/2402.08679
  - **Code:** https://github.com/Yu-Fangxu/COLD-Attack
  - **Mechanism:** Energy-based Constrained Decoding with Langevin Dynamics.
  - **Result:** Unifies fluency / sentiment / coherence constraints into one objective.
  - **Status:** Verified.

- **BEAST: Fast Adversarial Attacks in One GPU Minute** — Sadasivan et al. (2024), *ICML 2024*.
  - **Source:** https://arxiv.org/abs/2402.15570
  - **Code:** https://github.com/vinusankars/BEAST
  - **Mechanism:** Beam-search-based gradient-free attack.
  - **Result:** 89% ASR on Vicuna-7B in <1 minute (vs >1 hour for GCG).
  - **Status:** Verified.

- **AmpleGCG: Universal Generative Model of Adversarial Suffixes** — Liao & Sun (2024), *COLM 2024*.
  - **Source:** https://arxiv.org/abs/2404.07921
  - **Code:** https://github.com/OSU-NLP-Group/AmpleGCG
  - **Mechanism:** Train a generative model on intermediate GCG successes.
  - **Result:** 200 suffixes in 4 sec/query; 99% ASR on GPT-3.5.
  - **Status:** Verified.

- **AmpleGCG-Plus** — Kumar, Liao et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2410.22143
  - **Code:** https://github.com/OSU-NLP-Group/AmpleGCG
  - **Mechanism:** Improved AmpleGCG (more diverse training data, refined generator).
  - **Result:** Higher ASR with fewer attempts than original AmpleGCG.
  - **Status:** Verified.

- **I-GCG: Improved Optimization-Based Jailbreaking** — Jia et al. (2024), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2405.21018
  - **Code:** —
  - **Mechanism:** Multi-coordinate updates + diverse target templates.
  - **Result:** ~100% ASR; outperforms vanilla GCG.
  - **Status:** Verified.

- **Probe Sampling: Accelerating GCG** — Zhao et al. (2024), *NeurIPS 2024*.
  - **Source:** https://arxiv.org/abs/2403.01251
  - **Code:** https://github.com/zhaoyiran924/Probe-Sampling
  - **Mechanism:** Use a small draft model to filter candidates before evaluating on the target.
  - **Result:** 5.6× speedup on Llama-2-7b-chat.
  - **Status:** Verified.

- **AutoDAN-Turbo: Lifelong Strategy Self-Exploration** — Liu et al. (2024), *ICLR 2025 Spotlight*.
  - **Source:** https://arxiv.org/abs/2410.05295
  - **Code:** https://github.com/SaFoLab-WISC/AutoDAN-Turbo
  - **Mechanism:** Strategy library accumulates discovered attack tactics across runs.
  - **Result:** 88.5% on GPT-4-1106-turbo.
  - **Status:** Verified.

- **AdvPrompter: Fast Adaptive Adversarial Prompting** — Paulus et al. (2024), *ICLR 2025*.
  - **Source:** https://arxiv.org/abs/2404.16873
  - **Code:** https://github.com/facebookresearch/advprompter
  - **Mechanism:** Train an auxiliary LLM to generate human-readable adversarial suffixes.
  - **Result:** ~800× faster than GCG with comparable ASR.
  - **Status:** Verified.

- **Soft Prompt Threats: Embedding-Space Attacks** — Schwinn et al. (2024), *NeurIPS 2024*.
  - **Source:** https://arxiv.org/abs/2402.09063
  - **Code:** https://github.com/SchwinnL/LLM_Embedding_Attack
  - **Mechanism:** Continuous-embedding gradient descent with no token discretization.
  - **Result:** Stronger per-target attack at the cost of requiring embedding access.
  - **Status:** Unverified arXiv ID — repo and citations confirm a NeurIPS 2024 paper, but the canonical ID should be re-verified.

- **DrAttack: Decomposition + Reconstruction** — Li et al. (2024), *EMNLP Findings 2024*.
  - **Source:** https://arxiv.org/abs/2402.16914
  - **Code:** https://github.com/xirui-li/DrAttack
  - **Mechanism:** Decompose query → reconstruct via in-context demos → synonym search.
  - **Result:** 78% ASR on GPT-4 in 15 queries.
  - **Status:** Verified.

- **PRP: Universal Perturbations to Attack Guard-Rails** — Mangaokar et al. (2024), *ACL 2024*.
  - **Source:** https://arxiv.org/abs/2402.15911
  - **Code:** —
  - **Mechanism:** Two-stage — universal prefix for the guard model, then propagate to the response.
  - **Result:** High ASR against guard-rail-protected models in the paper's evaluation (specific figures in paper body).
  - **Status:** Verified.

- **I-FSJ: Improved Few-Shot Jailbreaking** — Zheng et al. (2024), *NeurIPS 2024*.
  - **Source:** https://arxiv.org/abs/2406.01288
  - **Code:** https://github.com/sail-sg/I-FSJ
  - **Mechanism:** Special-token injection plus demo-level random search.
  - **Result:** >80–95% ASR on Llama-2-7B / Llama-3-8B.
  - **Status:** Verified.

- **Universal Jailbreak Backdoors from Poisoned Human Feedback** — Rando & Tramèr (2023), *ICLR 2024*.
  - **Source:** https://arxiv.org/abs/2311.14455
  - **Code:** https://github.com/ethz-spylab/rlhf-poisoning
  - **Mechanism:** Poison RLHF preference data → universal trigger word.
  - **Result:** First universal backdoor in RLHF.
  - **Status:** Verified. → Primary treatment in `04_training_time_threats.md` § D1.

## A5. Black-Box Optimization / LLM-on-LLM Attacks

`#a5-black-box-optimization`

These attacks assume the attacker can call the model and read outputs but does not have gradients. PAIR (Chao et al. 2023) is the canonical framework: an attacker LLM iteratively refines its prompt against a target LLM until refusal becomes compliance. TAP extends PAIR with tree-search; Adaptive Attacks adds logprob-guided random search; J2 weaponizes a jailbroken model to attack others. The 2025 reasoning-model attacks (H-CoT, Adversarial Reasoning at Jailbreaking Time) target the visible chain-of-thought of o1/o3/R1.

### Entries

- **MasterKey: Automated Jailbreak Across Multiple Chatbots** — Deng et al. (2023), *NDSS 2024*.
  - **Source:** https://arxiv.org/abs/2307.08715
  - **Code:** https://github.com/LLMSecurity/MasterKey
  - **Mechanism:** Time-based defense reverse-engineering plus a fine-tuned attacker model.
  - **Result:** ~21.6% ASR on commercial chatbots; outperforms the no-attacker-model baseline (per-baseline figures in paper body).
  - **Status:** Verified.

- **GPTFUZZER: Auto-Generated Jailbreak Prompts** — Yu et al. (2023), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2309.10253
  - **Code:** https://github.com/sherdencooper/GPTFuzz
  - **Mechanism:** AFL-style fuzzing with mutate operators on seed templates.
  - **Result:** >90% ASR on ChatGPT / Llama-2.
  - **Status:** Verified.

- **FuzzLLM: Universal Fuzzing Framework** — Yao et al. (2023), *ICASSP 2024*.
  - **Source:** https://arxiv.org/abs/2309.05274
  - **Code:** https://github.com/RainJamesY/FuzzLLM
  - **Mechanism:** Three base classes (Role Play, Output Constrain, Privilege Escalation), composed.
  - **Result:** Black-box, combo-attack composition.
  - **Status:** Verified.

- **PAIR: Black-Box LLMs in Twenty Queries** — Chao et al. (2023), *NeurIPS 2023 R0-FoMo Workshop*.
  - **Source:** https://arxiv.org/abs/2310.08419
  - **Code:** https://github.com/patrickrchao/JailbreakingLLMs
  - **Mechanism:** Attacker LLM iteratively refines its prompt against a target LLM.
  - **Result:** <20 queries; produces semantic jailbreaks.
  - **Status:** Verified.

- **TAP: Tree of Attacks** — Mehrotra et al. (2023), *NeurIPS 2024*.
  - **Source:** https://arxiv.org/abs/2312.02119
  - **Code:** https://github.com/RICommunity/TAP
  - **Mechanism:** Tree-of-thought search plus pruning over PAIR-style attacker iterations.
  - **Result:** >80% ASR on GPT-4-Turbo / 4o; 60% fewer queries than PAIR.
  - **Status:** Verified.

- **Rainbow Teaming: Quality-Diversity Adversarial Generation** — Samvelyan et al. (2024), *NeurIPS 2024*.
  - **Source:** https://arxiv.org/abs/2402.16822
  - **Code:** —
  - **Mechanism:** MAP-Elites quality-diversity search over an adversarial-prompt archive.
  - **Result:** Hundreds of diverse jailbreaks with >90% ASR.
  - **Status:** Verified.

- **Adaptive Attacks on Safety-Aligned LLMs** — Andriushchenko, Croce, Flammarion (2024), *ICLR 2025*.
  - **Source:** https://arxiv.org/abs/2404.02151
  - **Code:** https://github.com/tml-epfl/llm-adaptive-attacks
  - **Mechanism:** Logprob-guided random search on a suffix targeting "Sure".
  - **Result:** 100% ASR on Vicuna / Mistral / Phi-3 / Llama-2/3 / Gemma / GPT-3.5/4o.
  - **Status:** Verified. → Primary methodology treatment in `03_defenses.md` § C6.

- **H-CoT: Hijacking Chain-of-Thought Safety Reasoning** — Kuo et al. (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2502.12893
  - **Code:** https://github.com/dukeceicenter/jailbreak-reasoning-openai-o1o3-deepseek-r1
  - **Mechanism:** Use the displayed chain-of-thought of o1 / o3 / R1 against itself.
  - **Result:** Refusal 98% → <2% on the targeted reasoning models.
  - **Status:** Verified.

- **Adversarial Reasoning at Jailbreaking Time** — Sabbaghi et al. (2025), *ICML 2025*.
  - **Source:** https://arxiv.org/abs/2502.01633
  - **Code:** —
  - **Mechanism:** Test-time-compute search using a continuous loss signal.
  - **Result:** State-of-the-art ASR on tested reasoning models (per-model breakdown in paper body).
  - **Status:** Verified.

- **J2 (Jailbreaking to Jailbreak)** — Scale AI Labs (Kritz, Robinson, Vacareanu 2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2502.09638
  - **Code:** —
  - **Mechanism:** Once jailbroken, refusal-trained LLMs become attackers.
  - **Result:** J2(Sonnet-3.7) → 0.975 ASR vs GPT-4o.
  - **Status:** Verified.

- **Siege / Tempest: Autonomous Multi-Turn Jailbreaking** — Zhou & Arel (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2503.10619
  - **Code:** —
  - **Mechanism:** BFS-style multi-turn tree search.
  - **Result:** Multi-turn extension of TAP.
  - **Status:** Verified — paper renamed from "Siege" to "Tempest" in v3 (2025); authors are Andy Zhou and Ron Arel.

- **Persona Prompts: GA-evolved Persona Jailbreaks** — Zhang, Zhao, Ye, Wang (2025), *arXiv preprint*.
  - **Source:** https://arxiv.org/abs/2507.22171
  - **Code:** —
  - **Mechanism:** Genetic-algorithm-evolved persona prompts.
  - **Result:** −50–70% refusal; +10–20% synergy with existing attacks.
  - **Status:** Verified — authors filled in 2026-05-06.

- **Speak Easy: Multi-step + Multilingual Interaction** — Chan, Ri, Xiao, Ghassemi (2025), *ICML 2025*.
  - **Source:** https://arxiv.org/abs/2502.04322
  - **Code:** —
  - **Mechanism:** Simple multi-step plus multilingual framework with HarmScore metric.
  - **Result:** New metric: actionability + informativeness.
  - **Status:** Verified — authors filled in 2026-05-06.

## Trends & open questions

The 2024–2026 attack-surface trends fall into three patterns:

**Aggressively growing vectors.** Multi-turn / agentic exploitation has become the dominant 2024–2026 vector: Crescendo (Microsoft 2024), Skeleton Key (Microsoft 2024), Bad Likert Judge (Unit 42 2024), Siege (2025), and AgentDojo (NeurIPS 2024) collectively pivoted the field from single-turn injection to *conversation-graph* attacks where each turn is benign but the trajectory is harmful. Tool-using agents (InjecAgent, AgentDojo, MCP tool-poisoning) introduced a new attack surface in 2024–2026: the model now has *capabilities*, not just outputs (see `02_indirect_and_agentic_attacks.md` § B2). Reasoning-model attacks emerged as a sub-class in 2025: with o1 / o3, R1, and Gemini-Flash-Thinking exposing chain-of-thought, H-CoT (2025), Adversarial Reasoning at Jailbreaking Time (2025), and J2 (2025) weaponize the reasoning trace itself.

**Bifurcated encoding/obfuscation.** Bijection Learning (2024), Plentiful Jailbreaks (2024), FlipAttack (2024), and Adversarial Poetry (2025) replace fixed-cipher attacks with *combinatorial families* of encodings teachable in-context, defeating signature-based detectors.

**Plateaued / replaced vectors.** Pure DAN-style persona roleplay has been largely neutralized in production by OpenAI / Anthropic patches plus aligned RLHF; persona attacks survive only as a *primitive* inside hybrid attacks. Vanilla GCG without acceleration (Probe Sampling), generative amplification (AmpleGCG), or improved coordinates (I-GCG) is now baseline; non-readable suffixes are caught by perplexity filters, and AdvPrompter / COLD-Attack / AutoDAN moved the field toward fluent suffixes.

**Emerging vectors to watch in 2026:** indirect PI through MCP and tool descriptions (tool-poisoning at the MCP-server-description level lets an attacker compromise *every* downstream agent that connects to the server); steganographic multimodal channels (StegoAttack 2025 hides payloads in cover paragraphs; ASCII-smuggling via Unicode tag block remains under-mitigated at most API gateways).

## Verification notes

Entries flagged unverified or vendor-blog-only:

- **Goodside "Translate to French"** — Twitter post + Simon Willison blog only; no arXiv equivalent.
- **DAN ("Do Anything Now") prompt evolution** — Reddit / community origin; the academic catalog at Shen et al. (arXiv:2308.03825) covers the wild prompts.
- **Skeleton Key** — Microsoft Security Blog disclosure (June 2024); no arXiv ID.
- **Bad Likert Judge** — Palo Alto Unit 42 vendor blog (Dec 2024); no arXiv version.
- **ASCII Smuggling via Unicode Tag Block** — Goodside / Thacker / Rehberger blog series plus AWS/Cisco/Promptfoo defense write-ups; industry-disclosed only.
- **Many-shot Jailbreaking (Anil et al.)** — Anthropic-hosted technical PDF + NeurIPS 2024 proceedings entry; no corresponding arXiv ID. The often-cited "arXiv:2404.02151" actually maps to Andriushchenko et al.'s adaptive-attacks paper (separate work in § A5).
- **Soft Prompt Threats (Schwinn et al. 2024)** — GitHub repo and citations confirm a NeurIPS 2024 paper; arXiv:2402.09063 is best-estimate but should be re-verified.
- **Several 2025 entries (Siege, Persona Prompts, Speak Easy, StegoAttack, Cipher Characters)** — arXiv-format-valid IDs; specific authors not surfaced in this session.

Post-2025 entries (Adversarial Poetry, H-CoT, J2, Adversarial Reasoning at Jailbreaking Time) carry highest re-verification priority — the field moves quarterly and venue assignments may evolve.

**Total entries in this file:** A1: 16 / A2: 15 / A3: 12 / A4: 16 / A5: 13 → **72 entries**.

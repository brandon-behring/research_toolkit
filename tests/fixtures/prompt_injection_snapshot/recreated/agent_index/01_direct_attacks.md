# 01 — Direct attacks (jailbreaks, encoding, white-box, black-box)

**Scope:** primary sources on direct prompt injection and jailbreak techniques: hand-crafted PI taxonomies, encoding/obfuscation, white-box gradient-based attacks, black-box query-driven attacks, multi-turn and reasoning-model variants.
**Out of scope:** indirect-PI / agentic attacks (see `02_indirect_and_agentic_attacks.md`); training-time backdoors/poisoning (see `04_training_time_threats.md`).

## A1. Hand-crafted PI taxonomies and persuasion-style jailbreaks

- **Ignore Previous Prompt** — Perez & Ribeiro (arXiv 2022).
  - **Source:** https://arxiv.org/abs/2211.09527
  - **Code:** —
  - **Mechanism:** Hand-crafted "ignore previous instructions" attack patterns against instruction-following LLMs.
  - **Result:** Foundational taxonomy of direct prompt-injection attacks; canonical reference for the term.
  - **Status:** Verified

- **Do Anything Now (DAN)** — Shen et al. (arXiv 2023).
  - **Source:** https://arxiv.org/abs/2308.03825
  - **Code:** —
  - **Mechanism:** Empirical collection and characterization of in-the-wild jailbreak prompts (e.g., DAN family) from public forums.
  - **Result:** Large-scale measurement of organically-discovered jailbreaks; widely cited as the in-the-wild baseline.
  - **Status:** Unverified

- **Jailbroken: How Does LLM Safety Training Fail?** — Wei et al. (arXiv 2023).
  - **Source:** https://arxiv.org/abs/2307.02483
  - **Code:** —
  - **Mechanism:** Failure-mode analysis identifying competing-objective and mismatched-generalization as canonical safety-training failures.
  - **Result:** Provides taxonomy of why aligned models break under specific prompt structures.
  - **Status:** Unverified

- **Persuasion (PAP)** — Zeng et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2401.06373
  - **Code:** —
  - **Mechanism:** Persuasion-taxonomy-driven jailbreak generator using human-derived rhetorical strategies.
  - **Result:** Adapts human persuasion taxonomies into a structured jailbreak generation pipeline.
  - **Status:** Unverified

- **Crescendo** — Russinovich et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2404.01833
  - **Code:** —
  - **Mechanism:** Multi-turn jailbreak escalating a benign topic toward harmful content over progressive turns.
  - **Result:** Demonstrates that single-turn safety filters miss progressive multi-turn manipulation.
  - **Status:** Verified

- **Many-shot Jailbreaking** — Anil et al. (Anthropic 2024).
  - **Source:** https://www.anthropic.com/research/many-shot-jailbreaking
  - **Code:** —
  - **Mechanism:** In-context jailbreak using hundreds of fake-assistant turns to override safety training.
  - **Result:** Shows long-context windows enable a new in-context attack vector.
  - **Status:** (vendor blog)

- **Many-shot Jailbreaking (PDF)** — Anil et al. (Anthropic 2024) (unverified, 2026-05-07).
  - **Source:** https://www-cdn.anthropic.com/af5633c94ed2beb282f6a53c595eb437e8e7b630/Many_Shot_Jailbreaking__2024_04_02_0936.pdf
  - **Code:** —
  - **Mechanism:** PDF companion document to the Anthropic many-shot blog post with extended methodology.
  - **Result:** Same finding as the blog post.
  - **Status:** (vendor blog)

- **LLM Defenses Are Not Robust to Multi-Turn Human Jailbreaks Yet** — Li et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2408.15221
  - **Code:** —
  - **Mechanism:** Empirical evaluation of existing defenses under multi-turn human red-teaming.
  - **Result:** Existing defenses regress substantially under multi-turn human attacks (vs. single-turn automated).
  - **Status:** Verified

## A2. Encoding, obfuscation, and language-shift jailbreaks

- **ArtPrompt** — Jiang et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2402.11753
  - **Code:** https://github.com/uw-nsl/ArtPrompt
  - **Mechanism:** Encodes harmful queries as ASCII art; safety classifiers fail to read the art.
  - **Result:** Visual encoding bypasses text-based safety filters.
  - **Status:** Unverified

- **Low-Resource Language Jailbreaks** — Yong et al. (arXiv 2023).
  - **Source:** https://arxiv.org/abs/2310.02446
  - **Code:** —
  - **Mechanism:** Translate harmful prompts into low-resource languages where safety training under-generalizes.
  - **Result:** English-centric safety training generalizes poorly across languages.
  - **Status:** Unverified

- **Multilingual Jailbreak Challenges** — Deng et al. (arXiv 2023).
  - **Source:** https://arxiv.org/abs/2310.06474
  - **Code:** —
  - **Mechanism:** Cross-lingual jailbreak benchmark measuring safety asymmetry across languages.
  - **Result:** Quantifies the multilingual safety gap with a structured benchmark.
  - **Status:** Unverified

- **Cognitive Overload** — Zhao et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2311.09827
  - **Code:** —
  - **Mechanism:** Forces the model into complex logical reasoning until safety constraints break down.
  - **Result:** Introduces cognitive-overload as a generic-purpose jailbreak primitive.
  - **Status:** Unverified

- **Word Substitution Cipher** — Handa et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2402.10601
  - **Code:** —
  - **Mechanism:** Uses simple word-substitution ciphers the model decodes, executing the harmful instruction post-decode.
  - **Result:** Cipher-based encoding attack against frontier proprietary models.
  - **Status:** Unverified

- **H-CoT (reasoning-model jailbreak)** — Kuo et al. (arXiv 2025).
  - **Source:** https://arxiv.org/abs/2502.12893
  - **Code:** —
  - **Mechanism:** Hijacks the chain-of-thought safety reasoning of reasoning models (o1, R1, Gemini 2.0 Flash Thinking).
  - **Result:** First systematic jailbreak targeting safety-reasoning steps in reasoning-model architectures.
  - **Status:** Unverified

- **HouYi (PI threat model)** — Liu et al. (arXiv 2023).
  - **Source:** https://arxiv.org/abs/2306.05499
  - **Code:** https://github.com/LLMSecurity/HouYi
  - **Mechanism:** Threat model and attack taxonomy for prompt injection in LLM-integrated applications.
  - **Result:** Systematizes attack surface across deployed LLM applications.
  - **Status:** Unverified

- **Universal PI** — Liu et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2403.04957
  - **Code:** —
  - **Mechanism:** Automatic search for transferable PI strings against deployed LLMs.
  - **Result:** Universal/transferable PI strings that work cross-model.
  - **Status:** Unverified

## A3. White-box (gradient) and black-box (query) optimization

- **GCG** — Zou et al. (arXiv 2023).
  - **Source:** https://arxiv.org/abs/2307.15043
  - **Code:** https://github.com/llm-attacks/llm-attacks
  - **Mechanism:** Greedy Coordinate Gradient white-box optimization producing adversarial suffixes.
  - **Result:** Canonical white-box jailbreak; adversarial suffixes transfer across models.
  - **Status:** Verified

- **AdvPrompter** — Paulus et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2404.16873
  - **Code:** —
  - **Mechanism:** Trains a small LLM to generate adversarial prompts that jailbreak a target.
  - **Result:** Fast, adaptive alternative to GCG-style discrete optimization.
  - **Status:** Unverified

- **FLRT (Fluent Student-Teacher)** — Thompson et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2407.17447
  - **Code:** —
  - **Mechanism:** Student-teacher distillation framework producing fluent adversarial prompts.
  - **Result:** Generates natural-language adversarial prompts that evade text-based detectors.
  - **Status:** Unverified

- **PAIR** — Chao et al. (arXiv 2023).
  - **Source:** https://arxiv.org/abs/2310.08419
  - **Code:** —
  - **Mechanism:** Black-box iterative jailbreak using an attacker LLM querying the target model.
  - **Result:** Achieves jailbreak in approximately twenty queries without gradients (per paper title).
  - **Status:** Verified

- **AutoDAN** — Liu et al. (arXiv 2023).
  - **Source:** https://arxiv.org/abs/2310.04451
  - **Code:** —
  - **Mechanism:** Genetic-algorithm-based stealthy jailbreak generator.
  - **Result:** Produces fluent jailbreaks that evade perplexity-based defenses.
  - **Status:** Verified

- **TAP / Tree of Attacks** — Mehrotra et al. (arXiv 2023).
  - **Source:** https://arxiv.org/abs/2312.02119
  - **Code:** —
  - **Mechanism:** Tree-search black-box jailbreak with branch pruning.
  - **Result:** Improves PAIR query-efficiency via tree-search structure.
  - **Status:** Verified

- **Best-of-N Jailbreaking** — Hughes et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2412.03556
  - **Code:** —
  - **Mechanism:** Cheap query-based jailbreak via N parallel perturbations of the attack prompt.
  - **Result:** Demonstrates simple Best-of-N sampling is competitive with sophisticated attacks.
  - **Status:** Unverified

# Direct attacks — hand-crafted, encoding/obfuscation, white-box and black-box jailbreaks

This file collects primary sources on direct prompt-injection and jailbreak techniques that operate on a single targeted LLM. Coverage spans hand-crafted PI taxonomies, encoding/obfuscation attacks, white-box gradient-based optimization, and black-box query-driven attacks. Multi-turn and reasoning-model variants are included.

## A1. Hand-crafted PI taxonomies and persuasion-style jailbreaks

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| Ignore Previous Prompt: Attack Techniques For Language Models | Perez & Ribeiro (2022) | arXiv preprint | arXiv:2211.09527 | — | Foundational taxonomy of direct prompt-injection attacks against instruction-following LLMs. | First systematic categorization of "ignore previous instructions"-style PI patterns. |
| "Do Anything Now": Characterizing and Evaluating In-The-Wild Jailbreak Prompts on Large Language Models | Shen et al. (2023) | arXiv preprint | arXiv:2308.03825 | — | Empirical study of in-the-wild jailbreak prompts ("DAN" family) collected from public forums. | Large-scale measurement of organically discovered jailbreaks across the open community. |
| Jailbroken: How Does LLM Safety Training Fail? | Wei et al. (2023) | arXiv preprint | arXiv:2307.02483 | — | Failure-mode analysis of LLM safety training under adversarial prompts. | Identifies competing-objective and mismatched-generalization as canonical failure modes. |
| How Johnny Can Persuade LLMs to Jailbreak Them: Rethinking Persuasion to Challenge AI Safety by Humanizing LLMs | Zeng et al. (2024) | arXiv preprint | arXiv:2401.06373 | — | Persuasion-taxonomy-driven jailbreak using social-engineering rhetoric. | Adapts human persuasion frameworks (PAP) into a structured jailbreak generator. |
| Great, Now Write an Article About That: The Crescendo Multi-Turn LLM Jailbreak Attack | Russinovich et al. (2024) | arXiv preprint | arXiv:2404.01833 | — | Multi-turn jailbreak that escalates a benign topic toward harmful content over several turns. | Demonstrates that single-turn safety filters miss progressive multi-turn manipulation. |
| Many-shot jailbreaking | Anil et al. (2024) | Anthropic research blog | (no arXiv) | — | In-context jailbreak using hundreds of fake-assistant turns to override safety training. | Shows that long-context window enables a new in-context attack vector. |
| Many-shot Jailbreaking | Anil et al. (2024) | Anthropic research PDF | (no arXiv) | — | PDF companion to the Anthropic many-shot blog post. | Same finding as the blog with extended methodology. |
| LLM Defenses Are Not Robust to Multi-Turn Human Jailbreaks Yet | Phute et al. (2024) | arXiv preprint | arXiv:2408.15221 | — | Empirical evaluation showing existing defenses fail under human multi-turn red-teaming. | Provides hard-positive multi-turn benchmarks where automated defenses regress. |

## A2. Encoding, obfuscation, and language-shift jailbreaks

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| ArtPrompt: ASCII Art-based Jailbreak Attacks against Aligned LLMs | Jiang et al. (2024) | arXiv preprint | arXiv:2402.11753 | — | Encodes harmful queries as ASCII art that safety classifiers fail to read. | Shows that visual encoding bypasses text-based safety filters. |
| Low-Resource Languages Jailbreak GPT-4 | Yong et al. (2023) | arXiv preprint | arXiv:2310.02446 | — | Translates harmful prompts into low-resource languages to bypass alignment. | Demonstrates English-centric safety training generalizes poorly across languages. |
| Multilingual Jailbreak Challenges in Large Language Models | Deng et al. (2023) | arXiv preprint | arXiv:2310.06474 | — | Cross-lingual jailbreak benchmarks measuring safety asymmetry across languages. | Quantifies the multilingual safety gap with a structured benchmark. |
| Cognitive Overload: Jailbreaking Large Language Models with Overloaded Logical Thinking | Zhao et al. (2024) | arXiv preprint | arXiv:2311.09827 | — | Forces the model into complex logical reasoning until safety constraints break. | Introduces cognitive-overload as a generic-purpose jailbreak primitive. |
| Jailbreaking Proprietary Large Language Models using Word Substitution Cipher | Handa et al. (2024) | arXiv preprint | arXiv:2402.10601 | — | Uses simple word-substitution ciphers the model decodes, executing the harmful instruction post-decode. | Cipher-based encoding attack against frontier proprietary models. |
| H-CoT: Hijacking the Chain-of-Thought Safety Reasoning Mechanism to Jailbreak Large Reasoning Models | Kuo et al. (2025) | arXiv preprint | arXiv:2502.12893 | — | Exploits the CoT-style safety reasoning of reasoning models (o1, R1, Gemini 2.0). | First systematic jailbreak targeting safety-reasoning steps in reasoning-model architectures. |
| Prompt Injection attack against LLM-integrated Applications | Liu et al. (2023) | arXiv preprint | arXiv:2306.05499 | — | Threat model and attack taxonomy for prompt injection in real LLM-integrated apps (HouYi). | Systematizes attack surface across deployed LLM applications. |
| Automatic and Universal Prompt Injection Attacks against Large Language Models | Liu et al. (2024) | arXiv preprint | arXiv:2403.04957 | — | Automatic search for transferable PI strings against deployed LLMs. | Universal/transferable PI strings that work cross-model. |

## A3. White-box (gradient) and black-box (query) optimization

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| Universal and Transferable Adversarial Attacks on Aligned Language Models | Zou et al. (2023) | arXiv preprint | arXiv:2307.15043 | llm-attacks/llm-attacks | GCG: gradient-coordinate-gradient white-box attack producing universal adversarial suffixes. | Canonical white-box jailbreak; suffixes transfer across models. |
| AdvPrompter: Fast Adaptive Adversarial Prompting for LLMs | Paulus et al. (2024) | arXiv preprint | arXiv:2404.16873 | — | Trains a small LLM to generate adversarial prompts that jailbreak a target. | Fast, adaptive alternative to GCG-style discrete optimization. |
| FLRT: Fluent Student-Teacher Redteaming | Thompson et al. (2024) | arXiv preprint | arXiv:2407.17447 | — | Student-teacher distillation framework producing fluent adversarial prompts. | Generates natural-language adversarial prompts that evade text-based detectors. |
| Jailbreaking Black Box Large Language Models in Twenty Queries | Chao et al. (2023) | arXiv preprint | arXiv:2310.08419 | — | PAIR: black-box iterative jailbreak using an attacker LLM querying the target. | Achieves jailbreak in ~20 queries without gradients. |
| AutoDAN: Generating Stealthy Jailbreak Prompts on Aligned Large Language Models | Liu et al. (2023) | arXiv preprint | arXiv:2310.04451 | — | Genetic-algorithm-based stealthy jailbreak generator. | Produces fluent jailbreaks that evade perplexity-based defenses. |
| Tree of Attacks: Jailbreaking Black-Box LLMs Automatically | Mehrotra et al. (2023) | arXiv preprint | arXiv:2312.02119 | — | TAP: tree-search black-box jailbreak with branch pruning. | Improves PAIR query-efficiency via tree-search structure. |
| Best-of-N Jailbreaking | Hughes et al. (2024) | arXiv preprint | arXiv:2412.03556 | — | Cheap query-based jailbreak via N parallel perturbations. | Demonstrates simple Best-of-N sampling is competitive with sophisticated attacks. |

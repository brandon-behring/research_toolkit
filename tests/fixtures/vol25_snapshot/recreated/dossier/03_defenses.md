# Defenses — detection, smoothing, architectural, latent-space, alignment

This file collects primary sources on defenses against prompt-injection and jailbreak attacks. Coverage spans classifier-based detection, randomization/smoothing, architectural separation of trusted/untrusted instructions, latent-space interventions, and alignment-as-defense.

## A1. Detection classifiers (Llama Guard, WildGuard, ShieldGemma, Constitutional Classifiers)

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| Llama Guard: LLM-based Input-Output Safeguard for Human-AI Conversations | Inan et al. (2023) | arXiv preprint | arXiv:2312.06674 | — | LLM-based safety classifier for input/output moderation in conversational AI. | Introduces Llama Guard as the canonical open input-output safety classifier. |
| WildGuard: Open One-Stop Moderation Tools for Safety Risks, Jailbreaks, and Refusals of LLMs | Han et al. (2024) | arXiv preprint | arXiv:2406.18495 | — | Multi-task moderation classifier covering risks, jailbreaks, and refusal handling. | Single-model classifier handling multiple safety dimensions. |
| ShieldGemma: Generative AI Content Moderation Based on Gemma | Zeng et al. (2024) | arXiv preprint | arXiv:2407.21772 | — | Gemma-based safety classifier for content moderation. | Open Gemma-derived alternative to Llama Guard for content moderation. |
| Constitutional Classifiers: Defending against Universal Jailbreaks across Thousands of Hours of Red Teaming | Sharma et al. (2025) | arXiv preprint | arXiv:2501.18837 | — | Constitution-trained classifiers tested against thousands of red-team hours. | Production-grade red-teamed classifier defense with public eval log. |
| Constitutional Classifiers++: Efficient Production-Grade Defenses against Universal Jailbreaks | Anthropic (2026) | arXiv preprint | arXiv:2601.04603 | — | Efficiency-focused successor to Constitutional Classifiers for production deployment. | Reduces inference cost of Constitutional Classifiers while preserving robustness. |
| Constitutional Classifiers: Defending against universal jailbreaks | Anthropic (2024) | Anthropic research blog | (no arXiv) | — | Blog companion to the Constitutional Classifiers paper. | Vendor blog framing of the Constitutional Classifier deployment. |
| JailGuard: A Universal Detection Framework for LLM Prompt-based Attacks | Zhang et al. (2023) | arXiv preprint | arXiv:2312.10766 | — | Universal jailbreak-detection framework using prompt mutation. | Mutation-based detection generalizes across attack families. |
| Llama-Prompt-Guard-2-86M | Meta (2024) | HF model card | (no arXiv) | meta-llama/Llama-Prompt-Guard-2-86M | Meta's lightweight prompt-injection classifier (HF model card). | Open small-model classifier for prompt-injection detection. |
| deberta-v3-base-prompt-injection-v2 | Protect AI (2024) | HF model card | (no arXiv) | protectai/deberta-v3-base-prompt-injection-v2 | Protect AI's DeBERTa-v3 prompt-injection detector v2. | Widely-used open DeBERTa baseline classifier for PI detection. |

## A2. Smoothing and runtime-randomization defenses

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| SmoothLLM: Defending Large Language Models Against Jailbreaking Attacks | Robey et al. (2023) | arXiv preprint | arXiv:2310.03684 | — | Randomized perturbation + majority vote at inference time. | Canonical smoothing-based defense against adversarial-suffix jailbreaks. |
| SafeDecoding: Defending against Jailbreak Attacks via Safety-Aware Decoding | Xu et al. (2024) | arXiv preprint | arXiv:2402.08983 | — | Decoding-time defense that re-weights safe tokens during generation. | Runtime decoding intervention without retraining. |

## A3. Architectural defenses (instruction hierarchy, spotlighting, StruQ, SecAlign, CaMeL)

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| The Instruction Hierarchy: Training LLMs to Prioritize Privileged Instructions | Wallace et al. (2024) | arXiv preprint | arXiv:2404.13208 | — | Trains models to honor a hierarchy among system/user/tool instructions. | Establishes instruction-hierarchy training as a structural PI defense. |
| Defending Against Indirect Prompt Injection Attacks With Spotlighting | Hines et al. (2024) | arXiv preprint | arXiv:2403.14720 | — | Spotlighting marks untrusted content so the model can identify it. | Lightweight prompt-engineering defense for indirect-PI threats. |
| StruQ: Defending Against Prompt Injection with Structured Queries | Chen et al. (2024) | arXiv preprint | arXiv:2402.06363 | — | Structured-query format separating trusted instructions from untrusted data. | Architectural separation defense via structured input format. |
| SecAlign: Defending Against Prompt Injection with Preference Optimization | Chen et al. (2024) | arXiv preprint | arXiv:2410.05451 | — | Preference-optimization training that hardens against PI inputs. | Combines DPO with PI-targeted training data. |
| Defeating Prompt Injections by Design | Debenedetti et al. (2025) | arXiv preprint | arXiv:2503.18813 | — | CaMeL: capability-controlled architecture defeating PI by design. | Architectural design that structurally prevents PI from triggering tool use. |
| CaMeL offers a promising new direction for mitigating prompt injection attacks | Willison (2025) | Simon Willison's Weblog | (no arXiv) | — | Independent analysis of the CaMeL defense direction. | Independent commentary contextualizing CaMeL within the defense landscape. |
| Jailbreak and Guard Aligned Language Models with Only Few In-Context Demonstrations | Wei et al. (2023) | arXiv preprint | arXiv:2310.06387 | — | In-context demonstrations as both attack and defense levers. | Shows few-shot in-context examples can both jailbreak and guard models. |
| Prompt Injection Attacks in Defended Systems | Zheng et al. (2024) | arXiv preprint | arXiv:2406.14048 | — | Studies paraphrase-based defenses against PI in real systems. | Paraphrase-as-defense effectiveness across attack families. |
| prompt-injection-defenses | tldrsec (2024) | GitHub repo | (no arXiv) | tldrsec/prompt-injection-defenses | Curated catalog of practical and proposed PI defenses. | Living index of PI defense techniques across the field. |
| How Microsoft defends against indirect prompt injection attacks | Microsoft (2025) | Microsoft Security blog | (no arXiv) | — | Microsoft's disclosure of in-product PI defenses. | Vendor disclosure of production PI-defense layering. |

## A4. Latent-space defenses (circuit breakers, refusal direction, representation engineering)

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| Improving Alignment and Robustness with Circuit Breakers | Zou et al. (2024) | arXiv preprint | arXiv:2406.04313 | — | Latent-space interventions that disrupt harmful representations. | Introduces representation-rerouting as a robust defense primitive. |
| Refusal in Language Models Is Mediated by a Single Direction | Arditi et al. (2024) | arXiv preprint | arXiv:2406.11717 | — | Identifies a single linear direction mediating refusal in aligned LLMs. | Mechanistic finding: refusal is mediated by a one-dimensional subspace. |
| Representation Engineering for Large-Language Models: Survey and Research Challenges | Zou et al. (2025) | arXiv preprint | arXiv:2502.17601 | — | Survey of representation-engineering methods for LLM alignment and robustness. | Provides field-level taxonomy of representation-engineering interventions. |

## A5. Alignment-as-defense (Constitutional AI, RAIN, robust alignment, shallow-deep safety)

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| Constitutional AI: Harmlessness from AI Feedback | Bai et al. (2022) | arXiv preprint | arXiv:2212.08073 | — | Constitution-driven RLAIF for training harmless assistants. | Establishes Constitutional AI training paradigm. |
| RAIN: Your Language Models Can Align Themselves without Finetuning | Li et al. (2023) | arXiv preprint | arXiv:2309.07124 | — | Inference-time self-alignment via reflective decoding. | Alignment without finetuning via tree-search self-evaluation. |
| Defending Against Alignment-Breaking Attacks via Robustly Aligned LLM | Cao et al. (2023) | arXiv preprint | arXiv:2309.14348 | — | Robust-alignment training procedure resilient to alignment-breaking attacks. | Defense-aware alignment training pipeline. |
| Safety Alignment Should Be Made More Than Just a Few Tokens Deep | Qi et al. (2024) | arXiv preprint | arXiv:2406.05946 | — | Argues current safety alignment is shallow and propose deep-token interventions. | Names "shallow alignment" pathology and motivates deeper defenses. |

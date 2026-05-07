# 03 — Defenses (detection, smoothing, architectural, latent-space, alignment)

**Scope:** primary sources on defenses against prompt-injection and jailbreak attacks: classifier-based detection, runtime smoothing/randomization, architectural separation of trusted/untrusted instructions, latent-space interventions, and alignment-as-defense.
**Out of scope:** attacks themselves (see `01_direct_attacks.md` and `02_indirect_and_agentic_attacks.md`); detection benchmarks (see `05_datasets_and_benchmarks.md`).

## A1. Detection classifiers

- **Llama Guard** — Inan et al. (arXiv 2023).
  - **Source:** https://arxiv.org/abs/2312.06674
  - **Code:** —
  - **Mechanism:** LLM-based safety classifier for input/output moderation.
  - **Result:** Establishes Llama Guard as the canonical open input-output safety classifier.
  - **Status:** Unverified

- **WildGuard** — Han et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2406.18495
  - **Code:** —
  - **Mechanism:** Multi-task moderation classifier covering risks, jailbreaks, and refusal handling.
  - **Result:** Single-model classifier handling multiple safety dimensions.
  - **Status:** Unverified

- **ShieldGemma** — Zeng et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2407.21772
  - **Code:** —
  - **Mechanism:** Gemma-based safety classifier for content moderation.
  - **Result:** Open Gemma-derived alternative to Llama Guard for content moderation.
  - **Status:** Unverified

- **Constitutional Classifiers** — Sharma et al. (arXiv 2025).
  - **Source:** https://arxiv.org/abs/2501.18837
  - **Code:** —
  - **Mechanism:** Constitution-trained classifiers tested against thousands of red-team hours.
  - **Result:** Production-grade red-teamed classifier defense with public eval log.
  - **Status:** Unverified

- **Constitutional Classifiers++** — Anthropic (arXiv 2026).
  - **Source:** https://arxiv.org/abs/2601.04603
  - **Code:** —
  - **Mechanism:** Efficiency-focused successor to Constitutional Classifiers for production deployment.
  - **Result:** Reduces inference cost of Constitutional Classifiers while preserving robustness.
  - **Status:** Unverified

- **Constitutional Classifiers (Anthropic blog)** — Anthropic (2024).
  - **Source:** https://www.anthropic.com/research/constitutional-classifiers
  - **Code:** —
  - **Mechanism:** Blog companion to the Constitutional Classifiers paper.
  - **Result:** Vendor-blog framing of Constitutional Classifier deployment.
  - **Status:** (vendor blog)

- **JailGuard** — Zhang et al. (arXiv 2023).
  - **Source:** https://arxiv.org/abs/2312.10766
  - **Code:** —
  - **Mechanism:** Universal jailbreak-detection framework using prompt mutation.
  - **Result:** Mutation-based detection generalizes across attack families.
  - **Status:** Unverified

- **Llama Prompt Guard 2** — Meta (HF 2024).
  - **Source:** https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M
  - **Code:** https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M
  - **Mechanism:** Meta's lightweight prompt-injection classifier (HF model card).
  - **Result:** Open small-model classifier for prompt-injection detection.
  - **Status:** Unverified

- **Protect AI DeBERTa-v3 v2** — Protect AI (HF 2024).
  - **Source:** https://huggingface.co/protectai/deberta-v3-base-prompt-injection-v2
  - **Code:** https://huggingface.co/protectai/deberta-v3-base-prompt-injection-v2
  - **Mechanism:** DeBERTa-v3 fine-tuned for prompt-injection detection (HF model card).
  - **Result:** Widely-used open DeBERTa baseline classifier for PI detection.
  - **Status:** Unverified

## A2. Smoothing and runtime-randomization defenses

- **SmoothLLM** — Robey et al. (arXiv 2023).
  - **Source:** https://arxiv.org/abs/2310.03684
  - **Code:** —
  - **Mechanism:** Randomized perturbation of inputs followed by majority vote at inference time.
  - **Result:** Canonical smoothing-based defense against adversarial-suffix jailbreaks.
  - **Status:** Verified

- **SafeDecoding** — Xu et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2402.08983
  - **Code:** —
  - **Mechanism:** Decoding-time defense that re-weights safe tokens during generation.
  - **Result:** Runtime decoding intervention without retraining.
  - **Status:** Unverified

## A3. Architectural defenses (instruction hierarchy, spotlighting, StruQ, SecAlign, CaMeL)

- **Instruction Hierarchy** — Wallace et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2404.13208
  - **Code:** —
  - **Mechanism:** Trains models to honor a hierarchy among system/user/tool instructions.
  - **Result:** Establishes instruction-hierarchy training as a structural PI defense.
  - **Status:** Verified

- **Spotlighting** — Hines et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2403.14720
  - **Code:** —
  - **Mechanism:** Marks untrusted content within the prompt so the model can identify and ignore PI.
  - **Result:** Lightweight prompt-engineering defense for indirect-PI threats.
  - **Status:** Verified

- **StruQ** — Chen et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2402.06363
  - **Code:** —
  - **Mechanism:** Structured-query format separating trusted instructions from untrusted data.
  - **Result:** Architectural separation defense via structured input format.
  - **Status:** Verified

- **SecAlign** — Chen et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2410.05451
  - **Code:** —
  - **Mechanism:** Preference-optimization training that hardens against PI inputs.
  - **Result:** Combines DPO with PI-targeted training data for robust defense.
  - **Status:** Verified

- **CaMeL** — Debenedetti et al. (arXiv 2025).
  - **Source:** https://arxiv.org/abs/2503.18813
  - **Code:** —
  - **Mechanism:** Capability-controlled architecture defeating PI by design.
  - **Result:** Architectural design that structurally prevents PI from triggering tool use.
  - **Status:** Unverified

- **CaMeL commentary (Willison)** — Willison (2025).
  - **Source:** https://simonwillison.net/2025/Apr/11/camel/
  - **Code:** —
  - **Mechanism:** Independent analysis of the CaMeL defense direction.
  - **Result:** Independent commentary contextualizing CaMeL within the defense landscape.
  - **Status:** (vendor blog)

- **Few-shot Guard / Jailbreak (Wei)** — Wei et al. (arXiv 2023).
  - **Source:** https://arxiv.org/abs/2310.06387
  - **Code:** —
  - **Mechanism:** In-context demonstrations as both attack and defense levers.
  - **Result:** Shows few-shot in-context examples can both jailbreak and guard models.
  - **Status:** Unverified

- **Paraphrase Defense** — Zheng et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2406.14048
  - **Code:** —
  - **Mechanism:** Studies paraphrase-based defenses against PI in real systems.
  - **Result:** Paraphrase-as-defense effectiveness across attack families.
  - **Status:** Unverified

- **prompt-injection-defenses (catalog)** — tldrsec (2024).
  - **Source:** https://github.com/tldrsec/prompt-injection-defenses
  - **Code:** https://github.com/tldrsec/prompt-injection-defenses
  - **Mechanism:** Curated GitHub catalog of practical and proposed PI defenses.
  - **Result:** Living index of PI defense techniques across the field.
  - **Status:** (vendor blog)

- **Microsoft Defends Indirect PI** — Microsoft (2025).
  - **Source:** https://www.microsoft.com/en-us/msrc/blog/2025/07/how-microsoft-defends-against-indirect-prompt-injection-attacks
  - **Code:** —
  - **Mechanism:** Microsoft's disclosure of in-product PI defenses.
  - **Result:** Vendor disclosure of production PI-defense layering.
  - **Status:** (vendor blog)

## A4. Latent-space defenses (circuit breakers, refusal direction, representation engineering)

- **Circuit Breakers** — Zou et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2406.04313
  - **Code:** —
  - **Mechanism:** Latent-space interventions that disrupt harmful representations.
  - **Result:** Introduces representation-rerouting as a robust defense primitive.
  - **Status:** Verified

- **Refusal direction** — Arditi et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2406.11717
  - **Code:** —
  - **Mechanism:** Identifies a single linear direction mediating refusal in aligned LLMs.
  - **Result:** Mechanistic finding: refusal is mediated by a one-dimensional subspace.
  - **Status:** Verified

- **Representation Engineering Survey** — Zou et al. (arXiv 2025).
  - **Source:** https://arxiv.org/abs/2502.17601
  - **Code:** —
  - **Mechanism:** Survey of representation-engineering methods for LLM alignment and robustness.
  - **Result:** Provides field-level taxonomy of representation-engineering interventions.
  - **Status:** Unverified

## A5. Alignment-as-defense

- **Constitutional AI** — Bai et al. (arXiv 2022).
  - **Source:** https://arxiv.org/abs/2212.08073
  - **Code:** —
  - **Mechanism:** Constitution-driven RLAIF for training harmless assistants.
  - **Result:** Establishes the Constitutional AI training paradigm.
  - **Status:** Verified

- **RAIN** — Li et al. (arXiv 2023).
  - **Source:** https://arxiv.org/abs/2309.07124
  - **Code:** —
  - **Mechanism:** Inference-time self-alignment via reflective decoding.
  - **Result:** Alignment without finetuning via tree-search self-evaluation.
  - **Status:** Unverified

- **Robustly Aligned LLM (Cao)** — Cao et al. (arXiv 2023).
  - **Source:** https://arxiv.org/abs/2309.14348
  - **Code:** —
  - **Mechanism:** Robust-alignment training procedure resilient to alignment-breaking attacks.
  - **Result:** Defense-aware alignment training pipeline.
  - **Status:** Unverified

- **Shallow-Deep Safety Alignment** — Qi et al. (arXiv 2024).
  - **Source:** https://arxiv.org/abs/2406.05946
  - **Code:** —
  - **Mechanism:** Argues current safety alignment is shallow and proposes deeper-token interventions.
  - **Result:** Names the "shallow alignment" pathology and motivates deeper defenses.
  - **Status:** Unverified

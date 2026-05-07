# 07 — Standards, regulatory, lab frameworks, industry reports

**Scope:** standards bodies (NIST, OWASP, MITRE), regulatory frameworks (EU AI Act, UK AISI), frontier-lab voluntary safety frameworks (RSP, Preparedness, FSF), system cards, and industry reports.
**Out of scope:** academic papers (see `01_direct_attacks.md` through `04_training_time_threats.md`); benchmarks (see `05_datasets_and_benchmarks.md`); vendor product pages (see `06_tools_and_vendors.md`).

## A1. Standards bodies (NIST, OWASP, MITRE)

- **NIST AI 600-1 (GenAI Profile)** — NIST (2024).
  - **Source:** https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence
  - **Status:** Government risk-management framework
  - **Product line:** NIST AI RMF GenAI profile
  - **Mechanism:** Risk-management framework specifically scoped to generative AI.
  - **Integration:** Reference framework for US federal AI risk management.

- **OWASP LLM01:2025 (Prompt Injection)** — OWASP (2025).
  - **Source:** https://genai.owasp.org/llmrisk/llm01-prompt-injection/
  - **Status:** OWASP project entry
  - **Product line:** OWASP Top 10 for LLM Applications
  - **Mechanism:** OWASP's prompt-injection entry in the LLM Top 10 list.
  - **Integration:** Authoritative OWASP entry referenced in PI literature.

- **OWASP Top 10 for LLM Applications 2025 (PDF)** — OWASP (2025).
  - **Source:** https://owasp.org/www-project-top-10-for-large-language-model-applications/assets/PDF/OWASP-Top-10-for-LLMs-v2025.pdf
  - **Status:** OWASP publication
  - **Product line:** OWASP Top 10 for LLM Applications
  - **Mechanism:** Full PDF of the 2025 OWASP Top 10 for LLM Applications.
  - **Integration:** Field-standard LLM application security top-10 list.

- **MITRE ATLAS** — MITRE (2024).
  - **Source:** https://atlas.mitre.org/
  - **Status:** MITRE program (active catalog)
  - **Product line:** Adversarial threat catalog for AI
  - **Mechanism:** ATT&CK-style threat catalog for AI systems with structured tactics/techniques.
  - **Integration:** Field-standard adversarial-AI threat catalog.

## A2. Regulatory frameworks (EU, UK)

- **EU AI Act** — European Commission (2024).
  - **Source:** https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai
  - **Status:** EU regulation (in force)
  - **Product line:** Cross-sector AI regulation
  - **Mechanism:** EU regulatory framework for AI systems by risk tier.
  - **Integration:** Authoritative EU regulatory text reference.

- **UK AISI Frontier AI Trends Report** — UK AISI (2025).
  - **Source:** https://www.aisi.gov.uk/frontier-ai-trends-report
  - **Status:** UK government publication
  - **Product line:** Frontier-AI risk + trend report
  - **Mechanism:** UK AI Security Institute frontier-AI trends report.
  - **Integration:** UK government's frontier-AI risk and trend assessment.

## A3. Frontier-lab voluntary safety frameworks and system cards

- **Anthropic RSP** — Anthropic (2024).
  - **Source:** https://www.anthropic.com/responsible-scaling-policy
  - **Status:** Voluntary lab framework (vendor blog)
  - **Product line:** Responsible Scaling Policy
  - **Mechanism:** Capability-tier safety framework with deployment gates per AI Safety Level.
  - **Integration:** Anthropic's internal capability-tier safety regime.

- **OpenAI Preparedness Framework** — OpenAI (2025).
  - **Source:** https://openai.com/index/updating-our-preparedness-framework/
  - **Status:** Voluntary lab framework (vendor blog)
  - **Product line:** Preparedness Framework
  - **Mechanism:** OpenAI's frontier-risk capability framework.
  - **Integration:** OpenAI's analogue to Anthropic's RSP.

- **DeepMind Frontier Safety Framework** — DeepMind (2024).
  - **Source:** https://deepmind.google/blog/introducing-the-frontier-safety-framework/
  - **Status:** Voluntary lab framework (vendor blog)
  - **Product line:** Frontier Safety Framework
  - **Mechanism:** DeepMind's analogue to RSP/Preparedness frameworks.
  - **Integration:** DeepMind's frontier-capability safety regime.

- **Frontier Model Forum Capability Assessments** — FMF (2024).
  - **Source:** https://www.frontiermodelforum.org/technical-reports/frontier-capability-assessments/
  - **Status:** Industry consortium publication
  - **Product line:** Frontier Capability Assessments
  - **Mechanism:** Cross-lab consortium capability-assessment publication.
  - **Integration:** Joint cross-lab capability-assessment framework.

- **Claude 4 System Card** — Anthropic (2025).
  - **Source:** https://www.anthropic.com/claude-4-system-card
  - **Status:** Vendor system card (vendor blog)
  - **Product line:** Claude 4 family
  - **Mechanism:** System card for Claude Opus 4 and Sonnet 4.
  - **Integration:** Vendor disclosure of Claude 4 family safety profile.

- **OpenAI Approach to Frontier Risk** — OpenAI (2024).
  - **Source:** https://openai.com/global-affairs/our-approach-to-frontier-risk/
  - **Status:** OpenAI policy statement (vendor blog)
  - **Product line:** Frontier-risk policy
  - **Mechanism:** OpenAI's high-level frontier-risk approach statement.
  - **Integration:** OpenAI's framing of frontier-AI risk policy.

- **GPT-4o System Card** — OpenAI (2024).
  - **Source:** https://openai.com/index/gpt-4o-system-card/
  - **Status:** Vendor system card (vendor blog)
  - **Product line:** GPT-4o
  - **Mechanism:** System card for GPT-4o.
  - **Integration:** Vendor disclosure of GPT-4o safety evaluation.

- **OpenAI o1 System Card** — OpenAI (2024).
  - **Source:** https://openai.com/index/openai-o1-system-card/
  - **Status:** Vendor system card (vendor blog)
  - **Product line:** o1 reasoning model
  - **Mechanism:** System card for the OpenAI o1 reasoning model.
  - **Integration:** Vendor disclosure of o1 reasoning-model safety evaluation.

## A4. Other / cross-cutting tool references

- **llm-attacks (cross-listing)** — Zou et al. (GitHub 2023).
  - **Source:** https://github.com/llm-attacks/llm-attacks
  - **Status:** Reference implementation
  - **Product line:** GCG attack
  - **Mechanism:** Cross-reference of the GCG codebase from the standards/other category.
  - **Integration:** Standalone attack codebase (also cross-listed in `06_tools_and_vendors.md`).

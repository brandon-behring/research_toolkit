# Research Plan: Calibration Methods & Metrics (Medium Fixture)

A scoped subset of vol28 covering classical calibration methods and calibration metrics. Used as a v1.1+ schema reference and test fixture (~22 entries). Full vol28 covers 6 sub-areas; this fixture covers 2.

## Sub-areas

- A1. Classical calibration methods
  - Source types: arXiv, ICML/NeurIPS/JMLR, classical ML papers
  - Notes: temperature scaling, Platt scaling, isotonic, Beta calibration, histogram binning, vector/matrix scaling.
- A2. Calibration metrics & reliability diagrams
  - Source types: arXiv, AAAI/AISTATS/JMLR
  - Notes: ECE family, Brier score, proper scoring rules, reliability diagrams.
- A3. (Padding) Empirical comparisons
  - Source types: arXiv preprints
  - Notes: cross-cutting empirical evaluations of calibration methods/metrics.
- A4. (Padding) Foundational references
  - Source types: classical statistics, JSTOR
  - Notes: pre-2010 calibration foundations cited as references.

## Out-of-scope

- Conformal prediction (separate sub-area in full vol28)
- Uncertainty quantification (deep ensembles / MC dropout / Bayesian)
- OOD detection
- LLM-specific calibration

## Claim family taxonomy

- calibration_method
- calibration_metric
- comparison_study

## Known landmark papers

- guo2017calibration: temperature scaling, modern NN calibration baseline
- platt1999platt: Platt scaling — sigmoid post-hoc calibration
- naeini2015obtaining: Bayesian binning + ECE family

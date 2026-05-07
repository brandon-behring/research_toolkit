# Classical calibration methods & metrics

Post-hoc and training-time calibration recipes for classifiers, plus the metrics and reliability diagnostics used to evaluate them. LLM-specific calibration lives in `05_llm_calibration.md`; conformal prediction lives in `02_conformal_prediction.md`.

## A1. Post-hoc calibration: scaling methods

- **Platt scaling** — Platt (1999, *Advances in Large Margin Classifiers*).
  - **Source:** https://www.researchgate.net/publication/2594015_Probabilistic_Outputs_for_Support_Vector_Machines_and_Comparisons_to_Regularized_Likelihood_Methods
  - **Code:** —
  - **Mechanism:** Fits a 2-parameter sigmoid on top of SVM decision scores via maximum likelihood on a held-out calibration set.
  - **Result:** Original "Platt scaling" recipe — turns uncalibrated margin scores into probabilities and remains a standard baseline.
  - **Status:** (no widely-known repo) Verified.

- **Temperature scaling** — Guo et al. (ICML 2017).
  - **Source:** https://arxiv.org/abs/1706.04599
  - **Code:** https://github.com/gpleiss/temperature_scaling
  - **Mechanism:** Divides pre-softmax logits by a single learned scalar T fit by NLL on a held-out calibration set.
  - **Result:** Establishes temperature scaling as the strong default post-hoc baseline for deep nets and popularizes ECE as the headline calibration metric.
  - **Status:** Verified.

- **Beta calibration** — Kull et al. (AISTATS 2017).
  - **Source:** http://proceedings.mlr.press/v54/kull17a.html
  - **Code:** —
  - **Mechanism:** Replaces Platt's logistic with a 3-parameter Beta-family link tailored to scores already in [0,1].
  - **Result:** Strictly more flexible than Platt while remaining identifiable; avoids the bias Platt has on already-near-calibrated scores.
  - **Status:** (no widely-known repo) Verified.

- **Dirichlet calibration** — Kull et al. (NeurIPS 2019).
  - **Source:** https://arxiv.org/abs/1910.12656
  - **Code:** https://github.com/dirichletcal/dirichlet_python
  - **Mechanism:** Generalizes matrix/vector scaling via a Dirichlet-link parametric family with ODIR regularization.
  - **Result:** Provides a full multiclass scaling parameterization that controls overfitting on small calibration sets.
  - **Status:** Verified.

## A2. Post-hoc calibration: binning & non-parametric methods

- **Histogram binning / isotonic recalibration** — Zadrozny & Elkan (ICML 2001).
  - **Source:** https://cseweb.ucsd.edu/~elkan/calibrated.pdf
  - **Code:** —
  - **Mechanism:** Applies histogram binning and isotonic regression to recalibrate decision-tree and naive-Bayes outputs.
  - **Result:** First systematic use of isotonic regression as a post-hoc calibrator for ML classifiers.
  - **Status:** (no widely-known repo) Verified.

- **Multiclass Platt/isotonic** — Zadrozny & Elkan (KDD 2002).
  - **Source:** https://doi.org/10.1145/775047.775151
  - **Code:** —
  - **Mechanism:** Extends Platt and isotonic recalibration to the multiclass setting via one-vs-rest decomposition.
  - **Result:** Established the multiclass post-hoc calibration recipe that remained the default for decades.
  - **Status:** (no widely-known repo) Verified.

- **Predicting Good Probabilities** — Niculescu-Mizil & Caruana (ICML 2005).
  - **Source:** https://www.cs.cornell.edu/~alexn/papers/calibration.icml05.crc.rev3.pdf
  - **Code:** —
  - **Mechanism:** Empirical comparison of Platt scaling, isotonic regression and raw scores across 10 classifier families.
  - **Result:** Definitive empirical evidence that boosted trees / SVMs need calibration while bagged trees do not.
  - **Status:** (no widely-known repo) Verified.

- **Mix-n-Match** — Zhang et al. (ICML 2020).
  - **Source:** https://arxiv.org/abs/2003.07329
  - **Code:** https://github.com/zhang64-llnl/Mix-n-Match-Calibration
  - **Mechanism:** Mixes parametric (temperature) and non-parametric (histogram) calibrators in an ensemble.
  - **Result:** Compositional calibrator combining accuracy-preserving and data-efficient binning beats either component alone.
  - **Status:** Verified.

- **Spline calibration** — Gupta et al. (ICLR 2021).
  - **Source:** https://arxiv.org/abs/2006.12800
  - **Code:** https://github.com/kartikgupta-at-anu/spline-calibration
  - **Mechanism:** Recalibrates by fitting a smoothing spline to the empirical reliability curve.
  - **Result:** Binning-free non-parametric calibrator that avoids the bias-variance tradeoff of histogram methods.
  - **Status:** Verified.

- **Scaling-binning (verified calibration)** — Kumar et al. (NeurIPS 2019).
  - **Source:** https://arxiv.org/abs/1909.10155
  - **Code:** https://github.com/p-lambda/verified_calibration
  - **Mechanism:** Composes a parametric scaler with a uniform-mass binning step and provides sample-complexity guarantees.
  - **Result:** First post-hoc calibrator with provably low calibration error and a debiased ECE estimator.
  - **Status:** Verified.

## A3. Calibration during training

- **Label smoothing for calibration** — Müller et al. (NeurIPS 2019).
  - **Source:** https://arxiv.org/abs/1906.02629
  - **Code:** —
  - **Mechanism:** Analyzes the effect of label smoothing on representations and downstream calibration.
  - **Result:** Shows label smoothing implicitly calibrates by penalizing overconfident logits, but harms knowledge distillation.
  - **Status:** (no widely-known repo) Verified.

- **Mixup calibration** — Thulasidasan et al. (NeurIPS 2019).
  - **Source:** https://arxiv.org/abs/1905.11001
  - **Code:** https://github.com/paganpasta/onmixup
  - **Mechanism:** Empirically studies the calibration side-effect of mixup augmentation.
  - **Result:** Mixup yields better-calibrated and more OOD-robust nets without an explicit calibration loss.
  - **Status:** Verified.

## A4. Calibration metrics & reliability diagrams

- **Brier score** — Brier (Monthly Weather Review 1950).
  - **Source:** https://ui.adsabs.harvard.edu/abs/1950MWRv...78....1B/abstract
  - **Code:** —
  - **Mechanism:** Introduces the squared-error scoring rule for probabilistic weather forecasts.
  - **Result:** The original Brier score — a strictly proper scoring rule still used as the default calibration-aware accuracy metric.
  - **Status:** (no widely-known repo) Verified.

- **DeGroot-Fienberg decomposition** — DeGroot & Fienberg (The Statistician 1983).
  - **Source:** https://www.jstor.org/stable/2987588
  - **Code:** —
  - **Mechanism:** Decomposes proper scoring rules into calibration plus refinement components.
  - **Result:** Foundational decomposition showing calibration and sharpness are orthogonal goals.
  - **Status:** (no widely-known repo) Verified.

- **Strictly proper scoring rules** — Gneiting & Raftery (JASA 2007).
  - **Source:** https://doi.org/10.1198/016214506000001437
  - **Code:** —
  - **Mechanism:** Unified treatment of strictly proper scoring rules for probabilistic prediction.
  - **Result:** Reference modern statement of the proper-scoring-rule theory underlying ECE / Brier / log-loss.
  - **Status:** (no widely-known repo) Verified.

- **BBQ / modern ECE** — Naeini et al. (AAAI 2015).
  - **Source:** https://ojs.aaai.org/index.php/AAAI/article/view/9602
  - **Code:** —
  - **Mechanism:** Bayesian model averaging over equal-frequency binning schemes (BBQ).
  - **Result:** Introduces ECE in its modern AAAI form and BBQ as a Bayesian binning calibrator.
  - **Status:** (no widely-known repo) Verified.

- **Adaptive ECE (ACE)** — Nixon et al. (CVPR 2019 Workshop).
  - **Source:** https://arxiv.org/abs/1904.01685
  - **Code:** —
  - **Mechanism:** Critical review of ECE estimators; proposes adaptive-binning ACE.
  - **Result:** Shows equal-width-bin ECE is unreliable for deep nets and recommends adaptive-bin variants.
  - **Status:** (no widely-known repo) Verified.

- **Debiased ECE** — Roelofs et al. (AISTATS 2022).
  - **Source:** https://arxiv.org/abs/2012.08668
  - **Code:** https://github.com/google-research/google-research
  - **Mechanism:** Quantifies the upward bias of plug-in ECE estimators with finite samples.
  - **Result:** Proposes debiased estimators with reduced sample bias and clarifies which ECE variants to use when.
  - **Status:** Verified.

- **Distribution-free binary calibration** — Gupta et al. (NeurIPS 2020).
  - **Source:** https://arxiv.org/abs/2006.10564
  - **Code:** https://github.com/aigen/df-posthoc-calibration
  - **Mechanism:** Distribution-free guarantees for calibration, confidence intervals and prediction sets in the binary case.
  - **Result:** Unifies post-hoc calibration with conformal-style coverage guarantees.
  - **Status:** Verified.

- **Calibration hypothesis tests** — Vaicenavicius et al. (AISTATS 2019).
  - **Source:** https://arxiv.org/abs/1902.06977
  - **Code:** https://github.com/uu-sml/calibration
  - **Mechanism:** Statistical hypothesis-testing framework for calibration evaluation.
  - **Result:** Provides asymptotic tests for calibration and characterizes ECE-estimator inconsistency.
  - **Status:** Verified.

- **Kernel calibration tests** — Widmann et al. (NeurIPS 2019).
  - **Source:** https://arxiv.org/abs/1910.11385
  - **Code:** https://github.com/devmotion/CalibrationTests.jl
  - **Mechanism:** Kernel-based calibration tests that consume the full multiclass simplex.
  - **Result:** First consistent calibration test that uses the entire predicted distribution rather than top-label only.
  - **Status:** Verified.

- **Pitfalls of in-domain UQ** — Ashukha et al. (ICLR 2020).
  - **Source:** https://arxiv.org/abs/2002.06470
  - **Code:** —
  - **Mechanism:** Empirical audit of UQ methods using calibrated test log-likelihood as the comparison metric.
  - **Result:** Argues most UQ comparisons are confounded by uncalibrated baselines; standardizes evaluation under temperature scaling.
  - **Status:** Verified.

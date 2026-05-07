# Classical Calibration Methods & Metrics

This file covers post-hoc and training-time calibration methods (G1) together with calibration metrics and reliability diagnostics (G2). LLM-specific calibration lives in `05_llm_calibration.md`; conformal prediction lives in `02_conformal_prediction.md`.

---

## A1. Post-hoc Calibration: Scaling Methods

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| Probabilistic Outputs for Support Vector Machines and Comparisons to Regularized Likelihood Methods | Platt (1999) | Advances in Large Margin Classifiers (MIT Press) | (no arXiv) | — | Fits a sigmoid on top of SVM decision scores via maximum likelihood on a held-out set | Original "Platt scaling" recipe — turns uncalibrated margin scores into probabilities with a 2-parameter logistic |
| On Calibration of Modern Neural Networks | Guo et al. (2017) | ICML 2017 | arXiv:1706.04599 | gpleiss/temperature_scaling | Shows modern deep nets are systematically overconfident and proposes temperature scaling | Establishes temperature scaling as the strong default post-hoc baseline; introduces ECE as common evaluation metric |
| Beta calibration: a well-founded and easily implemented improvement on logistic calibration for binary classifiers | Kull et al. (2017) | AISTATS 2017 | (no arXiv) | — | Replaces Platt's logistic with a 3-parameter Beta-family link tailored to scores already in [0,1] | Strictly more flexible than Platt while remaining identifiable; avoids the bias Platt has on already-near-calibrated scores |
| Beyond temperature scaling: Obtaining well-calibrated multiclass probabilities with Dirichlet calibration | Kull et al. (2019) | NeurIPS 2019 | arXiv:1910.12656 | dirichletcal/dirichlet_python | Generalizes matrix/vector scaling via a Dirichlet-link parametric family | Provides full multiclass scaling parameterization with ODIR regularization to control overfitting on small calibration sets |

## A2. Post-hoc Calibration: Binning & Non-parametric Methods

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| Obtaining calibrated probability estimates from decision trees and naive Bayesian classifiers | Zadrozny & Elkan (2001) | ICML 2001 | (no arXiv) | — | Applies histogram binning and isotonic regression to recalibrate tree and NB outputs | First systematic use of isotonic regression as a post-hoc calibrator for ML classifiers |
| Transforming classifier scores into accurate multiclass probability estimates | Zadrozny & Elkan (2002) | KDD 2002 | DOI:10.1145/775047.775151 | — | Extends Platt and isotonic recalibration to the multiclass setting via one-vs-rest decomposition | Established multiclass post-hoc calibration recipe that remained the default for decades |
| Predicting Good Probabilities with Supervised Learning | Niculescu-Mizil & Caruana (2005) | ICML 2005 | (no arXiv) | — | Empirical comparison of Platt, isotonic and raw scores across 10 classifier families | Definitive empirical evidence that boosted trees / SVMs need calibration while bagged trees do not |
| Mix-n-Match: Ensemble and Compositional Methods for Uncertainty Calibration in Deep Learning | Zhang et al. (2020) | ICML 2020 | arXiv:2003.07329 | zhang64-llnl/Mix-n-Match-Calibration | Mixes parametric (temperature) and non-parametric (histogram) calibrators in an ensemble | Compositional calibrator combining accuracy-preserving and data-efficient binning beats either component alone |
| Calibration of Neural Networks using Splines | Gupta et al. (2021) | ICLR 2021 | arXiv:2006.12800 | kartikgupta-at-anu/spline-calibration | Recalibrates by fitting a smoothing spline to the empirical reliability curve | Binning-free non-parametric calibrator that avoids the bias-variance tradeoff of histogram methods |
| Verified Uncertainty Calibration | Kumar et al. (2019) | NeurIPS 2019 | arXiv:1909.10155 | p-lambda/verified_calibration | Combines scaling with binning ("scaling-binning") and gives sample-complexity guarantees | First post-hoc calibrator with provably low calibration error and a debiased ECE estimator |

## A3. Calibration During Training

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| When Does Label Smoothing Help? | Müller et al. (2019) | NeurIPS 2019 | arXiv:1906.02629 | — | Analyzes the effect of label smoothing on representations and downstream calibration | Shows label smoothing implicitly calibrates by penalizing overconfident logits, but harms knowledge distillation |
| On Mixup Training: Improved Calibration and Predictive Uncertainty for Deep Neural Networks | Thulasidasan et al. (2019) | NeurIPS 2019 | arXiv:1905.11001 | paganpasta/onmixup | Empirically studies the calibration side-effect of mixup augmentation | Demonstrates mixup yields better-calibrated and more OOD-robust nets without an explicit calibration loss |

## A4. Calibration Metrics & Reliability Diagrams

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| Verification of Forecasts Expressed in Terms of Probability | Brier (1950) | Monthly Weather Review | DOI:10.1175/1520-0493(1950)078<0001:VOFEIT>2.0.CO;2 | — | Introduces the squared-error scoring rule for probabilistic weather forecasts | The original Brier score — a strictly proper scoring rule still used as the default calibration-aware accuracy metric |
| The Comparison and Evaluation of Forecasters | DeGroot & Fienberg (1983) | The Statistician (JSTOR) | (no arXiv) | — | Decomposes proper scoring rules into calibration plus refinement components | Foundational decomposition showing calibration and sharpness are orthogonal goals |
| Strictly Proper Scoring Rules, Prediction, and Estimation | Gneiting & Raftery (2007) | JASA | DOI:10.1198/016214506000001437 | — | Unified treatment of strictly proper scoring rules for probabilistic prediction | Reference modern statement of the proper-scoring-rule theory underlying ECE/Brier/log-loss |
| Obtaining Well Calibrated Probabilities Using Bayesian Binning | Naeini et al. (2015) | AAAI 2015 | (no arXiv) | — | Bayesian model averaging over equal-frequency binning schemes (BBQ) | Introduces ECE in its modern AAAI form and BBQ as a Bayesian binning calibrator |
| Measuring Calibration in Deep Learning | Nixon et al. (2019) | CVPR 2019 Workshop | arXiv:1904.01685 | — | Critical review of ECE estimators; proposes adaptive-binning ACE | Shows equal-width-bin ECE is unreliable for deep nets and recommends adaptive-bin variants |
| Mitigating Bias in Calibration Error Estimation | Roelofs et al. (2022) | AISTATS 2022 | arXiv:2012.08668 | google-research/google-research | Quantifies the upward bias of plug-in ECE estimators with finite samples | Proposes debiased estimators with reduced sample bias and clarifies which ECE variants to use when |
| Distribution-free binary classification: prediction sets, confidence intervals and calibration | Gupta et al. (2020) | NeurIPS 2020 | arXiv:2006.10564 | aigen/df-posthoc-calibration | Distribution-free guarantees for calibration, confidence intervals and prediction sets | Unifies post-hoc calibration with conformal-style coverage guarantees in the binary case |
| Evaluating model calibration in classification | Vaicenavicius et al. (2019) | AISTATS 2019 | arXiv:1902.06977 | uu-sml/calibration | Statistical hypothesis-testing framework for calibration evaluation | Provides asymptotic tests for calibration and characterizes ECE estimator inconsistency |
| Calibration tests in multi-class classification: A unifying framework | Widmann et al. (2019) | NeurIPS 2019 | arXiv:1910.11385 | devmotion/CalibrationTests.jl | Kernel-based calibration tests for the full multiclass simplex | First consistent calibration test that uses the entire predicted distribution rather than top-label only |
| Pitfalls of In-Domain Uncertainty Estimation and Ensembling in Deep Learning | Ashukha et al. (2020) | ICLR 2020 | arXiv:2002.06470 | bayesgroup/pytorch-ensembles | Empirical audit of UQ methods with calibrated-test-log-likelihood | Argues most UQ comparisons are confounded by uncalibrated baselines; standardizes evaluation under temperature scaling |

# Time-series Anomaly Detection — Toolkits & Surveys

The end-to-end detection toolkit plus the 2022 PVLDB survey that re-ran the field under a controlled protocol and reranked the detectors.

## A3. Detector toolkits

- **TODS (Time-series Outlier Detection System)** — Lai et al. (AAAI 2021 demo).
  - **Source:** https://arxiv.org/abs/2009.09822
  - **Code:** https://github.com/datamllab/tods
  - **Mechanism:** Automated outlier detection covering point, contextual, and collective anomaly types under one API. Includes data preparation, feature extraction, detection algorithms, and ensembling, with AutoML-style hyperparameter search.
  - **Result:** First end-to-end TS-OD toolkit shipping a consistent interface across the detector taxonomy; widely adopted as a teaching baseline.
  - **Status:** Verified.

## A4. Surveys / methodology critiques

- **Anomaly Detection in Time Series: A Comprehensive Evaluation (TimeEval)** — Schmidl, Wenig, Papenbrock (PVLDB 2022).
  - **Source:** https://arxiv.org/abs/2206.14948
  - **Code:** https://github.com/TimeEval/TimeEval
  - **Mechanism:** Head-to-head evaluation of 71 anomaly detectors on 967 datasets using a unified TimeEval framework. Strict preprocessing, identical hyperparameter-tuning budget per detector, identical scoring.
  - **Result:** Demonstrates that published per-detector numbers across the literature are not directly comparable; reranks the field under a controlled protocol and identifies which detectors generalize across data types.
  - **Status:** Verified.

---

Total entries: 2

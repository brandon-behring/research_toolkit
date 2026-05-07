# Time-series Anomaly Detection — Benchmarks & Datasets

Canonical streaming benchmark plus the NASA spacecraft telemetry datasets that became the de-facto reference corpora for multivariate detector evaluation.

## A1. Streaming benchmarks

- **Numenta Anomaly Benchmark (NAB)** — Ahmad, Lavin, Purdy, Agha (Neurocomputing 2017).
  - **Source:** https://arxiv.org/abs/1610.07677
  - **Code:** https://github.com/numenta/NAB
  - **Mechanism:** 58 real-world streams from server, IoT, and traffic domains; each has labeled anomaly windows. Defines an early-detection scoring profile (linear, reward-low-FP, reward-low-FN) instead of binary ROC.
  - **Result:** First open benchmark targeting *streaming* TS anomaly detection. Made the streaming-vs-batch evaluation distinction concrete and remains the most-cited streaming benchmark.
  - **Status:** Verified.

## A2. Telemetry datasets

- **MSL + SMAP (telemanom)** — Hundman, Constantinou, Laporte, Colwell, Soderstrom (KDD 2018).
  - **Source:** https://arxiv.org/abs/1802.04431
  - **Code:** https://github.com/khundman/telemanom
  - **Mechanism:** Releases the Mars Science Laboratory (27 channels) and Soil Moisture Active Passive (55 channels) NASA spacecraft telemetry corpora with labeled anomaly windows. Pairs an LSTM-based predictor with non-parametric dynamic thresholding.
  - **Result:** MSL + SMAP became the canonical reference datasets for *multivariate* TS anomaly detection — most subsequent detector papers report numbers on these two corpora.
  - **Status:** Verified.

---

Total entries: 2

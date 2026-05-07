# Time-series anomaly detection — Benchmarks & Datasets

Coverage of the canonical streaming benchmark plus the NASA spacecraft telemetry
datasets used as a de-facto reference dataset across the field.

## A1. Streaming benchmarks

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| Unsupervised real-time anomaly detection for streaming data | Ahmad, Lavin, Purdy, Agha (2017) | Neurocomputing | arXiv:1610.07677 | numenta/NAB | The Numenta Anomaly Benchmark (NAB): 58 labeled streams from real domains | First open benchmark targeting **streaming** anomaly detection with explicit early-detection scoring, not batch ROC |

## A2. Telemetry datasets

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| Detecting Spacecraft Anomalies Using LSTMs and Nonparametric Dynamic Thresholding | Hundman, Constantinou, Laporte, Colwell, Soderstrom (2018) | KDD 2018 | arXiv:1802.04431 | khundman/telemanom | Releases MSL (Mars Science Laboratory) and SMAP (Soil Moisture Active Passive) labeled telemetry datasets | The MSL + SMAP corpora became the most-cited reference datasets for **multivariate** time-series anomaly detection |

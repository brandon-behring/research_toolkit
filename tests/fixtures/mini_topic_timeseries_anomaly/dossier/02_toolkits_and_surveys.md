# Time-series anomaly detection — Toolkits & Surveys

The toolkit that operationalizes detector evaluation, plus the 2022 survey that
re-ran the field under controlled conditions and reranked the detectors.

## A3. Detector toolkits

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| TODS: An Automated Time Series Outlier Detection System | Lai, Zha, Wang, Xu, Zhao, Kumar, Chen, Zumkhawaka, Wan, Martinez, Hu (2021) | AAAI 2021 demo | arXiv:2009.09822 | datamllab/tods | Automated outlier detection across point, contextual, and collective anomalies with AutoML-style hyperparameter search | First **end-to-end** TS-OD toolkit covering data-prep / feature-extraction / detection / ensembling under one API |

## A4. Surveys / methodology critiques

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| Anomaly Detection in Time Series: A Comprehensive Evaluation | Schmidl, Wenig, Papenbrock (2022) | PVLDB 2022 | arXiv:2206.14948 | TimeEval/TimeEval | Head-to-head evaluation of 71 detectors on 967 datasets using a unified TimeEval framework | Demonstrates **published per-detector numbers are not comparable** across papers; reranks the field under a controlled protocol |

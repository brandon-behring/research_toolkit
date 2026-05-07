# Research Plan: Time-series Anomaly Detection Benchmarks

A 3–5 paper mini-dossier covering the canonical benchmarks, datasets, and toolkits for
unsupervised anomaly detection on temporal data, plus one survey establishing the
taxonomy of evaluation methodology. Deliberately scoped narrow — not exhaustive
coverage; this is the toolkit's "new use case" smoke test, not a real research artifact.

## Sub-areas

- A1. Streaming benchmarks
  - Source types: arXiv preprint, conference proceedings, GitHub
  - Notes: Earliest open benchmarks for live telemetry / IoT streams
- A2. Telemetry datasets
  - Source types: arXiv, conference proceedings
  - Notes: Real-world labeled spacecraft / industrial sensor datasets
- A3. Detector toolkits
  - Source types: arXiv, GitHub library, JMLR-style paper
  - Notes: Open-source libraries that ship N detection algorithms with a
    consistent API; not single-detector papers
- A4. Surveys / methodology critiques
  - Source types: VLDB / PVLDB, arXiv
  - Notes: Comparative studies that re-rank detectors under controlled protocols;
    needed to interpret per-benchmark numbers honestly

## Out-of-scope

- Supervised anomaly classification (the field is dominated by unsupervised /
  semi-supervised methods; supervised work is small and orthogonal)
- Synthetic-only benchmarks (NAB / MSL / SMAP all use real data; synthetic-only
  benchmarks tend to overstate detector performance)
- Vision-style outlier detection (CIFAR-10 outliers, etc.) — different problem class
- General time-series forecasting without an anomaly framing

## Claim family taxonomy

- benchmark
- dataset
- toolkit
- survey

## Known landmark papers

- ahmad2017nab: Numenta Anomaly Benchmark — earliest streaming benchmark
- hundman2018detecting: MSL + SMAP datasets — NASA spacecraft telemetry
- lai2021tods: TODS toolkit — automated outlier detection
- schmidl2022anomaly: PVLDB survey — first head-to-head detector comparison

These four are pre-known; `/research-gather` should not need to re-discover them
via WebSearch. Surfacing additional contemporary work (TranAD, TimeGPT, etc.) is
optional but in-scope.

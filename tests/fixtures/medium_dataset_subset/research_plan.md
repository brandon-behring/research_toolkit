# Research Plan: Time-Series Anomaly Datasets (Medium Fixture)

A scoped subset of the time-series anomaly detection dataset dossier. Used as a v1.6 schema reference and test fixture (~12 entries).

## Sub-areas

- A1. Streaming benchmarks
  - Source types: github, huggingface
  - Notes: NAB-shaped streaming anomaly with labeled timestamps.
- A2. Multivariate sensor benchmarks
  - Source types: github, zenodo
  - Notes: spacecraft / industrial / environmental sensor multivariate.
- A3. Classification / clustering archives
  - Source types: uci
  - Notes: UCR-style time-series archives that contain anomaly subsets.
- A4. Cloud / public datasets
  - Source types: aws_open_data
  - Notes: NYC TLC and similar public-cloud-hosted time-series datasets.

## Out-of-scope

- Forecasting-only datasets (no anomaly labels).
- Synthetic-only generators without a published benchmark.
- Datasets with non-redistributable licenses requiring special agreement.

## Claim family taxonomy

- time_series
- tabular
- multimodal

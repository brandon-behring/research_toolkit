# Time-series Anomaly Detection — Research Synthesis

<!-- AGENT-INDEX: this folder is a self-contained reference for time-series anomaly detection benchmarks. Read this README first. -->

**Purpose:** Mini-synthesis of canonical time-series anomaly detection benchmarks, datasets, toolkits, and surveys. Designed for both human readers and future LLM agents grounding reasoning in this literature.
**Self-containedness guarantee:** this folder has no hard dependence on sibling files. Move it elsewhere and it still works.
**Scope:** Unsupervised / semi-supervised anomaly detection on temporal data, 2017–2022.
**Coverage:** 4 entries across 2 topic files; structured 5-bullet entries (Source / Code / Mechanism / Result / Status).
**Last updated:** 2026-05-06.

## ⚠️ Scope boundary

This is a **mini fixture** for the research_toolkit's TDD harness, not a research artifact intended for external use. It demonstrates the canonical 5-bullet schema on a deliberately narrow domain so the validators have a clean positive case.

## How this is organized

| File | Topic | When to read |
|---|---|---|
| `01_benchmarks_and_datasets.md` | NAB streaming benchmark + MSL/SMAP telemetry datasets | Picking an evaluation harness |
| `02_toolkits_and_surveys.md` | TODS toolkit + Schmidl 2022 PVLDB survey | Choosing a detector library or interpreting prior numbers |

## Lookup recipes

- **"What's the canonical streaming TS-anomaly benchmark?"** → `01_benchmarks_and_datasets.md` § A1 (NAB, Ahmad et al. 2017).
- **"What multivariate datasets do most detector papers use?"** → `01_benchmarks_and_datasets.md` § A2 (MSL + SMAP, Hundman et al. 2018).
- **"What end-to-end TS outlier detection library should I try?"** → `02_toolkits_and_surveys.md` § A3 (TODS, Lai et al. 2021).
- **"Why don't published per-detector numbers agree?"** → `02_toolkits_and_surveys.md` § A4 (Schmidl et al. 2022 PVLDB survey).

## Glossary

- **NAB**: Numenta Anomaly Benchmark — 58 labeled streaming sequences with early-detection scoring.
- **MSL**: Mars Science Laboratory rover telemetry corpus.
- **SMAP**: Soil Moisture Active Passive satellite telemetry corpus.
- **TODS**: Time-series Outlier Detection System (toolkit).
- **TimeEval**: Schmidl 2022 evaluation framework that reranks detectors under a unified protocol.

## Verification & limits

- All 4 citations resolved as of 2026-05-06 against arXiv abstracts.
- This is a mini fixture; no independent audit rounds have been run.

## Attribution

Synthesized from a research dossier maintained by the research_toolkit. URLs link to arXiv primary sources.

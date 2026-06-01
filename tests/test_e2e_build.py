"""Full BUILDER-pipeline end-to-end integration test.

The sibling ``tests/test_pipeline_e2e.py`` is a validator-CHAIN smoke test: it
runs every validator over the committed medium fixture. It does NOT exercise the
committed BUILDER scripts. This module fills that gap — it drives the real,
committed v2.6 pipeline scripts in sequence on a TINY self-contained fixture and
asserts the whole chain produces a trustworthy, fully-validated strict-live
dossier from scratch:

    assemble_artifacts  -> bib/evidence/cache_manifest/gather_trace ledgers
    build_claim_graph   -> claim_graph.jsonl
    render_agent_index  -> pre_selection_manifest.yml + agent_index/
    verify_citations    -> citation_audit_report.md (asserts 100% substring pass)
    build_dashboard     -> dashboard.md (+ validators/freshness)
    research_kb_export  -> <slug>.jsonl (research-kb envelope)

The fixture is a hand-rolled content-addressed cache built under ``tmp_path``:
for each source we write the SAME bytes to ``blobs/sha256/<sha>`` (the raw
snapshot the cache_manifest hashes) and ``text/sha256/<sha>.txt`` (the extracted
text the anchors index), plus a valid ``metadata/sha256/<sha>.json`` — so the
sha256 the assembler records for the blob is self-consistent and the excerpt
anchors resolve against the text. No ``unittest.mock``: the scripts are driven
through their real ``main()`` entry points and every artifact is checked with its
real validator.

This is the regression backstop proving the committed pipeline still builds a
trustworthy dossier end to end — display==evidence, every evidence_id resolvable,
every excerpt_anchor re-verifying, citation 100%.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import assemble_artifacts as aa  # type: ignore[import-not-found]
import build_claim_graph as bcg  # type: ignore[import-not-found]
import build_dashboard as bd  # type: ignore[import-not-found]
import render_agent_index as rai  # type: ignore[import-not-found]
import research_kb_export as rke  # type: ignore[import-not-found]
import verify_citations as vc  # type: ignore[import-not-found]
from validators import (  # type: ignore[import-not-found]
    agent_index,
    agent_index_display,
    bib_ledger,
    cache_manifest,
    claim_graph,
    cross_stage,
    evidence_ledger,
    freshness,
    gather_trace,
    pre_selection_manifest,
    research_kb_export,
    v2_common,
)

from datetime import date

# A "today" recent enough that no entry is content-age-stale relative to its
# published_online dates below (freshness content-age WARNING is tier-relative;
# we keep all dates inside the same year to stay well clear).
TODAY = "2026-05-30"
TOPIC = "e2e_demo"


# ---------- Tiny content-addressed cache fixture ----------

# Three cached "sources." Each excerpt (and each mechanism_display override) is a
# verbatim substring of its body, so the anchors + the display guard pass.
DOC_A = (
    "Header for doc A.\n"
    "We introduce a calibration method that rescales predicted probabilities so "
    "they match empirical frequencies on held-out data.\n"
    "temperature scaling is a single-parameter post-hoc calibration method\n"
    "Footer A.\n"
)
DOC_B = (
    "Doc B preamble.\n"
    "This work proposes a reliability diagram estimator with debiased binning for "
    "evaluating probabilistic forecasts.\n"
    "Footer B.\n"
)
DOC_C = (
    "Doc C masthead.\n"
    "We benchmark conformal prediction sets and report marginal coverage close to "
    "the nominal level across distribution shifts.\n"
    "Footer C.\n"
)

EXCERPT_A = (
    "We introduce a calibration method that rescales predicted probabilities so "
    "they match empirical frequencies on held-out data."
)
EXCERPT_B = (
    "This work proposes a reliability diagram estimator with debiased binning for "
    "evaluating probabilistic forecasts."
)
EXCERPT_C = (
    "We benchmark conformal prediction sets and report marginal coverage close to "
    "the nominal level across distribution shifts."
)
# A cleaner DISPLAY sentence for source A that is still a verbatim raw-byte
# substring of DOC_A (exercises the display!=evidence override through the
# renderer + the audit-time agent_index_display validator).
DISPLAY_A = "temperature scaling is a single-parameter post-hoc calibration method"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_cache(cache_root: Path) -> dict[str, str]:
    """Write each DOC to blobs/ + text/ + metadata/; return {label: sha}.

    The raw blob and the extracted text are intentionally identical bytes so the
    sha256 the assembler records for the blob is the sha256 of the text the
    anchors index — a self-consistent toy cache the real validators accept.
    """
    blobs = cache_root / "blobs" / "sha256"
    text = cache_root / "text" / "sha256"
    meta = cache_root / "metadata" / "sha256"
    for d in (blobs, text, meta):
        d.mkdir(parents=True, exist_ok=True)
    shas: dict[str, str] = {}
    for label, body in (("a", DOC_A), ("b", DOC_B), ("c", DOC_C)):
        sha = _sha(body)
        shas[label] = sha
        (blobs / sha).write_text(body, encoding="utf-8")
        (text / f"{sha}.txt").write_text(body, encoding="utf-8")
        (meta / f"{sha}.json").write_text(
            json.dumps({"sha256": sha, "topic": TOPIC, "fetched_at": TODAY}),
            encoding="utf-8",
        )
    return shas


def _sources_doc(shas: dict[str, str], cache_root: Path) -> dict[str, Any]:
    """The sources-JSON consumed by BOTH assemble_artifacts and render_agent_index.

    Uses non-arXiv primary_urls so cross_stage's arxiv-id orphan/stale checks
    have empty sets on both sides (the dossier stays clean even under --strict).
    """
    return {
        "topic": TOPIC,
        "today": TODAY,
        "cache_root": str(cache_root),
        "sources": [
            {
                "n": "0001",
                "bibkey": "guo2017calibration",
                "primary_url": "https://example.org/guo2017",
                "title": "On Calibration of Modern Networks",
                "authors": "Guo et al. (2017)",
                "venue": "ICML",
                "claim_family": "calibration_method",
                "sub_area": "post_hoc_calibration",
                "sha": shas["a"],
                "excerpt": EXCERPT_A,
                "code_url": "https://github.com/example/calibration",
                "published_online": "2017-06-15",
            },
            {
                "n": "0002",
                "bibkey": "nixon2019reliability",
                "primary_url": "https://example.org/nixon2019",
                "title": "Measuring Calibration in Deep Learning",
                "authors": "Nixon et al. (2019)",
                "venue": "CVPRW",
                "claim_family": "calibration_metric",
                "sub_area": "calibration_metrics",
                "sha": shas["b"],
                "excerpt": EXCERPT_B,
                # no code_url -> Status notes "(no widely-known repo)"
                # no published_online -> Published online line absent
            },
            {
                "n": "0003",
                "bibkey": "angelopoulos2021conformal",
                "primary_url": "https://example.org/angelopoulos2021",
                "title": "A Gentle Introduction to Conformal Prediction",
                "authors": "Angelopoulos and Bates (2021)",
                "venue": "arXiv",
                "claim_family": "uncertainty_set",
                "sub_area": "conformal_prediction",
                "sha": shas["c"],
                "excerpt": EXCERPT_C,
                "published_online": "2021-07-15",
            },
        ],
        "rejects": [
            {
                "fetch_id": "fetch_reject_blog",
                "sub_area": "post_hoc_calibration",
                "query": "calibration blog post overview",
                "source_url": "https://example.org/some-blog",
                "is_relevant": True,
                "is_supported": "none",
                "is_useful": 2,
                "decision": "reject",
                "reason": "Secondary blog; superseded by the primary ICML paper.",
            }
        ],
    }


def _render_config() -> dict[str, Any]:
    """render_config.yml: per-topic DATA the renderer pairs with sources.json."""
    return {
        "schema_version": 1,
        "topic": TOPIC,
        "today": TODAY,
        "title": "Calibration & Uncertainty (e2e)",
        "blurb": "Tiny end-to-end fixture dossier on calibration and uncertainty sets.",
        "families": [
            {
                "file": "01_calibration_methods.md",
                "claim_family": "calibration_method",
                "heading": "Calibration methods",
            },
            {
                "file": "02_calibration_metrics.md",
                "claim_family": "calibration_metric",
                "heading": "Calibration metrics",
            },
            {
                "file": "03_uncertainty_sets.md",
                "claim_family": "uncertainty_set",
                "heading": "Uncertainty sets",
            },
        ],
        "results": {
            "guo2017calibration": "Temperature scaling fixes the overconfidence of modern networks.",
            "nixon2019reliability": "Debiased binning yields a less biased reliability-diagram estimate.",
            "angelopoulos2021conformal": "Conformal sets give finite-sample marginal coverage guarantees.",
        },
        "glossary": [
            {"term": "calibration", "definition": "Agreement between predicted probabilities and empirical frequencies."},
            {"term": "coverage", "definition": "Fraction of true labels contained in a prediction set."},
        ],
        "lookup_recipes": [
            {"question": "How to fix overconfidence?", "file": "01_calibration_methods.md", "ref": "guo2017calibration"},
        ],
        "scope_in": "post-hoc calibration, calibration metrics, conformal prediction sets.",
        "scope_out": "training-time calibration; Bayesian deep learning.",
        "readme_scope": "Focuses on post-hoc calibration and distribution-free uncertainty sets.",
        # display != evidence: a cleaner Mechanism sentence for source A that is
        # still a verbatim substring of DOC_A (guard-verified at write time, then
        # re-checked at audit time by validators/agent_index_display.py).
        "mechanism_display": {"guo2017calibration": DISPLAY_A},
    }


def _build_fixture(tmp_path: Path) -> tuple[Path, Path, Path, dict[str, str]]:
    """Write cache + sources.json + render_config.yml; return their paths + shas."""
    cache_root = tmp_path / "cache"
    shas = _write_cache(cache_root)
    sources_path = tmp_path / "sources.json"
    sources_path.write_text(
        json.dumps(_sources_doc(shas, cache_root)), encoding="utf-8"
    )
    config_path = tmp_path / "render_config.yml"
    config_path.write_text(
        yaml.safe_dump(_render_config(), sort_keys=False), encoding="utf-8"
    )
    return cache_root, sources_path, config_path, shas


# ---------- The end-to-end build ----------


def test_e2e_builder_pipeline_builds_trustworthy_dossier(tmp_path: Path) -> None:
    """Drive the whole committed builder pipeline from scratch; assert it is green.

    Runs assemble -> claim-graph -> render -> citation-audit -> dashboard ->
    export in order, validating every artifact with its real validator and
    checking the cross-stage integrity contract (display==evidence, resolvable
    evidence_ids, re-verifying anchors, 100% citation). One big test so the
    whole chain shares one fixture build and a single failure points at the
    first broken stage.
    """
    cache_root, sources_path, config_path, shas = _build_fixture(tmp_path)
    project = tmp_path / "project"
    project.mkdir(parents=True, exist_ok=True)

    # --- Stage 1: assemble_artifacts -> the four gather ledgers ---
    rc = aa.main([str(sources_path), str(project)])
    assert rc == 0
    bib_path = project / "bib_ledger.yml"
    evidence_path = project / "evidence_ledger.yml"
    cache_path = project / "cache_manifest.yml"
    trace_path = project / "gather_trace.yml"
    for p in (bib_path, evidence_path, cache_path, trace_path):
        assert p.exists(), f"assemble did not write {p.name}"

    assert bib_ledger.validate(bib_path) == []
    assert evidence_ledger.validate(evidence_path) == []
    assert cache_manifest.validate(cache_path) == []
    assert gather_trace.validate(trace_path) == []

    # The reject is carried into gather_trace alongside the 3 accepts.
    trace = yaml.safe_load(trace_path.read_text(encoding="utf-8"))
    decisions = [f.get("decision") for f in trace["fetches"]]
    assert decisions.count("accept") == 3
    assert decisions.count("reject") == 1

    # --- Stage 2: build_claim_graph -> claim_graph.jsonl ---
    # build_claim_graph.main consumes argv[1:] (argv[0] is the prog name).
    rc = bcg.main(["build_claim_graph", str(project)])
    assert rc == 0
    cg_path = project / "claim_graph.jsonl"
    assert cg_path.exists()
    assert claim_graph.validate(cg_path) == []

    # --- Stage 3: render_agent_index -> pre_selection_manifest + agent_index/ ---
    rc = rai.main([str(sources_path), str(project), "--config", str(config_path)])
    assert rc == 0
    psm_path = project / "pre_selection_manifest.yml"
    assert psm_path.exists()
    assert pre_selection_manifest.validate(psm_path) == []
    assert agent_index.validate(project / "agent_index") == []
    # The new v2.6 display-vs-evidence audit validator (write-time guard's
    # audit-time half): every rendered Mechanism sentence is a cache substring.
    assert agent_index_display.validate(project) == []
    # cross_stage runs the whole-project integrity check INCLUDING the display
    # audit. --strict (no warnings tolerated) must be clean for a from-scratch
    # dossier built by the committed pipeline.
    assert cross_stage.validate(project) == []
    assert cross_stage.validate(project, strict=True) == []

    # The display override surfaced for source A; the anchored excerpt in the
    # manifest is unchanged (display != evidence).
    fam1 = (project / "agent_index" / "01_calibration_methods.md").read_text(
        encoding="utf-8"
    )
    assert f"**Mechanism:** {DISPLAY_A}" in fam1
    psm = yaml.safe_load(psm_path.read_text(encoding="utf-8"))
    sel_a = next(
        s for s in psm["selections"] if s["selection_id"] == "sel_guo2017calibration"
    )
    assert sel_a["span"]["excerpt"] == EXCERPT_A

    # --- Stage 4: verify_citations -> 100% substring pass on the fixture ---
    # verify_citations.main consumes argv[1:]; run with --json to get metrics.
    rc = vc.main(
        ["verify_citations", str(project), "--today", TODAY, "--json"]
    )
    assert rc == 0  # exit 0 == no substring failures
    assert (project / "citation_audit_report.md").exists()
    audit = vc.audit(project)
    assert audit["substring_attempt"] == 3
    assert audit["substring_pass"] == 3  # 100%
    assert audit["substring_failures"] == []

    # --- Stage 5: build_dashboard -> dashboard.md (+ freshness validator) ---
    rc = bd.main(["build_dashboard", str(project), "--today", TODAY])
    assert rc == 0
    dash_path = project / "dashboard.md"
    assert dash_path.exists()
    dash = dash_path.read_text(encoding="utf-8")
    assert "Trust State" in dash
    assert "stale blockers: 0" in dash
    assert "evidence coverage: 3/3 claims" in dash
    # freshness validator over the whole project (default mode; today pinned so
    # nothing reads as stale or content-age-old).
    assert freshness.validate(project, today=date.fromisoformat(TODAY)) == []

    # --- Stage 6: research_kb_export -> a valid research-kb JSONL envelope ---
    export_path = tmp_path / "export" / "e2e.jsonl"
    rc = rke.main(["research_kb_export", str(project), "--output", str(export_path)])
    assert rc == 0
    assert export_path.exists()
    assert research_kb_export.validate(export_path) == []

    # Every export record wraps a claim_graph record verbatim (lossless v2 envelope).
    cg_records = [
        json.loads(line) for line in cg_path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    export_records = [
        json.loads(line) for line in export_path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    assert len(export_records) == len(cg_records)
    for rec in export_records:
        assert rec["export_schema_version"] == 2
        assert rec["source_project"] == "project"
        assert rec["payload"] in cg_records  # verbatim payload

    # --- Whole-chain integrity assertions ---
    _assert_integrity(project, cache_root)


def _assert_integrity(project: Path, cache_root: Path) -> None:
    """Cross-artifact key integrity: every link resolves + every anchor verifies."""
    bib = yaml.safe_load((project / "bib_ledger.yml").read_text(encoding="utf-8"))
    evidence = yaml.safe_load(
        (project / "evidence_ledger.yml").read_text(encoding="utf-8")
    )
    cache = yaml.safe_load((project / "cache_manifest.yml").read_text(encoding="utf-8"))

    evidence_ids = {e["evidence_id"] for e in evidence["entries"]}
    cache_by_id = {c["cache_id"]: c for c in cache["entries"]}

    # Every bib entry's evidence_ids + cache_ids resolve.
    for entry in bib["entries"]:
        for ev_id in entry["evidence_ids"]:
            assert ev_id in evidence_ids, f"dangling evidence_id {ev_id}"
        for cid in entry["cache_ids"]:
            assert cid in cache_by_id, f"dangling cache_id {cid}"

    # Every evidence excerpt_anchor re-verifies byte-for-byte against the cache.
    cache_root_value = cache.get("cache_root")
    for ev in evidence["entries"]:
        for support in ev["supports"]:
            anchor = support["excerpt_anchor"]
            errs = v2_common.verify_excerpt_anchor(
                excerpt=ev["excerpt"],
                cache_id=anchor["cache_id"],
                text_path_offset=anchor["text_path_offset"],
                sha256_of_span=anchor["sha256_of_span"],
                cache_entries_by_id=cache_by_id,
                manifest_path=project / "cache_manifest.yml",
                cache_root=cache_root_value,
                loc=f"integrity[{ev['evidence_id']}]",
            )
            assert errs == [], errs

    # Every cache entry's recorded sha256 equals the sha of the on-disk blob,
    # and bytes matches — the content-addressed-cache guarantee end to end.
    for c in cache["entries"]:
        blob = cache_root / "blobs" / "sha256" / c["sha256"]
        raw = blob.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == c["sha256"]
        assert len(raw) == c["bytes"]

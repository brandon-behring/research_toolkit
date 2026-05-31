"""Tests for scripts/render_agent_index.py.

Exercises the parameterized agent-index renderer against a tiny hand-rolled fixture
(a fake content-addressed cache + a small sources.json + a small render_config.yml).
No unittest.mock — fixtures are built on disk under tmp_path.

Covers: pre_selection_manifest + agent_index written; selections pass
v2_common.verify_excerpt_anchor and re-hash to their recorded span sha; family
grouping; published_online surfaced only when present; and the display-verify guard
rejecting a mechanism_display override that is not a verbatim substring of the source.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import render_agent_index as rai  # type: ignore[import-not-found]
from validators import v2_common  # type: ignore[import-not-found]


# ---------- Fixture data ----------

# Two cached "sources". Each excerpt is a verbatim substring of its body.
DOC_A = (
    "Header line for doc A.\n"
    "Building on prior work, this article studies synthetic control methods "
    "for comparative case studies and discusses their advantages.\n"
    "the synthetic control is constructed as a weighted average of control units\n"
    "Footer A.\n"
)
DOC_B = (
    "Doc B preamble.\n"
    "We develop an augmented estimator that de-biases the synthetic-control fit "
    "with an outcome model when pre-treatment balance is infeasible.\n"
    "Footer B.\n"
)

EXCERPT_A = "this article studies synthetic control methods for comparative case studies"
EXCERPT_B = "We develop an augmented estimator that de-biases the synthetic-control fit"
# A clean display sentence that IS a verbatim raw-byte substring of DOC_A:
DISPLAY_A_OK = "the synthetic control is constructed as a weighted average of control units"
# Not a substring of DOC_A (the guard must reject this):
DISPLAY_A_BAD = "this sentence never appears verbatim in the cached source text"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_cache(cache_root: Path) -> tuple[str, str]:
    """Write DOC_A/DOC_B as content-addressed blobs; return their shas."""
    d = cache_root / "text" / "sha256"
    d.mkdir(parents=True, exist_ok=True)
    sha_a, sha_b = _sha(DOC_A), _sha(DOC_B)
    (d / f"{sha_a}.txt").write_text(DOC_A, encoding="utf-8")
    (d / f"{sha_b}.txt").write_text(DOC_B, encoding="utf-8")
    return sha_a, sha_b


def _sources(sha_a: str, sha_b: str, cache_root: Path) -> dict[str, Any]:
    return {
        "topic": "sc_demo",
        "today": "2026-05-31",
        "cache_root": str(cache_root),
        "sources": [
            {
                "n": "0001",
                "bibkey": "abadie2010synthetic",
                "primary_url": "https://example.org/abadie",
                "title": "Synthetic Control Methods",
                "authors": "Abadie et al. (2010)",
                "venue": "JASA",
                "claim_family": "synthetic_control",
                "sha": sha_a,
                "excerpt": EXCERPT_A,
                "published_online": "2010-06-01",
            },
            {
                "n": "0002",
                "bibkey": "benmichael2021augmented",
                "primary_url": "https://example.org/benmichael",
                "title": "The Augmented Synthetic Control Method",
                "authors": "Ben-Michael et al. (2021)",
                "venue": "JASA",
                "claim_family": "sc_extensions",
                "sha": sha_b,
                "excerpt": EXCERPT_B,
                # no published_online -> Published online line must be absent
            },
        ],
    }


def _config(mech_display: dict[str, str] | None = None) -> dict[str, Any]:
    cfg: dict[str, Any] = {
        "schema_version": 1,
        "topic": "sc_demo",
        "title": "Synthetic Control (test)",
        "blurb": "A tiny test dossier.",
        "families": [
            {"file": "01_synthetic_control.md", "claim_family": "synthetic_control", "heading": "Synthetic control"},
            {"file": "02_extensions.md", "claim_family": "sc_extensions", "heading": "Extensions"},
        ],
        "results": {
            "abadie2010synthetic": "Weighted donor pool reconstructs the counterfactual.",
            "benmichael2021augmented": "Outcome-model de-biasing of the SCM fit.",
        },
        "glossary": [{"term": "donor pool", "definition": "Untreated units eligible for weight."}],
        "lookup_recipes": [{"question": "How is SC built?", "file": "01_synthetic_control.md", "ref": "abadie2010synthetic"}],
        "scope_in": "synthetic control",
        "scope_out": "pure RCTs",
    }
    if mech_display is not None:
        cfg["mechanism_display"] = mech_display
    return cfg


def _setup(tmp_path: Path, mech_display: dict[str, str] | None = None) -> tuple[Path, Path, Path, str, str]:
    """Build cache + sources.json + render_config.yml; return their paths + the two shas."""
    cache_root = tmp_path / "cache"
    sha_a, sha_b = _write_cache(cache_root)
    sources_path = tmp_path / "sources.json"
    sources_path.write_text(json.dumps(_sources(sha_a, sha_b, cache_root)), encoding="utf-8")
    config_path = tmp_path / "render_config.yml"
    config_path.write_text(yaml.safe_dump(_config(mech_display), sort_keys=False), encoding="utf-8")
    project_dir = tmp_path / "proj"
    return sources_path, config_path, project_dir, sha_a, sha_b


# ---------- Happy path: files written ----------

def test_render_writes_manifest_and_agent_index(tmp_path):
    sources_path, config_path, project_dir, _, _ = _setup(tmp_path)
    rc = rai.main([str(sources_path), str(project_dir), "--config", str(config_path)])
    assert rc == 0
    assert (project_dir / "pre_selection_manifest.yml").exists()
    ai = project_dir / "agent_index"
    assert (ai / "00_overview.md").exists()
    assert (ai / "README.md").exists()
    assert (ai / "01_synthetic_control.md").exists()
    assert (ai / "02_extensions.md").exists()


def test_render_writes_schema_version_3_manifest(tmp_path):
    sources_path, config_path, project_dir, _, _ = _setup(tmp_path)
    rai.main([str(sources_path), str(project_dir), "--config", str(config_path)])
    man = yaml.safe_load((project_dir / "pre_selection_manifest.yml").read_text())
    assert man["schema_version"] == 3
    assert man["topic"] == "sc_demo"
    assert man["freshness_policy"] == "strict_live"
    assert len(man["selections"]) == 2
    s0 = man["selections"][0]
    assert s0["selection_id"] == "sel_abadie2010synthetic"
    assert s0["bullet_id"] == "B1"
    assert s0["atom_id"] == "claim_sc_demo_0001"
    assert s0["cache_id"].startswith("cache_")
    assert set(s0["span"]) == {"text_path_offset", "sha256_of_span", "excerpt"}


# ---------- Anchors are sound ----------

def test_render_selections_rehash_to_recorded_span_sha(tmp_path):
    sources_path, config_path, project_dir, sha_a, sha_b = _setup(tmp_path)
    cache_root = tmp_path / "cache"
    rai.main([str(sources_path), str(project_dir), "--config", str(config_path)])
    man = yaml.safe_load((project_dir / "pre_selection_manifest.yml").read_text())
    by_sha = {"abadie2010synthetic": sha_a, "benmichael2021augmented": sha_b}
    for sel in man["selections"]:
        bibkey = sel["selection_id"][len("sel_"):]
        blob = (cache_root / "text" / "sha256" / f"{by_sha[bibkey]}.txt").read_bytes()
        a, b = sel["span"]["text_path_offset"]
        assert hashlib.sha256(blob[a:b]).hexdigest() == sel["span"]["sha256_of_span"]


def test_render_selections_pass_verify_excerpt_anchor(tmp_path):
    sources_path, config_path, project_dir, sha_a, sha_b = _setup(tmp_path)
    cache_root = tmp_path / "cache"
    rai.main([str(sources_path), str(project_dir), "--config", str(config_path)])
    man = yaml.safe_load((project_dir / "pre_selection_manifest.yml").read_text())
    by_sha = {"abadie2010synthetic": sha_a, "benmichael2021augmented": sha_b}
    for sel in man["selections"]:
        bibkey = sel["selection_id"][len("sel_"):]
        blob_path = cache_root / "text" / "sha256" / f"{by_sha[bibkey]}.txt"
        cache_id = sel["cache_id"]
        errs = v2_common.verify_excerpt_anchor(
            excerpt=sel["span"]["excerpt"],
            cache_id=cache_id,
            text_path_offset=sel["span"]["text_path_offset"],
            sha256_of_span=sel["span"]["sha256_of_span"],
            cache_entries_by_id={cache_id: {"text_path": str(blob_path)}},
            manifest_path=blob_path.parent,
            loc=f"test[{bibkey}]",
            cache_root=None,
        )
        assert errs == [], errs


# ---------- Family grouping + published_online ----------

def test_render_groups_sources_into_family_files(tmp_path):
    sources_path, config_path, project_dir, _, _ = _setup(tmp_path)
    rai.main([str(sources_path), str(project_dir), "--config", str(config_path)])
    fam1 = (project_dir / "agent_index" / "01_synthetic_control.md").read_text()
    fam2 = (project_dir / "agent_index" / "02_extensions.md").read_text()
    # Each source lands only in its own claim_family file. The blocks carry the
    # source URL (unique per source); the bibkey itself is not printed.
    assert "https://example.org/abadie" in fam1 and "https://example.org/benmichael" not in fam1
    assert "https://example.org/benmichael" in fam2 and "https://example.org/abadie" not in fam2
    assert "Synthetic Control Methods" in fam1
    assert "The Augmented Synthetic Control Method" in fam2
    # Result bullet text comes from config.results
    assert "Weighted donor pool reconstructs the counterfactual." in fam1
    assert "Outcome-model de-biasing of the SCM fit." in fam2


def test_render_surfaces_published_online_only_when_present(tmp_path):
    sources_path, config_path, project_dir, _, _ = _setup(tmp_path)
    rai.main([str(sources_path), str(project_dir), "--config", str(config_path)])
    fam1 = (project_dir / "agent_index" / "01_synthetic_control.md").read_text()
    fam2 = (project_dir / "agent_index" / "02_extensions.md").read_text()
    assert "**Published online:** 2010-06-01" in fam1  # abadie has the date
    assert "Published online" not in fam2               # ben-michael does not


# ---------- Mechanism display override + guard ----------

def test_render_uses_mechanism_display_override_when_substring(tmp_path):
    sources_path, config_path, project_dir, _, _ = _setup(
        tmp_path, mech_display={"abadie2010synthetic": DISPLAY_A_OK}
    )
    rc = rai.main([str(sources_path), str(project_dir), "--config", str(config_path)])
    assert rc == 0
    fam1 = (project_dir / "agent_index" / "01_synthetic_control.md").read_text()
    assert f"**Mechanism:** {DISPLAY_A_OK}" in fam1
    # the anchored excerpt is unchanged in the manifest (display != evidence)
    man = yaml.safe_load((project_dir / "pre_selection_manifest.yml").read_text())
    s0 = next(s for s in man["selections"] if s["selection_id"] == "sel_abadie2010synthetic")
    assert s0["span"]["excerpt"] == EXCERPT_A


def test_render_rejects_mechanism_display_not_substring(tmp_path):
    sources_path, config_path, project_dir, _, _ = _setup(
        tmp_path, mech_display={"abadie2010synthetic": DISPLAY_A_BAD}
    )
    rc = rai.main([str(sources_path), str(project_dir), "--config", str(config_path)])
    assert rc == 1  # display-verify guard fires -> non-zero exit


def test_verify_display_raises_on_non_substring(tmp_path):
    cache_root = tmp_path / "cache"
    sha_a, _ = _write_cache(cache_root)
    with pytest.raises(rai.RenderError, match="DISPLAY ERROR"):
        rai.verify_display(cache_root, sha_a, DISPLAY_A_BAD, "abadie2010synthetic")
    # the OK display returns the sentence unchanged
    assert rai.verify_display(cache_root, sha_a, DISPLAY_A_OK, "abadie2010synthetic") == DISPLAY_A_OK


# ---------- Config / source error handling ----------

def test_render_rejects_missing_result_for_source(tmp_path):
    sources_path, config_path, project_dir, _, _ = _setup(tmp_path)
    cfg = _config()
    del cfg["results"]["benmichael2021augmented"]  # drop one source's Result
    config_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    rc = rai.main([str(sources_path), str(project_dir), "--config", str(config_path)])
    assert rc == 1


def test_render_rejects_missing_config_file(tmp_path):
    sources_path, _, project_dir, _, _ = _setup(tmp_path)
    rc = rai.main([str(sources_path), str(project_dir), "--config", str(tmp_path / "nope.yml")])
    assert rc == 2


def test_render_defaults_config_to_project_dir(tmp_path):
    sources_path, _, _, _, _ = _setup(tmp_path)
    # When --config is omitted, the renderer looks for render_config.yml inside the
    # project dir. Put one there (with an explicit cache_root) and render.
    project_dir = tmp_path / "proj_default"
    project_dir.mkdir(parents=True, exist_ok=True)
    cfg = _config()
    cfg["cache_root"] = str(tmp_path / "cache")
    (project_dir / "render_config.yml").write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    rc = rai.main([str(sources_path), str(project_dir)])  # no --config
    assert rc == 0
    assert (project_dir / "pre_selection_manifest.yml").exists()

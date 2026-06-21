"""``is_strict_live`` gate — out-of-scope v2/v3 variants are n/a, not failed.

A dossier that declares a v2/v3 ``schema_version`` but a *variant* ``freshness_policy`` (e.g.
the ``agent_youtube_talks`` whisper-transcription source pool, which uses
``strict_live_cache_index_anchor_on_cite`` on its bib and omits the field on its cache_manifest)
is deliberately OUT OF SCOPE for the v2 strict-live validators. Before this gate it was admitted
by ``is_v2_mapping`` (schema_version only) and then failed every strict-live field check
spuriously (~1918 errors). These tests pin the fix AND its precision: v1/legacy ledgers and
genuine strict-live dossiers are unaffected.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
import shutil

import yaml

from validators import bib_ledger, cache_manifest, freshness
from validators.v2_common import is_strict_live, is_v2_mapping

REPO_ROOT = Path(__file__).resolve().parent.parent
V3_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "v3_strict_live_demo"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "v2_strict_live_ai_agents"

# The literal freshness_policy value carried by the youtube_talks bib_ledger.
VARIANT_POLICY = "strict_live_cache_index_anchor_on_cite"


def _write_yaml(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def test_is_strict_live_predicate() -> None:
    assert is_strict_live({"schema_version": 2, "freshness_policy": "strict_live"})
    assert is_strict_live({"schema_version": 3, "freshness_policy": "strict_live"})
    # variant policy / missing policy / non-v2 schema → NOT strict-live (out of scope)
    assert not is_strict_live({"schema_version": 3, "freshness_policy": VARIANT_POLICY})
    assert not is_strict_live({"schema_version": 3})
    assert not is_strict_live({"schema_version": 1, "freshness_policy": "strict_live"})
    # is_v2_mapping is the weaker (schema-only) gate that wrongly admitted the variant
    assert is_v2_mapping({"schema_version": 3, "freshness_policy": VARIANT_POLICY})


def test_variant_bib_ledger_is_na(tmp_path: Path) -> None:
    project = tmp_path / "p"
    shutil.copytree(V3_FIXTURE, project)
    path = project / "bib_ledger.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["freshness_policy"] = VARIANT_POLICY
    _write_yaml(path, data)
    assert bib_ledger.validate(path) == []


def test_variant_cache_manifest_is_na(tmp_path: Path) -> None:
    project = tmp_path / "p"
    shutil.copytree(V3_FIXTURE, project)
    path = project / "cache_manifest.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data.pop("freshness_policy", None)  # youtube_talks omits it entirely
    _write_yaml(path, data)
    assert cache_manifest.validate(path) == []


def test_variant_freshness_is_na(tmp_path: Path) -> None:
    # A v3 bib with a variant policy → freshness returns n/a ([]): NOT the "no strict-live
    # ledger found" error, and NOT a "must be 'strict_live'" cascade.
    project = tmp_path / "p"
    shutil.copytree(V3_FIXTURE, project)
    bib = project / "bib_ledger.yml"
    data = yaml.safe_load(bib.read_text(encoding="utf-8"))
    data["freshness_policy"] = VARIANT_POLICY
    _write_yaml(bib, data)
    assert freshness.validate(project, strict=True, today=date(2026, 5, 19)) == []


def test_v1_non_v2_ledger_still_validated_not_na(tmp_path: Path) -> None:
    # Precision guard: a non-v2 (no schema_version) ledger must NOT hit the variant n/a path —
    # per-entry validation still runs, so a bad status is caught.
    project = tmp_path / "p"
    shutil.copytree(V3_FIXTURE, project)
    path = project / "bib_ledger.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data.pop("schema_version", None)  # → is_v2_mapping False (v1/legacy), not the variant case
    data["entries"][0]["status"] = "not_a_status"
    _write_yaml(path, data)
    errors = bib_ledger.validate(path)
    assert any("status" in e for e in errors), errors

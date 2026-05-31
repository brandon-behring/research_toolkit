"""Tests for scripts/assemble_artifacts.py.

Builds a tiny self-contained content-addressed cache (real sha256-named text +
blob files) under a temp cache_root plus a small sources mapping in the shape the
assembler consumes, then asserts the four emitted artifacts: presence, anchor
verification through ``validators.v2_common.verify_excerpt_anchor``,
published_online emission, and EXCERPT-FAILURE handling. No unittest.mock — the
cache is hand-rolled on disk and the default cache_root is exercised via
``monkeypatch`` of the parsed JSON.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from scripts.assemble_artifacts import cache_id_for, main
from validators.v2_common import verify_excerpt_anchor

# Cached text bodies. The excerpts in the sources below are byte-substrings here.
TEXT_BODIES = {
    "geo": (
        "Geo experiments randomize treatment at the level of geographic regions. "
        "We report the results of a series of large-scale field experiments that "
        "manipulate the advertising exposure of millions of users across markets."
    ),
    "scm": (
        "The synthetic control method constructs a weighted combination of control "
        "units that approximates the treated unit prior to intervention, yielding a "
        "credible counterfactual for the post-period."
    ),
    "power": (
        "Statistical power for a two-sample comparison depends on the effect size, "
        "the variance of the outcome, and the number of geographic units assigned "
        "to each arm of the experiment."
    ),
}


def _sha_of(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _build_cache(cache_root: Path) -> dict[str, str]:
    """Write text + blob files for each body; return body-key -> sha256 map.

    Mirrors the on-disk layout the assembler reads:
    ``<cache_root>/text/sha256/<sha>.txt`` and ``<cache_root>/blobs/sha256/<sha>``.
    """
    text_dir = cache_root / "text" / "sha256"
    blob_dir = cache_root / "blobs" / "sha256"
    text_dir.mkdir(parents=True, exist_ok=True)
    blob_dir.mkdir(parents=True, exist_ok=True)
    shas: dict[str, str] = {}
    for key, body in TEXT_BODIES.items():
        sha = _sha_of(body)
        shas[key] = sha
        (text_dir / f"{sha}.txt").write_text(body, encoding="utf-8")
        (blob_dir / sha).write_bytes(body.encode("utf-8"))
    return shas


def _sources_doc(shas: dict[str, str], cache_root: Path) -> dict[str, Any]:
    """A three-source + one-reject mapping in the assembler's input shape."""
    return {
        "topic": "test_topic",
        "today": "2026-05-30",
        "cache_root": str(cache_root),
        "sources": [
            {
                "n": "0001",
                "bibkey": "blake2015consumer",
                "primary_url": "https://example.com/blake2015",
                "title": "Consumer Heterogeneity and Paid Search Effectiveness",
                "authors": "Blake, Nosko & Tadelis (2015)",
                "venue": "Econometrica",
                "claim_family": "geo_experiment_design",
                "sha": shas["geo"],
                "sub_area": "B1. Geo experiments",
                "excerpt": (
                    "We report the results of a series of large-scale field experiments "
                    "that manipulate the advertising exposure of millions of users"
                ),
                "published_online": "2015-01-15",
            },
            {
                "n": "0002",
                "bibkey": "abadie2010synthetic",
                "primary_url": "https://example.com/abadie2010",
                "cache_source_url": "https://example.com/abadie2010.pdf",
                "title": "Synthetic Control Methods for Comparative Case Studies",
                "authors": "Abadie, Diamond & Hainmueller (2010)",
                "venue": "JASA",
                "claim_family": "synthetic_control_panel",
                "sha": shas["scm"],
                "sub_area": "B2. Synthetic control",
                "excerpt": (
                    "constructs a weighted combination of control units that "
                    "approximates the treated unit prior to intervention"
                ),
            },
            {
                "n": "0003",
                "bibkey": "cohen1988power",
                "primary_url": "https://example.com/cohen1988",
                "title": "Statistical Power Analysis for the Behavioral Sciences",
                "authors": "Cohen (1988)",
                "venue": "Routledge",
                "claim_family": "geo_experiment_design",
                "sha": shas["power"],
                "sub_area": "B1. Geo experiments",
                "excerpt": "the variance of the outcome, and the number of geographic units",
                "code_url": "https://example.com/cohen/code",
            },
        ],
        "rejects": [
            {
                "fetch_id": "fetch_rejected_example",
                "sub_area": "B1. Geo experiments",
                "query": "some superseded source",
                "source_url": "https://example.com/rejected",
                "is_relevant": True,
                "is_supported": "none",
                "is_useful": 2,
                "decision": "reject",
                "reason": "Superseded by an accepted source.",
            }
        ],
    }


def _write_sources(path: Path, doc: dict[str, Any]) -> None:
    path.write_text(json.dumps(doc), encoding="utf-8")


def _cache_entries_by_id(project_dir: Path) -> dict[str, dict[str, Any]]:
    cache = yaml.safe_load((project_dir / "cache_manifest.yml").read_text())
    return {e["cache_id"]: e for e in cache["entries"]}


def test_assemble_writes_four_artifacts(tmp_path: Path) -> None:
    cache_root = tmp_path / "cache"
    shas = _build_cache(cache_root)
    sources_path = tmp_path / "sources.json"
    _write_sources(sources_path, _sources_doc(shas, cache_root))
    project_dir = tmp_path / "project"

    rc = main([str(sources_path), str(project_dir)])
    assert rc == 0
    for name in (
        "bib_ledger.yml",
        "evidence_ledger.yml",
        "cache_manifest.yml",
        "gather_trace.yml",
    ):
        assert (project_dir / name).exists()


def test_assemble_every_anchor_verifies(tmp_path: Path) -> None:
    cache_root = tmp_path / "cache"
    shas = _build_cache(cache_root)
    sources_path = tmp_path / "sources.json"
    _write_sources(sources_path, _sources_doc(shas, cache_root))
    project_dir = tmp_path / "project"

    assert main([str(sources_path), str(project_dir)]) == 0

    evidence = yaml.safe_load((project_dir / "evidence_ledger.yml").read_text())
    cache_by_id = _cache_entries_by_id(project_dir)
    manifest_path = project_dir / "cache_manifest.yml"
    cache_root_value = yaml.safe_load(manifest_path.read_text())["cache_root"]

    entries = evidence["entries"]
    assert len(entries) == 3
    for ev in entries:
        support = ev["supports"][0]
        anchor = support["excerpt_anchor"]
        errors = verify_excerpt_anchor(
            excerpt=ev["excerpt"],
            cache_id=anchor["cache_id"],
            text_path_offset=anchor["text_path_offset"],
            sha256_of_span=anchor["sha256_of_span"],
            cache_entries_by_id=cache_by_id,
            manifest_path=manifest_path,
            loc=ev["evidence_id"],
            cache_root=cache_root_value,
        )
        assert errors == [], errors


def test_assemble_evidence_defaults_and_ids(tmp_path: Path) -> None:
    cache_root = tmp_path / "cache"
    shas = _build_cache(cache_root)
    sources_path = tmp_path / "sources.json"
    _write_sources(sources_path, _sources_doc(shas, cache_root))
    project_dir = tmp_path / "project"
    main([str(sources_path), str(project_dir)])

    evidence = yaml.safe_load((project_dir / "evidence_ledger.yml").read_text())
    assert evidence["schema_version"] == 3
    first = evidence["entries"][0]
    assert first["evidence_id"] == "ev_test_topic_0001"
    assert first["source_type"] == "paper"
    assert first["source_quality"] == "primary"
    assert first["rights_status"] == "public"
    support = first["supports"][0]
    assert support["claim_id"] == "claim_test_topic_0001"
    assert support["field_path"] == "bib_ledger.entries[blake2015consumer].abstract"
    assert support["evidence_role"] == "supports"
    assert support["evidence_role_strength"] == "full"
    assert support["extraction_method"] == "verbatim_match"
    assert support["link_confidence"] == 0.98
    assert support["excerpt_anchor"]["cache_id"] == cache_id_for(shas["geo"])

    cache = yaml.safe_load((project_dir / "cache_manifest.yml").read_text())
    assert cache["schema_version"] == 2
    first_cache = cache["entries"][0]
    assert first_cache["rights_status"] == "private_use"
    assert "stale_after_days" not in first_cache  # belongs to bib, not cache
    assert first_cache["restricted"] is False
    assert first_cache["extraction_status"] == "ok"

    bib = yaml.safe_load((project_dir / "bib_ledger.yml").read_text())
    first_bib = bib["entries"][0]
    assert first_bib["status"] == "verified"
    assert first_bib["freshness_tier"] == "active"
    assert first_bib["stale_after_days"] == 90
    assert first_bib["verification_method"] == "webfetch"
    assert first_bib["evidence_ids"] == ["ev_test_topic_0001"]
    assert first_bib["cache_ids"] == [cache_id_for(shas["geo"])]


def test_assemble_published_online_emitted_when_provided(tmp_path: Path) -> None:
    cache_root = tmp_path / "cache"
    shas = _build_cache(cache_root)
    sources_path = tmp_path / "sources.json"
    _write_sources(sources_path, _sources_doc(shas, cache_root))
    project_dir = tmp_path / "project"
    main([str(sources_path), str(project_dir)])

    bib = {e["bibkey"]: e for e in yaml.safe_load((project_dir / "bib_ledger.yml").read_text())["entries"]}
    cache = yaml.safe_load((project_dir / "cache_manifest.yml").read_text())["entries"]
    cache_by_cid = {c["cache_id"]: c for c in cache}

    # Source 1: explicit published_online -> emitted as the date.
    assert bib["blake2015consumer"]["published_online"] == "2015-01-15"
    assert cache_by_cid[cache_id_for(shas["geo"])]["published_online"] == "2015-01-15"

    # Source 2: no published_online (but has cache_source_url) -> the field is
    # NOT emitted; cache_source_url alone does not introduce a null. cache_source_url
    # is NOT a bib_ledger field (the scratch helper + shipped artifacts only carry
    # code_url + published_online as bib optionals); it only steers the cache
    # entry's source_url, matching vaver2011measuring / google2024meridian.
    assert "published_online" not in bib["abadie2010synthetic"]
    assert "cache_source_url" not in bib["abadie2010synthetic"]
    abadie_cache = cache_by_cid[cache_id_for(shas["scm"])]
    assert "published_online" not in abadie_cache
    # the cache entry's source_url falls back to cache_source_url for this source.
    assert abadie_cache["source_url"] == "https://example.com/abadie2010.pdf"


def test_assemble_published_online_omitted_when_absent(tmp_path: Path) -> None:
    cache_root = tmp_path / "cache"
    shas = _build_cache(cache_root)
    sources_path = tmp_path / "sources.json"
    _write_sources(sources_path, _sources_doc(shas, cache_root))
    project_dir = tmp_path / "project"
    main([str(sources_path), str(project_dir)])

    bib = {e["bibkey"]: e for e in yaml.safe_load((project_dir / "bib_ledger.yml").read_text())["entries"]}
    cache_by_cid = {c["cache_id"]: c for c in yaml.safe_load((project_dir / "cache_manifest.yml").read_text())["entries"]}

    # Source 3: neither published_online nor cache_source_url -> field omitted.
    assert "published_online" not in bib["cohen1988power"]
    assert "published_online" not in cache_by_cid[cache_id_for(shas["power"])]
    # but code_url IS carried through into bib.
    assert bib["cohen1988power"]["code_url"] == "https://example.com/cohen/code"


def test_assemble_gather_trace_accepts_and_rejects(tmp_path: Path) -> None:
    cache_root = tmp_path / "cache"
    shas = _build_cache(cache_root)
    sources_path = tmp_path / "sources.json"
    _write_sources(sources_path, _sources_doc(shas, cache_root))
    project_dir = tmp_path / "project"
    main([str(sources_path), str(project_dir)])

    trace = yaml.safe_load((project_dir / "gather_trace.yml").read_text())
    assert trace["schema_version"] == 3
    fetches = trace["fetches"]
    # 3 accepted + 1 reject.
    assert len(fetches) == 4
    accepts = [f for f in fetches if f["decision"] == "accept"]
    rejects = [f for f in fetches if f["decision"] == "reject"]
    assert len(accepts) == 3
    assert len(rejects) == 1
    assert accepts[0]["assigned_bibkey"] == "blake2015consumer"
    assert rejects[0]["fetch_id"] == "fetch_rejected_example"
    assert "assigned_bibkey" not in rejects[0]


def test_assemble_bad_excerpt_fails_nonzero(tmp_path: Path, capsys) -> None:
    cache_root = tmp_path / "cache"
    shas = _build_cache(cache_root)
    doc = _sources_doc(shas, cache_root)
    # Corrupt one excerpt so it no longer substring-matches its cached text.
    doc["sources"][1]["excerpt"] = "this phrase does not appear anywhere in the cached text"
    sources_path = tmp_path / "sources.json"
    _write_sources(sources_path, doc)
    project_dir = tmp_path / "project"

    rc = main([str(sources_path), str(project_dir)])
    assert rc != 0
    err = capsys.readouterr().err
    assert "EXCERPT FAILURE" in err
    assert "abadie2010synthetic" in err
    # Nothing is written on failure.
    assert not (project_dir / "evidence_ledger.yml").exists()
    assert not (project_dir / "bib_ledger.yml").exists()


def test_assemble_cache_root_override(tmp_path: Path) -> None:
    """--cache-root overrides the cache_root declared in the sources JSON."""
    real_cache = tmp_path / "real_cache"
    shas = _build_cache(real_cache)
    doc = _sources_doc(shas, real_cache)
    # Point the JSON's cache_root at a nonexistent dir; the flag must win.
    doc["cache_root"] = str(tmp_path / "does_not_exist")
    sources_path = tmp_path / "sources.json"
    _write_sources(sources_path, doc)
    project_dir = tmp_path / "project"

    rc = main([str(sources_path), str(project_dir), "--cache-root", str(real_cache)])
    assert rc == 0
    assert (project_dir / "evidence_ledger.yml").exists()
    # The cache_manifest still records the JSON's declared cache_root (verbatim).
    cache = yaml.safe_load((project_dir / "cache_manifest.yml").read_text())
    assert cache["cache_root"] == str(tmp_path / "does_not_exist")


def test_assemble_missing_sources_file_returns_2(tmp_path: Path) -> None:
    rc = main([str(tmp_path / "nope.json"), str(tmp_path / "project")])
    assert rc == 2

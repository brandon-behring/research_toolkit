"""Tests for scripts/compose_cross_project_kg.py.

Builds two tiny fake project trees in tmp_path, each with a small valid
claim_graph.jsonl that shares one source (same primary_url, different id)
across projects, then runs the composer and checks that the merge dedups the
shared source once, unions its contributing projects, remaps the losing source
id on referencing claims, keeps all unique records, emits valid JSONL, and
produces a graph that validators/claim_graph.py accepts. Hand-rolled fixtures;
no unittest.mock.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import compose_cross_project_kg as ckg  # type: ignore[import-not-found]
from validators import claim_graph  # type: ignore[import-not-found]

# Shared source URL referenced by BOTH fake projects (exercises dedup). The
# toolkit derives a source id from this URL, but the two projects deliberately
# carry DIFFERENT ids for it so the url-based dedup + id remap is exercised.
SHARED_URL = "https://arxiv.org/abs/1706.03762"


def _confidence() -> dict[str, Any]:
    return {"score": 0.9, "factors": ["primary source"]}


def _write_graph(project_dir: Path, records: list[dict[str, Any]]) -> None:
    """Write a claim_graph.jsonl for a fake project directory."""
    project_dir.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(rec, ensure_ascii=False) for rec in records]
    (project_dir / "claim_graph.jsonl").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def _build_two_projects(tmp_path: Path) -> list[Path]:
    """Two project dirs sharing one source (by URL) under different ids."""
    proj_a = tmp_path / "research_alpha"
    proj_b = tmp_path / "research_beta"
    _write_graph(
        proj_a,
        [
            {
                "record_type": "entity",
                "id": "ent_transformer",
                "topic": "alpha",
                "entity_type": "concept",
                "canonical_name": "Transformer",
            },
            {
                "record_type": "source",
                "id": "src_attn_alpha",
                "topic": "alpha",
                "source_url": SHARED_URL,
                "primary_url": SHARED_URL,
                "cache_ids": ["cache_attn"],
            },
            {
                "record_type": "claim",
                "id": "clm_alpha_1",
                "topic": "alpha",
                "claim_type": "fact",
                "text": "Attention is all you need.",
                "status": "active",
                "evidence_ids": ["ev_alpha_1"],
                "entity_ids": ["ent_transformer", "src_attn_alpha"],
                "confidence": _confidence(),
            },
        ],
    )
    _write_graph(
        proj_b,
        [
            {
                "record_type": "entity",
                "id": "ent_rlhf",
                "topic": "beta",
                "entity_type": "concept",
                "canonical_name": "RLHF",
            },
            # Same source URL as proj_a, DIFFERENT id -> dedups + aliases.
            {
                "record_type": "source",
                "id": "src_attn_beta",
                "topic": "beta",
                "source_url": SHARED_URL,
                "primary_url": SHARED_URL,
                "cache_ids": ["cache_attn"],
            },
            {
                "record_type": "claim",
                "id": "clm_beta_1",
                "topic": "beta",
                "claim_type": "fact",
                "text": "RLHF builds on the transformer source.",
                "status": "active",
                "evidence_ids": ["ev_beta_1"],
                # references the beta source id, which loses to proj_a's id.
                "entity_ids": ["ent_rlhf", "src_attn_beta"],
                "confidence": _confidence(),
            },
        ],
    )
    return [proj_a, proj_b]


# ---------- Composition + dedup ----------


def test_compose_dedups_shared_source_by_primary_url(tmp_path):
    projects = _build_two_projects(tmp_path)
    records, errors = ckg.compose(projects, "2026-05-31")
    assert errors == [], errors
    sources = [r for r in records if r.get("record_type") == "source"]
    shared = [s for s in sources if s.get("source_url") == SHARED_URL]
    assert len(shared) == 1, sources


def test_compose_unions_source_projects_on_shared_source(tmp_path):
    projects = _build_two_projects(tmp_path)
    records, _ = ckg.compose(projects, "2026-05-31")
    shared = next(r for r in records if r.get("source_url") == SHARED_URL)
    assert set(shared["source_projects"]) == {"alpha", "beta"}, shared


def test_compose_keeps_all_unique_records(tmp_path):
    projects = _build_two_projects(tmp_path)
    records, _ = ckg.compose(projects, "2026-05-31")
    ids = sorted(r["id"] for r in records)
    # src_attn_beta is folded into src_attn_alpha; everything else survives.
    assert ids == [
        "clm_alpha_1",
        "clm_beta_1",
        "ent_rlhf",
        "ent_transformer",
        "src_attn_alpha",
    ], ids


def test_compose_remaps_losing_source_id_on_referencing_claim(tmp_path):
    projects = _build_two_projects(tmp_path)
    records, _ = ckg.compose(projects, "2026-05-31")
    claim_b = next(r for r in records if r.get("id") == "clm_beta_1")
    # proj_b referenced src_attn_beta, which dedups into proj_a's src_attn_alpha.
    assert "src_attn_beta" not in claim_b["entity_ids"], claim_b
    assert "src_attn_alpha" in claim_b["entity_ids"], claim_b


def test_compose_stamps_compose_date_on_every_record(tmp_path):
    projects = _build_two_projects(tmp_path)
    records, _ = ckg.compose(projects, "2026-05-31")
    assert all(r.get("composed_on") == "2026-05-31" for r in records), records


def test_compose_reports_missing_claim_graph(tmp_path):
    projects = _build_two_projects(tmp_path)
    missing = tmp_path / "research_empty"
    missing.mkdir()
    records, errors = ckg.compose([*projects, missing], "2026-05-31")
    assert any("no claim_graph.jsonl" in e for e in errors), errors


def test_compose_detects_cross_project_claim_id_collision(tmp_path):
    proj_a = tmp_path / "research_a"
    proj_b = tmp_path / "research_b"
    claim = {
        "record_type": "claim",
        "id": "clm_dup",
        "topic": "t",
        "claim_type": "fact",
        "text": "duplicated id across projects",
        "status": "active",
        "evidence_ids": ["ev"],
        "entity_ids": ["ent"],
        "confidence": _confidence(),
    }
    _write_graph(proj_a, [claim])
    _write_graph(proj_b, [dict(claim)])
    _records, errors = ckg.compose([proj_a, proj_b], "2026-05-31")
    assert any("collision" in e and "clm_dup" in e for e in errors), errors


# ---------- CLI + validator acceptance ----------


def test_main_writes_valid_jsonl_accepted_by_validator(tmp_path):
    projects = _build_two_projects(tmp_path)
    out = tmp_path / "composed" / "merged_claim_graph.jsonl"
    rc = ckg.main(
        [str(out), str(projects[0]), str(projects[1]), "--date", "2026-05-31"]
    )
    assert rc == 0
    assert out.exists()

    lines = [ln for ln in out.read_text(encoding="utf-8").splitlines() if ln.strip()]
    parsed = [json.loads(ln) for ln in lines]
    assert all(isinstance(rec, dict) for rec in parsed), parsed
    # Shared source present exactly once in the written file.
    assert sum(1 for r in parsed if r.get("source_url") == SHARED_URL) == 1, parsed

    # The merged graph passes the claim_graph schema validator.
    validator_errors = claim_graph.validate(out)
    assert validator_errors == [], validator_errors


def test_main_rejects_nonexistent_project_dir(tmp_path):
    out = tmp_path / "out.jsonl"
    rc = ckg.main([str(out), str(tmp_path / "does_not_exist")])
    assert rc == 2
    assert not out.exists()

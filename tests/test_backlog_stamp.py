"""Tests for scripts/backlog_stamp.py: stamp round-trip + not-found.

Uses the test-style sys.path.insert pattern for scripts/* imports.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import backlog_stamp as bs  # type: ignore[import-not-found]


def _backlog(tmp_path: Path) -> Path:
    data = {
        "schema_version": 1,
        "source_corpus": "interview_prep_series",
        "generated_at": "2026-05-24",
        "entries": [
            {
                "topic_id": "dml-het-effects",
                "title": "Double ML for heterogeneous treatment effects",
                "kind": "deepen",
                "track": 2,
                "priority": "P0",
                "rationale": "vol02 frontier",
                "claim_family_seeds": ["identification", "estimation", "inference"],
                "status": "proposed",
                "source_volume": "vol02_causal_inference",
            },
            {
                "topic_id": "behavioral-econ-product",
                "title": "Behavioral economics for product",
                "kind": "adjacent",
                "track": "cross",
                "priority": "P1",
                "rationale": "scaffold bridge",
                "claim_family_seeds": ["choice-architecture", "field-experiments", "welfare"],
                "status": "proposed",
            },
        ],
    }
    path = tmp_path / "topic_backlog.yml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def _load_entry(path: Path, topic_id: str) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return next(e for e in data["entries"] if e["topic_id"] == topic_id)


def test_backlog_stamp_writes_researched_lifecycle_fields(tmp_path: Path) -> None:
    path = _backlog(tmp_path)
    rc = bs.stamp(
        path,
        "dml-het-effects",
        status="researched",
        dossier="~/Claude/research_dml/agent_index/",
        today="2026-05-24",
    )
    assert rc == 0
    entry = _load_entry(path, "dml-het-effects")
    assert entry["status"] == "researched"
    assert entry["dossier_path"] == "~/Claude/research_dml/agent_index/"
    assert entry["researched_at"] == "2026-05-24"
    # Untouched entry preserved.
    assert _load_entry(path, "behavioral-econ-product")["status"] == "proposed"


def test_backlog_stamp_result_stays_valid(tmp_path: Path) -> None:
    from validators import topic_backlog

    path = _backlog(tmp_path)
    bs.stamp(path, "dml-het-effects", status="researched", today="2026-05-24")
    assert topic_backlog.validate(path) == []


def test_backlog_stamp_rejects_unknown_topic_id(tmp_path: Path) -> None:
    path = _backlog(tmp_path)
    assert bs.stamp(path, "no-such-topic", status="researched") == 2

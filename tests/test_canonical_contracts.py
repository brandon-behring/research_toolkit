"""Tests for v1 canonical dossier contracts and workflow commands."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import yaml

from research_toolkit import commands
from research_toolkit.canonical import impact_graph, sha256_file, validate_dossier
from research_toolkit.contracts import CORE_SCHEMAS, validate_schema_bundle
from research_toolkit.legacy_import import import_legacy

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures"


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(item, sort_keys=True) + "\n" for item in records),
        encoding="utf-8",
    )


def _write_valid_dossier(root: Path) -> None:
    root.mkdir()
    (root / "dossier.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0.0",
                "dossier_id": "dossier_demo",
                "topic": "demo",
                "kind": "research",
                "status": "reviewed",
                "created_at": "2026-07-14",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    _write_jsonl(
        root / "sources.jsonl",
        [
            {
                "schema_version": "1.0.0",
                "source_id": "src_demo",
                "requested_url": "https://example.com/source",
                "canonical_url": "https://example.com/source",
                "source_kind": "paper",
                "title": "Demo source",
                "authority_scope": "demo result only",
                "independence_cluster": "example.com",
                "rights_status": "public",
                "visibility": "public",
                "retrieved_at": "2026-07-14T00:00:00Z",
            }
        ],
    )
    _write_jsonl(
        root / "evidence.jsonl",
        [
            {
                "schema_version": "1.0.0",
                "evidence_id": "ev_demo",
                "source_id": "src_demo",
                "excerpt": "A directly relevant excerpt.",
                "extraction_method": "verbatim-match",
                "link_confidence": 0.95,
                "supports": [
                    {"claim_id": "claim_demo", "evidence_role": "supports", "strength": "full"}
                ],
                "retrieved_at": "2026-07-14T00:00:00Z",
                "rights_status": "public",
            }
        ],
    )
    _write_jsonl(
        root / "claims.jsonl",
        [
            {
                "schema_version": "1.0.0",
                "claim_id": "claim_demo",
                "text": "The demo result is supported.",
                "claim_type": "fact",
                "status": "active",
                "evidence_ids": ["ev_demo"],
                "confidence": 0.9,
                "created_at": "2026-07-14T00:00:00Z",
            }
        ],
    )
    _write_jsonl(
        root / "reviews.jsonl",
        [
            {
                "schema_version": "1.0.0",
                "review_id": "review_demo",
                "claim_id": "claim_demo",
                "reviewer": "reviewer-a",
                "reviewed_at": "2026-07-14T01:00:00Z",
                "disposition": "supported",
                "entailment": "full",
                "currency": "current",
                "methodology": "Primary source inspected in full context.",
                "risk_of_bias": "low",
                "confidence": 0.9,
                "evidence_ids": ["ev_demo"],
                "independent": True,
            }
        ],
    )
    _write_jsonl(
        root / "watch.jsonl",
        [
            {
                "schema_version": "1.0.0",
                "source_id": "src_demo",
                "canonical_url": "https://example.com/source",
                "volatility": "active",
                "cadence_days": 30,
                "owner": "research-owner",
                "last_retrieved_at": "2026-07-14T00:00:00Z",
                "last_semantic_review_at": "2026-07-14T01:00:00Z",
                "next_check_at": "2026-08-13",
                "events": ["release-feed"],
                "status": "active",
            }
        ],
    )
    run_dir = root / "runs" / "run_demo"
    run_dir.mkdir(parents=True)
    (run_dir / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "run_id": "run_demo",
                "topic": "demo",
                "started_at": "2026-07-14T00:00:00Z",
                "completed_at": "2026-07-14T01:00:00Z",
                "status": "complete",
                "toolkit": {
                    "commit": "test-commit",
                    "skills_version": "3.0.0-alpha.1",
                    "cli_version": "3.0.0a1",
                },
                "repositories": [],
                "environment": {
                    "python": "3.13",
                    "os": "test",
                    "model": "test",
                    "effort": "test",
                    "tool_policy": "test",
                },
                "decision_log": [],
                "searches": [],
                "inputs": [],
                "outputs": [],
                "attempts": [],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_jsonl(run_dir / "search-decisions.jsonl", [])
    _write_jsonl(run_dir / "refresh-events.jsonl", [])


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _write_release(root: Path) -> None:
    derived = root / "derived"
    derived.mkdir()
    (derived / "claim-graph.jsonl").write_text("{}\n", encoding="utf-8")
    (derived / "agent-index.md").write_text("# Demo\n", encoding="utf-8")
    (derived / "citation-report.json").write_text("{}\n", encoding="utf-8")
    (derived / "consumer-bindings.jsonl").write_text("", encoding="utf-8")
    (derived / "synthesis-export.jsonl").write_text("{}\n", encoding="utf-8")
    paths = [
        "dossier.yaml",
        "sources.jsonl",
        "evidence.jsonl",
        "claims.jsonl",
        "reviews.jsonl",
        "watch.jsonl",
        "derived/claim-graph.jsonl",
        "derived/agent-index.md",
        "derived/citation-report.json",
        "derived/consumer-bindings.jsonl",
        "derived/synthesis-export.jsonl",
    ]
    release = {
        "schema_version": "1.0.0",
        "release_id": "rr-20260714.1",
        "created_at": "2026-07-14T02:00:00Z",
        "freshness_cutoff": "2026-07-14",
        "repositories": [{"name": "research-dossiers", "commit": "test-commit"}],
        "artifacts": [{"path": path, "sha256": sha256_file(root / path)} for path in paths],
        "validators": [{"name": "canonical", "version": "1.0.0", "status": "pass"}],
        "unresolved_findings": [],
        "waivers": [],
        "reviewer_acceptance": [
            {"reviewer": "reviewer-a", "accepted_at": "2026-07-14T02:00:00Z"}
        ],
    }
    (root / "release.json").write_text(
        json.dumps(release, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def test_schema_bundle_loads_every_core_contract() -> None:
    assert len(CORE_SCHEMAS) == 11
    assert validate_schema_bundle() == []


def test_validate_dossier_accepts_referentially_complete_records(tmp_path: Path) -> None:
    dossier = tmp_path / "dossier"
    _write_valid_dossier(dossier)
    assert validate_dossier(dossier) == []


def test_validate_dossier_rejects_unresolved_evidence_reference(tmp_path: Path) -> None:
    dossier = tmp_path / "dossier"
    _write_valid_dossier(dossier)
    claims = json.loads((dossier / "claims.jsonl").read_text(encoding="utf-8"))
    claims["evidence_ids"] = ["ev_missing"]
    _write_jsonl(dossier / "claims.jsonl", [claims])
    errors = validate_dossier(dossier)
    assert any("unresolved evidence 'ev_missing'" in error for error in errors), errors


def test_research_run_initializes_clean_boundary(tmp_path: Path) -> None:
    dossier = tmp_path / "new-dossier"
    rc = commands.research_run_main(
        [
            str(dossier),
            "--initialize",
            "--dossier-id",
            "dossier_new",
            "--topic",
            "New topic",
            "--run-id",
            "run_20260714",
            "--date",
            "2026-07-14",
        ]
    )
    assert rc == 0
    assert validate_dossier(dossier) == []
    assert (dossier / "runs" / "run_20260714" / "manifest.json").is_file()


def test_impact_graph_traces_source_to_claim(tmp_path: Path) -> None:
    dossier = tmp_path / "dossier"
    _write_valid_dossier(dossier)
    result = impact_graph(dossier, source_id="src_demo", claim_id=None)
    assert result["sources"] == ["src_demo"]
    assert result["evidence"] == ["ev_demo"]
    assert result["claims"] == ["claim_demo"]


def test_validate_dossier_rejects_refresh_event_with_unknown_source(tmp_path: Path) -> None:
    dossier = tmp_path / "dossier"
    _write_valid_dossier(dossier)
    _write_jsonl(
        dossier / "runs" / "run_demo" / "refresh-events.jsonl",
        [
            {
                "schema_version": "1.0.0",
                "event_id": "event_demo",
                "source_id": "src_missing",
                "checked_at": "2026-07-14T02:00:00Z",
                "old_digest": None,
                "new_digest": None,
                "change_class": "unreachable",
                "affected_claim_ids": ["claim_demo"],
                "affected_consumer_binding_ids": [],
                "disposition": "review-required",
            }
        ],
    )
    errors = validate_dossier(dossier)
    assert any("unresolved source 'src_missing'" in error for error in errors), errors


def test_release_gate_verifies_complete_artifact_hash_set(tmp_path: Path) -> None:
    dossier = tmp_path / "dossier"
    _write_valid_dossier(dossier)
    _write_release(dossier)
    assert validate_dossier(dossier, require_release=True) == []
    (dossier / "derived" / "agent-index.md").write_text("changed\n", encoding="utf-8")
    errors = validate_dossier(dossier, require_release=True)
    assert any("digest mismatch" in error for error in errors), errors


def test_legacy_import_is_idempotent_and_semantically_unresolved(tmp_path: Path) -> None:
    source = FIXTURES / "v3_strict_live_demo"
    legacy = tmp_path / "legacy"
    shutil.copytree(source, legacy)
    target = tmp_path / "canonical"
    first = import_legacy(legacy, target)
    before = _tree_digest(target)
    second = import_legacy(legacy, target)
    assert len(first) == len(second)
    assert _tree_digest(target) == before
    claims = [json.loads(line) for line in (target / "claims.jsonl").read_text().splitlines()]
    assert claims
    assert {item["status"] for item in claims} == {"unresolved"}
    assert validate_dossier(target) == []

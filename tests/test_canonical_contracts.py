"""Tests for v1 canonical dossier contracts and workflow commands."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
from pathlib import Path

import pytest
import yaml

from research_toolkit import commands
from research_toolkit import legacy_import as legacy_import_module
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


def test_validate_dossier_rejects_secret_bearing_canonical_urls(
    tmp_path: Path,
) -> None:
    root = tmp_path / "dossier"
    _write_valid_dossier(root)
    source = json.loads((root / "sources.jsonl").read_text(encoding="utf-8"))
    source["requested_url"] = "https://user:pass@example.com/source"
    source["canonical_url"] = "https://example.com/source?apikey=top-secret"
    _write_jsonl(root / "sources.jsonl", [source])
    errors = validate_dossier(root)
    assert any("requested_url: unsafe durable URL" in error for error in errors)
    assert any("canonical_url: unsafe durable URL" in error for error in errors)


def test_validate_dossier_rejects_any_url_fingerprint_field(tmp_path: Path) -> None:
    root = tmp_path / "dossier"
    _write_valid_dossier(root)
    decisions_path = root / "runs" / "run_demo" / "search-decisions.jsonl"
    _write_jsonl(
        decisions_path,
        [
            {
                "decision_id": "decision_demo",
                "query": "demo",
                "source_url": "https://example.com/source",
                "source_url_fingerprint": "0" * 64,
                "decision": "include",
                "reason": "test",
                "decided_at": "2026-07-14T00:00:00Z",
            }
        ],
    )
    errors = validate_dossier(root)
    assert any(
        "source_url_fingerprint" in error and "offline guessing oracles" in error
        for error in errors
    ), errors


@pytest.mark.parametrize(
    "field",
    ["source_uri_sha256", "request_fingerprint", "url_checksum", "url_md5"],
)
def test_validate_dossier_rejects_url_fingerprint_aliases(
    tmp_path: Path,
    field: str,
) -> None:
    root = tmp_path / "dossier"
    _write_valid_dossier(root)
    source = json.loads((root / "sources.jsonl").read_text(encoding="utf-8"))
    source[field] = "0" * 64
    _write_jsonl(root / "sources.jsonl", [source])
    errors = validate_dossier(root)
    assert any(field in error and "offline guessing oracles" in error for error in errors)


def test_validate_dossier_rejects_secret_urls_embedded_in_prose(
    tmp_path: Path,
) -> None:
    root = tmp_path / "dossier"
    _write_valid_dossier(root)
    evidence = json.loads((root / "evidence.jsonl").read_text(encoding="utf-8"))
    evidence["excerpt"] = "See https://example.com/source?token=TOP-SECRET."
    _write_jsonl(root / "evidence.jsonl", [evidence])
    decisions = root / "runs" / "run_demo" / "search-decisions.jsonl"
    _write_jsonl(
        decisions,
        [
            {
                "decision_id": "decision_demo",
                "query": "Inspect https://example.org/search?signature=TOP-SECRET",
                "source_url": "https://example.org/source",
                "decision": "include",
                "reason": "test",
                "decided_at": "2026-07-14T00:00:00Z",
            }
        ],
    )
    errors = validate_dossier(root)
    assert any("evidence.jsonl[0].excerpt.embedded_url" in error for error in errors)
    assert any("search-decisions.jsonl[0].query.embedded_url" in error for error in errors)
    assert all("TOP-SECRET" not in error for error in errors)


def _write_release(root: Path) -> None:
    derived = root / "derived"
    derived.mkdir()
    (derived / "claim-graph.jsonl").write_text("{}\n", encoding="utf-8")
    (derived / "agent-index.md").write_text("# Demo\n", encoding="utf-8")
    (derived / "citation-report.json").write_text("{}\n", encoding="utf-8")
    (derived / "consumer-bindings.jsonl").write_text("", encoding="utf-8")
    _write_jsonl(
        derived / "synthesis-export.jsonl",
        [
            {
                "export_schema_version": 2,
                "record_type": "entity",
                "id": "export_ent_demo",
                "source_project": "demo",
                "exported_at": "2026-07-14",
                "payload": {
                    "record_type": "entity",
                    "id": "ent_demo",
                    "topic": "demo",
                    "entity_type": "paper",
                    "canonical_name": "Demo source",
                },
            }
        ],
    )
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


def test_release_gate_rejects_body_bearing_synthesis_export_even_when_hashed(
    tmp_path: Path,
) -> None:
    dossier = tmp_path / "dossier"
    _write_valid_dossier(dossier)
    _write_release(dossier)
    export = dossier / "derived" / "synthesis-export.jsonl"
    _write_jsonl(export, [{"record_type": "claim", "raw_body": "PRIVATE BYTES"}])
    release_path = dossier / "release.json"
    release = json.loads(release_path.read_text(encoding="utf-8"))
    artifact = next(
        item
        for item in release["artifacts"]
        if item["path"] == "derived/synthesis-export.jsonl"
    )
    artifact["sha256"] = sha256_file(export)
    release_path.write_text(
        json.dumps(release, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    errors = validate_dossier(dossier, require_release=True)
    assert any("raw_body" in error and "cached-body" in error for error in errors), errors


@pytest.mark.parametrize("field", ["rawBody", "raw-body", "rawBODY", "bytesBase64"])
def test_release_gate_rejects_body_field_spelling_variants_even_when_hashed(
    tmp_path: Path,
    field: str,
) -> None:
    dossier = tmp_path / "dossier"
    _write_valid_dossier(dossier)
    _write_release(dossier)
    export = dossier / "derived" / "synthesis-export.jsonl"
    _write_jsonl(
        export,
        [
            {
                "export_schema_version": 2,
                "record_type": "claim",
                "id": "export_claim_demo",
                "source_project": "demo",
                "exported_at": "2026-07-14",
                "payload": {field: "PRIVATE BYTES"},
            }
        ],
    )
    release_path = dossier / "release.json"
    release = json.loads(release_path.read_text(encoding="utf-8"))
    artifact = next(
        item
        for item in release["artifacts"]
        if item["path"] == "derived/synthesis-export.jsonl"
    )
    artifact["sha256"] = sha256_file(export)
    release_path.write_text(
        json.dumps(release, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    errors = validate_dossier(dossier, require_release=True)
    assert any(field in error and "cached-body" in error for error in errors), errors


def test_release_gate_rejects_nonpublic_source_and_excerpt_bodies(
    tmp_path: Path,
) -> None:
    dossier = tmp_path / "dossier"
    _write_valid_dossier(dossier)
    source_path = dossier / "sources.jsonl"
    source = json.loads(source_path.read_text(encoding="utf-8"))
    source["rights_status"] = "restricted"
    source["visibility"] = "restricted"
    _write_jsonl(source_path, [source])

    evidence_path = dossier / "evidence.jsonl"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    evidence["rights_status"] = "private-use"
    evidence["excerpt"] = "PRIVATE CACHED BODY"
    _write_jsonl(evidence_path, [evidence])

    # Non-public evidence is valid for a local research dossier, but cannot
    # cross the release boundary as a body-bearing excerpt.
    assert validate_dossier(dossier) == []
    _write_release(dossier)
    errors = validate_dossier(dossier, require_release=True)
    assert any("non-public rights status blocks release" in error for error in errors), errors
    assert any("non-public visibility blocks release" in error for error in errors), errors
    assert any("non-public excerpt rights block release" in error for error in errors), errors


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


def test_legacy_import_redacts_urls_uses_opaque_ids_and_maps_cache_only(
    tmp_path: Path,
) -> None:
    source = FIXTURES / "v3_strict_live_demo"
    legacy = tmp_path / "legacy"
    shutil.copytree(source, legacy)
    secret_url = "https://example.com/papers/v3-demo?token=top-secret#fragment"

    bib_path = legacy / "bib_ledger.yml"
    bib = yaml.safe_load(bib_path.read_text(encoding="utf-8"))
    bib["entries"][0]["bibkey"] = secret_url
    bib["entries"][0]["primary_url"] = secret_url
    bib["entries"][0]["title"] = f"Legacy title cites {secret_url}."
    bib["entries"][0]["claim_family"] = secret_url
    bib_path.write_text(yaml.safe_dump(bib, sort_keys=False), encoding="utf-8")

    evidence_path = legacy / "evidence_ledger.yml"
    evidence = yaml.safe_load(evidence_path.read_text(encoding="utf-8"))
    evidence["entries"][0]["source_url"] = secret_url
    evidence["entries"][0]["rights_status"] = "cache_only"
    evidence["entries"][0]["excerpt"] = f"Legacy excerpt cites {secret_url}."
    evidence["entries"][0]["supports"][0]["extraction_method"] = secret_url
    evidence_path.write_text(
        yaml.safe_dump(evidence, sort_keys=False), encoding="utf-8"
    )

    graph_path = legacy / "claim_graph.jsonl"
    graph_rows = [json.loads(line) for line in graph_path.read_text().splitlines()]
    for row in graph_rows:
        if row.get("record_type") == "claim":
            row["text"] = f"Legacy claim cites {secret_url}."
            row["claim_type"] = secret_url
            break
    graph_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in graph_rows),
        encoding="utf-8",
    )

    target = tmp_path / "canonical"
    import_legacy(legacy, target)
    sources = [json.loads(line) for line in (target / "sources.jsonl").read_text().splitlines()]
    imported_evidence = [
        json.loads(line) for line in (target / "evidence.jsonl").read_text().splitlines()
    ]
    assert sources[0]["source_id"] == "src_legacy_0001"
    assert sources[0]["canonical_url"].startswith(
        "https://example.com/papers/v3-demo?"
    )
    assert "REDACTED" in sources[0]["canonical_url"]
    assert sources[0]["source_kind"].endswith("?redacted=REDACTED")
    assert imported_evidence[0]["rights_status"] == "restricted"
    assert imported_evidence[0]["extraction_method"].endswith(
        "?redacted=REDACTED"
    )
    imported_claims = [
        json.loads(line) for line in (target / "claims.jsonl").read_text().splitlines()
    ]
    assert imported_claims[0]["claim_type"].endswith("?redacted=REDACTED")
    assert not (target / "derived" / "claim-graph.jsonl").exists()
    durable_bytes = b"".join(
        path.read_bytes() for path in target.rglob("*") if path.is_file()
    )
    assert b"top-secret" not in durable_bytes
    assert hashlib.sha256(secret_url.encode()).hexdigest().encode() not in durable_bytes
    assert hashlib.sha256(b"top-secret").hexdigest().encode() not in durable_bytes
    assert validate_dossier(target) == []


def test_legacy_import_rejects_credentials_without_target_writes(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy"
    shutil.copytree(FIXTURES / "v3_strict_live_demo", legacy)
    bib_path = legacy / "bib_ledger.yml"
    bib = yaml.safe_load(bib_path.read_text(encoding="utf-8"))
    bib["entries"][0]["primary_url"] = "https://user:secret@example.com/source"
    bib_path.write_text(yaml.safe_dump(bib, sort_keys=False), encoding="utf-8")
    target = tmp_path / "canonical"

    with pytest.raises(ValueError, match="credentials"):
        import_legacy(legacy, target)
    assert not target.exists()


def test_legacy_import_validates_stage_before_target_writes(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy"
    shutil.copytree(FIXTURES / "v3_strict_live_demo", legacy)
    evidence_path = legacy / "evidence_ledger.yml"
    evidence = yaml.safe_load(evidence_path.read_text(encoding="utf-8"))
    evidence["entries"][0]["supports"][0]["evidence_role"] = "invented-role"
    evidence_path.write_text(
        yaml.safe_dump(evidence, sort_keys=False), encoding="utf-8"
    )
    target = tmp_path / "canonical"

    with pytest.raises(ValueError, match="staged imported dossier failed validation"):
        import_legacy(legacy, target)
    assert not target.exists()


def test_legacy_import_outputs_are_owner_only_under_umask_022(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy"
    shutil.copytree(FIXTURES / "v3_strict_live_demo", legacy)
    target = tmp_path / "nested" / "canonical"

    previous_umask = os.umask(0o022)
    try:
        import_legacy(legacy, target)
    finally:
        os.umask(previous_umask)

    for path in (target, *target.rglob("*")):
        expected = 0o700 if path.is_dir() else 0o600
        assert stat.S_IMODE(path.lstat().st_mode) == expected, path
    assert stat.S_IMODE(target.parent.lstat().st_mode) == 0o700


def test_legacy_import_idempotent_rerun_tightens_existing_modes(
    tmp_path: Path,
) -> None:
    legacy = tmp_path / "legacy"
    shutil.copytree(FIXTURES / "v3_strict_live_demo", legacy)
    target = tmp_path / "canonical"
    import_legacy(legacy, target)

    for path in target.rglob("*"):
        path.chmod(0o755 if path.is_dir() else 0o644)
    target.chmod(0o755)
    import_legacy(legacy, target)

    for path in (target, *target.rglob("*")):
        expected = 0o700 if path.is_dir() else 0o600
        assert stat.S_IMODE(path.lstat().st_mode) == expected, path


def test_legacy_import_detects_silent_existing_file_chmod_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    legacy = tmp_path / "legacy"
    shutil.copytree(FIXTURES / "v3_strict_live_demo", legacy)
    target = tmp_path / "canonical"
    import_legacy(legacy, target)
    victim = target / "sources.jsonl"
    victim.chmod(0o644)
    real_chmod = os.chmod

    def silently_ignore_victim(path: os.PathLike[str] | str, mode: int) -> None:
        if Path(path) == victim:
            return
        real_chmod(path, mode)

    monkeypatch.setattr(legacy_import_module.os, "chmod", silently_ignore_victim)

    with pytest.raises(PermissionError, match="must have mode 0600"):
        import_legacy(legacy, target)
    assert stat.S_IMODE(victim.lstat().st_mode) == 0o644

"""Strict-live v2 validators and fixtures."""
from __future__ import annotations

import copy
from datetime import date
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

import pytest
import yaml

from validators import bib_ledger, dataset_ledger
from validators import cache_manifest, claim_graph, evidence_ledger, freshness, gather_trace, pre_selection_manifest, research_kb_export

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "v2_strict_live_ai_agents"
MULTI_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "v2_strict_live_multi_entry"
V3_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "v3_strict_live_demo"
ATOMIC_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "v2_strict_live_atomic"


def test_v2_fixture_passes_all_validators() -> None:
    assert bib_ledger.validate(FIXTURE / "bib_ledger.yml") == []
    assert dataset_ledger.validate(FIXTURE / "dataset_ledger.yml") == []
    assert evidence_ledger.validate(FIXTURE / "evidence_ledger.yml") == []
    assert cache_manifest.validate(FIXTURE / "cache_manifest.yml") == []
    assert claim_graph.validate(FIXTURE / "claim_graph.jsonl") == []
    assert research_kb_export.validate(FIXTURE / "research_kb_export.jsonl") == []
    assert freshness.validate(FIXTURE, strict=True, today=date(2026, 5, 19)) == []


def test_v2_bib_ledger_rejects_missing_entry_freshness_field(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(FIXTURE, project)
    text = (project / "bib_ledger.yml").read_text(encoding="utf-8")
    text = text.replace("  retrieved_at: 2026-05-19\n", "", 1)
    (project / "bib_ledger.yml").write_text(text, encoding="utf-8")
    errors = bib_ledger.validate(project / "bib_ledger.yml")
    assert any("retrieved_at" in e for e in errors), errors


def test_v2_dataset_ledger_rejects_stale_after_above_tier_default(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(FIXTURE, project)
    text = (project / "dataset_ledger.yml").read_text(encoding="utf-8")
    text = text.replace("  stale_after_days: 30\n", "  stale_after_days: 365\n", 1)
    (project / "dataset_ledger.yml").write_text(text, encoding="utf-8")
    errors = dataset_ledger.validate(project / "dataset_ledger.yml")
    assert any("exceeds strict-live default" in e for e in errors), errors


def test_freshness_strict_rejects_stale_entry(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(FIXTURE, project)
    errors = freshness.validate(project, strict=True, today=date(2026, 7, 1))
    assert any("stale as of 2026-07-01" in e for e in errors), errors


def test_freshness_rejects_missing_evidence_reference(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(FIXTURE, project)
    text = (project / "bib_ledger.yml").read_text(encoding="utf-8")
    text = text.replace("ev_ai_agent_security_0001", "ev_missing", 1)
    (project / "bib_ledger.yml").write_text(text, encoding="utf-8")
    errors = freshness.validate(project, strict=True, today=date(2026, 5, 19))
    assert any("ev_missing" in e and "evidence_ledger" in e for e in errors), errors


def test_cache_manifest_rejects_hash_mismatch(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(FIXTURE, project)
    raw = project / "cache" / "raw" / "agent_security.html"
    raw.write_text(raw.read_text(encoding="utf-8") + "\nmutated\n", encoding="utf-8")
    errors = cache_manifest.validate(project / "cache_manifest.yml")
    assert any("sha256" in e and "actual" in e for e in errors), errors


def test_evidence_ledger_rejects_empty_supports(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(FIXTURE, project)
    text = (project / "evidence_ledger.yml").read_text(encoding="utf-8")
    start = text.index("  supports:\n")
    end = text.index("  excerpt:", start)
    text = text[:start] + "  supports: []\n" + text[end:]
    (project / "evidence_ledger.yml").write_text(text, encoding="utf-8")
    errors = evidence_ledger.validate(project / "evidence_ledger.yml")
    assert any("supports" in e and "non-empty" in e for e in errors), errors


def test_claim_graph_rejects_claim_without_evidence(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(FIXTURE, project)
    lines = (project / "claim_graph.jsonl").read_text(encoding="utf-8").splitlines()
    lines[2] = lines[2].replace('"evidence_ids":["ev_ai_agent_security_0001"]', '"evidence_ids":[]')
    (project / "claim_graph.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    errors = claim_graph.validate(project / "claim_graph.jsonl")
    assert any("evidence_ids" in e for e in errors), errors


def test_research_kb_export_rejects_missing_payload(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(FIXTURE, project)
    path = project / "research_kb_export.jsonl"
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    records[0]["payload"] = {}
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
    errors = research_kb_export.validate(path)
    assert any("payload" in e for e in errors), errors


def test_research_kb_export_script_writes_valid_jsonl(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(FIXTURE, project)
    out = tmp_path / "kb_export.jsonl"
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "research_kb_export.py"),
            str(project),
            "--output",
            str(out),
            "--date",
            "2026-05-19",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr
    assert out.exists()
    assert research_kb_export.validate(out) == []


def test_build_claim_graph_smoke(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(FIXTURE, project)
    out = tmp_path / "claim_graph_built.jsonl"
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "build_claim_graph.py"),
            str(project),
            "--output",
            str(out),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr
    assert out.exists()
    assert claim_graph.validate(out) == []
    records = [
        json.loads(line)
        for line in out.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    record_types = {r.get("record_type") for r in records}
    assert {"entity", "source", "claim", "evidence", "cache_blob"}.issubset(record_types)


def test_build_dashboard_matches_fixture_byte_for_byte(tmp_path: Path) -> None:
    """Regression guard: build_dashboard.py output against the ai_agents fixture
    must match the canonical dashboard.md byte-for-byte. If this breaks, either
    the builder logic drifted or the fixture was edited in a way that diverges
    from what the builder produces."""
    out = tmp_path / "dashboard_built.md"
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "build_dashboard.py"),
            str(FIXTURE),
            "--output",
            str(out),
            "--today",
            "2026-05-19",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr
    expected = (FIXTURE / "dashboard.md").read_text(encoding="utf-8")
    actual = out.read_text(encoding="utf-8")
    assert actual == expected, (
        f"Dashboard builder output diverged from fixture. Diff:\n"
        f"--- expected (fixture)\n{expected!r}\n"
        f"--- actual (builder)\n{actual!r}"
    )


def test_build_dashboard_refuses_overwrite(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(FIXTURE, project)
    existing = project / "dashboard.md"
    assert existing.exists()
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "build_dashboard.py"),
            str(project),
            "--no-overwrite",
            "--today",
            "2026-05-19",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode != 0
    assert "refusing to overwrite" in result.stderr


def test_build_claim_graph_refuses_overwrite(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(FIXTURE, project)
    existing = project / "claim_graph.jsonl"
    assert existing.exists()
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "build_claim_graph.py"),
            str(project),
            "--no-overwrite",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode != 0
    assert "refusing to overwrite" in result.stderr


def test_build_dashboard_smoke(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(FIXTURE, project)
    out = tmp_path / "dashboard_built.md"
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "build_dashboard.py"),
            str(project),
            "--output",
            str(out),
            "--today",
            "2026-05-19",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "AI Agent Security" in content  # acronym title-case
    assert "stale blockers:" in content
    assert "evidence coverage:" in content
    assert "Refresh volatile benchmark pages by" in content  # entity-type-specific


# ----- Multi-entry fixture: builder branch tests -----


def test_multi_entry_fixture_passes_all_validators() -> None:
    assert bib_ledger.validate(MULTI_FIXTURE / "bib_ledger.yml") == []
    assert dataset_ledger.validate(MULTI_FIXTURE / "dataset_ledger.yml") == []
    assert evidence_ledger.validate(MULTI_FIXTURE / "evidence_ledger.yml") == []
    assert cache_manifest.validate(MULTI_FIXTURE / "cache_manifest.yml") == []
    assert claim_graph.validate(MULTI_FIXTURE / "claim_graph.jsonl") == []
    errors = freshness.validate(MULTI_FIXTURE, strict=True, today=date(2026, 5, 19))
    assert errors == [], errors


def test_build_claim_graph_quality_tiebreak(tmp_path: Path) -> None:
    """Two evidences support the same claim_id (primary + secondary); the
    builder must pick the primary evidence's excerpt as claim text and the
    higher confidence score."""
    project = tmp_path / "project"
    shutil.copytree(MULTI_FIXTURE, project)
    out = tmp_path / "claim_graph_built.jsonl"
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "build_claim_graph.py"),
            str(project),
            "--output",
            str(out),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr
    records = [
        json.loads(line)
        for line in out.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    by_id = {r["id"]: r for r in records}
    jb = by_id["claim_gpt5_jailbreak_rate"]
    assert jb["confidence"]["score"] == 0.95  # primary wins
    assert "17% jailbreak success rate" in jb["text"]  # primary excerpt
    assert sorted(jb["evidence_ids"]) == [
        "ev_jailbreak_corroboration",
        "ev_jailbreak_rate",
    ]
    # Both ledger entries that reference these evidences should become entities
    assert sorted(jb["entity_ids"]) == [
        "ent_huang2024gpt5jailbreak",
        "ent_park2024defenses",
    ]


def test_v23_c1_corroboration_count_on_multi_source_claim(tmp_path: Path) -> None:
    """v2.3 C1: claim_gpt5_jailbreak_rate has 2 distinct source_urls →
    corroboration_count: 2. Single-source claims omit the field."""
    project = tmp_path / "project"
    shutil.copytree(MULTI_FIXTURE, project)
    out = tmp_path / "claim_graph_built.jsonl"
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "build_claim_graph.py"),
            str(project),
            "--output",
            str(out),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr
    records = [
        json.loads(line)
        for line in out.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    by_id = {r["id"]: r for r in records if r.get("record_type") == "claim"}
    jb = by_id["claim_gpt5_jailbreak_rate"]
    assert jb.get("corroboration_count") == 2, jb
    # Single-source claims omit the field (additive, byte-stable fixtures)
    drift = by_id["claim_alignment_drift"]
    assert "corroboration_count" not in drift, drift


def test_build_claim_graph_propagates_aliases(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(MULTI_FIXTURE, project)
    out = tmp_path / "claim_graph_built.jsonl"
    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "build_claim_graph.py"),
            str(project),
            "--output",
            str(out),
        ],
        check=True,
        cwd=str(REPO_ROOT),
    )
    records = [
        json.loads(line)
        for line in out.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    by_id = {r["id"]: r for r in records if r["record_type"] == "entity"}
    assert by_id["ent_huang2024gpt5jailbreak"]["aliases"] == [
        "GJS",
        "Huang Jailbreak Study",
    ]
    assert by_id["ent_harmbench2024"]["aliases"] == ["HB"]
    # park entry has no aliases → field must be absent
    assert "aliases" not in by_id["ent_park2024defenses"]


def test_build_dashboard_weak_claims_and_multi_tier(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(MULTI_FIXTURE, project)
    out = tmp_path / "dashboard_built.md"
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "build_dashboard.py"),
            str(project),
            "--output",
            str(out),
            "--today",
            "2026-05-19",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr
    content = out.read_text(encoding="utf-8")
    assert "weak claims: 1" in content  # claim_alignment_drift, score 0.60
    assert "evidence coverage: 3/3 claims" in content
    assert "Refresh volatile papers by" in content  # uniform entity_type → specific noun
    assert "Refresh active entries by" in content  # mixed paper + benchmark → fallback


def test_build_dashboard_counts_contradictions(tmp_path: Path) -> None:
    """Programmatically inject a contradiction claim into claim_graph.jsonl
    and verify the dashboard reports conflicts: 1."""
    project = tmp_path / "project"
    shutil.copytree(MULTI_FIXTURE, project)
    cg = project / "claim_graph.jsonl"
    records = [
        json.loads(line)
        for line in cg.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    records.append({
        "record_type": "claim",
        "id": "claim_synthesis_conflict",
        "topic": "ai_safety_eval",
        "claim_type": "contradiction",
        "text": "Park's 17% replication conflicts with prior reports of <5% rates.",
        "status": "conflicted",
        "evidence_ids": ["ev_jailbreak_rate", "ev_jailbreak_corroboration"],
        "entity_ids": ["ent_huang2024gpt5jailbreak", "ent_park2024defenses"],
        "confidence": {"score": 0.70, "factors": ["mixed primary + secondary"]},
    })
    cg.write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in records) + "\n",
        encoding="utf-8",
    )
    out = tmp_path / "dashboard_built.md"
    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "build_dashboard.py"),
            str(project),
            "--output",
            str(out),
            "--today",
            "2026-05-19",
        ],
        check=True,
        cwd=str(REPO_ROOT),
    )
    content = out.read_text(encoding="utf-8")
    assert "conflicts: 1" in content
    assert "weak claims: 2" in content  # original + the new conflict claim (0.70)


# ----- Enum-rejection tests (parametrized) -----


def _write_yaml(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _load_evidence_ledger() -> dict:
    return yaml.safe_load((FIXTURE / "evidence_ledger.yml").read_text(encoding="utf-8"))


def _load_cache_manifest() -> dict:
    return yaml.safe_load((FIXTURE / "cache_manifest.yml").read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "field,bad_value,error_marker",
    [
        ("source_type", "not_a_real_source_type", "source_type"),
        ("source_quality", "premium", "source_quality"),
        ("rights_status", "public_domain", "rights_status"),
        ("verification_method", "telepathy", "verification_method"),
    ],
)
def test_evidence_ledger_rejects_bad_enum(
    tmp_path: Path, field: str, bad_value: str, error_marker: str
) -> None:
    data = _load_evidence_ledger()
    data["entries"][0][field] = bad_value
    path = tmp_path / "evidence_ledger.yml"
    _write_yaml(path, data)
    errors = evidence_ledger.validate(path)
    assert any(error_marker in e for e in errors), errors


def test_evidence_ledger_rejects_bad_evidence_role(tmp_path: Path) -> None:
    data = _load_evidence_ledger()
    data["entries"][0]["supports"][0]["evidence_role"] = "not_a_role"
    path = tmp_path / "evidence_ledger.yml"
    _write_yaml(path, data)
    errors = evidence_ledger.validate(path)
    assert any("evidence_role" in e for e in errors), errors


def test_evidence_ledger_rejects_duplicate_evidence_id(tmp_path: Path) -> None:
    data = _load_evidence_ledger()
    dup = copy.deepcopy(data["entries"][0])
    data["entries"].append(dup)
    path = tmp_path / "evidence_ledger.yml"
    _write_yaml(path, data)
    errors = evidence_ledger.validate(path)
    assert any("duplicate evidence_id" in e for e in errors), errors


@pytest.mark.parametrize(
    "field,bad_value,error_marker",
    [
        ("rights_status", "public_domain", "rights_status"),
        ("extraction_status", "kind_of_ok", "extraction_status"),
    ],
)
def test_cache_manifest_rejects_bad_enum(
    tmp_path: Path, field: str, bad_value: str, error_marker: str
) -> None:
    project = tmp_path / "project"
    shutil.copytree(FIXTURE, project)
    path = project / "cache_manifest.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["entries"][0][field] = bad_value
    _write_yaml(path, data)
    errors = cache_manifest.validate(path)
    assert any(error_marker in e for e in errors), errors


def test_cache_manifest_rejects_duplicate_cache_id(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(FIXTURE, project)
    path = project / "cache_manifest.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["entries"].append(copy.deepcopy(data["entries"][0]))
    _write_yaml(path, data)
    errors = cache_manifest.validate(path)
    assert any("duplicate cache_id" in e for e in errors), errors


def _load_claim_graph_records() -> list[dict]:
    return [
        json.loads(line)
        for line in (FIXTURE / "claim_graph.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in records) + "\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    "patch,error_marker",
    [
        ({"target_type": "entity", "field": "entity_type", "value": "lifeform"}, "entity_type"),
        ({"target_type": "claim", "field": "claim_type", "value": "vibes"}, "claim_type"),
        ({"target_type": "claim", "field": "status", "value": "shipped"}, "status"),
        ({"target_type": "*", "field": "record_type", "value": "not_a_record"}, "record_type"),
    ],
)
def test_claim_graph_rejects_bad_enum(
    tmp_path: Path, patch: dict, error_marker: str
) -> None:
    records = _load_claim_graph_records()
    target_type = patch["target_type"]
    for r in records:
        if target_type == "*" or r.get("record_type") == target_type:
            r[patch["field"]] = patch["value"]
            break
    path = tmp_path / "claim_graph.jsonl"
    _write_jsonl(path, records)
    errors = claim_graph.validate(path)
    assert any(error_marker in e for e in errors), errors


def test_claim_graph_rejects_duplicate_record_id(tmp_path: Path) -> None:
    records = _load_claim_graph_records()
    records.append(copy.deepcopy(records[0]))
    path = tmp_path / "claim_graph.jsonl"
    _write_jsonl(path, records)
    errors = claim_graph.validate(path)
    assert any("duplicate id" in e for e in errors), errors


# ----- v3 strict-live tests (schema_version: 3, span-anchored evidence) -----


def test_v3_fixture_passes_all_validators() -> None:
    assert bib_ledger.validate(V3_FIXTURE / "bib_ledger.yml") == []
    assert cache_manifest.validate(V3_FIXTURE / "cache_manifest.yml") == []
    assert evidence_ledger.validate(V3_FIXTURE / "evidence_ledger.yml") == []
    assert claim_graph.validate(V3_FIXTURE / "claim_graph.jsonl") == []
    errors = freshness.validate(V3_FIXTURE, strict=True, today=date(2026, 5, 19))
    assert errors == [], errors


def test_v3_rejects_missing_extraction_method(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(V3_FIXTURE, project)
    path = project / "evidence_ledger.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    del data["entries"][0]["supports"][0]["extraction_method"]
    _write_yaml(path, data)
    errors = evidence_ledger.validate(path)
    assert any("extraction_method" in e for e in errors), errors


def test_v3_rejects_missing_link_confidence(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(V3_FIXTURE, project)
    path = project / "evidence_ledger.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    del data["entries"][0]["supports"][0]["link_confidence"]
    _write_yaml(path, data)
    errors = evidence_ledger.validate(path)
    assert any("link_confidence" in e for e in errors), errors


def test_v3_rejects_link_confidence_above_cap(tmp_path: Path) -> None:
    """paraphrase caps at 0.85; assigning 0.95 must fail."""
    project = tmp_path / "project"
    shutil.copytree(V3_FIXTURE, project)
    path = project / "evidence_ledger.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["entries"][0]["supports"][0]["extraction_method"] = "paraphrase"
    data["entries"][0]["supports"][0]["link_confidence"] = 0.95
    # paraphrase doesn't require excerpt_anchor; remove it so the test isolates
    # the cap-violation error rather than substring failures
    del data["entries"][0]["supports"][0]["excerpt_anchor"]
    _write_yaml(path, data)
    errors = evidence_ledger.validate(path)
    assert any("exceeds cap" in e for e in errors), errors


def test_v3_substring_check_catches_mismatched_excerpt(tmp_path: Path) -> None:
    """If the excerpt doesn't match the bytes at text_path_offset, validation fails."""
    project = tmp_path / "project"
    shutil.copytree(V3_FIXTURE, project)
    path = project / "evidence_ledger.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["entries"][0]["excerpt"] = "completely different text not in the cache"
    _write_yaml(path, data)
    errors = evidence_ledger.validate(path)
    assert any("excerpt does not match span" in e for e in errors), errors


def test_v3_substring_check_catches_wrong_sha(tmp_path: Path) -> None:
    """If sha256_of_span doesn't match actual span bytes, validation fails."""
    project = tmp_path / "project"
    shutil.copytree(V3_FIXTURE, project)
    path = project / "evidence_ledger.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["entries"][0]["supports"][0]["excerpt_anchor"]["sha256_of_span"] = "0" * 64
    _write_yaml(path, data)
    errors = evidence_ledger.validate(path)
    assert any("sha256_of_span" in e for e in errors), errors


def test_v3_llm_inferred_requires_inference_chain(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(V3_FIXTURE, project)
    path = project / "evidence_ledger.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    support = data["entries"][0]["supports"][0]
    support["extraction_method"] = "llm_inferred"
    support["link_confidence"] = 0.50
    del support["excerpt_anchor"]
    # no inference_chain → should fail
    _write_yaml(path, data)
    errors = evidence_ledger.validate(path)
    assert any("inference_chain" in e for e in errors), errors


def test_v3_manual_override_requires_user_note_source(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(V3_FIXTURE, project)
    path = project / "evidence_ledger.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["entries"][0]["supports"][0]["extraction_method"] = "manual_override"
    del data["entries"][0]["supports"][0]["excerpt_anchor"]
    # source_quality remains "primary", not "user_note" → should fail
    _write_yaml(path, data)
    errors = evidence_ledger.validate(path)
    assert any("manual_override" in e and "user_note" in e for e in errors), errors


# ----- Cache manifest revisit-record tests (v2.1.0 Tier-1 #7) -----


def test_cache_manifest_accepts_revisit_record(tmp_path: Path) -> None:
    """A revisit record referring to a real capture entry validates."""
    project = tmp_path / "project"
    shutil.copytree(FIXTURE, project)
    path = project / "cache_manifest.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    original = data["entries"][0]
    data["entries"].append({
        "cache_id": f"{original['cache_id']}_r20260620",
        "source_url": original["source_url"],
        "fetched_at": "2026-06-20",
        "record_type": "revisit",
        "refers_to_cache_id": original["cache_id"],
        "refers_to_fetched_at": original["fetched_at"],
        "revisit_profile": "server-not-modified",
    })
    _write_yaml(path, data)
    errors = cache_manifest.validate(path)
    assert errors == [], errors


def test_cache_manifest_rejects_revisit_pointing_at_unknown_capture(tmp_path: Path) -> None:
    """A revisit record with refers_to_cache_id not in the manifest must fail
    with a closest-match suggestion."""
    project = tmp_path / "project"
    shutil.copytree(FIXTURE, project)
    path = project / "cache_manifest.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    real_capture_id = data["entries"][0]["cache_id"]
    data["entries"].append({
        "cache_id": "cache_revisit_bogus",
        "source_url": "https://example.com/x",
        "fetched_at": "2026-06-20",
        "record_type": "revisit",
        # Typo in refers_to_cache_id — should trigger closest-match hint
        "refers_to_cache_id": real_capture_id + "_TYPO",
        "revisit_profile": "server-not-modified",
    })
    _write_yaml(path, data)
    errors = cache_manifest.validate(path)
    assert any("refers_to_cache_id" in e and "not found" in e for e in errors), errors
    assert any("closest match" in e for e in errors), errors


def test_cache_manifest_rejects_bad_revisit_profile(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(FIXTURE, project)
    path = project / "cache_manifest.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    real_capture_id = data["entries"][0]["cache_id"]
    data["entries"].append({
        "cache_id": "cache_revisit_x",
        "source_url": "https://example.com/x",
        "fetched_at": "2026-06-20",
        "record_type": "revisit",
        "refers_to_cache_id": real_capture_id,
        "revisit_profile": "not_a_real_profile",
    })
    _write_yaml(path, data)
    errors = cache_manifest.validate(path)
    assert any("revisit_profile" in e for e in errors), errors


def test_v2_skills_codify_strict_live_cache_and_export_rules() -> None:
    skills = REPO_ROOT / ".claude" / "skills"
    gather = (skills / "research-gather.md").read_text(encoding="utf-8")
    dataset = (skills / "dataset-gather.md").read_text(encoding="utf-8")
    freshness_skill = (skills / "freshness-audit.md").read_text(encoding="utf-8")
    export_skill = (skills / "research-kb-export.md").read_text(encoding="utf-8")

    for text in (gather, dataset, freshness_skill):
        assert "strict-live" in text.lower()
        assert "cache" in text.lower()
        assert "evidence" in text.lower()
    assert "research-kb" in export_skill
    assert "research_kb_export.py" in export_skill


# ----- v2.2 Phase A: gather_trace.yml (Self-RAG adaptive retrieval) -----


def _load_gather_trace() -> dict:
    return yaml.safe_load(
        (FIXTURE / "gather_trace.yml").read_text(encoding="utf-8")
    )


def test_v22_gather_trace_fixture_validates() -> None:
    assert gather_trace.validate(FIXTURE / "gather_trace.yml") == []


@pytest.mark.parametrize(
    "field,bad_value,error_marker",
    [
        ("decision", "maybe", "decision"),
    ],
)
def test_v22_gather_trace_rejects_bad_decision_enum(
    tmp_path: Path, field: str, bad_value: str, error_marker: str
) -> None:
    data = _load_gather_trace()
    data["fetches"][0][field] = bad_value
    path = tmp_path / "gather_trace.yml"
    _write_yaml(path, data)
    errors = gather_trace.validate(path)
    assert any(error_marker in e for e in errors), errors


def test_v22_gather_trace_rejects_bad_is_supported(tmp_path: Path) -> None:
    data = _load_gather_trace()
    data["fetches"][0]["reflection"]["is_supported"] = "kinda"
    path = tmp_path / "gather_trace.yml"
    _write_yaml(path, data)
    errors = gather_trace.validate(path)
    assert any("is_supported" in e for e in errors), errors


def test_v22_gather_trace_rejects_is_useful_out_of_range(tmp_path: Path) -> None:
    data = _load_gather_trace()
    data["fetches"][0]["reflection"]["is_useful"] = 9
    path = tmp_path / "gather_trace.yml"
    _write_yaml(path, data)
    errors = gather_trace.validate(path)
    assert any("is_useful" in e for e in errors), errors


def test_v22_gather_trace_rejects_accept_without_bibkey(tmp_path: Path) -> None:
    data = _load_gather_trace()
    # first fixture entry is an accept with a bibkey; remove the bibkey
    del data["fetches"][0]["assigned_bibkey"]
    path = tmp_path / "gather_trace.yml"
    _write_yaml(path, data)
    errors = gather_trace.validate(path)
    assert any("accept" in e and "assigned_bibkey" in e for e in errors), errors


def test_v22_gather_trace_rejects_reject_with_bibkey(tmp_path: Path) -> None:
    data = _load_gather_trace()
    # second fixture entry is a reject; add a stray bibkey
    data["fetches"][1]["assigned_bibkey"] = "example2026agentsecurity"
    path = tmp_path / "gather_trace.yml"
    _write_yaml(path, data)
    errors = gather_trace.validate(path)
    assert any("reject" in e and "assigned_bibkey" in e for e in errors), errors


def test_v22_gather_trace_rejects_unknown_bibkey_cross_ref(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(FIXTURE, project)
    path = project / "gather_trace.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["fetches"][0]["assigned_bibkey"] = "nonexistent2099bibkey"
    _write_yaml(path, data)
    errors = gather_trace.validate(path)
    assert any("not found in bib_ledger" in e for e in errors), errors


def test_v22_gather_trace_rejects_duplicate_fetch_id(tmp_path: Path) -> None:
    data = _load_gather_trace()
    data["fetches"].append(copy.deepcopy(data["fetches"][0]))
    path = tmp_path / "gather_trace.yml"
    _write_yaml(path, data)
    errors = gather_trace.validate(path)
    assert any("duplicate fetch_id" in e for e in errors), errors


# ----- v2.2 Phase B: atomic decomposition + pre_selection_manifest -----


def test_v22_atomic_fixture_passes_all_validators() -> None:
    assert bib_ledger.validate(ATOMIC_FIXTURE / "bib_ledger.yml") == []
    assert evidence_ledger.validate(ATOMIC_FIXTURE / "evidence_ledger.yml") == []
    assert cache_manifest.validate(ATOMIC_FIXTURE / "cache_manifest.yml") == []
    assert claim_graph.validate(ATOMIC_FIXTURE / "claim_graph.jsonl") == []
    assert pre_selection_manifest.validate(
        ATOMIC_FIXTURE / "pre_selection_manifest.yml"
    ) == []
    assert freshness.validate(ATOMIC_FIXTURE, strict=True, today=date(2026, 5, 19)) == []


def test_v22_atomic_claim_graph_has_three_atoms() -> None:
    """Builder produces one claim record per atom_id, not one per bullet."""
    records = [
        json.loads(line)
        for line in (ATOMIC_FIXTURE / "claim_graph.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    atom_claims = [
        r for r in records
        if r.get("record_type") == "claim"
        and isinstance(r.get("id"), str)
        and r["id"].startswith("claim_atomic_demo_b1_")
    ]
    assert len(atom_claims) == 3, [r.get("id") for r in atom_claims]
    # Each atom binds to exactly one evidence_id at this scale
    for c in atom_claims:
        assert len(c.get("evidence_ids", [])) == 1, c


def test_v22_pre_selection_manifest_rejects_unknown_atom_id(tmp_path: Path) -> None:
    """The structural anti-hallucination guarantee: pre-selection can't
    commit to an atom_id that doesn't exist in claim_graph."""
    project = tmp_path / "project"
    shutil.copytree(ATOMIC_FIXTURE, project)
    path = project / "pre_selection_manifest.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["selections"][0]["atom_id"] = "claim_does_not_exist"
    _write_yaml(path, data)
    errors = pre_selection_manifest.validate(path)
    assert any("not found among claim records" in e for e in errors), errors


def test_v22_pre_selection_manifest_rejects_bad_sha256(tmp_path: Path) -> None:
    """Substring + sha256 check: tampering with the recorded hash is rejected."""
    project = tmp_path / "project"
    shutil.copytree(ATOMIC_FIXTURE, project)
    path = project / "pre_selection_manifest.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["selections"][0]["span"]["sha256_of_span"] = "0" * 64
    _write_yaml(path, data)
    errors = pre_selection_manifest.validate(path)
    assert any("sha256_of_span" in e for e in errors), errors


def test_v22_pre_selection_manifest_rejects_bad_excerpt(tmp_path: Path) -> None:
    """Excerpt-equality: the manifest's excerpt must match the span bytes."""
    project = tmp_path / "project"
    shutil.copytree(ATOMIC_FIXTURE, project)
    path = project / "pre_selection_manifest.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["selections"][0]["span"]["excerpt"] = "system fabricates ZERO accuracy"
    _write_yaml(path, data)
    errors = pre_selection_manifest.validate(path)
    assert any("excerpt does not match" in e for e in errors), errors


def test_v22_pre_selection_manifest_rejects_unknown_cache_id(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(ATOMIC_FIXTURE, project)
    path = project / "pre_selection_manifest.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["selections"][0]["cache_id"] = "cache_does_not_exist"
    _write_yaml(path, data)
    errors = pre_selection_manifest.validate(path)
    assert any("not found in cache_manifest" in e for e in errors), errors


def test_v22_pre_selection_manifest_rejects_duplicate_selection_id(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(ATOMIC_FIXTURE, project)
    path = project / "pre_selection_manifest.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["selections"].append(copy.deepcopy(data["selections"][0]))
    _write_yaml(path, data)
    errors = pre_selection_manifest.validate(path)
    assert any("duplicate selection_id" in e for e in errors), errors


def test_v22_atomic_dashboard_reports_corroboration_and_strength(tmp_path: Path) -> None:
    """v2.2 dashboard adds corroboration and atom-support-strength metrics
    on v3 fixtures. Atomic fixture should report 100% atoms fully supported,
    0% corroborated (since the demo has just one source per atom)."""
    out = tmp_path / "dashboard.md"
    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "build_dashboard.py"),
            str(ATOMIC_FIXTURE),
            "--output",
            str(out),
            "--today",
            "2026-05-19",
        ],
        check=True,
        capture_output=True,
    )
    text = out.read_text(encoding="utf-8")
    assert "atoms fully supported: 3/3 (100%)" in text, text
    # v2.3 B3: small-N suppression — N<6 gets an annotation, not a percentage.
    assert (
        "corroborated (≥2 independent sources): 0/3 "
        "(corpus too small for synthesis metric — needs ≥6 atoms)"
    ) in text, text


# ---------- v2.3 C2: synthesis_entry attribution wire-up ----------


def _scaffold_synthesis_project(
    base: Path,
    *,
    synthesis_entry_source_urls: list[str] | None = None,
    pre_selection_synthesis_ref: str | None = None,
    attribution_map: dict[str, list[str]] | None = None,
    synthesis_title: str = "Synthesis: emergence is partly artifact",
) -> Path:
    """Build a minimal project dir with one synthesis atom across 3 sources.

    The synthesis claim is ``claim_synthesis_emergence_debate``, supported by
    3 evidence entries from 3 distinct source_urls (Zhao / Schaeffer /
    fragility). Caller customizes the synthesis_entry source_urls and the
    pre_selection_manifest synthesis_entry_ref to exercise drift scenarios.
    """
    import yaml as _yaml
    project = base / "synthesis_project"
    project.mkdir()
    cache_dir = project / "cache"
    cache_dir.mkdir()

    sources = [
        ("https://arxiv.org/abs/2505.01234", "zhao2025distributional"),
        ("https://arxiv.org/abs/2304.15004", "schaeffer2023mirage"),
        ("https://arxiv.org/abs/2502.03200", "fragility2025critique"),
    ]

    # Scaffold cache blobs for verbatim_match anchor verification — minimal,
    # just enough that the cache_manifest validator accepts the project.
    cache_entries = []
    for url, _bibkey in sources:
        body = (
            f"Synthetic test source for {url}. " + "padding " * 100
        ).encode("utf-8")
        digest = hashlib.sha256(body).hexdigest()
        (cache_dir / "blobs" / "sha256").mkdir(parents=True, exist_ok=True)
        (cache_dir / "text" / "sha256").mkdir(parents=True, exist_ok=True)
        (cache_dir / "metadata" / "sha256").mkdir(parents=True, exist_ok=True)
        (cache_dir / "blobs" / "sha256" / digest).write_bytes(body)
        (cache_dir / "text" / "sha256" / f"{digest}.txt").write_text(
            body.decode("utf-8"), encoding="utf-8"
        )
        (cache_dir / "metadata" / "sha256" / f"{digest}.json").write_text(
            json.dumps({"sha256": digest}, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        cache_entries.append({
            "cache_id": f"cache_{digest[:16]}",
            "source_url": url,
            "fetched_at": "2026-05-23",
            "content_type": "text/html",
            "bytes": len(body),
            "sha256": digest,
            "raw_path": f"blobs/sha256/{digest}",
            "text_path": f"text/sha256/{digest}.txt",
            "metadata_path": f"metadata/sha256/{digest}.json",
            "restricted": False,
            "rights_status": "private_use",
            "extraction_status": "ok",
        })

    (project / "cache_manifest.yml").write_text(
        _yaml.safe_dump({
            "schema_version": 2,
            "topic": "synthesis_test",
            "generated_at": "2026-05-23",
            "current_as_of": "2026-05-23",
            "freshness_policy": "strict_live",
            "cache_root": "./cache",
            "entries": cache_entries,
        }, sort_keys=False),
        encoding="utf-8",
    )

    # bib_ledger with 3 entries that each reference one evidence_id
    bib_entries = []
    for (url, bibkey), ev_id in zip(
        sources,
        ["ev_zhao_distributional", "ev_schaeffer_mirage", "ev_fragility_critique"],
    ):
        bib_entries.append({
            "bibkey": bibkey,
            "title": f"Synthetic paper {bibkey}",
            "primary_url": url,
            "claim_family": "paper",
            "status": "verified",
            "evidence_ids": [ev_id],
        })
    (project / "bib_ledger.yml").write_text(
        _yaml.safe_dump({
            "schema_version": 3,
            "topic": "synthesis_test",
            "generated_at": "2026-05-23",
            "current_as_of": "2026-05-23",
            "freshness_policy": "strict_live",
            "claim_family_taxonomy": ["paper"],
            "entries": bib_entries,
        }, sort_keys=False),
        encoding="utf-8",
    )

    # evidence_ledger with 3 supports all pointing at the synthesis claim
    ev_entries = []
    for (url, bibkey), ev_id, cache_e in zip(
        sources,
        ["ev_zhao_distributional", "ev_schaeffer_mirage", "ev_fragility_critique"],
        cache_entries,
    ):
        ev_entries.append({
            "evidence_id": ev_id,
            "source_url": url,
            "source_type": "paper",
            "source_quality": "primary",
            "retrieved_at": "2026-05-23",
            "verification_method": "webfetch",
            "cache_ids": [cache_e["cache_id"]],
            "supports": [{
                "claim_id": "claim_synthesis_emergence_debate",
                "field_path": "agent_index/0K_test.md#emergence",
                "evidence_role": "supports",
                "evidence_role_strength": "full",
                "extraction_method": "paraphrase",
                "link_confidence": 0.7,
            }],
            "excerpt": f"Excerpt from {bibkey} on emergence as measurement artifact",
            "rights_status": "private_use",
        })
    (project / "evidence_ledger.yml").write_text(
        _yaml.safe_dump({
            "schema_version": 3,
            "topic": "synthesis_test",
            "generated_at": "2026-05-23",
            "current_as_of": "2026-05-23",
            "freshness_policy": "strict_live",
            "entries": ev_entries,
        }, sort_keys=False),
        encoding="utf-8",
    )

    # Optional: synthesis_entry.yml
    if synthesis_entry_source_urls is not None:
        synth_entry: dict[str, Any] = {
            "synthesis_id": "syn_synthesis_test_emergence_debate",
            "source_urls": synthesis_entry_source_urls,
            "title": synthesis_title,
            "claim_family": "paper",
            "volatility": "evolving",
            "tier_summary": "T1: 3, T2: 0, T3: 0",
            "status": "verified",
        }
        if attribution_map:
            synth_entry["attribution_map"] = attribution_map
        (project / "synthesis_entry.yml").write_text(
            _yaml.safe_dump({
                "schema_version": 2,
                "topic": "synthesis_test",
                "generated_at": "2026-05-23",
                "current_as_of": "2026-05-23",
                "freshness_policy": "strict_live",
                "entries": [synth_entry],
            }, sort_keys=False),
            encoding="utf-8",
        )

    # Optional: pre_selection_manifest with synthesis_entry_ref
    if pre_selection_synthesis_ref is not None:
        first_cache = cache_entries[0]
        sha256_of_span = hashlib.sha256(
            f"Synthetic test source for {sources[0][0]}. "
            .encode("utf-8")[:40]
        ).hexdigest()
        (project / "pre_selection_manifest.yml").write_text(
            _yaml.safe_dump({
                "schema_version": 3,
                "topic": "synthesis_test",
                "generated_at": "2026-05-23",
                "current_as_of": "2026-05-23",
                "freshness_policy": "strict_live",
                "selections": [{
                    "selection_id": "sel_synth_b1_a1",
                    "bullet_id": "B1",
                    "atom_id": "claim_synthesis_emergence_debate",
                    "cache_id": first_cache["cache_id"],
                    "synthesis_entry_ref": pre_selection_synthesis_ref,
                    "span": {
                        "text_path_offset": [0, 40],
                        "sha256_of_span": sha256_of_span,
                        "excerpt": f"Synthetic test source for {sources[0][0]}.",
                    },
                }],
            }, sort_keys=False),
            encoding="utf-8",
        )
    return project


def _run_build_claim_graph(project: Path, out: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "build_claim_graph.py"),
            str(project),
            "--output",
            str(out),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )


def test_v23_c2_synthesis_entry_ref_resolves_attribution(tmp_path: Path) -> None:
    """Happy path: synthesis_entry_ref + matching source_urls + attribution_map
    → claim text comes from attribution_map; synthesis_entry_id surfaces on
    the claim record."""
    project = _scaffold_synthesis_project(
        tmp_path,
        synthesis_entry_source_urls=[
            "https://arxiv.org/abs/2505.01234",
            "https://arxiv.org/abs/2304.15004",
            "https://arxiv.org/abs/2502.03200",
        ],
        pre_selection_synthesis_ref="syn_synthesis_test_emergence_debate",
        attribution_map={
            "Excerpt from zhao2025distributional on emergence as measurement artifact": [
                "https://arxiv.org/abs/2505.01234",
            ],
            "Emergence is partly an artifact of measurement choices": [
                "https://arxiv.org/abs/2505.01234",
                "https://arxiv.org/abs/2304.15004",
            ],
        },
    )
    out = tmp_path / "cg.jsonl"
    result = _run_build_claim_graph(project, out)
    assert result.returncode == 0, result.stderr

    records = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
    by_id = {r["id"]: r for r in records if r.get("record_type") == "claim"}
    claim = by_id["claim_synthesis_emergence_debate"]
    # Resolved text matches the attribution_map key (longest substring match)
    assert claim["text"] == (
        "Excerpt from zhao2025distributional on emergence as measurement artifact"
    ), claim["text"]
    assert claim["synthesis_entry_id"] == "syn_synthesis_test_emergence_debate"
    assert claim["corroboration_count"] == 3
    # No source_urls mismatch warning in stderr
    assert "source_urls mismatch" not in result.stderr


def test_v23_c2_falls_back_to_tiebreak_when_no_ref(tmp_path: Path) -> None:
    """No pre_selection_manifest at all → existing v2.2 tiebreak behavior.
    No synthesis_entry_id on the claim record."""
    project = _scaffold_synthesis_project(
        tmp_path,
        synthesis_entry_source_urls=None,
        pre_selection_synthesis_ref=None,
    )
    out = tmp_path / "cg.jsonl"
    result = _run_build_claim_graph(project, out)
    assert result.returncode == 0, result.stderr

    records = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
    by_id = {r["id"]: r for r in records if r.get("record_type") == "claim"}
    claim = by_id["claim_synthesis_emergence_debate"]
    # Text is one of the contributing-source excerpts (longest-excerpt tiebreak)
    assert claim["text"].startswith("Excerpt from "), claim["text"]
    assert "synthesis_entry_id" not in claim


def test_v23_c2_source_url_mismatch_warns(tmp_path: Path) -> None:
    """When synthesis_entry.source_urls drift from the supporting evidence's
    source_urls, a WARN is printed to stderr but the build succeeds (curation
    signal, not structural error)."""
    project = _scaffold_synthesis_project(
        tmp_path,
        synthesis_entry_source_urls=[
            "https://arxiv.org/abs/2505.01234",
            "https://arxiv.org/abs/9999.99999",  # NOT in supporting evidence
            "https://arxiv.org/abs/2502.03200",
        ],
        pre_selection_synthesis_ref="syn_synthesis_test_emergence_debate",
    )
    out = tmp_path / "cg.jsonl"
    result = _run_build_claim_graph(project, out)
    assert result.returncode == 0, result.stderr
    assert "source_urls mismatch" in result.stderr, result.stderr
    assert "9999.99999" in result.stderr or "2304.15004" in result.stderr


def test_v23_c2_dangling_ref_warns_and_falls_back(tmp_path: Path) -> None:
    """pre_selection_manifest references a synthesis_id that doesn't exist in
    synthesis_entry.yml → WARN + fall back to tiebreak."""
    project = _scaffold_synthesis_project(
        tmp_path,
        synthesis_entry_source_urls=[
            "https://arxiv.org/abs/2505.01234",
            "https://arxiv.org/abs/2304.15004",
            "https://arxiv.org/abs/2502.03200",
        ],
        pre_selection_synthesis_ref="syn_does_not_exist",
    )
    out = tmp_path / "cg.jsonl"
    result = _run_build_claim_graph(project, out)
    assert result.returncode == 0, result.stderr
    assert "not found in synthesis_entry.yml" in result.stderr, result.stderr

    records = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
    by_id = {r["id"]: r for r in records if r.get("record_type") == "claim"}
    claim = by_id["claim_synthesis_emergence_debate"]
    assert "synthesis_entry_id" not in claim
    assert claim["text"].startswith("Excerpt from "), claim["text"]


def test_v23_c2_no_attribution_map_uses_title(tmp_path: Path) -> None:
    """When synthesis_entry has no attribution_map (only title), claim text
    falls back to the synthesis title."""
    project = _scaffold_synthesis_project(
        tmp_path,
        synthesis_entry_source_urls=[
            "https://arxiv.org/abs/2505.01234",
            "https://arxiv.org/abs/2304.15004",
            "https://arxiv.org/abs/2502.03200",
        ],
        pre_selection_synthesis_ref="syn_synthesis_test_emergence_debate",
        attribution_map=None,
        synthesis_title="Synthesis claim about emergence and measurement",
    )
    out = tmp_path / "cg.jsonl"
    result = _run_build_claim_graph(project, out)
    assert result.returncode == 0, result.stderr

    records = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
    by_id = {r["id"]: r for r in records if r.get("record_type") == "claim"}
    claim = by_id["claim_synthesis_emergence_debate"]
    assert claim["text"] == "Synthesis claim about emergence and measurement"
    assert claim["synthesis_entry_id"] == "syn_synthesis_test_emergence_debate"


def test_v23_c2_pre_selection_validator_rejects_bad_ref_pattern(tmp_path: Path) -> None:
    """The pre_selection_manifest validator rejects synthesis_entry_ref values
    that don't start with 'syn_'."""
    from validators import pre_selection_manifest as psm
    import yaml as _yaml
    manifest = tmp_path / "pre_selection_manifest.yml"
    manifest.write_text(_yaml.safe_dump({
        "schema_version": 3,
        "topic": "test",
        "generated_at": "2026-05-23",
        "current_as_of": "2026-05-23",
        "freshness_policy": "strict_live",
        "selections": [{
            "selection_id": "sel_1",
            "bullet_id": "B1",
            "atom_id": "claim_test_b1_a1",
            "cache_id": "cache_xxx",
            "synthesis_entry_ref": "not_a_syn_prefix",
            "span": {
                "text_path_offset": [0, 10],
                "sha256_of_span": "a" * 64,
                "excerpt": "hello",
            },
        }],
    }), encoding="utf-8")
    errors = psm.validate(manifest)
    assert any("synthesis_entry_ref" in e and "syn_" in e for e in errors), errors


# ---------- v2.3 B3: dashboard small-N corroboration suppression ----------


def _scaffold_dashboard_project_with_n_claims(base: Path, n: int) -> Path:
    """Minimal v3 project with N single-source claims for B3 testing.

    Each claim has 1 source_url so corroboration_count=1. With N=6 the
    dashboard reports `0/6 (0%)` (the percentage branch); with N<6 it
    annotates "(corpus too small...)".
    """
    import yaml as _yaml
    project = base / f"dashboard_n{n}_project"
    project.mkdir()

    bib_entries = []
    ev_entries = []
    for i in range(n):
        bibkey = f"bib{i:02d}"
        url = f"https://example.com/paper{i:02d}"
        ev_id = f"ev_{i:02d}"
        claim_id = f"claim_test_atom{i:02d}"
        bib_entries.append({
            "bibkey": bibkey,
            "title": f"Test paper {i}",
            "primary_url": url,
            "claim_family": "paper",
            "status": "verified",
            "evidence_ids": [ev_id],
        })
        ev_entries.append({
            "evidence_id": ev_id,
            "source_url": url,
            "source_type": "paper",
            "source_quality": "primary",
            "retrieved_at": "2026-05-23",
            "verification_method": "webfetch",
            "supports": [{
                "claim_id": claim_id,
                "field_path": "agent_index/0K_test.md",
                "evidence_role": "supports",
                "evidence_role_strength": "full",
                "extraction_method": "paraphrase",
                "link_confidence": 0.7,
            }],
            "excerpt": f"Excerpt from paper {i}",
            "rights_status": "private_use",
        })

    (project / "bib_ledger.yml").write_text(
        _yaml.safe_dump({
            "schema_version": 3,
            "topic": "b3_test",
            "generated_at": "2026-05-23",
            "current_as_of": "2026-05-23",
            "freshness_policy": "strict_live",
            "claim_family_taxonomy": ["paper"],
            "entries": bib_entries,
        }, sort_keys=False),
        encoding="utf-8",
    )
    (project / "evidence_ledger.yml").write_text(
        _yaml.safe_dump({
            "schema_version": 3,
            "topic": "b3_test",
            "generated_at": "2026-05-23",
            "current_as_of": "2026-05-23",
            "freshness_policy": "strict_live",
            "entries": ev_entries,
        }, sort_keys=False),
        encoding="utf-8",
    )
    return project


def test_v23_b3_corroboration_annotated_at_small_n(tmp_path: Path) -> None:
    """N<6 atoms → corroboration line is annotated, not a percentage."""
    project = _scaffold_dashboard_project_with_n_claims(tmp_path, n=4)
    out = tmp_path / "dash.md"
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "build_dashboard.py"),
            str(project),
            "--output",
            str(out),
            "--today",
            "2026-05-23",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr
    text = out.read_text(encoding="utf-8")
    assert (
        "corroborated (≥2 independent sources): 0/4 "
        "(corpus too small for synthesis metric — needs ≥6 atoms)"
    ) in text, text


def test_v23_b3_corroboration_percentage_at_n6plus(tmp_path: Path) -> None:
    """N>=6 atoms → corroboration line reverts to the percentage form."""
    project = _scaffold_dashboard_project_with_n_claims(tmp_path, n=6)
    out = tmp_path / "dash.md"
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "build_dashboard.py"),
            str(project),
            "--output",
            str(out),
            "--today",
            "2026-05-23",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr
    text = out.read_text(encoding="utf-8")
    assert "corroborated (≥2 independent sources): 0/6 (0%)" in text, text
    # And the small-N annotation does NOT appear at N=6
    assert "corpus too small" not in text, text

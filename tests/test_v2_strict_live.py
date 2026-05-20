"""Strict-live v2 validators and fixtures."""
from __future__ import annotations

import copy
from datetime import date
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
import yaml

from validators import bib_ledger, dataset_ledger
from validators import cache_manifest, claim_graph, evidence_ledger, freshness, research_kb_export

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "v2_strict_live_ai_agents"
MULTI_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "v2_strict_live_multi_entry"
V3_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "v3_strict_live_demo"


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

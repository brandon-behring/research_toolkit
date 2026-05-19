"""Strict-live v2 validators and fixtures."""
from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import shutil
import subprocess
import sys

from validators import bib_ledger, dataset_ledger
from validators import cache_manifest, claim_graph, evidence_ledger, freshness, research_kb_export

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "v2_strict_live_ai_agents"


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

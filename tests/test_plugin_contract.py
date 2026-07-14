"""Tests for the clean-break Claude plugin surface."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPECTED_SKILLS = {
    "audit",
    "dataset-research",
    "freshness",
    "release",
    "research",
    "topic-discovery",
}


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    _, block, _ = text.split("---", 2)
    value = yaml.safe_load(block)
    assert isinstance(value, dict)
    return value


def test_plugin_manifest_names_research_toolkit() -> None:
    manifest = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["name"] == "research-toolkit"
    assert manifest["version"] == "3.0.0-alpha.1"


def test_plugin_exposes_exactly_six_namespaced_skills() -> None:
    skill_paths = sorted((REPO_ROOT / "skills").glob("*/SKILL.md"))
    assert {path.parent.name for path in skill_paths} == EXPECTED_SKILLS
    assert len(skill_paths) == 6
    for path in skill_paths:
        metadata = _frontmatter(path)
        assert metadata["name"] == path.parent.name
        assert metadata["description"]


def test_plugin_skills_use_portable_resource_paths() -> None:
    for path in (REPO_ROOT / "skills").glob("*/SKILL.md"):
        text = path.read_text(encoding="utf-8")
        assert "${CLAUDE_PLUGIN_ROOT}" in text
        assert "~/Claude/research_toolkit" not in text


def test_decision_protocol_is_self_contained() -> None:
    protocol = (REPO_ROOT / "references" / "decision_protocol.md").read_text()
    assert "do not require a personal `/exploring-options` installation" in protocol
    for name in ("research", "dataset-research", "topic-discovery"):
        text = (REPO_ROOT / "skills" / name / "SKILL.md").read_text()
        assert "decision_protocol.md" in text


def test_legacy_flat_skill_directory_has_no_skill_bodies() -> None:
    assert not list((REPO_ROOT / ".claude" / "skills").glob("*.md"))

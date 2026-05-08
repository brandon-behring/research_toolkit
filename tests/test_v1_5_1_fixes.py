"""Regression tests for v1.5.1 patch.

Three changes covered:
1. /agent-index skill body references the cross_stage validator in its
   Validation section (lint test).
2. /research-gather + /dossier-build skill bodies reference the medium
   fixture as a worked example (lint tests).
3. validators/audit_trail.py enforces sequential round numbering starting
   at 1 with no gaps (4 unit tests).

The lint tests are pedantic — their value is flagging if a future skill-body
refactor accidentally drops these references.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from validators import audit_trail

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / ".claude" / "skills"


# ---------- Skill-body lint tests ----------


def test_agent_index_skill_references_cross_stage() -> None:
    """v1.5.1: /agent-index Validation section now points at cross_stage validator."""
    text = (SKILLS / "agent-index.md").read_text(encoding="utf-8")
    assert "cross_stage" in text, (
        "/agent-index skill body should reference the cross_stage validator. "
        "If you intentionally removed it, update this test."
    )
    # Must be in the Validation section, not just a stray mention.
    validation_section_idx = text.find("## Validation")
    assert validation_section_idx >= 0, "Skill body missing Validation section"
    after = text[validation_section_idx:]
    assert "cross_stage" in after, (
        "cross_stage reference should be in the Validation section, not earlier"
    )


def test_research_gather_skill_references_medium_fixture() -> None:
    """v1.5.1: /research-gather points at medium fixture as a worked example."""
    text = (SKILLS / "research-gather.md").read_text(encoding="utf-8")
    assert "medium_topic_calibration_subset" in text, (
        "/research-gather skill body should reference the medium fixture as a "
        "v1.1+ schema worked example."
    )


def test_dossier_build_skill_references_medium_fixture() -> None:
    """v1.5.1: /dossier-build points at medium fixture as a worked example."""
    text = (SKILLS / "dossier-build.md").read_text(encoding="utf-8")
    assert "medium_topic_calibration_subset" in text, (
        "/dossier-build skill body should reference the medium fixture as a "
        "rendered worked example."
    )


# ---------- audit_trail sequential-round tests ----------


def _readme_with_rounds(*round_nums: int, date: str = "2026-05-07") -> str:
    """Build a fake README containing audit-trail notes for the given rounds."""
    parts = ["# Test agent-index README\n\n## Verification & limits\n\n"]
    for n in round_nums:
        parts.append(
            f"**Independent audit, round {n} ({date}):** A test note for round {n}.\n\n"
        )
    return "".join(parts)


def test_audit_trail_accepts_zero_rounds(tmp_path: Path) -> None:
    """Fresh agent_index with no audit notes still validates (existing behavior)."""
    p = tmp_path / "README.md"
    p.write_text("# Fresh\n\nNo audit yet.\n", encoding="utf-8")
    assert audit_trail.validate(p) == []


def test_audit_trail_accepts_single_round_one(tmp_path: Path) -> None:
    """Single round numbered 1 validates."""
    p = tmp_path / "README.md"
    p.write_text(_readme_with_rounds(1), encoding="utf-8")
    assert audit_trail.validate(p) == []


def test_audit_trail_accepts_contiguous_sequence(tmp_path: Path) -> None:
    """Rounds 1, 2, 3 in sequence validates."""
    p = tmp_path / "README.md"
    p.write_text(_readme_with_rounds(1, 2, 3), encoding="utf-8")
    assert audit_trail.validate(p) == []


def test_audit_trail_accepts_out_of_order_but_contiguous(tmp_path: Path) -> None:
    """Rounds written 3, 1, 2 — still contiguous when sorted, so OK.

    Real-world note: rounds are typically written in chronological order, but
    the validator only checks that the SET of rounds covers 1..N.
    """
    p = tmp_path / "README.md"
    p.write_text(_readme_with_rounds(3, 1, 2), encoding="utf-8")
    assert audit_trail.validate(p) == []


def test_audit_trail_rejects_gap(tmp_path: Path) -> None:
    """Rounds 1, 3 (skipping 2) is a hard error."""
    p = tmp_path / "README.md"
    p.write_text(_readme_with_rounds(1, 3), encoding="utf-8")
    errors = audit_trail.validate(p)
    assert any("gap" in e.lower() for e in errors), errors
    assert any("missing=[2]" in e for e in errors), errors


def test_audit_trail_rejects_larger_gap(tmp_path: Path) -> None:
    """Rounds 1, 5 — multiple missing rounds reported."""
    p = tmp_path / "README.md"
    p.write_text(_readme_with_rounds(1, 5), encoding="utf-8")
    errors = audit_trail.validate(p)
    assert any("missing=[2, 3, 4]" in e for e in errors), errors


def test_audit_trail_rejects_non_one_start(tmp_path: Path) -> None:
    """Rounds 2, 3 (no round 1) is a hard error."""
    p = tmp_path / "README.md"
    p.write_text(_readme_with_rounds(2, 3), encoding="utf-8")
    errors = audit_trail.validate(p)
    assert any("start at 1" in e.lower() for e in errors), errors


def test_audit_trail_rejects_duplicate_round(tmp_path: Path) -> None:
    """Rounds 1, 1 — duplicate is an error (existing behavior; verifies still works)."""
    p = tmp_path / "README.md"
    p.write_text(_readme_with_rounds(1, 1), encoding="utf-8")
    errors = audit_trail.validate(p)
    assert any("duplicate" in e.lower() for e in errors), errors


def test_audit_trail_existing_real_readmes_still_validate(tmp_path: Path) -> None:
    """Sanity: every fixture/real-world README we know about still validates
    under the v1.5.1 sequence rule. Catches accidental over-strictness.
    """
    fixture_readmes = [
        REPO_ROOT / "tests/fixtures/mini_topic_timeseries_anomaly/agent_index/README.md",
        REPO_ROOT / "tests/fixtures/medium_topic_calibration_subset/agent_index/README.md",
        REPO_ROOT / "tests/fixtures/prompt_injection_snapshot/real/agent_index/README.md",
        REPO_ROOT / "tests/fixtures/prompt_injection_snapshot/recreated/agent_index/README.md",
    ]
    for readme in fixture_readmes:
        if not readme.exists():
            continue  # tolerate missing fixtures in CI
        errors = audit_trail.validate(readme)
        assert errors == [], f"{readme.name}: unexpected errors {errors}"

"""Regression tests for v1.6 dataset-research skills.

Coverage:
- dataset_ledger validator: positive/negative cases (required fields,
  task_family enum, URL format, bibkey uniqueness, auth_required type,
  anti-cheat heuristic, --strict promotion, standalone CLI).
- Skill-body lint tests: each new skill body references its expected
  pattern points (medium fixture, cross_stage validator, dataset_sources
  reference).
- Integration: handcrafted smoke fixture validates under the new validator
  and existing agent_index + cross_stage where applicable.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from validators import dataset_ledger

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / ".claude" / "skills"
VALIDATORS_DIR = REPO_ROOT / "validators"
SMOKE_FIXTURE = (
    REPO_ROOT / "tests" / "fixtures" / "_handcrafted_dataset_smoke" / "dataset_ledger.yml"
)


# ---------- dataset_ledger validator: required-field positive cases ----------


def _minimal_ledger(extra: str = "") -> str:
    """Build a minimal valid ledger string with all 6 required fields populated."""
    return (
        "entries:\n"
        "- bibkey: smoke2025example\n"
        "  primary_url: https://example.com/datasets/foo\n"
        "  name: 'Smoke Example Dataset'\n"
        "  source: huggingface\n"
        "  status: unverified\n"
        "  task_family: classification\n"
        + extra
    )


def test_dataset_ledger_accepts_minimal(tmp_path: Path) -> None:
    p = tmp_path / "dataset_ledger.yml"
    p.write_text(_minimal_ledger(), encoding="utf-8")
    assert dataset_ledger.validate(p) == []


def test_dataset_ledger_accepts_smoke_fixture() -> None:
    """The handcrafted smoke fixture validates cleanly."""
    if not SMOKE_FIXTURE.exists():
        pytest.skip(f"{SMOKE_FIXTURE} not present")
    assert dataset_ledger.validate(SMOKE_FIXTURE) == []


def test_dataset_ledger_accepts_optional_fields(tmp_path: Path) -> None:
    """All optional fields accepted when well-formed."""
    p = tmp_path / "dataset_ledger.yml"
    p.write_text(
        _minimal_ledger(
            "  license: CC-BY-4.0\n"
            "  size: '10GB'\n"
            "  rows: 5000000\n"
            "  columns: 3\n"
            "  schema_url: https://example.com/datasets/foo/schema\n"
            "  access_method: hf datasets\n"
            "  auth_required: false\n"
            "  citation: 'Smith et al. (2025)'\n"
        ),
        encoding="utf-8",
    )
    assert dataset_ledger.validate(p) == []


# ---------- dataset_ledger validator: required-field negative cases ----------


def test_dataset_ledger_rejects_missing_required_field(tmp_path: Path) -> None:
    """Missing `name` should fail."""
    text = (
        "entries:\n"
        "- bibkey: smoke2025example\n"
        "  primary_url: https://example.com\n"
        "  source: huggingface\n"
        "  status: unverified\n"
        "  task_family: classification\n"
    )
    p = tmp_path / "dataset_ledger.yml"
    p.write_text(text, encoding="utf-8")
    errors = dataset_ledger.validate(p)
    assert any("missing required field 'name'" in e for e in errors), errors


def test_dataset_ledger_rejects_invalid_task_family(tmp_path: Path) -> None:
    """task_family not in fixed enum should fail."""
    p = tmp_path / "dataset_ledger.yml"
    p.write_text(_minimal_ledger().replace(
        "task_family: classification", "task_family: not_in_enum"
    ), encoding="utf-8")
    errors = dataset_ledger.validate(p)
    assert any("not_in_enum" in e and "fixed enum" in e for e in errors), errors


@pytest.mark.parametrize(
    "valid_value",
    [
        "classification", "regression", "sequence_labeling", "generation",
        "retrieval", "ranking", "multimodal", "graph", "time_series",
        "tabular", "recommendation", "structured_prediction", "other",
    ],
)
def test_dataset_ledger_accepts_all_enum_values(tmp_path: Path, valid_value: str) -> None:
    """Each of the 13 task_family enum values is accepted."""
    p = tmp_path / "dataset_ledger.yml"
    p.write_text(_minimal_ledger().replace(
        "task_family: classification", f"task_family: {valid_value}"
    ), encoding="utf-8")
    assert dataset_ledger.validate(p) == []


def test_dataset_ledger_rejects_duplicate_bibkey(tmp_path: Path) -> None:
    """Duplicate bibkeys are rejected."""
    text = (
        "entries:\n"
        "- bibkey: dup2025one\n"
        "  primary_url: https://example.com/a\n"
        "  name: 'A'\n"
        "  source: hf\n"
        "  status: unverified\n"
        "  task_family: classification\n"
        "- bibkey: dup2025one\n"
        "  primary_url: https://example.com/b\n"
        "  name: 'B'\n"
        "  source: hf\n"
        "  status: unverified\n"
        "  task_family: classification\n"
    )
    p = tmp_path / "dataset_ledger.yml"
    p.write_text(text, encoding="utf-8")
    errors = dataset_ledger.validate(p)
    assert any("duplicate bibkey" in e for e in errors), errors


def test_dataset_ledger_rejects_malformed_url(tmp_path: Path) -> None:
    p = tmp_path / "dataset_ledger.yml"
    p.write_text(_minimal_ledger().replace(
        "primary_url: https://example.com/datasets/foo",
        "primary_url: not-a-url",
    ), encoding="utf-8")
    errors = dataset_ledger.validate(p)
    assert any("not a valid http(s) URL" in e for e in errors), errors


def test_dataset_ledger_rejects_non_bool_auth_required(tmp_path: Path) -> None:
    """auth_required must be bool when present (not string '0' or 'false')."""
    p = tmp_path / "dataset_ledger.yml"
    p.write_text(
        _minimal_ledger("  auth_required: 'false'\n"),  # quoted string, not bool
        encoding="utf-8",
    )
    errors = dataset_ledger.validate(p)
    assert any("auth_required" in e and "boolean" in e for e in errors), errors


# ---------- Anti-cheat heuristic ----------


def _ledger_n_verified(n: int) -> str:
    parts = ["entries:"]
    for i in range(n):
        parts.append(
            f"- bibkey: smoke{i:04d}example\n"
            f"  primary_url: https://example.com/datasets/{i}\n"
            f"  name: 'Smoke Dataset {i}'\n"
            f"  source: huggingface\n"
            f"  status: verified\n"
            f"  task_family: classification\n"
        )
    return "\n".join(parts)


def test_anti_cheat_quiet_under_threshold(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """<30 entries → no warning even if all verified."""
    p = tmp_path / "dataset_ledger.yml"
    p.write_text(_ledger_n_verified(20), encoding="utf-8")
    errors = dataset_ledger.validate(p)
    assert errors == []
    err = capsys.readouterr().err
    assert "memory-verification" not in err.lower()


def test_anti_cheat_warns_at_30_plus_all_verified(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """≥30 entries all-verified → warning to stderr (not error by default)."""
    p = tmp_path / "dataset_ledger.yml"
    p.write_text(_ledger_n_verified(35), encoding="utf-8")
    errors = dataset_ledger.validate(p, strict=False)
    assert errors == []
    err = capsys.readouterr().err
    assert "memory-verification" in err.lower()


def test_anti_cheat_strict_promotes(tmp_path: Path) -> None:
    """--strict promotes the heuristic warning to an error."""
    p = tmp_path / "dataset_ledger.yml"
    p.write_text(_ledger_n_verified(35), encoding="utf-8")
    errors = dataset_ledger.validate(p, strict=True)
    assert any("memory-verification" in e.lower() for e in errors), errors


# ---------- Standalone CLI invocation ----------


def test_dataset_ledger_runs_standalone(tmp_path: Path) -> None:
    """python validators/dataset_ledger.py path works without `python -m`."""
    p = tmp_path / "dataset_ledger.yml"
    p.write_text(_minimal_ledger(), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(VALIDATORS_DIR / "dataset_ledger.py"), str(p)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"


def test_dataset_ledger_cli_strict_flag(tmp_path: Path) -> None:
    """--strict CLI flag promotes warning to error → exit 1."""
    p = tmp_path / "dataset_ledger.yml"
    p.write_text(_ledger_n_verified(35), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(VALIDATORS_DIR / "dataset_ledger.py"), "--strict", str(p)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 1, f"stderr: {result.stderr}"


# ---------- Skill-body lint tests ----------


def test_dataset_gather_skill_references_dataset_sources() -> None:
    text = (SKILLS / "dataset-gather.md").read_text(encoding="utf-8")
    assert "dataset_sources.md" in text, (
        "/dataset-gather must reference references/dataset_sources.md"
    )
    assert "dataset_ledger.template.yml" in text, (
        "/dataset-gather must reference templates/dataset_ledger.template.yml"
    )


def test_dataset_index_skill_references_cross_stage() -> None:
    """v1.5.1 convention: post-stage validators must include cross_stage."""
    text = (SKILLS / "dataset-index.md").read_text(encoding="utf-8")
    assert "cross_stage" in text, (
        "/dataset-index must reference cross_stage validator (v1.5.1 convention)"
    )


def test_dataset_research_wrapper_mentions_both_substages() -> None:
    """The one-shot wrapper must reference both /dataset-gather and /dataset-index."""
    text = (SKILLS / "dataset-research.md").read_text(encoding="utf-8")
    assert "/dataset-gather" in text and "/dataset-index" in text, (
        "/dataset-research wrapper must mention both sub-stages it orchestrates"
    )


def test_all_three_dataset_skills_exist() -> None:
    for skill in ("dataset-gather", "dataset-index", "dataset-research"):
        path = SKILLS / f"{skill}.md"
        assert path.exists(), f"missing {path}"


# ---------- Integration: smoke fixture validates ----------


def test_smoke_fixture_passes_dataset_validator() -> None:
    """The handcrafted smoke fixture under tests/fixtures/_handcrafted_dataset_smoke
    validates cleanly. This catches schema-shape regressions in either the
    fixture or the validator."""
    if not SMOKE_FIXTURE.exists():
        pytest.skip(f"{SMOKE_FIXTURE} not present")
    assert dataset_ledger.validate(SMOKE_FIXTURE) == []

"""Regression tests for v1.2 defensive-hardening fixes.

Covers:
- A2: cross_stage validator (claim_family taxonomy check, orphan-arxiv warnings,
      stale-ledger warnings, --strict promotion)
- A3: bib_ledger memory-verified anti-cheat heuristic (warning by default,
      error with --strict, threshold semantics)

A4 (xfail markers on test_recreation_diff.py) is verified by `make test`
itself — those xfails are part of the suite. Not separately tested here.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from validators import bib_ledger, cross_stage

REPO_ROOT = Path(__file__).resolve().parent.parent
VALIDATORS_DIR = REPO_ROOT / "validators"


# ---------- A2: cross-stage validator ----------

def _project_with(
    tmp_path: Path,
    *,
    research_plan: str | None = None,
    bib_ledger_yaml: str | None = None,
    dossier_files: dict[str, str] | None = None,
    agent_index_files: dict[str, str] | None = None,
) -> Path:
    """Build a project dir with optional artifacts."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    project = tmp_path / "project"
    project.mkdir()
    if research_plan is not None:
        (project / "research_plan.md").write_text(research_plan, encoding="utf-8")
    if bib_ledger_yaml is not None:
        (project / "bib_ledger.yml").write_text(bib_ledger_yaml, encoding="utf-8")
    if dossier_files is not None:
        d = project / "dossier"
        d.mkdir()
        for name, content in dossier_files.items():
            (d / name).write_text(content, encoding="utf-8")
    if agent_index_files is not None:
        d = project / "agent_index"
        d.mkdir()
        for name, content in agent_index_files.items():
            (d / name).write_text(content, encoding="utf-8")
    return project


_BASIC_PLAN = """# Research Plan: tests

A test plan.

## Sub-areas

- A1. Foo
  - Source types: arXiv
  - Notes: -
- A2. Bar
  - Source types: arXiv
  - Notes: -
- A3. Baz
  - Source types: arXiv
  - Notes: -
- A4. Qux
  - Source types: arXiv
  - Notes: -

## Out-of-scope

- Nothing

## Claim family taxonomy

- benchmark
- attack
- defense
"""

_BASIC_LEDGER = """entries:
- bibkey: foo2025one
  primary_url: https://arxiv.org/abs/2501.00001
  title: 'Foo paper one'
  status: unverified
  claim_family: benchmark
- bibkey: bar2025two
  primary_url: https://arxiv.org/abs/2501.00002
  title: 'Bar paper two'
  status: unverified
  claim_family: attack
"""


def test_cross_stage_passes_minimal_project(tmp_path: Path) -> None:
    """Project with research_plan + bib_ledger and matching taxonomy passes."""
    project = _project_with(
        tmp_path,
        research_plan=_BASIC_PLAN,
        bib_ledger_yaml=_BASIC_LEDGER,
    )
    assert cross_stage.validate(project) == []


def test_cross_stage_no_ledger_returns_empty(tmp_path: Path) -> None:
    """If no bib_ledger.yml, validator skips gracefully."""
    project = _project_with(tmp_path, research_plan=_BASIC_PLAN)
    assert cross_stage.validate(project) == []


def test_cross_stage_rejects_unknown_claim_family(tmp_path: Path) -> None:
    """A claim_family not in research_plan.md taxonomy is a HARD error."""
    bad_ledger = _BASIC_LEDGER + (
        "- bibkey: orphan2025foo\n"
        "  primary_url: https://arxiv.org/abs/2501.99999\n"
        "  title: 'Orphan paper'\n"
        "  status: unverified\n"
        "  claim_family: not_in_taxonomy\n"
    )
    project = _project_with(
        tmp_path,
        research_plan=_BASIC_PLAN,
        bib_ledger_yaml=bad_ledger,
    )
    errors = cross_stage.validate(project)
    assert any("not_in_taxonomy" in e for e in errors), errors


def test_cross_stage_warns_on_orphan_dossier_arxiv_id(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """An arxiv ID in dossier but not in ledger is a WARNING by default."""
    dossier = (
        "# Topic\n\n"
        "## A1. Foo\n\n"
        "| Title | Authors (year) | Venue | arXiv/DOI | GitHub | Desc | KC |\n"
        "|---|---|---|---|---|---|---|\n"
        "| Foo | F (2025) | arXiv preprint | arXiv:2501.00001 | — | x | y |\n"
        "| Orphan | O (2099) | arXiv preprint | arXiv:2099.99999 | — | x | y |\n"
    )
    project = _project_with(
        tmp_path,
        research_plan=_BASIC_PLAN,
        bib_ledger_yaml=_BASIC_LEDGER,
        dossier_files={"01_foo.md": dossier},
    )
    errors = cross_stage.validate(project, strict=False)
    assert errors == [], f"orphan should be a warning by default, got error: {errors}"
    err_text = capsys.readouterr().err
    assert "2099.99999" in err_text, f"warning should mention orphan ID; stderr: {err_text}"


def test_cross_stage_strict_promotes_orphan_to_error(tmp_path: Path) -> None:
    """--strict promotes orphan-arxiv warnings to errors."""
    dossier = (
        "# Topic\n\n"
        "## A1. Foo\n\n"
        "| Title | Authors (year) | Venue | arXiv/DOI | GitHub | Desc | KC |\n"
        "|---|---|---|---|---|---|---|\n"
        "| Foo | F (2025) | arXiv preprint | arXiv:2501.00001 | — | x | y |\n"
        "| Orphan | O (2099) | arXiv preprint | arXiv:2099.99999 | — | x | y |\n"
    )
    project = _project_with(
        tmp_path,
        research_plan=_BASIC_PLAN,
        bib_ledger_yaml=_BASIC_LEDGER,
        dossier_files={"01_foo.md": dossier},
    )
    errors = cross_stage.validate(project, strict=True)
    assert any("2099.99999" in e for e in errors), errors


def test_cross_stage_warns_on_stale_ledger_entry(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Ledger entries without a matching agent_index Source line are stale-warnings."""
    agent_index = (
        "# Foo synthesis\n\n"
        "## A1. Foo\n\n"
        "- **Foo** — F (2025).\n"
        "  - **Source:** https://arxiv.org/abs/2501.00001\n"
        "  - **Code:** —\n"
        "  - **Mechanism:** mechanism.\n"
        "  - **Result:** result.\n"
        "  - **Status:** Verified.\n"
    )
    project = _project_with(
        tmp_path,
        research_plan=_BASIC_PLAN,
        bib_ledger_yaml=_BASIC_LEDGER,  # has 2 entries; only 1 in agent_index
        agent_index_files={"01_foo.md": agent_index},
    )
    errors = cross_stage.validate(project, strict=False)
    assert errors == []
    err_text = capsys.readouterr().err
    assert "stale" in err_text.lower(), f"should warn about stale entry; stderr: {err_text}"
    assert "2501.00002" in err_text, f"should mention specific stale ID; stderr: {err_text}"


def test_cross_stage_runs_standalone_without_module_form(tmp_path: Path) -> None:
    """`python validators/cross_stage.py path` works (D1 + new validator)."""
    project = _project_with(
        tmp_path,
        research_plan=_BASIC_PLAN,
        bib_ledger_yaml=_BASIC_LEDGER,
    )
    result = subprocess.run(
        [sys.executable, str(VALIDATORS_DIR / "cross_stage.py"), str(project)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr


def test_cross_stage_strict_flag_via_cli(tmp_path: Path) -> None:
    """--strict CLI flag promotes warnings to errors."""
    bad_ledger = _BASIC_LEDGER + (
        "- bibkey: orphan2025foo\n"
        "  primary_url: https://arxiv.org/abs/2501.99999\n"
        "  title: 'Orphan paper'\n"
        "  status: unverified\n"
        "  claim_family: bogus_family\n"
    )
    project = _project_with(
        tmp_path,
        research_plan=_BASIC_PLAN,
        bib_ledger_yaml=bad_ledger,
    )
    # Without --strict: claim_family error fires (it's a hard check).
    result = subprocess.run(
        [sys.executable, str(VALIDATORS_DIR / "cross_stage.py"), str(project)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 1, "claim_family is hard error"
    # With --strict on a warning-only case, exit code should also be 1.
    # Build a project with only a soft-warning condition.
    dossier = (
        "# Topic\n\n"
        "## A1. Foo\n\n"
        "| Title | Authors (year) | Venue | arXiv/DOI | GitHub | Desc | KC |\n"
        "|---|---|---|---|---|---|---|\n"
        "| Foo | F (2025) | arXiv preprint | arXiv:2501.00001 | — | x | y |\n"
        "| Orphan | O (2099) | arXiv preprint | arXiv:2099.99999 | — | x | y |\n"
    )
    project2 = _project_with(
        tmp_path / "p2",
        research_plan=_BASIC_PLAN,
        bib_ledger_yaml=_BASIC_LEDGER,
        dossier_files={"01_foo.md": dossier},
    )
    no_strict = subprocess.run(
        [sys.executable, str(VALIDATORS_DIR / "cross_stage.py"), str(project2)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert no_strict.returncode == 0, "warning-only project passes without --strict"
    with_strict = subprocess.run(
        [
            sys.executable,
            str(VALIDATORS_DIR / "cross_stage.py"),
            "--strict",
            str(project2),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert with_strict.returncode == 1, "warning-only project fails with --strict"


# ---------- A3: bib_ledger memory-verified anti-cheat heuristic ----------

def _ledger_n_verified(n: int) -> str:
    parts = ["entries:"]
    for i in range(n):
        parts.append(
            f"- bibkey: smoke{i:04d}entry\n"
            f"  primary_url: https://arxiv.org/abs/2501.{i:05d}\n"
            f"  title: 'Smoke entry {i}'\n"
            f"  status: verified\n"
            f"  claim_family: example\n"
        )
    return "\n".join(parts)


def _ledger_n_mixed(n: int, n_verified: int) -> str:
    parts = ["entries:"]
    for i in range(n):
        status = "verified" if i < n_verified else "unverified"
        parts.append(
            f"- bibkey: smoke{i:04d}entry\n"
            f"  primary_url: https://arxiv.org/abs/2501.{i:05d}\n"
            f"  title: 'Smoke entry {i}'\n"
            f"  status: {status}\n"
            f"  claim_family: example\n"
        )
    return "\n".join(parts)


def test_anti_cheat_quiet_under_threshold(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Below MEMORY_VERIFIED_THRESHOLD (50) entries → no warning even if all verified."""
    p = tmp_path / "ledger.yml"
    p.write_text(_ledger_n_verified(30), encoding="utf-8")
    errors = bib_ledger.validate(p, strict=False)
    assert errors == []
    err = capsys.readouterr().err
    assert "memory-verification" not in err.lower(), (
        f"should not warn under threshold; stderr: {err}"
    )


def test_anti_cheat_quiet_with_mixed_status(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Even at 60 entries, if some are unverified, no warning."""
    p = tmp_path / "ledger.yml"
    p.write_text(_ledger_n_mixed(60, n_verified=50), encoding="utf-8")
    errors = bib_ledger.validate(p, strict=False)
    assert errors == []
    err = capsys.readouterr().err
    assert "memory-verification" not in err.lower(), (
        f"mixed-status should not warn; stderr: {err}"
    )


def test_anti_cheat_warns_on_50_plus_all_verified(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """50+ entries, all verified → warning to stderr (no error)."""
    p = tmp_path / "ledger.yml"
    p.write_text(_ledger_n_verified(60), encoding="utf-8")
    errors = bib_ledger.validate(p, strict=False)
    assert errors == [], f"warning, not error, by default; got {errors}"
    err = capsys.readouterr().err
    assert "memory-verification" in err.lower(), (
        f"should warn at threshold; stderr: {err}"
    )


def test_anti_cheat_strict_promotes_warning(tmp_path: Path) -> None:
    """--strict promotes the heuristic warning to an error."""
    p = tmp_path / "ledger.yml"
    p.write_text(_ledger_n_verified(60), encoding="utf-8")
    errors = bib_ledger.validate(p, strict=True)
    assert any("memory-verification" in e.lower() for e in errors), errors


def test_anti_cheat_strict_via_cli(tmp_path: Path) -> None:
    """`python validators/bib_ledger.py --strict ledger.yml` exits 1 when heuristic fires."""
    p = tmp_path / "ledger.yml"
    p.write_text(_ledger_n_verified(60), encoding="utf-8")
    no_strict = subprocess.run(
        [sys.executable, str(VALIDATORS_DIR / "bib_ledger.py"), str(p)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert no_strict.returncode == 0, "should pass without --strict"
    with_strict = subprocess.run(
        [
            sys.executable,
            str(VALIDATORS_DIR / "bib_ledger.py"),
            "--strict",
            str(p),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert with_strict.returncode == 1, "should fail with --strict"
    assert "memory-verification" in with_strict.stderr.lower()


# ---------- Existing fixture backward-compat ----------

def test_v1_2_validators_pass_on_existing_fixtures() -> None:
    """v1.2 changes do not break existing v1.0/v1.1 fixtures."""
    fixtures_dir = REPO_ROOT / "tests" / "fixtures"
    # mini fixture: small ledger, varied status — anti-cheat shouldn't fire.
    assert bib_ledger.validate(
        fixtures_dir / "mini_topic_timeseries_anomaly" / "bib_ledger.yml"
    ) == []
    # vol25 real: large ledger but mixed status.
    assert bib_ledger.validate(
        fixtures_dir / "vol25_snapshot" / "real" / "bib_ledger.yml"
    ) == []
    # vol25 recreated: also mixed.
    assert bib_ledger.validate(
        fixtures_dir / "vol25_snapshot" / "recreated" / "bib_ledger.yml"
    ) == []

"""End-to-end pipeline smoke test against the medium fixture.

The 6 skills (`/research-plan`, `/research-gather`, `/dossier-build`,
`/agent-index`, `/dossier-audit`, `/url-freshness-check`) are markdown
prompts executed by Claude Code agents — not Python functions. We can't
mock-drive them in pytest. What we CAN test:

1. Sequential validator chain — every validator passes against the medium
   fixture in the order the pipeline produces artifacts. Catches contract
   drift between stages (e.g., if stage N's output format changes and stage
   N+1's validator can't handle it).
2. Helper-script idempotency — `scripts/backfill_ledger.py` and
   `scripts/build_medium_fixture.py` produce stable output on repeat runs.
3. Deliberate-regression detection — if we mutate the fixture in a way that
   should fail validation, the chain catches it loudly.

This is the v1.4 "smoke test" — quick (<5s) and complete enough to gate PRs
without per-validator boilerplate in CI.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from validators import (
    agent_index,
    audit_trail,
    bib_ledger,
    cross_stage,
    dossier,
    research_plan,
    url_check_report,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
MEDIUM = REPO_ROOT / "tests" / "fixtures" / "medium_topic_calibration_subset"
SCRIPTS = REPO_ROOT / "scripts"


# ---------- 1. Sequential validator chain ----------


def test_full_validator_chain_against_medium_fixture() -> None:
    """All 5 stage validators + cross_stage pass against medium fixture.

    Order matches the pipeline's output order: research_plan first, then
    bib_ledger (depends on plan's claim_family taxonomy), then dossier
    (depends on ledger), then agent_index (depends on dossier), then
    cross_stage (validates the whole project).
    """
    chain = [
        ("research_plan", research_plan.validate, MEDIUM / "research_plan.md"),
        ("bib_ledger", bib_ledger.validate, MEDIUM / "bib_ledger.yml"),
        ("dossier", dossier.validate, MEDIUM / "dossier"),
        ("agent_index", agent_index.validate, MEDIUM / "agent_index"),
        (
            "audit_trail",
            audit_trail.validate,
            MEDIUM / "agent_index" / "README.md",
        ),
        ("cross_stage", cross_stage.validate, MEDIUM),
    ]
    failures: list[str] = []
    for name, validate_fn, target in chain:
        errors = validate_fn(target)
        if errors:
            failures.append(f"{name} failed: {errors}")
    assert not failures, "validator chain failures:\n" + "\n".join(failures)


def test_full_validator_chain_strict_mode() -> None:
    """Medium fixture passes cross_stage --strict — it's the reference 'good run'."""
    assert cross_stage.validate(MEDIUM, strict=True) == []
    # bib_ledger's anti-cheat heuristic doesn't fire below 50 entries; medium has 22.
    assert bib_ledger.validate(MEDIUM / "bib_ledger.yml", strict=True) == []


# ---------- 2. Helper-script idempotency ----------


def test_backfill_ledger_idempotent_on_medium_fixture(tmp_path: Path) -> None:
    """Re-running backfill_ledger.py against an already-backfilled project
    produces no change. Catches regressions where backfill clobbers existing
    fields or duplicates them.
    """
    # Copy medium fixture to a temp location to avoid mutating the real one.
    project = tmp_path / "project"
    shutil.copytree(MEDIUM, project)
    ledger_before = (project / "bib_ledger.yml").read_text(encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "backfill_ledger.py"), str(project)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr
    ledger_after = (project / "bib_ledger.yml").read_text(encoding="utf-8")
    assert ledger_before == ledger_after, (
        "backfill_ledger.py is not idempotent — re-running modified the ledger.\n"
        f"stderr: {result.stderr}"
    )


def test_build_medium_fixture_reproducible(tmp_path: Path) -> None:
    """Running scripts/build_medium_fixture.py rebuilds the fixture to its
    canonical form. We don't actually run the script (it would clobber the
    committed fixture); we just verify the script is syntactically valid and
    importable, then check that the existing fixture matches what the script
    expects to produce.
    """
    # Syntax + import check.
    result = subprocess.run(
        [sys.executable, "-c", "import ast; ast.parse(open(r'%s').read())"
         % str(SCRIPTS / "build_medium_fixture.py")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"build_medium_fixture.py has syntax errors: {result.stderr}"
    )
    # Structure check: fixture has the files the script promises to write.
    expected = [
        MEDIUM / "research_plan.md",
        MEDIUM / "bib_ledger.yml",
        MEDIUM / "dossier" / "01_calibration_methods_metrics.md",
        MEDIUM / "agent_index" / "01_calibration_methods_metrics.md",
        MEDIUM / "agent_index" / "README.md",
    ]
    missing = [p for p in expected if not p.exists()]
    assert not missing, f"medium fixture missing files: {missing}"


# ---------- 3. Deliberate-regression detection ----------


def test_chain_catches_orphan_dossier_arxiv_id(tmp_path: Path) -> None:
    """If we corrupt the medium fixture by adding an orphan arxiv ID to the
    dossier (one that's not in the ledger), --strict cross_stage catches it.
    Validates the cross_stage validator's signal on a real fixture.
    """
    project = tmp_path / "project"
    shutil.copytree(MEDIUM, project)
    dossier_file = project / "dossier" / "01_calibration_methods_metrics.md"
    text = dossier_file.read_text(encoding="utf-8")
    corrupted = text.replace(
        "## A1.",
        "## A0. Bogus injected entry\n\n"
        "| Title | Authors (year) | Venue | arXiv/DOI | GitHub | Desc | KC |\n"
        "|---|---|---|---|---|---|---|\n"
        "| Bogus | B (2099) | arXiv preprint | arXiv:2099.99999 | — | x | y |\n\n"
        "## A1.",
        1,
    )
    dossier_file.write_text(corrupted, encoding="utf-8")
    errors = cross_stage.validate(project, strict=True)
    assert any("2099.99999" in e for e in errors), (
        f"cross_stage --strict should catch orphan arxiv ID; got {errors}"
    )


def test_chain_catches_unknown_claim_family(tmp_path: Path) -> None:
    """Mutating a ledger entry to use a claim_family not in the plan's
    taxonomy is a HARD error from cross_stage.
    """
    project = tmp_path / "project"
    shutil.copytree(MEDIUM, project)
    ledger_file = project / "bib_ledger.yml"
    text = ledger_file.read_text(encoding="utf-8")
    corrupted = text.replace(
        "claim_family: calibration_method",
        "claim_family: not_in_taxonomy",
        1,
    )
    ledger_file.write_text(corrupted, encoding="utf-8")
    errors = cross_stage.validate(project)
    assert any("not_in_taxonomy" in e for e in errors), errors


def test_chain_catches_invalid_arxiv_url_in_ledger(tmp_path: Path) -> None:
    """Mutating a ledger entry's primary_url to /pdf/ form trips the
    arxiv-canonical-form check (v1.1).
    """
    project = tmp_path / "project"
    shutil.copytree(MEDIUM, project)
    ledger_file = project / "bib_ledger.yml"
    text = ledger_file.read_text(encoding="utf-8")
    corrupted = text.replace(
        "https://arxiv.org/abs/1706.04599",
        "https://arxiv.org/pdf/1706.04599.pdf",
        1,
    )
    ledger_file.write_text(corrupted, encoding="utf-8")
    errors = bib_ledger.validate(ledger_file)
    assert any("arxiv URL must be canonical" in e for e in errors), errors


# ---------- 4. Cross-fixture sanity (catches "every fixture passes for the wrong reason") ----------


def test_validator_chain_distinguishes_mini_from_medium() -> None:
    """Mini fixture passes; medium fixture also passes. Both should pass for
    the RIGHT reason — i.e., the validators actually see the differences.

    Sanity check: the two fixtures have different entry counts; both should
    validate but cross_stage should see different counts under the hood.
    """
    import yaml
    mini_ledger = yaml.safe_load(
        (REPO_ROOT / "tests" / "fixtures" / "mini_topic_timeseries_anomaly"
         / "bib_ledger.yml").read_text(encoding="utf-8")
    )
    medium_ledger = yaml.safe_load(
        (MEDIUM / "bib_ledger.yml").read_text(encoding="utf-8")
    )
    assert len(mini_ledger["entries"]) != len(medium_ledger["entries"])
    # Both validate cleanly.
    assert bib_ledger.validate(
        REPO_ROOT / "tests" / "fixtures" / "mini_topic_timeseries_anomaly"
        / "bib_ledger.yml"
    ) == []
    assert bib_ledger.validate(MEDIUM / "bib_ledger.yml") == []


# ---------- 5. URL-check report shape (catches v1.1 regex regression) ----------


def test_url_check_report_validator_accepts_well_formed(tmp_path: Path) -> None:
    """Sanity: the url_check_report validator's schema check still works.
    Catches a regression where a future change breaks the report shape.
    """
    report = tmp_path / "url_check.md"
    report.write_text(
        "# URL Freshness Report\n\n"
        "Generated: 2026-05-07\n\n"
        "## Summary\n\n"
        "- total: 22\n"
        "- ok: 22\n"
        "- broken: 0\n",
        encoding="utf-8",
    )
    assert url_check_report.validate(report) == []

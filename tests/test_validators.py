"""Tests for each validator: positive case + at least one negative case.

Each validator must:
- Return an empty error list on a known-good fixture artifact (positive case).
- Return >=1 error on a deliberately-corrupted variant (negative case), with
  the error message containing a substring that identifies the corruption.

This proves the validators have signal — they don't just accept everything.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from validators import (
    agent_index,
    audit_trail,
    bib_ledger,
    dossier,
    research_plan,
    url_check_report,
)


# ---------- positive cases (mini fixture) ----------

def test_research_plan_accepts_mini(mini_dir: Path) -> None:
    assert research_plan.validate(mini_dir / "research_plan.md") == []


def test_bib_ledger_accepts_mini(mini_dir: Path) -> None:
    assert bib_ledger.validate(mini_dir / "bib_ledger.yml") == []


def test_dossier_accepts_mini(mini_dir: Path) -> None:
    assert dossier.validate(mini_dir / "dossier") == []


def test_agent_index_accepts_mini(mini_dir: Path) -> None:
    assert agent_index.validate(mini_dir / "agent_index") == []


def test_audit_trail_accepts_clean_readme(mini_dir: Path) -> None:
    # Mini agent_index README has no audit-trail notes yet — that's fine
    # (the validator only fails on malformed notes, not absence).
    assert audit_trail.validate(mini_dir / "agent_index" / "README.md") == []


# ---------- negative cases (corrupted variants) ----------

def test_research_plan_rejects_too_few_subareas(mini_dir: Path, tmp_path: Path) -> None:
    text = (mini_dir / "research_plan.md").read_text(encoding="utf-8")
    # Replace the Sub-areas section with one that has only 2 sub-areas (need 4-8).
    truncated = text.replace(
        "## Sub-areas\n\n- A1",
        "## Sub-areas\n\n- only_one\n- and_another\n\n## ZZZ unused\n\n## A1",
    )
    bad = tmp_path / "research_plan.md"
    bad.write_text(truncated, encoding="utf-8")
    errors = research_plan.validate(bad)
    assert any("Sub-areas" in e and "at least" in e for e in errors), errors


def test_bib_ledger_rejects_duplicate_bibkey(mini_dir: Path, tmp_path: Path) -> None:
    text = (mini_dir / "bib_ledger.yml").read_text(encoding="utf-8")
    # Append a duplicate of the first bibkey.
    duplicated = text + (
        "- bibkey: ahmad2017nab\n"
        "  primary_url: https://arxiv.org/abs/0000.00000\n"
        "  title: 'Duplicate Title'\n"
        "  status: unverified\n"
        "  claim_family: benchmark\n"
    )
    bad = tmp_path / "bib_ledger.yml"
    bad.write_text(duplicated, encoding="utf-8")
    errors = bib_ledger.validate(bad)
    assert any("duplicate bibkey" in e for e in errors), errors


def test_bib_ledger_rejects_invalid_status(mini_dir: Path, tmp_path: Path) -> None:
    text = (mini_dir / "bib_ledger.yml").read_text(encoding="utf-8")
    bad_text = text.replace("status: verified", "status: bogus_status", 1)
    bad = tmp_path / "bib_ledger.yml"
    bad.write_text(bad_text, encoding="utf-8")
    errors = bib_ledger.validate(bad)
    assert any("not in" in e and "status" in e for e in errors), errors


def test_dossier_rejects_missing_first_4_columns(mini_dir: Path, tmp_path: Path) -> None:
    src = mini_dir / "dossier" / "01_benchmarks_and_datasets.md"
    text = src.read_text(encoding="utf-8")
    # Replace 'Authors (year)' header with something else; this should fail
    # the first-4-cols rule for paper tables (col 2 ≠ Authors (year)
    # makes it a non-paper table — but the data row only has 7 cells, none
    # of which contain a URL, since we strip the existing URLs too).
    # Easier: corrupt the header itself by removing the GitHub column.
    bad_text = text.replace(
        "| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |",
        "| Title | Authors (year) | Venue | arXiv/DOI | OneLine | Key contribution |",
    )
    dossier_dir = tmp_path / "dossier"
    dossier_dir.mkdir()
    (dossier_dir / "01_benchmarks_and_datasets.md").write_text(bad_text, encoding="utf-8")
    errors = dossier.validate(dossier_dir)
    assert any("column 5" in e or "header columns" in e for e in errors), errors


def test_agent_index_rejects_missing_agent_index_comment(
    mini_dir: Path, tmp_path: Path
) -> None:
    src_dir = mini_dir / "agent_index"
    target = tmp_path / "agent_index"
    target.mkdir()
    for src_file in src_dir.iterdir():
        if src_file.name == "README.md":
            text = src_file.read_text(encoding="utf-8")
            # Strip the AGENT-INDEX HTML comment.
            stripped = text.replace(
                "<!-- AGENT-INDEX: this folder is a self-contained reference for time-series anomaly detection benchmarks. Read this README first. -->\n",
                "",
            )
            (target / src_file.name).write_text(stripped, encoding="utf-8")
        else:
            (target / src_file.name).write_text(
                src_file.read_text(encoding="utf-8"), encoding="utf-8"
            )
    errors = agent_index.validate(target)
    assert any("AGENT-INDEX" in e for e in errors), errors


def test_audit_trail_rejects_bad_date_format(tmp_path: Path) -> None:
    bad = tmp_path / "README.md"
    bad.write_text(
        "**Independent audit, round 1 (May 2026):** something\n",
        encoding="utf-8",
    )
    errors = audit_trail.validate(bad)
    assert any("YYYY-MM-DD" in e for e in errors), errors


def test_url_check_report_rejects_missing_summary(tmp_path: Path) -> None:
    bad = tmp_path / "url_check.md"
    bad.write_text(
        "# URL Freshness Report\n\nGenerated: 2026-05-06\n\n(no summary section)",
        encoding="utf-8",
    )
    errors = url_check_report.validate(bad)
    assert any("Summary" in e for e in errors), errors


def test_url_check_report_accepts_minimal_well_formed(tmp_path: Path) -> None:
    good = tmp_path / "url_check.md"
    good.write_text(
        (
            "# URL Freshness Report\n\n"
            "Generated: 2026-05-06\n\n"
            "## Summary\n\n"
            "- total: 100\n"
            "- ok: 95\n"
            "- broken: 3\n"
            "- bot-blocked: 2\n"
        ),
        encoding="utf-8",
    )
    assert url_check_report.validate(good) == []

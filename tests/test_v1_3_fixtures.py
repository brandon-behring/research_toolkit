"""Regression tests for v1.3 — backfilled vol26/27/28 ledgers + medium fixture.

Covers:
- Medium fixture validates against all 5 v1.0/v1.1/v1.2 validators (full stack).
- Medium fixture demonstrates ≥80% authors/venue coverage (the ledger format
  example for v1.1+).
- Backfilled vol26/27/28 ledgers are referenced via path-existence checks
  (skipped if the working copies aren't present in this environment) — they
  live outside the toolkit repo, so tests are tolerant.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from validators import (
    agent_index,
    bib_ledger,
    cross_stage,
    dossier,
    research_plan,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
MEDIUM = REPO_ROOT / "tests" / "fixtures" / "medium_topic_calibration_subset"


# ---------- Medium fixture: positive cases against full validator stack ----------


def test_medium_research_plan_validates() -> None:
    assert research_plan.validate(MEDIUM / "research_plan.md") == []


def test_medium_bib_ledger_validates() -> None:
    assert bib_ledger.validate(MEDIUM / "bib_ledger.yml") == []


def test_medium_dossier_validates() -> None:
    assert dossier.validate(MEDIUM / "dossier") == []


def test_medium_agent_index_validates() -> None:
    assert agent_index.validate(MEDIUM / "agent_index") == []


def test_medium_cross_stage_validates_default() -> None:
    """Default mode passes (no hard errors)."""
    assert cross_stage.validate(MEDIUM) == []


def test_medium_cross_stage_strict_passes() -> None:
    """--strict mode also passes — fixture is a 'good run' reference example."""
    # 22 entries (under 50-entry anti-cheat threshold), all verified, but
    # bib_ledger anti-cheat is at the bib_ledger level not cross_stage.
    # Cross_stage --strict promotes orphan/stale warnings; medium fixture should
    # have neither.
    assert cross_stage.validate(MEDIUM, strict=True) == []


# ---------- Medium fixture: optional-field coverage ----------


def test_medium_authors_coverage_ge_55_pct() -> None:
    """Medium fixture (calibration subset of vol28) includes pre-2010 classics
    (Brier 1950, Platt 1999, Zadrozny 2001/2002, Niculescu-Mizil 2005, Gneiting
    2007, DeGroot 1983, etc.) that don't have arXiv IDs. The arxiv-ID-based
    backfill script skips them, so coverage is lower than vol26/27/28's ≥80%
    target. Realistic floor here is ~55-60%."""
    data = yaml.safe_load((MEDIUM / "bib_ledger.yml").read_text(encoding="utf-8"))
    entries = data["entries"]
    with_authors = sum(1 for e in entries if isinstance(e, dict) and e.get("authors"))
    coverage = with_authors / len(entries)
    assert coverage >= 0.55, f"authors coverage {coverage:.0%} < 55%"


def test_medium_venue_coverage_ge_55_pct() -> None:
    """Same rationale as authors coverage — pre-2010 classics drag this below
    the vol26/27/28 ≥80% target."""
    data = yaml.safe_load((MEDIUM / "bib_ledger.yml").read_text(encoding="utf-8"))
    entries = data["entries"]
    with_venue = sum(1 for e in entries if isinstance(e, dict) and e.get("venue"))
    coverage = with_venue / len(entries)
    assert coverage >= 0.55, f"venue coverage {coverage:.0%} < 55%"


def test_medium_code_url_coverage_ge_40_pct() -> None:
    """v1.3 acceptance criterion: ≥40% code_url coverage. Lower bar because
    older classical-stats papers (Brier, DeGroot, Platt) genuinely have no
    canonical repo."""
    data = yaml.safe_load((MEDIUM / "bib_ledger.yml").read_text(encoding="utf-8"))
    entries = data["entries"]
    with_code_url = sum(
        1 for e in entries if isinstance(e, dict) and e.get("code_url")
    )
    coverage = with_code_url / len(entries)
    assert coverage >= 0.40, f"code_url coverage {coverage:.0%} < 40%"


# ---------- Medium fixture: size + structure ----------


def test_medium_has_about_22_entries() -> None:
    """The vol28 calibration_method + calibration_metric subset has 22 entries.
    If this drifts substantially, regenerate the fixture."""
    data = yaml.safe_load((MEDIUM / "bib_ledger.yml").read_text(encoding="utf-8"))
    n = len(data["entries"])
    assert 20 <= n <= 25, (
        f"medium fixture has {n} entries; expected ~22. "
        f"Re-run scripts/build_medium_fixture.py if vol28 has drifted."
    )


def test_medium_under_anti_cheat_threshold() -> None:
    """Medium fixture (22 entries) is below the 50-entry anti-cheat threshold,
    so even if all entries are 'verified' the heuristic should be silent.
    This is intentional — medium fixture represents a 'good' run."""
    data = yaml.safe_load((MEDIUM / "bib_ledger.yml").read_text(encoding="utf-8"))
    n = len(data["entries"])
    assert n < bib_ledger.MEMORY_VERIFIED_THRESHOLD


# ---------- Backfilled real-world ledgers (tolerant of absence) ----------


@pytest.mark.parametrize("vol", ["vol26", "vol27", "vol28"])
def test_backfilled_ledger_validates_when_present(vol: str) -> None:
    """vol26/27/28 ledgers backfilled by scripts/backfill_ledger.py validate.

    Skipped if the working copy isn't in this environment (CI / fresh clone).
    """
    ledger = Path.home() / "Claude" / f"research_{vol}" / "bib_ledger.yml"
    if not ledger.exists():
        pytest.skip(f"{ledger} not present (working copy)")
    assert bib_ledger.validate(ledger) == []


@pytest.mark.parametrize("vol", ["vol26", "vol27", "vol28"])
def test_backfilled_ledger_has_high_authors_coverage(vol: str) -> None:
    """Each backfilled vol has ≥80% authors-field coverage (v1.3 target)."""
    ledger = Path.home() / "Claude" / f"research_{vol}" / "bib_ledger.yml"
    if not ledger.exists():
        pytest.skip(f"{ledger} not present (working copy)")
    data = yaml.safe_load(ledger.read_text(encoding="utf-8"))
    entries = data["entries"]
    with_authors = sum(1 for e in entries if isinstance(e, dict) and e.get("authors"))
    coverage = with_authors / len(entries)
    assert coverage >= 0.80, f"{vol} authors coverage {coverage:.0%} < 80%"

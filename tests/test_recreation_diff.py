"""Compare vol25_snapshot/real/ to vol25_snapshot/recreated/ after Phase 3.5.

The recreated/ directory is empty until /research-plan, /research-gather (or copy
real/bib_ledger.yml), /dossier-build, and /agent-index have been run on the
prompt-injection domain by the new skills. Until then this test skips.

The comparison is *schema-equivalence*, not byte-identity:
- Same number of files in agent_index/ (±0).
- Each agent_index file has the same number of `**Source:**` entries within ±20%.
- README has AGENT-INDEX comment + scope-boundary + lookup recipes + glossary.
- Same set of top-level section anchors (## A1., ## B2., etc.).

Discrepancies above tolerance are surfaced for human review (logged in
BURN_IN_NOTES.md), but the gate is the schema check, not content fidelity.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REAL = Path(__file__).resolve().parent / "fixtures" / "vol25_snapshot" / "real"
RECREATED = Path(__file__).resolve().parent / "fixtures" / "vol25_snapshot" / "recreated"

SOURCE_LINE_RE = re.compile(r"^\s*-\s*\*\*Source:\*\*", re.MULTILINE)
SECTION_ANCHOR_RE = re.compile(r"^## [A-Z]\d+\.", re.MULTILINE)


def _has_recreated_agent_index() -> bool:
    return (RECREATED / "agent_index").is_dir() and any(
        (RECREATED / "agent_index").glob("*.md")
    )


@pytest.fixture(scope="module")
def recreated_present() -> bool:
    return _has_recreated_agent_index()


def test_recreated_agent_index_file_count_matches(recreated_present: bool) -> None:
    if not recreated_present:
        pytest.skip("recreated/agent_index/ not populated yet (Phase 3.5)")
    real_files = sorted(p.name for p in (REAL / "agent_index").glob("*.md"))
    recreated_files = sorted(p.name for p in (RECREATED / "agent_index").glob("*.md"))
    assert len(real_files) == len(recreated_files), (
        f"file count mismatch — real: {len(real_files)} {real_files}, "
        f"recreated: {len(recreated_files)} {recreated_files}"
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "vol25 recreation under v1.0 skills produced ~70% drift in entry counts vs "
        "real (recreated finds substantially fewer entries per topic file because "
        "/research-gather under v1.0 didn't have the v1.1+ verification protocol or "
        "exhaustive-search prompting). This is a deliberate v1.0/v1.1 baseline "
        "documented in BURN_IN_NOTES.md Phase 3.5. Re-running vol25 recreation under "
        "v1.2+ skills would close the gap; that's a v1.3 backfill candidate, not a "
        "v1.2 fix. xfail strict=True so we notice if the gap ever closes."
    ),
)
def test_recreated_entry_counts_within_tolerance(recreated_present: bool) -> None:
    if not recreated_present:
        pytest.skip("recreated/agent_index/ not populated yet (Phase 3.5)")
    tolerance = 0.20
    discrepancies: list[str] = []
    for real_file in sorted((REAL / "agent_index").glob("*.md")):
        if real_file.name.lower() == "readme.md":
            continue
        recreated_file = RECREATED / "agent_index" / real_file.name
        if not recreated_file.exists():
            discrepancies.append(f"missing in recreated/: {real_file.name}")
            continue
        real_count = len(SOURCE_LINE_RE.findall(real_file.read_text(encoding="utf-8")))
        recreated_count = len(
            SOURCE_LINE_RE.findall(recreated_file.read_text(encoding="utf-8"))
        )
        if real_count == 0:
            continue
        delta_pct = abs(real_count - recreated_count) / real_count
        if delta_pct > tolerance:
            discrepancies.append(
                f"{real_file.name}: real={real_count} recreated={recreated_count} "
                f"({delta_pct:.0%} drift, tolerance={tolerance:.0%})"
            )
    assert not discrepancies, "\n".join(discrepancies)


def test_recreated_readme_has_required_sections(recreated_present: bool) -> None:
    if not recreated_present:
        pytest.skip("recreated/agent_index/ not populated yet (Phase 3.5)")
    readme = RECREATED / "agent_index" / "README.md"
    assert readme.exists(), f"missing {readme}"
    text = readme.read_text(encoding="utf-8")
    for required in (
        "AGENT-INDEX",
        "Scope boundary",  # callout heading
        "Lookup recipes",
        "Glossary",
    ):
        assert required.lower() in text.lower(), (
            f"recreated README missing required section: {required!r}"
        )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "vol25 recreation under v1.0 skills used per-file letter prefix only for "
        "the first file (all files used A1./A2./...) instead of the per-file "
        "convention (A./B./C./...). This was a v1.0 BURN_IN finding; v1.1 "
        "codified the per-file convention in templates/dossier_table.template.md "
        "and the dossier-build/agent-index skill bodies. Re-running vol25 "
        "recreation under v1.1+ skills would close the gap. xfail strict=True "
        "so we notice if the gap ever closes (e.g., after a v1.3 backfill)."
    ),
)
def test_recreated_section_anchors_match(recreated_present: bool) -> None:
    if not recreated_present:
        pytest.skip("recreated/agent_index/ not populated yet (Phase 3.5)")
    discrepancies: list[str] = []
    for real_file in sorted((REAL / "agent_index").glob("*.md")):
        if real_file.name.lower() == "readme.md":
            continue
        recreated_file = RECREATED / "agent_index" / real_file.name
        if not recreated_file.exists():
            continue
        real_anchors = set(SECTION_ANCHOR_RE.findall(real_file.read_text(encoding="utf-8")))
        recreated_anchors = set(
            SECTION_ANCHOR_RE.findall(recreated_file.read_text(encoding="utf-8"))
        )
        if real_anchors and real_anchors != recreated_anchors:
            missing = real_anchors - recreated_anchors
            extra = recreated_anchors - real_anchors
            if missing or extra:
                discrepancies.append(
                    f"{real_file.name}: missing={sorted(missing)} extra={sorted(extra)}"
                )
    assert not discrepancies, "\n".join(discrepancies)

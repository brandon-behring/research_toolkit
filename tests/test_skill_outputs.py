"""Run each validator against the corresponding fixture artifact in vol25_snapshot.

This catches schema drift if a fixture ever desyncs from a validator. The vol25
snapshot has *known* violations documented in fixtures/vol25_snapshot/README.md;
those are asserted explicitly so the tests fail loudly if the violation ever
shifts (e.g., the validator's signal changes or the snapshot is re-copied).
"""
from __future__ import annotations

from pathlib import Path

from validators import agent_index, bib_ledger, dossier


# ---------- vol25 snapshot — known violations + everything else clean ----------

def test_vol25_bib_ledger_has_one_known_violation(vol25_dir: Path) -> None:
    """Entry 63 (kim2024selfreminder) has empty primary_url. Documented in fixture README."""
    errors = bib_ledger.validate(vol25_dir / "bib_ledger.yml")
    assert len(errors) == 1, f"expected 1 known error, got {len(errors)}: {errors}"
    assert "entries[63]" in errors[0]
    assert "primary_url" in errors[0]
    assert "must be non-empty" in errors[0]


def test_vol25_dossier_passes_cleanly(vol25_dir: Path) -> None:
    """The dossier validator's content-type detection accommodates vol25's
    heterogeneous schemas (paper tables for 01-04; non-paper tables for 07)."""
    assert dossier.validate(vol25_dir / "dossier") == []


def test_vol25_agent_index_passes_cleanly(vol25_dir: Path) -> None:
    """The agent_index validator's loose schema accommodates the realized vol25
    synthesis (paper synthesis with optional Code; vendor / standards profiles
    with custom bullets)."""
    assert agent_index.validate(vol25_dir / "agent_index") == []

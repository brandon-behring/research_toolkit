"""Run each validator against the corresponding fixture artifact in prompt_injection_snapshot.

This catches schema drift if a fixture ever desyncs from a validator. The prompt-injection
snapshot has *known* violations documented in fixtures/prompt_injection_snapshot/README.md;
those are asserted explicitly so the tests fail loudly if the violation ever
shifts (e.g., the validator's signal changes or the snapshot is re-copied).
"""
from __future__ import annotations

from pathlib import Path

from validators import agent_index, bib_ledger, dossier


# ---------- prompt-injection snapshot — known violations + everything else clean ----------

def test_prompt_injection_bib_ledger_passes_cleanly(prompt_injection_dir: Path) -> None:
    """Vol25 bib_ledger validates cleanly under v1.1.

    Historical note: under v1.0, entry 63 (kim2024selfreminder) had an empty
    primary_url that was a known violation. The v1.1 cleanup populated the
    URL with the canonical Nature MI publication and the test was renamed
    to assert the post-fix clean state. This catches future regressions
    where the violation could re-surface.
    """
    assert bib_ledger.validate(prompt_injection_dir / "bib_ledger.yml") == []


def test_prompt_injection_dossier_passes_cleanly(prompt_injection_dir: Path) -> None:
    """The dossier validator's content-type detection accommodates prompt-injection's
    heterogeneous schemas (paper tables for 01-04; non-paper tables for 07)."""
    assert dossier.validate(prompt_injection_dir / "dossier") == []


def test_prompt_injection_agent_index_passes_cleanly(prompt_injection_dir: Path) -> None:
    """The agent_index validator's loose schema accommodates the realized prompt-injection
    synthesis (paper synthesis with optional Code; vendor / standards profiles
    with custom bullets)."""
    assert agent_index.validate(prompt_injection_dir / "agent_index") == []

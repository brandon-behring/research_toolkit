"""Run each validator against the corresponding fixture artifact in prompt_injection_snapshot.

This catches schema drift if a fixture ever desyncs from a validator. The prompt-injection
snapshot has *known* violations documented in fixtures/prompt_injection_snapshot/README.md;
those are asserted explicitly so the tests fail loudly if the violation ever
shifts (e.g., the validator's signal changes or the snapshot is re-copied).
"""
from __future__ import annotations

import re
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


# ---------- skill <-> repo consistency ----------

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / ".claude" / "skills"

# Captures (prefix, module) so a foreign-repo reference can be told apart from a
# local one. `synthesis-kb/scripts/ingest_dossiers.py` is a real file in a
# DIFFERENT repo and must not be flagged; `~/Claude/research_toolkit/scripts/x.py`
# and a bare `scripts/x.py` are both local and must be.
_MODULE_REF = re.compile(r"([\w~.-]*(?:/[\w~.-]+)*/)?((?:scripts|validators)/[a-z0-9_]+\.py)\b")

# Referenced but deliberately not implemented. Kept explicit rather than silently
# skipped, and asserted in BOTH directions below so the list cannot rot.
_KNOWN_UNIMPLEMENTED = {
    # citation-audit.md:39 hedges this inline as "(when available)", so it cannot
    # mislead a reader or an agent into invoking something that is not there.
    "scripts/migrate_v2_to_v3.py",
}


def _is_local(prefix: str | None) -> bool:
    """True when the reference resolves inside THIS repo rather than a sibling one."""
    if not prefix:
        return True
    return prefix.rstrip("/").endswith("research_toolkit")


def test_every_module_referenced_by_a_skill_exists() -> None:
    """Every scripts/*.py and validators/*.py path named in a skill spec must exist.

    Regression guard for RS1 (2026-06-12), which renamed the exporter to
    ``scripts/synthesis_export.py`` with no shim. ``research.md`` kept invoking
    ``scripts/research_kb_export.py`` in both its Stage 8 heading and its Stage 8
    command, so a literal ``/research`` run died at the final stage. It survived
    because the only test touching the rename asserted on the *export skill*
    (``synthesis-export.md``), not on the orchestrator that calls it.

    Deliberately repo-wide rather than a research.md-specific assertion: the
    defect was a class (a skill naming a module that does not exist), not an
    instance, and a targeted test would not have caught the next rename.

    Note ``validators/research_kb_export.py`` legitimately keeps its historical
    name and must continue to resolve — that asymmetry is exactly what made the
    original bug easy to miss by eye.
    """
    missing: list[str] = []
    for skill_path in sorted(SKILLS_DIR.glob("*.md")):
        text = skill_path.read_text(encoding="utf-8")
        for prefix, ref in sorted(set(_MODULE_REF.findall(text))):
            if not _is_local(prefix) or ref in _KNOWN_UNIMPLEMENTED:
                continue
            if not (REPO_ROOT / ref).is_file():
                missing.append(f"{skill_path.name}: {ref}")
    assert missing == [], "skills reference modules that do not exist:\n  " + "\n  ".join(missing)


def test_known_unimplemented_modules_are_still_unimplemented() -> None:
    """The allowlist above must shrink when a module lands, not silently go stale.

    Without this, implementing ``migrate_v2_to_v3.py`` would leave a permanent
    exemption that quietly suppresses a future regression on the same path.
    """
    landed = sorted(ref for ref in _KNOWN_UNIMPLEMENTED if (REPO_ROOT / ref).is_file())
    assert landed == [], (
        "these now exist and must be removed from _KNOWN_UNIMPLEMENTED:\n  " + "\n  ".join(landed)
    )

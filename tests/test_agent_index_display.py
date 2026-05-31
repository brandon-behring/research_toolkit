"""Tests for validators.agent_index_display (display-vs-evidence audit).

Builds a tiny strict-live project in ``tmp_path``: a content-addressed cache
text file with known prose, a cache_manifest.yml + evidence_ledger.yml +
pre_selection_manifest.yml referencing it, and an agent_index family file with
Mechanism bullets. Verifies that a verbatim-substring Mechanism passes, a
paraphrased / ellipsis-joined Mechanism is flagged, and an unlinkable bullet
errors. Hand-rolled fixtures only (no unittest.mock).

Also a real-data smoke test against the shipped research_mcp_server_security
dossier when present — it was rendered by the guarded renderer and must pass.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from validators import agent_index_display  # type: ignore[import-not-found]

CACHE_PROSE = (
    "Tool poisoning attacks embed hidden instructions in an MCP tool "
    "description so that a connected model executes attacker-controlled "
    "actions without the user ever seeing the malicious payload. "
    "The injected text is invisible in typical client UIs."
)
SHA = "0" * 64  # placeholder; this validator reads text_path, not the hash.


def _dump(path: Path, data: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _build_project(
    tmp_path: Path,
    *,
    good_mechanism: str,
    bad_mechanism: str,
    include_bad_block: bool = True,
    bad_bibkey: str = "smith2024poison",
    include_bad_selection: bool = True,
) -> Path:
    """Build a minimal strict-live project. Returns the project dir."""
    project = tmp_path / "proj"
    project.mkdir()

    # Content-addressed cache text file under text/sha256/<sha>.txt.
    cache_text_rel = f"text/sha256/{SHA}.txt"
    cache_text_path = project / cache_text_rel
    cache_text_path.parent.mkdir(parents=True, exist_ok=True)
    cache_text_path.write_text(CACHE_PROSE, encoding="utf-8")

    _dump(
        project / "cache_manifest.yml",
        {
            "schema_version": 2,
            "topic": "mcp security",
            "entries": [
                {
                    "cache_id": "cache_poison",
                    "source_url": "https://example.com/poison",
                    "fetched_at": "2026-01-01",
                    "content_type": "text/html",
                    "bytes": len(CACHE_PROSE.encode("utf-8")),
                    "sha256": SHA,
                    "raw_path": f"raw/sha256/{SHA}.html",
                    "text_path": cache_text_rel,
                    "metadata_path": f"meta/sha256/{SHA}.json",
                    "restricted": False,
                    "rights_status": "public",
                    "extraction_status": "ok",
                }
            ],
        },
    )

    _dump(
        project / "evidence_ledger.yml",
        {
            "schema_version": 2,
            "topic": "mcp security",
            "entries": [
                {
                    "evidence_id": "ev_good",
                    "bibkey": "doe2024tool",
                    "cache_id": "cache_poison",
                    "excerpt": good_mechanism,
                },
                {
                    "evidence_id": "ev_bad",
                    "bibkey": bad_bibkey,
                    "cache_id": "cache_poison",
                    # The ledger excerpt is itself a substring; the VIOLATION is
                    # introduced only in the rendered agent_index display text.
                    "excerpt": "Tool poisoning attacks embed hidden instructions",
                },
            ],
        },
    )

    selections: list[dict[str, Any]] = [
        {
            "family": "01_tool_poisoning",
            "bibkey": "doe2024tool",
            "evidence_id": "ev_good",
        }
    ]
    if include_bad_selection:
        selections.append(
            {
                "family": "01_tool_poisoning",
                "bibkey": bad_bibkey,
                "evidence_id": "ev_bad",
            }
        )
    _dump(
        project / "pre_selection_manifest.yml",
        {"schema_version": 2, "topic": "mcp security", "selections": selections},
    )

    index_dir = project / "agent_index"
    index_dir.mkdir()
    blocks = [
        "\n".join(
            [
                "- **Source:** doe2024tool",
                f"- **Mechanism:** {good_mechanism}",
                "- **Status:** verified",
            ]
        )
    ]
    if include_bad_block:
        blocks.append(
            "\n".join(
                [
                    f"- **Source:** {bad_bibkey}",
                    f"- **Mechanism:** {bad_mechanism}",
                    "- **Status:** verified",
                ]
            )
        )
    (index_dir / "01_tool_poisoning.md").write_text(
        "\n\n".join(blocks) + "\n", encoding="utf-8"
    )
    return project


# ---------- Positive case ----------


def test_validate_accepts_verbatim_substring_mechanism(tmp_path):
    # Both bullets are verbatim substrings of the cached prose → clean.
    project = _build_project(
        tmp_path,
        good_mechanism="Tool poisoning attacks embed hidden instructions in an MCP tool description",
        bad_mechanism="The injected text is invisible in typical client UIs.",
    )
    errors = agent_index_display.validate(project)
    assert errors == [], errors


def test_validate_accepts_display_override_that_is_still_substring(tmp_path):
    # A cleaner sentence that is STILL a raw substring of cached text passes.
    project = _build_project(
        tmp_path,
        good_mechanism="a connected model executes attacker-controlled actions",
        bad_mechanism="hidden instructions in an MCP tool description",
    )
    errors = agent_index_display.validate(project)
    assert errors == [], errors


def test_validate_accepts_project_without_agent_index(tmp_path):
    project = tmp_path / "empty"
    project.mkdir()
    assert agent_index_display.validate(project) == []


def test_validate_skips_legacy_agent_index_without_strict_live_artifacts(tmp_path):
    # A v1-era dossier: agent_index/ with Mechanism bullets but NO
    # cache_manifest.yml / evidence_ledger.yml / pre_selection_manifest.yml.
    # There is no content-addressed cache to ground against, so the
    # display-vs-evidence audit does not apply — return [] (must NOT raise
    # FileNotFoundError on the missing manifest). Mirrors several committed
    # fixtures (medium_topic_calibration_subset, mini_topic_timeseries_anomaly).
    project = tmp_path / "legacy"
    index_dir = project / "agent_index"
    index_dir.mkdir(parents=True)
    (index_dir / "01_topic.md").write_text(
        "\n".join(
            [
                "- **Source:** https://arxiv.org/abs/2401.00001",
                "- **Mechanism:** some legacy mechanism prose with no cache backing",
                "- **Status:** verified",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    assert agent_index_display.validate(project) == []


def test_validate_rejects_strict_live_project_missing_evidence_ledger(tmp_path):
    # cache_manifest.yml present but evidence_ledger.yml absent → malformed
    # strict-live project; surface a clear error (not a silent pass, not a crash).
    project = _build_project(
        tmp_path,
        good_mechanism="Tool poisoning attacks embed hidden instructions in an MCP tool description",
        bad_mechanism="The injected text is invisible in typical client UIs.",
        include_bad_block=False,
    )
    (project / "evidence_ledger.yml").unlink()
    errors = agent_index_display.validate(project)
    assert len(errors) == 1, errors
    assert "evidence_ledger.yml" in errors[0]


# ---------- Negative case: paraphrase / not-in-cache ----------


def test_validate_rejects_paraphrased_mechanism(tmp_path):
    project = _build_project(
        tmp_path,
        good_mechanism="Tool poisoning attacks embed hidden instructions in an MCP tool description",
        # Ellipsis-joined / paraphrased — NOT a verbatim substring of cached prose.
        bad_mechanism="Tool poisoning ... lets attackers fully hijack the agent entirely.",
    )
    errors = agent_index_display.validate(project)
    assert len(errors) == 1, errors
    assert "01_tool_poisoning.md" in errors[0]
    assert "substring" in errors[0]


def test_validate_rejects_only_the_tampered_bullet(tmp_path):
    # Exactly one of two bullets is tampered; the other must not be flagged.
    project = _build_project(
        tmp_path,
        good_mechanism="The injected text is invisible in typical client UIs.",
        bad_mechanism="A totally fabricated claim that never appears in the source at all.",
    )
    errors = agent_index_display.validate(project)
    assert len(errors) == 1, errors
    assert "fabricated" in errors[0].lower() or "substring" in errors[0]


# ---------- Negative case: missing cache linkage ----------


def test_validate_rejects_mechanism_with_no_resolvable_linkage(tmp_path):
    # The bad block's bibkey has NO pre_selection selection → unlinkable.
    project = _build_project(
        tmp_path,
        good_mechanism="Tool poisoning attacks embed hidden instructions in an MCP tool description",
        bad_mechanism="The injected text is invisible in typical client UIs.",
        include_bad_selection=False,
    )
    errors = agent_index_display.validate(project)
    assert len(errors) == 1, errors
    assert "no resolvable cache linkage" in errors[0]
    assert "01_tool_poisoning.md" in errors[0]


def test_validate_rejects_when_cache_text_missing(tmp_path):
    project = _build_project(
        tmp_path,
        good_mechanism="Tool poisoning attacks embed hidden instructions in an MCP tool description",
        bad_mechanism="The injected text is invisible in typical client UIs.",
        include_bad_block=False,
    )
    # Delete the backing cache text file → linkage resolves the entry but the
    # text cannot be read.
    (project / "text" / "sha256" / f"{SHA}.txt").unlink()
    errors = agent_index_display.validate(project)
    assert len(errors) == 1, errors
    assert "could not be read" in errors[0]


def test_validate_uses_inline_evidence_bullet_when_present(tmp_path):
    # When a block carries an explicit Evidence bullet, it is used directly
    # (no pre_selection needed for that block).
    project = _build_project(
        tmp_path,
        good_mechanism="Tool poisoning attacks embed hidden instructions in an MCP tool description",
        bad_mechanism="The injected text is invisible in typical client UIs.",
        include_bad_block=False,
    )
    # Rewrite the family file with an Evidence bullet but NO matching selection
    # would be needed because the Evidence bullet resolves directly.
    (project / "agent_index" / "01_tool_poisoning.md").write_text(
        "\n".join(
            [
                "- **Source:** anykey",
                "- **Evidence:** ev_good",
                "- **Mechanism:** a connected model executes attacker-controlled actions",
                "- **Status:** verified",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    assert agent_index_display.validate(project) == []


# ---------- Real-data smoke test (oracle) ----------

_SHIPPED = Path.home() / "Claude" / "research_mcp_server_security"


@pytest.mark.skipif(
    not (_SHIPPED / "agent_index").exists(),
    reason="shipped research_mcp_server_security dossier not present",
)
def test_validate_passes_on_shipped_mcp_server_security_dossier():
    # The shipped dossier was rendered by the guarded renderer → must pass.
    errors = agent_index_display.validate(_SHIPPED)
    assert errors == [], errors

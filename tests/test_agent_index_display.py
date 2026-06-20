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
    bad_extraction_method: str | None = None,
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

    _ev_bad: dict[str, Any] = {
        "evidence_id": "ev_bad",
        "bibkey": bad_bibkey,
        "cache_id": "cache_poison",
        # The ledger excerpt is itself a substring; the VIOLATION is
        # introduced only in the rendered agent_index display text.
        "excerpt": "Tool poisoning attacks embed hidden instructions",
    }
    if bad_extraction_method is not None:
        _ev_bad["supports"] = [
            {"claim_id": "claim_bad", "extraction_method": bad_extraction_method}
        ]
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
                _ev_bad,
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


# ---------- Paraphrase exemption (extraction_method) ----------


def test_validate_exempts_paraphrase_backed_mechanism(tmp_path):
    # A Mechanism grounded in extraction_method: paraphrase evidence is a declared
    # paraphrase (a synthesis of the source), not a verbatim claim — exempt from the
    # substring contract, so a non-substring display is NOT flagged. (Cache linkage is
    # still required; here it resolves fine, only the substring audit is skipped.)
    project = _build_project(
        tmp_path,
        good_mechanism="Tool poisoning attacks embed hidden instructions in an MCP tool description",
        bad_mechanism="Tool poisoning ... lets attackers fully hijack the agent entirely.",
        bad_extraction_method="paraphrase",
    )
    assert agent_index_display.validate(project) == []


def test_validate_still_enforces_substring_for_verbatim_match_evidence(tmp_path):
    # A verbatim_match claim keeps the substring contract: the same non-substring
    # display that paraphrase evidence would exempt is flagged here.
    project = _build_project(
        tmp_path,
        good_mechanism="Tool poisoning attacks embed hidden instructions in an MCP tool description",
        bad_mechanism="Tool poisoning ... lets attackers fully hijack the agent entirely.",
        bad_extraction_method="verbatim_match",
    )
    errors = agent_index_display.validate(project)
    assert len(errors) == 1, errors
    assert "substring" in errors[0]


def test_validate_exempts_paraphrase_before_cache_read(tmp_path):
    # Regression (offline/CI tier): the paraphrase exemption is applied BEFORE the cache
    # is consulted, so a paraphrase Mechanism raises no cache-linkage error when the
    # cache blob is absent — which is exactly the offline tier CI runs (no cache blobs
    # are committed). The bad block is paraphrase-backed and the cache text is deleted;
    # the ONLY error is the non-paraphrase good block. Pre-reorder, the paraphrase block
    # hit the cache read first and both blocks failed "could not be read".
    project = _build_project(
        tmp_path,
        good_mechanism="Tool poisoning attacks embed hidden instructions in an MCP tool description",
        bad_mechanism="Tool poisoning ... lets attackers fully hijack the agent entirely.",
        bad_extraction_method="paraphrase",
    )
    (project / "text" / "sha256" / f"{SHA}.txt").unlink()
    errors = agent_index_display.validate(project)
    assert len(errors) == 1, errors
    assert "could not be read" in errors[0]
    assert "fully hijack" not in errors[0]


def test_is_paraphrase_only_predicate_edge_cases():
    # Direct unit coverage of the exemption predicate — it gates every linked Mechanism,
    # so its edge behavior is load-bearing.
    p = agent_index_display._is_paraphrase_only
    # Exempt only when EVERY support is a declared paraphrase.
    assert p({"supports": [{"extraction_method": "paraphrase"}]}) is True
    # A mixed paraphrase + unspecified(None) record is NOT exempt — an unspecified support
    # keeps the substring contract (only verbatim_match used to be excluded).
    assert p({"supports": [{"extraction_method": "paraphrase"},
                           {"extraction_method": None}]}) is False
    # A verbatim_match support still blocks exemption.
    assert p({"supports": [{"extraction_method": "paraphrase"},
                           {"extraction_method": "verbatim_match"}]}) is False
    # All-unspecified / empty / absent supports → not a declared paraphrase → enforced.
    assert p({"supports": [{"claim_id": "c"}]}) is False
    assert p({"supports": []}) is False
    assert p({}) is False
    # A malformed supports (YAML `supports:` → None, or any non-list) returns False instead
    # of raising TypeError.
    assert p({"supports": None}) is False
    assert p({"supports": {"extraction_method": "paraphrase"}}) is False


# ---------- Rule B: atom-anchored synthesis ----------


def _build_atom_project(tmp_path, *, mechanism, evidence_entries):
    """A strict-live project whose single Mechanism is an atom-anchored synthesis."""
    project = tmp_path / "proj"
    (project / "agent_index").mkdir(parents=True)
    rel = f"text/sha256/{SHA}.txt"
    (project / rel).parent.mkdir(parents=True, exist_ok=True)
    (project / rel).write_text(CACHE_PROSE, encoding="utf-8")
    _dump(project / "cache_manifest.yml", {
        "schema_version": 2, "topic": "t",
        "entries": [{"cache_id": "cache_poison", "source_url": "https://example.com/p",
                     "sha256": SHA, "text_path": rel, "extraction_status": "ok"}]})
    _dump(project / "evidence_ledger.yml", {"schema_version": 3, "entries": evidence_entries})
    (project / "agent_index" / "01_x.md").write_text(
        "\n".join(["- **Source:** https://example.com/p",
                   f"- **Mechanism:** {mechanism}",
                   "- **Status:** verified"]) + "\n", encoding="utf-8")
    return project


def _atom_ev(evid, claim_id, excerpt):
    return {"evidence_id": evid, "cache_ids": ["cache_poison"], "excerpt": excerpt,
            "supports": [{"claim_id": claim_id, "extraction_method": "verbatim_match",
                          "excerpt_anchor": {"cache_id": "cache_poison",
                                             "text_path_offset": [0, 1], "sha256_of_span": "b" * 64}}]}


def test_validate_accepts_atom_anchored_synthesis_display(tmp_path):
    # A synthesis Mechanism that PARAPHRASES (not a verbatim substring of the cache) but cites
    # [claim_X] atoms that each resolve to a verbatim-anchored evidence record — grounded by
    # Rule B (the verbatim proof is the per-atom anchor, not the displayed sentence).
    project = _build_atom_project(
        tmp_path,
        mechanism="The attack secretly plants instructions [claim_a] so the agent is hijacked [claim_b].",
        evidence_entries=[
            _atom_ev("ev_a", "claim_a", "Tool poisoning attacks embed hidden instructions"),
            _atom_ev("ev_b", "claim_b", "a connected model executes attacker-controlled actions"),
        ])
    assert agent_index_display.validate(project) == []


def test_validate_rejects_dangling_claim_atom(tmp_path):
    # A cited atom with no matching evidence record is a dangling display↔evidence link — a
    # hard error even under Rule B (the link must hold; never silently passed).
    project = _build_atom_project(
        tmp_path,
        mechanism="A synthesis citing a nonexistent claim [claim_missing] cannot be grounded.",
        evidence_entries=[_atom_ev("ev_a", "claim_a", "Tool poisoning attacks embed hidden instructions")])
    errors = agent_index_display.validate(project)
    assert len(errors) == 1, errors
    assert "claim_missing" in errors[0] and "dangling" in errors[0]


def test_claim_ids_index():
    ev = {"entries": [
        {"evidence_id": "e1", "supports": [{"claim_id": "claim_x"}, {"claim_id": "claim_y"}]},
        {"evidence_id": "e2", "supports": [{"claim_id": "claim_z"}]},
        {"evidence_id": "e3", "supports": None},  # malformed → ignored, not raised
    ]}
    assert agent_index_display._claim_ids(ev) == {"claim_x", "claim_y", "claim_z"}


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

"""Tests for scripts/repair_evidence_bullet_atoms.py — malformed Evidence-bullet repair.

A ``- **Evidence:**`` bullet that lists several claim_ids or ev_ids (rather than one ev_id) is
converted to inline ``[claim_X]`` atoms in the Mechanism (grounded by the validator's Rule B) and
the malformed bullet is dropped. A single valid ev_id bullet is left untouched; an unresolvable
token is reported.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import repair_evidence_bullet_atoms as rep  # noqa: E402
from validators import agent_index_display as aid  # noqa: E402

CACHE_ID = "cache_t1"
SRC = "https://example.org/paper.pdf"  # non-arxiv: no arxiv-orphan --strict warning


def _ev(evid, claim_id, *, excerpt="x"):
    return {"evidence_id": evid, "source_url": SRC, "excerpt": excerpt, "cache_ids": [CACHE_ID],
            "supports": [{"claim_id": claim_id, "extraction_method": "verbatim_match",
                          "excerpt_anchor": {"cache_id": CACHE_ID,
                                             "text_path_offset": [0, 1], "sha256_of_span": "b" * 64}}]}


def _dossier(tmp_path, *, evidence_value, evidence_entries):
    d = tmp_path
    (d / "agent_index").mkdir(parents=True, exist_ok=True)
    block = "\n".join([
        "## S1. Heading", "",
        "- **bibkey_t**",
        f"  - **Source:** {SRC}",
        "  - **Mechanism:** A synthesis sentence that paraphrases several cited sources.",
        "  - **Status:** Verified.",
        f"  - **Evidence:** {evidence_value}",
    ]) + "\n"
    (d / "agent_index" / "01_x.md").write_text(block, encoding="utf-8")
    rel = "text/sha256/" + "a" * 64 + ".txt"
    (d / rel).parent.mkdir(parents=True, exist_ok=True)
    (d / rel).write_text("cache body", encoding="utf-8")
    (d / "cache_manifest.yml").write_text(yaml.safe_dump(
        {"schema_version": 2, "topic": "t", "cache_root": str(d),
         "entries": [{"cache_id": CACHE_ID, "source_url": SRC, "sha256": "a" * 64,
                      "text_path": rel, "extraction_status": "ok"}]}, sort_keys=False), encoding="utf-8")
    (d / "evidence_ledger.yml").write_text(
        yaml.safe_dump({"schema_version": 3, "entries": evidence_entries}, sort_keys=False), encoding="utf-8")
    (d / "bib_ledger.yml").write_text(yaml.safe_dump({"entries": []}, sort_keys=False), encoding="utf-8")
    return d


def test_claim_id_bullet_becomes_inline_atoms_green(tmp_path):
    d = _dossier(tmp_path, evidence_value="claim_a, claim_b",
                 evidence_entries=[_ev("ev_1", "claim_a"), _ev("ev_2", "claim_b")])
    result = rep.repair_dossier(d)
    assert result["kept"] is True
    out = (d / "agent_index" / "01_x.md").read_text()
    assert "[claim_a] [claim_b]" in out  # appended to the Mechanism
    assert "**Evidence:**" not in out    # malformed bullet dropped
    assert aid.validate(d) == []         # grounded by Rule B


def test_ev_id_bullet_maps_to_first_claim(tmp_path):
    d = _dossier(tmp_path, evidence_value="ev_1 ev_2",
                 evidence_entries=[_ev("ev_1", "claim_a"), _ev("ev_2", "claim_b")])
    result = rep.repair_dossier(d)
    assert result["kept"] is True
    assert result["fixes"][0]["atoms"] == ["claim_a", "claim_b"]
    assert aid.validate(d) == []


def test_single_valid_ev_id_bullet_untouched(tmp_path):
    d = _dossier(tmp_path, evidence_value="ev_1", evidence_entries=[_ev("ev_1", "claim_a")])
    before = (d / "agent_index" / "01_x.md").read_text()
    result = rep.repair_dossier(d)
    assert result["fixes"] == []  # a well-formed single ev_id bullet is left alone
    assert (d / "agent_index" / "01_x.md").read_text() == before


def test_unresolvable_token_reported_untouched(tmp_path):
    d = _dossier(tmp_path, evidence_value="claim_a, claim_does_not_exist",
                 evidence_entries=[_ev("ev_1", "claim_a")])
    before = (d / "agent_index" / "01_x.md").read_text()
    result = rep.repair_dossier(d)
    assert result["fixes"] == [] and len(result["unresolved"]) == 1
    assert "claim_does_not_exist" in result["unresolved"][0]["reason"]
    assert (d / "agent_index" / "01_x.md").read_text() == before


def test_idempotent_second_run_noop(tmp_path):
    d = _dossier(tmp_path, evidence_value="claim_a, claim_b",
                 evidence_entries=[_ev("ev_1", "claim_a"), _ev("ev_2", "claim_b")])
    rep.repair_dossier(d)
    after = (d / "agent_index" / "01_x.md").read_text()
    result2 = rep.repair_dossier(d)
    assert result2["fixes"] == [] and result2["unresolved"] == []
    assert (d / "agent_index" / "01_x.md").read_text() == after

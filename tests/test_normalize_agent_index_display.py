"""Tests for scripts/normalize_agent_index_display.py — the display-normalizer.

Post Rule B, the normalizer's scope is **0-atom paraphrase-display blocks only** (a displayed
sentence that paraphrases a single source whose verbatim span is its ``excerpt``). Atom-bearing
Mechanisms are grounded by the validator's Rule B and must be LEFT UNTOUCHED here.

Covers: (a) a 0-atom block with an Evidence bullet (route i) is rewritten to display:=excerpt;
(b) a 0-atom block joined by Source URL (route ii) is rewritten + gains its bullet; (c) an
atom-bearing block is SKIPPED (Rule B owns it); (d) an excerpt absent from the cache is REPORTED
(re-gather), file untouched; (e) idempotency; (f) a ``<url>`` Source; (g) insertion fidelity;
(h) the transactional restore (a residual reverts every touched file).

The gate oracle is the REAL ``cross_stage.validate(..., strict=True)`` — fixtures include a
minimal ``bib_ledger.yml`` (so cross_stage runs the display sub-validator) and non-arxiv Source
URLs (so the empty ledger raises no arxiv-orphan ``--strict`` warning).
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import normalize_agent_index_display as nz  # noqa: E402
from validators import agent_index_display as aid  # noqa: E402

CACHE_ID = "cache_t1"
SRC = "https://example.org/paper.pdf"  # non-arxiv: no arxiv-orphan --strict warning


def _ev(evid, excerpt, *, claim_id=None, method="verbatim_match",
        cache_id=CACHE_ID, source_url=SRC):
    support = {"extraction_method": method,
               "excerpt_anchor": {"cache_id": cache_id,
                                  "text_path_offset": [0, 1], "sha256_of_span": "b" * 64}}
    if claim_id:
        support["claim_id"] = claim_id
    # Real v3 records carry a top-level cache_ids list (what the display validator's
    # _evidence_cache_ids reads); the per-support excerpt_anchor mirrors the real shape.
    return {"evidence_id": evid, "source_url": source_url, "excerpt": excerpt,
            "cache_ids": [cache_id], "supports": [support]}


def _write_dossier(tmp_path, *, family_md, evidence_entries, cache_text):
    d = tmp_path
    (d / "agent_index").mkdir(parents=True, exist_ok=True)
    (d / "agent_index" / "01_x.md").write_text(family_md, encoding="utf-8")
    rel = "text/sha256/" + "a" * 64 + ".txt"
    tf = d / rel
    tf.parent.mkdir(parents=True, exist_ok=True)
    tf.write_text(cache_text, encoding="utf-8")
    (d / "cache_manifest.yml").write_text(
        yaml.safe_dump({"schema_version": 2, "topic": "t", "cache_root": str(d),
                        "entries": [{"cache_id": CACHE_ID, "source_url": SRC, "sha256": "a" * 64,
                                     "text_path": rel, "extraction_status": "ok"}]},
                       sort_keys=False), encoding="utf-8")
    (d / "evidence_ledger.yml").write_text(
        yaml.safe_dump({"schema_version": 3, "entries": evidence_entries}, sort_keys=False),
        encoding="utf-8")
    (d / "bib_ledger.yml").write_text(yaml.safe_dump({"entries": []}, sort_keys=False),
                                      encoding="utf-8")
    return d


def _block(*, source_line, mechanism, with_bullet=None, bibkey="bibkey_t_2001"):
    """Build one canonical agent_index block (2-space-indented bullets under a bibkey)."""
    lines = [
        "## S1.1. Heading", "",
        f"- **{bibkey}**",
        f"  - **Source:** {source_line}",
        "  - **Code:** —",
        f"  - **Mechanism:** {mechanism}",
        "  - **Result:** see the contribution above.",
        "  - **Status:** Verified (webfetch). cache_id `cache_t1`.",
    ]
    if with_bullet:
        lines.append(f"  - **Evidence:** {with_bullet}")
    return "\n".join(lines) + "\n"


# ---------- (a) 0-atom paraphrase display + Evidence bullet (route i) ----------

def test_zero_atom_bullet_normalizes_green(tmp_path):
    excerpt = "bursts and heavy tails are the empirical origin of human temporal dynamics"
    cache_text = f"lead\n{excerpt}\ntail"
    mech = "Examines the temporal distribution of human actions, challenging Poisson assumptions."
    d = _write_dossier(
        tmp_path,
        family_md=_block(source_line=SRC, mechanism=mech, with_bullet="ev_t_0001"),
        evidence_entries=[_ev("ev_t_0001", excerpt)],
        cache_text=cache_text)
    assert aid.validate(d) != []  # paraphrase display fails the substring contract first
    result = nz.normalize_dossier(d)
    assert result["kept"] is True and result["residual"] == []
    fx = result["fixes"][0]
    assert fx["route"] == "evidence-bullet" and fx["need_display_rewrite"] and not fx["need_bullet"]
    assert aid.validate(d) == []
    assert f"- **Mechanism:** {excerpt}\n" in (d / "agent_index" / "01_x.md").read_text()


# ---------- (b) 0-atom paraphrase display joined by Source URL (route ii) ----------

def test_zero_atom_source_url_join(tmp_path):
    excerpt = "a panel of smaller judges outperforms a single large judge at lower cost"
    cache_text = f"intro\n{excerpt}\nmore"
    mech = "Describes a panel-of-judges evaluation that is cheaper than one large judge."
    d = _write_dossier(
        tmp_path,
        family_md=_block(source_line=SRC, mechanism=mech),
        evidence_entries=[_ev("ev_t_0001", excerpt)],
        cache_text=cache_text)
    result = nz.normalize_dossier(d)
    assert result["kept"] is True
    fx = result["fixes"][0]
    assert fx["route"] == "source-url" and fx["need_display_rewrite"] and fx["need_bullet"]
    assert aid.validate(d) == []


# ---------- (c) atom-bearing block is SKIPPED (Rule B owns it) ----------

def test_atom_bearing_block_skipped(tmp_path):
    excerpt = "calibrated probability estimates are needed in many applications"
    cache_text = f"head\n{excerpt}\nfoot"
    # Editorial display with an inline atom — display != excerpt, NOT a substring; but the atom
    # resolves, so Rule B greens it. The normalizer must NOT rewrite it (preserve content).
    mech = f'Some Title — venue. Stated verbatim: "{excerpt}" [claim_t_0101]'
    d = _write_dossier(
        tmp_path,
        family_md=_block(source_line=SRC, mechanism=mech),
        evidence_entries=[_ev("ev_t_0001", excerpt, claim_id="claim_t_0101")],
        cache_text=cache_text)
    assert aid.validate(d) == []  # Rule B already grounds it
    before = (d / "agent_index" / "01_x.md").read_text()
    result = nz.normalize_dossier(d)
    assert result["fixes"] == [] and result["unresolved"] == []  # skipped, not touched
    assert result["kept"] is True
    assert (d / "agent_index" / "01_x.md").read_text() == before  # authored display intact


# ---------- (d) excerpt absent from cache -> REPORTED, untouched ----------

def test_excerpt_absent_reported_untouched(tmp_path):
    excerpt = "a sentence that does not appear anywhere in the cached blob"
    cache_text = "completely unrelated cached body text without the span"
    mech = "Paraphrases a claim whose verbatim span is not in this (bad) cache blob."
    family = _block(source_line=SRC, mechanism=mech, with_bullet="ev_t_0001")
    d = _write_dossier(
        tmp_path, family_md=family,
        evidence_entries=[_ev("ev_t_0001", excerpt)],
        cache_text=cache_text)
    before = (d / "agent_index" / "01_x.md").read_text()
    result = nz.normalize_dossier(d)
    assert result["fixes"] == [] and len(result["unresolved"]) == 1
    assert "RE-GATHER" in result["unresolved"][0]["reason"]
    assert result["kept"] is False
    assert (d / "agent_index" / "01_x.md").read_text() == before  # untouched


# ---------- (e) idempotency ----------

def test_idempotent_second_run_noop(tmp_path):
    excerpt = "idempotent verbatim sentence grounded in the cache"
    cache_text = f"x\n{excerpt}\ny"
    mech = "A paraphrase of the idempotent sentence in the cache."
    d = _write_dossier(
        tmp_path, family_md=_block(source_line=SRC, mechanism=mech, with_bullet="ev_t_0001"),
        evidence_entries=[_ev("ev_t_0001", excerpt)],
        cache_text=cache_text)
    nz.normalize_dossier(d)
    after_first = (d / "agent_index" / "01_x.md").read_text()
    result2 = nz.normalize_dossier(d)
    assert result2["fixes"] == [] and result2["unresolved"] == []
    assert result2["wrote"] is False and result2["kept"] is True
    assert (d / "agent_index" / "01_x.md").read_text() == after_first


# ---------- (f) <url>-wrapped Source (Mode 2) ----------

def test_angle_wrapped_source_url_join(tmp_path):
    excerpt = "angle bracketed source still joins by its embedded url"
    cache_text = f"head\n{excerpt}\nfoot"
    mech = "A paraphrase whose source is angle-bracketed."
    d = _write_dossier(
        tmp_path, family_md=_block(source_line=f"<{SRC}>", mechanism=mech),
        evidence_entries=[_ev("ev_t_0001", excerpt)], cache_text=cache_text)
    result = nz.normalize_dossier(d)
    assert result["kept"] is True and result["fixes"][0]["route"] == "source-url"
    assert aid.validate(d) == []


# ---------- (g) insertion fidelity ----------

def test_insertion_fidelity(tmp_path):
    excerpt = "fidelity check verbatim sentence in cache"
    cache_text = f"a\n{excerpt}\nb"
    mech = "A paraphrase to be replaced by the verbatim fidelity sentence."
    d = _write_dossier(
        tmp_path, family_md=_block(source_line=SRC, mechanism=mech),
        evidence_entries=[_ev("ev_t_0001", excerpt)],
        cache_text=cache_text)
    nz.normalize_dossier(d)
    out = (d / "agent_index" / "01_x.md").read_text()
    # Evidence bullet lands immediately after Status, at the bullet indent.
    assert ("  - **Status:** Verified (webfetch). cache_id `cache_t1`.\n"
            "  - **Evidence:** ev_t_0001\n") in out
    # Siblings byte-intact.
    assert "  - **Code:** —\n" in out
    assert "  - **Result:** see the contribution above.\n" in out
    assert "- **bibkey_t_2001**\n" in out


# ---------- (h) transactional restore: a residual reverts every touched file ----------

def test_transactional_restore_on_residual(tmp_path):
    good = "this verbatim sentence is present in the cache blob"
    bad = "this other sentence is absent from the cache blob entirely"
    cache_text = f"lead\n{good}\ntail"  # contains `good`, not `bad`
    b1 = _block(source_line=SRC, bibkey="bibkey_t_2001", with_bullet="ev_t_0001",
                mechanism="paraphrase of the present sentence")
    b2 = _block(source_line=SRC, bibkey="bibkey_t_2002", with_bullet="ev_t_0002",
                mechanism="paraphrase of the absent sentence")
    d = _write_dossier(
        tmp_path, family_md=b1 + "\n" + b2,
        evidence_entries=[_ev("ev_t_0001", good), _ev("ev_t_0002", bad)],
        cache_text=cache_text)
    before = (d / "agent_index" / "01_x.md").read_text()
    result = nz.normalize_dossier(d)
    assert len(result["fixes"]) == 1 and len(result["unresolved"]) == 1  # b1 fixable, b2 not
    assert result["kept"] is False and result["residual"]  # gate stays red on b2
    assert (d / "agent_index" / "01_x.md").read_text() == before  # b1's fix rolled back too


# ---------- unit: rewrite primitives ----------

def test_rewrite_mechanism_preserves_prefix_and_siblings():
    block = ("  - **Source:** https://x\n"
             "  - **Mechanism:** OLD editorial text\n"
             "  - **Result:** keep me\n")
    out = nz._rewrite_mechanism(block, "NEW verbatim excerpt")
    assert "  - **Mechanism:** NEW verbatim excerpt\n" in out
    assert "OLD editorial" not in out
    assert "  - **Source:** https://x\n" in out and "  - **Result:** keep me\n" in out


def test_ensure_evidence_bullet_after_status():
    block = ("  - **Mechanism:** m\n"
             "  - **Status:** Verified.\n")
    out = nz._ensure_evidence_bullet(block, "ev_z_0001")
    assert out == ("  - **Mechanism:** m\n"
                   "  - **Status:** Verified.\n"
                   "  - **Evidence:** ev_z_0001\n")
    # idempotent: a second call does not duplicate.
    assert nz._ensure_evidence_bullet(out, "ev_z_0001") == out

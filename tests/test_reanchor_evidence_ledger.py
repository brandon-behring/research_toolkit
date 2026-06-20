"""Tests for scripts/reanchor_evidence_ledger.py — the bulk evidence_ledger re-anchorer.

Covers the runbook's three required behaviours — (a) a raw-HTML-offset overflow re-anchors
clean against the extracted text, (b) an excerpt absent from the cache is REPORTED (re-gather),
never silently "fixed", (c) idempotency — plus format-preservation for both block- and
flow-style ``text_path_offset`` and the restore-on-bad-rewrite safety.

The novel script logic (plan/apply/rewrite) is unit-tested here against minimal fixtures;
the full evidence_ledger.validate green-gate integration is exercised by the live pilot.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import reanchor_evidence_ledger as rae  # noqa: E402
from validators.v2_common import verify_excerpt_anchor  # noqa: E402

CACHE_ID = "cache_t1"
CACHE_SHA = "a" * 64


def _make_dossier(
    tmp_path: Path, *, excerpt: str, cache_text: str, bad_offset: list[int],
    bad_sha: str = "b" * 64, style: str = "block",
) -> Path:
    """Write a minimal dossier (evidence_ledger.yml + cache_manifest.yml + text) with one
    entry whose anchor is deliberately broken (offset overflow / wrong sha)."""
    rel = f"text/sha256/{CACHE_SHA}.txt"
    tf = tmp_path / rel
    tf.parent.mkdir(parents=True, exist_ok=True)
    tf.write_text(cache_text, encoding="utf-8")
    (tmp_path / "cache_manifest.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 2, "topic": "t", "cache_root": str(tmp_path),
                "entries": [{
                    "cache_id": CACHE_ID, "source_url": "https://x", "sha256": CACHE_SHA,
                    "text_path": rel, "extraction_status": "ok",
                }],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    if style == "flow":
        off_block = f"      text_path_offset: [{bad_offset[0]}, {bad_offset[1]}]\n"
    else:
        off_block = f"      text_path_offset:\n      - {bad_offset[0]}\n      - {bad_offset[1]}\n"
    led = (
        "schema_version: 3\n"
        "entries:\n"
        "- evidence_id: ev_t_0001\n"
        "  supports:\n"
        "  - claim_id: claim_t_0001\n"
        "    extraction_method: verbatim_match\n"
        "    excerpt_anchor:\n"
        f"      cache_id: {CACHE_ID}\n"
        f"{off_block}"
        f"      sha256_of_span: {bad_sha}\n"
        f"  excerpt: '{excerpt}'\n"
    )
    (tmp_path / "evidence_ledger.yml").write_text(led, encoding="utf-8")
    return tmp_path


def _anchor_verifies(dossier: Path) -> list[str]:
    """Run the REAL verifier against the (single) anchor now in the written ledger."""
    led = yaml.safe_load((dossier / "evidence_ledger.yml").read_text())
    man = yaml.safe_load((dossier / "cache_manifest.yml").read_text())
    by_id = {e["cache_id"]: e for e in man["entries"]}
    entry = led["entries"][0]
    anchor = entry["supports"][0]["excerpt_anchor"]
    return verify_excerpt_anchor(
        excerpt=entry["excerpt"], cache_id=anchor["cache_id"],
        text_path_offset=anchor["text_path_offset"], sha256_of_span=anchor["sha256_of_span"],
        cache_entries_by_id=by_id, manifest_path=dossier / "cache_manifest.yml",
        loc="t", cache_root=man.get("cache_root"),
    )


# ---------- (a) raw-HTML-offset overflow re-anchors clean ----------

def test_overflow_offset_reanchors_clean(tmp_path: Path) -> None:
    excerpt = "the findable verbatim sentence"
    cache_text = f"header padding padding\n{excerpt}\nfooter trailing"  # short text
    dossier = _make_dossier(tmp_path, excerpt=excerpt, cache_text=cache_text,
                            bad_offset=[9000, 9030])  # overflows the short text
    plan = rae.plan_reanchor(dossier)
    assert len(plan["fixes"]) == 1 and len(plan["unresolved"]) == 0
    fx = plan["fixes"][0]
    assert fx["new_off"][1] <= len(cache_text.encode())  # within the extracted text
    rae.apply_reanchor(dossier, plan["fixes"])
    assert _anchor_verifies(dossier) == []  # the real /citation-audit check now passes


def test_overflow_reanchor_flow_style_preserved(tmp_path: Path) -> None:
    excerpt = "flow style anchor sentence"
    cache_text = f"x\n{excerpt}\ny"
    dossier = _make_dossier(tmp_path, excerpt=excerpt, cache_text=cache_text,
                            bad_offset=[5000, 5026], style="flow")
    plan = rae.plan_reanchor(dossier)
    rae.apply_reanchor(dossier, plan["fixes"])
    written = (dossier / "evidence_ledger.yml").read_text()
    assert "text_path_offset: [" in written  # flow style preserved (not expanded to block)
    assert _anchor_verifies(dossier) == []


# ---------- ambiguity: auto-resolve to first occurrence (loud, never a silent guess) ----------

def test_ambiguous_excerpt_auto_resolves_to_first_occurrence(tmp_path: Path) -> None:
    excerpt = "duplicated abstract line"
    cache_text = f"{excerpt}\n--meta--\n{excerpt}\n--body--"  # appears twice
    dossier = _make_dossier(tmp_path, excerpt=excerpt, cache_text=cache_text, bad_offset=[9000, 9024])
    plan = rae.plan_reanchor(dossier)
    assert len(plan["fixes"]) == 1 and len(plan["unresolved"]) == 0
    fx = plan["fixes"][0]
    assert "occurrence 1" in (fx.get("note") or "")
    assert fx["new_off"][0] == 0  # the FIRST occurrence
    rae.apply_reanchor(dossier, plan["fixes"])
    assert _anchor_verifies(dossier) == []


# ---------- (b) excerpt absent from cache -> reported, not fixed ----------

def test_absent_excerpt_reported_not_fixed(tmp_path: Path) -> None:
    dossier = _make_dossier(
        tmp_path, excerpt="a sentence that is nowhere in the cache",
        cache_text="completely unrelated cached body text", bad_offset=[9000, 9030],
    )
    before = (dossier / "evidence_ledger.yml").read_text()
    plan = rae.plan_reanchor(dossier)
    assert len(plan["fixes"]) == 0 and len(plan["unresolved"]) == 1
    assert "RE-GATHER" in plan["unresolved"][0]["reason"]
    rae.apply_reanchor(dossier, plan["fixes"])  # no fixes -> no-op
    assert (dossier / "evidence_ledger.yml").read_text() == before  # untouched


# ---------- (c) idempotency ----------

def test_idempotent_second_run_is_noop(tmp_path: Path) -> None:
    excerpt = "idempotent verbatim sentence here"
    dossier = _make_dossier(tmp_path, excerpt=excerpt,
                            cache_text=f"lead\n{excerpt}\ntail", bad_offset=[9000, 9033])
    plan1 = rae.plan_reanchor(dossier)
    rae.apply_reanchor(dossier, plan1["fixes"])
    after_first = (dossier / "evidence_ledger.yml").read_text()
    plan2 = rae.plan_reanchor(dossier)  # anchor now passes verify -> nothing to do
    assert plan2["fixes"] == [] and plan2["unresolved"] == []
    rae.apply_reanchor(dossier, plan2["fixes"])
    assert (dossier / "evidence_ledger.yml").read_text() == after_first


# ---------- format-preservation: only the targeted lines change ----------

def test_rewrite_block_changes_only_offset_and_sha() -> None:
    lines = (
        "    excerpt_anchor:\n"
        "      cache_id: cache_x\n"
        "      text_path_offset:\n"
        "      - 100\n"
        "      - 200\n"
        "      sha256_of_span: " + ("c" * 64) + "\n"
        "  excerpt: 'unchanged'\n"
    ).splitlines(keepends=True)
    ok = rae._rewrite_anchor_block(lines, "c" * 64, [7, 42], "d" * 64)
    out = "".join(lines)
    assert ok
    assert "- 7\n" in out and "- 42\n" in out and ("d" * 64) in out
    assert "cache_id: cache_x" in out and "excerpt: 'unchanged'" in out  # siblings intact
    assert "100" not in out and ("c" * 64) not in out


def test_rewrite_missing_sha_returns_false() -> None:
    lines = ["      sha256_of_span: " + ("e" * 64) + "\n"]
    assert rae._rewrite_anchor_block(lines, "f" * 64, [1, 2], "g" * 64) is False


# ---------- safety: a bad fix (sha not in file) restores + raises ----------

def test_apply_restores_on_unlocatable_block(tmp_path: Path) -> None:
    excerpt = "safety net sentence body"
    dossier = _make_dossier(tmp_path, excerpt=excerpt,
                            cache_text=f"a\n{excerpt}\nb", bad_offset=[9000, 9024])
    before = (dossier / "evidence_ledger.yml").read_text()
    bogus_fix = [{"evidence_id": "ev_t_0001", "cache_id": CACHE_ID, "old_off": [0, 1],
                  "old_sha": "0" * 64, "new_off": [1, 2], "new_sha": "1" * 64}]
    with pytest.raises(rae.ReanchorError):
        rae.apply_reanchor(dossier, bogus_fix)
    assert (dossier / "evidence_ledger.yml").read_text() == before  # restored/untouched

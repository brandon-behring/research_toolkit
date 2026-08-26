"""Real tests for verify_anchors.py.

The bar: every failure mode must be shown to FAIL. A checker demonstrated only on passing
input is indistinguishable from one that always passes.
"""

import hashlib
import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import verify_anchors as va


def build(tmp_path, text: bytes, span, *, root=None, sha_override=None,
          cache_id="cache_aaa", text_path="text/sha256/aaa.txt", manifest_cid=None):
    """Create a one-dossier corpus whose single atom anchors `span` of `text`."""
    cache = tmp_path / "cache"
    blob = cache / text_path
    blob.parent.mkdir(parents=True, exist_ok=True)
    blob.write_bytes(text)

    d = tmp_path / "research_x"
    d.mkdir(exist_ok=True)
    yaml.safe_dump({"cache_root": root or str(cache),
                    "entries": [{"cache_id": manifest_cid or cache_id,
                                 "text_path": text_path,
                                 "source_url": "https://example.org/p"}]},
                   (d / "cache_manifest.yml").open("w"))
    digest = sha_override or hashlib.sha256(text[span[0]:span[1]]).hexdigest()
    yaml.safe_dump({"entries": [{"evidence_id": "ev_1", "supports": [
        {"claim_id": "c1", "excerpt_anchor": {"cache_id": cache_id,
                                              "text_path_offset": list(span),
                                              "sha256_of_span": digest}}]}]},
                   (d / "evidence_ledger.yml").open("w"))
    return tmp_path


# ------------------------------------------------------------------ happy path

def test_matching_span_verifies(tmp_path):
    root = build(tmp_path, b"hello brave world", (6, 11))
    code, res = va.run(root, None)
    assert code == 0
    assert res["summary"]["verified"] == 1 and res["summary"]["mismatch"] == 0


# ------------------------------------------------------------------ THE byte trap

def test_offsets_are_bytes_not_characters(tmp_path):
    """The trap that agrees silently on ASCII.

    'café ' is 6 BYTES (é is 2) and 5 characters. A byte-slice of (6, 11) yields b'world';
    a character-slice of the decoded string yields 'orld' plus a stray byte. Only the byte
    reading reproduces a hash computed over bytes.
    """
    text = "café world".encode()          # b'caf\xc3\xa9 world' — 11 bytes, 10 chars
    assert len(text) == 11 and len("café world") == 10
    root = build(tmp_path, text, (6, 11))
    code, res = va.run(root, None)
    assert code == 0, res["dossiers"][0]["failures"]
    assert res["summary"]["verified"] == 1


def test_character_slicing_would_have_disagreed(tmp_path):
    """Pins the claim above: the two readings genuinely differ on this fixture, so the
    test would catch a regression to decode-then-slice rather than passing either way."""
    text = "café world".encode()
    by_bytes = hashlib.sha256(text[6:11]).hexdigest()
    by_chars = hashlib.sha256(text.decode()[6:11].encode()).hexdigest()
    assert by_bytes != by_chars


# ------------------------------------------------------------------ failure modes

def test_hash_mismatch_fails(tmp_path):
    root = build(tmp_path, b"hello brave world", (6, 11), sha_override="0" * 64)
    code, res = va.run(root, None)
    assert code == 1 and res["summary"]["mismatch"] == 1


def test_missing_blob_fails_not_warns(tmp_path):
    root = build(tmp_path, b"hello world", (0, 5))
    (tmp_path / "cache" / "text/sha256/aaa.txt").unlink()
    code, res = va.run(root, None)
    assert code == 1 and res["summary"]["missing_blob"] == 1


def test_cache_id_absent_from_manifest_fails(tmp_path):
    root = build(tmp_path, b"hello world", (0, 5), manifest_cid="cache_other")
    code, res = va.run(root, None)
    assert code == 1 and res["summary"]["unknown_cache_id"] == 1


# ------------------------------------------------------------------ three-state root

def test_absolute_unresolvable_root_is_a_manifest_defect(tmp_path):
    """The silent-proceed this tool exists to stop: a /Users path on a Linux box must not
    read as 'cold cache'."""
    root = build(tmp_path, b"hello world", (0, 5), root="/Users/nobody/research_cache")
    code, res = va.run(root, None)
    assert code == 1
    assert res["summary"]["root_defect"] == 1
    assert res["dossiers"][0]["root_state"] == "defect"


def test_tilde_relative_absent_root_is_a_clean_checkout_skip(tmp_path):
    """A clean checkout with no cache must not fail — that would make the gate unusable."""
    root = build(tmp_path, b"hello world", (0, 5), root="~/nonexistent_cache_xyz")
    code, res = va.run(root, None)
    assert code == 0
    assert res["summary"]["root_cold"] == 1 and res["summary"]["verified"] == 0


def test_defect_and_cold_are_not_conflated(tmp_path):
    a = build(tmp_path, b"hello world", (0, 5), root="/Users/nobody/x")
    code, res = va.run(a, None)
    assert res["summary"]["root_defect"] == 1 and res["summary"]["root_cold"] == 0


# ------------------------------------------------------------------ reporting

def _unanchored(tmp_path, method):
    d = tmp_path / "research_y"
    d.mkdir(exist_ok=True)
    yaml.safe_dump({"cache_root": str(tmp_path), "entries": []},
                   (d / "cache_manifest.yml").open("w"))
    sup = {"claim_id": "c"}
    if method:
        sup["extraction_method"] = method
    yaml.safe_dump({"entries": [{"evidence_id": "e", "supports": [sup]}]},
                   (d / "evidence_ledger.yml").open("w"))
    return va.run(tmp_path, None)


def test_supports_row_without_an_anchor_is_counted_not_silently_dropped(tmp_path):
    code, res = _unanchored(tmp_path, None)
    assert res["summary"]["no_anchor_other"] == 1 and res["summary"]["atoms"] == 0


def test_paraphrase_without_an_anchor_is_correct_not_a_gap(tmp_path):
    """A paraphrase cannot carry a verbatim span. Bucketing it with genuinely unanchored
    rows invites the next reader to see a gap where there is none."""
    code, res = _unanchored(tmp_path, "paraphrase")
    assert res["summary"]["no_anchor_paraphrase"] == 1
    assert res["summary"]["no_anchor_other"] == 0


def test_neither_unanchored_bucket_is_a_failure(tmp_path):
    for method in (None, "paraphrase"):
        code, _ = _unanchored(tmp_path, method)
        assert code == 0


def test_render_marks_pass_and_fail(tmp_path):
    root = build(tmp_path, b"hello brave world", (6, 11))
    _, ok = va.run(root, None)
    assert "**PASS**" in va.render(ok)
    root2 = build(tmp_path / "b", b"hello brave world", (6, 11), sha_override="0" * 64)
    _, bad = va.run(root2, None)
    assert "**FAIL**" in va.render(bad)


def test_dossier_filter_restricts_scope(tmp_path):
    build(tmp_path, b"hello brave world", (6, 11))
    code, res = va.run(tmp_path, ["research_nope"])
    assert res["summary"]["dossiers"] == 0

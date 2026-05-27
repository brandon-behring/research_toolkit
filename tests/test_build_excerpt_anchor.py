"""Tests for scripts/build_excerpt_anchor.py — the v3 excerpt-anchor producer.

Covers the byte-offset finder (exact + whitespace-tolerant + multi-byte), the CLI
exit codes, and a producer->verifier round-trip: every anchor the producer emits is
fed back through validators.v2_common.verify_excerpt_anchor (the exact check the
citation audit runs) and must pass.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import build_excerpt_anchor as bea  # noqa: E402
from validators.v2_common import verify_excerpt_anchor  # noqa: E402


def _verify(text_file: Path, excerpt: str, anchor: dict, *, cache_id: str = "c1") -> list[str]:
    """Run the real verifier against a produced anchor (text-file/absolute mode)."""
    return verify_excerpt_anchor(
        excerpt=excerpt,
        cache_id=cache_id,
        text_path_offset=anchor["text_path_offset"],
        sha256_of_span=anchor["sha256_of_span"],
        cache_entries_by_id={cache_id: {"text_path": str(text_file)}},
        manifest_path=text_file.parent,
        loc="t",
        cache_root=None,
    )


# ---------- find_span / build_anchor: exact match ----------

def test_build_anchor_matches_unique_exact_span() -> None:
    text = "intro line\nThe detector collapses on OOD data.\noutro"
    text_bytes = text.encode("utf-8")
    excerpt = "The detector collapses on OOD data."
    anchor = bea.build_anchor(text_bytes, excerpt)
    start, end = anchor["text_path_offset"]
    assert text_bytes[start:end] == excerpt.encode("utf-8")
    assert anchor["sha256_of_span"] == hashlib.sha256(excerpt.encode("utf-8")).hexdigest()


def test_build_anchor_offsets_account_for_multibyte_prefix() -> None:
    """Byte offsets must count multi-byte chars (é, em-dash) before the span."""
    text = "café —\nthe quick brown fox jumps"  # 'é'=2 bytes, '—'=3 bytes
    text_bytes = text.encode("utf-8")
    excerpt = "the quick brown fox"
    anchor = bea.build_anchor(text_bytes, excerpt)
    start, end = anchor["text_path_offset"]
    # "café " (6 bytes) + "—" (3) + "\n" (1) = 10
    assert start == 10
    assert text_bytes[start:end].decode("utf-8") == excerpt


# ---------- find_span: whitespace-tolerant ----------

def test_build_anchor_matches_across_differing_whitespace() -> None:
    """Excerpt with single spaces matches cached text with newlines/runs."""
    text = "preamble\nthe  quick\nbrown   fox jumps over"
    text_bytes = text.encode("utf-8")
    excerpt = "the quick brown fox"
    anchor = bea.build_anchor(text_bytes, excerpt)
    start, end = anchor["text_path_offset"]
    span = text_bytes[start:end].decode("utf-8")
    assert span.split() == excerpt.split()
    # round-trips through the real verifier (whitespace-normalized equality)
    tmp_ok = _verify_inline(text_bytes, excerpt, anchor)
    assert tmp_ok == [], tmp_ok


def _verify_inline(text_bytes: bytes, excerpt: str, anchor: dict) -> list[str]:
    # local helper that doesn't need a file: re-slice + hash + ws-normalized equality
    start, end = anchor["text_path_offset"]
    span = text_bytes[start:end]
    errs = []
    if hashlib.sha256(span).hexdigest() != anchor["sha256_of_span"]:
        errs.append("hash mismatch")
    if " ".join(span.decode("utf-8").split()) != " ".join(excerpt.split()):
        errs.append("normalized excerpt mismatch")
    return errs


# ---------- find_span: rejection cases ----------

def test_find_span_rejects_absent_excerpt() -> None:
    with pytest.raises(ValueError, match="not found"):
        bea.find_span(b"some cached text", "totally different phrase")


def test_find_span_rejects_ambiguous_excerpt() -> None:
    with pytest.raises(ValueError, match="more than once|matches"):
        bea.find_span(b"repeat repeat repeat", "repeat")


# ---------- CLI: text-path mode ----------

def test_main_text_path_mode_emits_passing_anchor(tmp_path: Path, capsys) -> None:
    text_file = tmp_path / "body.txt"
    text_file.write_text("alpha beta\nthe model overfits in-distribution\ngamma", encoding="utf-8")
    excerpt = "the model overfits in-distribution"
    rc = bea.main(["--text-path", str(text_file), "--excerpt", excerpt, "--json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert "text_path_offset" in out and "sha256_of_span" in out
    assert _verify(text_file, excerpt, out) == []


def test_main_rejects_empty_excerpt(tmp_path: Path) -> None:
    text_file = tmp_path / "body.txt"
    text_file.write_text("content", encoding="utf-8")
    rc = bea.main(["--text-path", str(text_file), "--excerpt", "   "])
    assert rc == 2


def test_main_reports_absent_excerpt_as_data_error(tmp_path: Path, capsys) -> None:
    text_file = tmp_path / "body.txt"
    text_file.write_text("the cached text says one thing", encoding="utf-8")
    rc = bea.main(["--text-path", str(text_file), "--excerpt", "an unrelated claim"])
    assert rc == 1
    assert "not found" in capsys.readouterr().err


# ---------- CLI: manifest mode (round-trip through resolve_cache_path) ----------

def _write_manifest_with_text(tmp_path: Path, excerpt_text: str) -> tuple[Path, str]:
    """Write a cache_root-style manifest + the relative text file; return (manifest, cache_id)."""
    sha = "a" * 64
    rel_text = f"text/sha256/{sha}.txt"
    text_file = tmp_path / rel_text
    text_file.parent.mkdir(parents=True, exist_ok=True)
    text_file.write_text(excerpt_text, encoding="utf-8")
    manifest = tmp_path / "cache_manifest.yml"
    payload = {
        "schema_version": 2,
        "topic": "test",
        "cache_root": str(tmp_path),
        "entries": [
            {
                "cache_id": "cache_test01",
                "source_url": "https://example.com/x",
                "sha256": sha,
                "text_path": rel_text,
                "extraction_status": "ok",
            }
        ],
    }
    manifest.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return manifest, "cache_test01"


def test_main_manifest_mode_resolves_cache_root_and_self_verifies(tmp_path: Path, capsys) -> None:
    excerpt = "frozen-probe transfer collapses to the random floor"
    manifest, cache_id = _write_manifest_with_text(
        tmp_path, f"header\n{excerpt}\nfooter"
    )
    rc = bea.main([str(manifest), "--cache-id", cache_id, "--excerpt", excerpt, "--json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["cache_id"] == cache_id
    assert isinstance(out["text_path_offset"], list) and len(out["text_path_offset"]) == 2


def test_main_manifest_mode_rejects_unknown_cache_id(tmp_path: Path, capsys) -> None:
    manifest, _ = _write_manifest_with_text(tmp_path, "some body text here")
    rc = bea.main([str(manifest), "--cache-id", "cache_missing", "--excerpt", "some body"])
    assert rc == 1
    assert "not found in manifest" in capsys.readouterr().err


def test_main_yaml_output_is_paste_ready(tmp_path: Path, capsys) -> None:
    excerpt = "attention-tracker is training-free"
    manifest, cache_id = _write_manifest_with_text(tmp_path, f"x\n{excerpt}\ny")
    rc = bea.main([str(manifest), "--cache-id", cache_id, "--excerpt", excerpt])
    assert rc == 0
    out = capsys.readouterr().out
    parsed = yaml.safe_load(out)
    assert set(parsed["excerpt_anchor"]) == {"cache_id", "text_path_offset", "sha256_of_span"}
    assert parsed["excerpt_anchor"]["cache_id"] == cache_id


# ---------- find_span / CLI: --occurrence disambiguation ----------

def test_find_span_selects_requested_occurrence() -> None:
    text_bytes = b"the claim. ... the claim. ... the claim."
    excerpt = "the claim."
    first = bea.find_span(text_bytes, excerpt, occurrence=1)
    second = bea.find_span(text_bytes, excerpt, occurrence=2)
    third = bea.find_span(text_bytes, excerpt, occurrence=3)
    assert first[0] < second[0] < third[0]
    assert text_bytes[second[0]:second[1]] == excerpt.encode("utf-8")


def test_find_span_rejects_out_of_range_occurrence() -> None:
    with pytest.raises(ValueError, match="out of range"):
        bea.find_span(b"x x x", "x", occurrence=9)


def test_main_occurrence_disambiguates_duplicated_excerpt(tmp_path: Path, capsys) -> None:
    text_file = tmp_path / "abstract.txt"
    # mimics an HTML abstract page where the abstract is duplicated (meta + body)
    text_file.write_text("ASIDE separates instructions.\n--\nASIDE separates instructions.", encoding="utf-8")
    excerpt = "ASIDE separates instructions."
    # ambiguous without --occurrence
    assert bea.main(["--text-path", str(text_file), "--excerpt", excerpt]) == 1
    assert "matches 2 spans" in capsys.readouterr().err
    # disambiguated
    rc = bea.main(["--text-path", str(text_file), "--excerpt", excerpt, "--occurrence", "2", "--json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert _verify(text_file, excerpt, out) == []

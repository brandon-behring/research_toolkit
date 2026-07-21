"""Tests for validators/bibtex_out.py — the emitted-.bib schema validator."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from validators import bibtex_out  # type: ignore[import-not-found]  # noqa: E402

_GOOD = (
    "@misc{doe2023x,\n"
    "  author       = {Doe, Jane and Roe, Richard},\n"
    "  title        = {A Perfectly Valid Title},\n"
    "  year         = {2023},\n"
    "}\n"
)


def test_bibtex_out_accepts_a_valid_entry() -> None:
    assert bibtex_out.validate_text(_GOOD) == []


def test_bibtex_out_rejects_a_file_with_no_entries() -> None:
    errors = bibtex_out.validate_text("% just a comment, no entries\n")
    assert any("no BibTeX entries" in e for e in errors), errors


def test_bibtex_out_detects_duplicate_keys() -> None:
    errors = bibtex_out.validate_text(_GOOD + "\n" + _GOOD)
    assert any("duplicate entry key: doe2023x" in e for e in errors), errors


def test_bibtex_out_detects_missing_required_field() -> None:
    entry = "@misc{no2023author,\n  title = {T},\n  year = {2023},\n}\n"
    errors = bibtex_out.validate_text(entry)
    assert any("missing required field 'author'" in e for e in errors), errors


def test_bibtex_out_detects_escaped_braces() -> None:
    entry = "@misc{bad2023braces,\n  author = {Doe, J},\n  title = {The \\{DNA\\} of X},\n}\n"
    errors = bibtex_out.validate_text(entry)
    assert any("brace" in e for e in errors), errors


def test_bibtex_out_validate_rejects_a_directory(tmp_path) -> None:
    errors = bibtex_out.validate(tmp_path)
    assert any("got directory" in e for e in errors), errors

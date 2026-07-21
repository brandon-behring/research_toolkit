"""Tests for scripts/emit_bibtex.py — ledger→BibTeX with cache-resolved authors.

Hand-rolled synthetic fixtures (a ledger + manifest + a cached /abs/ blob with
Highwire tags) under tmp_path; no network (--no-live) and no unittest.mock.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import emit_bibtex  # type: ignore[import-not-found]  # noqa: E402

_ABS_HTML = (
    "<html><head>\n"
    '<meta name="citation_author" content="Tschannen, Michael" />\n'
    '<meta name="citation_author" content="Zhai, Xiaohua" />\n'
    '<meta name="citation_title" content="SigLIP 2: Better Encoders" />\n'
    '<meta name="citation_date" content="2025/02/20" />\n'
    '<meta name="citation_arxiv_id" content="2502.14786" />\n'
    "</head></html>"
)


def _make_dossier(tmp_path: Path) -> Path:
    """A synthetic dossier: one arXiv entry (cache HAS Highwire tags) + one non-arXiv."""
    blob = tmp_path / "cache" / "text" / "sha256" / "abc.txt"
    blob.parent.mkdir(parents=True)
    blob.write_text(_ABS_HTML, encoding="utf-8")
    dossier = tmp_path / "dossier"
    dossier.mkdir()
    (dossier / "bib_ledger.yml").write_text(
        yaml.safe_dump({
            "entries": [
                {
                    "bibkey": "siglip2",
                    "primary_url": "https://arxiv.org/abs/2502.14786",
                    "title": "wrong display title",
                    "authors": "Tschannen et al. (2025)",
                    "cache_ids": ["cache_abc"],
                },
                {
                    "bibkey": "meta2024repo",
                    "primary_url": "https://github.com/meta/x",
                    "title": "A Repository",
                    "authors": "Meta AI (2024)",
                    "published_online": "2024-01-01",
                },
            ]
        }),
        encoding="utf-8",
    )
    (dossier / "cache_manifest.yml").write_text(
        yaml.safe_dump({
            "cache_root": str(tmp_path / "cache"),
            "entries": [{
                "cache_id": "cache_abc",
                "source_url": "https://arxiv.org/abs/2502.14786",
                "text_path": "text/sha256/abc.txt",
            }],
        }),
        encoding="utf-8",
    )
    return dossier


def test_emit_bibtex_resolves_authors_from_cached_highwire_tags(tmp_path) -> None:
    out = tmp_path / "refs.bib"
    assert emit_bibtex.main([str(_make_dossier(tmp_path)), "--no-live", "--out", str(out)]) == 0
    text = out.read_text()
    assert "author       = {Tschannen, Michael and Zhai, Xiaohua}" in text
    assert "Tschannen et al." not in text  # the ledger display string is NOT used
    assert "SigLIP 2: Better Encoders" in text  # cache title overrides the ledger's wrong title
    assert "eprint       = {2502.14786}" in text
    assert "archiveprefix = {arXiv}," in text


def test_emit_bibtex_falls_back_to_display_string_for_non_arxiv(tmp_path, capsys) -> None:
    out = tmp_path / "refs.bib"
    emit_bibtex.main([str(_make_dossier(tmp_path)), "--no-live", "--out", str(out)])
    text = out.read_text()
    assert "author       = {Meta AI (2024)}" in text  # display string kept as-is
    assert "year         = {2024}" in text  # from published_online
    err = capsys.readouterr().err
    assert "display-string authors" in err and "meta2024repo" in err  # flagged, not hidden


def test_emit_bibtex_escapes_specials_but_never_braces() -> None:
    assert emit_bibtex.bib_escape("AT&T 50% #1 x_y $z") == r"AT\&T 50\% \#1 x\_y \$z"
    assert emit_bibtex.bib_escape("The {DNA} of X") == "The {DNA} of X"  # braces untouched


def test_emit_bibtex_dedups_a_bibkey_repeated_across_dossiers(tmp_path) -> None:
    d1 = _make_dossier(tmp_path)
    d2 = tmp_path / "d2"
    d2.mkdir()
    (d2 / "bib_ledger.yml").write_text(
        yaml.safe_dump({"entries": [{
            "bibkey": "meta2024repo", "primary_url": "https://github.com/meta/x",
            "title": "A Repository", "authors": "Meta AI (2024)",
        }]}),
        encoding="utf-8",
    )
    out = tmp_path / "refs.bib"
    emit_bibtex.main([str(d1), str(d2), "--no-live", "--out", str(out)])
    assert out.read_text().count("@misc{meta2024repo,") == 1


def test_emit_bibtex_seed_wins_over_a_duplicate_ledger_key(tmp_path) -> None:
    seed = tmp_path / "seed.bib"
    seed.write_text("@misc{meta2024repo,\n  author = {Hand, Verified},\n  title = {Seed Entry},\n}\n")
    out = tmp_path / "refs.bib"
    emit_bibtex.main([str(_make_dossier(tmp_path)), "--no-live", "--seed", str(seed), "--out", str(out)])
    text = out.read_text()
    assert text.count("@misc{meta2024repo,") == 1  # not duplicated
    assert "Hand, Verified" in text  # the hand-verified seed version is the one kept


def test_emit_bibtex_rejects_a_missing_source(tmp_path) -> None:
    assert emit_bibtex.main([str(tmp_path / "does_not_exist"), "--no-live"]) == 2


def test_emit_bibtex_no_overwrite_refuses_an_existing_out(tmp_path) -> None:
    out = tmp_path / "refs.bib"
    out.write_text("do not clobber")
    rc = emit_bibtex.main([str(_make_dossier(tmp_path)), "--no-live", "--out", str(out), "--no-overwrite"])
    assert rc == 2
    assert out.read_text() == "do not clobber"


def test_to_last_first_normalises_atom_name_order() -> None:
    assert emit_bibtex._to_last_first("Michael Tschannen") == "Tschannen, Michael"
    assert emit_bibtex._to_last_first("Zhai, Xiaohua") == "Zhai, Xiaohua"  # already Family, Given
    assert emit_bibtex._to_last_first("Plato") == "Plato"  # single token unchanged

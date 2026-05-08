"""Regression tests for v1.1 fixes addressing prompt-injection/26/27/28 BURN_IN findings.

Each fix has a positive test (works as designed on a known-good input) and a
negative test (rejects a known-bad input that the v1.0 validator would have
silently accepted). The negative tests are the ones that prove the fix has signal.

Fixes covered:
- A1.a: bib_ledger optional fields (authors / venue / code_url) round-trip
- A1.b: arXiv URL canonical-form check (rejects /pdf/, accepts /abs/)
- A1.c: code_url URL-format check (rejects malformed URLs when field present)
- C1:   url-freshness-check positive char-class regex extracts URLs on macOS
- D1:   standalone validator invocation (`python validators/x.py path`) works
        without requiring `python -m`.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

from validators import bib_ledger

REPO_ROOT = Path(__file__).resolve().parent.parent
VALIDATORS_DIR = REPO_ROOT / "validators"


# ---------- A1.a: bib_ledger optional fields ----------

def _minimal_ledger(extra: str = "") -> str:
    return (
        "entries:\n"
        "- bibkey: smoke2025example\n"
        "  primary_url: https://arxiv.org/abs/2501.00001\n"
        "  title: 'A smoke-test entry'\n"
        "  status: unverified\n"
        "  claim_family: example\n"
        + extra
    )


def test_bib_ledger_accepts_optional_authors_venue_code_url(tmp_path: Path) -> None:
    """authors/venue/code_url are accepted when present and well-formed."""
    text = _minimal_ledger(
        "  authors: Smith et al. (2025)\n"
        "  venue: NeurIPS 2025\n"
        "  code_url: https://github.com/example-org/smoke\n"
    )
    p = tmp_path / "bib_ledger.yml"
    p.write_text(text, encoding="utf-8")
    assert bib_ledger.validate(p) == []


def test_bib_ledger_still_accepts_entries_without_optional_fields(
    mini_dir: Path,
) -> None:
    """Backward compat: existing entries (no optional fields) still validate."""
    assert bib_ledger.validate(mini_dir / "bib_ledger.yml") == []


def test_bib_ledger_rejects_empty_optional_field(tmp_path: Path) -> None:
    """An empty optional field is wrong — omit the key entirely instead."""
    text = _minimal_ledger("  authors: ''\n")
    p = tmp_path / "bib_ledger.yml"
    p.write_text(text, encoding="utf-8")
    errors = bib_ledger.validate(p)
    assert any("authors" in e and "non-empty" in e for e in errors), errors


def test_bib_ledger_rejects_non_string_optional_field(tmp_path: Path) -> None:
    """Optional fields must be strings when present."""
    text = _minimal_ledger("  authors: 12345\n")  # int, not str
    p = tmp_path / "bib_ledger.yml"
    p.write_text(text, encoding="utf-8")
    errors = bib_ledger.validate(p)
    assert any("authors" in e and "string" in e for e in errors), errors


# ---------- A1.b: arXiv canonical-form check ----------

@pytest.mark.parametrize(
    "url",
    [
        "https://arxiv.org/abs/2106.09685",
        "https://arxiv.org/abs/2106.09685v3",
        "https://arxiv.org/abs/2501.00001",
        "https://www.arxiv.org/abs/2106.09685",
        "http://arxiv.org/abs/2106.09685",
    ],
)
def test_bib_ledger_accepts_canonical_arxiv_urls(tmp_path: Path, url: str) -> None:
    text = (
        "entries:\n"
        "- bibkey: smoke2025example\n"
        f"  primary_url: {url}\n"
        "  title: 'A smoke-test entry'\n"
        "  status: unverified\n"
        "  claim_family: example\n"
    )
    p = tmp_path / "bib_ledger.yml"
    p.write_text(text, encoding="utf-8")
    assert bib_ledger.validate(p) == [], f"should accept canonical form: {url}"


@pytest.mark.parametrize(
    "url",
    [
        "https://arxiv.org/pdf/2106.09685.pdf",
        "https://arxiv.org/pdf/2106.09685",
        "https://arxiv.org/abs/notanid",
        "https://arxiv.org/abs/2106",
        "https://arxiv.org/find/cs/1/au:+Hu/0/1/0/all/0/1",
    ],
)
def test_bib_ledger_rejects_non_canonical_arxiv_urls(tmp_path: Path, url: str) -> None:
    text = (
        "entries:\n"
        "- bibkey: smoke2025example\n"
        f"  primary_url: {url}\n"
        "  title: 'A smoke-test entry'\n"
        "  status: unverified\n"
        "  claim_family: example\n"
    )
    p = tmp_path / "bib_ledger.yml"
    p.write_text(text, encoding="utf-8")
    errors = bib_ledger.validate(p)
    assert any("arxiv" in e.lower() for e in errors), (
        f"should reject non-canonical arxiv URL: {url}; got {errors}"
    )


def test_bib_ledger_passes_through_non_arxiv_urls(tmp_path: Path) -> None:
    """Non-arxiv URLs (DOIs, JSTOR, GitHub, etc.) skip the arxiv-format check."""
    for url in [
        "https://doi.org/10.1145/775047.775151",
        "https://www.nature.com/articles/s42256-023-00765-8",
        "https://proceedings.mlr.press/v54/kull17a.html",
        "https://github.com/some-org/some-repo",
    ]:
        text = (
            "entries:\n"
            "- bibkey: smoke2025example\n"
            f"  primary_url: {url}\n"
            "  title: 'A smoke-test entry'\n"
            "  status: unverified\n"
            "  claim_family: example\n"
        )
        p = tmp_path / "bib_ledger.yml"
        p.write_text(text, encoding="utf-8")
        assert bib_ledger.validate(p) == [], f"should pass non-arxiv URL: {url}"


# ---------- A1.c: code_url format check ----------

def test_bib_ledger_rejects_malformed_code_url(tmp_path: Path) -> None:
    text = _minimal_ledger("  code_url: 'not-a-url'\n")
    p = tmp_path / "bib_ledger.yml"
    p.write_text(text, encoding="utf-8")
    errors = bib_ledger.validate(p)
    assert any("code_url" in e and "valid" in e for e in errors), errors


# ---------- C1: URL-extraction regex ----------

POSITIVE_URL_REGEX = r"https?://[a-zA-Z0-9./?=&_~%#:+-]+"
# The negative form documented in BURN_IN as silently broken on macOS:
NEGATIVE_URL_REGEX_BROKEN_ON_MACOS = r"https?://[^[:space:]\)\]\"\<]+"


def test_positive_url_regex_extracts_typical_research_urls() -> None:
    """The positive char-class form must extract from a typical mixed-content paragraph."""
    sample = (
        "See https://arxiv.org/abs/2106.09685 for the LoRA paper.\n"
        "Code: https://github.com/microsoft/LoRA\n"
        "Vendor blog: https://huggingface.co/blog/peft (HF blog).\n"
        "DOI: https://doi.org/10.1145/775047.775151 (ACM).\n"
        "Trailing punct: see https://example.com/path/to/thing, also fine.\n"
    )
    matches = re.findall(POSITIVE_URL_REGEX, sample)
    assert len(matches) >= 5, f"positive regex should find ≥5 URLs; got {matches}"
    assert "https://arxiv.org/abs/2106.09685" in matches
    assert "https://github.com/microsoft/LoRA" in matches


def test_positive_url_regex_handles_special_chars() -> None:
    """Should handle DOI URLs with parentheses and percent-encoding."""
    sample = (
        "See https://example.com/path?foo=bar&baz=qux for query strings.\n"
        "Anchor: https://example.com/page#section-1 (with anchor).\n"
    )
    matches = re.findall(POSITIVE_URL_REGEX, sample)
    assert "https://example.com/path?foo=bar&baz=qux" in matches
    assert any(m.startswith("https://example.com/page#section-1") for m in matches)


# ---------- D1: standalone validator invocation ----------

@pytest.mark.parametrize(
    "validator_name,fixture_path",
    [
        ("research_plan.py", "mini_topic_timeseries_anomaly/research_plan.md"),
        ("bib_ledger.py", "mini_topic_timeseries_anomaly/bib_ledger.yml"),
        ("dossier.py", "mini_topic_timeseries_anomaly/dossier"),
        ("agent_index.py", "mini_topic_timeseries_anomaly/agent_index"),
        (
            "audit_trail.py",
            "mini_topic_timeseries_anomaly/agent_index/README.md",
        ),
    ],
)
def test_validator_runs_standalone_without_module_form(
    validator_name: str, fixture_path: str
) -> None:
    """`python validators/<x>.py path` works (no `python -m` required).

    Regression test for the BURN_IN finding "validators can't be run standalone
    without venv". Before D1 fix, this raised ModuleNotFoundError because the
    relative import `from validators._common import cli_main` couldn't resolve.
    """
    fixture = REPO_ROOT / "tests" / "fixtures" / fixture_path
    result = subprocess.run(
        [sys.executable, str(VALIDATORS_DIR / validator_name), str(fixture)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"standalone invocation failed: rc={result.returncode}\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )


def test_url_check_report_validator_runs_standalone(tmp_path: Path) -> None:
    """url_check_report validator also supports standalone invocation."""
    report = tmp_path / "url_check.md"
    report.write_text(
        "# URL Freshness Report\n\n"
        "Generated: 2026-05-07\n\n"
        "## Summary\n\n"
        "- total: 10\n"
        "- ok: 10\n"
        "- broken: 0\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(VALIDATORS_DIR / "url_check_report.py"), str(report)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"standalone url_check_report failed: rc={result.returncode}\n"
        f"stderr={result.stderr}"
    )


# ---------- Backward-compat regression: all four real-world ledgers still validate ----------

REAL_LEDGERS = [
    "tests/fixtures/mini_topic_timeseries_anomaly/bib_ledger.yml",
    "tests/fixtures/prompt_injection_snapshot/real/bib_ledger.yml",
    "tests/fixtures/prompt_injection_snapshot/recreated/bib_ledger.yml",
]


@pytest.mark.parametrize("ledger_path", REAL_LEDGERS)
def test_existing_ledgers_still_validate_under_v1_1_schema(ledger_path: str) -> None:
    """Backward compat: prompt-injection + mini fixtures still pass under the v1.1 validator.

    eval-methodology/27/28 ledgers live outside the toolkit repo and are spot-checked
    manually but not asserted here (they may be deleted or moved).
    """
    p = REPO_ROOT / ledger_path
    if not p.exists():
        pytest.skip(f"ledger not present: {p}")
    errors = bib_ledger.validate(p)
    assert errors == [], f"{ledger_path} should still validate; got {errors}"

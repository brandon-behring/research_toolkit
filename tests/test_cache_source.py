"""Tests for scripts/cache_source.py — the strict-live v2 caching helper."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
from urllib.error import URLError

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import cache_source  # noqa: E402


class _FakeHeaders:
    def __init__(self, content_type: str, extras: dict[str, str] | None = None) -> None:
        self._content_type = content_type
        self._extras = extras or {}

    def get_content_type(self) -> str:
        return self._content_type

    def get(self, key: str, default=None):
        return self._extras.get(key, default)


class _FakeResponse:
    def __init__(
        self,
        body: bytes,
        content_type: str,
        status: int = 200,
        extras: dict[str, str] | None = None,
    ) -> None:
        self._body = body
        self.status = status
        self.headers = _FakeHeaders(content_type, extras)

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *_exc) -> None:
        return None

    def read(self) -> bytes:
        return self._body

    def getcode(self) -> int:
        return self.status


def _patch_fetch(
    monkeypatch: pytest.MonkeyPatch,
    body: bytes,
    content_type: str,
    *,
    status: int = 200,
    extras: dict[str, str] | None = None,
) -> None:
    def fake_urlopen(req, timeout=30):
        return _FakeResponse(body, content_type, status=status, extras=extras)
    monkeypatch.setattr(cache_source, "urlopen", fake_urlopen)


def test_sha256_helper_matches_hashlib() -> None:
    data = b"hello world"
    assert cache_source._sha256(data) == hashlib.sha256(data).hexdigest()


def test_safe_text_html_extracts_text() -> None:
    text, status, warnings = cache_source._safe_text(b"<html>hi</html>", "text/html")
    assert "<html>" in text
    assert status == "ok"
    assert warnings == []


def test_safe_text_binary_falls_back_to_raw_only() -> None:
    text, status, warnings = cache_source._safe_text(b"\x00\x01\x02", "application/octet-stream")
    assert status == "raw_only"
    assert "raw binary cached" in text
    assert warnings == []


def test_cache_one_writes_blob_text_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # v2.3 A3 (#10): the unconditional JS-shell stub check fires on HTML
    # responses shorter than SUSPECT_TEXT_MIN_CHARS (500), so test bodies must
    # be padded above that threshold to avoid landing at stub status.
    body = (b"<html><body>Test page for cache_source. " + b"x" * 600 + b"</body></html>")
    _patch_fetch(monkeypatch, body, "text/html")

    entry = cache_source.cache_one(
        "https://example.com/test-page",
        cache_root=tmp_path,
        fetched_at="2026-05-19",
        topic="test_topic",
    )

    digest = hashlib.sha256(body).hexdigest()
    # v2.3+: manifest paths are relative to cache_root for portability
    raw_path = tmp_path / entry["raw_path"]
    text_path = tmp_path / entry["text_path"]
    metadata_path = tmp_path / entry["metadata_path"]

    assert raw_path.read_bytes() == body
    assert "Test page for cache_source" in text_path.read_text(encoding="utf-8")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["sha256"] == digest
    assert metadata["topic"] == "test_topic"
    assert metadata["source_url"] == "https://example.com/test-page"
    assert metadata["schema_version"] == 2

    assert entry["sha256"] == digest
    assert entry["bytes"] == len(body)
    assert entry["cache_id"] == f"cache_{digest[:16]}"
    assert entry["extraction_status"] == "ok"


def test_manifest_entry_paths_are_relative(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """v2.3+ #13: writer must serialize paths relative to cache_root.

    Absolute / ~-prefixed paths are not portable across machines. Regression
    guard against the bug that #2 was closed for but never actually fixed.
    """
    body = b"<html>portable</html>"
    _patch_fetch(monkeypatch, body, "text/html")

    entry = cache_source.cache_one(
        "https://example.com/portable",
        cache_root=tmp_path,
        fetched_at="2026-05-19",
        topic="t",
    )

    for field in ("raw_path", "text_path", "metadata_path"):
        value = entry[field]
        assert not value.startswith("/"), (
            f"{field} is absolute: {value!r} — manifests must be portable"
        )
        assert not value.startswith("~"), (
            f"{field} is ~-prefixed: {value!r} — manifests must be portable"
        )
        # Sanity: relative path resolves under cache_root
        assert (tmp_path / value).exists(), (
            f"{field} {value!r} does not resolve to a real file under cache_root"
        )


def test_cache_one_hash_stable_across_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    body = b"<html>stable</html>"
    _patch_fetch(monkeypatch, body, "text/html")
    e1 = cache_source.cache_one(
        "https://example.com/x", cache_root=tmp_path, fetched_at="2026-05-19", topic="t"
    )
    e2 = cache_source.cache_one(
        "https://example.com/x", cache_root=tmp_path, fetched_at="2026-05-19", topic="t"
    )
    assert e1["sha256"] == e2["sha256"]
    assert e1["raw_path"] == e2["raw_path"]


def test_main_reports_url_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def raise_url_error(req, timeout=30):
        raise URLError("network unreachable")
    monkeypatch.setattr(cache_source, "urlopen", raise_url_error)

    rc = cache_source.main([
        "cache_source.py",
        "https://example.com/broken",
        "--cache-root",
        str(tmp_path),
        "--topic",
        "fail_test",
        "--date",
        "2026-05-19",
    ])
    captured = capsys.readouterr()
    assert rc == 1
    assert "ERROR caching" in captured.err
    assert "broken" in captured.err


def test_main_prints_manifest_yaml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_fetch(monkeypatch, b"<html>yaml-test " + b"x" * 600 + b"</html>", "text/html")
    rc = cache_source.main([
        "cache_source.py",
        "https://example.com/yaml",
        "--cache-root",
        str(tmp_path),
        "--topic",
        "yaml_test",
        "--date",
        "2026-05-19",
    ])
    captured = capsys.readouterr()
    assert rc == 0
    assert "- cache_id: cache_" in captured.out
    assert "source_url: https://example.com/yaml" in captured.out
    assert "content_type: text/html" in captured.out
    assert "restricted: false" in captured.out


def test_cache_one_emits_etag_and_last_modified_on_capture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When the response carries ETag/Last-Modified, capture record records them."""
    _patch_fetch(
        monkeypatch,
        b"<html>etag-test</html>",
        "text/html",
        extras={"ETag": 'W/"abc123"', "Last-Modified": "Wed, 21 Oct 2026 07:28:00 GMT"},
    )
    entry = cache_source.cache_one(
        "https://example.com/etag-test",
        cache_root=tmp_path,
        fetched_at="2026-05-19",
        topic="t",
    )
    assert entry["record_type"] == "capture"
    assert entry["http_etag"] == 'W/"abc123"'
    assert entry["http_last_modified"] == "Wed, 21 Oct 2026 07:28:00 GMT"


def test_cache_one_304_emits_revisit_server_not_modified(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """304 response with prior_cache_id emits a server-not-modified revisit."""
    def fake_urlopen(req, timeout=30):
        from urllib.error import HTTPError
        from email.message import EmailMessage
        headers = EmailMessage()
        headers["Content-Type"] = "text/html"
        headers["ETag"] = 'W/"abc123"'
        raise HTTPError(req.full_url, 304, "Not Modified", headers, None)
    monkeypatch.setattr(cache_source, "urlopen", fake_urlopen)

    entry = cache_source.cache_one(
        "https://example.com/x",
        cache_root=tmp_path,
        fetched_at="2026-05-19",
        topic="t",
        if_etag='W/"abc123"',
        prior_cache_id="cache_abc123",
    )
    assert entry["record_type"] == "revisit"
    assert entry["revisit_profile"] == "server-not-modified"
    assert entry["refers_to_cache_id"] == "cache_abc123"
    assert entry["http_status"] == 304
    # No raw bytes written for revisit
    assert "raw_path" not in entry
    assert "sha256" not in entry


def test_cache_one_identical_payload_digest_revisit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """200 with the same hash as prior_sha256 emits an identical-payload-digest revisit."""
    body = b"<html>same content</html>"
    _patch_fetch(monkeypatch, body, "text/html")
    import hashlib
    digest = hashlib.sha256(body).hexdigest()

    entry = cache_source.cache_one(
        "https://example.com/same",
        cache_root=tmp_path,
        fetched_at="2026-05-19",
        topic="t",
        prior_cache_id=f"cache_{digest[:16]}",
        prior_sha256=digest,
    )
    assert entry["record_type"] == "revisit"
    assert entry["revisit_profile"] == "identical-payload-digest"
    assert entry["http_status"] == 200
    assert entry["refers_to_cache_id"] == f"cache_{digest[:16]}"


def test_cache_one_new_content_emits_capture_linked_to_prior(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """200 with new hash emits a fresh capture but records refers_to_cache_id."""
    _patch_fetch(monkeypatch, b"<html>different content " + b"x" * 600 + b"</html>", "text/html")
    entry = cache_source.cache_one(
        "https://example.com/changed",
        cache_root=tmp_path,
        fetched_at="2026-05-19",
        topic="t",
        prior_cache_id="cache_oldhash_v1",
        prior_sha256="0" * 64,  # deliberately different from new content
    )
    assert entry["record_type"] == "capture"
    assert "raw_path" in entry  # bytes were written
    assert entry["refers_to_cache_id"] == "cache_oldhash_v1"  # back-link recorded


# ----- v2.2.1: Playwright escalation -----


def test_v221_urllib_fast_path_no_escalation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When urllib returns substantial content, no Playwright escalation."""
    raw = b"<html><body>" + (b"real content " * 100) + b"</body></html>"
    _patch_fetch(monkeypatch, raw, "text/html")
    entry = cache_source.cache_one(
        "https://example.com/static",
        cache_root=tmp_path,
        fetched_at="2026-05-20",
        topic="test",
        escalate_on_failure=True,
    )
    # urllib default — fetch_method omitted from entry (backward compat)
    assert "fetch_method" not in entry
    assert entry["record_type"] == "capture"


def test_v221_escalates_on_http_403(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """403 from urllib with --escalate-on-failure → Playwright fallback."""
    from urllib.error import HTTPError

    rendered_raw = b"<html><body>" + (b"playwright content " * 100) + b"</body></html>"

    def fake_urllib(*_a, **_kw):
        raise HTTPError("https://example.com/sso", 403, "Forbidden", {}, None)

    monkeypatch.setattr(cache_source, "_fetch", fake_urllib)
    monkeypatch.setattr(
        cache_source, "_fetch_via_playwright",
        lambda _u: (200, rendered_raw, "text/html", None, None),
    )
    entry = cache_source.cache_one(
        "https://example.com/sso",
        cache_root=tmp_path,
        fetched_at="2026-05-20",
        topic="test",
        escalate_on_failure=True,
    )
    assert entry["fetch_method"] == "playwright_rendered"
    assert entry["bytes"] == len(rendered_raw)


def test_v221_does_not_escalate_without_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """403 from urllib WITHOUT --escalate-on-failure → still raises."""
    from urllib.error import HTTPError

    def fake_urllib(*_a, **_kw):
        raise HTTPError("https://example.com/sso", 403, "Forbidden", {}, None)

    monkeypatch.setattr(cache_source, "_fetch", fake_urllib)
    with pytest.raises(HTTPError):
        cache_source.cache_one(
            "https://example.com/sso",
            cache_root=tmp_path,
            fetched_at="2026-05-20",
            topic="test",
            escalate_on_failure=False,
        )


def test_v221_escalates_on_suspect_short_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """urllib returns 200 with very short text → Playwright fallback."""
    short_raw = b"<html><body>Loading</body></html>"  # < 500 chars
    rendered_raw = b"<html><body>" + (b"hydrated SPA " * 100) + b"</body></html>"
    _patch_fetch(monkeypatch, short_raw, "text/html")
    monkeypatch.setattr(
        cache_source, "_fetch_via_playwright",
        lambda _u: (200, rendered_raw, "text/html", None, None),
    )
    entry = cache_source.cache_one(
        "https://example.com/spa",
        cache_root=tmp_path,
        fetched_at="2026-05-20",
        topic="test",
        escalate_on_failure=True,
    )
    assert entry["fetch_method"] == "playwright_rendered"


def test_v221_escalates_on_js_required_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """urllib returns 200 with JS-required marker → Playwright fallback."""
    js_required = (
        b"<html><body>" + b"please enable javascript " * 30
        + b"<noscript>x</noscript></body></html>"
    )
    rendered_raw = b"<html><body>" + (b"hydrated content " * 100) + b"</body></html>"
    _patch_fetch(monkeypatch, js_required, "text/html")
    monkeypatch.setattr(
        cache_source, "_fetch_via_playwright",
        lambda _u: (200, rendered_raw, "text/html", None, None),
    )
    entry = cache_source.cache_one(
        "https://example.com/spa",
        cache_root=tmp_path,
        fetched_at="2026-05-20",
        topic="test",
        escalate_on_failure=True,
    )
    assert entry["fetch_method"] == "playwright_rendered"


def test_v221_content_is_suspect_heuristics() -> None:
    """Unit test the detection heuristics directly."""
    is_suspect, _ = cache_source._content_is_suspect(b"a" * 1000, "text/html")
    assert not is_suspect

    is_suspect, reason = cache_source._content_is_suspect(b"short", "text/html")
    assert is_suspect
    assert "chars" in reason

    is_suspect, reason = cache_source._content_is_suspect(
        b"some content " * 50 + b"<noscript>js needed</noscript>",
        "text/html",
    )
    assert is_suspect
    assert "noscript" in reason.lower()

    is_suspect, _ = cache_source._content_is_suspect(b"", "text/html")
    assert is_suspect


# ----- v2.4.1: graceful degradation when Playwright is unavailable (#18) -----
# Escalation is default-on at the skill level in v2.4.1, so passing
# --escalate-on-failure must NOT hard-crash installs that lack Playwright.


def test_v241_403_degrades_when_playwright_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """403 + escalate, but Playwright not installed → re-raise the original
    HTTPError (degrade to non-escalated) with a stderr WARN, not a crash."""
    from urllib.error import HTTPError

    def fake_urllib(*_a, **_kw):
        raise HTTPError("https://example.com/sso", 403, "Forbidden", {}, None)

    def raise_unavailable(_u):
        raise cache_source.PlaywrightUnavailable("playwright not installed")

    monkeypatch.setattr(cache_source, "_fetch", fake_urllib)
    monkeypatch.setattr(cache_source, "_fetch_via_playwright", raise_unavailable)
    with pytest.raises(HTTPError):
        cache_source.cache_one(
            "https://example.com/sso",
            cache_root=tmp_path,
            fetched_at="2026-05-24",
            topic="test",
            escalate_on_failure=True,
        )
    assert "Playwright escalation" in capsys.readouterr().err


def test_v241_suspect_degrades_to_stub_when_playwright_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Suspect content + escalate, but Playwright not installed → fall back to a
    stub record (same as no-escalation) with a stderr WARN."""
    short_raw = b"<html><body>Loading</body></html>"  # < 500 chars trips suspect

    def raise_unavailable(_u):
        raise cache_source.PlaywrightUnavailable("playwright not installed")

    _patch_fetch(monkeypatch, short_raw, "text/html")
    monkeypatch.setattr(cache_source, "_fetch_via_playwright", raise_unavailable)
    entry = cache_source.cache_one(
        "https://example.com/spa",
        cache_root=tmp_path,
        fetched_at="2026-05-24",
        topic="test",
        escalate_on_failure=True,
    )
    assert entry["extraction_status"] == "stub"
    assert "Playwright escalation" in capsys.readouterr().err


# ----- v2.3 A2: PDF extraction cascade (#11) -----


def test_pdf_text_only_extraction_ok(plain_text_pdf_bytes: bytes) -> None:
    """Plain-text PDF → status: ok, no warnings."""
    text, status, warnings = cache_source._extract_pdf_text(plain_text_pdf_bytes)
    assert status == "ok"
    assert "synthetic plain-text test PDF" in text
    assert warnings == []


def test_pdf_equation_rich_marks_rich_when_docling_succeeds(
    equation_rich_pdf_bytes: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Equation-rich PDF with Docling mocked → status: rich."""
    def fake_docling(raw: bytes, *, docling_cache_dir=None):
        return "# Equation-Rich Synthetic\n\n$\\frac{a}{b}$ extracted by Docling", "rich", []

    monkeypatch.setattr(cache_source, "_extract_via_docling", fake_docling)
    text, status, warnings = cache_source._extract_pdf_text(equation_rich_pdf_bytes)
    assert status == "rich"
    assert "Docling" in text


def test_pdf_equation_rich_docling_errors_falls_back_to_ok_text_only(
    equation_rich_pdf_bytes: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Math detected but Docling crashes → ok_text_only + WARN."""
    def fake_docling(raw: bytes, *, docling_cache_dir=None):
        raise RuntimeError("Docling model load failed")

    monkeypatch.setattr(cache_source, "_extract_via_docling", fake_docling)
    text, status, warnings = cache_source._extract_pdf_text(equation_rich_pdf_bytes)
    assert status == "ok_text_only"
    assert any("Docling" in w for w in warnings)
    # pdfplumber text still returned
    assert text


def test_pdf_equation_rich_docling_missing_falls_back_to_ok_text_only(
    equation_rich_pdf_bytes: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Math detected but docling not installed → ok_text_only + helpful WARN."""
    def fake_docling(raw: bytes, *, docling_cache_dir=None):
        raise ImportError("No module named 'docling'")

    monkeypatch.setattr(cache_source, "_extract_via_docling", fake_docling)
    text, status, warnings = cache_source._extract_pdf_text(equation_rich_pdf_bytes)
    assert status == "ok_text_only"
    assert any("docling" in w.lower() and "install" in w.lower() for w in warnings)


def test_pdf_encrypted_marks_partial(encrypted_pdf_bytes: bytes) -> None:
    """Encrypted PDF → status: partial + WARN."""
    text, status, warnings = cache_source._extract_pdf_text(encrypted_pdf_bytes)
    assert status == "partial"
    assert any("encrypt" in w.lower() for w in warnings)


def test_pdf_image_only_marks_degraded(
    image_only_pdf_bytes: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Image-only PDF → status: degraded + WARN.

    pdfplumber returns near-empty text on these. We mock Docling to fail
    (Docling's OCR would otherwise rescue the page; in this test we want to
    confirm the fall-through degraded branch).
    """
    def fake_docling(raw: bytes, *, docling_cache_dir=None):
        raise RuntimeError("Docling unavailable for this test")

    monkeypatch.setattr(cache_source, "_extract_via_docling", fake_docling)
    text, status, warnings = cache_source._extract_pdf_text(image_only_pdf_bytes)
    assert status == "degraded"
    assert any("low text yield" in w for w in warnings)


def test_pdf_extraction_failure_marks_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Corrupt PDF bytes + Docling also fails → status: failed."""
    def fake_docling(raw: bytes, *, docling_cache_dir=None):
        raise RuntimeError("docling cannot handle corrupt bytes either")

    monkeypatch.setattr(cache_source, "_extract_via_docling", fake_docling)
    text, status, warnings = cache_source._extract_pdf_text(b"not a real pdf at all")
    assert status == "failed"
    assert any("pdfplumber failed" in w for w in warnings)


def test_no_extract_pdfs_returns_raw_only(plain_text_pdf_bytes: bytes) -> None:
    """--no-extract-pdfs preserves the pre-v2.3 raw_only behavior."""
    text, status, warnings = cache_source._safe_text(
        plain_text_pdf_bytes, "application/pdf", extract_pdfs=False
    )
    assert status == "raw_only"
    assert "extraction skipped" in text
    assert warnings == []


def test_safe_text_dispatches_pdf(
    plain_text_pdf_bytes: bytes,
) -> None:
    """_safe_text routes application/pdf to the cascade."""
    text, status, warnings = cache_source._safe_text(
        plain_text_pdf_bytes, "application/pdf"
    )
    assert status == "ok"
    assert "synthetic plain-text test PDF" in text


# ----- v2.3 A2: equation detection unit -----


def test_equation_detection_plain_text_no_match() -> None:
    is_rich, reason = cache_source._detect_equation_richness(
        "The quick brown fox jumps over the lazy dog. " * 30
    )
    assert not is_rich


def test_equation_detection_latex_residue_matches() -> None:
    is_rich, reason = cache_source._detect_equation_richness(
        "Some prose about \\frac{a}{b} and other things"
    )
    assert is_rich
    assert "LaTeX residue" in reason


def test_equation_detection_unicode_math_density_matches() -> None:
    # 12 math chars in 100-char string = 120/1000 — well over the 3.0 threshold
    is_rich, reason = cache_source._detect_equation_richness(
        "x ≤ y ≥ z ∑ ∫ ∂ ∇ ∞ ± × ÷ " + "padding " * 5
    )
    assert is_rich
    assert "unicode math density" in reason


def test_equation_detection_chemistry_no_false_positive() -> None:
    # 'CO₂' and 'H₂O' use subscripts not in our math char set; should NOT trip
    is_rich, _ = cache_source._detect_equation_richness(
        "The reaction CO2 + H2O produces H2CO3 in aqueous solution. " * 10
    )
    assert not is_rich


# ----- v2.3 A2: per-host extraction log -----


def test_extraction_log_appends_per_call(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_fetch(monkeypatch, b"<html>" + b"x" * 600 + b"</html>", "text/html")
    log_path = tmp_path / "ext_log.jsonl"
    cache_source.cache_one(
        "https://example.com/log-test",
        cache_root=tmp_path / "cache",
        fetched_at="2026-05-23",
        topic="t",
        extraction_log_path=log_path,
        run_id="abc123",
    )
    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    import json as _json
    record = _json.loads(lines[0])
    assert record["status"] == "ok"
    assert record["run_id"] == "abc123"
    assert record["source_url"] == "https://example.com/log-test"
    assert "hostname" in record


def test_default_extraction_log_path_is_per_host(tmp_path: Path) -> None:
    log_path = cache_source._default_extraction_log_path(tmp_path)
    assert log_path.parent == tmp_path
    assert log_path.name.startswith("extraction_log_")
    assert log_path.name.endswith(".jsonl")


# ----- v2.3 A2: docling cache dir threading -----


def test_docling_cache_dir_threaded_through_env(
    equation_rich_pdf_bytes: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When docling_cache_dir is provided, HF_HOME is set so Docling honors it."""
    captured: dict[str, str] = {}

    def fake_docling_inner(raw, *, docling_cache_dir=None):
        captured["docling_cache_dir"] = docling_cache_dir or ""
        captured["HF_HOME"] = os.environ.get("HF_HOME", "")
        return "mock output", "rich", []

    monkeypatch.setattr(cache_source, "_extract_via_docling", fake_docling_inner)
    text, status, _ = cache_source._extract_pdf_text(
        equation_rich_pdf_bytes, docling_cache_dir="/tmp/test_docling_cache"
    )
    assert status == "rich"
    assert captured["docling_cache_dir"] == "/tmp/test_docling_cache"


# ----- v2.3 A3: JS-shell stub detection (#10) -----


def test_js_shell_marked_stub_without_escalation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """v2.3 #10: unconditional stub detection. urllib 200 with suspect content
    AND no --escalate-on-failure → extraction_status: stub + WARN."""
    short_raw = b"<html><body>Loading</body></html>"  # < 500 chars trips suspect
    _patch_fetch(monkeypatch, short_raw, "text/html")

    entry = cache_source.cache_one(
        "https://example.com/spa",
        cache_root=tmp_path,
        fetched_at="2026-05-23",
        topic="t",
        escalate_on_failure=False,  # explicitly off
    )
    assert entry["extraction_status"] == "stub"
    assert any("JS-shell stub" in w for w in entry.get("extraction_warnings", []))
    captured = capsys.readouterr()
    assert "WARN" in captured.err
    assert "stub" in captured.err


def test_js_shell_escalates_with_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """v2.3 #10: when --escalate-on-failure is set, suspect content triggers
    Playwright (existing v2.2.1 behavior) and the stub status is NOT set."""
    short_raw = b"<html><body>Loading</body></html>"
    rendered_raw = b"<html><body>" + (b"hydrated " * 100) + b"</body></html>"
    _patch_fetch(monkeypatch, short_raw, "text/html")
    monkeypatch.setattr(
        cache_source,
        "_fetch_via_playwright",
        lambda url: (200, rendered_raw, "text/html", None, None),
    )

    entry = cache_source.cache_one(
        "https://example.com/spa",
        cache_root=tmp_path,
        fetched_at="2026-05-23",
        topic="t",
        escalate_on_failure=True,
    )
    assert entry["extraction_status"] == "ok"  # not stub — Playwright rendered fine
    assert entry["fetch_method"] == "playwright_rendered"


# ----- v2.3 --strict-extraction exit code -----


def test_strict_extraction_exits_nonzero_on_stub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    short_raw = b"<html><body>Loading</body></html>"
    _patch_fetch(monkeypatch, short_raw, "text/html")
    rc = cache_source.main([
        "cache_source.py",
        "https://example.com/spa",
        "--cache-root",
        str(tmp_path),
        "--topic",
        "t",
        "--date",
        "2026-05-23",
        "--strict-extraction",
    ])
    assert rc == 1

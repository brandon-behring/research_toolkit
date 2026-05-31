"""Tests for cache_source v2.6 source provenance.

Covers best-effort ``published_online`` capture (arXiv API / Crossref / HTML
meta) and the arXiv abs-page stub fallback. All network primitives are replaced
with hand-rolled fakes via ``monkeypatch.setattr`` (no real I/O, no
``unittest.mock``). The fake ``_fetch`` accepts every call shape the module
uses: ``_fetch(url, if_etag=..., if_last_modified=...)`` (main fetch),
``_fetch(abs_url)`` (abs fallback), and ``_fetch(api, timeout=...)`` (date
lookups).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import cache_source  # type: ignore[import-not-found]


# ---------- Canned upstream payloads ----------

ARXIV_API_XML = (
    "<?xml version='1.0' encoding='UTF-8'?>"
    "<feed xmlns='http://www.w3.org/2005/Atom'>"
    "<entry>"
    "<id>http://arxiv.org/abs/1506.00356v2</id>"
    "<published>2019-08-08T17:08:30Z</published>"
    "<updated>2019-08-09T10:00:00Z</updated>"
    "<title>A Fake Paper</title>"
    "</entry></feed>"
).encode("utf-8")


def _crossref_json(date_parts: list[list[int]]) -> bytes:
    return json.dumps(
        {"message": {"issued": {"date-parts": date_parts}}}
    ).encode("utf-8")


# Bodies padded well past SUSPECT_TEXT_MIN_CHARS (500) so they read as genuine.
def _real_html(body_seed: str, *, head: str = "") -> bytes:
    body = (body_seed + " ") * 60
    return (
        f"<html><head><title>T</title>{head}</head><body>{body}</body></html>"
    ).encode("utf-8")


ARXIV_ABS_HTML = _real_html("Real abstract content with several meaningful words")
STUB_HTML = (
    "<html><head><title>loading</title></head>"
    "<body>You need to enable JavaScript is required to run this app.</body></html>"
).encode("utf-8")
META_HTML = _real_html(
    "A genuine blog body with plenty of words",
    head='<meta property="article:published_time" content="2021-03-14T09:00:00Z">',
)
META_CITATION_HTML = _real_html(
    "Citation-style article body text repeated here",
    head='<meta name="citation_publication_date" content="2018/11/02">',
)


# ---------- Fake fetch primitive ----------

class _FakeFetcher:
    """Returns canned (status, body, ctype, etag, last) keyed by URL substring.

    Records every requested URL in ``self.calls``. Accepts all call shapes the
    module uses (keyword conditional headers, positional abs-fallback, timeout).
    """

    def __init__(self, responses: dict[str, tuple[int, bytes, str]]):
        self.responses = responses
        self.calls: list[str] = []

    def __call__(self, url, *, if_etag=None, if_last_modified=None, timeout=None):
        self.calls.append(url)
        for needle, (status, body, ctype) in self.responses.items():
            if needle in url:
                return status, body, ctype, None, "Wed, 01 Jan 2025 00:00:00 GMT"
        raise OSError(f"no canned response for {url}")


# ---------- Fake urllib boundary (exercises the REAL _fetch) ----------

class _FakeHeaders:
    """Stand-in for ``http.client.HTTPMessage`` used by ``_fetch``."""

    def __init__(self, content_type: str):
        self._content_type = content_type

    def get_content_type(self):
        return self._content_type

    def get(self, key, default=None):
        return default  # no ETag / Last-Modified in these canned responses


class _FakeResponse:
    """Context-manager response with the surface ``_fetch`` reads."""

    def __init__(self, status: int, body: bytes, content_type: str):
        self.status = status
        self._body = body
        self.headers = _FakeHeaders(content_type)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._body


class _FakeUrlopen:
    """Replacement for ``cache_source.urlopen`` — does NOT inject ``_fetch``.

    Lets a test drive the genuine production path (``fetch=None``) so the
    ``_fetch(api, timeout=...)`` call shape is exercised end-to-end. Keyed by
    URL substring; records every (url, timeout) pair seen. The real ``_fetch``
    passes a ``Request`` object, so the URL is read off ``.full_url``.
    """

    def __init__(self, responses: dict[str, tuple[int, bytes, str]]):
        self.responses = responses
        self.calls: list[tuple[str, int | None]] = []

    def __call__(self, req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        self.calls.append((url, timeout))
        for needle, (status, body, ctype) in self.responses.items():
            if needle in url:
                return _FakeResponse(status, body, ctype)
        raise OSError(f"no canned response for {url}")


# ---------- arXiv publication-date lookup ----------

def test_arxiv_published_date_extracts_date_part():
    fetcher = _FakeFetcher({"export.arxiv.org": (200, ARXIV_API_XML, "text/xml")})
    assert cache_source._arxiv_published_date("1506.00356", fetch=fetcher) == "2019-08-08"
    assert any("id_list=1506.00356" in c for c in fetcher.calls)


def test_arxiv_published_date_swallows_fetch_error():
    def _boom(url, *, timeout=None):
        raise OSError("simulated network down")

    assert cache_source._arxiv_published_date("1506.00356", fetch=_boom) is None


def test_arxiv_published_date_returns_none_on_non_200():
    fetcher = _FakeFetcher({"export.arxiv.org": (503, b"", "text/xml")})
    assert cache_source._arxiv_published_date("1506.00356", fetch=fetcher) is None


# ---------- Crossref publication-date lookup ----------

def test_crossref_published_date_full_date():
    fetcher = _FakeFetcher(
        {"api.crossref.org": (200, _crossref_json([[2020, 6, 15]]), "application/json")}
    )
    assert cache_source._crossref_published_date("10.1/x", fetch=fetcher) == "2020-06-15"


def test_crossref_published_date_year_only_omitted():
    fetcher = _FakeFetcher(
        {"api.crossref.org": (200, _crossref_json([[2020]]), "application/json")}
    )
    assert cache_source._crossref_published_date("10.1/x", fetch=fetcher) is None


def test_crossref_published_date_year_month_omitted():
    fetcher = _FakeFetcher(
        {"api.crossref.org": (200, _crossref_json([[2020, 6]]), "application/json")}
    )
    assert cache_source._crossref_published_date("10.1/x", fetch=fetcher) is None


def test_crossref_published_date_swallows_error():
    def _boom(url, *, timeout=None):
        raise ValueError("bad json upstream")

    assert cache_source._crossref_published_date("10.1/x", fetch=_boom) is None


# ---------- HTML meta publication-date parsing ----------

def test_meta_published_date_parses_article_published_time():
    assert cache_source._meta_published_date(META_HTML.decode("utf-8")) == "2021-03-14"


def test_meta_published_date_parses_citation_publication_date_slashes():
    assert (
        cache_source._meta_published_date(META_CITATION_HTML.decode("utf-8"))
        == "2018-11-02"
    )


def test_meta_published_date_returns_none_without_meta():
    assert cache_source._meta_published_date("<html><body>no dates</body></html>") is None


def test_iso_date_or_none_rejects_partial_and_invalid():
    assert cache_source._iso_date_or_none("2020") is None
    assert cache_source._iso_date_or_none("2020-06") is None
    assert cache_source._iso_date_or_none("2020-13-40") is None
    assert cache_source._iso_date_or_none(None) is None
    assert cache_source._iso_date_or_none("2020-06-15T10:00:00Z") == "2020-06-15"


def test_arxiv_id_from_url_strips_version():
    assert cache_source._arxiv_id_from_url("https://arxiv.org/pdf/1506.00356v2") == "1506.00356"
    assert cache_source._arxiv_id_from_url("https://arxiv.org/abs/1506.00356") == "1506.00356"
    assert cache_source._arxiv_id_from_url("https://example.com/page") is None


# ---------- cache_one integration: published_online ----------

def _read_meta(tmp_path, entry):
    return json.loads(
        (tmp_path / "metadata" / "sha256" / f"{entry['sha256']}.json").read_text()
    )


def test_cache_one_writes_published_online_for_arxiv(tmp_path, monkeypatch):
    fetcher = _FakeFetcher(
        {
            "arxiv.org/abs/1506.00356": (200, ARXIV_ABS_HTML, "text/html"),
            "export.arxiv.org": (200, ARXIV_API_XML, "text/xml"),
        }
    )
    monkeypatch.setattr(cache_source, "_fetch", fetcher)
    entry = cache_source.cache_one(
        "https://arxiv.org/abs/1506.00356",
        cache_root=tmp_path,
        fetched_at="2026-01-01",
        topic="t",
    )
    assert entry["published_online"] == "2019-08-08"
    assert _read_meta(tmp_path, entry)["published_online"] == "2019-08-08"
    # No fallback needed (abs page fetched directly, not suspect).
    assert "escalation_reason" not in entry


def test_cache_one_writes_published_online_for_doi(tmp_path, monkeypatch):
    fetcher = _FakeFetcher(
        {
            "doi.org/10.1000/xyz": (200, _real_html("DOI landing body"), "text/html"),
            "api.crossref.org": (200, _crossref_json([[2022, 9, 1]]), "application/json"),
        }
    )
    monkeypatch.setattr(cache_source, "_fetch", fetcher)
    entry = cache_source.cache_one(
        "https://doi.org/10.1000/xyz",
        cache_root=tmp_path,
        fetched_at="2026-01-01",
        topic="t",
    )
    assert entry["published_online"] == "2022-09-01"


def test_cache_one_omits_published_online_for_doi_year_only(tmp_path, monkeypatch):
    fetcher = _FakeFetcher(
        {
            "doi.org/10.1000/xyz": (200, _real_html("DOI landing body"), "text/html"),
            "api.crossref.org": (200, _crossref_json([[2022]]), "application/json"),
        }
    )
    monkeypatch.setattr(cache_source, "_fetch", fetcher)
    entry = cache_source.cache_one(
        "https://doi.org/10.1000/xyz",
        cache_root=tmp_path,
        fetched_at="2026-01-01",
        topic="t",
    )
    assert "published_online" not in entry


def test_cache_one_writes_published_online_from_meta(tmp_path, monkeypatch):
    fetcher = _FakeFetcher({"example.com/post": (200, META_HTML, "text/html")})
    monkeypatch.setattr(cache_source, "_fetch", fetcher)
    entry = cache_source.cache_one(
        "https://example.com/post",
        cache_root=tmp_path,
        fetched_at="2026-01-01",
        topic="t",
    )
    assert entry["published_online"] == "2021-03-14"


# ---------- arXiv stub fallback (no --escalate-on-failure) ----------

def test_cache_one_falls_back_to_arxiv_abs_on_stub(tmp_path, monkeypatch):
    fetcher = _FakeFetcher(
        {
            "arxiv.org/pdf/1506.00356": (200, STUB_HTML, "text/html"),
            "arxiv.org/abs/1506.00356": (200, ARXIV_ABS_HTML, "text/html"),
            "export.arxiv.org": (200, ARXIV_API_XML, "text/xml"),
        }
    )
    monkeypatch.setattr(cache_source, "_fetch", fetcher)
    entry = cache_source.cache_one(
        "https://arxiv.org/pdf/1506.00356",
        cache_root=tmp_path,
        fetched_at="2026-01-01",
        topic="t",
    )
    # Fallback abs page was fetched.
    assert any("arxiv.org/abs/1506.00356" in c for c in fetcher.calls)
    assert entry["escalation_reason"] == cache_source.ARXIV_ABS_FALLBACK_REASON
    # Recorded content is the abs page, not the stub.
    assert entry["extraction_status"] == cache_source.EXTRACTION_STATUS_OK
    blob = (tmp_path / "blobs" / "sha256" / entry["sha256"]).read_bytes()
    assert b"Real abstract content" in blob
    assert b"enable JavaScript" not in blob
    # Date still captured from the API.
    assert entry["published_online"] == "2019-08-08"


def test_cache_one_keeps_stub_when_abs_also_stub(tmp_path, monkeypatch):
    fetcher = _FakeFetcher(
        {
            "arxiv.org/pdf/1506.00356": (200, STUB_HTML, "text/html"),
            "arxiv.org/abs/1506.00356": (200, STUB_HTML, "text/html"),
            "export.arxiv.org": (200, ARXIV_API_XML, "text/xml"),
        }
    )
    monkeypatch.setattr(cache_source, "_fetch", fetcher)
    entry = cache_source.cache_one(
        "https://arxiv.org/pdf/1506.00356",
        cache_root=tmp_path,
        fetched_at="2026-01-01",
        topic="t",
    )
    assert entry["extraction_status"] == cache_source.EXTRACTION_STATUS_STUB
    assert "escalation_reason" not in entry


# ---------- Regression guards ----------

def test_cache_one_plain_url_has_no_published_online_or_fallback(tmp_path, monkeypatch):
    fetcher = _FakeFetcher(
        {"example.org/docs": (200, _real_html("Plain docs body no dates"), "text/html")}
    )
    monkeypatch.setattr(cache_source, "_fetch", fetcher)
    entry = cache_source.cache_one(
        "https://example.org/docs",
        cache_root=tmp_path,
        fetched_at="2026-01-01",
        topic="t",
    )
    assert "published_online" not in entry
    assert "escalation_reason" not in entry
    assert "fetch_method" not in entry  # urllib default stays implicit
    # Exactly one fetch — no extra lookups for a plain, non-arXiv/non-DOI page.
    assert fetcher.calls == ["https://example.org/docs"]


def test_cache_one_succeeds_when_date_lookup_raises(tmp_path, monkeypatch):
    # arXiv content page fetches fine, but the API lookup raises -> still cached.
    def _fetch(url, *, if_etag=None, if_last_modified=None, timeout=None):
        if "export.arxiv.org" in url:
            raise OSError("simulated API outage")
        return 200, ARXIV_ABS_HTML, "text/html", None, None

    monkeypatch.setattr(cache_source, "_fetch", _fetch)
    entry = cache_source.cache_one(
        "https://arxiv.org/abs/1506.00356",
        cache_root=tmp_path,
        fetched_at="2026-01-01",
        topic="t",
    )
    assert "published_online" not in entry
    assert entry["record_type"] == "capture"
    assert (tmp_path / "metadata" / "sha256" / f"{entry['sha256']}.json").exists()


# ---------- DEFAULT-path date lookup (the REAL _fetch, no fetch= injection) ----------
#
# The injected-fetch tests above pass a fake that accepts ``timeout=``; they do
# NOT prove the production path (``fetch=None`` -> real ``_fetch``) works. These
# tests monkeypatch only the urllib boundary (``cache_source.urlopen``) so the
# genuine ``_fetch(api, timeout=PUBDATE_TIMEOUT)`` call shape is exercised. They
# would fail if ``_fetch`` lacked a ``timeout`` parameter (the regressed bug).

def test_arxiv_published_date_default_path_uses_real_fetch(monkeypatch):
    fake = _FakeUrlopen({"export.arxiv.org": (200, ARXIV_API_XML, "text/xml")})
    monkeypatch.setattr(cache_source, "urlopen", fake)
    # No fetch= argument -> exercises the real _fetch via the urlopen boundary.
    assert cache_source._arxiv_published_date("1506.00356") == "2019-08-08"
    assert any("id_list=1506.00356" in url for url, _ in fake.calls)
    # The shorter pubdate timeout actually reaches urlopen (proves _fetch
    # accepted and forwarded timeout= rather than raising TypeError).
    assert any(t == cache_source.PUBDATE_TIMEOUT for _, t in fake.calls)


def test_crossref_published_date_default_path_uses_real_fetch(monkeypatch):
    fake = _FakeUrlopen(
        {"api.crossref.org": (200, _crossref_json([[2020, 6, 15]]), "application/json")}
    )
    monkeypatch.setattr(cache_source, "urlopen", fake)
    assert cache_source._crossref_published_date("10.1/x") == "2020-06-15"
    assert any(t == cache_source.PUBDATE_TIMEOUT for _, t in fake.calls)


def test_published_online_for_default_path_resolves_arxiv_date(monkeypatch):
    # Whole resolver, default path: arXiv id -> real _fetch -> arXiv API -> date.
    fake = _FakeUrlopen({"export.arxiv.org": (200, ARXIV_API_XML, "text/xml")})
    monkeypatch.setattr(cache_source, "urlopen", fake)
    got = cache_source._published_online_for(
        "https://arxiv.org/abs/1506.00356", ARXIV_ABS_HTML, "text/html"
    )
    assert got == "2019-08-08"

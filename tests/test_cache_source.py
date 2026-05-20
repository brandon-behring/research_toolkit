"""Tests for scripts/cache_source.py — the strict-live v2 caching helper."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from urllib.error import URLError

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import cache_source  # noqa: E402


class _FakeResponse:
    def __init__(self, body: bytes, content_type: str) -> None:
        self._body = body
        self._content_type = content_type

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *_exc) -> None:
        return None

    def read(self) -> bytes:
        return self._body

    @property
    def headers(self) -> "_FakeResponse":  # quack: get_content_type lives on headers
        return self

    def get_content_type(self) -> str:
        return self._content_type


def _patch_fetch(monkeypatch: pytest.MonkeyPatch, body: bytes, content_type: str) -> None:
    def fake_urlopen(req, timeout=30):
        return _FakeResponse(body, content_type)
    monkeypatch.setattr(cache_source, "urlopen", fake_urlopen)


def test_sha256_helper_matches_hashlib() -> None:
    data = b"hello world"
    assert cache_source._sha256(data) == hashlib.sha256(data).hexdigest()


def test_safe_text_html_extracts_text() -> None:
    text, status = cache_source._safe_text(b"<html>hi</html>", "text/html")
    assert "<html>" in text
    assert status == "ok"


def test_safe_text_binary_falls_back_to_raw_only() -> None:
    text, status = cache_source._safe_text(b"\x00\x01\x02", "application/octet-stream")
    assert status == "raw_only"
    assert "raw binary cached" in text


def test_cache_one_writes_blob_text_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    body = b"<html><body>Test page for cache_source.</body></html>"
    _patch_fetch(monkeypatch, body, "text/html")

    entry = cache_source.cache_one(
        "https://example.com/test-page",
        cache_root=tmp_path,
        fetched_at="2026-05-19",
        topic="test_topic",
    )

    digest = hashlib.sha256(body).hexdigest()
    raw_path = Path(entry["raw_path"])
    text_path = Path(entry["text_path"])
    metadata_path = Path(entry["metadata_path"])

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
    _patch_fetch(monkeypatch, b"<html>yaml-test</html>", "text/html")
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

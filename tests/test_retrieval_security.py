"""Adversarial tests for the public, read-only retrieval boundary."""

from __future__ import annotations

from email.message import EmailMessage
from pathlib import Path
import socket
import sys
import time
from urllib.error import URLError
from urllib.request import Request

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from research_toolkit import retrieval_security as security  # noqa: E402
from scripts import cache_source  # noqa: E402


def _public_resolver(host, port, **_kwargs):
    return [
        (
            socket.AF_INET,
            socket.SOCK_STREAM,
            socket.IPPROTO_TCP,
            "",
            ("93.184.216.34", port),
        )
    ]


def _private_resolver(host, port, **_kwargs):
    return [
        (
            socket.AF_INET,
            socket.SOCK_STREAM,
            socket.IPPROTO_TCP,
            "",
            ("10.0.0.8", port),
        )
    ]


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/",
        "http://127.1/",
        "http://[::1]/",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.1/",
        "http://192.168.1.1/",
        "http://0.0.0.0/",
        "http://localhost/",
        "http://metadata.google.internal/",
        "file:///etc/passwd",
        "ftp://example.com/archive",
        "https://example.com:8443/private",
        "https://user:password@example.com/source",
        "https://example.com\\@127.0.0.1/",
    ],
)
def test_validate_public_url_rejects_unsafe_targets(url: str) -> None:
    with pytest.raises(security.RetrievalSecurityError):
        security.validate_public_url(url, resolver=_public_resolver)


def test_validate_public_url_accepts_public_dns() -> None:
    assert (
        security.validate_public_url(
            "https://example.com/source", resolver=_public_resolver
        )
        == "https://example.com/source"
    )


def test_validate_public_url_rejects_private_dns_answer() -> None:
    with pytest.raises(security.RetrievalSecurityError, match="non-public"):
        security.validate_public_url(
            "https://public-looking.example/source", resolver=_private_resolver
        )


def test_validate_public_url_rejects_mixed_dns_answer() -> None:
    def mixed(host, port, **_kwargs):
        return _public_resolver(host, port) + _private_resolver(host, port)

    with pytest.raises(security.RetrievalSecurityError, match="10.0.0.8"):
        security.validate_public_url("https://example.com/source", resolver=mixed)


def test_os_resolver_is_bounded_by_absolute_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate = security.threading.Event()

    def blocked_resolver(*_args, **_kwargs):
        gate.wait(1.0)
        return _public_resolver("example.com", 443)

    monkeypatch.setattr(security.socket, "getaddrinfo", blocked_resolver)
    with pytest.raises(TimeoutError, match="resolution deadline"):
        security.validate_public_url(
            "https://example.com/source",
            deadline=security.time.monotonic() + 0.01,
        )
    gate.set()


def test_redirect_handler_rejects_private_location_before_open() -> None:
    handler = security._ValidatingRedirectHandler(  # noqa: SLF001
        max_redirects=5,
        resolver=_public_resolver,
    )
    request = Request("https://example.com/start")
    with pytest.raises(security.RetrievalSecurityError):
        handler.redirect_request(
            request,
            None,
            302,
            "Found",
            {},
            "http://169.254.169.254/latest/meta-data/",
        )


def test_redirect_handler_enforces_hard_count() -> None:
    handler = security._ValidatingRedirectHandler(  # noqa: SLF001
        max_redirects=0,
        resolver=_public_resolver,
    )
    with pytest.raises(security.RetrievalSecurityError, match="redirect limit"):
        handler.redirect_request(
            Request("https://example.com/start"),
            None,
            302,
            "Found",
            {},
            "https://example.com/next",
        )


def test_redirect_handler_rejects_https_downgrade() -> None:
    handler = security._ValidatingRedirectHandler(  # noqa: SLF001
        max_redirects=5,
        resolver=_public_resolver,
    )
    with pytest.raises(security.RetrievalSecurityError, match="HTTPS-to-HTTP"):
        handler.redirect_request(
            Request("https://example.com/start"),
            None,
            302,
            "Found",
            {},
            "http://example.com/next",
        )


def test_redirect_handler_rejects_secret_query_before_following() -> None:
    handler = security._ValidatingRedirectHandler(  # noqa: SLF001
        max_redirects=5,
        resolver=_public_resolver,
    )
    with pytest.raises(security.RetrievalSecurityError, match="query-bearing"):
        handler.redirect_request(
            Request("https://example.com/start"),
            None,
            302,
            "Found",
            {},
            "https://example.org/final?token=reflected-secret",
        )


def test_secure_urlopen_enforces_header_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    release = security.threading.Event()

    class FakeResponse:
        def close(self) -> None:
            return None

    class SlowOpener:
        def open(self, *_args, **_kwargs):
            release.wait(1.0)
            return FakeResponse()

    monkeypatch.setattr(security, "build_opener", lambda *_args: SlowOpener())
    started = time.monotonic()
    try:
        with pytest.raises(TimeoutError, match="before headers"):
            security.secure_urlopen(
                "https://example.com/source",
                timeout=0.02,
                resolver=_public_resolver,
            )
        assert time.monotonic() - started < 0.25
    finally:
        release.set()


def test_secure_urlopen_aborts_tracked_socket_at_header_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    release = security.threading.Event()
    trackers = []
    fake_socket = None

    class FakeSocket:
        def __init__(self) -> None:
            self.shutdown_called = False
            self.close_called = False

        def shutdown(self, _how) -> None:
            self.shutdown_called = True

        def close(self) -> None:
            self.close_called = True

    class SlowOpener:
        def open(self, *_args, **_kwargs):
            nonlocal fake_socket
            fake_socket = FakeSocket()
            trackers[0](fake_socket)
            release.wait(1.0)
            raise OSError("cancelled")

    def handler(_resolver, _deadline, tracker):
        trackers.append(tracker)
        return object()

    monkeypatch.setattr(security, "_PinnedHTTPHandler", handler)
    monkeypatch.setattr(security, "_PinnedHTTPSHandler", handler)
    monkeypatch.setattr(security, "build_opener", lambda *_args: SlowOpener())
    try:
        with pytest.raises(TimeoutError, match="before headers"):
            security.secure_urlopen(
                "https://example.com/source",
                timeout=0.02,
                resolver=_public_resolver,
            )
        assert fake_socket is not None
        assert fake_socket.shutdown_called is True
        assert fake_socket.close_called is True
    finally:
        release.set()


def test_connection_uses_validated_ip_not_hostname(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connected: list[tuple[str, int]] = []

    class FakeSocket:
        def settimeout(self, _timeout):
            return None

        def bind(self, _source):
            return None

        def connect(self, address):
            connected.append(address)

        def close(self):
            return None

    monkeypatch.setattr(security.socket, "socket", lambda *_args: FakeSocket())
    sock = security._connect_public(  # noqa: SLF001
        "example.com",
        443,
        5.0,
        None,
        resolver=_public_resolver,
    )
    assert isinstance(sock, FakeSocket)
    assert connected == [("93.184.216.34", 443)]


def test_connection_reports_validated_socket_to_tracker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tracked = []

    class FakeSocket:
        def settimeout(self, _timeout):
            return None

        def connect(self, _address):
            return None

        def close(self):
            return None

    monkeypatch.setattr(security.socket, "socket", lambda *_args: FakeSocket())
    sock = security._connect_public(  # noqa: SLF001
        "example.com",
        443,
        5.0,
        None,
        resolver=_public_resolver,
        socket_tracker=tracked.append,
    )
    assert tracked == [sock]


def test_redact_url_removes_userinfo_fragment_and_all_query_values() -> None:
    raw = (
        "https://alice:password@example.com/path?api_key=supersecret&view=full"
        "#private-fragment"
    )
    safe = security.redact_url(raw)
    assert "alice" not in safe
    assert "password" not in safe
    assert "supersecret" not in safe
    assert "private-fragment" not in safe
    assert "api_key" not in safe
    assert "view" not in safe
    assert safe.endswith("?redacted=REDACTED")


@pytest.mark.parametrize(
    "key",
    ["apikey", "accessToken", "Policy", "Key-Pair-Id", "ticket", "format"],
)
def test_redact_url_never_persists_query_values(key: str) -> None:
    safe = security.redact_url(f"https://example.com/source?{key}=top-secret")
    assert "top-secret" not in safe
    assert "REDACTED" in safe


@pytest.mark.parametrize(
    "url",
    [
        "https://user:pass@example.com/source",
        "https://example.com/source?apikey=raw-secret",
        "https://example.com/source#private",
    ],
)
def test_validate_record_url_rejects_unsanitized_urls(url: str) -> None:
    with pytest.raises(security.RetrievalSecurityError):
        security.validate_record_url(url)


def test_validate_record_url_accepts_redacted_query_values() -> None:
    assert security.validate_record_url(
        "https://example.com/source?redacted=REDACTED"
    )


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/source?apikey=REDACTED",
        "https://example.com/source?TOP-SECRET=REDACTED",
        "https://example.com/source?redacted=REDACTED&token=REDACTED",
        "https://example.com/source?%72edacted=REDACTED",
    ],
)
def test_validate_record_url_accepts_only_the_fixed_redaction_query(url: str) -> None:
    with pytest.raises(security.RetrievalSecurityError, match="exactly"):
        security.validate_record_url(url)


def test_validate_record_url_allows_only_known_public_identifier_queries() -> None:
    youtube = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    with pytest.raises(security.RetrievalSecurityError):
        security.validate_record_url(youtube)
    assert security.validate_record_url(youtube, allow_public_query=True) == youtube
    with pytest.raises(security.RetrievalSecurityError):
        security.validate_record_url(
            "https://www.youtube.com/watch?v=public&token=secret",
            allow_public_query=True,
        )


def test_validate_public_url_rejects_signed_query_before_dns() -> None:
    called = False

    def resolver(*_args, **_kwargs):
        nonlocal called
        called = True
        return _public_resolver("example.com", 443)

    with pytest.raises(security.RetrievalSecurityError, match="query-bearing"):
        security.validate_public_url(
            "https://example.com/source?token=top-secret", resolver=resolver
        )
    assert called is False


def test_validate_public_url_accepts_allowlisted_public_identifier_query() -> None:
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert security.validate_public_url(url, resolver=_public_resolver) == url


def test_validate_record_url_allows_only_namespaced_legacy_urns() -> None:
    placeholder = "urn:legacy-source:src_missing"
    with pytest.raises(security.RetrievalSecurityError):
        security.validate_record_url(placeholder)
    assert (
        security.validate_record_url(placeholder, allow_legacy_urn=True)
        == placeholder
    )


@pytest.mark.parametrize(
    "field",
    [
        "source_uri_sha256",
        "request_fingerprint",
        "url_checksum",
        "url_md5",
        "requestedURLHash",
        "href_sha256",
        "canonicalLinkDigest",
        "source-link-checksum",
        "endpoint_hash",
        "locatorFingerprint",
    ],
)
def test_durable_value_errors_rejects_url_fingerprint_aliases(field: str) -> None:
    errors = security.durable_value_errors({field: "0" * 64}, "record")
    assert any("offline guessing oracles" in error for error in errors), errors


@pytest.mark.parametrize("field", ["content_sha256", "sha256"])
def test_durable_value_errors_allows_non_locator_content_hashes(field: str) -> None:
    assert security.durable_value_errors({field: "0" * 64}, "record") == []


def test_durable_value_errors_scans_mapping_keys_without_echoing_secret() -> None:
    secret = "TOP-SECRET-MAPPING-KEY"
    errors = security.durable_value_errors(
        {f"https://example.com/private?token={secret}": "value"},
        "record",
    )
    assert any("mapping_key[0].embedded_url" in error for error in errors), errors
    assert all(secret not in error for error in errors)


def test_durable_value_errors_scans_embedded_urls_in_free_text() -> None:
    errors = security.durable_value_errors(
        {
            "excerpt": "See https://example.com/source?token=TOP-SECRET.",
            "query": "Public id https://www.youtube.com/watch?v=public-id",
        },
        "record",
    )
    assert len(errors) == 1
    assert "record.excerpt.embedded_url" in errors[0]
    assert "TOP-SECRET" not in errors[0]


class _Headers(EmailMessage):
    def __init__(self, content_length: int | None = None) -> None:
        super().__init__()
        self["Content-Type"] = "text/plain"
        if content_length is not None:
            self["Content-Length"] = str(content_length)


class _Response:
    def __init__(self, body: bytes, *, declared: int | None = None) -> None:
        self.body = body
        self.offset = 0
        self.status = 200
        self.headers = _Headers(declared)

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            size = len(self.body) - self.offset
        chunk = self.body[self.offset : self.offset + size]
        self.offset += len(chunk)
        return chunk

    def getcode(self) -> int:
        return self.status


def test_read_response_limited_rejects_declared_oversize() -> None:
    with pytest.raises(security.ResponseTooLargeError, match="declared"):
        security.read_response_limited(_Response(b"small", declared=100), max_bytes=10)


def test_read_response_limited_rejects_streamed_oversize() -> None:
    response = _Response(b"01234567890")
    aborted = []
    response._research_toolkit_abort = lambda: aborted.append(True)
    with pytest.raises(security.ResponseTooLargeError, match="exceeds"):
        security.read_response_limited(response, max_bytes=10)
    assert aborted == [True]


def test_read_response_limited_rejects_compressed_content() -> None:
    response = _Response(b"compressed")
    response.headers["Content-Encoding"] = "gzip"
    with pytest.raises(security.RetrievalSecurityError, match="encoded"):
        security.read_response_limited(response)


def test_read_response_limited_enforces_absolute_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(security.time, "monotonic", lambda: 11.0)
    with pytest.raises(TimeoutError, match="deadline"):
        security.read_response_limited(_Response(b"body"), deadline=10.0)


def test_read_response_limited_rejects_a_read_that_finishes_after_deadline() -> None:
    class SlowResponse(_Response):
        def read(self, size: int = -1) -> bytes:
            time.sleep(0.03)
            return b""

    with pytest.raises(TimeoutError, match="deadline"):
        security.read_response_limited(
            SlowResponse(b""), deadline=time.monotonic() + 0.01
        )


def test_cross_origin_redirect_strips_origin_specific_headers() -> None:
    handler = security._ValidatingRedirectHandler(  # noqa: SLF001
        max_redirects=5, resolver=_public_resolver
    )
    request = Request(
        "https://example.com/start",
        headers={
            "Authorization": "Bearer secret",
            "Cookie": "session=secret",
            "If-None-Match": "private-etag",
            "User-Agent": "research-test",
            "Accept-Encoding": "identity",
        },
    )
    redirected = handler.redirect_request(
        request, None, 302, "Found", {}, "https://example.org/final"
    )
    assert redirected is not None
    redirected_headers = {
        key.lower(): value for key, value in redirected.header_items()
    }
    assert "authorization" not in redirected_headers
    assert "cookie" not in redirected_headers
    assert "if-none-match" not in redirected_headers
    assert redirected_headers["user-agent"] == "research-test"
    assert redirected_headers["accept-encoding"] == "identity"


def test_cache_fetch_applies_response_ceiling(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        cache_source,
        "urlopen",
        lambda _request, timeout=30: _Response(b"01234567890"),
    )
    with pytest.raises(security.ResponseTooLargeError):
        cache_source._fetch("https://example.com/source", max_bytes=10)


def test_cache_fetch_requests_identity_encoding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, str | None] = {}

    def fake_urlopen(request, timeout=30):
        captured["encoding"] = dict(request.header_items()).get("Accept-encoding")
        return _Response(b"body")

    monkeypatch.setattr(cache_source, "urlopen", fake_urlopen)
    cache_source._fetch("https://example.com/source")
    assert captured["encoding"] == "identity"


def test_cache_defaults_rights_to_unknown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = b"<html>" + b"source text " * 100 + b"</html>"
    monkeypatch.setattr(
        cache_source,
        "_fetch",
        lambda *_args, **_kwargs: (200, body, "text/html", None, None),
    )
    entry = cache_source.cache_one(
        "https://example.com/source",
        cache_root=tmp_path,
        fetched_at="2026-07-14",
        topic="security",
    )
    assert entry["rights_status"] == "unknown"
    assert entry["visibility"] == "public"
    assert entry["restricted"] is True


def test_cache_records_rights_visibility_and_license_independently(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = b"<html>" + b"restricted source text " * 100 + b"</html>"
    monkeypatch.setattr(
        cache_source,
        "_fetch",
        lambda *_args, **_kwargs: (200, body, "text/html", None, None),
    )
    entry = cache_source.cache_one(
        "https://example.com/source",
        cache_root=tmp_path,
        fetched_at="2026-07-14",
        topic="security",
        rights_status="private_use",
        visibility="authenticated",
        license_value="custom terms; local research only",
    )
    assert entry["rights_status"] == "private_use"
    assert entry["visibility"] == "authenticated"
    assert entry["license"] == "custom terms; local research only"
    assert entry["restricted"] is True


def test_cache_fails_before_write_when_private_modes_cannot_be_enforced(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = b"<html>" + b"source text " * 100 + b"</html>"
    monkeypatch.setattr(
        cache_source,
        "_fetch",
        lambda *_args, **_kwargs: (200, body, "text/html", None, None),
    )

    def denied(*_args, **_kwargs):
        raise PermissionError("mode change denied")

    monkeypatch.setattr(cache_source.os, "chmod", denied)
    with pytest.raises(PermissionError, match="mode change denied"):
        cache_source.cache_one(
            "https://example.com/source",
            cache_root=tmp_path,
            fetched_at="2026-07-14",
            topic="security",
        )
    assert not list(tmp_path.rglob("blobs"))


def test_cache_rejects_query_secret_before_fetch_or_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = b"<html>" + b"source text " * 100 + b"</html>"
    called = False

    def unexpected(*_args, **_kwargs):
        nonlocal called
        called = True
        return (200, body, "text/html", None, None)

    monkeypatch.setattr(
        cache_source,
        "_fetch",
        unexpected,
    )
    with pytest.raises(security.RetrievalSecurityError, match="query-bearing"):
        cache_source.cache_one(
            "https://example.com/source?token=top-secret&format=html",
            cache_root=tmp_path,
            fetched_at="2026-07-14",
            topic="security",
        )
    assert called is False
    assert not list(tmp_path.rglob("*"))


def test_cache_records_sanitized_redirect_final_url(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    body = b"<html>" + b"source text " * 100 + b"</html>"
    monkeypatch.setattr(
        cache_source,
        "_fetch",
        lambda *_args, **_kwargs: (
            200,
            body,
            "text/html",
            None,
            None,
            "https://www.youtube.com/watch?v=second-public-id",
        ),
    )
    entry = cache_source.cache_one(
        "https://www.youtube.com/watch?v=first-public-id",
        cache_root=tmp_path,
        fetched_at="2026-07-14",
        topic="security",
    )
    assert entry["source_url"].endswith("v=first-public-id")
    assert entry["final_url"].endswith("v=second-public-id")


def test_main_redacts_query_secret_from_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    raw = "https://example.com/source?access_token=top-secret"

    def fail(*_args, **_kwargs):
        raise URLError(f"network failed for {raw}")

    monkeypatch.setattr(cache_source, "_fetch", fail)
    assert (
        cache_source.main(["cache_source.py", raw, "--cache-root", str(tmp_path)]) == 1
    )
    error = capsys.readouterr().err
    assert "top-secret" not in error
    assert "REDACTED" in error


def test_browser_execution_is_unconditionally_disabled() -> None:
    with pytest.raises(cache_source.PlaywrightUnavailable, match="disabled"):
        cache_source._fetch_via_playwright("https://example.com/source")


def test_browser_flag_fails_before_any_fetch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    called = False

    def unexpected(*_args, **_kwargs):
        nonlocal called
        called = True
        return (200, b"should not run", "text/plain", None, None)

    monkeypatch.setattr(cache_source, "_fetch", unexpected)
    monkeypatch.setattr(cache_source, "_fetch_via_playwright", unexpected)
    with pytest.raises(cache_source.PlaywrightUnavailable, match="disabled"):
        cache_source.cache_one(
            "https://example.com/source",
            cache_root=tmp_path,
            fetched_at="2026-07-14",
            topic="security",
            escalate_on_failure=True,
        )
    assert called is False

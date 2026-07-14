"""Network safety primitives for research-source retrieval.

The cache is allowed to read public HTTP(S) sources only.  This module keeps
that boundary below both the CLI and browser escalation paths: it rejects
ambiguous/private targets, disables ambient proxies, pins each connection to a
validated DNS result, validates every redirect, and exposes URL redaction for
durable records and diagnostics.
"""

from __future__ import annotations

from collections.abc import Callable
import http.client
import ipaddress
import queue
import re
import socket
import ssl
import threading
import time
from typing import Any
from urllib.error import HTTPError
from urllib.parse import parse_qsl, urlsplit, urlunsplit
from urllib.request import (
    HTTPHandler,
    HTTPRedirectHandler,
    HTTPSHandler,
    ProxyHandler,
    Request,
    build_opener,
)


DEFAULT_MAX_REDIRECTS = 5
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_MAX_RESPONSE_BYTES = 25 * 1024 * 1024
DEFAULT_BROWSER_MAX_TOTAL_BYTES = 50 * 1024 * 1024
DEFAULT_BROWSER_MAX_REQUESTS = 200

_ALLOWED_SCHEMES = {"http", "https"}
_DEFAULT_PORTS = {"http": 80, "https": 443}
_FORBIDDEN_HOSTS = {
    "instance-data",
    "localhost",
    "localhost.localdomain",
    "metadata",
    "metadata.google.internal",
    "metadata.google",
}
_FORBIDDEN_HOST_SUFFIXES = (
    ".home.arpa",
    ".internal",
    ".invalid",
    ".local",
    ".localhost",
    ".test",
)
_CONTROL_OR_AMBIGUOUS = re.compile(r"[\x00-\x20\x7f\\]")
_PUBLIC_QUERY_KEYS: dict[str, frozenset[str]] = {
    # Public resource identifiers used by the migrated corpus. This is an
    # allowlist, not a general claim that parameters named ``id`` are safe.
    "dataverse.harvard.edu": frozenset({"persistentId"}),
    "export.arxiv.org": frozenset({"id_list"}),
    "journals.plos.org": frozenset({"id", "type"}),
    "openreview.net": frozenset({"id"}),
    "papers.ssrn.com": frozenset({"abstract_id"}),
    "webscope.sandbox.yahoo.com": frozenset({"datatype", "did"}),
    "www.aeaweb.org": frozenset({"id"}),
    "www.youtube.com": frozenset({"v"}),
}
_SAFE_LEGACY_URN = re.compile(
    r"^urn:legacy-(?:source|search-decision):[A-Za-z0-9._:-]+$"
)
_DURABLE_URL_IN_TEXT = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
_DURABLE_PATH_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]{0,127}$")
_URL_FINGERPRINT_MARKERS = (
    "checksum",
    "digest",
    "fingerprint",
    "hash",
    "md5",
    "sha1",
    "sha256",
    "sha512",
)

Resolver = Callable[..., list[tuple[Any, ...]]]
SocketTracker = Callable[[socket.socket], None]

# Neither the platform resolver nor urllib's header parser exposes a portable
# cancellation primitive. Bound each watchdog class to one live daemon so a
# wedged OS call cannot create an unbounded thread leak. Later requests fail at
# their own deadline while that one worker remains stuck.
_DNS_GATE = threading.BoundedSemaphore(1)
_OPEN_GATE = threading.BoundedSemaphore(1)


class RetrievalSecurityError(OSError):
    """A URL or network transition crossed the public-read boundary."""


class ResponseTooLargeError(RetrievalSecurityError):
    """A response exceeded the configured byte ceiling."""


def redact_url(url: str) -> str:
    """Return a record-safe URL without userinfo, fragments, or query details.

    Query-key heuristics are not a safe secret boundary: signed URLs use many
    vendor-specific key names, and apparently harmless values can still be
    bearer credentials. Query keys can themselves expose account names or
    credential formats, so durable records replace the entire query with one
    fixed marker rather than retaining attacker-controlled names.
    """
    try:
        parsed = urlsplit(url)
        host = parsed.hostname
        if not host:
            return "<redacted-invalid-url>"
        try:
            port = parsed.port
        except ValueError:
            port = None
        host_for_netloc = f"[{host}]" if ":" in host else host
        netloc = host_for_netloc + (f":{port}" if port is not None else "")
        return urlunsplit(
            (
                parsed.scheme.lower(),
                netloc,
                parsed.path,
                "redacted=REDACTED" if parsed.query else "",
                "",
            )
        )
    except (TypeError, ValueError, UnicodeError):
        return "<redacted-invalid-url>"


def redact_exception(exc: BaseException, source_url: str) -> str:
    """Render an exception while removing an exact sensitive request URL."""
    message = str(exc).replace(source_url, redact_url(source_url))

    def _replace(match: re.Match[str]) -> str:
        return redact_url(match.group(0).rstrip(".,;:)"))

    return re.sub(r"https?://[^\s'\"]+", _replace, message)


def _normalized_target(url: str) -> tuple[str, str, int]:
    if not isinstance(url, str) or not url or _CONTROL_OR_AMBIGUOUS.search(url):
        raise RetrievalSecurityError(
            "URL contains whitespace, controls, or a backslash"
        )
    try:
        parsed = urlsplit(url)
        scheme = parsed.scheme.lower()
        host = parsed.hostname
        port = parsed.port
    except (ValueError, UnicodeError) as exc:
        raise RetrievalSecurityError("URL cannot be parsed safely") from exc
    if scheme not in _ALLOWED_SCHEMES:
        raise RetrievalSecurityError(f"URL scheme {scheme!r} is not allowed")
    if parsed.username is not None or parsed.password is not None:
        raise RetrievalSecurityError("credentials in source URLs are not allowed")
    if not host:
        raise RetrievalSecurityError("URL has no hostname")
    try:
        normalized_host = host.rstrip(".").encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise RetrievalSecurityError("URL hostname is not valid IDNA") from exc
    if not normalized_host:
        raise RetrievalSecurityError("URL has an empty hostname")
    if normalized_host in _FORBIDDEN_HOSTS or normalized_host.endswith(
        _FORBIDDEN_HOST_SUFFIXES
    ):
        raise RetrievalSecurityError(
            f"hostname is reserved or local: {redact_url(url)}"
        )
    effective_port = port if port is not None else _DEFAULT_PORTS[scheme]
    if effective_port != _DEFAULT_PORTS[scheme]:
        raise RetrievalSecurityError(
            f"non-standard port is not allowed for {scheme}: {effective_port}"
        )
    return scheme, normalized_host, effective_port


def validate_record_url(
    url: str,
    *,
    allow_public_query: bool = False,
    allow_legacy_urn: bool = False,
) -> str:
    """Validate that a URL is safe to persist in a canonical record.

    This is deliberately DNS-free so historical records remain auditable when
    a source is offline.  It enforces the same syntax/credential boundary as
    retrieval and requires every persisted query value to have been redacted.
    """
    try:
        parsed = urlsplit(url)
    except (TypeError, ValueError, UnicodeError) as exc:
        raise RetrievalSecurityError("record URL cannot be parsed safely") from exc
    if allow_legacy_urn and _SAFE_LEGACY_URN.fullmatch(url):
        return url
    _scheme, normalized_host, _port = _normalized_target(url)
    if parsed.fragment:
        raise RetrievalSecurityError("fragments are not allowed in record URLs")
    query = parse_qsl(parsed.query, keep_blank_values=True)
    public_keys = _PUBLIC_QUERY_KEYS.get(normalized_host, frozenset())
    public_identifier_query = (
        allow_public_query
        and bool(query)
        and all(
            key in public_keys
            and bool(value)
            and len(value) <= 512
            and not _CONTROL_OR_AMBIGUOUS.search(key)
            and not _CONTROL_OR_AMBIGUOUS.search(value)
            for key, value in query
        )
    )
    fixed_redaction_query = parsed.query == "redacted=REDACTED"
    if query and not fixed_redaction_query and not public_identifier_query:
        raise RetrievalSecurityError(
            "record URL query values must be REDACTED using exactly "
            "redacted=REDACTED, or match the domain-specific "
            "public-identifier allowlist"
        )
    return url


def _is_url_fingerprint_field(key: Any) -> bool:
    """Return whether a field name plausibly fingerprints a request URL."""
    raw = str(key)
    raw = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", raw)
    raw = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", "_", raw)
    normalized = re.sub(r"[^a-z0-9]+", "_", raw.lower()).strip("_")
    tokens = set(normalized.split("_"))
    has_locator = (
        "url" in tokens
        or "uri" in tokens
        or "request" in tokens
        or "requested" in tokens
        or "href" in tokens
        or "link" in tokens
        or "endpoint" in tokens
        or "locator" in tokens
        or normalized.startswith(("url", "uri"))
    )
    return has_locator and any(
        marker in tokens or marker in normalized
        for marker in _URL_FINGERPRINT_MARKERS
    )


def _embedded_urls(text: str) -> list[str]:
    urls: list[str] = []
    for match in _DURABLE_URL_IN_TEXT.finditer(text):
        candidate = match.group(0)
        while candidate and candidate[-1] in ".,;:!?)]}":
            candidate = candidate[:-1]
        if candidate:
            urls.append(candidate)
    return urls


def durable_value_errors(value: Any, loc: str) -> list[str]:
    """Recursively reject secret-bearing URLs and URL fingerprints.

    Durable records contain URLs in more than fields named ``*_url``: titles,
    excerpts, queries, notes, and nested policy objects are all attacker-
    controlled surfaces. This scanner therefore validates every embedded
    HTTP(S) URL and rejects ambiguous URL/request fingerprint aliases at any
    depth.
    """
    errors: list[str] = []
    if isinstance(value, dict):
        for index, (key, child) in enumerate(value.items()):
            raw_key = str(key)
            key_loc = f"{loc}.mapping_key[{index}]"
            # Mapping keys are attacker-controlled durable text too. Scan them
            # at an index-only location so a secret-bearing key is never echoed
            # into a diagnostic path.
            errors.extend(durable_value_errors(raw_key, key_loc))
            key_label = (
                raw_key
                if _DURABLE_PATH_KEY.fullmatch(raw_key)
                else f"mapping_value[{index}]"
            )
            child_loc = f"{loc}.{key_label}"
            if _is_url_fingerprint_field(key):
                errors.append(
                    f"{child_loc}: forbidden URL hash/digest/fingerprint field; "
                    "URL fingerprints are offline guessing oracles"
                )
            errors.extend(durable_value_errors(child, child_loc))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(durable_value_errors(child, f"{loc}[{index}]"))
    elif isinstance(value, str):
        for index, url in enumerate(_embedded_urls(value)):
            try:
                validate_record_url(url, allow_public_query=True)
            except RetrievalSecurityError as exc:
                errors.append(
                    f"{loc}.embedded_url[{index}]: unsafe durable URL: {exc}"
                )
    return errors


def _validate_retrieval_query(url: str, normalized_host: str) -> None:
    """Reject bearer/signed query strings before DNS or network access.

    Only a small host-and-key allowlist of public resource identifiers is
    accepted. A redacted placeholder can be safe to record, but is never a URL
    that this generic retriever should fetch.
    """
    parsed = urlsplit(url)
    if parsed.fragment:
        raise RetrievalSecurityError("fragments are not allowed in retrieval URLs")
    if not parsed.query:
        return
    query = parse_qsl(parsed.query, keep_blank_values=True)
    public_keys = _PUBLIC_QUERY_KEYS.get(normalized_host, frozenset())
    if not query or not all(
        key in public_keys
        and bool(value)
        and len(value) <= 512
        and not _CONTROL_OR_AMBIGUOUS.search(key)
        and not _CONTROL_OR_AMBIGUOUS.search(value)
        for key, value in query
    ):
        raise RetrievalSecurityError(
            "query-bearing retrieval is allowed only for domain-specific "
            "public resource identifiers; use a query-free canonical URL"
        )


def validate_retrieval_url(url: str) -> str:
    """Validate DNS-free syntax and public-query policy for retrieval."""
    _scheme, normalized_host, _port = _normalized_target(url)
    _validate_retrieval_query(url, normalized_host)
    return url


def record_safe_url(url: str) -> str:
    """Preserve allowlisted public identifiers; redact every other query."""
    try:
        return validate_record_url(url, allow_public_query=True)
    except RetrievalSecurityError:
        return redact_url(url)


def _is_public_ip(value: str) -> bool:
    try:
        address = ipaddress.ip_address(value.split("%", 1)[0])
    except ValueError:
        return False
    return address.is_global


def _resolve_public_host(
    host: str,
    port: int,
    *,
    resolver: Resolver | None = None,
    deadline: float | None = None,
) -> list[tuple[Any, ...]]:
    try:
        if deadline is None:
            lookup = resolver or socket.getaddrinfo
            infos = lookup(host, port, type=socket.SOCK_STREAM)
        else:
            # getaddrinfo has no portable timeout. Run the OS resolver in a
            # daemon thread so the request can still honor its absolute
            # deadline. A wedged resolver cannot keep the CLI process alive.
            result_queue: queue.Queue[tuple[bool, Any]] = queue.Queue(maxsize=1)
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not _DNS_GATE.acquire(timeout=remaining):
                raise TimeoutError("hostname resolution deadline expired")
            lookup = resolver or socket.getaddrinfo

            def resolve() -> None:
                try:
                    result_queue.put(
                        (
                            True,
                            lookup(host, port, type=socket.SOCK_STREAM),
                        )
                    )
                except BaseException as exc:  # passed back to the caller
                    result_queue.put((False, exc))
                finally:
                    _DNS_GATE.release()

            worker = threading.Thread(target=resolve, daemon=True)
            try:
                worker.start()
            except BaseException:
                _DNS_GATE.release()
                raise
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("hostname resolution deadline expired")
            try:
                succeeded, payload = result_queue.get(timeout=remaining)
            except queue.Empty as exc:
                raise TimeoutError("hostname resolution deadline expired") from exc
            if not succeeded:
                raise payload
            infos = payload
    except TimeoutError:
        raise
    except OSError as exc:
        raise RetrievalSecurityError(f"hostname resolution failed for {host}") from exc
    if not infos:
        raise RetrievalSecurityError(f"hostname resolved to no addresses: {host}")
    unsafe: list[str] = []
    usable: list[tuple[Any, ...]] = []
    for info in infos:
        try:
            address = str(info[4][0])
        except (IndexError, TypeError):
            unsafe.append("<malformed-address>")
            continue
        if not _is_public_ip(address):
            unsafe.append(address)
        else:
            usable.append(info)
    # Reject mixed public/private answers too.  Choosing the public member would
    # make rebinding and split-horizon DNS behavior non-obvious.
    if unsafe:
        raise RetrievalSecurityError(
            f"hostname resolves to a non-public address: {host} ({', '.join(unsafe)})"
        )
    if not usable:
        raise RetrievalSecurityError(f"hostname has no public address: {host}")
    return usable


def validate_public_url(
    url: str,
    *,
    resolver: Resolver | None = None,
    deadline: float | None = None,
) -> str:
    """Validate syntax, port, DNS results, and public routability."""
    _scheme, host, port = _normalized_target(url)
    _validate_retrieval_query(url, host)
    try:
        literal = ipaddress.ip_address(host.split("%", 1)[0])
    except ValueError:
        if re.fullmatch(r"[0-9.]+", host) or host.lower().startswith("0x"):
            raise RetrievalSecurityError(
                f"ambiguous numeric hostname is not allowed: {redact_url(url)}"
            )
        _resolve_public_host(host, port, resolver=resolver, deadline=deadline)
    else:
        if not literal.is_global:
            raise RetrievalSecurityError(
                f"literal address is not public: {redact_url(url)}"
            )
    return url


def _connect_public(
    host: str,
    port: int,
    timeout: float | object,
    source_address: tuple[str, int] | None,
    *,
    resolver: Resolver | None,
    deadline: float | None = None,
    socket_tracker: SocketTracker | None = None,
) -> socket.socket:
    infos = _resolve_public_host(host, port, resolver=resolver, deadline=deadline)
    last_error: OSError | None = None
    for family, socktype, proto, _canonname, sockaddr in infos:
        sock: socket.socket | None = None
        try:
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("public retrieval deadline expired")
            else:
                remaining = timeout
            sock = socket.socket(family, socktype, proto)
            if remaining is not socket._GLOBAL_DEFAULT_TIMEOUT:
                sock.settimeout(remaining)  # type: ignore[arg-type]
            if source_address:
                sock.bind(source_address)
            sock.connect(sockaddr)
            if socket_tracker is not None:
                socket_tracker(sock)
            return sock
        except OSError as exc:
            last_error = exc
            if sock is not None:
                sock.close()
    raise RetrievalSecurityError(
        f"could not connect to validated public host {host}"
    ) from last_error


def _http_connection_factory(
    resolver: Resolver | None,
    deadline: float,
    socket_tracker: SocketTracker | None,
):
    class PinnedHTTPConnection(http.client.HTTPConnection):
        def connect(self) -> None:
            self.sock = _connect_public(
                self.host,
                self.port,
                self.timeout,
                self.source_address,
                resolver=resolver,
                deadline=deadline,
                socket_tracker=socket_tracker,
            )
            if self._tunnel_host:
                self._tunnel()

    return PinnedHTTPConnection


def _https_connection_factory(
    resolver: Resolver | None,
    deadline: float,
    socket_tracker: SocketTracker | None,
):
    class PinnedHTTPSConnection(http.client.HTTPSConnection):
        def connect(self) -> None:
            raw_sock = _connect_public(
                self.host,
                self.port,
                self.timeout,
                self.source_address,
                resolver=resolver,
                deadline=deadline,
                socket_tracker=socket_tracker,
            )
            server_hostname = self.host
            if self._tunnel_host:
                self.sock = raw_sock
                self._tunnel()
                raw_sock = self.sock
                server_hostname = self._tunnel_host
            self.sock = self._context.wrap_socket(
                raw_sock,
                server_hostname=server_hostname,
            )
            if socket_tracker is not None:
                socket_tracker(self.sock)

    return PinnedHTTPSConnection


class _PinnedHTTPHandler(HTTPHandler):
    def __init__(
        self,
        resolver: Resolver | None,
        deadline: float,
        socket_tracker: SocketTracker | None = None,
    ) -> None:
        super().__init__()
        self._connection = _http_connection_factory(
            resolver, deadline, socket_tracker
        )

    def http_open(self, req: Request):
        return self.do_open(self._connection, req)


class _PinnedHTTPSHandler(HTTPSHandler):
    def __init__(
        self,
        resolver: Resolver | None,
        deadline: float,
        socket_tracker: SocketTracker | None = None,
    ) -> None:
        self._context = ssl.create_default_context()
        super().__init__(context=self._context)
        self._connection = _https_connection_factory(
            resolver, deadline, socket_tracker
        )

    def https_open(self, req: Request):
        return self.do_open(self._connection, req, context=self._context)


class _ValidatingRedirectHandler(HTTPRedirectHandler):
    def __init__(
        self,
        *,
        max_redirects: int,
        resolver: Resolver | None,
        deadline: float | None = None,
    ) -> None:
        super().__init__()
        self._max_redirects = max_redirects
        self._resolver = resolver
        self._deadline = deadline
        self._redirect_count = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self._redirect_count += 1
        if self._redirect_count > self._max_redirects:
            raise RetrievalSecurityError(
                f"redirect limit exceeded ({self._max_redirects}) for {redact_url(req.full_url)}"
            )
        old_scheme, old_host, old_port = _normalized_target(req.full_url)
        new_scheme, new_host, new_port = _normalized_target(newurl)
        if old_scheme == "https" and new_scheme != "https":
            raise RetrievalSecurityError("HTTPS-to-HTTP redirect is not allowed")
        validate_public_url(
            newurl, resolver=self._resolver, deadline=self._deadline
        )
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is None:
            return None
        if (old_scheme, old_host, old_port) != (new_scheme, new_host, new_port):
            # urllib currently preserves caller headers across redirects.  Keep
            # the allowlist intentionally tiny so future authenticated adapters
            # cannot leak credentials or origin-specific conditional values.
            allowed = {"user-agent", "accept-encoding"}
            for key, _value in list(redirected.header_items()):
                if key.lower() not in allowed:
                    redirected.remove_header(key)
        return redirected


def secure_urlopen(
    request: Request | str,
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    max_redirects: int = DEFAULT_MAX_REDIRECTS,
    resolver: Resolver | None = None,
):
    """Open one public GET/HEAD request through a DNS-pinned safe opener.

    Ambient proxy variables are intentionally ignored: a proxy would move the
    DNS and private-network boundary outside this process.  Callers that need a
    managed egress proxy should supply an audited adapter rather than silently
    inheriting shell state.
    """
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    if max_redirects < 0:
        raise ValueError("max_redirects must be non-negative")
    req = request if isinstance(request, Request) else Request(request)
    if req.get_method().upper() not in {"GET", "HEAD"}:
        raise RetrievalSecurityError("retrieval permits GET and HEAD only")
    deadline = time.monotonic() + timeout
    validate_public_url(req.full_url, resolver=resolver, deadline=deadline)
    req.remove_header("Accept-Encoding")
    req.add_header("Accept-Encoding", "identity")
    cancelled = threading.Event()
    active_sockets: set[socket.socket] = set()
    sockets_lock = threading.Lock()

    def track_socket(sock: socket.socket) -> None:
        close_immediately = False
        with sockets_lock:
            if cancelled.is_set():
                close_immediately = True
            else:
                active_sockets.add(sock)
        if close_immediately:
            try:
                sock.close()
            except (AttributeError, OSError):
                pass

    def abort_active_sockets() -> None:
        cancelled.set()
        with sockets_lock:
            sockets = tuple(active_sockets)
            active_sockets.clear()
        for sock in sockets:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except (AttributeError, OSError):
                pass
            try:
                sock.close()
            except (AttributeError, OSError):
                pass

    opener = build_opener(
        ProxyHandler({}),
        _PinnedHTTPHandler(resolver, deadline, track_socket),
        _PinnedHTTPSHandler(resolver, deadline, track_socket),
        _ValidatingRedirectHandler(
            max_redirects=max_redirects,
            resolver=resolver,
            deadline=deadline,
        ),
    )
    remaining = deadline - time.monotonic()
    if remaining <= 0 or not _OPEN_GATE.acquire(timeout=remaining):
        abort_active_sockets()
        raise TimeoutError("public retrieval deadline expired before headers")
    result_queue: queue.Queue[tuple[bool, Any]] = queue.Queue(maxsize=1)

    def open_request() -> None:
        try:
            response = opener.open(req, timeout=remaining)
            if cancelled.is_set():
                response.close()
                abort_active_sockets()
                return
            result_queue.put((True, response))
        except BaseException as exc:  # preserve exact urllib failure semantics
            result_queue.put((False, exc))
        finally:
            _OPEN_GATE.release()

    worker = threading.Thread(target=open_request, daemon=True)
    try:
        worker.start()
    except BaseException:
        _OPEN_GATE.release()
        raise
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        abort_active_sockets()
        raise TimeoutError("public retrieval deadline expired before headers")
    try:
        succeeded, payload = result_queue.get(timeout=remaining)
    except queue.Empty as exc:
        abort_active_sockets()
        raise TimeoutError("public retrieval deadline expired before headers") from exc
    if not succeeded:
        abort_active_sockets()
        if isinstance(payload, (HTTPError, RetrievalSecurityError, TimeoutError)):
            raise payload
        if isinstance(payload, OSError):
            raise RetrievalSecurityError(
                f"public retrieval failed for {redact_url(req.full_url)}"
            ) from payload
        raise payload
    try:
        setattr(payload, "_research_toolkit_deadline", deadline)
        setattr(payload, "_research_toolkit_abort", abort_active_sockets)
    except (AttributeError, TypeError):
        pass
    return payload


def _abort_response(response: Any) -> None:
    """Close a response and its tracked transport after a bounded-read failure."""
    abort = getattr(response, "_research_toolkit_abort", None)
    if callable(abort):
        abort()
    closer = getattr(response, "close", None)
    if callable(closer):
        try:
            closer()
        except OSError:
            pass


def _set_response_timeout(response: Any, timeout: float) -> None:
    """Set the remaining deadline on urllib/http.client's underlying socket."""
    current = response
    seen: set[int] = set()
    for _depth in range(8):
        if current is None or id(current) in seen:
            return
        seen.add(id(current))
        setter = getattr(current, "settimeout", None)
        if callable(setter):
            setter(max(timeout, 0.001))
            return
        next_value = None
        for attribute in ("fp", "raw", "_sock", "sock"):
            candidate = getattr(current, attribute, None)
            if candidate is not None and id(candidate) not in seen:
                next_value = candidate
                break
        current = next_value


def read_response_limited(
    response: Any,
    *,
    max_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
    deadline: float | None = None,
) -> bytes:
    """Read a response incrementally under byte, encoding, and time ceilings."""
    if max_bytes < 1:
        raise ValueError("max_bytes must be positive")
    if deadline is None:
        deadline = getattr(response, "_research_toolkit_deadline", None)
    if deadline is None:
        deadline = time.monotonic() + DEFAULT_TIMEOUT_SECONDS
    content_encoding = response.headers.get("Content-Encoding")
    if content_encoding and content_encoding.strip().lower() != "identity":
        _abort_response(response)
        raise RetrievalSecurityError(
            f"encoded response bodies are not allowed: {content_encoding!r}"
        )
    content_length = response.headers.get("Content-Length")
    if content_length is not None:
        try:
            declared = int(content_length)
        except (TypeError, ValueError):
            declared = -1
        if declared > max_bytes:
            _abort_response(response)
            raise ResponseTooLargeError(
                f"declared response size {declared} exceeds {max_bytes} bytes"
            )
    chunks: list[bytes] = []
    total = 0
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            _abort_response(response)
            raise TimeoutError("response body deadline expired")
        _set_response_timeout(response, remaining)
        allowance = max_bytes - total + 1
        try:
            # HTTPResponse.read1 performs at most one underlying socket read.
            # Recomputing the timeout for each read makes the wall-clock limit
            # absolute even when a peer drips bytes below an inactivity limit.
            reader = getattr(response, "read1", response.read)
            chunk = reader(min(64 * 1024, allowance))
        except TypeError:
            # A small compatibility surface for hand-rolled test doubles.  Real
            # HTTPResponse objects always support sized reads.
            try:
                chunk = response.read()
            except BaseException:
                _abort_response(response)
                raise
            if len(chunk) > max_bytes:
                _abort_response(response)
                raise ResponseTooLargeError(f"response exceeds {max_bytes} bytes")
            if time.monotonic() > deadline:
                _abort_response(response)
                raise TimeoutError("response body deadline expired")
            return chunk
        except BaseException:
            _abort_response(response)
            raise
        if time.monotonic() > deadline:
            _abort_response(response)
            raise TimeoutError("response body deadline expired")
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            _abort_response(response)
            raise ResponseTooLargeError(f"response exceeds {max_bytes} bytes")
        chunks.append(chunk)
    return b"".join(chunks)

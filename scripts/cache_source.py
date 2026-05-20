#!/usr/bin/env python3
"""Cache public source artifacts into the strict-live global content cache.

Default path is dependency-free (urllib). v2.2.1 adds optional Playwright
escalation for JS-rendered sites that urllib can't see — gated behind
``--escalate-on-failure`` so the script stays usable without Playwright
installed.

Stores raw bytes, a best-effort text derivative, and metadata JSON under
a content-addressed cache root. Prints manifest-ready YAML entries; a
gather/freshness skill is responsible for appending them deliberately.
"""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# Detection heuristics for when urllib's result is suspect and Playwright
# might do better. Tuned conservatively: a 500-char minimum catches blank
# SPAs and "Please enable JavaScript" placeholders without false-positiving
# legitimate short pages (most useful sources are >1k chars after
# extraction).
SUSPECT_TEXT_MIN_CHARS = 500
SUSPECT_JS_MARKERS = (
    "Please enable JavaScript",
    "Please enable Javascript",
    "JavaScript is required",
    "<noscript>",
    "id=\"__next\"></div>",  # next.js empty mount
    "id=\"root\"></div>",  # CRA empty mount
)
ESCALATABLE_HTTP_STATUSES = (403, 429)
PLAYWRIGHT_FETCH_METHOD = "playwright_rendered"
URLLIB_FETCH_METHOD = "urllib"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_text(data: bytes, content_type: str) -> tuple[str, str]:
    if content_type.startswith("text/") or "json" in content_type or "html" in content_type:
        return data.decode("utf-8", errors="replace"), "ok"
    return (
        f"[raw binary cached; no dependency-free extractor available for {content_type}]\n",
        "raw_only",
    )


def _fetch(
    source_url: str,
    *,
    if_etag: str | None = None,
    if_last_modified: str | None = None,
) -> tuple[int, bytes, str, str | None, str | None]:
    """Fetch a URL with optional conditional headers.

    Returns (status_code, body_bytes, content_type, etag, last_modified).
    On a 304 Not Modified response, body_bytes is empty.
    """
    headers = {"User-Agent": "research_toolkit/2.1 strict-live cache"}
    if if_etag:
        headers["If-None-Match"] = if_etag
    if if_last_modified:
        headers["If-Modified-Since"] = if_last_modified
    req = Request(source_url, headers=headers)
    try:
        with urlopen(req, timeout=30) as response:  # noqa: S310
            status = response.status if hasattr(response, "status") else response.getcode()
            content_type = response.headers.get_content_type() or "application/octet-stream"
            etag = response.headers.get("ETag")
            last_modified = response.headers.get("Last-Modified")
            return status, response.read(), content_type, etag, last_modified
    except HTTPError as exc:
        if exc.code == 304:
            return 304, b"", exc.headers.get_content_type() or "", exc.headers.get("ETag"), exc.headers.get("Last-Modified")
        raise


def _content_is_suspect(raw: bytes, content_type: str) -> tuple[bool, str]:
    """Heuristic: does urllib's result look like it might be a JS-rendered
    page that didn't actually load? Returns (is_suspect, reason)."""
    if not raw:
        return True, "empty response body"
    # For HTML/text content, decode and check length + markers
    if content_type.startswith("text/") or "html" in content_type:
        try:
            text = raw.decode("utf-8", errors="replace")
        except Exception:
            return False, ""
        if len(text) < SUSPECT_TEXT_MIN_CHARS:
            return True, f"extracted text only {len(text)} chars (< {SUSPECT_TEXT_MIN_CHARS} threshold)"
        for marker in SUSPECT_JS_MARKERS:
            if marker in text:
                return True, f"contains JS-required marker {marker!r}"
    return False, ""


def _fetch_via_playwright(source_url: str) -> tuple[int, bytes, str, str | None, str | None]:
    """Render with headless Chromium. Lazy-imports playwright so the script
    stays usable without Playwright installed.

    Returns the same tuple shape as ``_fetch``: (status, body_bytes,
    content_type, etag, last_modified). etag/last_modified are None
    because Playwright doesn't expose the conditional-GET headers from
    the response cleanly via its high-level API.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright escalation requested but the 'playwright' package is "
            "not installed. Run: pip install -e \".[dev]\" && playwright install chromium"
        ) from exc

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context(
                user_agent="research_toolkit/2.2.1 strict-live cache (Playwright)"
            )
            page = context.new_page()
            response = page.goto(source_url, wait_until="domcontentloaded", timeout=30_000)
            # Give SPAs a moment to hydrate; networkidle would be ideal but
            # many CDN-served sites never reach idle.
            page.wait_for_timeout(1500)
            html = page.content()
            status = response.status if response is not None else 200
            content_type = "text/html"
            if response is not None:
                ct = response.headers.get("content-type")
                if isinstance(ct, str):
                    content_type = ct.split(";", 1)[0].strip() or "text/html"
            return status, html.encode("utf-8"), content_type, None, None
        finally:
            browser.close()


def _private_write(path: Path, data: bytes | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        path.write_text(data, encoding="utf-8")
    else:
        path.write_bytes(data)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def cache_one(
    source_url: str,
    *,
    cache_root: Path,
    fetched_at: str,
    topic: str,
    if_etag: str | None = None,
    if_last_modified: str | None = None,
    prior_cache_id: str | None = None,
    prior_sha256: str | None = None,
    escalate_on_failure: bool = False,
) -> dict:
    """Cache a URL. Supports 304-first conditional GET when prior etag /
    last-modified are provided. v2.2.1 adds optional Playwright escalation.

    - On HTTP 304 → emit a `revisit` record (server-not-modified) referring
      to prior_cache_id. Zero new bytes.
    - On HTTP 200 with hash matching prior_sha256 → emit a `revisit` record
      (identical-payload-digest) referring to prior_cache_id. Zero new bytes
      written (existing cache is untouched).
    - On HTTP 200 with new content → emit a fresh `capture` record with
      raw/text/metadata files written.

    When ``escalate_on_failure=True``:
    - HTTP 403 / 429 from urllib → retry via Playwright.
    - urllib succeeds but content is suspect (blank / too short / JS-required
      marker) → retry via Playwright.
    - The resulting capture record carries ``fetch_method: playwright_rendered``
      so audits know JS rendering was needed.
    """
    fetch_method = URLLIB_FETCH_METHOD
    escalation_reason: str | None = None
    try:
        status, raw, content_type, etag, last_modified = _fetch(
            source_url, if_etag=if_etag, if_last_modified=if_last_modified
        )
    except HTTPError as exc:
        if escalate_on_failure and exc.code in ESCALATABLE_HTTP_STATUSES:
            escalation_reason = f"urllib HTTP {exc.code}"
            status, raw, content_type, etag, last_modified = _fetch_via_playwright(source_url)
            fetch_method = PLAYWRIGHT_FETCH_METHOD
        else:
            raise

    # Successful urllib fetch — but check if content looks suspect
    if (
        fetch_method == URLLIB_FETCH_METHOD
        and escalate_on_failure
        and status not in (304,)
    ):
        is_suspect, reason = _content_is_suspect(raw, content_type)
        if is_suspect:
            escalation_reason = reason
            status, raw, content_type, etag, last_modified = _fetch_via_playwright(source_url)
            fetch_method = PLAYWRIGHT_FETCH_METHOD

    # 304 Not Modified → revisit record (server-not-modified)
    if status == 304 and prior_cache_id:
        return {
            "cache_id": f"cache_{prior_cache_id.removeprefix('cache_')}_r{fetched_at.replace('-', '')}",
            "source_url": source_url,
            "fetched_at": fetched_at,
            "record_type": "revisit",
            "revisit_profile": "server-not-modified",
            "refers_to_cache_id": prior_cache_id,
            "refers_to_fetched_at": None,  # caller can fill in if known
            "http_status": 304,
            "http_etag": etag,
            "http_last_modified": last_modified,
        }

    digest = _sha256(raw)

    # 200 OK but identical to prior → revisit (identical-payload-digest)
    if prior_cache_id and prior_sha256 and digest == prior_sha256:
        return {
            "cache_id": f"cache_{prior_cache_id.removeprefix('cache_')}_r{fetched_at.replace('-', '')}",
            "source_url": source_url,
            "fetched_at": fetched_at,
            "record_type": "revisit",
            "revisit_profile": "identical-payload-digest",
            "refers_to_cache_id": prior_cache_id,
            "refers_to_fetched_at": None,
            "http_status": 200,
            "http_etag": etag,
            "http_last_modified": last_modified,
        }

    # New capture
    blob_dir = cache_root / "blobs" / "sha256"
    text_dir = cache_root / "text" / "sha256"
    meta_dir = cache_root / "metadata" / "sha256"

    raw_path = blob_dir / digest
    text_path = text_dir / f"{digest}.txt"
    metadata_path = meta_dir / f"{digest}.json"

    text, extraction_status = _safe_text(raw, content_type)
    metadata = {
        "schema_version": 2,
        "topic": topic,
        "source_url": source_url,
        "fetched_at": fetched_at,
        "content_type": content_type,
        "bytes": len(raw),
        "sha256": digest,
        "cache_policy": "max_local_private",
        "restricted": False,
        "rights_status": "private_use",
        "extraction_status": extraction_status,
        "fetch_method": fetch_method,
        "http_etag": etag,
        "http_last_modified": last_modified,
    }
    if escalation_reason:
        metadata["escalation_reason"] = escalation_reason

    cache_root.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(cache_root, 0o700)
    except OSError:
        pass
    _private_write(raw_path, raw)
    _private_write(text_path, text)
    _private_write(metadata_path, json.dumps(metadata, indent=2, sort_keys=True) + "\n")

    entry = {
        "cache_id": f"cache_{digest[:16]}",
        "source_url": source_url,
        "fetched_at": fetched_at,
        "record_type": "capture",
        "content_type": content_type or mimetypes.guess_type(source_url)[0] or "application/octet-stream",
        "bytes": len(raw),
        "sha256": digest,
        "raw_path": str(raw_path),
        "text_path": str(text_path),
        "metadata_path": str(metadata_path),
        "restricted": False,
        "rights_status": "private_use",
        "extraction_status": extraction_status,
    }
    # Only emit fetch_method when it deviates from the urllib default — keeps
    # existing fixtures byte-stable.
    if fetch_method != URLLIB_FETCH_METHOD:
        entry["fetch_method"] = fetch_method
    if etag:
        entry["http_etag"] = etag
    if last_modified:
        entry["http_last_modified"] = last_modified
    # Link back to prior capture if this is a re-fetch with content changed
    if prior_cache_id:
        entry["refers_to_cache_id"] = prior_cache_id
    return entry


def _print_yaml_entry(entry: dict) -> None:
    print("- cache_id: " + entry["cache_id"])
    is_revisit = entry.get("record_type") == "revisit"
    if is_revisit:
        keys = (
            "source_url",
            "fetched_at",
            "record_type",
            "revisit_profile",
            "refers_to_cache_id",
            "refers_to_fetched_at",
            "http_status",
            "http_etag",
            "http_last_modified",
        )
    else:
        keys = (
            "source_url",
            "fetched_at",
            "record_type",
            "content_type",
            "bytes",
            "sha256",
            "raw_path",
            "text_path",
            "metadata_path",
            "restricted",
            "rights_status",
            "extraction_status",
            "fetch_method",
            "http_etag",
            "http_last_modified",
            "refers_to_cache_id",
        )
    for key in keys:
        if key not in entry:
            continue
        value = entry[key]
        if value is None:
            continue
        if isinstance(value, bool):
            value = str(value).lower()
        print(f"  {key}: {value}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Cache public source artifacts. Supports 304-first conditional GET "
        "via --if-etag / --if-last-modified / --prior-cache-id for v2.1 revisit records."
    )
    parser.add_argument("source_url", nargs="+")
    parser.add_argument("--cache-root", default="~/Claude/research_cache")
    parser.add_argument("--topic", default="unspecified")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument(
        "--if-etag",
        help="Send If-None-Match header; 304 response emits a revisit record",
    )
    parser.add_argument(
        "--if-last-modified",
        help="Send If-Modified-Since header (e.g., 'Wed, 21 Oct 2026 07:28:00 GMT')",
    )
    parser.add_argument(
        "--prior-cache-id",
        help="cache_id of the prior capture; populated on revisit records as refers_to_cache_id",
    )
    parser.add_argument(
        "--prior-sha256",
        help="sha256 of the prior capture; if the new fetch hashes identically, emits "
        "an identical-payload-digest revisit instead of a fresh capture",
    )
    parser.add_argument(
        "--escalate-on-failure",
        action="store_true",
        help="v2.2.1: if urllib returns 403/429 OR suspect content (blank / too short / "
        "JS-required marker), retry via headless Chromium (Playwright). Requires "
        "'pip install -e \".[dev]\" && playwright install chromium'.",
    )
    args = parser.parse_args(argv[1:])

    root = Path(args.cache_root).expanduser().resolve()
    failures = 0
    for source_url in args.source_url:
        try:
            entry = cache_one(
                source_url,
                cache_root=root,
                fetched_at=args.date,
                topic=args.topic,
                if_etag=args.if_etag,
                if_last_modified=args.if_last_modified,
                prior_cache_id=args.prior_cache_id,
                prior_sha256=args.prior_sha256,
                escalate_on_failure=args.escalate_on_failure,
            )
        except (URLError, TimeoutError, OSError) as exc:
            failures += 1
            print(f"ERROR caching {source_url}: {exc}", file=sys.stderr)
            continue
        _print_yaml_entry(entry)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

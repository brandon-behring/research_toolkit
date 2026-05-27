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
from datetime import date, datetime, timezone
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import re
import socket
import sys
import uuid
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

# v2.3 PDF extraction (closes #11). Cascade: pdfplumber for fast text + Docling
# (lazy-imported) when equation richness is detected. Both are pyproject hard
# deps so the cascade Just Works on a clean install.
#
# Unicode math chars + commonly-used Greek letters (subset — keeps the regex
# fast; expand if false-negative rate is high in practice). Latin-1 superscript
# / subscript codepoints are deliberately excluded — they appear in normal text
# (e.g., 'CO₂', '1st'). Greek lowercase/uppercase is included because academic
# papers use it heavily even for non-math purposes; the threshold compensates.
_UNICODE_MATH_CHARS = set("∑∫∂≤≥∈∉⊕⊗≠≈≡∀∃∇∞±×÷∝√∆Σ∏⊂⊃⊆⊇∩∪∧∨¬→←↔⇒⇐⇔⊥∥∠⟨⟩")
_GREEK_CHARS = set("αβγδεζηθικλμνξοπρστυφχψωΓΔΘΛΞΠΣΦΨΩ")
_LATEX_RESIDUE_PATTERNS = (
    r"\\frac\b",
    r"\\sum\b",
    r"\\int\b",
    r"\\prod\b",
    r"\\sqrt\b",
    r"\\partial\b",
    r"\\begin\{equation\}",
    r"\\begin\{align\}",
    r"\\begin\{matrix\}",
)
_LATEX_RESIDUE_RE = re.compile("|".join(_LATEX_RESIDUE_PATTERNS))
# Equation richness threshold: math-char density per 1000 chars (excludes
# Greek which is over-counted in academic text). Chosen empirically: most
# plain-text academic PDFs land at ~0-2, equation-rich PDFs ~5-20+.
_EQUATION_DENSITY_THRESHOLD = 3.0

# v2.3 extraction_status enum (closes #11 + #10). Hierarchy from best to worst:
# rich > ok > ok_text_only > degraded > stub > partial > failed > raw_only.
EXTRACTION_STATUS_OK = "ok"  # pdfplumber/text-content extracted cleanly
EXTRACTION_STATUS_RICH = "rich"  # Docling extracted equations as LaTeX
EXTRACTION_STATUS_OK_TEXT_ONLY = "ok_text_only"  # math detected, Docling failed/absent
EXTRACTION_STATUS_DEGRADED = "degraded"  # both extractors low-yield (image PDF)
EXTRACTION_STATUS_PARTIAL = "partial"  # encrypted PDF, partial extraction
EXTRACTION_STATUS_FAILED = "failed"  # both extractors errored
EXTRACTION_STATUS_RAW_ONLY = "raw_only"  # non-PDF binary, no extractor
EXTRACTION_STATUS_STUB = "stub"  # A3: JS-shell HTML stub detected

# Statuses that should emit a stderr WARN. ok / rich / raw_only stay silent.
LOUD_EXTRACTION_STATUSES = {
    EXTRACTION_STATUS_OK_TEXT_ONLY,
    EXTRACTION_STATUS_DEGRADED,
    EXTRACTION_STATUS_PARTIAL,
    EXTRACTION_STATUS_FAILED,
    EXTRACTION_STATUS_STUB,
}
# Statuses where --strict-extraction causes a non-zero exit (everything
# except ok / rich / raw_only).
STRICT_FAIL_STATUSES = LOUD_EXTRACTION_STATUSES
# Minimum chars-per-page for a PDF to NOT be flagged as degraded.
_DEGRADED_CHARS_PER_PAGE_THRESHOLD = 100


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _detect_equation_richness(text: str) -> tuple[bool, str]:
    """v2.3: scan extracted text for equation markers.

    Returns ``(is_math_rich, reason)``. Tuned to minimize false positives on
    chemistry papers (e.g., ``H₂O``), set notation in CS papers, and
    Greek-letter usage in linguistics/history papers. The cost of a false
    positive is small (an extra Docling escalation + a WARN); the cost of a
    false negative is lost equation fidelity.
    """
    if not text:
        return False, ""
    # LaTeX residue is a near-zero false-positive signal — math papers
    # sometimes leak \frac{} et al through PDF extraction.
    if _LATEX_RESIDUE_RE.search(text):
        return True, "LaTeX residue (\\frac / \\sum / \\int / \\begin{equation})"
    # Unicode math density per 1000 chars. Greek alone is excluded (over-counts
    # academic prose); requires the harder math operators to trip.
    math_count = sum(1 for c in text if c in _UNICODE_MATH_CHARS)
    density = (math_count / len(text)) * 1000 if text else 0
    if density >= _EQUATION_DENSITY_THRESHOLD:
        return True, (
            f"unicode math density {density:.1f}/1000 chars "
            f"(>= {_EQUATION_DENSITY_THRESHOLD} threshold)"
        )
    # Garbled fragment: clusters of math symbols + Greek with little prose.
    # Mostly catches papers whose pdfplumber output has equations stripped
    # mid-sentence, leaving "α + β ≤ γ" islands with no surrounding words.
    greek_count = sum(1 for c in text if c in _GREEK_CHARS)
    if math_count + greek_count >= 20 and len(text) < 5000:
        return True, (
            f"dense math/Greek cluster ({math_count + greek_count} chars in "
            f"{len(text)}-char snippet — likely truncated equation context)"
        )
    return False, ""


def _extract_pdf_text(raw: bytes, *, docling_cache_dir: str | None = None) -> tuple[str, str, list[str]]:
    """v2.3 cascade: pdfplumber → equation detection → Docling escalation.

    Returns ``(text, extraction_status, warnings)`` where:
    - text: extracted text content (empty bytes guard: returns a short
      explanatory string instead of empty so downstream text_path readers
      always get a non-empty file).
    - extraction_status: one of EXTRACTION_STATUS_* constants.
    - warnings: list of human-readable strings explaining any non-ideal
      outcome. Empty when status is `ok` or `rich`.
    """
    warnings: list[str] = []

    # Stage 1: pdfplumber (fast path, always tried first).
    try:
        import pdfplumber
        from io import BytesIO
    except ImportError:
        warnings.append(
            "pdfplumber not installed (pip install -e \".\") — falling back to raw_only"
        )
        return (
            "[PDF cached; pdfplumber unavailable, install pdfplumber>=0.11]\n",
            EXTRACTION_STATUS_RAW_ONLY,
            warnings,
        )

    try:
        with pdfplumber.open(BytesIO(raw)) as pdf:
            page_texts = []
            for page in pdf.pages:
                t = page.extract_text() or ""
                page_texts.append(t)
            text = "\n\n".join(page_texts)
            num_pages = len(pdf.pages)
    except Exception as exc:
        # Encryption detection: pdfplumber raises PdfminerException (often with
        # empty message) for encrypted PDFs. Catch by class name + message
        # heuristics since pdfminer's exception class varies across versions.
        msg = str(exc).lower()
        exc_type = type(exc).__name__.lower()
        is_encrypted = (
            "encrypted" in msg
            or "password" in msg
            or "pdfencryption" in exc_type
            or "pdfminerexception" in exc_type
        )
        if is_encrypted:
            # Confirm via pypdf which has clearer encryption signaling
            try:
                from pypdf import PdfReader
                from pypdf.errors import PdfReadError
                reader = PdfReader(BytesIO(raw))
                if reader.is_encrypted:
                    warnings.append(
                        f"PDF encrypted; pdfplumber refused extraction: {exc.__class__.__name__}"
                    )
                    return (
                        f"[PDF encrypted; install password OR use a non-encrypted source]\n",
                        EXTRACTION_STATUS_PARTIAL,
                        warnings,
                    )
            except ImportError:
                # pypdf not installed — trust the heuristic
                warnings.append(
                    f"PDF appears encrypted (heuristic): {exc.__class__.__name__}"
                )
                return (
                    f"[PDF appears encrypted; pdfplumber refused: {exc}]\n",
                    EXTRACTION_STATUS_PARTIAL,
                    warnings,
                )
            except Exception:
                pass
        warnings.append(f"pdfplumber failed: {exc}")
        # Try Docling as last-ditch even without math signal
        try:
            text, status, more_warnings = _extract_via_docling(
                raw, docling_cache_dir=docling_cache_dir
            )
            warnings.extend(more_warnings)
            if status == EXTRACTION_STATUS_RICH:
                return text, status, warnings
        except Exception:
            pass
        return (
            f"[PDF extraction failed: {exc}]\n",
            EXTRACTION_STATUS_FAILED,
            warnings,
        )

    # Check for degraded (image-PDF) before equation detection — saves a
    # Docling call when there's just no text to extract.
    if num_pages > 0 and len(text) / num_pages < _DEGRADED_CHARS_PER_PAGE_THRESHOLD:
        warnings.append(
            f"low text yield: {len(text)} chars across {num_pages} pages "
            f"(< {_DEGRADED_CHARS_PER_PAGE_THRESHOLD}/page — likely image-PDF)"
        )
        # Still attempt Docling — it has OCR capability for image-PDFs.
        try:
            docling_text, docling_status, docling_warnings = _extract_via_docling(
                raw, docling_cache_dir=docling_cache_dir
            )
            warnings.extend(docling_warnings)
            if docling_status == EXTRACTION_STATUS_RICH and len(docling_text) > len(text):
                return docling_text, docling_status, warnings
        except Exception as exc:
            warnings.append(f"Docling fallback also failed: {exc}")
        return text or "[PDF text extraction yielded near-empty result]\n", EXTRACTION_STATUS_DEGRADED, warnings

    # Stage 2: equation richness check → Docling escalation
    is_math_rich, reason = _detect_equation_richness(text)
    if not is_math_rich:
        return text, EXTRACTION_STATUS_OK, warnings

    # Math detected — escalate to Docling
    try:
        docling_text, docling_status, docling_warnings = _extract_via_docling(
            raw, docling_cache_dir=docling_cache_dir
        )
        warnings.extend(docling_warnings)
        if docling_status == EXTRACTION_STATUS_RICH:
            return docling_text, EXTRACTION_STATUS_RICH, warnings
        # Docling itself reported a non-rich status — fall through
    except ImportError:
        warnings.append(
            f"equations detected ({reason}) but docling not installed; "
            f"text-only output may lose equation fidelity. "
            f"Install with: pip install docling"
        )
    except Exception as exc:
        warnings.append(
            f"equations detected ({reason}); Docling escalation failed: {exc}; "
            f"falling back to pdfplumber output (equation fidelity lost)"
        )

    return text, EXTRACTION_STATUS_OK_TEXT_ONLY, warnings


def _extract_via_docling(raw: bytes, *, docling_cache_dir: str | None = None) -> tuple[str, str, list[str]]:
    """Stage 2 of the v2.3 PDF cascade — lazy import + run Docling.

    Returns ``(text, extraction_status, warnings)``. Raises ``ImportError`` if
    Docling itself isn't installed (caller handles the warn-and-degrade path).
    Other exceptions propagate so the caller can decide whether to fall back.
    """
    # Honor DOCLING_CACHE_DIR (cross-machine cache sync support).
    if docling_cache_dir:
        os.environ.setdefault("HF_HOME", str(Path(docling_cache_dir).expanduser()))

    from docling.document_converter import DocumentConverter
    from io import BytesIO

    warnings: list[str] = []
    converter = DocumentConverter()
    # Docling's API accepts a path or stream; some versions need a tmp file.
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(raw)
        tmp_path = tmp.name
    try:
        result = converter.convert(tmp_path)
        text = result.document.export_to_markdown()
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
    return text, EXTRACTION_STATUS_RICH, warnings


def _safe_text(
    data: bytes,
    content_type: str,
    *,
    extract_pdfs: bool = True,
    docling_cache_dir: str | None = None,
) -> tuple[str, str, list[str]]:
    """Dispatch text extraction by content_type.

    v2.3: returns ``(text, extraction_status, warnings)`` (was ``(text, status)``
    pre-v2.3). PDFs go through the cascade in ``_extract_pdf_text`` when
    ``extract_pdfs`` is True; otherwise PDFs land at ``raw_only`` for
    byte-stable backward compat.
    """
    if content_type.startswith("text/") or "json" in content_type or "html" in content_type:
        return data.decode("utf-8", errors="replace"), EXTRACTION_STATUS_OK, []
    if content_type == "application/pdf" or content_type.endswith("/pdf"):
        if not extract_pdfs:
            return (
                "[PDF cached; extraction skipped (--no-extract-pdfs)]\n",
                EXTRACTION_STATUS_RAW_ONLY,
                [],
            )
        return _extract_pdf_text(data, docling_cache_dir=docling_cache_dir)
    return (
        f"[raw binary cached; no dependency-free extractor available for {content_type}]\n",
        EXTRACTION_STATUS_RAW_ONLY,
        [],
    )


def _append_extraction_log(
    log_path: Path,
    *,
    cache_id: str,
    source_url: str,
    status: str,
    warnings: list[str],
    run_id: str,
) -> None:
    """v2.3: per-host extraction log. One JSON line per call. Per-host filename
    avoids Dropbox/Drive conflicted-copy issues when cache_root is on a synced
    dir (closes #14-style cross-machine concerns)."""
    record = {
        "cache_id": cache_id,
        "source_url": source_url,
        "status": status,
        "warnings": warnings,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "run_id": run_id,
        "hostname": socket.gethostname(),
    }
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


def _default_extraction_log_path(cache_root: Path) -> Path:
    """Per-host log file at <cache_root>/extraction_log_<hostname>.jsonl."""
    safe_hostname = re.sub(r"[^a-zA-Z0-9_-]", "_", socket.gethostname())
    return cache_root / f"extraction_log_{safe_hostname}.jsonl"


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
    headers = {"User-Agent": "research_toolkit/2.5.0 strict-live cache"}
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


class PlaywrightUnavailable(RuntimeError):
    """Playwright escalation was requested but the package isn't installed.

    Callers catch this to degrade gracefully (urllib stub / re-raised HTTP
    error) instead of failing hard, preserving the "usable without
    Playwright" contract even when escalation is default-on. Genuine
    Playwright *runtime* failures (browser launch, navigation timeout) are
    NOT this type and still propagate as errors.
    """


def _fetch_via_playwright(source_url: str) -> tuple[int, bytes, str, str | None, str | None]:
    """Render with headless Chromium. Lazy-imports playwright so the script
    stays usable without Playwright installed.

    Returns the same tuple shape as ``_fetch``: (status, body_bytes,
    content_type, etag, last_modified). etag/last_modified are None
    because Playwright doesn't expose the conditional-GET headers from
    the response cleanly via its high-level API.

    Raises ``PlaywrightUnavailable`` when the package is not installed so
    callers can degrade gracefully.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise PlaywrightUnavailable(
            "Playwright escalation requested but the 'playwright' package is "
            "not installed. Run: pip install -e \".[dev]\" && playwright install chromium"
        ) from exc

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context(
                user_agent="research_toolkit/2.5.0 strict-live cache (Playwright)"
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
    extract_pdfs: bool = True,
    docling_cache_dir: str | None = None,
    extraction_log_path: Path | None = None,
    run_id: str | None = None,
) -> dict:
    """Cache a URL. Supports 304-first conditional GET when prior etag /
    last-modified are provided. v2.2.1 adds optional Playwright escalation.
    v2.3 adds PDF cascade extraction (#11) and unconditional JS-shell stub
    detection (#10).

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
    - If Playwright is not installed, escalation degrades gracefully (the
      403/429 case re-raises the original HTTP error; the suspect-content
      case falls back to a ``stub`` record) with a stderr WARN — so callers
      may pass this flag by default without requiring Playwright.

    v2.3:
    - JS-shell suspect detection now runs even without `escalate_on_failure`;
      a suspect HTML page lands at `extraction_status: stub` with a stderr
      WARN so downstream stages can skip it (closes #10).
    - PDFs get the equation-aware cascade in `_extract_pdf_text` when
      `extract_pdfs=True` (default). `--no-extract-pdfs` preserves the
      pre-v2.3 `raw_only` behavior for byte-stable fixtures (closes #11).
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
            try:
                status, raw, content_type, etag, last_modified = _fetch_via_playwright(source_url)
                fetch_method = PLAYWRIGHT_FETCH_METHOD
            except PlaywrightUnavailable as pw_exc:
                # Default-on escalation must not break installs without
                # Playwright: degrade to the non-escalated behavior.
                print(
                    f"WARN: {source_url} HTTP {exc.code}; Playwright escalation "
                    f"unavailable ({pw_exc}); degrading to non-escalated behavior",
                    file=sys.stderr,
                )
                raise exc
        else:
            raise

    # v2.3 #10: suspect detection ALWAYS runs on urllib results (not just when
    # escalation is requested). If suspect AND escalation enabled → Playwright.
    # If suspect AND no escalation → flagged as `stub` in the manifest with a
    # stderr WARN so the caller knows the cache is degraded.
    stub_reason: str | None = None
    if fetch_method == URLLIB_FETCH_METHOD and status not in (304,):
        is_suspect, reason = _content_is_suspect(raw, content_type)
        if is_suspect:
            if escalate_on_failure:
                escalation_reason = reason
                try:
                    status, raw, content_type, etag, last_modified = _fetch_via_playwright(source_url)
                    fetch_method = PLAYWRIGHT_FETCH_METHOD
                except PlaywrightUnavailable as pw_exc:
                    # Degrade to the same stub outcome as no-escalation.
                    print(
                        f"WARN: {source_url} suspect content ({reason}); Playwright "
                        f"escalation unavailable ({pw_exc}); degrading to stub",
                        file=sys.stderr,
                    )
                    stub_reason = reason
            else:
                stub_reason = reason

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

    text, extraction_status, extraction_warnings = _safe_text(
        raw,
        content_type,
        extract_pdfs=extract_pdfs,
        docling_cache_dir=docling_cache_dir,
    )
    # v2.3 #10: if the urllib first pass hit a JS-shell stub and escalation
    # wasn't enabled, override the status (text extraction itself succeeded —
    # we just want downstream stages to know the content is degraded).
    if stub_reason and extraction_status == EXTRACTION_STATUS_OK:
        extraction_status = EXTRACTION_STATUS_STUB
        extraction_warnings = list(extraction_warnings) + [
            f"JS-shell stub detected (no Playwright escalation): {stub_reason}"
        ]

    cache_id_value = f"cache_{digest[:16]}"

    # v2.3 loud-failure surface #1: per-PDF / per-stub WARN to stderr.
    if extraction_status in LOUD_EXTRACTION_STATUSES:
        warn_msg = (
            f"WARN: {source_url} extraction degraded "
            f"({extraction_status})"
        )
        if extraction_warnings:
            warn_msg += f" — {extraction_warnings[0]}"
        print(warn_msg, file=sys.stderr)

    # v2.3 loud-failure surface #2: persistent extraction log (per-host).
    if extraction_log_path is not None:
        try:
            _append_extraction_log(
                extraction_log_path,
                cache_id=cache_id_value,
                source_url=source_url,
                status=extraction_status,
                warnings=list(extraction_warnings),
                run_id=run_id or "",
            )
        except OSError as exc:
            print(f"WARN: failed to append extraction_log: {exc}", file=sys.stderr)

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
    if extraction_warnings:
        metadata["extraction_warnings"] = list(extraction_warnings)

    cache_root.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(cache_root, 0o700)
    except OSError:
        pass
    _private_write(raw_path, raw)
    _private_write(text_path, text)
    _private_write(metadata_path, json.dumps(metadata, indent=2, sort_keys=True) + "\n")

    entry = {
        "cache_id": cache_id_value,
        "source_url": source_url,
        "fetched_at": fetched_at,
        "record_type": "capture",
        "content_type": content_type or mimetypes.guess_type(source_url)[0] or "application/octet-stream",
        "bytes": len(raw),
        "sha256": digest,
        "raw_path": str(raw_path.relative_to(cache_root)),
        "text_path": str(text_path.relative_to(cache_root)),
        "metadata_path": str(metadata_path.relative_to(cache_root)),
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
    if extraction_warnings:
        entry["extraction_warnings"] = list(extraction_warnings)
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
            "extraction_warnings",
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
        if key == "extraction_warnings" and isinstance(value, list):
            print(f"  {key}:")
            for item in value:
                print(f"    - {item}")
            continue
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
    parser.add_argument(
        "--no-extract-pdfs",
        action="store_true",
        help="v2.3: skip PDF text extraction (PDFs land at extraction_status: "
        "raw_only). Default behavior extracts via pdfplumber + Docling cascade.",
    )
    parser.add_argument(
        "--strict-extraction",
        action="store_true",
        help="v2.3: exit non-zero on any extraction_status that triggers a WARN "
        "(ok_text_only / degraded / partial / failed / stub). For debugging.",
    )
    parser.add_argument(
        "--extraction-log",
        default=None,
        help="v2.3: path to append-only JSONL log of extraction outcomes. "
        "Default: <cache_root>/extraction_log_<hostname>.jsonl (per-host filename "
        "avoids Dropbox/Drive conflicts on synced cache_root).",
    )
    parser.add_argument(
        "--docling-cache-dir",
        default=os.environ.get("DOCLING_CACHE_DIR"),
        help="v2.3: where Docling caches its models (~600 MB on first PDF). "
        "Honors $DOCLING_CACHE_DIR env var. For cross-machine cache sync, point "
        "both machines at the same Dropbox/Drive dir.",
    )
    args = parser.parse_args(argv[1:])

    root = Path(args.cache_root).expanduser().resolve()
    extraction_log_path = (
        Path(args.extraction_log).expanduser().resolve()
        if args.extraction_log
        else _default_extraction_log_path(root)
    )
    run_id = uuid.uuid4().hex[:12]
    extract_pdfs = not args.no_extract_pdfs
    failures = 0
    strict_violations = 0
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
                extract_pdfs=extract_pdfs,
                docling_cache_dir=args.docling_cache_dir,
                extraction_log_path=extraction_log_path,
                run_id=run_id,
            )
        except (URLError, TimeoutError, OSError) as exc:
            failures += 1
            print(f"ERROR caching {source_url}: {exc}", file=sys.stderr)
            continue
        _print_yaml_entry(entry)
        if args.strict_extraction and entry.get("extraction_status") in STRICT_FAIL_STATUSES:
            strict_violations += 1
    return 1 if (failures or strict_violations) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

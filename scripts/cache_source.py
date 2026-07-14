#!/usr/bin/env python3
"""Cache public source artifacts into the strict-live global content cache.

The network path is dependency-light (urllib). Browser execution is
intentionally disabled: request interception is not an egress firewall, and an
untrusted page must not execute until a verified OS and network sandbox exists.

Stores raw bytes, a best-effort text derivative, and metadata JSON under
a content-addressed cache root. Prints manifest-ready YAML entries; a
gather/freshness skill is responsible for appending them deliberately.

All network reads pass through the public-only retrieval boundary: DNS-pinned
HTTP(S), redirect revalidation, fixed time/size limits, no ambient proxy, and
GET/HEAD only. Rights default to unknown and are recorded separately from
access. PDF parsing is opt-in because parser work needs a stronger resource
sandbox than byte retrieval.
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
import stat
import sys
import time
from typing import Any
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request

import yaml

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators._common import ARXIV_ID_RE, ARXIV_OLD_ID_RE, DOI_RE
from research_toolkit.retrieval_security import (
    DEFAULT_MAX_RESPONSE_BYTES,
    DEFAULT_TIMEOUT_SECONDS,
    read_response_limited,
    record_safe_url,
    redact_exception,
    redact_url,
    secure_urlopen as urlopen,
    validate_retrieval_url,
)


# Detection heuristics for when urllib's result is an unusable JS shell. Tuned
# conservatively: a 500-char minimum catches blank
# SPAs and "Please enable JavaScript" placeholders without false-positiving
# legitimate short pages (most useful sources are >1k chars after
# extraction).
SUSPECT_TEXT_MIN_CHARS = 500
SUSPECT_JS_MARKERS = (
    "Please enable JavaScript",
    "Please enable Javascript",
    "JavaScript is required",
    "<noscript>",
    'id="__next"></div>',  # next.js empty mount
    'id="root"></div>',  # CRA empty mount
)
URLLIB_FETCH_METHOD = "urllib"
USER_AGENT = "research_toolkit/3.0 strict-live cache"
ALLOWED_CACHE_RIGHTS_STATUS = {
    "public",
    "private_use",
    "restricted",
    "unknown",
    "cache_only",
}
ALLOWED_VISIBILITY = {"public", "authenticated", "private"}

# v2.3 PDF extraction (closes #11). The opt-in ``pdf`` extra supplies
# pdfplumber for fast text; ``rich-pdf`` also supplies lazy-loaded Docling for
# equation/OCR-sensitive work. The small core install still caches PDF bytes
# and reports ``raw_only`` rather than silently installing an ML stack.
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


def _extract_pdf_text(
    raw: bytes, *, docling_cache_dir: str | None = None
) -> tuple[str, str, list[str]]:
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

    # Stage 1: pdfplumber (fast path when the pdf/rich-pdf extra is installed).
    try:
        import pdfplumber
        from io import BytesIO
    except ImportError:
        warnings.append(
            'pdfplumber not installed (pip install -e ".[pdf]") — falling back to raw_only'
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

                reader = PdfReader(BytesIO(raw))
                if reader.is_encrypted:
                    warnings.append(
                        f"PDF encrypted; pdfplumber refused extraction: {exc.__class__.__name__}"
                    )
                    return (
                        "[PDF encrypted; install password OR use a non-encrypted source]\n",
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
            if docling_status == EXTRACTION_STATUS_RICH and len(docling_text) > len(
                text
            ):
                return docling_text, docling_status, warnings
        except Exception as exc:
            warnings.append(f"Docling fallback also failed: {exc}")
        return (
            text or "[PDF text extraction yielded near-empty result]\n",
            EXTRACTION_STATUS_DEGRADED,
            warnings,
        )

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
            'Install with: pip install -e ".[rich-pdf]"'
        )
    except Exception as exc:
        warnings.append(
            f"equations detected ({reason}); Docling escalation failed: {exc}; "
            f"falling back to pdfplumber output (equation fidelity lost)"
        )

    return text, EXTRACTION_STATUS_OK_TEXT_ONLY, warnings


def _extract_via_docling(
    raw: bytes, *, docling_cache_dir: str | None = None
) -> tuple[str, str, list[str]]:
    """Stage 2 of the v2.3 PDF cascade — lazy import + run Docling.

    Returns ``(text, extraction_status, warnings)``. Raises ``ImportError`` if
    Docling itself isn't installed (caller handles the warn-and-degrade path).
    Other exceptions propagate so the caller can decide whether to fall back.
    """
    # Honor DOCLING_CACHE_DIR (cross-machine cache sync support).
    if docling_cache_dir:
        os.environ.setdefault("HF_HOME", str(Path(docling_cache_dir).expanduser()))

    from docling.document_converter import DocumentConverter

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
    extract_pdfs: bool = False,
    docling_cache_dir: str | None = None,
) -> tuple[str, str, list[str]]:
    """Dispatch text extraction by content_type.

    v2.3: returns ``(text, extraction_status, warnings)`` (was ``(text, status)``
    pre-v2.3). PDFs go through the cascade in ``_extract_pdf_text`` when
    ``extract_pdfs`` is True; otherwise PDFs land at ``raw_only`` for
    byte-stable backward compat.
    """
    if (
        content_type.startswith("text/")
        or "json" in content_type
        or "html" in content_type
    ):
        return data.decode("utf-8", errors="replace"), EXTRACTION_STATUS_OK, []
    if content_type == "application/pdf" or content_type.endswith("/pdf"):
        if not extract_pdfs:
            return (
                "[PDF cached; extraction disabled by default; use --extract-pdfs only for trusted inputs]\n",
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
    fd = _open_private_fd(log_path, os.O_WRONLY | os.O_APPEND)
    with os.fdopen(fd, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _default_extraction_log_path(cache_root: Path) -> Path:
    """Per-host log file at <cache_root>/extraction_log_<hostname>.jsonl."""
    safe_hostname = re.sub(r"[^a-zA-Z0-9_-]", "_", socket.gethostname())
    return cache_root / f"extraction_log_{safe_hostname}.jsonl"


def _fetch(
    source_url: str,
    *,
    if_etag: str | None = None,
    if_last_modified: str | None = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    max_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
) -> tuple[int, bytes, str, str | None, str | None, str]:
    """Fetch a public URL with conditional headers and hard safety bounds.

    Returns (status_code, body_bytes, content_type, etag, last_modified,
    final_url).
    On a 304 Not Modified response, body_bytes is empty. ``timeout`` (seconds)
    bounds the request; the publication-date lookups pass a shorter value so a
    slow API can't stall caching. DNS is validated and pinned by ``urlopen``;
    every redirect is revalidated, ambient proxies are disabled, and the body
    is read incrementally under ``max_bytes``.
    """
    headers = {"User-Agent": USER_AGENT, "Accept-Encoding": "identity"}
    if if_etag:
        headers["If-None-Match"] = if_etag
    if if_last_modified:
        headers["If-Modified-Since"] = if_last_modified
    req = Request(source_url, headers=headers)
    deadline = time.monotonic() + timeout
    try:
        with urlopen(req, timeout=timeout) as response:
            status = (
                response.status if hasattr(response, "status") else response.getcode()
            )
            content_type = (
                response.headers.get_content_type() or "application/octet-stream"
            )
            etag = response.headers.get("ETag")
            last_modified = response.headers.get("Last-Modified")
            body = read_response_limited(
                response, max_bytes=max_bytes, deadline=deadline
            )
            final_url = (
                response.geturl() if hasattr(response, "geturl") else source_url
            )
            return status, body, content_type, etag, last_modified, final_url
    except HTTPError as exc:
        if exc.code == 304:
            return (
                304,
                b"",
                exc.headers.get_content_type() or "",
                exc.headers.get("ETag"),
                exc.headers.get("Last-Modified"),
                exc.geturl() if hasattr(exc, "geturl") else source_url,
            )
        raise


def _unpack_fetch_result(
    result: tuple[Any, ...], requested_url: str
) -> tuple[int, bytes, str, str | None, str | None, str]:
    """Accept legacy five-field test adapters while preserving final URLs."""
    if len(result) == 5:
        status, body, content_type, etag, last_modified = result
        return status, body, content_type, etag, last_modified, requested_url
    if len(result) == 6:
        status, body, content_type, etag, last_modified, final_url = result
        return status, body, content_type, etag, last_modified, final_url
    raise ValueError(f"fetch adapter returned {len(result)} fields; expected 5 or 6")


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
            return (
                True,
                f"extracted text only {len(text)} chars (< {SUSPECT_TEXT_MIN_CHARS} threshold)",
            )
        for marker in SUSPECT_JS_MARKERS:
            if marker in text:
                return True, f"contains JS-required marker {marker!r}"
    return False, ""


# v2.6 source provenance: best-effort publication-date capture + arXiv stub
# recovery. The arXiv/DOI id-extraction regexes (ARXIV_ID_RE, ARXIV_OLD_ID_RE,
# DOI_RE) are imported from validators._common so every cache/dossier script
# stays in lockstep. Every network lookup here is timeout-bounded and
# failure-tolerant — a date lookup that errors or times out must NEVER break
# caching (the field is optional).
PUBDATE_TIMEOUT = 20
ARXIV_ABS_FALLBACK_REASON = "arxiv_abs_fallback"

# arXiv Atom API <published> element, e.g. 2019-08-08T17:08:30Z → date part.
_ARXIV_PUBLISHED_RE = re.compile(r"<published>\s*(\d{4}-\d{2}-\d{2})T", re.I)
# A clean YYYY-MM-DD prefix in a longer datetime string (ISO dash or slash).
_ISO_DATE_PREFIX_RE = re.compile(r"^\s*(\d{4})[-/](\d{2})[-/](\d{2})")
# Generic HTML publication-date <meta> tags (content captured in either order).
_META_PUBDATE_RES = (
    re.compile(
        r"<meta[^>]+(?:property|name)\s*=\s*[\"']article:published_time[\"']"
        r"[^>]*?content\s*=\s*[\"']([^\"']+)[\"']",
        re.I,
    ),
    re.compile(
        r"<meta[^>]+content\s*=\s*[\"']([^\"']+)[\"']"
        r"[^>]*?(?:property|name)\s*=\s*[\"']article:published_time[\"']",
        re.I,
    ),
    re.compile(
        r"<meta[^>]+name\s*=\s*[\"']citation_publication_date[\"']"
        r"[^>]*?content\s*=\s*[\"']([^\"']+)[\"']",
        re.I,
    ),
    re.compile(
        r"<meta[^>]+content\s*=\s*[\"']([^\"']+)[\"']"
        r"[^>]*?name\s*=\s*[\"']citation_publication_date[\"']",
        re.I,
    ),
    re.compile(
        r"<meta[^>]+name\s*=\s*[\"']dc\.date(?:\.issued)?[\"']"
        r"[^>]*?content\s*=\s*[\"']([^\"']+)[\"']",
        re.I,
    ),
    re.compile(
        r"<meta[^>]+content\s*=\s*[\"']([^\"']+)[\"']"
        r"[^>]*?name\s*=\s*[\"']dc\.date(?:\.issued)?[\"']",
        re.I,
    ),
)


def _arxiv_id_from_url(url: str) -> str | None:
    """Return the bare arXiv id (version suffix stripped) from a URL, else None."""
    m = ARXIV_ID_RE.search(url) or ARXIV_OLD_ID_RE.search(url)
    if not m:
        return None
    return re.sub(r"v\d+$", "", m.group(1))


def _doi_from_url(url: str) -> str | None:
    """Return the DOI from a URL, else None (trailing punctuation trimmed)."""
    m = DOI_RE.search(url)
    if not m:
        return None
    return m.group(1).rstrip("/.,;")


def _iso_date_or_none(value: str | None) -> str | None:
    """Coerce a datetime-ish string to a calendar-valid ``YYYY-MM-DD`` or None.

    Accepts ISO (``2019-08-08T...``) and slash (``2019/08/08``) prefixes only;
    anything that is not a full year-month-day is rejected. The date is
    range-checked (a bogus ``2019-13-40`` is dropped) so the value always
    satisfies the cache_manifest / bib_ledger ISO-date validators.
    """
    if not value:
        return None
    m = _ISO_DATE_PREFIX_RE.match(value)
    if not m:
        return None
    year, month, day = m.group(1), m.group(2), m.group(3)
    try:
        datetime(int(year), int(month), int(day))
    except ValueError:
        return None
    return f"{year}-{month}-{day}"


def _arxiv_published_date(
    arxiv_id: str, *, fetch: Any = None, timeout: int = PUBDATE_TIMEOUT
) -> str | None:
    """Look up the v1 submission date for ``arxiv_id`` via the arXiv API.

    Queries ``export.arxiv.org/api/query?id_list=<id>`` and returns the date
    part of the Atom ``<published>`` element as ``YYYY-MM-DD``. ``fetch`` is an
    injectable ``_fetch``-shaped callable (for tests). Best-effort: any
    transport / decode / parse failure returns None.
    """
    fetcher = fetch or _fetch
    api = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    try:
        status, body, _ctype, _etag, _last, _final = _unpack_fetch_result(
            fetcher(api, timeout=timeout), api
        )
    except Exception:  # noqa: BLE001 — a date lookup must never break caching
        return None
    if status != 200 or not body:
        return None
    try:
        text = body.decode("utf-8", "replace")
    except Exception:  # noqa: BLE001
        return None
    m = _ARXIV_PUBLISHED_RE.search(text)
    if not m:
        return None
    return _iso_date_or_none(m.group(1))


def _crossref_published_date(
    doi: str, *, fetch: Any = None, timeout: int = PUBDATE_TIMEOUT
) -> str | None:
    """Look up the issued date for ``doi`` via the Crossref REST API.

    Reads ``message.issued.date-parts[0]`` and returns ``YYYY-MM-DD`` ONLY when
    year, month, AND day are all present; a year-only (or year+month) value is
    dropped because the validators require a full ISO date. ``fetch`` is an
    injectable ``_fetch``-shaped callable. Best-effort: any failure returns None.
    """
    fetcher = fetch or _fetch
    api = f"https://api.crossref.org/works/{doi}"
    try:
        status, body, _ctype, _etag, _last, _final = _unpack_fetch_result(
            fetcher(api, timeout=timeout), api
        )
    except Exception:  # noqa: BLE001
        return None
    if status != 200 or not body:
        return None
    try:
        data = json.loads(body.decode("utf-8", "replace"))
    except Exception:  # noqa: BLE001
        return None
    parts = data.get("message", {}).get("issued", {}).get("date-parts", [])
    if not isinstance(parts, list) or not parts:
        return None
    first = parts[0]
    if not isinstance(first, list) or len(first) < 3:
        return None  # year-only / year+month: omit (validators need full date)
    try:
        year, month, day = int(first[0]), int(first[1]), int(first[2])
    except (TypeError, ValueError):
        return None
    return _iso_date_or_none(f"{year:04d}-{month:02d}-{day:02d}")


def _meta_published_date(html: str) -> str | None:
    """Best-effort parse of a publication date from HTML ``<meta>`` tags.

    Recognises ``article:published_time``, ``citation_publication_date``, and
    ``dc.date`` / ``dc.date.issued`` variants. Returns a clean ``YYYY-MM-DD`` or
    None (a partial / unparseable date is dropped).
    """
    if not html:
        return None
    for pattern in _META_PUBDATE_RES:
        m = pattern.search(html)
        if m:
            iso = _iso_date_or_none(m.group(1))
            if iso:
                return iso
    return None


def _published_online_for(
    url: str, raw: bytes, content_type: str, *, fetch: Any = None
) -> str | None:
    """Resolve ``published_online`` for a fetched source, best-effort.

    Priority: arXiv API → Crossref (DOI) → HTML ``<meta>`` tags. Returns a clean
    ``YYYY-MM-DD`` or None. Never raises (each lookup is failure-tolerant) and
    never falls back to the server ``Last-Modified`` (that is the file mod time,
    not the publication date).
    """
    arxiv_id = _arxiv_id_from_url(url)
    if arxiv_id:
        date_str = _arxiv_published_date(arxiv_id, fetch=fetch)
        if date_str:
            return date_str
    doi = _doi_from_url(url)
    if doi:
        date_str = _crossref_published_date(doi, fetch=fetch)
        if date_str:
            return date_str
    ct = (content_type or "").lower()
    if ct.startswith("text/") or "html" in ct:
        try:
            return _meta_published_date(raw.decode("utf-8", "replace"))
        except Exception:  # noqa: BLE001
            return None
    return None


class PlaywrightUnavailable(ValueError):
    """Browser escalation is disabled until an audited sandbox exists."""


def _fetch_via_playwright(source_url: str) -> tuple[()]:
    """Fail closed; request interception alone cannot contain browser egress."""
    del source_url
    raise PlaywrightUnavailable(
        "browser escalation is disabled: Chromium requires a verified process, "
        "resource, and default-deny network sandbox before it may execute "
        "untrusted source content"
    )


def _ensure_private_directory(path: Path) -> None:
    """Create or tighten a cache directory, failing before sensitive writes."""
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path, 0o700)
    if path.stat().st_mode & 0o077:
        raise PermissionError(f"cache directory is not private: {path}")


def _open_private_fd(path: Path, flags: int) -> int:
    """Open a regular cache file as 0600 without following a final symlink."""
    _ensure_private_directory(path.parent)
    safe_flags = flags | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        safe_flags |= os.O_NOFOLLOW
    fd = os.open(path, safe_flags, 0o600)
    try:
        os.fchmod(fd, 0o600)
        mode = os.fstat(fd).st_mode
        if not stat.S_ISREG(mode):
            raise PermissionError(f"cache path is not a regular file: {path}")
        if mode & 0o077:
            raise PermissionError(f"cache file is not private: {path}")
    except BaseException:
        os.close(fd)
        raise
    return fd


def _private_write(path: Path, data: bytes | str) -> None:
    payload = data.encode("utf-8") if isinstance(data, str) else data
    fd = _open_private_fd(path, os.O_WRONLY | os.O_TRUNC)
    with os.fdopen(fd, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


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
    extract_pdfs: bool = False,
    docling_cache_dir: str | None = None,
    extraction_log_path: Path | None = None,
    run_id: str | None = None,
    rights_status: str = "unknown",
    visibility: str = "public",
    license_value: str | None = None,
) -> dict:
    """Cache a URL under fail-closed retrieval and persistence boundaries.

    - On HTTP 304 → emit a `revisit` record (server-not-modified) referring
      to prior_cache_id. Zero new bytes.
    - On HTTP 200 with hash matching prior_sha256 → emit a `revisit` record
      (identical-payload-digest) referring to prior_cache_id. Zero new bytes
      written (existing cache is untouched).
    - On HTTP 200 with new content → emit a fresh `capture` record with
      raw/text/metadata files written.

    ``escalate_on_failure=True`` fails closed. Browser rendering remains
    disabled until Chromium is contained by an audited process/resource
    sandbox and a default-deny network boundary.

    v2.3:
    - JS-shell suspect detection now runs even without `escalate_on_failure`;
      a suspect HTML page lands at `extraction_status: stub` with a stderr
      WARN so downstream stages can skip it (closes #10).
    - PDFs are raw-only by default. The equation-aware cascade runs only when
      `extract_pdfs=True` is explicitly selected for trusted inputs.

    v2.6 (source provenance):
    - Best-effort ``published_online`` (the date content first appeared online,
      ``YYYY-MM-DD``) is resolved from the arXiv API / Crossref / HTML meta tags
      and written to both the metadata JSON and the returned entry; omitted when
      unavailable. Never the server Last-Modified.
    - arXiv stub recovery: when content is suspect (stub) AND the URL has an
      arXiv id, the plain-HTML abs page is auto-fetched as a fallback EVEN
      WITHOUT ``escalate_on_failure`` (urllib handles it). The record then
      carries ``escalation_reason: arxiv_abs_fallback``.
    """
    validate_retrieval_url(source_url)
    if rights_status not in ALLOWED_CACHE_RIGHTS_STATUS:
        raise ValueError(
            f"rights_status must be one of {sorted(ALLOWED_CACHE_RIGHTS_STATUS)}"
        )
    if visibility not in ALLOWED_VISIBILITY:
        raise ValueError(f"visibility must be one of {sorted(ALLOWED_VISIBILITY)}")
    if license_value is not None and not license_value.strip():
        raise ValueError("license_value must be non-empty when provided")
    if escalate_on_failure:
        raise PlaywrightUnavailable(
            "browser escalation is disabled: Chromium requires a verified process, "
            "resource, and default-deny network sandbox before it may execute "
            "untrusted source content"
        )

    recorded_url = record_safe_url(source_url)
    restricted = visibility != "public" or rights_status != "public"
    fetch_method = URLLIB_FETCH_METHOD
    escalation_reason: str | None = None
    status, raw, content_type, etag, last_modified, effective_url = (
        _unpack_fetch_result(
            _fetch(source_url, if_etag=if_etag, if_last_modified=if_last_modified),
            source_url,
        )
    )
    validate_retrieval_url(effective_url)
    recorded_final_url = record_safe_url(effective_url)
    final_url_observed = effective_url != source_url

    # v2.3 #10: suspect detection ALWAYS runs on urllib results (not just when
    # escalation is requested). Suspect content is flagged as `stub` in the
    # manifest; executing it in a browser is not an allowed recovery path.
    #
    # v2.6: ``effective_url`` is the URL the recorded content actually came from
    # (may shift to the arXiv abs page on fallback below); it drives the
    # publication-date lookup. Default is the redirect-resolved final URL.
    stub_reason: str | None = None
    if fetch_method == URLLIB_FETCH_METHOD and status not in (304,):
        is_suspect, reason = _content_is_suspect(raw, content_type)
        if is_suspect:
            # v2.6: arXiv stub recovery. If the fetched content is a stub and
            # the URL carries an arXiv id, fetch the plain-HTML abs page (urllib
            # handles it — no Playwright needed) EVEN WITHOUT escalate_on_failure.
            # This directly fixes caching an HTML/JS stub when the arXiv abs page
            # was available. Tried before Playwright so it wins for arXiv URLs.
            arxiv_id = _arxiv_id_from_url(source_url)
            if arxiv_id:
                abs_url = f"https://arxiv.org/abs/{arxiv_id}"
                if abs_url != source_url:
                    try:
                        (
                            a_status,
                            a_raw,
                            a_ct,
                            a_etag,
                            a_last,
                            a_final,
                        ) = _unpack_fetch_result(_fetch(abs_url), abs_url)
                    except (HTTPError, URLError, OSError):
                        a_status, a_raw, a_ct, a_etag, a_last, a_final = (
                            0,
                            b"",
                            "",
                            None,
                            None,
                            abs_url,
                        )
                    if a_status == 200 and a_raw:
                        a_suspect, _a_reason = _content_is_suspect(a_raw, a_ct)
                        if not a_suspect:
                            status, raw, content_type = (
                                a_status,
                                a_raw,
                                a_ct or "text/html",
                            )
                            etag, last_modified = a_etag, a_last
                            effective_url = a_final
                            validate_retrieval_url(a_final)
                            recorded_final_url = record_safe_url(a_final)
                            final_url_observed = a_final != source_url
                            escalation_reason = ARXIV_ABS_FALLBACK_REASON
                            is_suspect = False
            if is_suspect:
                stub_reason = reason

    # 304 Not Modified → revisit record (server-not-modified)
    if status == 304 and prior_cache_id:
        return {
            "cache_id": f"cache_{prior_cache_id.removeprefix('cache_')}_r{fetched_at.replace('-', '')}",
            "source_url": recorded_url,
            "fetched_at": fetched_at,
            "record_type": "revisit",
            "revisit_profile": "server-not-modified",
            "refers_to_cache_id": prior_cache_id,
            "refers_to_fetched_at": None,  # caller can fill in if known
            "http_status": 304,
            "http_etag": etag,
            "http_last_modified": last_modified,
            "restricted": restricted,
            "rights_status": rights_status,
            "visibility": visibility,
            **({"license": license_value} if license_value else {}),
            **(
                {"final_url": recorded_final_url}
                if final_url_observed
                else {}
            ),
        }

    digest = _sha256(raw)

    # 200 OK but identical to prior → revisit (identical-payload-digest)
    if prior_cache_id and prior_sha256 and digest == prior_sha256:
        return {
            "cache_id": f"cache_{prior_cache_id.removeprefix('cache_')}_r{fetched_at.replace('-', '')}",
            "source_url": recorded_url,
            "fetched_at": fetched_at,
            "record_type": "revisit",
            "revisit_profile": "identical-payload-digest",
            "refers_to_cache_id": prior_cache_id,
            "refers_to_fetched_at": None,
            "http_status": 200,
            "http_etag": etag,
            "http_last_modified": last_modified,
            "restricted": restricted,
            "rights_status": rights_status,
            "visibility": visibility,
            **({"license": license_value} if license_value else {}),
            **(
                {"final_url": recorded_final_url}
                if final_url_observed
                else {}
            ),
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
    # If the HTTP response is a JS shell, override the status: text extraction
    # succeeded mechanically, but browser execution is not an allowed recovery.
    if stub_reason and extraction_status == EXTRACTION_STATUS_OK:
        extraction_status = EXTRACTION_STATUS_STUB
        extraction_warnings = list(extraction_warnings) + [
            f"JS-shell stub detected (browser execution disabled): {stub_reason}"
        ]

    cache_id_value = f"cache_{digest[:16]}"

    # v2.6: best-effort original publication date (arXiv API / Crossref / HTML
    # meta). Resolved from effective_url so an arXiv abs fallback still looks up
    # the right id. Never the server Last-Modified (file mod time, not pub date).
    published_online = _published_online_for(effective_url, raw, content_type)

    # v2.3 loud-failure surface #1: per-PDF / per-stub WARN to stderr.
    if extraction_status in LOUD_EXTRACTION_STATUSES:
        warn_msg = f"WARN: {recorded_url} extraction degraded ({extraction_status})"
        if extraction_warnings:
            warn_msg += f" — {extraction_warnings[0]}"
        print(warn_msg, file=sys.stderr)

    # v2.3 loud-failure surface #2: persistent extraction log (per-host).
    if extraction_log_path is not None:
        _append_extraction_log(
            extraction_log_path,
            cache_id=cache_id_value,
            source_url=recorded_url,
            status=extraction_status,
            warnings=list(extraction_warnings),
            run_id=run_id or "",
        )

    metadata = {
        "schema_version": 2,
        "topic": topic,
        "source_url": recorded_url,
        **(
            {"final_url": recorded_final_url}
            if final_url_observed
            else {}
        ),
        "fetched_at": fetched_at,
        "content_type": content_type,
        "bytes": len(raw),
        "sha256": digest,
        "cache_policy": "max_local_private",
        "restricted": restricted,
        "rights_status": rights_status,
        "visibility": visibility,
        "extraction_status": extraction_status,
        "fetch_method": fetch_method,
        "http_etag": etag,
        "http_last_modified": last_modified,
    }
    if published_online:
        metadata["published_online"] = published_online
    if license_value:
        metadata["license"] = license_value
    if escalation_reason:
        metadata["escalation_reason"] = escalation_reason
    if extraction_warnings:
        metadata["extraction_warnings"] = list(extraction_warnings)

    _ensure_private_directory(cache_root)
    _private_write(raw_path, raw)
    _private_write(text_path, text)
    _private_write(metadata_path, json.dumps(metadata, indent=2, sort_keys=True) + "\n")

    entry = {
        "cache_id": cache_id_value,
        "source_url": recorded_url,
        **(
            {"final_url": recorded_final_url}
            if final_url_observed
            else {}
        ),
        "fetched_at": fetched_at,
        "record_type": "capture",
        "content_type": content_type
        or mimetypes.guess_type(source_url)[0]
        or "application/octet-stream",
        "bytes": len(raw),
        "sha256": digest,
        "raw_path": str(raw_path.relative_to(cache_root)),
        "text_path": str(text_path.relative_to(cache_root)),
        "metadata_path": str(metadata_path.relative_to(cache_root)),
        "restricted": restricted,
        "rights_status": rights_status,
        "visibility": visibility,
        "extraction_status": extraction_status,
    }
    if license_value:
        entry["license"] = license_value
    # Only emit fetch_method when it deviates from the urllib default — keeps
    # existing fixtures byte-stable.
    if fetch_method != URLLIB_FETCH_METHOD:
        entry["fetch_method"] = fetch_method
    # v2.6: surface why content was replaced (e.g. arxiv_abs_fallback) so audits
    # can see the recorded content is not the originally-requested URL's body.
    if escalation_reason:
        entry["escalation_reason"] = escalation_reason
    # v2.6: best-effort original publication date (omitted when unavailable).
    if published_online:
        entry["published_online"] = published_online
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
    """Emit one manifest-ready entry through a real YAML serializer."""
    print(
        yaml.safe_dump(
            [entry], sort_keys=False, allow_unicode=True, default_flow_style=False
        ).rstrip()
    )


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
        help="disabled: browser execution requires a verified process/resource "
        "sandbox and default-deny network boundary",
    )
    pdf_group = parser.add_mutually_exclusive_group()
    pdf_group.add_argument(
        "--extract-pdfs",
        action="store_true",
        default=False,
        help="opt in to local PDF parsing for trusted inputs; raw-only caching is "
        "the default because parser resource isolation is not yet guaranteed",
    )
    pdf_group.add_argument(
        "--no-extract-pdfs",
        dest="extract_pdfs",
        action="store_false",
        help=argparse.SUPPRESS,
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
    parser.add_argument(
        "--rights-status",
        choices=sorted(ALLOWED_CACHE_RIGHTS_STATUS),
        default="unknown",
        help="Redistribution/use rights determination. Defaults to unknown; a public "
        "URL never implies public redistribution rights.",
    )
    parser.add_argument(
        "--visibility",
        choices=sorted(ALLOWED_VISIBILITY),
        default="public",
        help="Access visibility of the retrieved source, independent of rights.",
    )
    parser.add_argument(
        "--license",
        dest="license_value",
        default=None,
        help="Optional observed license identifier or concise license note.",
    )
    args = parser.parse_args(argv[1:])

    root = Path(args.cache_root).expanduser().resolve()
    extraction_log_path = (
        Path(args.extraction_log).expanduser().resolve()
        if args.extraction_log
        else _default_extraction_log_path(root)
    )
    run_id = uuid.uuid4().hex[:12]
    extract_pdfs = args.extract_pdfs
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
                rights_status=args.rights_status,
                visibility=args.visibility,
                license_value=args.license_value,
            )
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            failures += 1
            print(
                f"ERROR caching {redact_url(source_url)}: "
                f"{redact_exception(exc, source_url)}",
                file=sys.stderr,
            )
            continue
        _print_yaml_entry(entry)
        if (
            args.strict_extraction
            and entry.get("extraction_status") in STRICT_FAIL_STATUSES
        ):
            strict_violations += 1
    return 1 if (failures or strict_violations) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

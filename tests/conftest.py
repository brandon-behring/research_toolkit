"""Shared pytest fixtures for the research_toolkit test suite.

v2.3+ adds PDF fixtures generated locally via reportlab + pypdf (no committed
PDFs, no licensing concerns, no network requirement). Tests that need a
realistic equation-rich PDF use the ``equation_rich_pdf`` fixture which seeds
the bytes with LaTeX residue + unicode math chars sufficient to trip
``_detect_equation_richness``. Tests that need Docling integration MOCK
``docling.document_converter.DocumentConverter`` to avoid the 600 MB model
download in CI.
"""
from __future__ import annotations

import io
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures"


@pytest.fixture(scope="session")
def mini_dir() -> Path:
    return FIXTURES / "mini_topic_timeseries_anomaly"


@pytest.fixture(scope="session")
def prompt_injection_dir() -> Path:
    return FIXTURES / "prompt_injection_snapshot" / "real"


# ---------- PDF fixtures (v2.3 / #11) ----------


def _build_plain_text_pdf() -> bytes:
    """1-page PDF with ~600 chars of plain text, no math markers."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    body = (
        "This is a synthetic plain-text test PDF for the research_toolkit "
        "v2.3 cascade. It contains no LaTeX residue, no unicode math chars, "
        "no Greek letters, and no equation markers of any kind. The PDF "
        "extraction cascade should land it at extraction_status: ok via "
        "pdfplumber on the first pass without invoking Docling. This text is "
        "padded to roughly six hundred characters to ensure the per-page "
        "char threshold is comfortably exceeded so the degraded heuristic "
        "does not trip on a synthetic fixture."
    )
    # Word-wrap the body across the page so it actually renders as text
    x, y = 72, 720
    for chunk in [body[i:i+70] for i in range(0, len(body), 70)]:
        c.drawString(x, y, chunk)
        y -= 14
    c.showPage()
    c.save()
    return buf.getvalue()


def _build_equation_rich_pdf() -> bytes:
    """1-page PDF with unicode math + LaTeX residue + Greek to trip
    ``_detect_equation_richness``."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    # Mix of unicode math (≤≥∑∫∂∈∀∃) and Greek (αβγδ) + LaTeX residue (\frac, \sum).
    # Density well above the 3.0/1000 threshold AND a LaTeX marker for the
    # near-zero-false-positive path.
    lines = [
        "Equation-rich synthetic PDF for v2.3 cascade testing.",
        "Equation 1: \\frac{\\partial L}{\\partial \\theta} = 0",
        "Constraints: \\alpha \\le \\beta, \\sum_i x_i \\in \\mathbb{R}",
        "More math: ∑ α + ∫ β ≤ γ; ∀x ∃y. ∂f/∂x ≈ ∇L",
        "Greek soup: α β γ δ ε ζ η θ λ μ ν ξ π σ τ φ χ ψ ω",
        "Operators: ⊕ ⊗ ≠ ≈ ≡ ∞ ± × ÷ ∝ √ Σ Π ⊂ ⊃",
        "LaTeX block: \\begin{equation} E = mc^2 \\end{equation}",
    ]
    y = 720
    for line in lines:
        c.drawString(72, y, line)
        y -= 18
    c.showPage()
    c.save()
    return buf.getvalue()


def _build_image_only_pdf() -> bytes:
    """1-page PDF with no extractable text (degraded test case).

    Reportlab can produce text-less pages by drawing only graphic primitives.
    pdfplumber's extract_text() returns empty/near-empty for these.
    """
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    # Just draw shapes — no drawString, no text objects
    c.rect(72, 72, 200, 200, fill=1)
    c.circle(400, 400, 50, fill=1)
    c.showPage()
    c.save()
    return buf.getvalue()


def _build_encrypted_pdf() -> bytes:
    """Plain-text PDF encrypted with an empty owner password.

    pdfplumber raises with 'encrypted' in the message → cascade marks
    extraction_status: partial.
    """
    from pypdf import PdfReader, PdfWriter

    base = _build_plain_text_pdf()
    reader = PdfReader(io.BytesIO(base))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(user_password="secret", owner_password="ownersecret")
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


@pytest.fixture(scope="session")
def plain_text_pdf_bytes() -> bytes:
    return _build_plain_text_pdf()


@pytest.fixture(scope="session")
def equation_rich_pdf_bytes() -> bytes:
    return _build_equation_rich_pdf()


@pytest.fixture(scope="session")
def image_only_pdf_bytes() -> bytes:
    return _build_image_only_pdf()


@pytest.fixture(scope="session")
def encrypted_pdf_bytes() -> bytes:
    return _build_encrypted_pdf()


@pytest.fixture
def test_cache_root(tmp_path) -> Path:
    """Per-test cache root for cache_source.py integration tests."""
    root = tmp_path / "research_cache"
    root.mkdir()
    return root


@pytest.fixture(autouse=True)
def _quiet_extraction_warnings(monkeypatch):
    """v2.3: extraction WARN noise on stderr makes pytest output unreadable.
    Set RESEARCH_TOOLKIT_QUIET_TESTS=1 to silence — tests that need to assert
    on stderr capture via ``capsys`` use it directly.
    """
    # No-op for now; placeholder so tests stay explicit about stderr capture.
    yield

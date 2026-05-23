"""Tests for scripts/reextract_pdfs.py (v2.3 — closes #11 for upgrade path)."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import cache_source, reextract_pdfs  # noqa: E402


def _scaffold_raw_only_pdf_cache(
    cache_root: Path, pdf_bytes: bytes, *, source_url: str = "https://example.com/p.pdf"
) -> dict:
    """Write a raw_only PDF cache entry to disk + return its manifest shape."""
    digest = hashlib.sha256(pdf_bytes).hexdigest()
    (cache_root / "blobs" / "sha256").mkdir(parents=True, exist_ok=True)
    (cache_root / "text" / "sha256").mkdir(parents=True, exist_ok=True)
    (cache_root / "metadata" / "sha256").mkdir(parents=True, exist_ok=True)
    (cache_root / "blobs" / "sha256" / digest).write_bytes(pdf_bytes)
    # The placeholder text the old v2.2 _safe_text() would have written
    (cache_root / "text" / "sha256" / f"{digest}.txt").write_text(
        "[raw binary cached; no dependency-free extractor available for application/pdf]\n",
        encoding="utf-8",
    )
    (cache_root / "metadata" / "sha256" / f"{digest}.json").write_text(
        json.dumps(
            {
                "sha256": digest,
                "extraction_status": "raw_only",
                "content_type": "application/pdf",
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return {
        "cache_id": f"cache_{digest[:16]}",
        "source_url": source_url,
        "fetched_at": "2026-05-19",
        "content_type": "application/pdf",
        "bytes": len(pdf_bytes),
        "sha256": digest,
        "raw_path": f"blobs/sha256/{digest}",
        "text_path": f"text/sha256/{digest}.txt",
        "metadata_path": f"metadata/sha256/{digest}.json",
        "restricted": False,
        "rights_status": "private_use",
        "extraction_status": "raw_only",
    }


def test_reextract_promotes_raw_only_pdf_to_ok(
    tmp_path: Path, plain_text_pdf_bytes: bytes
) -> None:
    """Plain-text PDF flips from raw_only → ok after re-extraction."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    entry = _scaffold_raw_only_pdf_cache(cache_dir, plain_text_pdf_bytes)

    manifest_path = tmp_path / "cache_manifest.yml"
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 2,
                "topic": "test_reextract",
                "generated_at": "2026-05-19",
                "current_as_of": "2026-05-19",
                "freshness_policy": "strict_live",
                "cache_root": str(cache_dir),
                "entries": [entry],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    rc = reextract_pdfs.reextract(manifest_path, dry_run=False)
    assert rc == 0

    rewritten = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert rewritten["entries"][0]["extraction_status"] == "ok"
    # text_path updated on disk
    text_file = cache_dir / "text" / "sha256" / f"{entry['sha256']}.txt"
    assert "synthetic plain-text test PDF" in text_file.read_text(encoding="utf-8")
    # metadata.json updated
    meta_file = cache_dir / "metadata" / "sha256" / f"{entry['sha256']}.json"
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    assert meta["extraction_status"] == "ok"


def test_reextract_is_idempotent(
    tmp_path: Path, plain_text_pdf_bytes: bytes
) -> None:
    """Already-extracted entries are skipped on re-run."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    entry = _scaffold_raw_only_pdf_cache(cache_dir, plain_text_pdf_bytes)
    entry["extraction_status"] = "ok"  # pretend it was already extracted

    manifest_path = tmp_path / "cache_manifest.yml"
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 2,
                "topic": "test_idempotency",
                "generated_at": "2026-05-19",
                "current_as_of": "2026-05-19",
                "freshness_policy": "strict_live",
                "cache_root": str(cache_dir),
                "entries": [entry],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    rc = reextract_pdfs.reextract(manifest_path, dry_run=False)
    assert rc == 0  # nothing to do


def test_reextract_dry_run_does_not_write(
    tmp_path: Path, plain_text_pdf_bytes: bytes
) -> None:
    """--dry-run reports candidates without writing."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    entry = _scaffold_raw_only_pdf_cache(cache_dir, plain_text_pdf_bytes)

    manifest_path = tmp_path / "cache_manifest.yml"
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 2,
                "topic": "test_dry_run",
                "generated_at": "2026-05-19",
                "current_as_of": "2026-05-19",
                "freshness_policy": "strict_live",
                "cache_root": str(cache_dir),
                "entries": [entry],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    before = manifest_path.read_text(encoding="utf-8")
    text_before = (cache_dir / "text" / "sha256" / f"{entry['sha256']}.txt").read_text(
        encoding="utf-8"
    )

    rc = reextract_pdfs.reextract(manifest_path, dry_run=True)
    assert rc == 1  # would-change exit code

    assert manifest_path.read_text(encoding="utf-8") == before
    assert (cache_dir / "text" / "sha256" / f"{entry['sha256']}.txt").read_text(
        encoding="utf-8"
    ) == text_before


def test_reextract_skips_non_pdf_entries(
    tmp_path: Path, plain_text_pdf_bytes: bytes
) -> None:
    """HTML raw_only entries (if any) are not touched."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    pdf_entry = _scaffold_raw_only_pdf_cache(cache_dir, plain_text_pdf_bytes)
    html_entry = dict(pdf_entry)
    html_entry["content_type"] = "text/html"
    html_entry["cache_id"] = "cache_html0000000000"

    manifest_path = tmp_path / "cache_manifest.yml"
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 2,
                "topic": "test_skip",
                "generated_at": "2026-05-19",
                "current_as_of": "2026-05-19",
                "freshness_policy": "strict_live",
                "cache_root": str(cache_dir),
                "entries": [pdf_entry, html_entry],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    rc = reextract_pdfs.reextract(manifest_path, dry_run=False)
    assert rc == 0

    rewritten = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    # PDF promoted
    assert rewritten["entries"][0]["extraction_status"] == "ok"
    # HTML still raw_only (skipped)
    assert rewritten["entries"][1]["extraction_status"] == "raw_only"


def test_reextract_strict_extraction_fails_on_degraded(
    tmp_path: Path, image_only_pdf_bytes: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    """--strict-extraction returns nonzero when a degraded entry surfaces."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    entry = _scaffold_raw_only_pdf_cache(cache_dir, image_only_pdf_bytes)

    manifest_path = tmp_path / "cache_manifest.yml"
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 2,
                "topic": "test_strict",
                "generated_at": "2026-05-19",
                "current_as_of": "2026-05-19",
                "freshness_policy": "strict_live",
                "cache_root": str(cache_dir),
                "entries": [entry],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    # Force Docling absence so the image-only path actually lands at degraded
    monkeypatch.setattr(
        cache_source,
        "_extract_via_docling",
        lambda raw, **kw: (_ for _ in ()).throw(ImportError("no docling")),
    )

    rc = reextract_pdfs.reextract(manifest_path, dry_run=False, strict_extraction=True)
    assert rc == 1  # strict violation

    rewritten = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert rewritten["entries"][0]["extraction_status"] == "degraded"

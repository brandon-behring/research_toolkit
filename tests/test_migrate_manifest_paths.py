"""Tests for scripts/migrate_manifest_paths.py (v2.3 — closes #13)."""
from __future__ import annotations

from pathlib import Path
import sys

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import migrate_manifest_paths  # noqa: E402


def _write_manifest(target: Path, entries: list[dict]) -> None:
    payload = {
        "schema_version": 2,
        "topic": "test_migration",
        "generated_at": "2026-05-23",
        "current_as_of": "2026-05-23",
        "freshness_policy": "strict_live",
        "cache_root": "~/Claude/research_cache",
        "entries": entries,
    }
    target.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_migrate_strips_cache_root_prefix(tmp_path: Path) -> None:
    """v2.0-v2.2 absolute paths get relativized against cache_root."""
    manifest = tmp_path / "cache_manifest.yml"
    _write_manifest(manifest, [
        {
            "cache_id": "cache_abc123def4567890",
            "source_url": "https://example.com/x",
            "fetched_at": "2026-05-19",
            "content_type": "text/html",
            "bytes": 10,
            "sha256": "a" * 64,
            "raw_path": "~/Claude/research_cache/blobs/sha256/aaaa",
            "text_path": "~/Claude/research_cache/text/sha256/aaaa.txt",
            "metadata_path": "~/Claude/research_cache/metadata/sha256/aaaa.json",
            "restricted": False,
            "rights_status": "private_use",
            "extraction_status": "ok",
        }
    ])

    rc = migrate_manifest_paths.migrate(manifest, dry_run=False)
    assert rc == 0

    rewritten = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    entry = rewritten["entries"][0]
    assert entry["raw_path"] == "blobs/sha256/aaaa"
    assert entry["text_path"] == "text/sha256/aaaa.txt"
    assert entry["metadata_path"] == "metadata/sha256/aaaa.json"


def test_migrate_is_idempotent(tmp_path: Path) -> None:
    """Already-portable manifests are not modified on re-run."""
    manifest = tmp_path / "cache_manifest.yml"
    _write_manifest(manifest, [
        {
            "cache_id": "cache_abc123def4567890",
            "source_url": "https://example.com/x",
            "fetched_at": "2026-05-19",
            "content_type": "text/html",
            "bytes": 10,
            "sha256": "a" * 64,
            "raw_path": "blobs/sha256/aaaa",
            "text_path": "text/sha256/aaaa.txt",
            "metadata_path": "metadata/sha256/aaaa.json",
            "restricted": False,
            "rights_status": "private_use",
            "extraction_status": "ok",
        }
    ])
    before = manifest.read_text(encoding="utf-8")

    rc = migrate_manifest_paths.migrate(manifest, dry_run=False)
    assert rc == 0

    after = manifest.read_text(encoding="utf-8")
    # Content equality holds (no rewrite happened)
    assert yaml.safe_load(before) == yaml.safe_load(after)


def test_migrate_dry_run_does_not_write(tmp_path: Path) -> None:
    """--dry-run reports would-change without modifying the file."""
    manifest = tmp_path / "cache_manifest.yml"
    _write_manifest(manifest, [
        {
            "cache_id": "cache_abc123def4567890",
            "source_url": "https://example.com/x",
            "fetched_at": "2026-05-19",
            "content_type": "text/html",
            "bytes": 10,
            "sha256": "a" * 64,
            "raw_path": "~/Claude/research_cache/blobs/sha256/aaaa",
            "text_path": "~/Claude/research_cache/text/sha256/aaaa.txt",
            "metadata_path": "~/Claude/research_cache/metadata/sha256/aaaa.json",
            "restricted": False,
            "rights_status": "private_use",
            "extraction_status": "ok",
        }
    ])
    before = manifest.read_text(encoding="utf-8")

    rc = migrate_manifest_paths.migrate(manifest, dry_run=True)
    assert rc == 1  # would-change exit code

    after = manifest.read_text(encoding="utf-8")
    assert before == after


def test_migrate_warns_on_out_of_root_paths(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Paths that are absolute but not under cache_root surface a warning."""
    manifest = tmp_path / "cache_manifest.yml"
    _write_manifest(manifest, [
        {
            "cache_id": "cache_abc123def4567890",
            "source_url": "https://example.com/x",
            "fetched_at": "2026-05-19",
            "content_type": "text/html",
            "bytes": 10,
            "sha256": "a" * 64,
            "raw_path": "/tmp/totally-unrelated/aaaa",
            "text_path": "blobs/sha256/aaaa.txt",
            "metadata_path": "blobs/sha256/aaaa.json",
            "restricted": False,
            "rights_status": "private_use",
            "extraction_status": "ok",
        }
    ])

    rc = migrate_manifest_paths.migrate(manifest, dry_run=False)
    captured = capsys.readouterr()
    assert "not under cache_root" in captured.err
    # Path was left unchanged (still absolute)
    rewritten = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    assert rewritten["entries"][0]["raw_path"] == "/tmp/totally-unrelated/aaaa"
    # No portable paths were rewritten, so exit is 0
    assert rc == 0


def test_migrate_errors_without_cache_root(tmp_path: Path) -> None:
    """Manifests without cache_root cannot be migrated; surface error."""
    manifest = tmp_path / "cache_manifest.yml"
    payload = {
        "schema_version": 2,
        "topic": "test",
        "generated_at": "2026-05-23",
        "current_as_of": "2026-05-23",
        "freshness_policy": "strict_live",
        # NO cache_root
        "entries": [{"cache_id": "x", "raw_path": "/foo"}],
    }
    manifest.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    rc = migrate_manifest_paths.migrate(manifest, dry_run=False)
    assert rc == 2


def test_migrate_skips_revisit_entries(tmp_path: Path) -> None:
    """Revisit entries reference captures by ID, no paths to fix."""
    manifest = tmp_path / "cache_manifest.yml"
    _write_manifest(manifest, [
        {
            "cache_id": "cache_capture_aaaa",
            "source_url": "https://example.com/x",
            "fetched_at": "2026-05-19",
            "content_type": "text/html",
            "bytes": 10,
            "sha256": "a" * 64,
            "raw_path": "~/Claude/research_cache/blobs/sha256/aaaa",
            "text_path": "~/Claude/research_cache/text/sha256/aaaa.txt",
            "metadata_path": "~/Claude/research_cache/metadata/sha256/aaaa.json",
            "restricted": False,
            "rights_status": "private_use",
            "extraction_status": "ok",
        },
        {
            "cache_id": "cache_revisit_bbbb",
            "source_url": "https://example.com/x",
            "fetched_at": "2026-05-20",
            "record_type": "revisit",
            "revisit_profile": "server-not-modified",
            "refers_to_cache_id": "cache_capture_aaaa",
        },
    ])

    rc = migrate_manifest_paths.migrate(manifest, dry_run=False)
    assert rc == 0
    rewritten = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    # Capture rewritten
    assert rewritten["entries"][0]["raw_path"] == "blobs/sha256/aaaa"
    # Revisit untouched (no path fields)
    assert "raw_path" not in rewritten["entries"][1]

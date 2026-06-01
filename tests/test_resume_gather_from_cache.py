"""Tests for scripts/resume_gather_from_cache.py."""
from __future__ import annotations

import json
from pathlib import Path

from scripts import assemble_artifacts
from scripts import resume_gather_from_cache

# The per-source keys assemble_artifacts.assemble() reads. The recovered
# skeleton must carry all of these so it is a valid assemble input.
ASSEMBLE_REQUIRED_SOURCE_KEYS = (
    "n",
    "bibkey",
    "primary_url",
    "title",
    "authors",
    "venue",
    "claim_family",
    "sha",
    "sub_area",
    "excerpt",
)


def _write_blob(
    cache_root: Path,
    sha: str,
    *,
    topic: str,
    source_url: str,
    status: str = "ok",
    text: str = "x" * 5000,
    content_type: str = "text/html",
    published_online: str | None = None,
) -> None:
    """Write a metadata sidecar + matching text file into a fake cache."""
    meta_dir = cache_root / "metadata" / "sha256"
    text_dir = cache_root / "text" / "sha256"
    blob_dir = cache_root / "blobs" / "sha256"
    meta_dir.mkdir(parents=True, exist_ok=True)
    text_dir.mkdir(parents=True, exist_ok=True)
    blob_dir.mkdir(parents=True, exist_ok=True)
    (text_dir / f"{sha}.txt").write_text(text, encoding="utf-8")
    (blob_dir / sha).write_text(text, encoding="utf-8")
    (meta_dir / f"{sha}.json").write_text(
        json.dumps(
            {
                "sha256": sha,
                "topic": topic,
                "source_url": source_url,
                "fetched_at": "2026-05-30T00:00:00+00:00",
                "content_type": content_type,
                "extraction_status": status,
                "published_online": published_online,
                "text_bytes": len(text.encode("utf-8")),
            }
        ),
        encoding="utf-8",
    )


def _fake_cache(tmp_path: Path) -> Path:
    """Build a cache with 2 good X blobs, 1 stub X blob, 1 good Y blob."""
    root = tmp_path / "cache"
    _write_blob(
        root,
        "aaa",
        topic="topic_x",
        source_url="https://example.com/x1",
        published_online="2024-01-01",
    )
    _write_blob(root, "bbb", topic="topic_x", source_url="https://example.com/x2")
    _write_blob(
        root,
        "ccc",
        topic="topic_x",
        source_url="https://example.com/x3",
        status="stub",
        text="tiny",
    )
    _write_blob(root, "ddd", topic="topic_y", source_url="https://example.com/y1")
    return root


def test_only_selects_requested_topic(tmp_path: Path) -> None:
    """Blobs from other topics are not recovered."""
    root = _fake_cache(tmp_path)
    skeleton = resume_gather_from_cache.recover_sources(
        resume_gather_from_cache.iter_metadata(root), "topic_x", root
    )
    shas = {src["sha"] for src in skeleton["sources"]}
    assert shas == {"aaa", "bbb", "ccc"}


def test_stub_blob_flagged_low_quality(tmp_path: Path) -> None:
    """A tiny stub blob is flagged low-quality with a reason, not trusted."""
    root = _fake_cache(tmp_path)
    skeleton = resume_gather_from_cache.recover_sources(
        resume_gather_from_cache.iter_metadata(root), "topic_x", root
    )
    stub = next(src for src in skeleton["sources"] if src["sha"] == "ccc")
    assert stub["_low_quality"] is True and "extraction_status=stub" in stub["_low_quality_reason"]


def test_good_blob_not_flagged_low_quality(tmp_path: Path) -> None:
    """A healthy blob with enough text carries no low-quality marker."""
    root = _fake_cache(tmp_path)
    skeleton = resume_gather_from_cache.recover_sources(
        resume_gather_from_cache.iter_metadata(root), "topic_x", root
    )
    good = next(src for src in skeleton["sources"] if src["sha"] == "aaa")
    assert "_low_quality" not in good


def test_cache_known_fields_filled(tmp_path: Path) -> None:
    """Cache-known fields (url, published_online, text path) are populated."""
    root = _fake_cache(tmp_path)
    skeleton = resume_gather_from_cache.recover_sources(
        resume_gather_from_cache.iter_metadata(root), "topic_x", root
    )
    good = next(src for src in skeleton["sources"] if src["sha"] == "aaa")
    assert (
        good["primary_url"] == "https://example.com/x1"
        and good["published_online"] == "2024-01-01"
        and good["_cached_text_path"].endswith("text/sha256/aaa.txt")
    )


def test_judgment_fields_marked_placeholder(tmp_path: Path) -> None:
    """Fields needing judgment are TODO/empty, not fabricated."""
    root = _fake_cache(tmp_path)
    skeleton = resume_gather_from_cache.recover_sources(
        resume_gather_from_cache.iter_metadata(root), "topic_x", root
    )
    good = next(src for src in skeleton["sources"] if src["sha"] == "aaa")
    assert (
        good["bibkey"] == "TODO"
        and good["claim_family"] == "TODO"
        and good["sub_area"] == "TODO"
        and good["title"] == ""
        and good["excerpt"] == ""
    )


def test_output_shape_has_assemble_required_keys(tmp_path: Path) -> None:
    """Every recovered source carries the keys assemble_artifacts reads."""
    root = _fake_cache(tmp_path)
    skeleton = resume_gather_from_cache.recover_sources(
        resume_gather_from_cache.iter_metadata(root), "topic_x", root
    )
    out = tmp_path / "recovered.json"
    out.write_text(json.dumps(skeleton), encoding="utf-8")
    loaded = json.loads(out.read_text(encoding="utf-8"))
    needed = set(ASSEMBLE_REQUIRED_SOURCE_KEYS)
    assert loaded["topic"] == "topic_x"
    assert {"topic", "today", "cache_root", "sources", "rejects"} <= set(loaded)
    assert all(needed <= set(src) for src in loaded["sources"])


def test_completed_skeleton_is_valid_assemble_input(tmp_path: Path) -> None:
    """A recovered source, once an excerpt is filled, feeds assemble() cleanly.

    Proves the skeleton is a real assemble input (not just key-shaped): fill
    one source's placeholder fields the way a resumer would, then run the
    actual assemble() and confirm it emits a bib + evidence entry with no
    excerpt failures.
    """
    root = _fake_cache(tmp_path)
    # Give the good blob a known excerpt that occurs in its cached text.
    excerpt = "the quick brown fox"
    (root / "text" / "sha256" / "aaa.txt").write_text(
        "intro " + excerpt + " outro", encoding="utf-8"
    )
    skeleton = resume_gather_from_cache.recover_sources(
        resume_gather_from_cache.iter_metadata(root), "topic_x", root
    )
    completed = next(src for src in skeleton["sources"] if src["sha"] == "aaa")
    completed.update(
        {
            "bibkey": "smith2024fox",
            "title": "A Fox Paper",
            "authors": "Smith, A.",
            "venue": "arXiv preprint",
            "claim_family": "primary",
            "sub_area": "foxes",
            "excerpt": excerpt,
        }
    )
    data = {
        "topic": "topic_x",
        "today": "2026-05-30",
        "cache_root": str(root),
        "sources": [completed],
        "rejects": [],
    }
    artifacts, failures = assemble_artifacts.assemble(data, root)
    assert failures == []
    assert len(artifacts["bib"]) == 1 and artifacts["bib"][0]["bibkey"] == "smith2024fox"
    assert len(artifacts["evidence"]) == 1


def test_existing_merge_keeps_filled_record(tmp_path: Path) -> None:
    """A human-completed record survives merge and is not overwritten."""
    root = _fake_cache(tmp_path)
    existing = {
        "topic": "topic_x",
        "today": "2026-05-01",
        "cache_root": str(root),
        "sources": [
            {
                "n": 1,
                "bibkey": "smith2024foo",
                "primary_url": "https://example.com/x1",
                "title": "Real Title",
                "authors": "Smith, A.",
                "venue": "ACL",
                "claim_family": "fam",
                "sha": "aaa",
                "sub_area": "area",
                "excerpt": "real excerpt",
            }
        ],
        "rejects": [],
    }
    skeleton = resume_gather_from_cache.recover_sources(
        resume_gather_from_cache.iter_metadata(root), "topic_x", root, existing
    )
    kept = next(src for src in skeleton["sources"] if src["sha"] == "aaa")
    assert kept["title"] == "Real Title" and kept["bibkey"] == "smith2024foo"


def test_existing_merge_dedups_by_sha(tmp_path: Path) -> None:
    """A cache blob already present (by sha) is not added twice."""
    root = _fake_cache(tmp_path)
    existing = {
        "topic": "topic_x",
        "today": "2026-05-01",
        "cache_root": str(root),
        "sources": [
            {
                "n": 1,
                "bibkey": "smith2024foo",
                "primary_url": "https://other.example/renamed",
                "title": "Real Title",
                "authors": "Smith, A.",
                "venue": "ACL",
                "claim_family": "fam",
                "sha": "aaa",
                "sub_area": "area",
                "excerpt": "real excerpt",
            }
        ],
        "rejects": [],
    }
    skeleton = resume_gather_from_cache.recover_sources(
        resume_gather_from_cache.iter_metadata(root), "topic_x", root, existing
    )
    aaa_records = [src for src in skeleton["sources"] if src["sha"] == "aaa"]
    assert len(aaa_records) == 1 and skeleton["_recovery_summary"]["recovered"] == 2


def test_existing_merge_dedups_by_primary_url(tmp_path: Path) -> None:
    """A cache blob already present (by primary_url) is not re-added."""
    root = _fake_cache(tmp_path)
    existing = {
        "topic": "topic_x",
        "today": "2026-05-01",
        "cache_root": str(root),
        "sources": [
            {
                "n": 1,
                "bibkey": "smith2024foo",
                "primary_url": "https://example.com/x1",
                "title": "Real Title",
                "authors": "Smith, A.",
                "venue": "ACL",
                "claim_family": "fam",
                "sha": "different-sha",
                "sub_area": "area",
                "excerpt": "real excerpt",
            }
        ],
        "rejects": [],
    }
    skeleton = resume_gather_from_cache.recover_sources(
        resume_gather_from_cache.iter_metadata(root), "topic_x", root, existing
    )
    x1_records = [src for src in skeleton["sources"] if src["primary_url"] == "https://example.com/x1"]
    assert len(x1_records) == 1


def test_main_writes_output_and_is_read_only(tmp_path: Path) -> None:
    """main() writes the out file and never mutates the cache."""
    root = _fake_cache(tmp_path)
    before = {p.name for p in (root / "metadata" / "sha256").iterdir()}
    out = tmp_path / "out.json"
    rc = resume_gather_from_cache.main(
        ["topic_x", "--cache-root", str(root), "--out", str(out)]
    )
    after = {p.name for p in (root / "metadata" / "sha256").iterdir()}
    written = json.loads(out.read_text(encoding="utf-8"))
    assert rc == 0 and before == after and len(written["sources"]) == 3


def test_main_missing_existing_errors(tmp_path: Path) -> None:
    """A nonexistent --existing path exits 1 with a clear message."""
    root = _fake_cache(tmp_path)
    out = tmp_path / "out.json"
    rc = resume_gather_from_cache.main(
        ["topic_x", "--cache-root", str(root), "--out", str(out), "--existing", str(tmp_path / "nope.json")]
    )
    assert rc == 1

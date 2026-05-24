"""Tests for each validator: positive case + at least one negative case.

Each validator must:
- Return an empty error list on a known-good fixture artifact (positive case).
- Return >=1 error on a deliberately-corrupted variant (negative case), with
  the error message containing a substring that identifies the corruption.

This proves the validators have signal — they don't just accept everything.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from validators import (
    agent_index,
    audit_trail,
    bib_ledger,
    cache_manifest,
    dossier,
    evidence_ledger,
    research_plan,
    url_check_report,
)


# ---------- positive cases (mini fixture) ----------

def test_research_plan_accepts_mini(mini_dir: Path) -> None:
    assert research_plan.validate(mini_dir / "research_plan.md") == []


def test_bib_ledger_accepts_mini(mini_dir: Path) -> None:
    assert bib_ledger.validate(mini_dir / "bib_ledger.yml") == []


def test_dossier_accepts_mini(mini_dir: Path) -> None:
    assert dossier.validate(mini_dir / "dossier") == []


def test_agent_index_accepts_mini(mini_dir: Path) -> None:
    assert agent_index.validate(mini_dir / "agent_index") == []


def test_audit_trail_accepts_clean_readme(mini_dir: Path) -> None:
    # Mini agent_index README has no audit-trail notes yet — that's fine
    # (the validator only fails on malformed notes, not absence).
    assert audit_trail.validate(mini_dir / "agent_index" / "README.md") == []


# ---------- negative cases (corrupted variants) ----------

def test_research_plan_rejects_too_few_subareas(mini_dir: Path, tmp_path: Path) -> None:
    text = (mini_dir / "research_plan.md").read_text(encoding="utf-8")
    # Replace the Sub-areas section with one that has only 2 sub-areas (need 4-8).
    truncated = text.replace(
        "## Sub-areas\n\n- A1",
        "## Sub-areas\n\n- only_one\n- and_another\n\n## ZZZ unused\n\n## A1",
    )
    bad = tmp_path / "research_plan.md"
    bad.write_text(truncated, encoding="utf-8")
    errors = research_plan.validate(bad)
    assert any("Sub-areas" in e and "at least" in e for e in errors), errors


def test_bib_ledger_rejects_duplicate_bibkey(mini_dir: Path, tmp_path: Path) -> None:
    text = (mini_dir / "bib_ledger.yml").read_text(encoding="utf-8")
    # Append a duplicate of the first bibkey.
    duplicated = text + (
        "- bibkey: ahmad2017nab\n"
        "  primary_url: https://arxiv.org/abs/0000.00000\n"
        "  title: 'Duplicate Title'\n"
        "  status: unverified\n"
        "  claim_family: benchmark\n"
    )
    bad = tmp_path / "bib_ledger.yml"
    bad.write_text(duplicated, encoding="utf-8")
    errors = bib_ledger.validate(bad)
    assert any("duplicate bibkey" in e for e in errors), errors


def test_bib_ledger_rejects_invalid_status(mini_dir: Path, tmp_path: Path) -> None:
    text = (mini_dir / "bib_ledger.yml").read_text(encoding="utf-8")
    bad_text = text.replace("status: verified", "status: bogus_status", 1)
    bad = tmp_path / "bib_ledger.yml"
    bad.write_text(bad_text, encoding="utf-8")
    errors = bib_ledger.validate(bad)
    assert any("not in" in e and "status" in e for e in errors), errors


def test_dossier_rejects_missing_first_4_columns(mini_dir: Path, tmp_path: Path) -> None:
    src = mini_dir / "dossier" / "01_benchmarks_and_datasets.md"
    text = src.read_text(encoding="utf-8")
    # Replace 'Authors (year)' header with something else; this should fail
    # the first-4-cols rule for paper tables (col 2 ≠ Authors (year)
    # makes it a non-paper table — but the data row only has 7 cells, none
    # of which contain a URL, since we strip the existing URLs too).
    # Easier: corrupt the header itself by removing the GitHub column.
    bad_text = text.replace(
        "| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |",
        "| Title | Authors (year) | Venue | arXiv/DOI | OneLine | Key contribution |",
    )
    dossier_dir = tmp_path / "dossier"
    dossier_dir.mkdir()
    (dossier_dir / "01_benchmarks_and_datasets.md").write_text(bad_text, encoding="utf-8")
    errors = dossier.validate(dossier_dir)
    assert any("column 5" in e or "header columns" in e for e in errors), errors


def test_agent_index_rejects_missing_agent_index_comment(
    mini_dir: Path, tmp_path: Path
) -> None:
    src_dir = mini_dir / "agent_index"
    target = tmp_path / "agent_index"
    target.mkdir()
    for src_file in src_dir.iterdir():
        if src_file.name == "README.md":
            text = src_file.read_text(encoding="utf-8")
            # Strip the AGENT-INDEX HTML comment.
            stripped = text.replace(
                "<!-- AGENT-INDEX: this folder is a self-contained reference for time-series anomaly detection benchmarks. Read this README first. -->\n",
                "",
            )
            (target / src_file.name).write_text(stripped, encoding="utf-8")
        else:
            (target / src_file.name).write_text(
                src_file.read_text(encoding="utf-8"), encoding="utf-8"
            )
    errors = agent_index.validate(target)
    assert any("AGENT-INDEX" in e for e in errors), errors


def test_audit_trail_rejects_bad_date_format(tmp_path: Path) -> None:
    bad = tmp_path / "README.md"
    bad.write_text(
        "**Independent audit, round 1 (May 2026):** something\n",
        encoding="utf-8",
    )
    errors = audit_trail.validate(bad)
    assert any("YYYY-MM-DD" in e for e in errors), errors


def test_url_check_report_rejects_missing_summary(tmp_path: Path) -> None:
    bad = tmp_path / "url_check.md"
    bad.write_text(
        "# URL Freshness Report\n\nGenerated: 2026-05-06\n\n(no summary section)",
        encoding="utf-8",
    )
    errors = url_check_report.validate(bad)
    assert any("Summary" in e for e in errors), errors


def test_url_check_report_accepts_minimal_well_formed(tmp_path: Path) -> None:
    good = tmp_path / "url_check.md"
    good.write_text(
        (
            "# URL Freshness Report\n\n"
            "Generated: 2026-05-06\n\n"
            "## Summary\n\n"
            "- total: 100\n"
            "- ok: 95\n"
            "- broken: 3\n"
            "- bot-blocked: 2\n"
        ),
        encoding="utf-8",
    )
    assert url_check_report.validate(good) == []


# ---------- v2.3 lessons: fuzzy taxonomy + heading tolerance + wiki-links ----------

def test_common_matches_canonical_fuzzy_helper() -> None:
    """Unit test for matches_canonical_fuzzy — covers exact, substring (both
    directions), case/whitespace/backtick normalization, and the min-len guard.
    """
    from validators._common import matches_canonical_fuzzy

    canonical = {
        "Session state (--resume, fork_session, scratchpads)",
        "Agentic loops (stop_reason, tool result handling)",
        "Built-in tools (Read, Write, Edit, Bash, Grep, Glob)",
    }

    # Exact match (after normalization)
    assert matches_canonical_fuzzy(
        "Session state (--resume, fork_session, scratchpads)", canonical
    )

    # Substring — note is shorter than canonical
    assert matches_canonical_fuzzy("Session state", canonical)
    assert matches_canonical_fuzzy("Agentic loops", canonical)

    # Punctuation normalization (`--` stripped; backticks stripped)
    assert matches_canonical_fuzzy(
        "Session state (resume, fork_session, scratchpads)", canonical
    )
    assert matches_canonical_fuzzy(
        "Built-in tools (`Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob`)", canonical
    )

    # Min-len guard: a too-short value shouldn't match via substring
    assert not matches_canonical_fuzzy("loops", canonical)
    assert not matches_canonical_fuzzy("ABC", canonical)

    # Genuinely unknown value
    assert not matches_canonical_fuzzy(
        "Completely unrelated taxonomy entry that won't match", canonical
    )


def test_url_check_report_accepts_summary_with_parenthetical(tmp_path: Path) -> None:
    """Heading regex tolerates clarifying parentheticals (BURN_IN dogfood #3)."""
    good = tmp_path / "url_check.md"
    good.write_text(
        (
            "# URL Freshness Report\n\n"
            "Generated: 2026-05-06\n\n"
            "## Summary (May 2026 snapshot)\n\n"
            "- total: 100\n"
            "- ok: 95\n"
            "- broken: 3\n"
            "- bot-blocked: 2\n"
        ),
        encoding="utf-8",
    )
    assert url_check_report.validate(good) == []


def test_cross_stage_fuzzy_claim_family_is_warning_not_error(tmp_path: Path) -> None:
    """A paraphrased claim_family that fuzzy-matches the taxonomy is a WARN,
    not an error (default strict=False). BURN_IN dogfood #5.
    """
    from validators import cross_stage

    (tmp_path / "research_plan.md").write_text(
        (
            "# Research Plan: test\n\n"
            "## Sub-areas\n\n- A1 alpha\n- A2 beta\n\n"
            "## Out-of-scope\n\n- nothing\n\n"
            "## Claim family taxonomy\n\n"
            "- `benchmark`\n"
            "- `dataset_resource`\n"
            "- `toolkit`\n"
        ),
        encoding="utf-8",
    )
    (tmp_path / "bib_ledger.yml").write_text(
        (
            "entries:\n"
            "- bibkey: alpha2024test\n"
            "  primary_url: https://arxiv.org/abs/2401.00001\n"
            "  title: 'Alpha Test Paper'\n"
            "  status: unverified\n"
            "  claim_family: dataset_resource_v2\n"
        ),
        encoding="utf-8",
    )
    errors_default = cross_stage.validate(tmp_path)
    # Default (non-strict): the paraphrased family fuzzy-matches → WARN, not error.
    assert errors_default == [], errors_default

    errors_strict = cross_stage.validate(tmp_path, strict=True)
    # Strict: WARN promotes to error.
    assert any("paraphrases" in e or "fuzzy" in e for e in errors_strict), errors_strict


def test_cross_stage_dangling_wiki_link_warns(tmp_path: Path) -> None:
    """Dangling [[slug]] cross-references in agent_index/ produce warnings
    (--strict promotes to error). BURN_IN dogfood #6.
    """
    from validators import cross_stage

    # Minimal valid setup so the other checks don't fire spuriously.
    (tmp_path / "research_plan.md").write_text(
        (
            "# Research Plan: test\n\n"
            "## Sub-areas\n\n- A1 alpha\n- A2 beta\n\n"
            "## Out-of-scope\n\n- nothing\n\n"
            "## Claim family taxonomy\n\n- `benchmark`\n"
        ),
        encoding="utf-8",
    )
    (tmp_path / "bib_ledger.yml").write_text(
        (
            "entries:\n"
            "- bibkey: alpha2024test\n"
            "  primary_url: https://arxiv.org/abs/2401.00001\n"
            "  title: 'Alpha Test Paper'\n"
            "  status: unverified\n"
            "  claim_family: benchmark\n"
        ),
        encoding="utf-8",
    )
    agent_index_dir = tmp_path / "agent_index"
    agent_index_dir.mkdir()
    (agent_index_dir / "README.md").write_text(
        (
            "<!-- AGENT-INDEX: test -->\n\n"
            "## Scope boundary\n\nx\n\n## Lookup recipes\n\nx\n\n"
            "## Glossary\n\nx\n"
        ),
        encoding="utf-8",
    )
    (agent_index_dir / "01_synthesis.md").write_text(
        (
            "# Synthesis\n\n"
            "- **Source:** https://arxiv.org/abs/2401.00001 alpha2024test\n"
            "  See [[alpha2024test]] for the canonical paper (resolves: bibkey).\n"
            "  See [[02_other_synthesis]] for related material (resolves: filename).\n"
            "  See [[totally-nonexistent-slug]] (DANGLING — should warn).\n"
        ),
        encoding="utf-8",
    )
    (agent_index_dir / "02_other_synthesis.md").write_text(
        "# Other\n\n- **Source:** https://arxiv.org/abs/2401.00001 alpha2024test\n",
        encoding="utf-8",
    )

    errors_default = cross_stage.validate(tmp_path)
    # The dangling link is a WARN, not an error in default mode.
    assert errors_default == [], errors_default

    errors_strict = cross_stage.validate(tmp_path, strict=True)
    assert any(
        "dangling" in e and "totally-nonexistent-slug" in e for e in errors_strict
    ), errors_strict


# ---------- cache_manifest path portability (v2.3 / #13) ----------


def _scaffold_cache(cache_root: Path, body: bytes, name: str = "aaaa") -> dict:
    """Write blob/text/metadata files into cache_root and return manifest entry shape."""
    digest = hashlib.sha256(body).hexdigest()
    (cache_root / "blobs" / "sha256").mkdir(parents=True, exist_ok=True)
    (cache_root / "text" / "sha256").mkdir(parents=True, exist_ok=True)
    (cache_root / "metadata" / "sha256").mkdir(parents=True, exist_ok=True)
    (cache_root / "blobs" / "sha256" / digest).write_bytes(body)
    (cache_root / "text" / "sha256" / f"{digest}.txt").write_text(
        body.decode("utf-8", errors="replace"), encoding="utf-8"
    )
    (cache_root / "metadata" / "sha256" / f"{digest}.json").write_text(
        json.dumps({"sha256": digest}), encoding="utf-8"
    )
    return {
        "cache_id": f"cache_{digest[:16]}",
        "source_url": "https://example.com/portable",
        "fetched_at": "2026-05-23",
        "content_type": "text/html",
        "bytes": len(body),
        "sha256": digest,
        "raw_path": f"blobs/sha256/{digest}",
        "text_path": f"text/sha256/{digest}.txt",
        "metadata_path": f"metadata/sha256/{digest}.json",
        "restricted": False,
        "rights_status": "private_use",
        "extraction_status": "ok",
    }


def test_cache_manifest_resolves_relative_paths_against_cache_root(tmp_path: Path) -> None:
    """v2.3 _resolve honors cache_root for relative path values."""
    cache_dir = tmp_path / "shared_cache"
    cache_dir.mkdir()
    entry = _scaffold_cache(cache_dir, b"<html>portable</html>")

    manifest_dir = tmp_path / "project" / "docs"
    manifest_dir.mkdir(parents=True)
    manifest = manifest_dir / "cache_manifest.yml"
    payload = {
        "schema_version": 2,
        "topic": "portable_test",
        "generated_at": "2026-05-23",
        "current_as_of": "2026-05-23",
        "freshness_policy": "strict_live",
        "cache_root": str(cache_dir),
        "entries": [entry],
    }
    manifest.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    errors = cache_manifest.validate(manifest)
    assert errors == [], errors


def test_cache_manifest_rejects_absolute_path(tmp_path: Path) -> None:
    """v2.3 portability guard: writer-side absolute paths fail validation."""
    cache_dir = tmp_path / "shared_cache"
    cache_dir.mkdir()
    entry = _scaffold_cache(cache_dir, b"<html>absolute</html>")
    # Promote to absolute path (the writer bug we're guarding against)
    digest = entry["sha256"]
    entry["raw_path"] = str(cache_dir / "blobs" / "sha256" / digest)

    manifest = tmp_path / "cache_manifest.yml"
    payload = {
        "schema_version": 2,
        "topic": "absolute_test",
        "generated_at": "2026-05-23",
        "current_as_of": "2026-05-23",
        "freshness_policy": "strict_live",
        "cache_root": str(cache_dir),
        "entries": [entry],
    }
    manifest.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    errors = cache_manifest.validate(manifest)
    assert any("portable" in e and "raw_path" in e for e in errors), errors


def test_cache_manifest_rejects_tilde_path(tmp_path: Path) -> None:
    """v2.3 portability guard: ~-prefixed paths fail validation."""
    cache_dir = tmp_path / "shared_cache"
    cache_dir.mkdir()
    entry = _scaffold_cache(cache_dir, b"<html>tilde</html>")
    entry["text_path"] = "~/Claude/research_cache/text/sha256/whatever.txt"

    manifest = tmp_path / "cache_manifest.yml"
    payload = {
        "schema_version": 2,
        "topic": "tilde_test",
        "generated_at": "2026-05-23",
        "current_as_of": "2026-05-23",
        "freshness_policy": "strict_live",
        "cache_root": str(cache_dir),
        "entries": [entry],
    }
    manifest.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    errors = cache_manifest.validate(manifest)
    assert any("portable" in e and "text_path" in e for e in errors), errors


# ---------- mixed-cache-location dossiers (v2.3.x / #14) ----------


def test_cache_manifest_falls_back_to_manifest_local_for_derived_artifacts(
    tmp_path: Path,
) -> None:
    """v2.3.x #14: when cache_root is set, fall back to manifest_path.parent
    for entries whose files live dossier-local (derived artifacts per
    ADR-049 body-quote anchoring discipline).

    Mixed-cache scenario:
    - Primary cache entries (sha256-keyed PDFs/HTML) live in cache_root
    - Derived per-bibkey artifacts (pdftotext body_text + body_meta) live
      under <manifest_dir>/cache/body_text/<bibkey>.txt
    Both should validate cleanly under v2.3.x.
    """
    cache_dir = tmp_path / "shared_cache"
    cache_dir.mkdir()

    # Primary entry: lives in cache_root
    primary_entry = _scaffold_cache(cache_dir, b"<html>primary content</html>")

    # Derived entry: pdftotext output lives DOSSIER-LOCAL, not in cache_root.
    # This mirrors the ADR-049 body-quote anchoring pattern.
    manifest_dir = tmp_path / "project" / "docs" / "research" / "topic-a"
    manifest_dir.mkdir(parents=True)
    body_text_dir = manifest_dir / "cache" / "body_text"
    body_text_dir.mkdir(parents=True)
    body_text_dir.joinpath("debenedetti2025camel.txt").write_text(
        "Sample body-quote anchored extraction from a published paper.\n",
        encoding="utf-8",
    )
    # Also need raw_path + metadata_path to exist somewhere; use dossier-local
    # for these too (the derived-artifact case).
    papers_dir = manifest_dir / "papers"
    papers_dir.mkdir(parents=True)
    pdf_bytes = b"%PDF-1.4 stub"
    pdf_path = papers_dir / "debenedetti2025camel.pdf"
    pdf_path.write_bytes(pdf_bytes)
    body_meta_dir = manifest_dir / "cache" / "body_meta"
    body_meta_dir.mkdir(parents=True)
    body_meta_dir.joinpath("debenedetti2025camel.json").write_text(
        json.dumps({"extraction_method": "pdftotext"}), encoding="utf-8"
    )

    pdf_sha = hashlib.sha256(pdf_bytes).hexdigest()
    derived_entry = {
        "cache_id": "cache_body_debenedetti2025camel",
        "source_url": "https://arxiv.org/abs/2503.18813",
        "fetched_at": "2026-05-23",
        "content_type": "application/pdf",
        "bytes": len(pdf_bytes),
        "sha256": pdf_sha,
        "raw_path": "papers/debenedetti2025camel.pdf",
        "text_path": "cache/body_text/debenedetti2025camel.txt",
        "metadata_path": "cache/body_meta/debenedetti2025camel.json",
        "restricted": False,
        "rights_status": "private_use",
        "extraction_status": "ok",
    }

    manifest = manifest_dir / "cache_manifest.yml"
    payload = {
        "schema_version": 2,
        "topic": "mixed_test",
        "generated_at": "2026-05-23",
        "current_as_of": "2026-05-23",
        "freshness_policy": "strict_live",
        "cache_root": str(cache_dir),
        "entries": [primary_entry, derived_entry],
    }
    manifest.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    errors = cache_manifest.validate(manifest)
    assert errors == [], errors


def test_resolve_cache_path_prefers_cache_root_then_dossier_local(
    tmp_path: Path,
) -> None:
    """Resolution order for v2.3.x #14:
    1. cache_root / value (if exists)
    2. manifest_path.parent / value (if cache_root candidate doesn't exist)
    3. cache_root / value (for consistent error messages when neither exists)
    """
    from validators.v2_common import resolve_cache_path

    cache_dir = tmp_path / "cache_root"
    cache_dir.mkdir()
    manifest_dir = tmp_path / "dossier"
    manifest_dir.mkdir()
    manifest_path = manifest_dir / "cache_manifest.yml"
    manifest_path.write_text("# stub\n")

    # Case 1: file in cache_root
    (cache_dir / "shared.txt").write_text("shared")
    resolved = resolve_cache_path(
        "shared.txt", manifest_path=manifest_path, cache_root=str(cache_dir)
    )
    assert resolved == (cache_dir / "shared.txt").resolve()

    # Case 2: file dossier-local only (cache_root candidate doesn't exist)
    (manifest_dir / "local.txt").write_text("local")
    resolved = resolve_cache_path(
        "local.txt", manifest_path=manifest_path, cache_root=str(cache_dir)
    )
    assert resolved == (manifest_dir / "local.txt").resolve()

    # Case 3: neither exists — return cache_root candidate for consistent
    # error messages (caller's .exists() check will surface failure)
    resolved = resolve_cache_path(
        "missing.txt", manifest_path=manifest_path, cache_root=str(cache_dir)
    )
    assert resolved == (cache_dir / "missing.txt").resolve()

    # Case 4: no cache_root — v2.0-v2.2 behavior (manifest-local only)
    (manifest_dir / "legacy.txt").write_text("legacy")
    resolved = resolve_cache_path(
        "legacy.txt", manifest_path=manifest_path, cache_root=None
    )
    assert resolved == (manifest_dir / "legacy.txt").resolve()

    # Case 5: absolute path passes through expanduser
    absolute = str(cache_dir / "shared.txt")
    resolved = resolve_cache_path(
        absolute, manifest_path=manifest_path, cache_root=str(cache_dir)
    )
    assert resolved == Path(absolute)


def test_evidence_ledger_validates_dossier_local_body_anchor_with_cache_root(
    tmp_path: Path,
) -> None:
    """Integration test for #14: evidence_ledger validation with cache_root
    set + a verbatim_match anchor whose text_path lives DOSSIER-LOCAL.

    Pairs with test_cache_manifest_falls_back_to_manifest_local_for_derived_artifacts
    above (which exercises the same fallback through cache_manifest validation).
    This test exercises the SAME fallback through verify_excerpt_anchor (used
    by evidence_ledger.validate). Both paths share resolve_cache_path under
    the hood; this test ensures the integration through verify_excerpt_anchor
    survives any future refactor that drops the cache_root pass-through.
    """
    # Shared cache_root (unused by this test's body-anchored entry, but set
    # to match the real-world mixed-cache scenario).
    cache_dir = tmp_path / "shared_cache"
    cache_dir.mkdir()

    # Dossier directory (where the manifest + evidence_ledger live).
    manifest_dir = tmp_path / "project" / "docs" / "research" / "topic-a"
    manifest_dir.mkdir(parents=True)

    # Body-quote-anchored text lives DOSSIER-LOCAL per ADR-049 discipline.
    # The cache_id uses the "cache_body_<bibkey>" convention (non-sha256).
    body_text_dir = manifest_dir / "cache" / "body_text"
    body_text_dir.mkdir(parents=True)
    # Use exact-byte content so we can compute the precise offset + hash.
    body_text = b"The figure shows 91.2% accuracy on the held-out evaluation set."
    body_text_path = body_text_dir / "demo_paper.txt"
    body_text_path.write_bytes(body_text)

    # Extract a verbatim span "91.2% accuracy" + compute its sha256.
    span_start = body_text.index(b"91.2% accuracy")
    span_end = span_start + len(b"91.2% accuracy")
    span_bytes = body_text[span_start:span_end]
    span_sha = hashlib.sha256(span_bytes).hexdigest()

    # Companion PDF (raw_path target) + metadata (also dossier-local).
    papers_dir = manifest_dir / "papers"
    papers_dir.mkdir(parents=True)
    pdf_bytes = b"%PDF-1.4 stub for body-anchored entry"
    pdf_path = papers_dir / "demo_paper.pdf"
    pdf_path.write_bytes(pdf_bytes)
    body_meta_dir = manifest_dir / "cache" / "body_meta"
    body_meta_dir.mkdir(parents=True)
    body_meta_dir.joinpath("demo_paper.json").write_text(
        json.dumps({"extraction_method": "pdftotext"}), encoding="utf-8"
    )

    pdf_sha = hashlib.sha256(pdf_bytes).hexdigest()
    cache_manifest_payload = {
        "schema_version": 2,
        "topic": "integration_test",
        "generated_at": "2026-05-23",
        "current_as_of": "2026-05-23",
        "freshness_policy": "strict_live",
        "cache_root": str(cache_dir),
        "entries": [
            {
                "cache_id": "cache_body_demo_paper",
                "source_url": "https://example.com/demo_paper",
                "fetched_at": "2026-05-23",
                "content_type": "application/pdf",
                "bytes": len(pdf_bytes),
                "sha256": pdf_sha,
                "raw_path": "papers/demo_paper.pdf",
                "text_path": "cache/body_text/demo_paper.txt",
                "metadata_path": "cache/body_meta/demo_paper.json",
                "restricted": False,
                "rights_status": "private_use",
                "extraction_status": "ok",
            }
        ],
    }
    (manifest_dir / "cache_manifest.yml").write_text(
        yaml.safe_dump(cache_manifest_payload, sort_keys=False), encoding="utf-8"
    )

    evidence_payload = {
        "schema_version": 3,
        "topic": "integration_test",
        "generated_at": "2026-05-23",
        "current_as_of": "2026-05-23",
        "freshness_policy": "strict_live",
        "entries": [
            {
                "evidence_id": "ev_integration_test_0001",
                "source_url": "https://example.com/demo_paper",
                "source_type": "paper",
                "source_quality": "primary",
                "retrieved_at": "2026-05-23",
                "verification_method": "pdf",
                "verified_at": "2026-05-23",
                "verified_fields": ["source_url"],
                "freshness_tier": "stable",
                "stale_after_days": 365,
                "cache_ids": ["cache_body_demo_paper"],
                "evidence_ids": [],
                "supports": [
                    {
                        "claim_id": "claim_integration_test_accuracy",
                        "field_path": "bib_ledger.entries[0].title",
                        "evidence_role": "supports",
                        "evidence_role_strength": "full",
                        "extraction_method": "verbatim_match",
                        "link_confidence": 0.95,
                        "excerpt_anchor": {
                            "cache_id": "cache_body_demo_paper",
                            "text_path_offset": [span_start, span_end],
                            "sha256_of_span": span_sha,
                        },
                    }
                ],
                "excerpt": "91.2% accuracy",
                "rights_status": "private_use",
            }
        ],
    }
    evidence_path = manifest_dir / "evidence_ledger.yml"
    evidence_path.write_text(
        yaml.safe_dump(evidence_payload, sort_keys=False), encoding="utf-8"
    )

    # Pre-fix behavior: would fail with "text_path file does not exist" because
    # resolve_cache_path would only try cache_root.
    # Post-fix: falls back to manifest_path.parent → finds the dossier-local
    # body_text file → passes substring + hash check.
    errors = evidence_ledger.validate(evidence_path)
    assert errors == [], errors

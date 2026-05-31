#!/usr/bin/env python3
"""Assemble the four strict-live gather artifacts from a sources JSON + cache.

Committed successor to the uncommitted ``~/Claude/_assemble.py`` scratch helper
that the strict-live topic batches were built with. Reads a sources-JSON
description of gathered references plus the on-disk content-addressed web cache,
then writes the four strict-live gather artifacts into a project directory::

    bib_ledger.yml        schema_version 2 — one entry per source
    evidence_ledger.yml   schema_version 3 — one entry per source, byte-anchored
    cache_manifest.yml    schema_version 2 — one entry per cached blob
    gather_trace.yml      schema_version 3 — accepted sources + rejected fetches

Every evidence excerpt is anchored to byte offsets + a sha256-of-span. The byte
math is delegated to :func:`scripts.build_excerpt_anchor.build_anchor` (the
canonical anchor producer) instead of a private re-implementation. It is called
with ``occurrence=1`` so that, like the scratch ``anchor()`` (which does
``blob.find(needle)`` and silently takes the first hit), the FIRST byte-match is
selected even when the excerpt recurs in the cached text (common for arXiv
abstracts duplicated on the HTML page). For a verbatim byte-substring this yields
``[first_occurrence_start, end]`` and ``sha256(text_bytes[start:end])`` —
byte-identical to the scratch helper — and passes
``validators.v2_common.verify_excerpt_anchor``.

Sources-JSON schema (the shape ``_assemble.py`` / the topic batches use): a JSON
mapping with top-level ``topic``, ``today`` (ISO date used for every
``*_at`` / ``generated_at`` / ``current_as_of`` field), ``cache_root`` (``~`` is
expanded), ``sources`` (list), and ``rejects`` (list). Each source has ``n``,
``bibkey``, ``primary_url``, ``title``, ``authors``, ``venue``, ``claim_family``,
``sha`` (the blob's sha256; ``cache_id`` is ``"cache_" + sha[:16]``), ``sub_area``,
``excerpt``, and optional ``code_url`` / ``cache_source_url`` /
``published_online``. ``code_url`` (when present) is carried into the bib entry;
``cache_source_url`` is NOT a bib field — it only sets the cache entry's
``source_url`` (e.g. a PDF mirror of an abstract page). ``published_online`` is
emitted into the bib + cache entries only when the source carries it (mirroring
the shipped batches; a bare ``cache_source_url`` does NOT add a null
``published_online``). Each reject has ``fetch_id``, ``sub_area``, ``query``,
``source_url``, ``is_relevant``, ``is_supported``, ``is_useful``, ``decision``,
``reason``.

Hardcoded evidence defaults (matching the scratch helper + shipped artifacts):
source_type ``paper``, source_quality ``primary``, evidence_role ``supports``,
evidence_role_strength ``full``, extraction_method ``verbatim_match``,
link_confidence ``0.98``, evidence rights_status ``public``, cache rights_status
``private_use``, freshness_tier ``active``, stale_after_days ``90``,
verification_method ``webfetch``.

An excerpt that does not byte-substring-match its cached text is reported as an
``EXCERPT FAILURE`` to stderr and causes a non-zero exit (no silent dropping).

Exit codes: 0 success; 1 excerpt failure / data error; 2 usage / file-not-found.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.build_excerpt_anchor import build_anchor

STALE_AFTER_DAYS = 90
FRESHNESS_TIER = "active"
VERIFICATION_METHOD = "webfetch"
VERIFIED_FIELDS = ["title", "authors", "year", "primary_url"]


def cache_id_for(sha: str) -> str:
    """Derive the cache_id (``cache_`` + first 16 hex chars of the sha256)."""
    return "cache_" + sha[:16]


def _build_bib_entry(src: dict[str, Any], today: str, evidence_id: str, cache_id: str) -> dict[str, Any]:
    # Note: cache_source_url is NOT a bib_ledger field (it lives on the cache
    # entry's source_url); the scratch _assemble.py + shipped artifacts only
    # carry code_url + published_online as bib optionals.
    entry: dict[str, Any] = {
        "bibkey": src["bibkey"],
        "primary_url": src["primary_url"],
        "title": src["title"],
        "status": "verified",
        "claim_family": src["claim_family"],
    }
    if "code_url" in src:
        entry["code_url"] = src["code_url"]
    entry.update(
        {
            "authors": src["authors"],
            "venue": src["venue"],
            "retrieved_at": today,
            "verified_at": today,
            "verification_method": VERIFICATION_METHOD,
            "verified_fields": list(VERIFIED_FIELDS),
            "freshness_tier": FRESHNESS_TIER,
            "stale_after_days": STALE_AFTER_DAYS,
            "evidence_ids": [evidence_id],
            "cache_ids": [cache_id],
        }
    )
    if "published_online" in src:
        entry["published_online"] = src["published_online"]
    return entry


def _build_cache_entry(src: dict[str, Any], today: str, cache_id: str, blob_bytes: int) -> dict[str, Any]:
    sha = src["sha"]
    entry: dict[str, Any] = {
        "cache_id": cache_id,
        "source_url": src.get("cache_source_url", src["primary_url"]),
        "fetched_at": today,
        "content_type": "text/html",
        "bytes": blob_bytes,
        "sha256": sha,
        "raw_path": f"blobs/sha256/{sha}",
        "text_path": f"text/sha256/{sha}.txt",
        "metadata_path": f"metadata/sha256/{sha}.json",
        "restricted": False,
        "rights_status": "private_use",
        "extraction_status": "ok",
    }
    if "published_online" in src:
        entry["published_online"] = src["published_online"]
    return entry


def _build_evidence_entry(
    src: dict[str, Any],
    today: str,
    evidence_id: str,
    claim_id: str,
    cache_id: str,
    anchor: dict[str, Any],
) -> dict[str, Any]:
    return {
        "evidence_id": evidence_id,
        "source_url": src["primary_url"],
        "source_type": "paper",
        "source_quality": "primary",
        "retrieved_at": today,
        "verification_method": VERIFICATION_METHOD,
        "cache_ids": [cache_id],
        "supports": [
            {
                "claim_id": claim_id,
                "field_path": f"bib_ledger.entries[{src['bibkey']}].abstract",
                "evidence_role": "supports",
                "evidence_role_strength": "full",
                "extraction_method": "verbatim_match",
                "link_confidence": 0.98,
                "excerpt_anchor": {
                    "cache_id": cache_id,
                    "text_path_offset": anchor["text_path_offset"],
                    "sha256_of_span": anchor["sha256_of_span"],
                },
            }
        ],
        "excerpt": src["excerpt"],
        "rights_status": "public",
        "confidence": {
            "score": 0.95,
            "factors": ["primary source", "cached raw snapshot"],
        },
    }


def _build_accept_fetch(src: dict[str, Any], today: str) -> dict[str, Any]:
    return {
        "fetch_id": f"fetch_{src['bibkey']}",
        "sub_area": src["sub_area"],
        "query": f"{src['title'][:60]} primary source",
        "source_url": src["primary_url"],
        "fetched_at": today,
        "reflection": {"is_relevant": True, "is_supported": "full", "is_useful": 5},
        "decision": "accept",
        "reason": "Primary source; title/author/year confirmed on fetched page; cached + anchored.",
        "assigned_bibkey": src["bibkey"],
    }


def _build_reject_fetch(reject: dict[str, Any], today: str) -> dict[str, Any]:
    return {
        "fetch_id": reject["fetch_id"],
        "sub_area": reject["sub_area"],
        "query": reject["query"],
        "source_url": reject["source_url"],
        "fetched_at": today,
        "reflection": {
            "is_relevant": reject["is_relevant"],
            "is_supported": reject["is_supported"],
            "is_useful": reject["is_useful"],
        },
        "decision": reject["decision"],
        "reason": reject["reason"],
    }


def assemble(
    data: dict[str, Any],
    cache_root: Path,
) -> tuple[
    dict[str, list[dict[str, Any]]],
    list[str],
]:
    """Build the four artifact entry-lists from a parsed sources mapping.

    Returns ``(artifacts, failures)`` where ``artifacts`` maps each of
    ``bib`` / ``evidence`` / ``cache`` / ``fetches`` to its entry list and
    ``failures`` lists human-readable strings for excerpts that did not occur in
    their cached text. Callers must treat a non-empty ``failures`` list as a
    hard error and not write anything.
    """
    topic = data["topic"]
    today = data["today"]

    bib: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    cache: list[dict[str, Any]] = []
    fetches: list[dict[str, Any]] = []
    failures: list[str] = []

    for src in data.get("sources", []):
        sha = src["sha"]
        cache_id = cache_id_for(sha)
        evidence_id = f"ev_{topic}_{src['n']}"
        claim_id = f"claim_{topic}_{src['n']}"

        text_path = cache_root / "text" / "sha256" / f"{sha}.txt"
        blob_path = cache_root / "blobs" / "sha256" / sha
        text_bytes = text_path.read_bytes()

        # cache + bib are emitted regardless; evidence only when the excerpt anchors.
        cache.append(_build_cache_entry(src, today, cache_id, blob_path.stat().st_size))
        bib.append(_build_bib_entry(src, today, evidence_id, cache_id))

        # occurrence=1 forces first-occurrence selection, matching the scratch
        # _assemble.py anchor() (blob.find -> first hit) and the shipped
        # artifacts. Without it build_anchor raises on excerpts that recur in
        # the cached text (e.g. arXiv abstracts duplicated on the HTML page).
        try:
            anchor = build_anchor(text_bytes, src["excerpt"], occurrence=1)
        except ValueError as exc:
            failures.append(f"{src['bibkey']} ({sha[:16]}): {exc}")
            continue

        evidence.append(
            _build_evidence_entry(src, today, evidence_id, claim_id, cache_id, anchor)
        )
        fetches.append(_build_accept_fetch(src, today))

    for reject in data.get("rejects", []):
        fetches.append(_build_reject_fetch(reject, today))

    artifacts = {"bib": bib, "evidence": evidence, "cache": cache, "fetches": fetches}
    return artifacts, failures


def _dump(path: Path, header: dict[str, Any], key: str, items: list[dict[str, Any]]) -> None:
    import yaml

    doc = dict(header)
    doc[key] = items
    path.write_text(
        yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=4096),
        encoding="utf-8",
    )


def write_artifacts(
    project_dir: Path,
    data: dict[str, Any],
    artifacts: dict[str, list[dict[str, Any]]],
) -> None:
    """Write the four YAML artifacts into ``project_dir``."""
    project_dir.mkdir(parents=True, exist_ok=True)
    topic = data["topic"]
    today = data["today"]
    common = {
        "topic": topic,
        "generated_at": today,
        "current_as_of": today,
        "freshness_policy": "strict_live",
    }
    _dump(
        project_dir / "bib_ledger.yml",
        {"schema_version": 2, **common},
        "entries",
        artifacts["bib"],
    )
    _dump(
        project_dir / "evidence_ledger.yml",
        {"schema_version": 3, **common},
        "entries",
        artifacts["evidence"],
    )
    _dump(
        project_dir / "cache_manifest.yml",
        {"schema_version": 2, **common, "cache_root": data["cache_root"]},
        "entries",
        artifacts["cache"],
    )
    _dump(
        project_dir / "gather_trace.yml",
        {"schema_version": 3, **common},
        "fetches",
        artifacts["fetches"],
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="assemble_artifacts",
        description=__doc__.splitlines()[0] if __doc__ else None,
    )
    parser.add_argument("sources", help="path to the sources JSON mapping")
    parser.add_argument("project_dir", help="directory to write the 4 artifacts into")
    parser.add_argument(
        "--cache-root",
        default=None,
        help="override the cache_root from the sources JSON (content-addressed cache)",
    )
    args = parser.parse_args(argv)

    sources_path = Path(args.sources).expanduser()
    project_dir = Path(args.project_dir).expanduser()
    try:
        data = json.loads(sources_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"error: sources file not found: {sources_path}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON in {sources_path}: {exc}", file=sys.stderr)
        return 1

    cache_root = Path(args.cache_root or data["cache_root"]).expanduser()

    artifacts, failures = assemble(data, cache_root)

    if failures:
        print("EXCERPT FAILURE (fix the excerpt in the sources JSON and rerun):", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    write_artifacts(project_dir, data, artifacts)
    print(
        f"wrote bib={len(artifacts['bib'])} evidence={len(artifacts['evidence'])} "
        f"cache={len(artifacts['cache'])} fetches={len(artifacts['fetches'])} -> {project_dir}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

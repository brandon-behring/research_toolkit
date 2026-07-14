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
``published_online`` / ``rights_status`` / ``visibility`` / ``license``.
Rights default to ``unknown`` and access visibility is left unknown when those
fields are absent; only explicit public rights plus public visibility produce an
unrestricted cache body. ``code_url`` (when present) is carried into the bib entry;
``cache_source_url`` is NOT a bib field — it only sets the cache entry's
``source_url`` (e.g. a PDF mirror of an abstract page). ``published_online`` is
emitted into the bib + cache entries only when the source carries it (mirroring
the shipped batches; a bare ``cache_source_url`` does NOT add a null
``published_online``). Each reject has ``fetch_id``, ``sub_area``, ``query``,
``source_url``, ``is_relevant``, ``is_supported``, ``is_useful``, ``decision``,
``reason``.

Evidence defaults (matching the scratch helper + shipped artifacts except for
the former unsafe rights assumption):
source_type ``paper``, source_quality ``primary``, evidence_role ``supports``,
evidence_role_strength ``full``, extraction_method ``verbatim_match``,
link_confidence ``0.98``, evidence/cache rights_status ``unknown`` unless the
source supplies a valid decision, freshness_tier ``active``, stale_after_days
``90``, verification_method ``webfetch``.

An excerpt that does not byte-substring-match its cached text is reported as an
``EXCERPT FAILURE`` to stderr and causes a non-zero exit (no silent dropping).

Exit codes: 0 success; 1 excerpt failure / data error; 2 usage / file-not-found.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.build_excerpt_anchor import build_anchor
from research_toolkit.retrieval_security import (
    RetrievalSecurityError,
    record_safe_url,
    validate_record_url,
)

STALE_AFTER_DAYS = 90
FRESHNESS_TIER = "active"
VERIFICATION_METHOD = "webfetch"
VERIFIED_FIELDS = ["title", "authors", "year", "primary_url"]
ALLOWED_RIGHTS_STATUS = {"public", "private_use", "restricted", "unknown", "cache_only"}
ALLOWED_VISIBILITY = {"public", "authenticated", "private"}
_URL_IN_TEXT = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
_PRIVATE_DIRECTORY_MODE = 0o700
_PRIVATE_FILE_MODE = 0o600


class ArtifactRollbackError(OSError):
    """The artifact transaction failed and its private backups were retained."""


def _mode(path: Path) -> int:
    """Return the permission bits without following a final symlink."""
    return stat.S_IMODE(os.lstat(path).st_mode)


def _verify_private_directory(path: Path) -> None:
    info = os.lstat(path)
    if not stat.S_ISDIR(info.st_mode):
        raise NotADirectoryError(f"artifact directory is not a directory: {path}")
    if stat.S_IMODE(info.st_mode) != _PRIVATE_DIRECTORY_MODE:
        raise PermissionError(
            f"artifact directory must have mode 0700: {path}"
        )


def _ensure_private_directory(path: Path) -> None:
    """Create missing directories privately and tighten the output directory."""
    missing: list[Path] = []
    current = path
    while True:
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            missing.append(current)
            parent = current.parent
            if parent == current:
                raise
            current = parent
            continue
        if not stat.S_ISDIR(info.st_mode):
            raise NotADirectoryError(f"artifact path parent is not a directory: {current}")
        break

    for directory in reversed(missing):
        try:
            os.mkdir(directory, _PRIVATE_DIRECTORY_MODE)
        except FileExistsError:
            # A concurrent creator does not bypass the type/mode checks below.
            pass
        os.chmod(directory, _PRIVATE_DIRECTORY_MODE)
        _verify_private_directory(directory)

    # Existing output directories are also tightened before any artifact data
    # is written. This makes reruns safe after a permissive mode change.
    os.chmod(path, _PRIVATE_DIRECTORY_MODE)
    _verify_private_directory(path)


def _write_private_text(path: Path, content: str) -> None:
    """Atomically replace ``path`` with a verified owner-only regular file."""
    _ensure_private_directory(path.parent)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        os.fchmod(fd, _PRIVATE_FILE_MODE)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise PermissionError(f"artifact temporary path is not a regular file: {path}")
        if stat.S_IMODE(info.st_mode) != _PRIVATE_FILE_MODE:
            raise PermissionError(
                f"artifact temporary file must have mode 0600: {path}"
            )
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            fd = -1
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        info = os.lstat(path)
        if not stat.S_ISREG(info.st_mode):
            raise PermissionError(f"artifact path is not a regular file: {path}")
        if _mode(path) != _PRIVATE_FILE_MODE:
            raise PermissionError(f"artifact file must have mode 0600: {path}")
    finally:
        if fd >= 0:
            os.close(fd)
        temp_path.unlink(missing_ok=True)


def _record_url(value: Any, loc: str) -> str:
    """Return a URL that is safe to persist, without exposing the raw value."""
    raw = str(value or "").strip()
    if not raw:
        raise ValueError(f"{loc}: source URL is required")
    safe = record_safe_url(raw)
    try:
        validate_record_url(safe, allow_public_query=True)
    except RetrievalSecurityError as exc:
        raise ValueError(f"{loc}: source URL is not safe to persist ({exc})") from exc
    return safe


def _record_safe_text(value: Any) -> str:
    """Redact credentials, fragments, and non-public queries in free-form prose."""
    text = str(value or "")

    def replace(match: re.Match[str]) -> str:
        raw = match.group(0)
        trailing = ""
        while raw and raw[-1] in ".,;:!?)]}":
            trailing = raw[-1] + trailing
            raw = raw[:-1]
        safe = record_safe_url(raw)
        try:
            validate_record_url(safe, allow_public_query=True)
        except RetrievalSecurityError:
            safe = "<redacted-invalid-url>"
        return safe + trailing

    return _URL_IN_TEXT.sub(replace, text)


def _sanitize_record_values(value: Any) -> Any:
    """Recursively enforce URL redaction across every value headed for YAML."""
    if isinstance(value, str):
        return _record_safe_text(value)
    if isinstance(value, list):
        return [_sanitize_record_values(item) for item in value]
    if isinstance(value, dict):
        return {key: _sanitize_record_values(item) for key, item in value.items()}
    return value


def _safe_failure_text(value: Any) -> str:
    """Return an error label/message without echoing URL-borne credentials."""
    return _record_safe_text(value)


def _source_rights(src: dict[str, Any]) -> tuple[str, str | None]:
    """Return a validated, conservative body-rights/access decision."""
    rights_status = src.get("rights_status", "unknown")
    if rights_status not in ALLOWED_RIGHTS_STATUS:
        raise ValueError(
            f"rights_status {rights_status!r} not in {sorted(ALLOWED_RIGHTS_STATUS)}"
        )
    visibility = src.get("visibility")
    if visibility is not None and visibility not in ALLOWED_VISIBILITY:
        raise ValueError(
            f"visibility {visibility!r} not in {sorted(ALLOWED_VISIBILITY)}"
        )
    return rights_status, visibility


def cache_id_for(sha: str) -> str:
    """Derive the cache_id (``cache_`` + first 16 hex chars of the sha256)."""
    return "cache_" + sha[:16]


def _build_bib_entry(src: dict[str, Any], today: str, evidence_id: str, cache_id: str) -> dict[str, Any]:
    # Note: cache_source_url is NOT a bib_ledger field (it lives on the cache
    # entry's source_url); the scratch _assemble.py + shipped artifacts only
    # carry code_url + published_online as bib optionals.
    entry: dict[str, Any] = {
        "bibkey": src["bibkey"],
        "primary_url": _record_url(src["primary_url"], "source.primary_url"),
        "title": src["title"],
        "status": "verified",
        "claim_family": src["claim_family"],
    }
    if "code_url" in src:
        entry["code_url"] = _record_url(src["code_url"], "source.code_url")
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
    rights_status, visibility = _source_rights(src)
    entry: dict[str, Any] = {
        "cache_id": cache_id,
        "source_url": _record_url(
            src.get("cache_source_url", src["primary_url"]),
            "source.cache_source_url" if "cache_source_url" in src else "source.primary_url",
        ),
        "fetched_at": today,
        "content_type": "text/html",
        "bytes": blob_bytes,
        "sha256": sha,
        "raw_path": f"blobs/sha256/{sha}",
        "text_path": f"text/sha256/{sha}.txt",
        "metadata_path": f"metadata/sha256/{sha}.json",
        "restricted": rights_status != "public" or visibility != "public",
        "rights_status": rights_status,
        "extraction_status": "ok",
    }
    if visibility is not None:
        entry["visibility"] = visibility
    if "license" in src:
        entry["license"] = src["license"]
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
    rights_status, _ = _source_rights(src)
    return {
        "evidence_id": evidence_id,
        "source_url": _record_url(src["primary_url"], "source.primary_url"),
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
        "rights_status": rights_status,
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
        "source_url": _record_url(src["primary_url"], "source.primary_url"),
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
        "source_url": _record_url(reject["source_url"], "reject.source_url"),
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

        try:
            _source_rights(src)
            _record_url(src["primary_url"], "source.primary_url")
            if "cache_source_url" in src:
                _record_url(src["cache_source_url"], "source.cache_source_url")
            if "code_url" in src:
                _record_url(src["code_url"], "source.code_url")
        except ValueError as exc:
            failures.append(
                f"{_safe_failure_text(src.get('bibkey', '<unknown source>'))}: "
                f"{_safe_failure_text(exc)}"
            )
            continue

        # An excerpt is a byte-anchored quotation. Redacting it after anchor
        # construction would silently invalidate that anchor, while retaining
        # it could persist a bearer URL. Require the caller to choose a safe
        # excerpt instead.
        if _record_safe_text(src["excerpt"]) != src["excerpt"]:
            failures.append(
                f"{_safe_failure_text(src.get('bibkey', '<unknown source>'))}: "
                "excerpt contains URL "
                "material that is not safe to persist; choose a different excerpt"
            )
            continue

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
            failures.append(
                f"{_safe_failure_text(src['bibkey'])} "
                f"({_safe_failure_text(sha[:16])}): {_safe_failure_text(exc)}"
            )
            continue

        evidence.append(
            _build_evidence_entry(src, today, evidence_id, claim_id, cache_id, anchor)
        )
        fetches.append(_build_accept_fetch(src, today))

    for reject in data.get("rejects", []):
        try:
            fetches.append(_build_reject_fetch(reject, today))
        except ValueError as exc:
            failures.append(
                f"{_safe_failure_text(reject.get('fetch_id', '<unknown reject>'))}: "
                f"{_safe_failure_text(exc)}"
            )

    artifacts = _sanitize_record_values(
        {"bib": bib, "evidence": evidence, "cache": cache, "fetches": fetches}
    )
    return artifacts, failures


def _render_yaml(
    header: dict[str, Any],
    key: str,
    items: list[dict[str, Any]],
) -> str:
    import yaml

    doc = dict(header)
    doc[key] = items
    doc = _sanitize_record_values(doc)
    return yaml.safe_dump(
        doc,
        sort_keys=False,
        allow_unicode=True,
        width=4096,
    )


def _preflight_artifact_targets(
    project_dir: Path,
    names: tuple[str, ...],
) -> dict[str, bool]:
    """Record target presence and reject directories, links, and special files."""
    existed: dict[str, bool] = {}
    for name in names:
        target = project_dir / name
        try:
            info = os.lstat(target)
        except FileNotFoundError:
            existed[name] = False
            continue
        if not stat.S_ISREG(info.st_mode):
            raise PermissionError(
                f"artifact target must be a regular file or absent: {target}"
            )
        existed[name] = True
    return existed


def _rollback_artifact_set(
    project_dir: Path,
    backup_dir: Path,
    existed: dict[str, bool],
) -> None:
    """Remove new targets and restore every original file moved to backup."""
    for name, was_present in existed.items():
        target = project_dir / name
        backup = backup_dir / name
        backup_present = backup.exists()
        if not backup_present and was_present:
            # The original was never moved, so this target must be left alone.
            continue
        try:
            info = os.lstat(target)
        except FileNotFoundError:
            pass
        else:
            if not stat.S_ISREG(info.st_mode):
                raise PermissionError(
                    f"cannot safely roll back non-regular artifact target: {target}"
                )
            target.unlink()
        if backup_present:
            os.replace(backup, target)


def _commit_artifact_set(
    project_dir: Path,
    staged_dir: Path,
    backup_dir: Path,
    existed: dict[str, bool],
) -> None:
    """Commit the staged set, restoring the complete prior set on any failure."""
    names = tuple(existed)
    try:
        for name in names:
            if existed[name]:
                os.replace(project_dir / name, backup_dir / name)
        for name in names:
            os.replace(staged_dir / name, project_dir / name)
        for name in names:
            target = project_dir / name
            info = os.lstat(target)
            if not stat.S_ISREG(info.st_mode):
                raise PermissionError(f"artifact path is not a regular file: {target}")
            if stat.S_IMODE(info.st_mode) != _PRIVATE_FILE_MODE:
                raise PermissionError(f"artifact file must have mode 0600: {target}")
    except BaseException:
        try:
            _rollback_artifact_set(project_dir, backup_dir, existed)
        except BaseException as rollback_error:
            raise ArtifactRollbackError(
                "artifact-set commit failed and automatic rollback also failed; "
                f"private recovery files remain under {backup_dir.parent}"
            ) from rollback_error
        raise


def write_artifacts(
    project_dir: Path,
    data: dict[str, Any],
    artifacts: dict[str, list[dict[str, Any]]],
) -> None:
    """Transactionally replace the four YAML artifacts in ``project_dir``."""
    _ensure_private_directory(project_dir)
    topic = data["topic"]
    today = data["today"]
    common = {
        "topic": topic,
        "generated_at": today,
        "current_as_of": today,
        "freshness_policy": "strict_live",
    }
    rendered = {
        "bib_ledger.yml": _render_yaml(
            {"schema_version": 2, **common}, "entries", artifacts["bib"]
        ),
        "evidence_ledger.yml": _render_yaml(
            {"schema_version": 3, **common}, "entries", artifacts["evidence"]
        ),
        "cache_manifest.yml": _render_yaml(
            {"schema_version": 2, **common, "cache_root": data["cache_root"]},
            "entries",
            artifacts["cache"],
        ),
        "gather_trace.yml": _render_yaml(
            {"schema_version": 3, **common}, "fetches", artifacts["fetches"]
        ),
    }
    names = tuple(rendered)
    transaction_dir = Path(
        tempfile.mkdtemp(
            prefix=".assemble-artifacts-",
            dir=project_dir,
        )
    )
    retain_recovery = False
    try:
        os.chmod(transaction_dir, _PRIVATE_DIRECTORY_MODE)
        _verify_private_directory(transaction_dir)
        staged_dir = transaction_dir / "staged"
        backup_dir = transaction_dir / "backup"
        _ensure_private_directory(staged_dir)
        _ensure_private_directory(backup_dir)
        for name, content in rendered.items():
            _write_private_text(staged_dir / name, content)

        existed = _preflight_artifact_targets(project_dir, names)
        _commit_artifact_set(
            project_dir,
            staged_dir,
            backup_dir,
            existed,
        )
    except ArtifactRollbackError:
        retain_recovery = True
        raise
    finally:
        if not retain_recovery:
            shutil.rmtree(transaction_dir, ignore_errors=False)


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

    try:
        write_artifacts(project_dir, data, artifacts)
    except OSError as exc:
        print(f"error: could not write private artifacts: {exc}", file=sys.stderr)
        return 1
    print(
        f"wrote bib={len(artifacts['bib'])} evidence={len(artifacts['evidence'])} "
        f"cache={len(artifacts['cache'])} fetches={len(artifacts['fetches'])} -> {project_dir}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
